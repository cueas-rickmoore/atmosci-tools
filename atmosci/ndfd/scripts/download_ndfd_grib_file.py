#! /usr/bin/env python

import datetime

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
wait_times = options.wait_times

filetype = args[0]
period = args[1]

target_date = datetime.date.today()

factory = NdfdGribFileFactory()
if dev_mode: factory.useDirpathsForMode('dev')
if options.wait_times is not None:
    if ',' in options.wait_times:
        wait_times = tuple([int(t) for t in options.wait_times.split(',')])
    else: wait_times = (int(options.wait_times),)
    factory.setDownloadWaitTimes(wait_times)

status, path, url, message = \
    factory.downloadForecast(target_date, filetype, period, region, source, debug)
print status, message
print url
print path

