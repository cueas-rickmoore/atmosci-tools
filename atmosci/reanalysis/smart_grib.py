
import datetime
ONE_HOUR = datetime.timedelta(hours=1)
import warnings

import numpy as N
import pygrib

from atmosci.utils import tzutils
from atmosci.utils.timeutils import lastDayOfMonth

from atmosci.seasonal.methods.static  import StaticFileAccessorMethods

from atmosci.reanalysis.factory import ReanalysisGribFactoryMethods


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartReanalysisGribMethods(StaticFileAccessorMethods):

    def completeInitialization(self, **kwargs):
        self.data_mask = None
        self.grib_indexes = None
        self.grib_region = kwargs.get('grib_region', 'conus')
        self.grid_region = grid_region = kwargs.get('grid_region', 'NE')
        self.grid_shape = None
        grid_source = kwargs.get('grid_source', 'acis')
        self.grid_source = self.sourceConfig(grid_source)
        dims = self.sourceConfig('reanalysis.grid').dimensions[grid_region]
        self.grid_dimensions = (dims.lat, dims.lon)
        self.shared_grib_dir = kwargs.get('shared_grib_dir', True)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dataForHour(self, variable, grib_hour, **kwargs):
        debug = kwargs.get('debug', False)
        verbose = kwargs.get('verbose', False)
        return_units = kwargs.get('return_units', False)

        found, reader = self.gribFileReader(grib_hour, variable),
        if verbose: print '\nreading data from :\n    ', reader.filepath
        if not found:
            filepath = self.gribFilepath(grib_time, variable, self.grib_region)
            return False, (grib_time, filepath)

        # read the message
        try:
            message = reader.messageFor(variable)
        except Exception as e:
            return False, (grib_time, reader.filepath)

        units = message.units
        if debug:
            print 'message retrieved :\n    ', message
            print '\n            grib_time :', message.dataTime
            print '             analDate :', message.analDate
            print '            validDate :', message.validDate
            print '             dataDate :', message.dataDate
            print '             dataTime :', message.dataTime
            print '         forecastTime :', message.forecastTime
            print '         validityDate :', message.validityDate
            print '           data units :', units

        data = message.values[self.grib_indexes]
        missing_value = float(message.missingValue)
        reader.close()
        del message
        del reader

        if N.ma.is_masked(data): data = data.data
        if debug: print '      retrieved shape :', data.shape
        data = data.reshape(self.grid_shape)
        if debug: print '           grid shape :', data.shape

        data[N.where(data >= missing_value)] = N.nan

        if debug:
            print '... before applying mask'
            print '        missing value :', missing_value
            print '         missing data :', len(N.where(N.isnan(data))[0])
            print '           valid data :', len(N.where(N.isfinite(data))[0])
            print '\n        data extremes :', N.nanmin(data), N.nanmean(data), N.nanmax(data)

        # apply the regional boundary mask
        data[N.where(self.data_mask == True)] = N.nan

        if debug:
            print '... after applying mask'
            print '         missing data :', len(N.where(N.isnan(data))[0])
            print '           valid data :', len(N.where(N.isfinite(data))[0])

        if return_units: package = (units, data)
        else: package = data

        return True, package

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def readerForHour(self, variable, hour):
        try:
            reader = self.gribFileReader(hour, variable, self.grib_region,
                                         shared_grib_dir=self.shared_grib_dir,
                                         file_must_exist=True)
            return True, reader

        except IOError: # IOError means file for this hour does not exist
            filepath = self.gribFilepath(grib_time, variable, self.grib_region)
            return False, (grib_time, filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def slices(self, data_start_time, data_end_time, hours_per_slice=24):

        num_hours = tzutils.hoursInTimespan(data_start_time, data_end_time)
        if num_hours <= hours_per_slice:
            return ((data_start_time, data_end_time),)

        slices = [ ]
        increment = datetime.timedelta(hours=hours_per_slice-1)
        
        slice_start = data_start_time
        while slice_start <= data_end_time:
            slice_end = min(slice_start + increment, data_end_time)
            slices.append((slice_start, slice_end))
            slice_start = slice_end + ONE_HOUR

        return tuple(slices)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timeSlice(self, variable, slice_start_time, slice_end_time, **kwargs):
        failed = [ ]

        if self.grib_indexes is None: self._initStaticResouces_()

        # filter annoying numpy warnings
        warnings.filterwarnings('ignore',"All-NaN axis encountered")
        warnings.filterwarnings('ignore',"All-NaN slice encountered")
        warnings.filterwarnings('ignore',"invalid value encountered in greater")
        warnings.filterwarnings('ignore',"invalid value encountered in less")
        warnings.filterwarnings('ignore',"Mean of empty slice")
        # MUST ALSO TURN OFF WARNING FILTERS AT END OF SCRIPT !!!!!

        region = kwargs.get('region', self.region)
        
        grib_start_time = tzutils.tzaDatetime(slice_start_time, self.tzinfo)
        grib_end_time = tzutils.tzaDatetime(slice_end_time, self.tzinfo)
        num_hours = tzutils.hoursInTimespan(grib_start_time, grib_end_time)

        data = N.empty((num_hours,)+self.grid_dimensions, dtype=float)
        data.fill(N.nan)

        units = None
        date_indx = 0
        grib_time = grib_start_time
        while units is None and grib_time <= grib_end_time:
            success, package = self.dataForHour(variable, grib_time,
                                                return_units=True, **kwargs)
            if success:
                units, data_for_hour = package
                data[date_indx,:,:] = data_for_hour
            else: failed.append(package)

            grib_time += ONE_HOUR
            date_indx += 1

        while grib_time <= grib_end_time:
            success, data_for_hour = \
                self.dataForHour(variable, grib_time, **kwargs)
            if success: data[date_indx,:,:] = data_for_hour
            else: failed.append(data_for_hour)

            grib_time += ONE_HOUR
            date_indx += 1

        # turn annoying numpy warnings back on
        warnings.resetwarnings()

        return units, data, tuple(failed)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _dataForVariable(self, reader, variable, grib_time):
        # read the message
        try:
            message = reader.messageFor(variable)
        except Exception as e:
            return False, (grib_time, reader.filepath)

        units = message.units
        data = message.values[self.grib_indexes]
        missing_value = float(message.missingValue)
        del message

        if N.ma.is_masked(data): data = data.data
        data = data.reshape(self.grid_shape)
        # set all missing values to NaN
        data[N.where(data >= missing_value)] = N.nan
        # apply the regional boundary mask
        data[N.where(self.data_mask == True)] = N.nan

        return True, (units, data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initStaticResouces_(self):
        reader = self.staticFileReader(self.grid_source, self.grid_region)
        self.grid_shape, self.grib_indexes = reader.gribSourceIndexes('ndfd')
        # get the region boundary mask
        self.data_mask = reader.getData('cus_mask')
        reader.close()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SmartReanalysisGribReader(SmartReanalysisGribMethods,
                                ReanalysisGribFactoryMethods, object):

    def __init__(self, analysis_source, grid_source, grid_region,
                       config_object=CONFIG, **kwargs):

        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, 'project')

        # initialize reanalysis grib-specific configuration
        self._initReanalysisGribFactory_(analysis_source, **kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)

