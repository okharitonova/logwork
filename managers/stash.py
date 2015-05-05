"""
Stash manager.
Returns count changed lines (added, deleted) by issue on current day
"""

from datetime import datetime

from clients.stash import StashClient
from models.activity import Activity, STATUS_STASH


class StashManager:

    def __init__(self, user, password, repo):
        self.stash_client = StashClient(user, password, repo)

    def get_list_user_branches(self):
        activities = []
        branches = self.stash_client.get_brahcnes()
        if branches:
            for branch in branches:
                # get commits and check the date,
                # because branches don`t contain a date
                commit = self.stash_client.get_commit(
                    branch['latestChangeset'])
                date = datetime.fromtimestamp(commit['authorTimestamp'] / 1000)
                if (date.date() < datetime.today().date() or
                        not commit.get('attributes', None)):
                    break

                changes = self.stash_client.get_changes(
                    branch['latestChangeset'])
                if not changes['diffs']:
                    continue

                count_lines_changes = 0
                for diff in changes['diffs']:
                    for hunk in diff['hunks']:
                        for segment in hunk['segments']:
                            if segment['type'] != 'CONTEXT':
                                count_lines_changes += len(segment['lines'])

                activity = Activity(
                    commit['attributes']['jira-key'].pop(),
                    name=STATUS_STASH,
                    date=date,
                    changed_lines=count_lines_changes)

                activities.append(activity)

        return activities

