#! /Volumes/projects/venvs/builds/bin/python

import os, sys
import datetime
UPDATE_START_TIME = datetime.datetime.now()

import urllib
from dateutil.relativedelta import relativedelta

import numpy as N

from atmosci.utils.timeutils import elapsedTime

from atmosci.seasonal.factory import NDFDProjectFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-a', action='store', type=int, dest='attempts', default=5)
parser.add_option('-f', action='store', dest='filetypes', default='maxt,mint')
parser.add_option('-p', action='store', dest='periods',
                        default='001-003,004-007')
parser.add_option('-w', action='store', type=int, dest='wait_time', default=10)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

attempts = options.attempts
debug = options.debug
verbose = options.verbose or debug
wait_time = options.wait_time

if ',' in options.filetypes:
    filetypes = options.filetypes.split(',')
else: filetypes = [options.filetypes,]

if ',' in options.periods:
    periods = options.periods.split(',')
else: periods = [options.periods,]


latest_time = datetime.datetime.utcnow()
target_year = latest_time.year

factory = NDFDProjectFactory()
factory.setDownloadAttempts(attempts)
factory.setDownloadWaitTime(wait_time)

target_date, filepaths, failed = \
    factory.downloadLatestForecast(filetypes=filetypes, periods=periods,
                                   debug=debug)

elapsed_time = elapsedTime(UPDATE_START_TIME, True)
fmt = '\ncompleted download for %s in %s' 
print fmt % (target_date.isoformat(), elapsed_time)
if len(filepaths) > 0:
    print 'successfully downloaded :'
    for path in filepaths: print '    ', path
if len(failed) > 0:
    print '\ndownload failed after %d attempts for :' % factory.wait_attempts
    for info in failed:
        print '    %s (%s) @ %s' % info

transport_dirpath = '/Volumes/Transport/data/app_data'
if os.path.exists(transport_dirpath):
    ndfd_dirpath = os.path.split(filepaths[0])[0]
    dest_dirpath = os.path.join(transport_dirpath, 'shared/forecast/ndfd')
    command = '/usr/bin/rsync -cgloprtuD %s %s' % (ndfd_dirpath, dest_dirpath)
    print '\n\n', command
    os.system(command)

