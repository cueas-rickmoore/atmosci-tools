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
from atmosci.utils.timeutils import elapsedTime, nextMonth, lastDayOfMonth
from atmosci.utils.units import convertUnits

from atmosci.ndfd.factory import NdfdGridFileFactory
from atmosci.ndfd.smart_grib import SmartNdfdGribFileReader


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.ndfd.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def checkPreviousMonth(target_date, grid_dataset, grid_region):
    if target_date.month > 1:
        month_end_date = lastDayOfMonth(target_date.year, target_date.month-1)
        filepath = grid_factory.ndfdGridFilepath(month_end_date, grid_dataset, grid_region)
        if os.path.exists(filepath):
            reader = grid_factory.ndfdGridFileReader(month_end_date, grid_dataset, grid_region)
            last_update = reader.lastUpdate(grid_dataset, None)
            reader.close()
            if last_update not in (None, 'never'):
                return month_end_date, last_update.date()
        return month_end_date, None
    return None, None


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def checkFileValidity(factory, fcast_date, grib_variable, timespan, region):
    filepath = factory.ndfdGribFilepath(fcast_date, grib_variable, timespan, region)
    filesize = os.path.getsize(filepath)
    if filesize < 1000:
        info = (grib_variable, timespan, str(fcast_date), filesize)
        print '%s %s grib file for %s is only %d bytes' % info
        print 'removing', filepath
        os.remove(filepath)


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
    filepath = grid_factory.ndfdGridFilepath(fcast_start.date(), grid_dataset, region)
    if not os.path.exists(filepath):
        grid_factory.buildForecastGridFile(fcast_start.date(), grid_dataset, region=region)

    if len(data) > 1:
        fcast_end = data[-1][1]
        if fcast_end.month != fcast_start.month:
            filepath = grid_factory.ndfdGridFilepath(fcast_end.date(), grid_dataset, region)
            if not os.path.exists(filepath):
                grid_factory.buildForecastGridFile(fcast_end.date(), grid_dataset, region=region)
    else: fcast_end = fcast_start

    manager_date = fcast_start.date()
    manager = gridManager(grid_factory, manager_date, grid_dataset, region)
    if debug: print'\nUpdating grid file :\n    ', manager.filepath

    for source, fcast_time, grid in data:
        manager.open('a')
        if fcast_time.month != manager_date.month:
            manager.close()
            manager_date = fcast_time.date()
            manager = gridManager(grid_factory, manager_date, grid_dataset, region)
            if debug: print'\nUpdating grid file :\n    ', manager.filepath
        if verbose:
            print '    inserting :', fcast_time, source, N.nanmin(grid), N.nanmax(grid)
        manager.updateForecast(grid_dataset, fcast_time, grid, source=source)
        manager.close()

    return fcast_start, fcast_time


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

default = "TD,TEMP,RHM,QPF,POP12"
parser.add_option('-g', action='store', dest='grib_variables', default=default,
        help='List of grib variables to be updated (default="%s")' % default)
parser.add_option('-p', action='store', type=int, dest='prev_days', default=10)
parser.add_option('-r', action='store', dest='grid_region',
                        default=CONFIG.sources.ndfd.grid.region)
parser.add_option('-s', action='store', dest='grid_source',
                        default=CONFIG.sources.ndfd.grid.source)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
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
file_timezone = options.file_timezone
fill_gaps = True
graceful_fail = False
grib_region_key = options.grib_region
grib_timezone = options.grib_timezone
grib_variables = tuple([var.upper() for var in options.grib_variables.split(',')])
grid_region_key = options.grid_region
grid_source_key = options.grid_source
local_timezone = options.local_timezone
prev_days = options.prev_days
TODAY = datetime.date.today()
utc_file = options.utc_file
verbose = options.verbose or debug

if utc_file: file_timezone = 'UTC'
else: file_timezone = local_timezone

num_date_args = len(args)
if num_date_args == 0: # update whatever is available
    start_date = end_date = None

elif num_date_args == 1:
    if 'n' in args[0]: # back some number of days
        end_date = TODAY
        start_date = end_date - datetime.timedelta(days=int(args[0].replace('n','')))
    else: # singla day in current month
        start_date = end_date = datetime.date(TODAY.year, TODAY.month, int(args[0]))

