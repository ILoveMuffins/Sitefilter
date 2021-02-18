#!/usr/bin/env python

import itertools
import requests
import os
import sys
import time

from urllib.parse import urlencode


def readfile(name):
    with open(name, 'r') as f:
        return f.readlines()


PROXIES = {
    'http': 'http://127.0.0.1:8081',
    'https': 'http://127.0.0.1:8081',
}
SEARCH_ENGINE_ID = ''
API_KEY = ''
MAX_PAGES = 5
SITEFILTER_TMP_DIR = '/tmp/sitefilter'
GOOGLE_RESULTS_FILE_PATH = f'{SITEFILTER_TMP_DIR}/google-results'
EXCLUDED = [
    '-inurl:stackoverflow', '-inurl:serverfault', '-inurl:edu.au', '-inurl:github', '-inurl:quora', '-inurl:elsevier', '-inurl:ebay',
    '-inurl:arxiv', '-inurl:stackexchange', '-inurl:ieee', '-inurl:readthedocs', '-inurl:youtube', '-inurl:wikipedia', '-inurl:yahoo',
    '-inurl:stanford', '-inurl:psu.edu', '-inurl:ac.uk', '-inurl:readthedocs.io', '-inurl:medium', '-inurl:apache', '-inurl:techtarget',
    '-inurl:facebook', '-inurl:linkedin', '-inurl:amazon', '-inurl:google', '-inurl:twitter', '-inurl:reddit', '-inurl:github',
    '-inurl:pinterest', '-inurl:chomikuj', '-inurl:ncbi',
    '-inurl:edu', '-inurl:gov',  # very wide
]
PATH = sys.path[0]
BANNED_PHRASES = readfile(f'{PATH}/banned-phrases.txt')


def main():
    site_title = {}
    query = ' '.join(itertools.chain(sys.argv[1:], EXCLUDED))
    print(f'[*] query: "{query}"')
    print(f'[*] len(query): {len(query)}')

    for page_nr in range(1, MAX_PAGES + 1):
        start = (page_nr - 1) * 10 + 1
        try:
            data = google_search(query, API_KEY, SEARCH_ENGINE_ID, start=start)
        except Exception as e:
            print('[*] Exc:', e)
            break

        if 'items' not in data:
            print('[*] There is no "items" key:', data)
            break

        for item in data["items"]:
            title = item.get('title')
            site = item['displayLink']
            if site.startswith('www'):
                site = site.partition('.')[-1]

            dot_cnt = site.count('.')
            if dot_cnt > 3:
                splitted = site.split('.')
                cutted = splitted[-4:]
                site = '.'.join(cutted)
            if not any(banned in title for banned in BANNED_PHRASES):
                site_title[site] = title

    save_sites_to_file(site_title.keys())


def google_search(query, api_key, cse_id, **kwargs):
    url = 'https://customsearch.googleapis.com/customsearch/v1?'
    params = urlencode({'key': api_key, 'cx': cse_id, 'q': query, **kwargs})
    url += params
    fail_no = 0

    while True:
        try:
            response = requests.get(url, proxies=PROXIES)
        except Exception as e:
            print('Exception', e)
            return None

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            print('[*] HTTP code:', response.status_code)
            if response.status_code != 503:
                print(e)
                raise
        else:
            return response.json()

        # 503 error -> retry
        time.sleep(.5)
        fail_no += 1
        if fail_no > 3:
            print('[*] HTTP 503 Exception')
            return {}


def save_sites_to_file(sites):
    if sites:
        if not os.path.isdir(SITEFILTER_TMP_DIR):
            # create dir if does not exist
            os.makedirs(SITEFILTER_TMP_DIR)

        with open(GOOGLE_RESULTS_FILE_PATH, 'w') as f:
            for site in sites:
                f.write(f'{site}\n')


if __name__ == '__main__':
    main()

"""
# useful links
CSE: https://cse.google.com/cse/setup/basic?cx=007953257871078349415:e01uapwh5pm
API: https://console.developers.google.com/apis/credentials/key/405d5f63-e1fc-47da-85e5-68071b9f4004?authuser=0&project=search-results-1593847065428&pli=1
# problem - 0 results, solution:
https://stackoverflow.com/questions/37083058/programmatically-searching-google-in-python-using-custom-search
"""
