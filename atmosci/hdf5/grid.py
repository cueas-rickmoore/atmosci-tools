""" Classes for accessing data from Hdf5 encoded grid files.
"""

import os
import math

import numpy as N

from atmosci.hdf5.file import Hdf5FileReader, Hdf5FileManager

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5GridFileMixin:

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def getData(self, dataset_name, bounded=False, **kwargs):
        self.assertFileOpen()
        if kwargs.get('bounded', False):
            dataset = self.getDataset(dataset_name)
            data = self._coordBoundsSubset(dataset)
            return self._processDataOut(dataset_name, data, **kwargs)
        else:
            data = self._getData_(self._hdf5_file_, dataset_name, **kwargs)
            return self._processDataOut(dataset_name, data, **kwargs)

    def getDataInBounds(self, dataset_name, **kwargs):
        dataset = self.getDataset(dataset_name)
        return self._processDataOut(dataset_name, data, **kwargs)

    def get2DSlice(self, dataset_name, min_lon, max_lon, min_lat, max_lat,
                         **kwargs):
        min_y, min_x = self.ll2index(min_lon, min_lat)
        max_y, max_x = self.ll2index(max_lon, max_lat)
        dataset = self.getDataset(dataset_name)
        data = self._slice2DDataset(dataset, min_y, max_y, min_x, max_x)
        return self._processDataOut(dataset_name, data, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def distanceBetweenNodes(self, lon1, lat1, lon2, lat2):
        lon_diffs = lon1 - lon2
        lat_diffs = lat1 - lat2
        return N.sqrt( (lon_diffs * lon_diffs) + (lat_diffs * lat_diffs) )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getBoundingBox(self):
        if self._bounding_box is None:
            return (self._min_avail_lon, self._min_avail_lat,
                    self._max_avail_lon, self._max_avail_lat)
        else: self._bounding_box

    def getIndexBounds(self):
        """ Returns a tuple containg the minimum and maximum x and y indexes
        """
        if self._index_bbox is None:
            return (self._min_avail_y, self._max_avail_y,
                    self._min_avail_x, self._max_avail_x)
        else: return self._index_box

    def getCoordinateLimits(self):
        limits = { }
        limits['min_avail_lon'] = self._min_avail_lon
        limits['max_avail_lon'] = self._max_avail_lon
        limits['min_avail_lat'] = self._min_avail_lat
        limits['max_avail_lat'] = self._max_avail_lat
        limits['max_avail_x'] = self._max_avail_x
        limits['min_avail_x'] = self._min_avail_x
        limits['max_avail_y'] = self._max_avail_y
        limits['min_avail_y'] = self._min_avail_y
        return limits

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    def getNodeData(self, dataset_name, lon, lat):
        y, x = self.ll2index(lon, lat)
        return self.getDataset(dataset_name).value[y, x]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def indexOfClosestNode(self, lon, lat):
        return self._indexOfClosestNode(lon, lat)

    def index2ll(self, y, x):
        """ Returns the lon/lat coordinates of grid node at the y/x index
        """
        return self._lons[y,x], self._lats[y,x]

    def ll2index(self, lon, lat):
        """ Returns the indexes of the grid node that is closest to the
        lon/lat coordinate point.
        """
        return self._indexOfClosestNode(lon, lat)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setAreaMask(self, mask_name='mask'):
        """ Returns the area mask as an array.
        """
        mask_array, attrs = self.getRawData(mask_name)
        self._area_mask = mask_array

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setCoordinateBounds(self, point_or_bbox):
        if len(point_or_bbox) == 2:
            self._lon_lat_bounds = None
            self._y, self._x = self.ll2index(*point_or_bbox)
            self._index_bounds = None
        elif len(point_or_bbox) == 4:
            self._lon_lat_bounds = tuple(point_or_bbox)
            y1, x1 = self.ll2index(*point_or_bbox[:2])
            y2, x2 = self.ll2index(*point_or_bbox[2:])
            self._index_bounds = (y1, x1+1, y2, x2+1)
            self._y = None
            self._x = None
        else:
            errmsg = "Invalid value for 'point_or_bbox'. It must contain "
            errmsg += "either a point (lon,lat) or a bounding box "
            errmsg += "(min_lon,min_lat,max_lon,max_lat)."
            raise ValueError, errmsg

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setIndexBounds(self, point_or_bbox):
        if len(point_or_bbox) == 2:
            self._y = point_or_bbox[0]
            self._x = point_or_bbox[1]
            self._index_bounds = None
            self._lon_lat_bounds = None
        elif len(point_or_bbox) == 4:
            min_y = point_or_bbox[0]
            min_x = point_or_bbox[1]
            max_y = point_or_bbox[2]
            max_x = point_or_bbox[3]
            self._index_bounds = (min_y, max_y, min_x, max_x)
            min_lon, min_lat = self.index2ll(*point_or_bbox[:2])
            max_lon, max_lat = self.index2ll(*point_or_bbox[2:])
            self._lon_lat_bounds = (min_lon, min_lat, max_lon, max_lat)
            self._y = None
            self._x = None
        else:
            errmsg = "Invalid value for 'point_or_bbox'. It must contain "
            errmsg += "either a point (y,x) or a bounding box "
            errmsg += "(min_y,min_x,max_y,max_y)."
            raise ValueError, errmsg

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setNodeSearchRadius(self, radius):
        self.node_search_radius = radius

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def unsetGridBounds(self):
        self._index_bounds = None
        self._lon_lat_bounds = None
        self._y = None
        self._x = None

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _coordBoundsSubset(self, dataset):
        """ Returns a subset of a grid that is within the grid manager's
        lon/lat bounding box. Grid shape must be [y, x].
        """
        if self._index_bbox is not None:
            min_y, max_y, min_x, max_x = self._index_bbox

            if max_y < dataset.shape[0]:
                if max_x < dataset.shape[1]:
                    return dataset.value[min_y:max_y, min_x:max_x]
                else:
                    return dataset.value[min_y:max_y, min_x:]
            else:
                if max_x < dataset.shape[1]:
                    return dataset.value[min_y:, min_x:max_x]
                else:
                    return dataset.value[min_y:, min_x:]

        # asking for a single point
        elif self._x is not None:
            return  dataset.value[self._y, self._x]

        # asking for the whole dataset
        return dataset.value

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _indexOfClosestNode(self, target_lon, target_lat):
        # "closeness" is dependent on the projection and grid spacing of
        # the data ... this implementation is decent for grids in the
        # continental U.S. with small node spacing (~ 5km or less) such
        # as the ACIS 5 km Lambert Conformal grids supplied by NRCC.
        # It should really be implemented in a subclass using a method
        # that is specific to the grid type in use.
        radius = self.node_search_radius
        indexes = N.where( (self.lons >= (target_lon - radius)) &
                           (self.lons <= (target_lon + radius)) &
                           (self.lats >= (target_lat - radius)) &
                           (self.lats <= (target_lat + radius)) )

        distances = \
        self.distanceBetweenNodes(self.lons[indexes], self.lats[indexes],
                                  target_lon, target_lat)
        indx = N.where(distances == distances.min())[0][0]
        return indexes[0][indx], indexes[1][indx]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initCoordinateLimits(self):
        """ Sets the absolute limts for lon/lat and index coordinates for
        grids present in the file.
        """
        # initialize grid coordinate and index bounds to None
        self._lon_lat_bbox = None
        self._index_bbox = None

        # get lon/lat grids and capture grid limits
        try:
            self.lons = self.getData('lon')
            self.lats = self.getData('lat')
        except:
            self._min_avail_lat = None
            self._max_avail_lat = None
            self._min_avail_lon = None
            self._max_avail_lon = None

            self._min_avail_x = None
            self._max_avail_x = None 
            self._min_avail_y = None
            self._max_avail_y = None

            self.lons = None
            self.lats = None
        else:
            # capture lat/lon limits
            self._min_avail_lat = N.nanmin(self.lats)
            self._max_avail_lat = N.nanmax(self.lats)
            self._min_avail_lon = N.nanmin(self.lons)
            self._max_avail_lon = N.nanmax(self.lons)

            # capture index limits
            self._min_avail_x = 0
            self._max_avail_x = self.lons.shape[1]
            self._min_avail_y = 0
            self._max_avail_y = self.lons.shape[0]

            # set the default search radius
            self._setDefaultSearchRadius_()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _slice2DDataset(self, dataset, min_y, max_y, min_x, max_x):
        if max_y == min_y:
            if max_x == min_x: # retrieve data for one node
                return dataset[min_y, min_x]
            elif max_x < dataset.shape[1]:
                return dataset.value[min_y, min_x:max_x]
            else: # max_x >= dataset.shape[1]
                return dataset.value[min_y, min_x:]
        elif max_y < dataset.shape[0]:
            if max_x == min_x:
                return dataset.value[min_y:max_y, min_x]
            elif max_x < dataset.shape[1]:
                return dataset.value[min_y:max_y, min_x:max_x]
            else: # max_x >= dataset.shape[1]
                return dataset.value[min_y:max_y, min_x:]
        else: # max_y >= dataset.shape[0]
            if max_x == min_x:
                return dataset.value[min_y:, min_x]
            elif max_x < dataset.shape[1]:
                return dataset.value[start, min_y:, min_x:max_x]
            else: # max_x >= dataset.shape[1]
                return dataset.value[min_y:, min_x:]

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _clearManagerAttributes_(self):
        Hdf5DataFileManager._clearManagerAttributes_(self)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _loadGridFileAttributes_(self):
        Hdf5FileReader._loadManagerAttributes_(self)
        self._initCoordinateLimits()
        self.unsetGridBounds()
        if self.lats is not None:
            self.grid_shape = self.lats.shape
            self.grid_size = self.lats.size
        else:
            self.grid_shape = ()
            self.grid_size = -32768
 
        if ( not hasattr(self, 'node_search_radius')
             or self.node_search_radius is None ) and self.lats is not None:
            self._setDefaultSearchRadius_()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _setDefaultSearchRadius_(self):
        lat_diff = (self.lats[1] - self.lats[0])
        lon_diff = (self.lons[1] - self.lons[0])
        # 55% of distance between farthest nodes in a single grid rectangle
        self.node_search_radius = N.sqrt(lat_diff**2. + lon_diff**2.) * 0.55


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5GridFileReader(Hdf5FileReader, Hdf5GridFileMixin):
    """ Provides read-only access to datasets, groups and other obsects in
    Hdf5-encoded files. Additinally provides special methods for accessing
    data in datasets based on regular Latitude/Longitude grids. Indexing
    based on Latitude/Longitude is available provided that rows are
    ordered by Latitude and columns are ordered by Longitude. For this to
    work, the minimum Latitude must be at row index 0 and the minimum
    Longitude must be at column index 0.

    Inherits all of the capabilities of Hdf5FileReader
    """

    def __init__(self, hdf5_filepath):
        Hdf5FileReader.__init__(self, hdf5_filepath)
        self._area_mask = None

    def _loadManagerAttributes_(self):
        Hdf5FileReader._loadManagerAttributes_(self)
        self._loadGridFileAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5GridFileManager(Hdf5FileManager, Hdf5GridFileMixin):
    """ Provides read/write access to datasets, groups and other obsects in
    Hdf5-encoded files. Additinally provides special methods for accessing
    data in datasets based on regular Latitude/Longitude grids. Indexing
    based on Latitude/Longitude is available provided that rows are
    ordered by Latitude and columns are ordered by Longitude. For this to
    work, the minimum Latitude must be at row index 0 and the minimum
    Longitude must be at column index 0.

    Inherits all of the capabilities of Hdf5FileManager
    """

    def __init__(self, hdf5_filepath, mode='r'):
        Hdf5FileManager.__init__(self, hdf5_filepath, mode)
        self._area_mask = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def insertDataInBounds(self, dataset_name, data, **kwargs):
        data = self._processDataIn(dataset_name, data, **kwargs)
        dataset = self.getDataset(dataset_name)
        self._insertDataInBounds(dataset_name, dataset, data,)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def insert2DSlice(self, dataset_name, data, min_lon, max_lon, min_lat,
                            max_lat, **kwargs):
        data = self._processDataIn(dataset_name, data, **kwargs)
        min_y, min_x = self.ll2index(min_lon, min_lat)
        max_y, max_x = self.ll2index(max_lon, max_lat)
        dataset = self.getDataset(dataset_name)
        self._insert2DSlice(dataset, data, min_y, max_y, min_x, max_x)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _insertDataInBounds(dataset_name, dataset, data):
        if self._index_bbox is not None:
            min_y, max_y, min_x, max_x = self._index_bbox

            if max_y < dataset.shape[0]:
                if max_x < dataset.shape[1]:
                    dataset[min_y:max_y, min_x:max_x] = data
                else: dataset[min_y:max_y, min_x:] = data
            else:
                if max_x < dataset.shape[1]:
                    dataset[min_y:, min_x:max_x] = data
                else: dataset[min_y:, min_x:] = data
        else:
            errmsg = 'Coordinate bounding box has not been defined.'
            raise AttributeError, errmsg

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _insert2DSlice(dataset, data, min_y, max_y, min_x, max_x):
        if max_y == min_y:
            if max_x == min_x: # retrieve data for one node
                dataset[min_y, min_x] = data
            elif max_x < dataset.shape[1]:
                dataset[min_y, min_x:max_x] = data
            else: # max_x >= dataset.shape[1]
                dataset[min_y, min_x:] = data
        elif max_y < dataset.shape[0]:
            if max_x == min_x:
                dataset[min_y:max_y, min_x] = data
            elif max_x < dataset.shape[1]:
                dataset[min_y:max_y, min_x:max_x] = data
            else: # max_x >= dataset.shape[1]
                dataset[min_y:max_y, min_x:] = data
        else: # max_y >= dataset.shape[0]
            if max_x == min_x:
                dataset[min_y:, min_x] = data
            elif max_x < dataset.shape[1]:
                dataset[start, min_y:, min_x:max_x] = data
            else: # max_x >= dataset.shape[1]
                dataset[min_y:, min_x:] = data

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        Hdf5FileManager._loadManagerAttributes_(self)
        self._loadGridFileAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5GridFileBuilder(Hdf5GridFileManager):
    """ Creates a new HDF5 file with read/write access to datasets, groups,
    and other objects. 

    Inherits all of the capabilities of Hdf5GridFileManager
    """

    def __init__(self, hdf5_filepath, lons, lats):
        self._access_authority = ('r','a', 'w')
        Hdf5GridFileManager.__init__(self, hdf5_filepath, 'w')
        self.setFileAttribute('created', self.timestamp)

        min_lon = N.nanmin(lons)
        max_lon = N.nanmax(lons)
        min_lat = N.nanmin(lats)
        max_lat = N.nanmax(lats)

        # capture latitude grid limits
        self.setFileAttributes(min_lon=min_lon, max_lon=max_lon,
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

