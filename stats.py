#!/usr/bin/env python2

import os
import datetime

import requests
import pytz

pacific = pytz.timezone('US/Eastern')

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
        if local.isoweekday() >= 6: # sat or sunday
            return False
        return local.time().hour >= 9 and local.time().hour <= 18

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
        Return all completed features and their estimates for a project
        '''
        features = self._getJSON(
                "/projects/%d/stories" % projectId,
                { "filter": "state:accepted type:Feature includedone:true" })
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
    apiToken = os.environ['TRACKER_API_TOKEN']
    projectId = int(os.environ['PROJECT_ID'])

    client = TrackerClient(apiToken)

    features = client.getDoneFeatures(projectId)

    for storyId, estimate in features:
        history = client.getHistory(projectId, storyId)
        duration = Clocker.hoursWorked(history)
        print storyId, estimate, duration