elif num_date_args == 2:
    if 'd' in args[0] or 'd' in args[1]: # args are days
        start_date = datetime.date(TODAY.year, TODAY.month, int(args[0].replace('d','')))
        end_date = datetime.date(TODAY.year, TODAY.month, int(args[1].replace('d','')))
    else: # month day incurrent year
        start_date = end_date = datetime.date(TODAY.year, int(args[0]), int(args[1]))

elif num_date_args == 3:
    arg_0 = int(args[0])
    if arg_0 > 12: # arg_0 is a year, single day in that year
        start_date = end_date = datetime.date(arg_0, int(args[1]), int(args[2]))
    else: # arg_0 is a month, multiple days in month in current year
        start_date = datetime.date(TODAY.year, arg_0, int(args[1]))
        end_date = datetime.date(TODAY.year, arg_0, int(args[2]))

elif num_date_args == 4:
    arg_0 = int(args[0])
    if arg_0 > 12: # arg_0 is a year, multiple days in month
        month = int(args[1])
        start_date = datetime.date(arg_0, month, int(args[2]))
        end_date = datetime.date(arg_0, month, int(args[3]))
    else: # days in different months in current year
        start_date = datetime.date(TODAY.year, arg_0, int(args[1]))
        end_date = datetime.date(TODAY.year, int(args[2]), int(args[3]))

elif num_date_args == 5:
    arg_0 = int(args[0]) # arg_0 is a year
    # days in different months in that year
    start_date = datetime.date(arg_0, int(args[1]), int(args[2]))
    end_date = datetime.date(arg_0, int(args[3]), int(args[4]))

else:
    raise ValueError, 'Invalid time arguments : %s' % str(args)

smart_grib = SmartNdfdGribFileReader()
if dev_mode: smart_grib.useDirpathsForMode('dev')
ndfd = smart_grib.sourceConfig('ndfd')
grib_region = smart_grib.regionConfig(grib_region_key)

grid_factory = NdfdGridFileFactory()
if dev_mode: grid_factory.useDirpathsForMode('dev')
grid_region = grid_factory.regionConfig(grid_region_key)
grid_source = grid_factory.sourceConfig(grid_source_key)

variables_requested = grib_variables
variables_processed = []

