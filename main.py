"""
The main part of script.
Designed for adding necessary time in jira by activity user for the current day.
It takes all activity from jira (changed status of issue, added comment,
created issue, issue which status was in development) and logged time.
If logged time in sum less then need,
it distributed according to AVAILABLE_ACTIONS_WITH_WEIGHT.
All distribution occurs in two phases.
In the first phase time added in issue which hasn`t logged time or if
logged time less than weight.
And in the second phase divides rest time to issue,
which hasn`t logged time by user or for all issues.
"""
from __future__ import division

import argparse
import configparser
import getpass
import logging
import sys

# from tabulate import tabulate

from managers.jira import JiraManager
from managers.stash import StashManager
from models.activity import AVAILABLE_ACTIONS_WITH_WEIGHT, STATUS_STASH


def get_settings(file, section=None):
    """
    Returns settings
    :param section:
    :return:
    """
    config = configparser.ConfigParser()
    config.read(file)
    if section:
        return config[section]
    else:
        return config


settings = get_settings('settings.txt', 'main')


logging.basicConfig(filename=settings['logger_file'], level=logging.DEBUG)
logger = logging.getLogger(__name__)


def run():
    """
    The main function.
    :return:
    """
    auth_param = _parse_incoming_argument()
    if not auth_param:
        return

    user, passwd, repo, save_log = auth_param

    try:
        jira_manager = JiraManager(user, passwd)
        stash_manager = StashManager(user, passwd, repo)
    except Exception as err:
        logger.error(err)
        return 'Wrong jira or stash authorize'

    jira_activities = jira_manager.get_all_acivities()
    logger.info('Jira activities: %s', jira_activities)
    stash_activities = stash_manager.get_list_user_branches()
    logger.info('Stash activities: %s', stash_activities)
    activities = jira_activities + stash_activities
    if not activities:
        logger.info('Don`t found activities')
        return "no activity"
    # _print_table_activities(activities)

    sum_logged_time = sum([int(i.worklog) for i in activities
                           if int(i.worklog) > 0])
    need_logged_time = int(settings['need_logged_time'])
    logger.info('Sum logged time by user: %s', sum_logged_time)
    if sum_logged_time >= need_logged_time:
        logger.info('All time are logged')
        return 'all time are logged'

    issue_with_logged_and_weight = {}
    sum_weight = 0
    for activity in activities:
        issue_with_logged_and_weight.setdefault(activity.key,
                                                {'weight': 0, 'worklog': 0})

        activity_weight = int(AVAILABLE_ACTIONS_WITH_WEIGHT.
                              get(activity.name, 0))
        if activity.name == STATUS_STASH:
            activity_weight *= activity.changed_lines

        issue_with_logged_and_weight[activity.key]['weight'] += activity_weight
        # sum all weight in available activity for get 100%
        sum_weight += activity_weight

        if activity.worklog > 0:
            issue_with_logged_and_weight[activity.key]['worklog'] += \
                activity.worklog

    weight_one_part = _get_weight_one_part(sum_logged_time, sum_weight)
    logger.info('Weight of one part: %s', weight_one_part)
    changed_issues = {}
    for key, value in issue_with_logged_and_weight.items():
        if value['weight'] == 0:
            del issue_with_logged_and_weight[key]
            continue

        part_time = round(value['weight'] * weight_one_part, 0)
        if value['worklog'] >= part_time:
            continue

        logger.info("LOGGED KEY: {}, TIME: {}m".
                    format(key, round(part_time / 60, 2)))
        jira_manager.add_worklog(key, part_time, save_log)
        sum_logged_time += part_time
        changed_issues[key] = value

    if sum_logged_time >= need_logged_time:
        logger.info('All logged')
        return 'all done'

    issues = changed_issues or issue_with_logged_and_weight
    logger.info('Issue for second phase: %s', issues)
    weight_one_part = _get_weight_one_part(
        sum_logged_time,
        sum([int(i['weight']) for i in issues.values()])
    )
    logger.info('Weight of one part: %s', weight_one_part)
    for key, value in issues.items():
        time = round(value['weight'] * weight_one_part, 0)
        logger.info("LOGGED KEY: {}, TIME: {}m".
                    format(key, round(time / 60, 2)))
        jira_manager.add_worklog(key, time, save_log)
    logger.info('All logged')
    return


def _parse_incoming_argument():
    """
    Parse incoming argument.
    For auth in jira and stash.
    :return: user, passwd, repo, save_log or None
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('-u', action='store', dest='user',
                        type=str, help='User')
    parser.add_argument('-s', action='store', dest='stash',
                        type=str, help='Stash repository, like this: '
                                       'o.kharitonova/repos/tracking')
    parser.add_argument('-l', action='store', dest='save_log',
                        type=str, help='Add worklog in jira')
    parser.add_argument('-f', action='store', dest='file',
                        type=str, help='File with settings')

    args = parser.parse_args()
    if args.user and args.stash:
        user = args.user
        repo = args.stash
        passwd = getpass.getpass()
    elif args.file:
        user_settings = get_settings(args.file, 'auth')
        user = user_settings['user']
        passwd = user_settings['password']
        repo = user_settings['repo']
    else:
        parser.print_help()
        parser.error('Not enough arguments!')
        return
    save_log = args.save_log or False
    return user, passwd, repo, save_log


def _get_weight_one_part(logged_time, sum_weight):
    """
    Returns weight (in seconds) of one part.
    :param logged_time: int
    :param sum_weight: int
    :return: int
    """
    return (
        round((int(settings['need_logged_time']) - logged_time) / sum_weight,
              0) if sum_weight > 0 else 0
    )

#
# def _print_table_activities(activities):
#     table = []
#     for activity in activities:
#         table.append([
#             activity.key, activity.name, text_type(activity.date),
#             text_type(activity.worklog), text_type(activity.changed_lines)])
#
#     print tabulate(
#         table, headers=["KEY", "ACTIVITY", "DATE", "WORKLOG", "CHANGED LINES"])


if __name__ == '__main__':
    sys.exit(run())
