import contextlib
import datetime
import json
import logging
import os
import requests
import shutil
import sys
import time

log = logging.getLogger('pull')
handler = logging.StreamHandler(sys.stderr)
log.addHandler(handler)
log.setLevel(logging.DEBUG)

project_root = 'other_projects'
source_root = 'gecko-dev'
source_repo = 'git@github.com:mozilla/gecko-dev.git'
dest_root = 'webextension-schema'
dest_repo = 'https://addons-robot@github.com/andymckay/webextension-schema.git'

dir_mapping = [
    [
        os.path.join(source_root, 'toolkit/components/extensions/schemas'),
        os.path.join(dest_root, 'gecko/toolkit'),
    ],
    [
        os.path.join(source_root, 'browser/components/extensions/schemas'),
        os.path.join(dest_root, 'gecko/browser'),
    ],
    [
        os.path.join(source_root, 'mobile/android/components/extensions/schemas'),
        os.path.join(dest_root, 'gecko/mobile'),
    ]
]

GITHUB_USERNAME = os.getenv('GITHUB_USERNAME')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')


def git(cmd):
    log.debug('git cmd: {}'.format(cmd))
    return os.popen('git {}'.format(cmd)).readlines()


def make_pull_request(commit, uid):
    url = 'https://api.github.com/repos/andymckay/webextension-schema/pulls'
    res = requests.post(
        url,
        json={
            'title': 'add-ons robot updates from mozilla-central',
            'head': 'addons-robot:changes-{}'.format(uid),
            'base': 'master',
            'body': 'Updates from mozilla-central on {}'.format(
                datetime.datetime.today().date())
        },
        auth=(GITHUB_USERNAME, GITHUB_TOKEN)
    )
    res.raise_for_status()
    log.debug('pull request created')


@contextlib.contextmanager
def temp_chdir(path):
    starting_directory = os.getcwd()
    try:
        log.info('cd {}'.format(path))
        os.chdir(path)
        yield
    finally:
        os.chdir(starting_directory)


def setup():
    with temp_chdir(project_root):
        if not os.path.exists(source_root):
            git('clone {}'.format(source_repo))

    with temp_chdir(os.path.join(project_root, source_root)):
        git('pull')

    with temp_chdir(project_root):
        if not os.path.exists(dest_root):
            git('clone {}'.format(dest_repo))
            git('config user.name "Addons Robot"')
            git('config user.email "addons-dev-automation+github@mozilla.com"')
            git('remote add addons-robot git@github.com:addons-robot/webextension-schema.git')

    with temp_chdir(os.path.join(project_root, dest_root)):
        git('pull')


def copy_files():
    for src_dir, dest_dir in dir_mapping:
        for root, dirname, filenames in os.walk(os.path.join(project_root, src_dir)):
            for filename in filenames:
                full = os.path.join(root, filename)
                if full.endswith('.json'):
                    shutil.copy(full, os.path.join(project_root, dest_dir))


def bump_version():
    # Note: assumes already in this dir.
    data = json.load(open('package.json', 'r'))
    x, y, z = data['version'].split('.')
    data['version'] = '{}.{}.{}'.format(x, int(y)+1, z)
    json.dump(data, open('package.json', 'w'), indent=2)


def make_commit(target, uid):
    with temp_chdir(os.path.join(project_root, dest_root)):
        stdout = git('status --porcelain')
        changed = False

        for line in stdout:
            if line.startswith('??'):
                git('add {}'.format(line[3:]))
            if line.startswith(' M'):
                git('add {}'.format(line[3:]))
            changed = True

        if changed:
            bump_version()
            git('branch changes-{}'.format(uid))
            git('checkout changes-{}'.format(uid))
            git('commit -m "changes from addons-robot {}" -a'.format(uid))
            git('push {} changes-{}'.format(target, uid))
            git('checkout master')
            return True

    return False


if __name__ == '__main__':
    uid = str(int(time.time()))
    setup()
    copy_files()
    commit = make_commit('addons-robot', uid)
    if commit:
        make_pull_request(commit, uid)
