
import sys
import itertools
import urllib, urllib2
from datetime import datetime
from datetime import date as dt_date

try:
    import simplejson as json
except ImportError:
    import json

import numpy as N

from atmosci.utils.report import Reporter

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.config import STATIONS

DEFAULT_URL = STATIONS.download_url
DEFAULT_VERSION = STATIONS.download_version

ELEMENT_NAME_MAP = { 'tn' : 'mint' , 'tx' : 'maxt' , 'pp' : 'pcpn' }

NON_NUMERIC_ELEMS = ()
NON_NUMERIC_VX_IDS = (6,20,21,30,32,46,47,49,50,51,58,59,60,61,65,66,67,68)
ALL_NON_NUMERIC_ELEMS = NON_NUMERIC_ELEMS + NON_NUMERIC_VX_IDS

OUTLIERS = { 'mint' : (-30. , 130.) , 'maxt' : (-30. , 130.) , 'pcpn' : (0., 5.) }

PRECIP_VX_IDS = (4,5,10,11,13,36,37,38,52,64,93,94,101,110,111,112,113)
PRECIP_ELEM_NAMES = ('pcpn','snow','snwd',)
ALL_PRECIP_ELEMENTS = PRECIP_ELEM_NAMES + PRECIP_VX_IDS

TEMP_VX_IDS = (1,2,3,8,9,14,15,16,22,23,25,39,40,43,48,63,69,86,107,108,
           114,115,116,117)
