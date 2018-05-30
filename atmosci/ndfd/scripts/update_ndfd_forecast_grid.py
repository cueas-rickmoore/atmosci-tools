#! /Volumes/Transport/venvs/atmosci/bin/python
#! /usr/bin/env python
#
# Copyright (c) 2007-2018 Rick Moore and Cornell University Atmospheric
#                         Sciences
# All Rights Reserved
# Principal Author : Rick Moore
#
# ndfd is part of atmosci - Scientific Software for Atmosphic Science
#
# see copyright.txt file in this directory for details

import os, sys
import warnings

import datetime
ONE_DAY = datetime.timedelta(days=1)
UPDATE_START_TIME = datetime.datetime.now()

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.timeutils import elapsedTime, nextMonth
from atmosci.utils.units import convertUnits

from atmosci.ndfd.factory import NdfdGridFileFactory
from atmosci.ndfd.smart_grib import SmartNdfdGribFileReader


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.ndfd.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def gridManager(grid_factory, manager_date, grid_dataset, region):
    filepath = grid_factory.ndfdGridFilepath(manager_date, grid_dataset, region)
    if not os.path.exists(filepath):
        return grid_factory.buildForecastGridFile(manager_date, grid_dataset,
                                                  region=region)
    manager = grid_factory.ndfdGridFileManager(manager_date, grid_dataset, region, 'a')
    return manager


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def updateForecast(grid_factory, grid_dataset, grib_variable, data, units,
                   region, verbose):
    # start and end times for data in forecast
    fcast_start = data[0][1]
    if len(data) > 1: fcast_end = data[-1][1]
    else: fcast_end = fcast_start

    manager_date = fcast_start.date()
    manager = gridManager(grid_factory, manager_date, grid_dataset, region)
    if debug: print'updating grid file :\n    ', manager.filepath

    for source, fcast_time, grid in data:
        manager.open('a')
        if fcast_time.month != manager_date.month:
            manager.close()
            manager_date = fcast_time.date()
            manager = gridManager(grid_factory, manager_date, grid_dataset, region)
            if debug: print'updating grid file :\n    ', manager.filepath
        if verbose:
            print 'inserting :', fcast_time, source, N.nanmin(grid), N.nanmax(grid)
        manager.updateForecast(grid_dataset, fcast_time, grid, source=source)
        manager.close()

    return fcast_start, fcast_end


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

usage = 'usage: %prog variable [options]'
usage += '\n       %prog variable [options]'
usage += '\n       %prog variable month day [options]'
usage += '\n       %prog variable month 1st_day last_day [options]'
usage += '\n       %prog variable month day month day [options]'
usage += '\n       %prog variable year month day month day [options]'
usage += '\n       %prog variable year month day year month day [options]'
usage += '\n\nNo time args are passed, update forecast for current day.'
usage += '\n2,3 or 4 time args are passed, update days in current year.'

from optparse import OptionParser
parser = OptionParser(usage)

parser.add_option('-r', action='store', dest='grid_region',
                        default=CONFIG.sources.ndfd.grid.region)
parser.add_option('-s', action='store', dest='grid_source',
                        default=CONFIG.sources.ndfd.grid.source)
parser.add_option('-t', action='store', dest='timespan', default=None)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-g', action='store_true', dest='graceful_fail',
                        default=False)
parser.add_option('-f', action='store_false', dest='fill_gaps', default=True)
parser.add_option('-u', action='store_false', dest='utc_file', default=True)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--fileltz', action='store', dest='file_timezone',
                        default=CONFIG.sources.ndfd.grid.file_timezone)
parser.add_option('--grib_region', action='store', dest='grib_region',
                        default=CONFIG.sources.ndfd.grib.region)
parser.add_option('--gribtz', action='store', dest='grib_timezone',
                        default=CONFIG.sources.ndfd.grib.timezone)
parser.add_option('--localtz', action='store', dest='local_timezone',
                        default=CONFIG.project.local_timezone)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
fill_gaps = options.fill_gaps
file_timezone = options.file_timezone
graceful_fail = options.graceful_fail
grib_region_key = options.grib_region
grib_timezone = options.grib_timezone
grid_region_key = options.grid_region
grid_source_key = options.grid_source
local_timezone = options.local_timezone
timespan = options.timespan
today = datetime.date.today()
utc_file = options.utc_file
verbose = options.verbose or debug

if utc_file: file_timezone = 'UTC'
else: file_timezone = local_timezone

grib_variable = args[0].upper()

if grib_variable in ('QPF','PCPN'):
    timespans = ('001-003',)
else:
    if timespan is None:
        timespans = ('001-003','004-007')
    else: timespans = (timepsan,)

