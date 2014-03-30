
from datetime import datetime
from dateutil.relativedelta import relativedelta
from copy import copy

import Data, Meta
UnknownUcanId = Meta.MetaQuery.UnknownUcanId
import ucanCallMethods

import numpy as N

from atmosci.utils.data import safedict, AsciiSafeDict
from atmosci.utils.timeutils import dateAsTuple, asDatetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.stations.vardefs import ELEM_TO_TSVAR_MAP

ONE_HOUR = relativedelta(hours=1)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UcanError(Exception): pass
class UcanDateMismatchError(UcanError): pass
class UcanCorbaError(UcanError): pass
class UcanInvalidElementError(UcanError): pass
class UcanInvalidTsvarError(UcanError): pass
class UcanUknownError(UcanError): pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UcanUndefinedElementError(Exception): pass

def getTsVarFromMap(network, element_name):
    try:
        return ELEM_TO_TSVAR_MAP[network][element_name]
    except:
        errmsg = 'TsVar codes have not been defined for %s on the %s network'
        raise UcanUndefinedElementError, errmsg % (element_name, network)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UcanErrorExplanation(Exception): pass

def getExplanation(e, station_dict, detail):
    args = list(e.args)
    msg = ' %s : %s' % (e.__class__.__name__,repr(e))
    args.insert(0, msg)
    msg = 'Station %(ucanid)d : %(name)s : %(network)s' % station_dict
    args.append(msg)
    args.append(detail)
    return '\n'.join([str(arg) for arg in args])

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class UcanConnection(object):

    def __init__(self, elem_codeset_function=None, base_time=None,
                       first_hour_in_day=0, max_days_per_request=30):
        self.getTsVarCodesets = elem_codeset_function

        if base_time is None:
            self.base_time = datetime(1900,1,1,0)
        elif isinstance(base_time, (tuple,list)):
            if len(base_time) == 4:
                self.base_time =datetime(*base_time)
            elif len(base_time) == 3:
                if isinstance(base_time, tuple):
                    _base_time_ = list(base_time)
                else: _base_time_ = copy(base_time)
                _base_time_.append(0)
                self.base_time = datetime(*_base_time_)
            else:
                errmsg = "Invalid value for `base_time` argument : %s"
                raise ValueError, errmsg % str(base_time)
        else:
            errmsg = "Invalid type for `base_time` argument : %s"
            raise ValueError, errmsg % str(type(base_time))
            
        self.first_hour_in_day = first_hour_in_day
        self.hours_per_request = max_days_per_request*24
        self.request_delta = relativedelta(hours=self.hours_per_request)

        self.ucan = ucanCallMethods.general_ucan()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, station_dict, major, minor, start_date=None,
                      end_date=None, dtype=float, units=None,
                      fill_data_gaps=True, debug=False):
        _station_ = self._tsvarSafeDict(station_dict)
        sid = self._getStationId(_station_, False)
        ucanid = station_dict['ucanid']

        # open connection to the CORBA server
        try:
            ts_var = self.getTsVar(_station_, major, minor)
        except UcanInvalidTsvarError, e:
            errmsg = '%s is not a valid element for station %d'
            errmsg = errmsg % (elem,_station_['ucanid'])
            raise UcanInvalidElementError, errmsg

        # tell the server what unitswe want
        if units is not None and not callable(units):
            try:
                ts_var.setUnits(units)
            except Exception as e:
                detail = "failed call to ts_var.setUnits('%s') for (%d,%d)"
                explanation = getExplanation(e, _station_,
                                             detail % (units,major,minor))
                raise UcanErrorExplanation, explanation

        # tell the server what value we want back for missing data
        if dtype == float:
            ts_var.setMissingDataAsFloat(-32768.)

        start_time, end_time, start_gap, end_gap =\
        self._validIntervalAndGaps(ts_var, start_date, end_date, debug)

        # add ONE_HOUR to end_time because ts_var always returns one hour
        # less than requested
        end_time += ONE_HOUR

        # accumulate data array
        hourly_data = [ ]
        time_spans = self.getReasonableTimeSpans(start_time, end_time)
        for start_span, end_span in time_spans:
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

        # release connection to the CORBA server
        ts_var.release()

        if fill_data_gaps:
            # fill data gaps at each end
            if start_gap is not None:
                hourly_data = start_gap + hourly_data
                start_time -= relativedelta(hours=len(start_gap))
            if end_gap is not None:
                hourly_data.extend(end_gap)
                end_time += relativedelta(hours=len(end_gap))

        if debug:
            msg = '%s %d : num hours = %d : num_days = %d'
            num_hours = len(hourly_data)
            print msg % (sid,ucanid, num_hours, num_hours/24)

        # take back the hour we added so ts_var would give us all the data
        end_time -= ONE_HOUR

        return start_time, end_time, N.array(hourly_data, dtype=dtype)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getMetadata(self, station_dict):
        _station_dict_ = self._tsvarSafeDict(station_dict)
        query = self.ucan.get_query()
        try:
            metadata = query.getInfoForUcanIdAsSeq(_station_dict_['ucanid'],())
            metadata = ucanCallMethods.NameAny_to_dict(metadata[-1].fields)
            if 'id' in metadata and isinstance(metadata['id'], int):
                metadata['id'] = str(metadata['id'])
            return metadata
        except:
            raise
        finally:
            query.release()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getOneDay(self, station, dataset_name, date, debug=False):
        # returns data for a single 24-hour period
        start_time, end_time = self._get24HourTimeSpan(date)
        return  self.getData(station, dataset_name, start_time, end_time, debug)

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def getCodesets(self, station_dict, dataset, start_time=None, end_time=None,
                          debug=False):
        """ returns a tuple of each ts_var requeired to cover time span
            when start_time and end_time are set to None, all available
            codesets are returned
        """
        if start_time is not None: d_start_time = asDatetime(start_time)
        else: d_start_time = self.base_time
        if end_time is not None: d_end_time = asDatetime(end_time)
        else: d_end_time = latest_safe_time

        latest_safe_time = self._latestSafeTime()
        _station_ = self._tsvarSafeDict(station_dict)

        # figure out which ts_vars are needed to complete the request
        majors = [ ]
        ts_vars = [ ]
        for codeset in self.getTsVarCodesets(_station_['network'], dataset):
            major = codeset['major']
            minor = codeset['minor']
            if major in majors and minor == 0: continue
            try:
                tsvar = self.getTsVar(_station_, major, minor)
            except (UcanInvalidTsvarError, UcanCorbaError):
                continue

            span = tsvar.getValidDateRange()
            tsvar.release()
            tsv_start_time = asDatetime(span[0])
            tsv_end_time = asDatetime(span[1])
            if tsv_start_time > d_end_time\
            or tsv_end_time < d_start_time: continue

            ts_vars.append((codeset,tsv_start_time,tsv_end_time))
            majors.append(major)

        # none or one ts_var in time interval
        if len(ts_vars) < 2: return ts_vars

        # ts_vars must be sorted by ascending start date
        ts_vars.sort(key=lambda tsv: tsv[1])

        # adjust or eliminate overlapping ts_vars
        adjusted = [ts_vars[0],]
        prev_end_time = ts_vars[0][-1]

        for codeset, tsv_start_time, tsv_end_time in ts_vars[1:]:
            if tsv_end_time > prev_end_time:
                if tsv_start_time < prev_end_time:
                    tsv_start_time = prev_end_time + ONE_HOUR
                adjusted.append((codeset,tsv_start_time,tsv_end_time))
                prev_end_time = tsv_end_time
        return adjusted

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getReasonableTimeSpans(self, start_time, end_time):
        # break up time span into self.hours_per_request increments due to
        # tsvar/ucan server limitations
        start_span = copy(start_time)
        spans = [ ]
        while start_span < end_time:
            hours = self._elapsedTime(start_span, end_time)
            if hours > self.hours_per_request:
                end_span = start_span + self.request_delta
            else:
                end_span = end_time
            spans.append( (start_span, end_span) )
            # set next 'start_span' to previous `end_span` because ts_var
            # always returns one hour less than requested
            start_span = end_span
        return spans

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getTsVar(self, station_dict, major, minor=0):
        _station_ = self._tsvarSafeDict(station_dict)
        data = self.ucan.get_data()
        try:
            if _station_['network'] == 'icao':
                station_id = self._getStationId(_station_, True)
                return data.newTSVarNative(major, minor, station_id)
            else:
                return data.newTSVar(major, minor, _station_['ucanid'])
        except Exception as e:
            data.release()
            errmsg = '(%d,%d) is not a valid tsvar for station %d'
            errmsg = errmsg % (major, minor, _station_['ucanid'])
            if e.__class__.__name__ == 'UnknownUcanId':
                raise UcanInvalidTsvarError, errmsg
            else:
                ucan_msg = str(e)
                if 'CORBA' in ucan_msg or 'omnoORB' in ucan_msg:
                    raise UcanCorbaError, '%s\n%s' % (errmsg, ucan_msg)
                else:
                    raise UcanUknownError, '%s\n%s' % (errmsg, ucan_msg)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getValidDateRange(self, station_dict, major, minor, debug=False):
        _station_ = self._tsvarSafeDict(station_dict)
        try:
           ts_var = self.getTsVar(_station_, major, minor)
        except UcanInvalidTsvarError, e:
            errmsg = '%s is not a valid element for station %d'
            errmsg = errmsg % (elem,_station_dict['ucanid'])
            raise UcanInvalidElementError, errmsg

        start_time, end_time = ts_var.getValidDateRange()
        ts_var.release()

        return datetime(*start_time), datetime(*end_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ucanid(self, station_dict):
        _station_dict_ = self._tsvarSafeDict(station_dict)
        station_id = self._getStationId(_station_dict_, True)
        try:
            query = self.ucan.get_query()
            result = query.getUcanFromIdAsSeq(station_id,
                                              _station_dict_['network'])
        except:
            raise
        finally:
            query.release()

        if len(result) > 0:
            return int(result[-1].ucan_id)
        else:
            errmsg = 'Unable to acquire UCAN id for %s : %s'
            raise KeyError, errmsg % (station_id, _station_dict_['name'])

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def _elapsedTime(self, start_time, end_time, as_hours=True):
        delta = asDatetime(end_time) - asDatetime(start_time)
        if as_hours: return (delta.days * 24) + (delta.seconds / 3600)
        else: return delta.days

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _get24HourTimeSpan(self, date):
        _time = list(dateAsTuple(date)[:3])
        _time.append(self.first_hour_in_day)
        start_time = asDatetime(*_time)
        end_time = start_time + ONE_DAY
        return start_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _getStationId(self, station_dict, encode=True):
        _station_dict = self._tsvarSafeDict(station_dict)
        if 'id' in _station_dict:
            if isinstance(_station_dict['id'], int):
                 return str(_station_dict['id'])
            else:
                if encode: return _station_dict['id'].upper().encode('ascii')
                else: return _station_dict['id']
        else:
            if isinstance(_station_dict['sid'], int):
                 return str(_station_dict['sid'])
            else:
                if encode: return _station_dict['sid'].upper().encode('ascii')
                else: return _station_dict['sid']

     # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _latestSafeTime(self):
        return datetime(*datetime.now().timetuple()[:4]) - ONE_HOUR

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _tsvarSafeDict(self, station_dict):
        station_dict['network'] = station_dict['network'].encode('iso-8859-1')
        if not isinstance(station_dict, AsciiSafeDict): 
            return AsciiSafeDict.makeSafe(station_dict, True)
        else: return station_dict
        
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _validIntervalAndGaps(self, ts_var, start_date, end_date, debug=False):
        start_range, end_range = ts_var.getValidDateRange()
        if start_date is None:
            start_time = max(self.base_time, asDatetime(start_range))
        else: start_time = asDatetime(start_date)

        # add ONE_HOUR to end_time because ts_var always returns one hour
        # less than requested
        if end_date is None: end_time = asDatetime(end_range)
        else: end_time = asDatetime(end_date)

        if debug:
            print sid, ucanid, elem, 'requested', start_date, end_date
            print sid, ucanid, elem, 'available', start_range, end_range
            print sid, ucanid, elem, 'useable  ', start_time, end_time
        
        start_gap = None
        gap = self._elapsedTime(start_time, start_range)
        if gap > 0: start_gap = [-32768. for i in range(start_gap)]

        end_gap = None
        gap = self._elapsedTime(end_range, end_time)
        if gap > 0: end_gap = [-32768. for i in range(end_gap)]
        if debug:
            print sid, ucanid, elem, 'gaps     ', start_gap, end_gap

        return start_time, end_time, start_gap, end_gap

