#! /Users/rem63/venvs/atmosci/bin/python

import copy
import os, sys, shlex
import subprocess
from datetime import datetime
from dateutil.relativedelta import relativedelta

from twisted.internet import reactor

from nrcc.utils.report import Reporter
from nrcc.utils.logging import logException, logFailure
from nrcc.utils.parallel import RestrictedParallelProcessController

from nrcc.stations.scripts.factory import StationDataManagerFactory

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from nrcc.stations import STATIONS_SCRIPT_DIR

#APP = os.path.splitext(os.path.split(__file__)[1])[0].upper().replace('_',' ')
APP = os.path.split(sys.argv[0])[1] + ' ' + ' '.join(sys.argv[1:])
#PID = os.getpid()
PID = 'PID %d' % os.getpid()

ONE_DAY = relativedelta(days=1)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()

parser = OptionParser()
parser.add_option('-l', action='store', type='string', dest='log_filepath',
                  default=None,
                  help='path to alternate file to be used for logging')
parser.add_option('--ma', action='store', type='string', dest='max_attempts',
                  default=None)
parser.add_option('--mrt', action='store', type='string', dest='max_run_time',
                  default=None)
parser.add_option('-p', action='store', type='int', default=2,
                  dest='max_concurrent_processes')
parser.add_option('-r', action='store', type='string', dest='region',
                  default=None,
                  help="name of NOAA/RCC region to process : ne, eor, etc.")
parser.add_option('--st', action='store', type='int', dest='sleep_time',
                  default=None)
parser.add_option('-u', action='store', type='string', dest='base_url',
                  default=None)
parser.add_option('-w', action='store', type='string', dest='working_dir',
                  default=None,
                  help="alternate working directory for downloaded files")
parser.add_option('--wt', action='store', type='int', dest='wait_time',
                  default=None)
parser.add_option('-x', action='store_true', dest='replace_existing',
                  default=False,
                  help='replace existing hourly data file with new data')
parser.add_option('-z', action='store_true', dest='debug', default=False,
                  help='show all available debug output')

options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

reporter = Reporter(PID)

try:
    start_perf = datetime.now()

    if len(args) > 1:
        year = int(args[0])
        month = int(args[1])
        day = int(args[2])
        if len(args) > 3:
            num_days = int(args[3])
        else:
            num_days = 0
        date = datetime(year,month,day)
    else:
        date = datetime.now()
        year = today.year
        month = (today.month)
        day = today.day
        if len(args) > 1:
            num_days = int(args[0])
        else:
            num_days = 0
    date_str = date.strftime('%B %d, %Y')
    last_date = date - relativedelta(days=num_days)

    debug = options.debug
    replace_existing = options.replace_existing

    if options.max_run_time is not None:
        max_run_time = options.max_run_time
        if max_run_time[-1] == ':':
            run_time_hours = int(max_run_time[:-1])
            run_time_minutes = 0
        elif max_run_time[0] == ':':
            run_time_hours = 0
            run_time_minutes = int(max_run_time[1:])
        else:
            colon = max_run_time.find(':')
            if colon > 0:
                run_time_hours = int(max_run_time[:colon])
                run_time_minutes = int(max_run_time[colon+1:])
            else:
                run_time_hours = int(max_run_time)
                run_time_minutes = 0
        run_time = relativedelta(hours=run_time_hours,
                                 minutes=run_time_minutes)
        if run_time_hours > 0:
            run_time_str = '%d hours' % run_time_hours
            if run_time_minutes > 0:
                run_time_str += ', %M minutes' % run_time_minutes
        else:
            run_time_str = '%d minutes' % run_time_minutes

        quit_time = datetime.now() + run_time
        if debug:
            print 'parallel server quit time', quit_time
    else:
        run_time_str = ''
        quit_time = None

    reporter = Reporter(PID, options.log_filepath)
    reporter.logEvent(APP)

    factory = StationDataManagerFactory(date, options)

    script_name = 'create_station_cache.py'
    script = os.path.join(STATIONS_SCRIPT_DIR, script_name)

    process_args = [script, ' ', ' ', ' ',
                    '-r', factory.region_name.lower(),
                   ]

    process_args.append('-l')
    if options.log_filepath is not None:
        log_filepath = options.log_filepath
    else:
        log_filepath = os.path.join(factory.getDirectory('working'),
                                    'parallel_downloads.log')
    process_args.append(log_filepath)

    if options.max_attempts is not None:
        process_args.extend(['--ma', options.max_attempts])
    if options.sleep_time is not None:
        process_args.extend(['--st', options.sleep_time])
    if options.base_url is not None:
        process_args.extend(['-u', options.base_url])
    if options.wait_time is not None:
        process_args.extend(['--wt', options.wait_time])

    if replace_existing: process_args.append('-x')
    if debug: process_args.append('-z')

except:
    logException(APP, reporter, 'Application initialization')
    os._exit(1)

try:
    processes = [ ]
    while date >= last_date:
        process_args[1] = str(date.year)
        process_args[2] = str(date.month)
        process_args[3] = str(date.day)
        print date
        
        processes.append( (date.strftime('%Y%m%d-download'), sys.executable,
                          tuple(process_args), os.environ, None) )
        date -= ONE_DAY

    print [process[0] for process in processes]
    controller = RestrictedParallelProcessController(reactor, tuple(processes),
                                          options.max_concurrent_processes,
                                          None, quit_time, debug, reporter)
    try:
        controller.start()
    except Exception as e:
        logException(APP, reporter, 'Parallel process controller')
        reporter.logEvent('***** parallel processing terminated *****')
        os._exit(1)

    msg = 'Server stopped because ' + controller.server_status
    reporter.reportInfo(msg)

    num_completed = controller.num_completed
    num_failed = len(controller.failed_processes)
    num_attempts = len(processes) - num_completed - num_failed 
    msg = 'Attempted station downloads for %d days' % num_attempts
    reporter.reportInfo(msg)
    msg = '%d subprocesses completed successfully' % num_completed
    reporter.reportInfo(msg)

    perf_msg = 'Total elapsed time ='

    if num_failed > 0:
        controller.failed_processes.sort()
        bombs = [str(pid) for pid in controller.failed_processes]
        msg = '%d subprocesses failed : %s' % (num_failed,', '.join(bombs))
        reporter.logError(msg)
        reporter.logPerformance(start_perf, perf_msg)
        # when the log file is closed, the reporter will write to stdout
        # this part will be captured by cron and emailed to the process owner
        reporter.reportEvent(msg)
        reporter.reportEvent('For details, see log file : %s' %
                             reporter.filepath)
        reporter.flush()
        os._exit(1)

    reporter.logPerformance(start_perf, perf_msg)

except Exception:
    logException(APP, reporter, 'Parallel station downloads')
    reporter.logEvent('***** parallel download server terminated *****')
    os._exit(1)

reporter.logEvent('parallel server stopped gracefully')

