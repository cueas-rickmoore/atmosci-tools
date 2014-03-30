#! /Users/rem63/venvs/atmosci/bin/python

import os, sys

from atmosci.base.sqlite import SqliteDatabaseManager

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

TABLE_DEF = ( ('major','INTEGER'), ('minor','INTEGER'),
              'UNIQUE (major, minor)', ('name','TEXT'),
              ('type','TEXT'), ('sample_frequency','TEXT'),
              ('report_frequency','TEXT'), ('units','TEXT'),
              ('network','TEXT'), ('description','TEXT'),)
TABLE_NAME = 'elements'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-d', action='store', type='string', dest='db_filepath',
    default='major_minor_map.sqlite')
parser.add_option('-z', action='store_true', dest='debug', default=False,
                  help='show all available debug output')
options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

db_filepath = os.path.abspath(options.db_filepath)
if os.path.exists(db_filepath): os.remove(db_filepath)
db_manager = SqliteDatabaseManager(db_filepath)
db_manager.createTable(TABLE_NAME, TABLE_DEF)
db_manager.createIndex('major', TABLE_NAME) 
db_manager.createIndex('network', TABLE_NAME) 

src_filepath = os.path.abspath(args[0])
src_file = open(src_filepath,'r')

line = src_file.readline()
while line:
    columns = line.strip().split('|')
    major = int(columns[0])
    minor = int(columns[1])
    description, type_, sample_freq, report_freq, units = columns[2:7]
    network = columns[7]
    if ':' in network: network, name = network.split(':')
    else: name = ''

    data = (major, minor, name, type_, sample_freq, report_freq, units,
            network, description)
    db_manager.addRecord(TABLE_NAME, data)
    db_manager.commit()

    line = src_file.readline()

