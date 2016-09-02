import datetime
import logging
import os
import sys

from utils import notify_irc, parse_link_headers

import requests

log = logging.getLogger()
handler = logging.StreamHandler(sys.stderr)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

logging.getLogger("requests").propagate = False

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

log.info('Running deploy_comment.py: {}'.format(datetime.datetime.now()))
repos = 'https://api.github.com/repos/'
myself = 'addons-robot'

message = ('This has been deployed to our '
'[development server](https://addons-dev.allizom.org). Please see '
'[push duty](https://addons.readthedocs.io/en/latest/server/push-duty.html) '
'for when it will be deployed to production.')


class AlreadyCommented(Exception):
    pass


def has_commented(url):
    log.debug(url)
    res = requests.get(url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
    res.raise_for_status()
    for comment in res.json():
        if myself in comment['user']['login']:
            raise AlreadyCommented()

    next_url = parse_link_headers(res.headers.get('link', '')).get('next')
    if next_url:
        has_commented(next_url)


def list_pull_requests(location):
    # https://developer.github.com/v3/pulls/
    url = repos + '{}/pulls'.format(location)
    url = url + '?state=closed'

    res = requests.get(url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
    res.raise_for_status()
    pull_requests = []
    for pull_request in res.json():
        # Don't comment on pull requests that weren't merged.
        # https://github.com/mozilla/addons-bots/issues/9
        if not pull_request['merged_at']:
            log.info('No merge, ignoring.')
            continue

        # Note we aren't going to try and paginate through the list, we'll
        # assume that the last 20 pull requests will usually suffice.
        try:
            has_commented(pull_request['_links']['comments']['href'])
        except AlreadyCommented:
            log.info('Already commented, ignoring.')
            continue

        pull_requests.append(pull_request)

    return pull_requests


def check_deployed(pull, commit_hash, commits_since):
    commit = pull['merge_commit_sha']
    if not commit:
        return False

    # Would commit_hash == commit ever happen?
    if (commit_hash in commits_since) or (commit_hash == commit) :
        # Its been deployed, rejoice.
        return True

    return False


def get_commits(location, endpoint):
    log.debug(endpoint)
    res = requests.get(endpoint)
    res.raise_for_status()
    commit_hash = res.json()['version']

    url = repos + '{}/commits?sha={}&per_page=100'.format(location, commit_hash)
    log.debug(url)
    res = requests.get(url, auth=(GITHUB_USERNAME, GITHUB_TOKEN))
    res.raise_for_status()

    commits_since = set([commit['sha'] for commit in res.json()])
    return commit_hash, commits_since


def comment_on_pull_request(location, pull):
    # https://developer.github.com/v3/issues/comments/#create-a-comment
    url = repos + '{}/issues/{}/comments'.format(location, pull['number'])
    log.debug(url)
    res = requests.post(
        url,
        json={'body': message},
        auth=(GITHUB_USERNAME, GITHUB_TOKEN)
    )
    res.raise_for_status()


if __name__ == '__main__':
    location = sys.argv[1]
    assert '/' in location
    endpoint = sys.argv[2]
    assert endpoint.startswith('https://')

    log.info('Checking: {}'.format(location))

    pulls = list_pull_requests(location)
    log.info('Found: {} pull requests'.format(len(pulls)))
    commit_hash, commits_since = get_commits(location, endpoint)
    log.info('Found version on server and last 100 commits.')

    for pull in pulls:
        if check_deployed(pull, commit_hash, commits_since):
            comment_on_pull_request(location, pull)
            notify_irc('Commented on pull request: {}'.format(pull['number']))
            log.info('Commented on pull request: {}'.format(pull['number']))
        else:
            log.info('Pull request not deployed: {}'.format(pull['number']))