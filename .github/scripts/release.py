#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ----------------------------------------------------------------------
# Copyright 2023 Michaël Arnauts & Someone Like You
#
# This file is part of Astro.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.
#
# ----------------------------------------------------------------------

from __future__ import absolute_import, division, unicode_literals

import os
import re
import shutil
import json

import xml.etree.ElementTree as ET

DIST_DIR = 'dist'


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


if __name__ == '__main__':
    with open('addon.xml', 'r') as f:
        tree = ET.fromstring(f.read())
        addon_info = {
            'id': tree.get('id'),
            'name': tree.get('name'),
            'version': tree.get('version'),
            'news': tree.find("./extension[@point='xbmc.addon.metadata']/news").text
        }

    if not os.path.isdir(DIST_DIR):
        os.mkdir(DIST_DIR)

    brand = addon_info['id']
    dest = os.path.join(DIST_DIR, brand)
    if not os.path.isdir(dest):
        os.mkdir(dest)
    for f in get_files():
        if os.path.isfile(f):
            shutil.copy(f, dest)
        else:
            shutil.copytree(f, os.path.join(dest, f), dirs_exist_ok=True)
    shutil.make_archive(os.path.join(DIST_DIR, "%s-%s" %
                        (brand, addon_info['version'])), 'zip', DIST_DIR, brand)
    print(json.dumps(
        {"version": addon_info['version'], "name": re.sub(r"(\[[^\]]+\])", "", addon_info['name']), "id": addon_info['id'], "dest": dest}))