for grib_variable in grib_variables:
    VARIABLE_START_TIME = datetime.datetime.now()

    if grib_variable == 'QPF': timespans = ('001-003',)
    else: timespans = ('001-003','004-007')

    grid_dataset = grid_factory.ndfdGridDatasetName(grib_variable)

    if end_date is None:
        update_end = smart_grib.lastAvailableForecast(grib_variable, timespans[-1], grib_region, prev_days)
        if update_end is None:
            info = (grib_variable, prev_days)
            print 'No forecast grib files available for %s in the last %d days' % info
            continue

    if start_date is None:
        filepath = grid_factory.ndfdGridFilepath(TODAY, grid_dataset, grid_region)
        if os.path.exists(filepath):
            reader = grid_factory.ndfdGridFileReader(TODAY, grid_dataset, grid_region)
            last_update = reader.lastUpdate(grid_dataset, None).date()
            reader.close()
            if last_update is not None:
                update_start = last_update
            else: # in case TODAY is early in a new month
                prev_month, last_update = checkPreviousMonth(TODAY, grid_dataset, grid_region)
                if last_update is not None:
                    update_start = last_update
                else:
                    if prev_month is not None:
                        info (grid_dataset, prev_month.replace(day=1))
                        print 'No previous %s forecast update since at least %s' % info
                    else:
                        print 'No previous %s forecast update yet this year' % grid_dataset
                    print 'You can only correct this by using valid start and end dates.'
                    continue

        else:
            grid_factory.buildForecastGridFile(TODAY, grid_dataset, region=grid_region)
            update_start = datetme.date(TODAY.year, TODAY.month, 1)

        if update_end < update_start:
            info = (grib_variable, update_start.strftime('%Y-%m-%d'), update_end.strftime('%Y-%m-%d'))
            print 'Auto update for %s should start at %s but last available forecast is %s' % info
            continue

    else:
        update_start = start_date
        filepath = grid_factory.ndfdGridFilepath(update_start, grid_dataset, grid_region)
        if not os.path.exists(filepath):
            grid_factory.buildForecastGridFile(update_start, grid_dataset, region=grid_region)
        update_end = end_date

    # make sure that update_end file exists when the update spans more than one month
    if update_end.month > update_start.month:
        filepath = grid_factory.ndfdGridFilepath(update_end, grid_dataset, grid_region)
        if not os.path.exists(filepath):
            grid_factory.buildForecastGridFile(update_end, grid_dataset, region=grid_region)

    min_fcast_time = tzutils.asUTCTime(datetime.datetime(2099,12,31,23))
    max_fcast_time = tzutils.asUTCTime(datetime.datetime(1900,1,1,0))

    manager = None
    prev_date_filepath = None

    if debug:
        print 'Processing %s files for :' % grib_variable
        print '    update start :', update_start
        print '      update end :', update_end


    # filter annoying numpy warnings
    warnings.filterwarnings('ignore',"All-NaN axis encountered")
    warnings.filterwarnings('ignore',"All-NaN slice encountered")
    warnings.filterwarnings('ignore',"invalid value encountered in greater")
    warnings.filterwarnings('ignore',"invalid value encountered in less")
    warnings.filterwarnings('ignore',"Mean of empty slice")
    # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!


    num_updates = 0
    target_date = update_start
    while target_date <= update_end:
        if debug:
            print '\ntarget date :', target_date

        for timespan in timespans:
            # get all hours that in latest forecast for this date
            try:
                units, data = smart_grib.dataForRegion(target_date, grib_variable, timespan, grib_region,
                                         grid_region, grid_source, fill_gaps, graceful_fail, debug)
            except ValueError as e:
                info = (grib_variable, str(target_date))
                reason = str(e)
                if reason == 'file not found':
                    continue
                else:
                    print 'Error reading %s forecast for %s' % info
                    print reason
                    checkFileValidity(smart_grib, target_date, grib_variable, timespan, grib_region)
                    continue

            except Exception as e:
                info = (grib_variable, str(target_date))
                print 'Error reading %s forecast for %s' % info
                print str(e)
                continue

            if len(data) > 0:
                fcast_start, fcast_end = \
                    updateForecast(grid_factory, grid_dataset, grib_variable, data, units, grid_region, verbose)
                num_updates += 1

                max_fcast_time = max(max_fcast_time, fcast_end)
                min_fcast_time = min(min_fcast_time, fcast_start)

                if fcast_end > fcast_start:
                    info = (grib_variable, timespan, fcast_start.strftime('%Y-%m-%d'),
                            fcast_end.strftime('%Y-%m-%d'))
                    print 'Updated %s data for %s timespan from %s thru %s' % info
                else:
                    info = (grib_variable, timespan, fcast_start.strftime('%Y-%m-%d'))
                    print '    updated %s data for %s timespan on %s' % info
            else:
                info = (grib_variable, timespan, str(target_date))
                print '%s DATA NOT AVAILABLE FOR %s TIMESPAN ON %s' % info
     
        target_date += ONE_DAY

    # turn annoying numpy warnings back on
    warnings.resetwarnings()


    variables_processed.append(grid_dataset)
    if num_updates > 0:
        elapsed_time = elapsedTime(VARIABLE_START_TIME, True)
        msg = 'Completed %s updates in %s'
        print msg % (grib_variable, elapsed_time)
    else: print '%s forecast is already up to date.' % grib_variable
    print ' '  # dummy space between reports for each variable

# summarize total time spent in updates
elapsed_time = elapsedTime(UPDATE_START_TIME, True)
num_vars_processed = len(variables_processed)
num_vars_requested = len(variables_requested)

if num_vars_processed == num_vars_requested:
    print 'Updated %d forecast grid files in %s' % (num_vars_processed, elapsed_time)
else:
    if len(variables_processed) > 0:
        info = (num_vars_processed, num_vars_requested, elapsed_time)
        print 'Forecast for %s of %s grid files updated in %s' % info
    else: print 'Forecast was not updated'

