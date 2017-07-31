#! /usr/bin/env python

import os, sys
import warnings

import datetime
BUILD_START_TIME = datetime.datetime.now()
ONE_HOUR = datetime.timedelta(hours=1)

import numpy as N
import pygrib

from atmosci.utils import tzutils
from atmosci.utils.timeutils import elapsedTime

from atmosci.reanalysis.factory import ReanalysisGridFileFactory, \
                                       ReanalysisGribFileFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def dataFromGrib(grib_var_name, grib_time, grib_region, grib_factory,
                 verbose=False, debug=False):
    try:
        reader = grib_factory.gribFileReader(grib_time, grib_var_name,
                                             grib_region,
                                             file_must_exist=True,
                                             shared_grib_dir=True)
        if verbose: print 'reading data from :\n    ', reader.filepath
    except IOError: # IOError means file for this hour does not exist
        filepath = \
            grib_factory.gribFilepath(grib_time, grib_var_name, grib_region)
        return False, (grib_time, filepath)

    # read the message
    message = reader.messageFor(grib_var_name)
    if debug:
        print 'message retrieved :\n    ', message
        print 'valid date :', message.validDate
        print 'data units :', message.units
        print 'analDate :', message.analDate
        print 'validDate :', message.validDate
        print 'dataDate :', message.dataDate
        print 'dataTime :', message.dataTime
        print 'forecastTime :', message.forecastTime
        print 'validityDate :', message.validityDate
    data = message.values
    data = data[grib_indexes]
    if N.ma.is_masked(data): data = data.data

    data = data.reshape(grid_shape)
    if debug: print 'grid shape :', data.shape

    missing_value = message.missingValue
    missing = N.where(data == missing_value)
    not_missing = N.where(data != missing_value)
    data[missing] = N.nan
    if debug: 
        print 'data extremes :',N.nanmin(data),N.nanmean(data),N.nanmax(data)
    counts = (data.shape, len(not_missing[0]), len(missing[0]))
    data_hour = tzutils.asHourInTimezone(message.analDate, 'UTC')
    info = (message.units, data_hour, counts)
    reader.close()
    del reader

    return True, (data, info)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-m', action='store', type=int, dest='max_hours',
                        default=None)
parser.add_option('-r', action='store', dest='region', default='conus')
parser.add_option('-s', action='store', dest='source', default='acis')

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-t', action='store_true', dest='use_time_in_path',
                        default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

parser.add_option('--fcast_days', action='store', type=int, dest='fcast_days',
                                  default=7)
parser.add_option('--grib_region', action='store', dest='grib_region',
                                   default='conus')
parser.add_option('--grib_source', action='store', dest='grib_source',
                                   default='urma.ncep')
parser.add_option('--gribtz', action='store', dest='grib_timezone',
                              default='UTC')
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
grib_region = options.grib_region
grib_source = options.grib_source
grib_timezone = options.grib_timezone
local_timezone = options.local_timezone
obs_days = options.obs_days
region_key = options.region
source_key = options.source
target_hour = options.target_hour
use_time_in_path = options.use_time_in_path
verbose = options.verbose or debug

grib_var_name = args[0].upper()

num_args = len(args)
if len(args) == 1:
    now = datetime.date.today()
    date_tuple = (now.year, now.month, now.day)
elif num_args == 4:
    date_tuple = tuple([int(t) for t in args[1:4]])
else:
    errmsg = 'No arguments passed to script. You must at least specify'
    raise RuntimeError, '%s the grib variable name.' % errmsg

reference_date = datetime.date(*date_tuple)

if debug:
    print 'requesting ...'
    print '    variable :', grib_var_name
    print '    ref date :', reference_date

if 'urma' in grib_source:
    from atmosci.reanalysis.urma.config import URMA_SOURCES
    CONFIG.sources.link(URMA_SOURCES)
elif 'rtma' in grib_source:
    from atmosci.reanalysis.rtma.config import RTMA_SOURCES
    CONFIG.sources.link(RTMA_SOURCES)

# create a factory for access to grid files
grid_factory = ReanalysisGridFileFactory()
if dev_mode: grid_factory.useDirpathsForMode('dev')
region = grid_factory.regionConfig(region_key)

timespan = grid_factory.fileTimespan(reference_date, obs_days, fcast_days,
                                     target_hour, local_timezone)
start_time, reference_time, end_time = timespan
if debug:
    print 'data timespan ...'
    print '    start hour :', start_time
    print '    ref hour :', reference_time
    print '    end hour :', end_time

