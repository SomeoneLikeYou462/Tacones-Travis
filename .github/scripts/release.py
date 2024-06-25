#!/usr/bin/env python
# coding: utf-8
# Author: Roman Miroshnychenko aka Roman V.M.
# E-mail: romanvm@yandex.ua
# License: GPL v.3 <http://www.gnu.org/licenses/gpl-3.0.en.html>
"""
Deploy Kodi addons to GitHub repository and/or publish Sphinx docs to GitHub Pages
"""

from __future__ import print_function
import re
import os
import sys
import json
import shutil
import argparse
from subprocess import call
from xml.etree.ElementTree import ElementTree as ET

USER_NAME = os.environ.get('USER_NAME', '')
USER_EMAIL = os.environ.get(
    'USER_EMAIL', '')
DEVNULL = open(os.devnull, 'w')
GH_TOKEN = os.environ.get('GH_TOKEN', '')
PYV = sys.version_info[0]
DIST_DIR = "dist"

# Utility functions


def execute(args, silent=False):
    if silent:
        stdout, stderr = DEVNULL, DEVNULL
    else:
        stdout, stderr = sys.stdout, sys.stderr

    call_string = ' '.join(args).replace(GH_TOKEN, '*****')
    print('Executing: ' + call_string)
    res = call(args, stdout=stdout, stderr=stderr)

    if res:
        raise RuntimeError('Call {call} returned error code {res}'.format(
            call=call_string,
            res=res
        ))


def clean_pyc(folder):
    cwd = os.getcwd()
    os.chdir(folder)
    paths = os.listdir(folder)

    for path in paths:
        abs_path = os.path.abspath(path)
        if os.path.isdir(abs_path):
            clean_pyc(abs_path)
        elif path[-4:] == '.pyc':
            os.remove(abs_path)
    os.chdir(cwd)


def create_zip(zip_name, root_dir, addon):
    clean_pyc(root_dir)
    shutil.make_archive(zip_name, 'zip', root_dir=root_dir, base_dir=addon)
    print('ZIP created successfully.')


# Argument parsing
parser = argparse.ArgumentParser(
    description='Deploy an addon to my Kodi repo and/or publish docs on GitHub Pages')
parser.add_argument(
    '-r', '--repo', help='push to my Kodi repo', action='store_true')
parser.add_argument(
    '-d', '--docs', help='publish docs to GH pages', action='store_true')
parser.add_argument(
    '-z', '--zip', help='pack addon into a ZIP file', action='store_true')
parser.add_argument('addon', nargs='?', help='addon ID',
                    action='store', default='')
parser.add_argument('-k', '--kodi', nargs=1,
                    help='the name of Kodi addon repo')
parser.add_argument('-b', '--branch', nargs=1,
                    help='the name of a branch in the Kodi addon repo', default='krypton')
parser.add_argument('-v', '--version', nargs='?',
                    help='writes the addon version [as read from xml] to the specified file (defaults to "version")', default='version')
parser.add_argument('-m', '--metadata',
                    help='Sends to the GitHub action the required information', action='store_true')
args = parser.parse_args()

# Define args
if not args.addon:
    addon = os.environ.get('ADDON', '')
else:
    addon = args.addon

if not args.version:
    args.version = 'version'

# Define auxiliary variables
repo_name = os.environ.get('ADDON_REPOSITORY', '')
repo_slug = "{}/{}".format(USER_NAME, repo_name)

# Define paths
root_dir = os.path.dirname(os.path.abspath(__file__))
if ".github" in root_dir:
    root_dir = root_dir.split(".github")[0]
kodi_repo_dir = os.path.join(root_dir, repo_name)
docs_dir = os.path.join(root_dir, 'docs')
html_dir = os.path.join(docs_dir, '_build', 'html')

# Get add-on version from XML
xml = ET().parse(os.path.join(root_dir, 'addon.xml'))
version = xml.get("version")

