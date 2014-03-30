#! /Users/rem63/venvs/atmosci/bin/python

USAGE = """%prog [options] grid_id data_key filepath

Arguments: grid_file = numeric identifier used by grid component factory to 
                       access grid information.
           data_key = name the gridded dataset to be plotted.
           filepath = path to the grid file that contains the dataset
                      to be plotted.

Defaults : output FILEPATH is constructed from grid name and data_key.
           IMAGE_FORMAT = png.
           TITLE = constructed from grid name and data_key 
"""

import os, sys
import datetime
import numpy as N

import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot

from nrcc.utils.options import getBboxFromOptions, getDataBboxFromOptions

from nrcc.stations.scripts.factory import StationDataManagerFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#APP = os.path.splitext(os.path.split(__file__)[1])[0].upper().replace('_',' ')
APP = os.path.split(sys.argv[0])[1] + ' ' + ' '.join(sys.argv[1:])
#PID = os.getpid()
PID = 'PID %d' % os.getpid()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser(usage=USAGE)
parser.add_option('-b', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('-o', action='store', type='string', dest='output_filepath',
                  default=None, help='full path for the plot image file')
parser.add_option('-r', action='store', type='string', dest='region',
                  default='EOR')
parser.add_option('-s', action='store', type='string', dest='source',
                   default='dem5k', help=' Data source.')
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None,
                  help="alternate working directory for downloaded files")
parser.add_option('-z', action='store_true', dest='debug', default=False,
                  help='show all available debug output')

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

year = int(args[0])
month = int(args[1])
day = int(args[2])
date = (year,month,day)

factory = StationDataManagerFactory(date, options)
manager = factory.getDataManager('stn')

if options.bbox is not None:
    bbox = getBboxFromOptions(options)
    manager.setLonLatBounds(bbox)

lons, lats = manager.getLonLat()
uid, attrs = manager.getRawData('uid')
name, attrs = manager.getRawData('name')
state, attrs = manager.getRawData('state')

outfile = open('station_list.txt','w')
for indx in range(len(lons)):
    line = '%d    %10.5f    %8.5f    %s, %s\n' % (uid[indx], lons[indx],
                                                  lats[indx], state[indx],
                                                  name[indx])
    outfile.write(line)
outfile.close()

