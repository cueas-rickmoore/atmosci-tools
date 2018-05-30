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

import datetime
UPDATE_START_TIME = datetime.datetime.now()

from atmosci.utils.timeutils import elapsedTime

from atmosci.ndfd.factory import NdfdGribFileFactory


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='region', default='conus')
parser.add_option('-s', action='store', dest='source', default='nws')
parser.add_option('-w', action='store', dest='wait_times', default=None)

parser.add_option('-d', action='store_true', dest='dev_mode', default=False)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

debug = options.debug
dev_mode = options.dev_mode
region = options.region
source = options.source
verbose = options.verbose or debug

if ',' in args[0]: variables = args[0].split(',')
else: variables = [ args[0],]
print 'variables', variables

factory = NdfdGribFileFactory()
if dev_mode: factory.useDirpathsForMode('dev')
if options.wait_times is not None:
    if ',' in options.wait_times:
        wait_times = tuple([int(t) for t in options.wait_times.split(',')])
    else: wait_times = (int(options.wait_times),)
    factory.setDownloadWaitTimes(wait_times)

target_date = factory.timeOfLatestForecast()

count = 0
success = 0

for variable in variables:
    if variable in ('qpf','QPF'): periods = ('001-003',)
    else: periods =('001-003','004-007')

    for period in periods:
        count += 1
        status, path, url, message = \
          factory.downloadForecast(target_date, variable, period, region, source, debug)

        if status == 200:
            success += 1
            if debug: print '%s %s data was saved to file:\n    %s' % (period, variable, path)
            else: print '%s %s data was saved to file: %s' % (period, variable, path)

        elif status == 999:
            print message
            print '    %s %s data was not updated (%s).' (period, variable, path)
            if verbose: print '    failed URL :', url

        elif status == 404:
            info = (period, variable, status)
            print '%s %s download with HTTP error code %d.' % info
            print '    failed URL :', url
            print '    file was not updated :', message 

        else:
            info = (period, variable, status, message)
            print '%s %s download with HTTP error code %d.\n    %s' % info
            if verbose: print '    failed URL :', url
            print '    file was not updated :', message

elapsed_time = elapsedTime(UPDATE_START_TIME, True)
failed = count - success
if failed > 0:
    print 'Successfully completed %d downloads in %s' % (count, elapsed_time)
else:
    print 'Successfiully completed %d of %d downloads in %s' % (success, count, elapsed_time)

