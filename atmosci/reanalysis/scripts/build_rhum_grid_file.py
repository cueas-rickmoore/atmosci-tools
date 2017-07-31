#! /usr/bin/env python

import os, sys
import warnings

import datetime
BUILD_START_TIME = datetime.datetime.now()
ONE_HOUR = datetime.timedelta(hours=1)

import numpy as N

from atmosci.utils import tzutils
from atmosci.utils.timeutils import elapsedTime
from atmosci.equations import rhumFromDpt

from atmosci.reanalysis.factory import ReanalysisGridFileFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.urma.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-i', action='store', type=int, dest='interval', default=24)
parser.add_option('-r', action='store', dest='region', default='conus')
parser.add_option('-s', action='store', dest='source', default='acis')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-t', action='store_true', dest='use_time_in_path',
                        default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--fcast_days', action='store', type=int, dest='fcast_days',
                                  default=7)
parser.add_option('--localtz', action='store', dest='local_timezone',
                               default='US/Eastern')
parser.add_option('--obs_days', action='store', type=int, dest='obs_days',
                                default=10)
parser.add_option('--target', action='store', type=int, dest='target_hour',
                              default=7)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
fcast_days = options.fcast_days
interval = datetime.timedelta(hours=options.interval)
local_timezone = options.local_timezone
obs_days = options.obs_days
region_key = options.region
source_key = options.source
target_hour = options.target_hour
use_time_in_path = options.use_time_in_path
verbose = options.verbose or debug

# precip files can only be created from NCEP APCP gribs
file_var_name = 'RHUM'

num_args = len(args)
if num_args == 0:
    now = datetime.date.today()
    date_tuple = (now.year, now.month, now.day)
elif num_args == 3:
    date_tuple = tuple([int(n) for n in args])
else:
    errmsg = 'No arguments passed to script. You must at least specify'
    raise RuntimeError, '%s the grib variable name.' % errmsg

reference_date = datetime.date(*date_tuple)

if debug:
    print 'requesting ...'
    print '    file var :', file_var_name
    print '    ref date :', reference_date

# create a factory for access to grid files
grid_factory = ReanalysisGridFileFactory('reanalysis', CONFIG)
if dev_mode: grid_factory.useDirpathsForMode('dev')
region = grid_factory.regionConfig(region_key)

timespan = grid_factory.fileTimespan(reference_date, obs_days, fcast_days,
                                     target_hour, local_timezone)
file_start_time, reference_time, file_end_time = timespan
if debug:
    print 'timespan in local timezone...'
    print '    start hour :', file_start_time
    print '    ref hour :', reference_time
    print '    end hour :', file_end_time

# get readers for temperature and dew point files 
dewpt_reader = grid_factory.gridFileManager('DPT', region_key,
                                    start_time=file_start_time,
                                    end_time=file_end_time,
                                    use_time_in_path=use_time_in_path)
dewpt_units = dewpt_reader.datasetAttribute('DPT','units')
last_valid_time = dewpt_reader.timeAttribute('DPT', 'last_valid_time')

temp_reader = grid_factory.gridFileManager('TMP', region_key,
                                   start_time=file_start_time,
                                   end_time=file_end_time,
                                   use_time_in_path=use_time_in_path)
temp_units = temp_reader.datasetAttribute('TMP','units')
last_valid_time = min(last_valid_time, 
                      temp_reader.timeAttribute('TMP', 'last_valid_time'))

# get latitude and longitude grids to use in new file
lats = temp_reader.getData('lat')
lons = temp_reader.getData('lon')

# get builder for the reference time span
builder = grid_factory.gridFileBuilder(file_var_name, region_key,
                               start_time=file_start_time,
                               end_time=file_end_time,
                               use_time_in_path=use_time_in_path)
print 'building grid file :', builder.filepath

builder.build(lons=lons, lats=lats)
del lats, lons

builder.open('r')
time_attrs = builder.timeAttributes(file_var_name)
builder.close()
if debug: print '\ntime attributes :', time_attrs, '\n'
file_end_time = time_attrs['end_time']
file_start_time = time_attrs['start_time']

# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

missing_hours = [ ]

last_valid_time = min(last_valid_time, file_end_time)

start_time = file_start_time
while start_time <= last_valid_time:
    end_time = start_time + interval
    if end_time > last_valid_time: end_time = last_valid_time
    dewpt = dewpt_reader.timeSlice('DPT', start_time, end_time)
    temps = temp_reader.timeSlice('TMP', start_time, end_time)
    rhum = rhumFromDpt(temps, dewpt, temp_units)
    if verbose: print '    adding data for :', start_time, end_time
    if debug:
        print '        dewpt', N.nanmin(dewpt), N.nanmean(dewpt), N.nanmax(dewpt)
        print '        temp', N.nanmin(temps), N.nanmean(temps), N.nanmax(temps)
        diffs = temps - dewpt
        print '        diffs', N.nanmin(diffs), N.nanmean(diffs), N.nanmax(diffs)
        print '        rhum', N.nanmin(rhum), N.nanmean(rhum), N.nanmax(rhum)

    builder.open('a')
    builder.updateDataset(file_var_name, start_time, rhum, units='%',
                          source='urma', update_provenance=True)
    builder.close()
    start_time = end_time + ONE_HOUR

# turn annoying numpy warnings back on
warnings.resetwarnings()

elapsed_time = elapsedTime(BUILD_START_TIME, True)
msg = '\nCompleted build for "%s" file in %s. Data entered for :'
print msg % (file_var_name, elapsed_time)
local_time = tzutils.asLocalTime(file_start_time, local_timezone)
local_str = tzutils.hourAsString(local_time, True)
utc_str = tzutils.hourAsString(file_start_time, True)
print '    %s >> %s' % (local_str, utc_str)
local_time = tzutils.asLocalTime(end_time, local_timezone)
local_str = tzutils.hourAsString(local_time, True)
utc_str = tzutils.hourAsString(end_time, True)
print '    thru\n    %s >> %s' % (local_str, utc_str)