num_date_args = len(args) - 1
if num_date_args == 0:
    # update with latest available data
    # if today is the last day of the month there may be data for the
    # next month availble late in the day
    next_month_1st = nextMonth(today) # returns the first day of next month
    if (next_month_1st - today).days > 1: end_date = today
    else: end_date = next_month_1st

    start_date = None

elif num_date_args == 1:
    end_date = today
    start_date = end_date - datetime.timedelta(days=int(args[1]))
else:
    arg_1 = int(args[1])
    if num_date_args == 2: # month day incurrent year
        start_date = end_date = \
            datetime.date(today.year, arg_1, int(args[2]))
    elif num_date_args == 3:
        if arg_1 > 12: # arg_1 is a year, single day in that year
            start_date = end_date = \
                datetime.date(arg_1, int(args[2]), int(args[3]))
        else: # arg_1 is a month, multiple days in month in current year
            start_date = datetime.date(today.year, arg_1, int(args[2]))
            end_date = datetime.date(today.year, arg_1, int(args[3]))
    elif num_date_args == 4:
        if arg_1 > 12: # arg_1 is a year, multiple days in month
            month = int(args[2])
            start_date = datetime.date(arg_1, month, int(args[3]))
            end_date = datetime.date(arg_1, month, int(args[4]))
        else: # days in different months in current year
            start_date = datetime.date(today.year, arg_1, int(args[2]))
            end_date = datetime.date(today.year, int(args[3]), int(args[4]))
    elif num_date_args == 5: # arg_1 is a year
        # days in different months in that year
        start_date = datetime.date(arg_1, int(args[2]), int(args[3]))
        end_date = datetime.date(arg_1, int(args[4]), int(args[5]))
    else:
        raise ValueError, 'Invalid time arguments : %s' % str(args[1:])

smart_grib = SmartNdfdGribFileReader()
if dev_mode: smart_grib.useDirpathsForMode('dev')
ndfd = smart_grib.sourceConfig('ndfd')
grib_region = smart_grib.regionConfig(grib_region_key)

grid_factory = NdfdGridFileFactory()
if dev_mode: grid_factory.useDirpathsForMode('dev')
grid_region = grid_factory.regionConfig(grid_region_key)
grid_source = grid_factory.sourceConfig(grid_source_key)
grid_dataset = grid_factory.ndfdGridDatasetName(grib_variable)

if start_date is None:
    reader = grid_factory.ndfdGridFileReader(end_date, grid_dataset, grid_region)
    last_update = reader.lastUpdate(grid_dataset, None)
    reader.close()
    if last_update is None: start_date = end_date
    else: start_date = last_update.date()

print 'Updating %s forecast for %s thru %s' % (grib_variable, start_date, end_date)

min_fcast_time = tzutils.asUTCTime(datetime.datetime(2099,12,31,23))
max_fcast_time = tzutils.asUTCTime(datetime.datetime(1900,1,1,0))

manager = None
prev_date_filepath = None

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

num_updates = 0

target_date = start_date
while target_date <= end_date:
    if debug:
        print ' '
        print 'processing target date :', target_date
    # get all hours that in latest forecast for this date
    try:
        units, data = smart_grib.dataForRegion(target_date, grib_variable,
                                 timespans, grib_region, grid_region,
                                 grid_source, fill_gaps, graceful_fail, debug)
    except ValueError as e:
        reason = str(e)
        if '/ndfd/' in reason:
            filepath = reason.split('/ndfd/')[1]
            print '    forecast not available for', filepath
            target_date += ONE_DAY
            continue
        else: raise e

    if len(data) > 0:
        fcast_start, fcast_end = \
            updateForecast(grid_factory, grid_dataset, grib_variable, data,
                           units, grid_region, verbose)
        num_updates += 1

        max_fcast_time = max(max_fcast_time, fcast_end)
        min_fcast_time = min(min_fcast_time, fcast_start)

        if fcast_end != fcast_start:
            info = (grib_variable, fcast_start.strftime('%Y-%m-%d:%H'),
                    fcast_end.strftime('%Y-%m-%d:%H'))
            print '    updated %s data for %s thru %s' % info
        else:
            info = (grib_variable, fcast_start.strftime('%Y-%m-%d:%H'))
            print '    updated %s data for %s' % info
    else:
        print 'DATA NOT AVAILABLE FOR %s %s' % (str(target_date), timespans)
        break

    target_date += ONE_DAY

# turn annoying numpy warnings back on
warnings.resetwarnings()

grib_variable = grib_variable.upper()
if num_updates > 0:
    elapsed_time = elapsedTime(UPDATE_START_TIME, True)
    msg = '\ncompleted NDFD "%s" forecast update for %s thru %s in %s'
    print msg % (grib_variable, min_fcast_time.strftime('%Y-%m-%d:%H'),
                 max_fcast_time.strftime('%Y-%m-%d:%H'), elapsed_time)
else: print 'NDFD "%s" forecast is already up to date.' % grib_variable

