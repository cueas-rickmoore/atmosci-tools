#! /Volumes/projects/venvs/test/bin/python

import os, sys
import warnings

import datetime
ONE_DAY = datetime.timedelta(days=1)

from atmosci.tempexts.factory import TempextsProjectFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser.add_option('-r', action='store', dest='region', default=None)
parser.add_option('-s', action='store', dest='source', default=None)
parser.add_option('-v', action='store_true', dest='verbose', default=False)
parser.add_option('-z', action='store_true', dest='debug', default=False)

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

current_year = datetime.date.today().year

debug = options.debug
verbose = options.verbose or debug
print '\ndownload_source_temp_grids.py', args

factory = TempextsProjectFactory()
project = factory.projectConfig()

region = factory.regionConfig(options.region)
source = factory.ourceConfig(options.source)

latest_available_date = factory.latestAvailableDate(source)
latest_available_time = \
    factory.latestAvailableTime(source, latest_available_date)
if latest_available_time > datetime.datetime.now():
    latest_available_date = latest_available_date - ONE_DAY

end_date = None
num_args = len(args)
if num_args == 0:
    end_date = datetime.date.today()
    target_year = end_date.year
    start_date = None
elif num_args in (3,5):
    target_year = int(args[0])
    month = int(args[1])
    day = int(args[2])
    start_date = datetime.date(target_year,month,day)
    if num_args == 5:
        month = int(args[3])
        day = int(args[4])
        end_date = datetime.date(target_year,month,day)
else:
    errmsg = 'Invalid number of arguments (%d).' % num_args
    raise SyntaxError, errmsg

first_day_of_year = datetime.date(target_year,1,1)

# get a temperature data file manger
filepath = factory.tempextsFilepath(target_year, source, region)
if debug:
    print 'temp filepath', os.path.exists(os.path.normpath(filepath)), filepath
if not os.path.exists(os.path.normpath(filepath)):
    manager = \
        factory.tempextsFileBuilder(source, target_year, region, 'temps')
    if start_date is None: start_date = datetime.date(target_year,1,1)
else:
    manager = factory.tempextsFileManager(source, target_year, region,
                                           'temps', mode='r')
    if start_date is None:
        last_obs_date = manager.dateAttribute('temps.maxt',
                                                    'last_obs_date', None)
        if last_obs_date is not None:
            start_date = last_obs_date - ONE_DAY
            if start_date < first_day_of_year: start_date = first_day_of_year
        else: start_date = datetime.date(target_year,1,1)

acis_grid = manager.datasetAttribute('temps.maxt', 'acis_grid')
manager.close()

if end_date is None: end_date = latest_available_date
if end_date == start_date:
    msg = 'downloding %s temps for %s'
    print msg % (source.tag, start_date.strftime('%B %d, %Y'))  
    end_date = None
else:
    msg = 'downloding %s temps for %s thru %s'
    print msg % (source.tag, start_date.strftime('%B %d'),  
                 end_date.strftime('%B %d, %Y'))

if debug:
    print 'temp manager', manager
    print 'temp manager file', manager.filepath


# filter annoying numpy warnings
warnings.filterwarnings('ignore',"All-NaN axis encountered")
warnings.filterwarnings('ignore',"All-NaN slice encountered")
warnings.filterwarnings('ignore',"invalid value encountered in greater")
warnings.filterwarnings('ignore',"invalid value encountered in less")
warnings.filterwarnings('ignore',"Mean of empty slice")
# MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

# download current ACIS mint,maxt for time span
data = factory.getAcisGridData(int(acis_grid), 'mint,maxt', start_date,
                               end_date, False, bbox=manager.data_bbox, 
                               debug=debug)
if debug: print 'temp data\n', data

print 'updating "temps" group'
manager.open('a')
manager.updateTempGroup(start_date, data['mint'], data['maxt'], source.tag)
manager.close()

# turn annoying numpy warnings back on
warnings.resetwarnings()

