#! /usr/bin/env python

import os, sys
import warnings

import datetime
ONE_HOUR = datetime.timedelta(hours=1)
ONE_DAY = datetime.timedelta(hours=23)

import numpy as N

from atmosci.reanalysis.factory import ReanalysisGridFileFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='grid_region',
                        default=CONFIG.sources.reanalysis.grid.region)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-n', action='store_true', dest='subdir_by_num_hours',
                        default=False)
parser.add_option('-t', action='store_true', dest='use_time_in_path',
                        default=False)
parser.add_option('-u', action='store_true', dest='utc_file', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--fcast_days', action='store', type=int, dest='fcast_days',
                                  default=None)
parser.add_option('--localtz', action='store', dest='local_timezone',
                               default='US/Eastern')
parser.add_option('--obs_days', action='store', type=int, dest='obs_days',
                                default=None)
parser.add_option('--target', action='store', type=int, dest='target_hour',
                              default=None)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
fcast_days = options.fcast_days
grid_region = options.grid_region
local_timezone = options.local_timezone
obs_days = options.obs_days
subdir_by_num_hours = options.subdir_by_num_hours
target_hour = options.target_hour
use_time_in_path = options.use_time_in_path
utc_file = options.utc_file
verbose = options.verbose or debug

if utc_file: file_timezone = 'UTC'
else: file_timezone = local_timezone

file_variable = args[0].upper()

num_args = len(args)
now = datetime.date.today()
if len(args) == 1: # fix current month
    date_tuple = (now.year, now.month, now.day)
elif num_args == 2: # fix specific month in current year
    date_tuple = (now.year, int(args[1]), 1)
elif num_args == 3: # fix year/month
    date_tuple = (int(args[1]), int(args[2]), 1)
else:
    errmsg = 'No arguments passed to script. You must at least specify'
    raise RuntimeError, '%s the grib variable name.' % errmsg

reference_date = datetime.date(*date_tuple)

if verbose:
    print 'requesting ...'
    print '    variable :', file_variable
    print '    ref date :', reference_date
    print '    timezone :', file_timezone

# create a factory for access to grid files
grid_factory = ReanalysisGridFileFactory(CONFIG, timezone=file_timezone)
if dev_mode: grid_factory.useDirpathsForMode('dev')
region = grid_factory.regionConfig(grid_region)

# look for overrides of the default timespan parameters
kwargs = { 'timezone':file_timezone, }
if fcast_days is not None: kwargs['fcast_days'] = fcast_days
if obs_days is not None: kwargs['obs_days'] = obs_days
if target_hour is not None: kwargs['target_hour'] = target_hour
if subdir_by_num_hours: kwargs['grid_subdir_by_hours'] = True

grid_start_time, reference_time, grid_end_time, num_hours = \
                 grid_factory.fileTimespan(reference_date, **kwargs)
if verbose:
    print ' grid file timespan in local timeszone :'
    print '    start hour :', grid_start_time
    print '      ref hour :', reference_time
    print '      end hour :', grid_end_time
    print '     num hours :', num_hours
    print '     file date :', reference_time.date()
else:
    reference_time = timespan[1]

# get reguired information from static file
manager = grid_factory.gridFileManager(reference_time, file_variable,
                                       grid_region, mode='r', **kwargs)
time_attrs = manager.timeAttributes(file_variable)
data_start_time = time_attrs['start_time']
last_valid_time = time_attrs['last_valid_time']
manager.close()


# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

repair_count = 0
# assumes first hour in file is not all N.nan and can be used
manager.open('a')
available_data = \
    manager.timeSlice(file_variable, data_start_time, last_valid_time)
manager.close()

count = 0
# need first hour with valid data
hour = 1 # this is the first hour to test for replacement  
valid = len(N.where(N.isfinite(available_data[0,:,:]))[0])
while valid == 0:
    valid = len(N.where(N.isfinite(available_data[hour,:,:]))[0])
    count += 1
    hour += 1
prev_hour = hour -1

# no point looking for empty last value
last_hour = available_data.shape[0]-1
while hour < last_hour:
    data = available_data[hour,:,:]
    valid = len(N.where(N.isfinite(data))[0])
    if valid == 0:
        in_a_row = 1
        bad_time = data_start_time + datetime.timedelta(hours=hour)
        repaired_hour = hour
        print '\nNo data found for hour', hour, '=', bad_time
        hour += 1
        next_data = available_data[hour,:,:]
        valid = len(N.where(N.isfinite(next_data))[0])
        while valid == 0:
            in_a_row += 1
            hour += 1
            next_data = available_data[hour,:,:]
            valid = len(N.where(N.isfinite(next_data))[0])

        if in_a_row == 1:
            print 'previous hour', prev_hour
            prev_data = available_data[prev_hour,:,:]
            print '    extremes :', N.nanmin(prev_data), N.nanmean(prev_data), \
                                    N.nanmedian(prev_data), N.nanmax(prev_data)
            print 'next hour', hour
            print '    extremes :', N.nanmin(next_data), N.nanmean(next_data), \
                                    N.nanmedian(next_data), N.nanmax(next_data)
            print 'replacing data for hour :', repaired_hour
            data = N.around(((prev_data + next_data) / 2), 2)
            print '    extremes :', N.nanmin(data), N.nanmean(data), \
                                    N.nanmedian(data), N.nanmax(data)

            manager.open('a')
            manager.insertFudgedData(file_variable, bad_time, data)
            manager.close()
        else:
            print 'problem encountered : %d empty hours in a row' % in_a_row
            print 'next available data is not until hour', hour

        print ' '

        prev_hour = hour

    else:
        in_a_row = 0
        prev_hour = hour
        hour = hour + 1

        if (hour % 25) == 0:
            print 'progress to hour', hour

# turn annoying numpy warnings back on
warnings.resetwarnings()

