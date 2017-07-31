#! /Volumes/projects/venvs/builds/bin/python

import os, sys
import datetime
ONE_HOUR = datetime.timedelta(hours=1)

import pytz
import numpy as N
import urllib

from atmosci.utils.timeutils import elapsedTime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CACHE_SERVER_BUFFER_MIN = 20

NOMADS_SERVER = 'http://nomads.ncep.noaa.gov/pub/data/nccf/com/rtma/prod'
NOMADS_SUBDIR = 'rtma2p5.%(utc_date)s'
NOMADS_ACPC_DATA = 'rtma2p5.%(utc_time)s.pcp.184.grb2'
NOMADS_ACPC_URL = '/'.join((NOMADS_SERVER, NOMADS_SUBDIR, NOMADS_ACPC_DATA))
NOMADS_DATA = 'rtma2p5.t%(utc_hour)sz.2dvaranl_ndfd.grb2'

THREDDS_SERVER = \
    'http://thredds.ucar.edu/thredds/fileServer/grib/NCEP/RTMA/CONUS_2p5km/'
THREDDS_DATA = 'RTMA_CONUS_2p5km_%(utc_date)s_%(utc_hour)s00.grib2'

DATA_URLS = { 'nomads': '/'.join((NOMADS_SERVER, NOMADS_SUBDIR, NOMADS_DATA)),
              'thredds': '/'.join((THREDDS_SERVER, THREDDS_DATA)) }

RTMA_DIRPATH = '/Volumes/data/app_data/shared/reanalysis/conus/rtma/'
RTMA_SUBDIR_PATH = os.path.join(RTMA_DIRPATH, '%(utc_date)s')
APCP_FILENAME = 'rtma.%(utc_time)sz.precip.grb2'
APCP_FILEPATH = os.sep.join((RTMA_SUBDIR_PATH, APCP_FILENAME))
DATA_FILENAME = 'rtma.%(utc_time)sz.data.grb2'
DATA_FILEPATH = os.sep.join((RTMA_SUBDIR_PATH, DATA_FILENAME))

UTC_FORMAT = '%Y.%m.%d:%HUTC'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def utcTimes(utc_time):
    return { 'utc_date': utc_time.strftime('%Y%m%d'),
             'utc_hour': utc_time.strftime('%H'), 
             'utc_time': utc_time.strftime('%Y%m%d%H') }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def downloadRTMA(utc_time, server='nomads', verbose=False, debug=False):
    files = [ ]
    utc_time_str =utc_time.strftime(UTC_FORMAT)
    utc_times = utcTimes(utc_time)
    rtma_dirpath = RTMA_SUBDIR_PATH % utc_times
    if debug: print 'dirpath', os.path.isdir(rtma_dirpath), rtma_dirpath
    if not os.path.isdir(rtma_dirpath): os.makedirs(rtma_dirpath)

    # download main data file
    local_filepath = DATA_FILEPATH % utc_times
    # don't download a file it already exists
    if not os.path.exists(local_filepath):
        remote_url = DATA_URLS[server] % utc_times
        if verbose:
            print '\ndownloading :', remote_url
            print 'to :', local_filepath
        try:
            (destfile, info) = urllib.urlretrieve(remote_url, local_filepath)
            if debug: print info
        except Exception as e:
            print '*** download of "%s" failed' % remote_url.split('prod')[1]
        else:
            if int(info['Content-Length']) < 300:
                print 'Data download failed for %s' % utc_time_str
                if os.path.exists(local_filepath):
                    os.remove(local_filepath)
            else:
                files.append((utc_times['utc_time'], local_filepath))

    if server == 'nomads':
        # download the precip file
        local_filepath = APCP_FILEPATH % utc_times
        # don't download a file it already exists
        if not os.path.exists(local_filepath):
            remote_url = NOMADS_ACPC_URL % utc_times
            if verbose:
                print '\ndownloading :', remote_url
                print 'to :', local_filepath
            try:
                (destfile,info) = urllib.urlretrieve(remote_url, local_filepath)
                if debug: print info
            except:
                errmsg = '*** download of "%s" failed' 
                print errmsg % remote_url.split('prod')[1]
            else:
                if int(info['Content-Length']) < 300:
                    print 'Precip download failed for %s' % utc_time_str
                    if os.path.exists(local_filepath):
                        os.remove(local_filepath)
                else:
                    files.append((utc_times['utc_time'], local_filepath))

    return tuple(files)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-n', action='store', type=int, dest='num_hours', default=4)
parser.add_option('-p', action='store', dest='periods',
                        default='001-003,004-007')
parser.add_option('-s', action='store', dest='server', default='nomads')
parser.add_option('-u', action='store_true', dest='utc_date', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

download_start = datetime.datetime.now()

debug = options.debug
file_count = 0
num_hours = options.num_hours
server = options.server
utc_date = options.utc_date
verbose = options.verbose or debug

tz = pytz.timezone('US/Eastern')
if len(args) > 0:
    date_args = tuple([int(n) for n in args[0].split('.')])
    if utc_date: # input date is already UTC corrected
        end_hour = datetime.datetime(*date_args)
    else:
        hour = tz.localize(datetime.datetime(*date_args))
        end_hour = hour.astimezone(pytz.utc)
else:
    hour = tz.localize(datetime.datetime.now())
    end_hour = hour.astimezone(pytz.utc)
if debug:
    print 'num_hours', num_hours
    print 'end_hour', end_hour

utc_hour = end_hour - datetime.timedelta(hours=num_hours-1)
while utc_hour <= end_hour:
    if debug: print '\nprocessing download for', utc_hour
    files = downloadRTMA(utc_hour, server, verbose, debug)
    file_count += len(files)
    utc_hour += ONE_HOUR

elapsed_time = elapsedTime(download_start, True)
print '\ncompleted downloaded %d in %s' % (file_count, elapsed_time)

transport_dirpath = \
    '/Volumes/Transport/data/app_data/shared/reanalysis/conus/rtma'
if file_count > 0 and os.path.exists(transport_dirpath):
    command = \
        '/usr/bin/rsync -cgloprtuD %s %s' % (RTMA_DIRPATH, transport_dirpath)
    print '\n', command
    os.system(command)

