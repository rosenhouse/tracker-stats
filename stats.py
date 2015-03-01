#!/usr/bin/env python2

import os
import datetime

import requests

def from_utc(utcTime,fmt="%Y-%m-%dT%H:%M:%SZ"):
    return datetime.datetime.strptime(utcTime, fmt)

def hoursWorked(stateChanges):  # TODO: limit this to 9am-6pm M-F
    duration = datetime.timedelta(0)
    timeOfLastStart = None
    for dt, newState in stateChanges:
        if newState == 'started':
            timeOfLastStart = dt
        elif timeOfLastStart is not None:
            duration += (dt - timeOfLastStart)
            timeOfLastStart = None
    return duration.total_seconds() / (60 * 60)

class Client:
    def __init__(self, apiToken):
        self.session = requests.Session()
        self.session.headers.update({"X-TrackerToken": apiToken})
        self.baseUrl = "https://www.pivotaltracker.com/services/v5"

    def getPointedFeatures(self, projectId):
        url = self.baseUrl + "/projects/%d/stories" % projectId
        query = { "filter": "state:accepted type:Feature includedone:true" }
        features = self.session.get(url, params=query).json()
        return [ (f['id'], f['estimate']) for f in features ]

    def getStateChanges(self, projectId, storyId):
        url = self.baseUrl + "/projects/%d/stories/%d/activity" % (projectId, storyId)
        activity = self.session.get(url).json()
        changes = [
            (a['occurred_at'], c['new_values']['current_state'])
                for a in activity
                for c in a['changes']
                if ('new_values' in c) and ('current_state' in c['new_values'])
            ]
        return sorted([ (from_utc(date), state) for date,state in changes ])

if __name__ == "__main__":
    apiToken = os.environ['TOKEN']
    projectId = int(os.environ['PROJECT_ID'])

    client = Client(apiToken)

    features = client.getPointedFeatures(projectId)

    for storyId, estimate in features:
        stateChanges = client.getStateChanges(projectId, storyId)
        duration = hoursWorked(stateChanges)
        print storyId, estimate, duration
