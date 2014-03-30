
import os, sys
from copy import deepcopy
from datetime import datetime
import time
import urllib2

import numpy as N

from atmosci.base.manager import DatasetKey
from atmosci.utils.report import Reporter

from atmosci.stations.multi import AcisMultiStationDataClient
from atmosci.stations.manager import StationDataFileManager
from atmosci.stations.utils import elementID, indexableElementID, postal2ncdc

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.stations.client import ALL_NON_NUMERIC_ELEMS

from atmosci.stations.elements import OBS_FLAG_KEYS, OBS_TIME_KEYS
from atmosci.stations.elements import OBSERVED_PREFIX

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def evalObsFlag(obs_value, obs_flag):
    if obs_flag == ' ' and obs_value in ('M','T','S'):
        return obs_value.encode('ascii','ignore')
    return obs_flag.encode('ascii','ignore')

def evalObsValue(element_id, obs_value, obs_flag):
    if element_id not in ALL_NON_NUMERIC_ELEMS:
        if obs_flag == 'T' or obs_value == 'T':
            return 0.005
        elif obs_flag in ('M','S') or obs_value in ('M','S'):
            return N.inf
        else:
            value = float(obs_value)
            if element_id == 'pcpn' and value < 0:
                return N.nan
            return value
    # flags don't change the value of non-numeric elements
    return obs_value

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class StationDataFileBuilder(object):
    """ Retrieves station data for a group of states and writes it to a file.
    """

    REQUIRED_METADATA = ('uid','ll','elev')
    REQUIRED_ELEMS = ()

    def __init__(self, station_manager_class, station_data_filepath, elems=(),
                       metadata=(), base_url=None, file_attrs=(),
                       server_reset_wait_time=30, reporter_or_filepath=None,
                       **request_args):
        self.station_manager_class = station_manager_class
        self.station_data_filepath = station_data_filepath

        if elems:
             self.elements = self._guaranteeRequiredElements(elems)
        else:
            self.elements = self.REQUIRED_ELEMS

        self.element_ids = [ ]
        for element in self.elements:
            elem_id = indexableElementID(element)
            self.element_ids.append(elem_id)

        if metadata:
            self.metadata = tuple( set(self.REQUIRED_METADATA) | set(metadata) )
        else:
            self.metadata = self.REQUIRED_METADATA

        if base_url is None:
            self.client = AcisMultiStationDataClient()
        else:
            self.client = AcisMultiStationDataClient(base_url)

        self.file_attrs = file_attrs
        self.server_reset_wait_time = server_reset_wait_time

        # create a reporter for perfomance and debug
        if isinstance(reporter_or_filepath, Reporter):
            self.reporter = reporter_or_filepath
        else:
            self.reporter = Reporter(self.__class__.__name__,
                                     reporter_or_filepath)
            self.reporter.close()

        self.request_args = request_args
        self.extension_data = { }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, date, states, max_attempts=1, debug=False,
                       performance=False):
        state_error = "attempt %d to retrieve stations for %s failed"
        self.client.debug = debug
        reporter = self.reporter
        
        if performance:
            msg = "Attempting to download stations for %d states :"
            reporter.logInfo(msg % len(states))

        start_perf = datetime.now() # for performance reporting

        num_states = len(states)
        station_data = None
        required_meta_key = self.REQUIRED_METADATA[0]

        attempts = 0
        total_stations = 0
        total_valid = 0
        while len(states) > 0 and attempts < max_attempts:
            attempts += 1
            do_over_states = [ ]

            for state in states:
                try:
                    results = self.allStationsInState(state, date, performance)
                except urllib2.HTTPError as e:
                    if attempts >= max_attempts: raise
                    
                    if e.code >= 400 and e.code < 500:
                        reporter.logError('REQUEST : %s' +
                                          state_error % (attempts, state))
                    elif e.code >= 500:
                        reporter.logError('ACIS SERVER : ' +
                                          state_error % (attempts, state))
                    reporter.logError('HTTP response code = %s' % str(e.code))

                    # recoverable errors
                    if e.code in (500, 502, 503, 504, 598, 599):
                        do_over_states.append(state)
                        reporter.logInfo('waiting for server to clear ...')
                        time.sleep(self.server_reset_wait_time)

                    else: # no recovery path
                        errmsg = 'Build of station data file failed : %s'
                        reporter.reportError(errmsg %
                                             self.station_data_filepath)
                        raise

                except urllib2.URLError as e:
                    if attempts >= max_attempts: raise
                    
                    reporter.logError('urllib2 : ' +
                                      state_error % (attempts, state))
                    reporter.logException('urllib2.URLError')
                    # these errors are temporary and often recoverable
                    do_over_states.append(state)

                except Exception as e:
                    reporter.logException(state_error % (attempts, state))
                    # must assume that unknown exceptions are not recoverable
                    raise

                else:
                    num_stations, state_data = results
                    total_stations += num_stations
                    if state_data:
                        if station_data is not None:
                            for key in station_data:
                                station_data[key] += state_data[key]
                            total_valid += len(state_data[required_meta_key])
                        else:
                            station_data = state_data
                            total_stations = num_stations
                            total_valid = len(station_data[required_meta_key])

            # reset state list to those that failed
            states = do_over_states

        if len(do_over_states) > 0:
            errmsg = "SERVER ERROR : Unable to download data for %d states : "
            errmsg += str(tuple(do_over_states))
            raise RuntimeError, errmsg % len(do_over_states)

        if total_stations == 0:
            errmsg = "No station data available at the time of this run"
            raise LookupError, errmsg

        if performance:
            msg = 'Download %d stations from %d states in'
            reporter.logPerformance(start_perf,
                                    msg % (total_stations,num_states))

        start_save = datetime.now() # for performance reporting
        if 'obs_date' not in self.file_attrs:
            file_attrs = { 'obs_date':date, }
            file_attrs.update(self.file_attrs)
            manager = self.newStationFileManager(station_data['lon'],
                                                 station_data['lat'],
                                                 file_attrs)
        else:
            manager = self.newStationFileManager(station_data['lon'],
                                                 station_data['lat'],
                                                 self.file_attrs)
        del station_data['lon']
        del station_data['lat']

        num_datasets = len(station_data.keys()) + 2
        self._saveDatasets(date, manager, station_data)
        manager.closeFile()
        del station_data
        del self.extension_data
        self.extension_data = { }

        if performance:
            msg = 'Saved %d datasets of %d observations each in'
            reporter.logPerformance(start_save,
                                    msg % (num_datasets,total_valid))

        return total_valid, total_stations

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def allStationsInState(self, state, date, performance):
        start_state = datetime.now()
        num_stations = 0
        num_valid = 0
        ncdc_code = postal2ncdc(state)
        required = set(self.REQUIRED_METADATA)
        station_data = { }

        stations = self.client.allStationsInState(state, self.elements, date, 
                                                  self.metadata,
                                                  **self.request_args)
        num_stations = len(stations['data'])
        if num_stations < 1:
            if performance:
                self.statePerfSummary(start_state, state, 0, 0) 
            return 0, station_data

        # list of data elements returned by ACIS
        elements = deepcopy(stations['elems'])
        data_keys = [indexableElementID(element) for element in elements]

        # only keep stations that have all required metadata
        usable = [row for row in stations['data']
                  if (set(row['meta'].keys()) & required) == required]
        if len(usable) < 1:
            if performance:
                self.statePerfSummary(start_state, state, num_stations, 0) 
            return 0, station_data

        del stations
        meta_keys = usable[0]['meta'].keys()

        # merge metadata values and data values into a single list
        merged = [row['meta'].values() + row['data'] for row in usable]
        del usable

        # reorganize merged station data into ordered lists of values
        # corresponding each metadata and obs data key
        all_keys = meta_keys + data_keys

        for indx in range(len(all_keys)):
            station_data[all_keys[indx]] = [row[indx] for row in merged]
        del merged

        # break up multi-component values in station data arrays
        if 'll' in station_data:
            station_data['lon'] = [value[0] for value in station_data['ll']]
            station_data['lat'] = [value[1] for value in station_data['ll']]
            del station_data['ll']

        for element in elements:
            key = indexableElementID(element)
            data = station_data[key]

            # additon data descriptors requested
            if 'add' in element:
                # observation time
                if 't' in element['add']:
                    t_key = OBS_TIME_KEYS.get(key, key+'_obs_time')
                    indx = element['add'].index('t') + 1
                    station_data[t_key] = [obs[indx] for obs in data]
                # data "correctness" flag
                if 'f' in element['add']:
                    f_key = OBS_FLAG_KEYS.get(key, key+'_obs_flag')
                    indx = element['add'].index('f') + 1
                    flags = [evalObsFlag(obs[0],obs[indx]) for obs in data]
                    station_data[f_key] = flags
                    data = [evalObsValue(key,obs[0],obs[indx]) for obs in data]
                else:
                    data = [evalObsFlag(key,obs[0],' ') for obs in data]
            else:
                data = [evalObsFlag(key,obs[0],' ') for obs in data]
            if key == 'pcpn':
                bad_indexes = [indx for indx in range(len(data)) 
                                    if N.isnan(data[indx])]
                if bad_indexes:
                    print 'WARNING: Invalid precip values at', str(bad_indexes)
                    sys.stdout.flush()

            station_data[key] = data

        # handle change in name of dataset sent by ACIS web services
        # used to be named 'postal', downstream now expects 'state'
        if 'state' not in station_data:
            station_data['state'] = [state for stn in station_data['lon']]
        if 'ncdc' not in station_data:
            station_data['ncdc'] = [ncdc_code for stn in station_data['lon']]
        if 'name' in station_data:
            station_data['name'] = [name.encode('iso-8859-1')
                                    for name in station_data['name']]

        station_data = self.validStations(state, station_data)
        num_valid = len(station_data[self.REQUIRED_METADATA[0]])

        self._processExtensionDatasets(station_data)

        if performance:
            self.statePerfSummary(start_state, state, num_stations, num_valid) 

        return num_stations, station_data

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def statePerfSummary(self, elapsed_time, state, num_stations, num_valid):
        msg = 'downloaded %d stations for %s (%d usable) in'
        self.reporter.logPerformance(elapsed_time,
                                     msg % (num_stations, state, num_valid))

    def validStations(self, state, station_data):
        return station_data

    def newStationFileManager(self, lons, lats, file_attrs):
        datasets = ( ('lon', N.array(lons), None),
                     ('lat', N.array(lats), None),
                   )
        return self.station_manager_class.newFile(self.station_data_filepath,
                                                  file_attrs, datasets)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _guaranteeRequiredElements(self, elements):
        elements = list(elements)
        elem_ids = [elementID(element) for element in elements]
        for required in self.REQUIRED_ELEMS:
            req_id = elementID(required)
            if req_id not in elem_ids:
                elements.append(required)
        return tuple(elements)

    def _processExtensionDatasets(self, station_data):
        pass

    def _saveDataset(self, manager, dataset_name, data, attributes=None):
        if not isinstance(data, N.ndarray):
            data = manager._dataAsArray(dataset_name, data)
        try:
            manager.createDataset(dataset_name, data, attributes)
        except Exception as e:
            errmsg = "Failed to create '%s' dataset."
            self.reporter.logException(errmsg % dataset_name)
            raise

    def _saveDatasets(self, obs_date, manager, data_arrays):
        manager.setOpenState(True)

        elems = [elem_id for elem_id in self.element_ids]
        elems.extend([OBSERVED_PREFIX+elem_id for elem_id in self.element_ids])

        for dataset_name, data in data_arrays.items():
            if dataset_name in elems:
                attrs = { 'obs_date':obs_date, }
                self._saveDataset(manager, dataset_name, data, attrs)
            else:
                self._saveDataset(manager, dataset_name, data)
        
        for dataset_name, data in self.extension_data.items():
            self._saveDataset(manager, dataset_name, data)

        manager.setOpenState(False)

