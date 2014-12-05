
import sys
import urllib, urllib2

try:
    import simplejson as json
except ImportError:
    import json

from atmosci.utils.timeutils import asDatetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AcisWebServicesClient:

    def __init__(self, base_url='http://data.rcc-acis.org/', debug=False):

        self.base_url = base_url
        self.debug = debug
        self.last_query = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def request(self, *args, **request_dict):
        raise NotImplementedError

    def submitRequest(self, data_type, **request_dict):
        query_json = self.jsonFromRequest(data_type, request_dict)
        return self.submitQuery(data_type, query_json)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def query(self, json_string):
        raise NotImplementedError

    def submitQuery(self, data_type, json_string):
        ERROR_MSG = 'Error processing response to query : %s %s'

        if not isinstance(json_string, basestring):
            raise TypeError, '"json_string" argument must be a string'
        try:
            json_query_dict = json.loads(json_string)
        except:
            errmsg = '"json_string" argument is not a valid JSON string :\n%s'
            raise ValueError, errmsg % json_string
            
        url = self.base_url
        if url.endswith('/'):
            if data_type.startswith('/'): url += data_type[1:]
            else: url += data_type
        else:
            if data_type.startswith('/'): url += data_type
            else: url += '/' + data_type

        if self.debug:
            print 'POST', url
            print 'params =', json_string

        post_params = urllib.urlencode({'params':json_string})
        req = urllib2.Request(url, post_params,
                              { 'Accept':'application/json' }
                             )
        url += ' json=' + post_params
        try:
            response = urllib2.urlopen(req)
        except Exception as e:
            setattr(e, 'details', ERROR_MSG % ('POST',url))
            raise e

        try:
            response_string = response.read()
        except Exception as e:
            setattr(e, 'details', ERROR_MSG % ('POST',url))
            raise e

        # track last successful query
        self.last_query = json_string

        return response_string, response

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def acisDateString(self, date):
        return asDatetime(date).strftime('%Y-%m-%d')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def jsonFromRequest(self, data_type, request_dict):
        # look for a valid date or date range
        query_dict = self._validateRequestDate(request_dict)

        # make sure there is a valid location for this type of request
        key, location = self._validateLocation(date_type, request_dict)
        query_dict[key] = location

        # metadata
        metadata = self._validateMetadata(request_dict)
        if metadata is not None: query_dict['meta'] = metadata

        # data elements
        if 'Data' in data_type:
            query_dict['elems'] = self._validateDataElems(request_dict)

        return json.dumps(query_dict)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def jsonToPython(self, response_string, response):
        """ Convert a json string to Python objects ... handle known instances
        where server injects badly formed JSON into the stream
        """
        if 'DOCTYPE HTML PUBLIC' in response_string:
            errmsg = 'SERVER ERROR : '
            if 'server encountered an internal error' in response_string:
                errmsg += 'server encountered an unspecified internal error.'
                ecode = 503
            else:
                ecode = 500
                errmsg += 'server returned HTML, not valid JSON.\n'
                errmsg += response_string
            raise urllib2.HTTPError(response.geturl(),ecode,errmsg,None,None)

        server_error = 'SERVER ERROR : '
        errors = [ ]
        if '[Failure instance:' in response_string:
            found_start = response_string.find('[Failure instance:')
            while found_start > 0:
                found_end = response_string.find('\n],',found_start)
                error = response_string[found_start:found_end+3]
                errors.append(''.join(error.splitlines()))
                before = response_string[:found_start]
                after = response_string[found_end+3:]
                response_string = before + after
                found_start = response_string.find('[Failure instance:')
        if errors:
            errmsg = 'the following errors found in returned JSON string :'
            print server_error, errmsg
            for error in errors:
                print error
            print 'The resulting data block may be incomplete.'
            sys.stdout.flush()

        try:
           return json.loads(response_string)
        except Exception as e:
            errmsg += 'unable to handle improperly formated JSON from server.\n'
            errmsg += response.geturl() + '\n'
            errmsg += 'Returned JSON = ' + response_string
            setattr(e, 'details', errmsg)
            raise e

    # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - # - #

    def _validateDataElems(self, request_dict):
        if'elems' in request_dict: return request_dict['elems']
        raise KeyError, "'elems' key missing from query." % data_type

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _validateRequestDate(self, request_dict):
        if 'date' in request_dict:
            return { 'date' : self.acisDateString(request_dict['date']) }
        elif 'sdate' in request_dict and 'edate' in request_dict:
            return { 'sdate' : self.acisDateString(request_dict['sdate']),
                     'edate' : self.acisDateString(request_dict['edate']) }
        else: 
            raise KeyError, 'Request has no date or an incomplete date span.'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _validateLocation(self, date_type, request_dict):
        # make sure there is a valid location in the request
        if data_type == 'StnData': loc_keys = ['sid',]
        elif data_type == 'MultiStnData':
            loc_keys = ['state','county','climdiv','cwa','basin','bbox','sids']
        elif data_type == 'StnMeta':
            loc_keys = ['state','county','climdiv','cwa','basin','bbox']
        elif data_type == 'GridData':
            loc_keys = ['state','bbox','loc']
        elif data_type == 'General':
            loc_keys = ['state','county','climdiv','cwa','basin']

        union = set(loc_keys) & set(request_dict)

        if len(union) == 0:
            raise KeyError, "No location key in %s query." % data_type
        elif len(union) > 1:
            raise KeyError, "Multiple location keys in %s query." % data_type

        key = union[0]
        return key, request_dict[key]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _validateMetadata(self, request_dict):
        return request_dict.get('meta', request_dict.get('metadata', None))

