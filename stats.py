#!/usr/bin/env python2

import os
import datetime
import argparse

import requests
import pytz

pacific = pytz.timezone('US/Pacific')
workStart = datetime.time(hour=9, minute=15)
lunchStart = datetime.time(hour=12, minute=30)
lunchEnd = datetime.time(hour=13, minute=30)
workEnd = datetime.time(hour=18)

class Clocker:
    '''
    Count the hours
    '''

    @staticmethod
    def isDuringWorkDay(time):
        '''
        Crude guess at whether a given time was during work hours
        '''
        local = time.astimezone(pacific)
        weekday = local.weekday()
        if local.isoweekday() >= 6:  # sat or sunday
            return False
        t = local.time()
        if t < workStart or t > workEnd:
            return False
        if t > lunchStart and t < lunchEnd:
            return False
        return True

    @staticmethod
    def workTimeBetween(start, end):
        '''
        How many normal work hours (M-F, 9-6) are between the start and end time
        '''
        duration = datetime.timedelta(0)
        resolution = datetime.timedelta(minutes=10)
        while start < end:
            if Clocker.isDuringWorkDay(start):
                duration += resolution
            start += resolution
        return duration

    @staticmethod
    def hoursWorked(history):
        '''
        How many hours were spent on a story, given it's history of state changes
        *** This is often a gross over-estimate.  But what else can we do?  ***
        '''
        duration = datetime.timedelta(0)
        timeOfLastStart = None
        for newTime, newState in history:
            if newState == 'started':
                timeOfLastStart = newTime
            elif timeOfLastStart is not None:
                duration += Clocker.workTimeBetween(timeOfLastStart, newTime)
                timeOfLastStart = None
        return duration.total_seconds() / (60 * 60)


class TrackerClient:
    '''
    An API client for Pivotal Tracker
    '''

    def __init__(self, apiToken):
        self.session = requests.Session()
        self.session.headers.update({"X-TrackerToken": apiToken})
        self.baseUrl = "https://www.pivotaltracker.com/services/v5"

    def _getJSON(self, route, queryParams=None):
        return self.session.get(self.baseUrl + route, params=queryParams).json()

    def getDoneFeatures(self, projectId):
        '''
        Return all completed features and their estimates from the last 6 months
          (Tracker API only exposes activity that far back)
        '''
        min_date = (datetime.datetime.now()-datetime.timedelta(days=180)).strftime("%m/%d/%Y")
        features = self._getJSON(
                "/projects/%d/stories" % projectId,
                { 'filter': 'state:accepted type:Feature includedone:true created_since:"%s"' % min_date })
        return [ (f['id'], f['estimate']) for f in features ]

    def getHistory(self, projectId, storyId):
        '''
        Return a condensed history of a story as (date, state) pairs
        where state is { started, finished, delivered, accepted }
        '''
        activity = self._getJSON("/projects/%d/stories/%d/activity" % (projectId, storyId))
        changes = [
            (a['occurred_at'], c['new_values']['current_state'])
                for a in activity
                for c in a['changes']
                if ('new_values' in c) and ('current_state' in c['new_values'])
            ]
        return sorted([ (TrackerClient._parse_timestamp(date), state) for date,state in changes ])

    @staticmethod
    def _parse_timestamp(utcTime, fmt="%Y-%m-%dT%H:%M:%SZ"):
        return pytz.utc.localize(datetime.datetime.strptime(utcTime, fmt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='collect some stats for a Tracker Project')
    parser.add_argument('token', help='API token for Pivotal Tracker')
    parser.add_argument('project', type=int, help='Project ID to collect stats on')
    args = parser.parse_args()

    client = TrackerClient(args.token)

    features = client.getDoneFeatures(args.project)

    for storyId, estimate in features:
        history = client.getHistory(args.project, storyId)
        duration = Clocker.hoursWorked(history)
        print "%d\t%d\t%1.2f" % (storyId, estimate, duration)
