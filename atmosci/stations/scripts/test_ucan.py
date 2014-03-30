# /Library/Frameworks/Python.framework/Versions/2.6/bin/python

import os, sys
from copy import copy
from datetime import datetime
from dateutil.relativedelta import relativedelta

import Data, Meta
import ucanCallMethods

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

tsvars = {
'pcpn' : { 'cu_log' : ( {'major':5, 'minor':7, 'units':'inch'},
                        {'major':5, 'minor':0, 'units':'inch'}, ),
           'icao' : ( {'major':5, 'minor':3, 'units':'inch'},
                      {'major':5, 'minor':0, 'units':'inch'}, ),
           'newa' : ( {'major':5, 'minor':6, 'units':'inch'},
                      {'major':5, 'minor':0, 'units':'inch'}, ),
           'njwx' : ( {'major':5, 'minor':8, 'units':'inch'},
                      {'major':5, 'minor':0, 'units':'inch'}, ),
         },
'rhum' : { 'cu_log' : ( {'major':24, 'minor':6, 'units':'percent'},
                       {'major':24, 'minor':0, 'units':'percent'}, ),
           'icao' : ( {'major':24, 'minor':3, 'units':'percent'},
                      {'major':24, 'minor':0, 'units':'percent'}, ),
           'newa' : ( {'major':24, 'minor':5, 'units':'percent'},
                      {'major':24, 'minor':0, 'units':'percent'}, ),
           'njwx' : ( {'major':24, 'minor':9, 'units':'percent'},
                      {'major':24, 'minor':0, 'units':'percent'}, ),
         },
'temp' : { 'cu_log' : ( {'major':126, 'minor':1, 'units':'F'},
                        {'major':126, 'minor':0, 'units':'F'}, ),
           'icao' : ( {'major':23, 'minor':3, 'units':'F'},
                      {'major':23, 'minor':0, 'units':'F'}, ),
           'newa' : ( {'major':23, 'minor':6, 'units':'F'},
                      {'major':23, 'minor':0, 'units':'F'}, ),
           'njwx' : ( {'major':23, 'minor':7, 'units':'F'},
                      {'major':23, 'minor':0, 'units':'F'}, ),
         },
}

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getReasonableTimeSpans(start_time, end_time, days_per_request=30):
    # break up time span into self.hours_per_request increments due to
    # tsvar/ucan server limitations
    hours_per_request = days_per_request * 24
    request_delta = relativedelta(hours=hours_per_request)
    start_span = copy(start_time)
    spans = [ ]
    while start_span < end_time:
        delta = end_time - start_span
        hours = (delta.days * 24) + (delta.seconds / 3600)
        if hours > hours_per_request:
            end_span = start_span + request_delta
        else:
            end_span = end_time
        spans.append( (start_span, end_span) )
        # set next 'start_span' to previous `end_span` because ts_var
        # always returns one hour less than requested
        start_span = end_span
    return hours_per_request, spans

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-z', action='store_true', dest='debug', default=False,
                  help='show all available debug output')
options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

stars = '*' * 72
dataset = args[0]
ucanid = 33686 
sid = 'cu_gfr'
network = 'cu_log'
tsvar = tsvars[dataset][network][0]
major = tsvar['major']
minor = tsvar['minor']
units = tsvar['units']

ucan = ucanCallMethods.general_ucan()

query = ucan.get_query()
result = query.getUcanFromIdAsSeq(sid, network)
query.release()
print '%d : %s : ucan id : %s' % (ucanid, sid, result[-1].ucan_id)

query = ucan.get_query()
metadata = query.getInfoForUcanIdAsSeq(ucanid,())
metadata = ucanCallMethods.NameAny_to_dict(metadata[-1].fields)
query.release()

print 'print metatadata for %d : %s', (ucanid, sid)
print metadata
print '\n%s\n' % stars

data = ucan.get_data()
if network == 'icao': ts_var = data.newTSVarNative(major, minor, sid)
else: ts_var = data.newTSVar(major, minor, ucanid)

start_time, end_time = ts_var.getValidDateRange()
print 'valid date range :', start_time, end_time
_start_time_ = datetime(*start_time)
_end_time_ = datetime(*end_time)
delta = _start_time_ - _end_time_
print 'time span is %d hours' % ((delta.days * 24) + (delta.seconds / 3600))

hours_per_request, spans = getReasonableTimeSpans(_start_time_, _end_time_)
print 'requires %d requests of %s hours each' % (len(spans), hours_per_request)

ts_var.setUnits(units)
hourly_data = [ ]
for start_span, end_span in spans:
    failed = True
    try:
        ts_var.setDateRange(start_span.timetuple()[:4],
                            end_span.timetuple()[:4])
        tsv_data = ts_var.getDataSeqAsFloat()
        failed = False
    finally:
        # if it failed, release connection to the CORBA server
        if failed: ts_var.release()

    # got here only if successful
    hourly_data.extend(tsv_data)
    print '\n%s\n' % stars
    print len(tsv_data), start_span, end_span
    print 'first 24 hrs', tsv_data[:24]
    print '\nlast 24 hrs', tsv_data[-24:]

ts_var.release()
data.release()

