import datetime
import logging
import os
import sys

from utils import notify_irc

import requests

log = logging.getLogger()
handler = logging.StreamHandler(sys.stderr)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

logging.getLogger("requests").propagate = False

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

log.info('Running close.py: {}'.format(datetime.datetime.now()))
before = datetime.date(2016,5,1)

message = (
 "Thank you for submitting your pull request. However pull requests are not "
 "accepted on github as per the contribution guidelines. Please use Bugzilla "
 "to submit patches instead: https://github.com/{}/blob/master/CONTRIBUTING.md"
)

repos = 'https://api.github.com/repos/'

def list_pull_requests(location):
    # https://developer.github.com/v3/pulls/
    # Note this defaults to open pull requests.
    url = repos + '{}/pulls'.format(location)
    log.debug(url)
    res = requests.get(url)
    res.raise_for_status()
    pull_requests = []
    for pull_request in res.json():
        created = datetime.datetime.strptime(
            pull_request['created_at'][:19],
            '%Y-%m-%dT%H:%M:%S')
        # Strip out pull requests created before this date.
        if created.date() > before:
            pull_requests.append(pull_request)

    return pull_requests


def close_pull_request(location, pull):
    # https://developer.github.com/v3/issues/comments/#create-a-comment
    url = repos + '{}/issues/{}/comments'.format(location, pull['number'])
    log.debug(url)
    res = requests.post(
        url,
        json={'body': message.format(location)},
        auth=(GITHUB_USERNAME, GITHUB_TOKEN)
    )
    res.raise_for_status()
    # https://developer.github.com/v3/pulls/#update-a-pull-request
    url = repos + '{}/pulls/{}'.format(location, pull['number'])
    log.debug(url)
    res = requests.patch(
        url,
        json={'state': 'closed'},
        auth=(GITHUB_USERNAME, GITHUB_TOKEN)
    )
    res.raise_for_status()
    notify_irc('Closed pull request {}#{}'.format(location, pull['number']))


if __name__ == '__main__':
    location = sys.argv[1]
    assert '/' in location
    log.info('Checking: {}'.format(location))
    pulls = list_pull_requests(location)
    log.info('Found: {} pull requests since {}'.format(len(pulls), before))
    for pull in pulls:
        close_pull_request(location, pull)
        log.info('Successfully closed pull request: {}'.format(pull['number']))
