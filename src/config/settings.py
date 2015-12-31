import os

CACHE_DIR = os.path.abspath('./cache')
LOGS_DIR = os.path.abspath('./logs')


def get_cache(filename):
    return os.path.join(CACHE_DIR, filename)