if not addon:
    addon = xml.get("id")

addonName = re.sub(r"(\[[^\]]+\])", "", xml.get("name")).title()

# Define ZIP locations
zip_name = os.path.join(DIST_DIR, "%s-%s" %
                        (addon, version))
zip_path = os.path.join(root_dir, zip_name + '.zip')

# Define URLs
REPO_URL_MASK = 'https://{username}:{gh_token}@github.com/{repo_slug}.git'
gh_repo_url = REPO_URL_MASK.format(
    username=USER_NAME.lower(), gh_token=GH_TOKEN, repo_slug=repo_slug)
kodi_repo_url = REPO_URL_MASK.format(
    username=USER_NAME.lower(), gh_token=GH_TOKEN, repo_slug=repo_slug)

# Start working
os.chdir(root_dir)


def get_files():
    """ Get a list of files that we should package. """
    # Start with all non-hidden files
    files = [f for f in os.listdir() if not f.startswith('.')]

    # Exclude files from .gitattributes
    with open('.gitattributes', 'r') as f:
        for line in f.read().splitlines():
            filename, mode = line.split(' ')
            filename = filename.strip('/')
            if mode == 'export-ignore' and filename in files:
                files.remove(filename)

    # Exclude files from .gitignore. I know, this won't do matching
    with open('.gitignore', 'r') as f:
        for filename in f.read().splitlines():
            filename = filename.strip('/')
            if filename in files:
                files.remove(filename)

    return files


if not os.path.isdir(DIST_DIR):
    os.mkdir(DIST_DIR)

dest = os.path.join(DIST_DIR, addon)
if not os.path.isdir(dest):
    os.mkdir(dest)


if args.version:
    _path = os.path.join(root_dir, args.version)
    with open(_path, "w") as file:
        file.write(version)

if args.zip:
    for f in get_files():
        if os.path.isfile(f):
            shutil.copy(f, dest)
        else:
            shutil.copytree(f, os.path.join(dest, f), dirs_exist_ok=True)
    shutil.make_archive(zip_name, 'zip', DIST_DIR, addon)

if args.repo:
    if not os.path.exists(zip_path):
        create_zip(zip_name, root_dir, addon)

    if not os.path.exists(kodi_repo_dir) or \
       not os.path.exists(os.path.join(kodi_repo_dir, '.git')):
        execute(['git', 'clone', kodi_repo_url])

    # Sin sentido
    # else:
    #     execute(['git', 'pull'])

    os.chdir(kodi_repo_dir)
    execute(['git', 'remote', 'set-url', 'origin', kodi_repo_url])
    # execute(['git', 'checkout', 'gh-pages'])
    execute(['git', 'config', 'user.name', USER_NAME])
    execute(['git', 'config', 'user.email', USER_EMAIL])
    # addon_repo = os.path.join(kodi_repo_dir, 'repo', addon)
    addon_repo = os.path.join(kodi_repo_dir, addon)

    if not os.path.exists(addon_repo):
        os.mkdir(addon_repo)

    shutil.copy(zip_path, addon_repo)
    shutil.copy(os.path.join(root_dir, 'addon.xml'), addon_repo)

    # os.chdir(os.path.join(kodi_repo_dir, 'repo'))
    execute(['pip%s' % PYV, 'install', 'lxml'])
    os.chdir(kodi_repo_dir)
    execute(['python', 'repo_prep.py'])
    os.chdir(kodi_repo_dir)

    execute(['git', 'add', '--all', '.'])
    execute(['git', 'commit', '-m',
            ':sparkles: Update {addon} to v.{version}'.format(addon=addon, version=version)])
    execute(['git', 'push', '--force'])

    print('Addon {addon} v{version} deployed to Kodi repo'.format(
        addon=addon, version=version))

if args.metadata:
    print(json.dumps(
        {"version": version, "name": addonName, "id": addon, "dest": dest}))
