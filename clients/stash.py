import base64
import configparser
import json
import urllib2

from . import get_settings


class StashClient(object):

    def __init__(self, user, password, repo):
        self.config = get_settings('stash')
        # repo=o.kharitonova/repos/tracking
        self.base_url = '%s%s' % (self.config['base_url'], repo)
        self.user = user
        self.password = password

    def _do_request(self, url):
        """
        Send http request to stash.
        :param url: string
        :return: dictionary
        """
        result = None
        request = urllib2.Request('{0}/{1}'.format(self.base_url, url))
        base64string = base64.encodestring(
            '%s:%s' % (self.user, self.password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        try:
            f = urllib2.urlopen(request)
            result = json.loads(f.read())
        except Exception as e:
            pass

        return result

    def get_brahcnes(self):
        """
        Returns branches from user`s repository.
        Also we can set param limit in query. Default limit is 25 (we use it).
        Branches are order desc sort.
        return: list of branches
        """
        branches = self._do_request(self.config['url_branches'])
        if branches['values']:
            return branches['values']

    def get_commit(self, id):
        """
        Returns data of commit.
        :param id: string
        :return: dictionary
        """
        return self._do_request(
            '{0}/{1}'.format(self.config['url_commit'], id))

    def get_changes(self, commit_id):
        """
        Returns diff.
        :param commit_id:
        :return:
        """
        return self._do_request(
            '{0}/{1}/{2}'.format(
                self.config['url_commit'],
                commit_id,
                self.config['url_diff']
            )
        )
