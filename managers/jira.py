# coding: utf-8

from datetime import datetime
from dateutil import parser
from six import text_type

from clients.jira import JiraClient
from models.activity import (
    Activity,
    STATUS_WORKLOG,
    STATUS_CREATED,
    STATUS_COMMENTED,
    STATUS_DEVELOPMENT)


class JiraManager(object):

    def __init__(self, user, password):
        self.jira_client = JiraClient(user, password)
        self.username = self.jira_client.current_user()

    def get_all_acivities(self):
        """
        Aggregates all user`s activity
        :return: dict of models.activity.Activity
        """
        activities = []
        activities += self.issues_with_user_in_participants()
        activities += self.created_issues()
        activities += self.issue_in_development()
        return activities

    def issues_with_user_in_participants(self):
        """
        Append issue updated today.
        Add all issuses, where current user is participant and
        which was changed today
        """
        activities = []
        issues = self.jira_client.search_issues(
            'Participants = currentUser() '
            'AND updated > startOfDay() ',
            expand='changelog'
        )
        today = datetime.today().date()
        for issue in issues:
            changelog = issue.changelog
            # Get history (equivalently tab History in jira interface)
            for history in changelog.histories:
                if (history.author.name != self.username or
                        parser.parse(history.created).date() < today):
                    continue

                for item in history.items:
                    if item.field == 'status':
                        activity = Activity(issue.key, date=history.created)
                        activity.name = item.toString
                        activities.append(activity)

            # Get comments are left by currentuser
            comments = self.jira_client.comments(issue)
            for comment in comments:
                if (comment.author.name == self.username and
                        parser.parse(comment.created).date() == today):
                    activity = Activity(
                        issue.key,
                        date=comment.created,
                        name=STATUS_COMMENTED
                    )
                    activities.append(activity)

            worklogs = self.jira_client.worklogs(issue)
            for worklog in worklogs:
                if (worklog.author.name == self.username and
                        parser.parse(worklog.created).date() == today):
                    activity = Activity(
                        issue.key,
                        date=worklog.created,
                        name=STATUS_WORKLOG,
                        worklog=worklog.timeSpentSeconds
                    )
                    activities.append(activity)

        return activities

    def created_issues(self):
        """
        Append issues created by currentUser during the day.
        """
        issues = self.jira_client.search_issues(
            'reporter = currentUser() '
            'AND created > startOfDay()')
        if issues:
            return self._append_activities(STATUS_CREATED, issues)
        return []

    def issue_in_development(self):
        """
        Append issues which have status in development.
        This status can set not necessarily today.
        """
        issues = self.jira_client.search_issues(
            'assignee = currentUser() '
            'AND status = Development '
            'AND updated < startOfDay()'
        )
        if issues:
            return self._append_activities(STATUS_DEVELOPMENT, issues)
        return []

    def _append_activities(self, activity_name, issues):
        activities = []
        for issue in issues:
            activity = Activity(issue.key, name=activity_name)
            activities.append(activity)
        return activities

    def add_worklog(self, issue, time_spent, save_log=False):
        if save_log:
            self.jira_client.add_worklog(
                issue=issue, timeSpent='{}m'.format(round(time_spent / 60, 0)))
        else:
            print ("KEY: {}, TIME: {}h".
                   format(issue, text_type(round(time_spent / 3600, 3))))