# create a factory for access to grib & static files
grib_factory = ReanalysisGribFileFactory(grib_source, CONFIG)
if dev_mode: grib_factory.useDirpathsForMode('dev')

# get reguired information from static file
static_source = grib_factory.sourceConfig(source_key)
reader = grib_factory.staticFileReader(static_source, region)
lats = reader.getData('lat')
lons = reader.getData('lon')
grid_shape, grib_indexes = reader.gribSourceIndexes('ndfd')
reader.close()
del reader

# get builder for the reference time span
builder = grid_factory.gridFileBuilder(grib_var_name, region_key,
                               start_time=start_time, end_time=end_time,
                               use_time_in_path=use_time_in_path)
print 'building grid file :', builder.filepath

builder.build(lons=lons, lats=lats)
del lats, lons

builder.open('r')
time_attrs = builder.timeAttributes(grib_var_name)
builder.close()


# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

downloaded_hours = [ ]
missing_hours = [ ]
analysis = grib_source.split('.')[0]

# read a grib file for each hour
file_end_time = time_attrs['end_time']
grib_time = time_attrs['start_time']
if options.max_hours is None:
    end_hour = time_attrs['end_time']
else:
    end_hour = grib_time + datetime.timedelta(hours=options.max_hours-1)

while grib_time <= end_hour:
    if debug: 'attempting to get data for :', grib_time
    success, result = dataFromGrib(grib_var_name, grib_time, grib_region,
                                   grib_factory, verbose, debug)
    if debug: print success, '\n', result, '\n'
    if success:
        data, (units, hour, (shape,valid,missing)) = result
        if hour >= start_time: # skip times earlier than file starts
            builder.open('a')
            if debug: print '    adding data for :', hour
            builder.updateDataset(grib_var_name, hour, data,
                                      units=units, source='urma',
                                      update_provenance=True)
            builder.close()
            downloaded_hours.append(hour)
    else:
        missing_hours.append(result)
        if len(missing_hours) <= 5:
            grib_time += ONE_HOUR
            continue
        else: break

    grib_time += ONE_HOUR

# turn annoying numpy warnings back on
warnings.resetwarnings()

if len(downloaded_hours) > 0:
    msg = '\n"%s" grib data updated for %d hours :'
    print msg % (grib_var_name, len(downloaded_hours))
    if verbose: 
        for hour in downloaded_hours:
            utc_str = tzutils.hourAsString(hour,True)
            local_str = tzutils.hourAsString(
                                tzutils.asLocalTime(hour,local_timezone),
                                True)
            print '%s >> %s' % (local_str, utc_str)
    else:
        hour = downloaded_hours[0]
        local_time = tzutils.asLocalTime(hour, local_timezone)
        local_str = tzutils.hourAsString(local_time, True)
        utc_str = tzutils.hourAsString(hour,True)
        print '%s >> %s' % (local_str, utc_str)

        hour = downloaded_hours[-1]
        local_time = tzutils.asLocalTime(hour, local_timezone)
        local_str = tzutils.hourAsString(local_time, True)
        utc_str = tzutils.hourAsString(hour,True)
        print 'thru'
        print '%s >> %s' % (local_str, utc_str)

if len(missing_hours) > 0:
    msg = '\n%d "%s" grib files were not available :'
    print msg % (len(missing_hours), grib_var_name)
    if debug:
        for grib_time, filepath in missing_hours:
            local_time = tzutils.asLocalTime(grib_time, local_timezone)
            local_str = tzutils.hourAsString(local_time, True)
            print '%s >> %s' % (local_str, filepath)
    else:
        first_time, filepath = missing_hours[0]
        local_time = tzutils.asLocalTime(first_time, local_timezone)
        hour_as_str = tzutils.hourAsString(local_time, True)
        print '%s >> %s' % (hour_as_str, filepath)
        if file_end_time > first_time:
            print 'thru'
            local_time = tzutils.asLocalTime(file_end_time, local_timezone)
            hour_as_str = tzutils.hourAsString(local_time, True)
            first_str = tzutils.fileTimeString(first_time)
            file_end_str = tzutils.fileTimeString(file_end_time)
            filepath = filepath.replace(first_str, file_end_str)
            print '%s >> %s' % (hour_as_str, filepath)

elapsed_time = elapsedTime(BUILD_START_TIME, True)
msg = '\ncompleted build for "%s" file in %s'
print msg % (grib_var_name, elapsed_time)

