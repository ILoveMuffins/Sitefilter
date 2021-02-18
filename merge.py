#!/usr/bin/env python3

import collections
import concurrent.futures as futures
import os


SITEFILTER_TMP_DIR = '/tmp/sitefilter'
UNIQUE_SITES_FILE_PATH = f'{SITEFILTER_TMP_DIR}/unique-sites'
EXCLUDED_SITES_FILE_PATH = f'{SITEFILTER_TMP_DIR}/excluded-sites'
SITE_CANDIDATES_FILE_PATH = f'{SITEFILTER_TMP_DIR}/google-results'
MERGE_FILE = f'/home/{os.environ["USER"]}/Projects/sitefilter/rest2'

FILES = """
books
cnc
dictionaries
economy
exceptionsitelist
informatics
informatics2
math
radio
recipes
rest
rest2
spiritual
to-sort-0
to-sort-1
""".split()

EXCLUDED_PHRASES = """
4chan
abcnews
aliexpress
alibaba
allegro
amazon
arvix.org
audio
bbc
blogspot
book
buy
chomikuj
cosplay
czyta
dailymotion
demotywatory
discord
disboard
ebay
eska
etsy
facebook
fakt.pl
film
flickr
gallery
github
giphy
google
health
herokuapp
image
imdb
instagram
interia
issuu
ksiazk
media
nationalgeographic
msn.com
newsweek
nk.pl
onet.
photo
pics
picture
pinterest
psu.ed
pudelek
readthedocs
reddit
shop
shutterstock
slide
smog.pl
sport
stack
steemit
travel
trip
tube
tumblr
tv
twitter
usc.edu
vimeo
vk.com
yandex
youtube
walmart
wizaz
wordpress
wp.pl
wyborcza
""".split()

ALREADY_INCLUDED_SUFFIXES = """
ac.at
ac.bd
ac.be
ac.cn
ac.cy
ac.fj
ac.id
ac.il
ac.in
ac.ir
ac.jp
ac.ke
ac.kr
ac.lk
ac.ma
ac.nz
ac.rs
ac.rs
ac.ru
ac.rw
ac.ss
ac.th
ac.tz
ac.ug
ac.uk
ac.za
ar.al
bl.uk
c2.com
edu.pl
europa.eu
go.jp
inria.fr
gov.pl
nj.us
sap.com
uc.pt
uu.nl
waw.pl
zendesk.com
""".split()

LSTRIP_PHRASES = """
blog.
bugs.
dev.
discuss.
doc.
docs.
forum.
forums.
ftp.
git.
jira.
mail.
man.
mirror.
mirrors.
py.
src.
support.
wiki.
""".split()


def main():
    if not os.path.isdir(SITEFILTER_TMP_DIR):
        os.makedirs(SITEFILTER_TMP_DIR)

    if (
        not os.path.isfile(UNIQUE_SITES_FILE_PATH) or
        not os.path.isfile(EXCLUDED_SITES_FILE_PATH)
    ):
        create_cache_files()

    sites, excluded = get_from_cache()
    candidates = read_set(SITE_CANDIDATES_FILE_PATH)
    open(SITE_CANDIDATES_FILE_PATH, 'w').close()  # clear this file
    no_duplicates = candidates - sites - excluded

    with open(MERGE_FILE, 'a') as f, open(UNIQUE_SITES_FILE_PATH, 'a') as g:
        for site in no_duplicates:
            # end `site` processing conditions
            if any(site.endswith(sufix) for sufix in ALREADY_INCLUDED_SUFFIXES):
                break
            if any(exc in site for exc in EXCLUDED_PHRASES):
                print(f'[-] In excluded:', site)
                break

            # add `site` to exception list file
            print(f'[+] Adding site: {site}')
            txt = f'{site}\n'
            f.write(txt)
            g.write(txt)


def create_cache_files():
    sites, excluded = set(), set()

    with futures.ThreadPoolExecutor(max_workers=len(FILES)) as executor:
        files_future = set(executor.submit(read_file, _file) for _file in FILES)

        for future in futures.as_completed(files_future):
            _sites, _excluded = future.result()
            sites.update(_sites)
            excluded.update(_excluded)

    with open(UNIQUE_SITES_FILE_PATH, 'w') as f:
        for site in sites:
            f.write(f'{site}\n')

    with open(EXCLUDED_SITES_FILE_PATH, 'w') as f:
        for exc in excluded:
            f.write(f'{exc}\n')


def read_file(_file):
    sites, excluded = set(), set()

    with open(_file, 'r') as file_:
        for line in file_:
            line = line.strip()
            if line:
                if line.startswith('#'):
                    line = line.strip('#').split()
                    if line:
                        excluded.add(line[0])
                else:
                    line = line.split()
                    sites.add(line[0])

    return sites, excluded


def get_from_cache():
    sites = read_set(UNIQUE_SITES_FILE_PATH)
    excluded = read_set(EXCLUDED_SITES_FILE_PATH)
    return sites, excluded


def read_set(fname):
    with open(fname, 'r') as f:
        lines = f.readlines()

    http_prefix, https_prefix = 'http://', 'https://'
    http_pref_len, https_pref_len = len(http_prefix), len(https_prefix)

    sites = set()
    for line in lines:
        line = line.strip().lower()
        if line.startswith('http'):
            line = line[line.startswith(http_prefix) and http_pref_len :]
            line = line[line.startswith(https_prefix) and https_pref_len :]

        sites.add(line)

    # clear every `site` from deduplicated collection (set)
    rtn = set()
    for site in sites:
        for phrase in LSTRIP_PHRASES:
            if site.startswith(phrase) and site.count('.') > 1:
                print(f'[*] Removing "{phrase}" from site: "{site}"')
                site = site.removeprefix(phrase)
                break
        rtn.add(site)

    print()  # newline
    return rtn


if __name__ == '__main__':
    main()
