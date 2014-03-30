#! /Users/rem63/venvs/atmosci/bin/python

import os
from datetime import datetime

from nrcc.utils.report import reportPerformance
from nrcc.utils.string import tupleFromString

from nrcc.stations.manager import StationDataFileManager
from nrcc.stations.builder import StationDataFileBuilder
from nrcc.stations.scripts.factory import StationDataManagerFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from nrcc.config import STATIONS

DEFAULT_ELEMENTS = ( {'name':'pcpn', 'add':['f','t']},
                     {'name':'maxt', 'add':['f','t']},
                     {'name':'mint', 'add':['f','t']},
                   )
DEFAULT_METADATA = 'uid,name,ll,elev'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-a', action='store', type='string', dest='max_attempts',
                  default=5)
parser.add_option('-e', action='store', type='string', dest='elements',
                  default=DEFAULT_ELEMENTS)
parser.add_option('-m', action='store', type='string', dest='metadata',
                  default=DEFAULT_METADATA)
parser.add_option('-o', action='store', type='string', dest='station_filepath',
                  default=None)
parser.add_option('-r', action='store', type='string', dest='region',
                  default='EOR', help="Region.")
parser.add_option('-u', action='store', type='string', dest='base_url',
                  default=STATIONS.download_url)
parser.add_option('-x', action='store_true', dest='replace_existing',
                  default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)
options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

start_perf = datetime.now()

if len(args) > 0:
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
else:
    today = datetime.now()
    year = today.year
    month = today.month
    day = today.day
date = (year,month,day)

factory = StationDataManagerFactory(date, options)
station_filepath = factory.getFilepath('stations')

if os.path.exists(station_filepath):
    replace_existing = options.replace_existing
    if replace_existing:
        os.remove(station_filepath)
    else:
        print 'INFO:', station_filepath, 'already exists.'
        exit()

if type(options.elements) in (dict,tuple,list):
    elements = options.elements
else:
    elements = tupleFromString(options.elements)
metadata = tupleFromString(options.metadata)
file_attributes = { 'bbox':factory.region_bbox, 'data_bbox':factory.data_bbox }

builder = StationDataFileBuilder(StationDataFileManager, station_filepath,
                                 elements, metadata, options.base_url,
                                 file_attributes)
builder(date, factory.region.states, options.max_attempts, debug=options.debug,
        performance=True)

msg = 'Total time to build station cache file ='
reportPerformance(datetime.now()-start_perf, msg)

