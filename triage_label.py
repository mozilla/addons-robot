import datetime
import logging
import os
import re
import requests
import sys

from utils import notify_irc

log = logging.getLogger()
handler = logging.StreamHandler(sys.stderr)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

logging.getLogger("requests").propagate = False

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

log.info('Running label.py: {}'.format(datetime.datetime.now()))

message = 'Filed by a developer so marking as triaged.'
root = 'https://api.github.com/'

developers = [
    'krupa',
    'kumar303',
    'diox',
    'andymckay',
    'eviljeff',
    'jasonthomas',
    'EnTeQuAk',
    'wagnerand',
    'tofumatt',
    'mstriemer',
    'muffinresearch',
]


issues = []

def parse_link_headers(header):
    rx = '\<(.*?)>; rel="(\w+)"(?:,)'
    return dict([(v, k) for k, v in re.findall(rx, header)])


def list_issues(location):
    # https://developer.github.com/v3/search/
    # Note this defaults to open pull requests.
    url = root + 'search/issues'
    labels = (
        'state:open+type:issue+-label:triaged+-label:"pull request ready"'
        '+-label:"in progress"+repo:{}'.format(location))
    # Because github fails when you pass these as params and escape them.
    url = url + '?q={}&sort:created'.format(labels)
    _list_issues(url)


def _list_issues(url):
    log.info('Calling: {}'.format(url))
    res = requests.get(url)
    res.raise_for_status()
    for issue in res.json()['items']:
        if issue['user']['login'] in developers:
            issues.append(issue)

    next_url = parse_link_headers(res.headers.get('link')).get('next')
    if next_url:
        _list_issues(next_url)


def triage_issue(location, issue):
    # https://developer.github.com/v3/issues/#edit-an-issue
    url = root + 'repos/{}/issues/{}'.format(location, issue['number'])
    labels = issue['labels']
    labels.append('triaged')
    res = requests.patch(
        url,
        json={'labels': labels},
        auth=(GITHUB_USERNAME, GITHUB_TOKEN)
    )
    res.raise_for_status()
    notify_irc('Triage label added to {}#{}'.format(location, issue['number']))


if __name__ == '__main__':
    location = sys.argv[1]
    assert '/' in location
    log.info('Checking: {}'.format(location))
    list_issues(location)
    for issue in issues:
        log.info('Automatic triage of: {}'.format(issue['number']))
        triage_issue(location, issue)
