""" Classes for accessing data from Hdf5 encoded grid files.
"""

import os

import numpy as N

from atmosci.utils.timeutils import asDatetime, asDatetimeDate
from atmosci.utils.timeutils import dateAsInt, matchDateType

from atmosci.hdf5.grid import Hdf5GridFileReader, Hdf5GridFileManager
from atmosci.hdf5.grid import Hdf5GridFileBuilder

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

TIME_SPAN_ERROR = 'Invalid time span. '
TIME_SPAN_ERROR += 'Either "date" OR "start_date" plus "end_date" are required.'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5DateGridReaderMixin(object):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    def getDataAtNode(self, dataset_name, lon, lat, start_date=None,
                            end_date=None, **kwargs):
        y, x = self.ll2index(lon, lat)
        if start_date is None:
            data = self.getDataset(dataset_name).value[:, y, x]
        else:
            if end_date is None:
                indx = self._indexForDate(dataset_name, date)
                data = self.getDataset(dataset_name).value[indx, y, x]
            else:
                start, end = \
                self._indexesForDates(dataset_name, start_date, end_date)
                data = self.getDataset(dataset_name).value[start:end, y, x]
        return self._processDataOut(dataset_name, data, **kwargs)
    dataAtNode = getDataAtNode

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDataForDate(self, dataset_name, date, **kwargs):
        indx = self._indexForDate(dataset_name, date)
        dataset = self.getDataset(dataset_name)
        return self._processDataOut(dataset_name, dataset[indx], **kwargs)
    dataForDate = getDataForDate
    
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDataSince(self, dataset_name, date, **kwargs):
        return self.getDateSlice(dataset_name, date, self.end_date, **kwargs)
    dataSince = getDataSince

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDataThru(self, dataset_name, date, **kwargs):
        return self.getDateSlice(dataset_name, self.start_date, date, **kwargs)
    dataThru = getDataThru

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDateAttribute(self, object_path, attribute_name, default=None):
        date = self.getObjectAttribute(object_path, attribute_name, default)
        if date is not None: return asDatetimeDate(date)
        return None
    dateAttribute = getDateAttribute

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDateSlice(self, dataset_name, start_date, end_date, **kwargs):
        start, end = self._indexesForDates(dataset_name, start_date, end_date)
        dataset = self.getDataset(dataset_name)
        data = self._dateSlice(dataset, start, end)
        return self._processDataOut(dataset_name, data, **kwargs)
    dateSlice = getDateSlice

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def get3DSlice(self, dataset_name, start_date, end_date, min_lon, max_lon,
                         min_lat, max_lat, **kwargs):
        min_y, min_x = self.ll2index(min_lon, min_lat)
        max_y, max_x = self.ll2index(max_lon, max_lat)
        start, end = self._indexesForDates(dataset_name, start_date, end_date)
        data = \
        self._slice3DDataset(dataset, start, end, min_y, max_y, min_x, max_x)
        return self._processDataOut(dataset_name, data, **kwargs)
    dataSlice = get3DSlice

   # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def indexFromDate(self, dataset_name, date):
        return self._indexForDate(dataset_name, date)

    def indexesFromDates(self, dataset_name, start_date, end_date):
        return self._indexesForDates(dataset_name, start_date, end_date)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setDateAttribute(self, object_path, attribute_name, date):
        date_str = date.strftime('%Y-%m-%d')
        self.setObjectAttribute(object_path, attribute_name, date_str)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _dateSlice(self, dataset, start_index, end_index):
        dataset_dims = len(dataset.shape)
        if end_index == start_index:
            if dataset_dims == 1: return dataset.value[start_index]
            elif dataset_dims == 2: return dataset.value[start_index, :]
            else: return dataset.value[start_index, :, :]
        else:
            if dataset_dims == 1: return dataset.value[start_index:end_index]
            elif dataset_dims == 2:
                return dataset.value[start_index:end_index, :]
            else: return dataset.value[start_index:end_index, :, :]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _indexForDate(self, dataset_name, date):
        _date = matchDateType(date, self.start_date)
        return (_date - self.start_date).days

    def _indexesForDates(self, dataset_name, start_date, end_date):
        start_index = self._indexForDate(dataset_name, start_date)
        if end_date is None: end_index = start_index + 1
        else: end_index = self._indexForDate(dataset_name, end_date) + 1
        return (start_index, end_index)

   # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _slice3DDataset(self, dataset, start, end, min_y, max_y, min_x, max_x):
        if end == start: # single date
            if max_y == min_y:
                if max_x == min_x: # retrieve data for one node
                    return dataset.value[start, min_y, min_x]
                elif max_x < dataset.shape[2]:
                    return dataset.value[start, min_y, min_x:max_x]
                else: # max_x >= dataset.shape[2]
                    return dataset.value[start, min_y, min_x:]
            elif max_y < dataset.shape[1]:
                if max_x == min_x:
                    return dataset.value[start, min_y:max_y, min_x]
                elif max_x < dataset.shape[2]:
                    return dataset.value[start, min_y:max_y, min_x:max_x]
                else: # max_x >= dataset.shape[2]
                    return dataset.value[start, min_y:max_y, min_x:]
            else: # max_y >= dataset.shape[1]
                if max_x == min_x:
                    return dataset.value[start, min_y:, min_x]
                elif max_x < dataset.shape[2]:
                    return dataset.value[start, min_y:, min_x:max_x]
                else: # max_x >= dataset.shape[2]
                    return dataset.value[start, min_y:, min_x:]
        elif end < dataset.shape[0]:
            if max_y == min_y:
                if max_x == min_x: # retrieve data for one node
                    return dataset.value[start:end, min_y, min_x]
                elif max_x < dataset.shape[2]:
                    return dataset.value[start:end, min_y, min_x:max_x]
                else: # max_x >= dataset.shape[2]
                    return dataset.value[start:end, min_y, min_x:]
            elif max_y < dataset.shape[1]:
                if max_x == min_x:
                    return dataset.value[start:end, min_y:max_y, min_x]
                elif max_x < dataset.shape[2]:
                    return dataset.value[start, min_y:max_y, min_x:max_x]
                else: # max_x >= dataset.shape[2]
                    return dataset.value[start:end, min_y:max_y, min_x:]
            else: # max_y >= dataset.shape[1]
                if max_x == min_x:
                    return dataset.value[start:end, min_y:, min_x]
                elif max_x < dataset.shape[2]:
                    return dataset.value[start:end, min_y:, min_x:max_x]
                else: # max_x >= dataset.shape[2]
                    return dataset.value[start:end, min_y:, min_x:]
        else: # end > dataset.shape[0] ... retrieve all dates to end of dataset
            if max_y == min_y:
                if max_x == min_x: # retrieve data for one node
                    return dataset.value[start:, min_y, min_x]
                elif max_x < dataset.shape[2]:
                    return dataset.value[start:, min_y, min_x:max_x]
                else: # max_x >= dataset.shape[2]
                    return dataset.value[start:, min_y, min_x:]
            elif max_y < dataset.shape[1]:
                if max_x == min_x:
                    return dataset.value[start:, min_y:max_y, min_x]
                elif max_x < dataset.shape[2]:
                    return dataset.value[start:, min_y:max_y, min_x:max_x]
                else: # max_x >= dataset.shape[2]
                    return dataset.value[start:, min_y:max_y, min_x:]
            else: # max_y >= dataset.shape[1]
                if max_x == min_x:
                    return dataset.value[start:, min_y:, min_x]
                elif max_x < dataset.shape[2]:
                    return dataset.value[start:, min_y:, min_x:max_x]
                else: # max_x >= dataset.shape[2]
                    return dataset.value[start:, min_y:, min_x:]

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadDataGridAttributes_(self):
        if hasattr(self, 'start_date') \
        and isinstance(self.start_date, basestring):
            self.start_date = asDatetimeDate(self.start_date)
        if hasattr(self, 'end_date') \
        and isinstance(self.end_date, basestring):
            self.end_date = asDatetimeDate(self.end_date)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5DateGridManagerMixin(Hdf5DateGridReaderMixin):
    """ Provides read/write access to 3D gridded data in HDF5 files where
    the first dimension is time, the 2nd dimension is rows and the 3rd
    dimension is columns. Grids can contain any type of data. Indexing
    based on Time/Latitude/Longitude is available. Time indexes may be
    derived from date/time with earliest date at index 0. Row indexes
    may be derived from Latitude coordinates with minimum Latitude at
    row index 0. Columns indexes may be derived from Longitude
    coordinates with minimum Longitude at column index 0.

    Inherits all of the capabilities of Hdf5GridFileManager
    """

    def __init__(self, hdf5_filepath, mode='r'):
        Hdf5GridFileManager.__init__(self, hdf5_filepath, mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def insertByDate(self, dataset_name, data, start_date, **kwargs):
        date_index = self._indexForDate(dataset_name, start_date)
        self._insertByDateIndex(dataset_name, data, date_index, **kwargs)

    def insertAtNodeByDate(self, dataset_name, data, start_date, lon, lat,
                                 **kwargs):
        date_index = self._indexForDate(dataset_name, start_date)
        y, x = self.ll2index(lon, lat)
        self._insertDateAtNodeByDateIndex(dataset_name, data, date_index, x, y,
                                          **kwargs)

    def insert3DSlice(self, dataset_name, data, start_date, min_lon, max_lon,
                            min_lat, max_lat, **kwargs):
        min_y, min_x = self.ll2index(min_lon, min_lat)
        max_y, max_x = self.ll2index(max_lon, max_lat)
        date_index = self._indexForDate(dataset_name, start_date)
        self._insert3DSlice(dataset_name, data, date_index, min_y, max_y,
                            min_x, max_x, **kwargs)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _insertByDateIndex(self, dataset_name, data, date_index, **kwargs):
        errmsg = 'Cannot insert data with %dD data into %dD dataset by date.'

        dataset = self.getDataset(dataset_name)
        dataset_dims = len(dataset.shape)
        if dataset_dims == 3:
            if data.ndim == 3:
                end_index = date_index + data.shape[0]
                dataset[date_index:end_index] = \
                    self._processDataIn(dataset_name, data, **kwargs)
            elif data.ndim == 2:
                dataset[date_index] = \
                    self._processDataIn(dataset_name, data, **kwargs)
            else:
                raise ValueError, errmsg % (data.ndim, dataset_dims)
        elif dataset_dims == 1:
            if isinstance(data, N.ndarray):
                if data.ndim == 1:
                    if len(data) > 1:
                        end_index = date_index + len(data)
                        dataset[date_index:end_index] = \
                            self._processDataIn(dataset_name, data, **kwargs)
                    else:
                        dataset[date_index] = \
                            self._processDataIn(dataset_name, data, **kwargs)
                else:
                    raise ValueError, errmsg % (data.ndim, dataset_dims)
            else: # insert scalar value
                dataset[date_index] = self._processDataIn(dataset_name, data,
                                                          **kwargs)
        else:
            raise ValueError, errmsg % (data.ndim, dataset_dims)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _insertAtNodeByDateIndex(self, dataset_name, data, date_index, x, y,
                                       **kwargs):
        end_index = date_index + data.shape[0]
        dataset = self.getDataset(dataset_name)
        dataset[date_index:end_index, y, x] = \
            self._processDataIn(dataset_name, data, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _insert3DSlice(self, dataset_name, data, start, min_y, max_y,
                             min_x, max_x):
        if data.dims == 2: end = start
        elif data.dims == 3: end = start + data.shape[0]
        else:
            errmsg = 'Cannot insert %dD data into a 3D dataset.'
            raise ValueError, errmsg % data.dims

        dataset = self.getDataset(dataset_name)
        if end == start: # single date
            if max_y == min_y:
                if max_x == min_x: # retrieve data for one node
                    dataset[start, min_y, min_x] = data
                elif max_x < dataset.shape[2]:
                    dataset[start, min_y, min_x:max_x] = data
                else: # max_x >= dataset.shape[2]
                    dataset[start, min_y, min_x:] = data
            elif max_y < dataset.shape[1]:
                if max_x == min_x:
                    dataset[start, min_y:max_y, min_x] = data
                elif max_x < dataset.shape[2]:
                    dataset[start, min_y:max_y, min_x:max_x] = data
                else: # max_x >= dataset.shape[2]
                    dataset[start, min_y:max_y, min_x:] = data
            else: # max_y >= dataset.shape[1]
                if max_x == min_x:
                    dataset[start, min_y:, min_x] = data
                elif max_x < dataset.shape[2]:
                    dataset[start, min_y:, min_x:max_x] = data
                else: # max_x >= dataset.shape[2]
                    dataset[start, min_y:, min_x:] = data
        elif end < dataset.shape[0]:
            if max_y == min_y:
                if max_x == min_x: # retrieve data for one node
                    dataset[start:end, min_y, min_x] = data
                elif max_x < dataset.shape[2]:
                    dataset[start:end, min_y, min_x:max_x] = data
                else: # max_x >= dataset.shape[2]
                    dataset[start:end, min_y, min_x:] = data
            elif max_y < dataset.shape[1]:
                if max_x == min_x:
                    dataset[start:end, min_y:max_y, min_x] = data
                elif max_x < dataset.shape[2]:
                    dataset[start, min_y:max_y, min_x:max_x] = data
                else: # max_x >= dataset.shape[2]
                    dataset[start:end, min_y:max_y, min_x:] = data
            else: # max_y >= dataset.shape[1]
                if max_x == min_x:
                    dataset[start:end, min_y:, min_x] = data
                elif max_x < dataset.shape[2]:
                    dataset[start:end, min_y:, min_x:max_x] = data
                else: # max_x >= dataset.shape[2]
                    dataset[start:end, min_y:, min_x:] = data
        else: # end > dataset.shape[0] ... retrieve all dates to end of dataset
            if max_y == min_y:
                if max_x == min_x: # retrieve data for one node
                    dataset[start:, min_y, min_x] = data
                elif max_x < dataset.shape[2]:
                    dataset[start:, min_y, min_x:max_x] = data
                else: # max_x >= dataset.shape[2]
                    dataset[start:, min_y, min_x:] = data
            elif max_y < dataset.shape[1]:
                if max_x == min_x:
                    dataset[start:, min_y:max_y, min_x] = data
                elif max_x < dataset.shape[2]:
                    dataset[start:, min_y:max_y, min_x:max_x] = data
                else: # max_x >= dataset.shape[2]
                    dataset.value[start:, min_y:max_y, min_x:] = data
            else: # max_y >= dataset.shape[1]
                if max_x == min_x:
                    dataset[start:, min_y:, min_x] = data
                elif max_x < dataset.shape[2]:
                    dataset[start:, min_y:, min_x:max_x] = data
                else: # max_x >= dataset.shape[2]
                    dataset[start:, min_y:, min_x:] = data


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5DateGridFileReader(Hdf5DateGridReaderMixin, Hdf5GridFileReader):
    """ Provides read-only access to 3D gridded data in HDF5 files where
    the first dimension is time, the 2nd dimension is rows and the 3rd
    dimension is columns. Grids can contain any type of data. Indexing
    based on Time/Latitude/Longitude is available. Time indexes may be
    derived from date/time with earliest date at index 0. Row indexes
    may be derived from Latitude coordinates with minimum Latitude at
    row index 0. Columns indexes may be derived from Longitude
    coordinates with minimum Longitude at column index 0.

    Inherits all of the capabilities of Hdf5GridFileReader
    """

    def __init__(self, hdf5_filepath):
        Hdf5GridFileReader.__init__(self, hdf5_filepath)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        Hdf5GridFileReader._loadManagerAttributes_(self)
        self._loadDataGridAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5DateGridFileManager(Hdf5DateGridManagerMixin, Hdf5GridFileManager):
    """ Provides read/write access to 3D gridded data in HDF5 files where
    the first dimension is time, the 2nd dimension is rows and the 3rd
    dimension is columns. Grids can contain any type of data. Indexing
    based on Time/Latitude/Longitude is available. Time indexes may be
    derived from date/time with earliest date at index 0. Row indexes
    may be derived from Latitude coordinates with minimum Latitude at
    row index 0. Columns indexes may be derived from Longitude
    coordinates with minimum Longitude at column index 0.

    Inherits all of the capabilities of Hdf5GridFileManager
    """

    def __init__(self, hdf5_filepath, mode='r'):
        Hdf5GridFileManager.__init__(self, hdf5_filepath, mode)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        Hdf5GridFileManager._loadManagerAttributes_(self)
        self._loadDataGridAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5DateGridFileBuilder(Hdf5DateGridManagerMixin, Hdf5GridFileBuilder):
    """ Creates a new HDF5 file with read/write access to 3D gridded data
    where the first dimension is time, the 2nd dimension is rows and the
    3rd dimension is columns.

    Inherits all of the capabilities of Hdf5GridFileBuilder
    """

    def __init__(self, hdf5_filepath, start_date, end_date, lons, lats):
        Hdf5GridFileBuilder.__init__(self, hdf5_filepath, lons, lats)
        # set the time span for this file
        self.setFileAttributes(start_date=dateAsInt(start_date),
                               end_date=dateAsInt(end_date))
        # close the file to make sure attributes are saved
        self.close()
        # reopen the file in append mode
        self.open(mode='a')

