#!/usr/bin/python

import os
import pymarc

path = '/path/to/dir/with/xmlfiles/'

def get_place_of_pub(record):
    try:
        place_of_pub = record['260']['a']
        print place_of_pub
    except Exception as e:
        print e

for file in os.listdir(path):
    if file.endswith('.xml'):
        pymarc.map_xml(get_place_of_pub, path + file)