TEMP_ELEM_NAMES = ('mint','maxt','avgt','obst',) 
ALL_TEMP_ELEMENTS = TEMP_ELEM_NAMES + TEMP_VX_IDS


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def reportException(errmsg):
    print errmsg
    import traceback
    exception_type, exception_instance, trace_back = sys.exc_info()
    print traceback.format_exception(exception_type, exception_instance,
                                     trace_back)

    sys.stdout.flush()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class BaseAcisDataClient:

    def __init__(self, base_url=DEFAULT_URL, outliers=OUTLIERS,
                       precip_trace=0.005, accumulated_precip=N.inf,
                       missing=N.inf, reporter_or_filepath=None,
                       version=DEFAULT_VERSION, debug=False,
                       performance=False, **kwargs):

        self.base_url = base_url
        self.outliers = outliers
        self.precip_trace = precip_trace
        self.accumulated_precip = accumulated_precip
        self.missing = missing
        if isinstance(reporter_or_filepath, Reporter):
            self.reporter = reporter_or_filepath
        else:
            self.reporter = Reporter(self.__class__.__name__,
                                     reporter_or_filepath)
            self.reporter.close()
        self.version = version
        self.debug = debug
        self.performance = performance
        self.keyword_args = kwargs
        if version <  2.0:
            self.ignore_awdn = kwargs.get('ignore_awdn', True)
            self.default_elements = ('pcpn','maxt','mint')
        else:
            self.default_elements = ( { 'name':'maxt', 'add':['f',] },
                                      { 'name':'mint', 'add':['f',] },
                                      { 'name':'pcpn', 'add':['f',] },
                                    )
        self.default_metadata = ('uid','ll','elev')

        self.element_name_map = ELEMENT_NAME_MAP
        self.temp_elem_ids = ALL_TEMP_ELEMENTS
        self.precip_elem_ids = ALL_PRECIP_ELEMENTS
        self.non_numeric_elem_ids = ALL_NON_NUMERIC_ELEMS
        self.elem_names = TEMP_ELEM_NAMES + PRECIP_ELEM_NAMES
        self.vx_ids = TEMP_VX_IDS + PRECIP_VX_IDS + NON_NUMERIC_VX_IDS

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def request(self, data_type, method='POST', **kwargs):
        if self.version >= 2.0 and method != 'POST':
            errmsg = "only 'POST' method is supported by this version ACIS"
            raise ValueError, errmsg

        ERROR_MSG = 'Error processing request : %s %s'
        # make sure that `elems` is a list and POSTed if necessary
        elems = self.validateElements(kwargs.get('elems',self.default_elements))
        kwargs['elems'] = elems

        if self.version < 2.0:
            if 'no_awdn' not in kwargs and self.ignore_awdn:
                kwargs['no_awdn'] = 1
        else:
            if 'no_awdn' in kwargs:
                del kwargs['no_awdn']

        for date_key in ('date','sDate','eDate'):
            date = kwargs.get(date_key,None)
            if date is None: continue # date key is not present

            if isinstance(date, (datetime, dt_date)):
                date = date.strftime('%Y%m%d')
            elif isinstance(date, (list,tuple)):
                if date[0] > 31: # year is first element in sequence
                    date = '%d%02d%02d' % date
                else: # year is last element in sequence
                    date = '%d%02d%02d' % (date[2],date[0],date[1])
            elif type(date) not in (str,unicode):
                raise ValueError, "Bad data type for '%s' argument" % date_key

            kwargs[date_key] = date

        url = self.base_url
        if url.endswith('/'):
            if data_type.startswith('/'):
                url += data_type[1:]
            else:
                url += data_type
        else:
            if data_type.startswith('/'):
                url += data_type
            else:
                url += '/' + data_type

        if method == 'POST':
            post_args = json.dumps(kwargs)
            if self.debug:
                print 'POST', url
                print 'params =', post_args
            post_params = urllib.urlencode({'params':post_args})
            req = urllib2.Request( url, post_params,
                                  { 'Accept':'application/json' }
                                 )
            url += ' json=' + post_params
            start_time = datetime.now()
            try:
                response = urllib2.urlopen(req)
            except Exception:
                self.reporter.logError(ERROR_MSG % (method, url))
                raise
            end_time = datetime.now()

        else:
            url += '?' + urllib.urlencode(kwargs) + '&output=json'
            if self.debug:
                print 'GET', url
            start_time = datetime.now()
            try:
                response = urllib2.urlopen(url)
            except Exception:
                self.reporter.logError(ERROR_MSG % (method, url))
                raise
            end_time = datetime.now()

        try:
            response_data = response.read()
        except Exception:
            self.reporter.logError(ERROR_MSG % (method, url))
            raise
        end_time = datetime.now()

        if self.performance:
            msg = 'Time to retrieve data from ACIS web service ='
            self.reporter.logPerformance(start_time, msg)

        return kwargs['elems'], response_data, response

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dateAsString(self, date):
        if isinstance(date, (str,unicode)):
            if '/' in date:
                return date.replace('/','-')
            else:
                return date
        elif isinstance(date, (tuple,list)):
            return self._dateTupleAsString(date)
        try:
            return date.strftime('%Y-%m-%d')
        except:
            raise ValueError, 'Invalid type for date.'

    def _dateTupleAsString(self, date):
        return '%d-%02d-%02d' % date

    def _validDateRange(self, start_date, end_date):
        start_date = self._dateAsTuple(start_date)
        if end_date is not None:
            end_date = self._dateAsTuple(end_date)
        return start_date, end_date

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def findOutliers(self, data, min_value, max_value):
        bogus = [ ]
        i = 0
        while i < len(data):
            value = data[i]
            if value > max_value:
                bogus.append( (i, value) )
            elif value < min_value and value != -32768.: 
                bogus.append( (i, value) )
            i+=1
        return tuple(bogus)

    def responseAsDict(self, json_string):
        return json.loads(json_string)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def serializeDataValue(self, element, data):
        if self.version < 2.0:
            # do nothing for non-numeric data
            if element in self.non_numeric_elem_ids:
                return data
            # handle characters in numeric data types
            if data == 'M': return self.missing
            if element in self.precip_elem_ids:
                if data == 'T': return self.precip_trace
                if data == 'S': return self.missing
                if data.endswith('A'): return self.accumulated_precip
            # all other numeric values want to be floating point
            return float(data)

        else:
            elem_id = element.get('name',element.get('vX',None))
            # do nothing for non-numeric data or unrecognized elements
            if elem_id is None or elem_id in self.non_numeric_elem_ids:
                return data
            # handle characters in numeric data types
            if data[0] in ('A','M','S',' '): data[0] = self.missing
            elif data[0] == 'T': data[0] = self.precip_trace
            elif data[0] == 'S': data[0] = self.missing
            # all other numeric values want to be floating point
            else:
                data[0] = float(data[0])
            return data

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def validateElementDict(self, elem):
        if 'name' in elem:
            name = elem['name']
            elem_name = self.element_name_map.get(name,name)
            if elem_name in self.elem_names:
                elem['name'] = elem_name
                return elem
            raise ValueError, "Invalid value for 'name' in element dictionary"
        elif 'vX' in elem:
            if elem['vX'] in self.vx_ids:
                return elem
            raise ValueError, "Invalid value for 'vX' in element dictionary"

        errmsg = "Element dictionary must contain either the 'name' or 'vX' key"
        raise KeyError, errmsg

    def validateElementString(self, elem):
        if elem.isdigit() and int(elem) in self.vx_ids:
            return { 'vX' : int(elem), }
        elif elem in self.elem_names:
            return { 'name': elem, }
        name = self.element_name_map.get(elem,None)
        if name is not None:
            return { 'name': name, }

        errmsg = "String contains invalid element identifier '%s'"
        raise ValueError, errmsg % elem

    def validateElements(self, elements):
        if elements is None: return None
        if isinstance(elements, dict):
            return (self.validateElementDict(elements),)

        elif isinstance(elements, (str,unicode)):
            return (self.validateElementString(elements),)

        elif isinstance(elements, (tuple,list)):
            valid_elems = [ ]
            for elem in elements:
                if isinstance(elem, (str,unicode)):
                    valid_elems.append(self.validateElementString(elem))
                elif isinstance(elem, dict):
                    valid_elems.append(self.validateElementDict(elem))
            return tuple(valid_elems)

        raise ValueError, "Invalid type for element identifier"

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _pythonObjectsFromJson(self, json_string, response,
                                     request_detail=None):
        """ Convert a json string to Python objects ... handle known instances
        where server injects badly formed JSON into the stream
        """
        if 'DOCTYPE HTML PUBLIC' in json_string:
            errmsg = 'SERVER ERROR : '
            if 'server encountered an internal error' in json_string:
                errmsg += 'server encountered an unspecified internal error.'
                if request_detail is not None:
                    errmsg += '\n' + request_detail
                ecode = 503
            else:
                ecode = 500
                errmsg += 'server returned HTML, not valid JSON.\n'
                if request_detail is not None:
                    errmsg += request_detail + '\n'
                errmsg += json_string
            raise urllib2.HTTPError(response.geturl(),ecode,errmsg,None,None)

        server_error = 'SERVER ERROR : '
        errors = [ ]
        if '[Failure instance:' in json_string:
            found_start = json_string.find('[Failure instance:')
            while found_start > 0:
                found_end = json_string.find('\n],',found_start)
                error = json_string[found_start:found_end+3]
                errors.append(''.join(error.splitlines()))
                before = json_string[:found_start]
                after = json_string[found_end+3:]
                json_string = before + after
                found_start = json_string.find('[Failure instance:')

        if errors:
            errmsg = 'the following errors found in returned JSON string :'
            print server_error, errmsg
            for error in errors:
                print error
            if request_detail is not None:
                errmsg = 'Station data block may be incomplete for'
                print errmsg, request_detail
            else:
                errmsg = 'The resulting station data block may be incomplete.'
            sys.stdout.flush()

        try:
           return json.loads(json_string)
        except:
            errmsg += 'unable to handle improperly formated JSON from server.\n'
            errmsg += response.geturl() + '\n'
            if request_detail is not None:
                errmsg += request_detail + '\n'
            errmsg += json_string
            reportException(errmsg)

