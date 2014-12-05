""" Classes for accessing data from Hdf5 encoded grid files.
"""

import os

import numpy as N

from atmosci.utils.timeutils import asDatetime, dateAsInt

from atmosci.hdf5.grid import Hdf5GridFileReader, Hdf5GridFileManager

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

TIME_SPAN_ERROR = 'Invalid time span. '
TIME_SPAN_ERROR += 'Either "date" OR "start_date" plus "end_date" are required.'

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5DateGridMixin:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDataForDate(self, dataset_name, date, **kwargs):
        indx = self._indexForDate(dataset_name, date)
        dataset = self.getDataset(dataset_name)
        return self._processDataOut(dataset_name, dataset[indx], **kwargs)

    def getDataSince(self, dataset_name, date, **kwargs):
        return self.getDateSlice(dataset_name, date, self.end_date, **kwargs)

    def getDataThru(self, dataset_name, date, **kwargs):
        return self.getDateSlice(dataset_name, self.start_date, date, **kwargs)

    def getDateSlice(self, dataset_name, start_date, end_date, **kwargs):
        start, end = self._indexesForDates(dataset_name, start_date, end_date)
        dataset = self.getDataset(dataset_name)
        data = self._dateSlice(dataset, start, end)
        return self._processDataOut(dataset_name, data, **kwargs)

    def get3DSlice(self, dataset_name, start_date, end_date, min_lon, max_lon,
                         min_lat, max_lat, **kwargs):
        min_y, min_x = self.ll2index(min_lon, min_lat)
        max_y, max_x = self.ll2index(max_lon, max_lat)
        start, end = self._indexesForDates(dataset_name, start_date, end_date)
        data = \
        self._slice3DDataset(dataset, start, end, min_y, max_y, min_x, max_x)
        return self._processDataOut(dataset_name, data, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    def getDateAtNode(self, dataset_name, lon, lat, start_date, end_date=None,
                            **kwargs):
        y, x = self.ll2index(lon, lat)
        if end_date is None:
            indx = self._indexForDate(dataset_name, date)
            data = self.getDataset(dataset_name).value[indx, y, x]
        else:
            start, end = \
            self._indexesForDates(dataset_name, start_date, end_date)
            data = self.getDataset(dataset_name).value[start:end, y, x]
        return self._processDataOut(dataset_name, data, **kwargs)

   # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def indexFromDate(self, dataset_name, date):
        return self._indexForDate(dataset_name, date)

    def indexesFromDates(self, dataset_name, start_date, end_date):
        return self._indexesForDates(dataset_name, start_date, end_date)

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
        return (asDatetime(date) - self.start_date).days

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
            self.start_date = asDatetime(self.start_date)
        if hasattr(self, 'end_date') \
        and isinstance(self.end_date, basestring):
            self.end_date = asDatetime(self.end_date)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5DateGridFileReader(Hdf5DateGridMixin, Hdf5GridFileReader):
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

class Hdf5DateGridFileManager(Hdf5DateGridMixin, Hdf5GridFileManager):
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

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        Hdf5GridFileManager._loadManagerAttributes_(self)
        self._loadDataGridAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5DateGridFileBuilder(Hdf5DateGridFileManager):
    """ Creates a new HDF5 file with read/write access to 3D gridded data
    where the first dimension is time, the 2nd dimension is rows and the
    3rd dimension is columns.

    Inherits all of the capabilities of Hdf5DateGridFileManager
    """

    def __init__(self, hdf5_filepath, start_date, end_date, lons, lats):
        self._access_authority = ('r','a', 'w')
        Hdf5DateGridFileManager.__init__(self, hdf5_filepath, 'w')
        self.setFileAttribute('created', self.timestamp)

        # capture longitude/latitude limits of grids
        min_lon = N.nanmin(lons)
        max_lon = N.nanmax(lons)
        min_lat = N.nanmin(lats)
        max_lat = N.nanmax(lats)

        self.setFileAttributes(created=manager.timestamp,
                               start_date=dateAsInt(start_date),
                               end_date=dateAsInt(end_date),
                               min_lon=min_lon, max_lon=max_lon,
                               min_lat=min_lat, max_lat=max_lat)

        # cache the lon/lat grids
        self.createDataset('lon', lons)
        self.setDatasetAttributes('lon', min=min_lon, max=max_lon)

        self.createDataset('lat', lats)
        self.setDatasetAttributes('lat', min=min_lat, max=max_lat)

        # close the file to make sure everything got written
        self.close()

        # reopen the file in append mode
        self.open(mode='a')

