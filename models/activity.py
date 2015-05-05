from datetime import datetime
from dateutil import parser


STATUS_WORKLOG = 'Workloged'
STATUS_CREATED = 'Created'
STATUS_COMMENTED = 'Commented'
STATUS_DEVELOPMENT = 'Development'
STATUS_STASH = "Stash"

AVAILABLE_ACTIONS_WITH_WEIGHT = {
    'New': 1,
    'ReadyForDev': 1,
    'Testing': 3,
    'Need Fixing': 1,
    'Fixing': 10,
    'Need Testing': 1,
    'ReadyForTraining': 1,
    'Training': 1,
    'Release': 1,
    'Done': 1,
    'Need Code Review': 3,
    'Code Review': 5,
    STATUS_DEVELOPMENT: 10,
    STATUS_STASH: 1,
    STATUS_COMMENTED: 4,
    STATUS_CREATED: 5,
}

class Activity(object):

    def __init__(self, key, date=None, name='', worklog=0, changed_lines=0):
        self._key = key
        self._name = name
        self._date = date
        self._worklog = worklog
        self._changed_lines = changed_lines

    @property
    def key(self):
        return self._key

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def date(self):
        if self._date and type(self._date) is not datetime:
            self._date = parser.parse(self._date, ignoretz=True)
        return self._date

    @property
    def worklog(self):
        return int(self._worklog)

    @worklog.setter
    def worklog(self, value):
        self._worklog += int(value)

    @property
    def changed_lines(self):
        return self._changed_lines

    @changed_lines.setter
    def changed_lines(self, value):
        self._changed_lines += int(value)
