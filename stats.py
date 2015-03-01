#!/usr/bin/env python2

import os
import datetime
import argparse

import requests
import pytz


class Clocker:

    '''
    Count the hours
    '''

    def __init__(self, timezone):
        self.timezone = pytz.timezone(timezone)
        self.work_start = datetime.time(hour=9, minute=15)
        self.lunch_start = datetime.time(hour=12, minute=30)
        self.lunch_end = datetime.time(hour=13, minute=30)
        self.work_end = datetime.time(hour=18)

    def is_during_work_day(self, utc_time):
        '''
        Crude guess at whether a given time was during work hours
        '''
        local = utc_time.astimezone(self.timezone)
        if local.isoweekday() >= 6:  # sat or sunday
            return False
        t = local.time()
        if t < self.work_start or t > self.work_end:
            return False
        if t > self.lunch_start and t < self.lunch_end:
            return False
        return True

    def work_time_between(self, start, end):
        '''
        How much work time (M-F, 9-6) elapsed between the start time and end time
        '''
        duration = datetime.timedelta(0)
        resolution = datetime.timedelta(minutes=10)
        while start < end:
            if self.is_during_work_day(start):
                duration += resolution
            start += resolution
        return duration

    def hours_worked(self, history):
        '''
        How many hours were spent on a story, given it's history of state changes
        *** This is probably a gross over-estimate.  But what else can we do?  ***
        '''
        duration = datetime.timedelta(0)
        last_start = None
        for new_time, new_state in history:
            if new_state == 'started':
                last_start = new_time
            elif last_start is not None:
                duration += self.work_time_between(last_start, new_time)
                last_start = None
        return duration.total_seconds() / (60 * 60)


class TrackerClient:

    '''
    An API client for Pivotal Tracker
    '''

    def __init__(self, apiToken):
        self.session = requests.Session()
        self.session.headers.update({"X-TrackerToken": apiToken})

    def _get_json(self, route, queryParams=None):
        return self.session.get(
            "https://www.pivotaltracker.com/services/v5" + route,
            params=queryParams).json()

    def get_done_features(self, project_id):
        '''
        Return all completed features and their estimates from the last 6 months
          (Tracker API only exposes activity that far back)
        '''
        min_date = (
            datetime.datetime.now() -
            datetime.timedelta(
                days=180)).strftime("%m/%d/%Y")
        features = self._get_json(
            "/projects/%d/stories" %
            project_id, {
                'filter': 'state:accepted type:Feature includedone:true created_since:"%s"' %
                min_date})
        return [(f['id'], f['estimate']) for f in features]

    def get_history(self, project_id, story_id):
        '''
        Return a condensed history of a story as (date, state) pairs
        where state is { started, finished, delivered, accepted }
        '''
        activity = self._get_json(
            "/projects/%d/stories/%d/activity" %
            (project_id, story_id))
        changes = [
            (a['occurred_at'], c['new_values']['current_state'])
            for a in activity
            for c in a['changes']
            if ('new_values' in c) and ('current_state' in c['new_values'])
        ]
        return sorted([(TrackerClient._parse_timestamp(date), state)
                       for date, state in changes])

    @staticmethod
    def _parse_timestamp(utcTime, fmt="%Y-%m-%dT%H:%M:%SZ"):
        return pytz.utc.localize(datetime.datetime.strptime(utcTime, fmt))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='compare hours worked to points estimated')
    parser.add_argument('token', help='API token for Pivotal Tracker')
    parser.add_argument(
        'project',
        type=int,
        help='Project ID to collect stats on')
    parser.add_argument(
        '--timezone',
        default='US/Pacific',
        help='Timezone, e.g. US/Pacific')
    args = parser.parse_args()

    clocker = Clocker(args.timezone)
    client = TrackerClient(args.token)

    features = client.get_done_features(args.project)

    print "%s\t%s\t%s" % ('story_id', 'estimate', 'duration')
    for story_id, estimate in features:
        history = client.get_history(args.project, story_id)
        duration = clocker.hours_worked(history)
        print "%d\t%d\t%1.2f" % (story_id, estimate, duration)
