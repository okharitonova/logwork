from __future__ import absolute_import
from jira import JIRA

from . import get_settings


class JiraClient(JIRA):

    def __init__(self, user, password):
        config = get_settings('jira')
        super(JiraClient, self).__init__(
            server=config['server'],
            basic_auth=(user, password)
        )
