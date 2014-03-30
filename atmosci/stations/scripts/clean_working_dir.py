#! /Users/rem63/venvs/atmosci/bin/python

import os, sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

from nrcc.stations.scripts.factory import StationDataManagerFactory

from nrcc.utils.time import lastDayOfMonth

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

#APP = os.path.splitext(os.path.split(__file__)[1])[0].upper().replace('_',' ')
APP = os.path.split(sys.argv[0])[1] + ' ' + ' '.join(sys.argv[1:])
#PID = os.getpid()
PID = 'PID %d' % os.getpid()

ONE_DAY = relativedelta(days=1)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

# processing script data configuration options
parser.add_option('-r', action='store', type='string', dest='region',
                  default=None)
parser.add_option('-z', action='store_true', dest='debug', default=False)
options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

year = int(args[0])
if len(args) > 1: months = [int(arg) for arg in args[1:]]
else: months = [month for month in range(1,13)]
dates = [ ]
for month in months:
    date = datetime(year, month, 1)
    end_date = datetime(year, month, lastDayOfMonth(year, month))
    while date <= end_date:
        dates.append(date)
        date += ONE_DAY
if options.debug: print dates

factory = StationDataManagerFactory(dates[0], options)
cleaner = factory.getDirectoryCleaner()
cleaner(dates, options.region, options.debug)

