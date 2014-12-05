""" Classes for accessing  and managing data in Hdf5 encoded grid files.
"""

import os
from datetime import datetime

import h5py
import numpy as N

from atmosci.utils.data import safedict, dictToWhere, listToWhere
from atmosci.utils.timeutils import asDatetime

from atmosci.hdf5.mixin import Hdf5DataReaderMixin, Hdf5DataWriterMixin

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5FileReader(Hdf5DataReaderMixin, object):
    """ Provides read-only access to datasets, groups and other obsects in
    Hdf5-encoded files.
    """

    def __init__(self, hdf5_filepath):
        self._unpackers = { }
        if not hasattr(self, '_access_authority'):
            self._access_authority = ('r',)
            self._open_(hdf5_filepath, 'r')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def assertFileOpen(self):
        if self._hdf5_file_ is None: raise IOError, 'No open Hdf5 file.'

    def assertFileWritable(self):
        raise IOError, 'Hdf5 file is not writable.'

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dotPaths(self, obj_keys):
        paths = [self.dotPath(key) for key in obj_keys]
        paths.sort()
        if isinstance(obj_keys, tuple): return tuple(paths)
        else: return paths

    def dotPath(self, key):
        if key.startswith('/'): return key[1:].replace('/','.')
        return key.replace('/','.')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getData(self, dataset_name, **kwargs):
        self.assertFileOpen()
        data = self._getData_(self._hdf5_file_, dataset_name, **kwargs)
        return self._processDataOut(dataset_name, data, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDataWhere(self, dataset_name, criteria=None, **kwatgs):
        datasets = [ ]
        if criteria:
            indexes = self._where(criteria)
            if indexes and len(indexes[0]) > 0:
                return self.getData(dataset_name, indexes=indexes, **kwargs)
            else:
                errmsg = 'No entries meet search criteria : %s'
                raise ValueError, errmsg % str(criteria)
        return self.getData(dataset_name, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _datasetNames(self):
        return self._dataset_names
    dataset_names = property(_datasetNames)

    def datasetExists(self, dataset_name):
        return dataset_name in self._dataset_names
    hasDataset = datasetExists

    def datasetExistsIn(self, dataset_name, parent_name):
        if parent_name == '__file__':
            return dataset_name in self._dataset_names
        else:
            self.assertFileOpen()
            return datast_name in self._getDatasetKeys_(parent_name)

    def getDataset(self, dataset_name):
        self.assertFileOpen()
        return self._getDataset_(self._hdf5_file_, dataset_name)

    def getDatasetAttribute(self, dataset_name, attr_name):
        self.assertFileOpen()
        parent = self._hdf5_file_
        return self._getDatasetAttribute_(parent, dataset_name, attr_name)

    def getDatasetAttributes(self, dataset_name):
        self.assertFileOpen()
        return self._getDatasetAttributes_(self._hdf5_file_, dataset_name)
    getDatasetAttrs = getDatasetAttributes

    def getDatasetShape(self, dataset_name):
        return self.getDataset(dataset_name).shape

    def getDatasetType(self, dataset_name):
        return self.getDataset(dataset_name).dtype

    def listDatasets(self):
        return self.listDatasetsIn('__file__')

    def listDatasetsIn(self, parent_name):
        self.assertFileOpen()
        if parent_name == '__file__': _object = self._hdf5_file_
        else: _object = self._getObject_(self._hdf5_file_, parent_name)
        keys = [ self.dotPath(key) for key in self._getObjectKeys_(_object)
                                   if isinstance(_object[key], h5py.Dataset) ]
        return list(keys)

    def registerDataUnpacker(dataset_name, function):
        self._unpackers[dataset_name] = function

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def close(self):
        if hasattr(self, '_hdf5_file_') and self._hdf5_file_ is not None:
            self._clearManagerAttributes_()
            self._close_(self._hdf5_file_)
        self._hdf5_file_ = None
        self._hdf5_file_mode = None

    def getFileAttribute(self, attr_name):
        self.assertFileOpen()
        return self._getFileAttribute_(self._hdf5_file_, attr_name)

    def getFileAttributes(self):
        self.assertFileOpen()
        return self._getFileAttributes_(self._hdf5_file_)

    def getFileHierarchy(self, grouped=False):
        if grouped:
            groups, datasets =\
            self._getObjectHierarchy_(self._hdf5_file_, '.', True)
            return (tuple(groups), tuple(datasets))
        else:
            return tuple(self._getObjectHierarchy_(self._hdf5_file_, '.'))

    def getFilePath(self):
        return self._hdf5_filepath
    filepath = property(getFilePath)

    def getFileMode(self):
        return self._hdf5_file_mode
    filemode = property(getFileMode)

    def open(self, mode='r'):
        if mode not in self._access_authority:
            errmsg = "'%s' is not in list of modes allowed by this manager."
            raise ValueError, errmsg % mode
        if hasattr(self, '_hdf5_file_mode') and self._hdf5_file_mode != mode:
            self.close()
        if self._hdf5_file_ is None:
            self._open_(self._hdf5_filepath, mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _groupNames(self):
        return self._group_names
    group_names = property(_groupNames)

    def getGroup(self, group_name):
        self.assertFileOpen()
        _object = self._getGroup_(self._hdf5_file_, group_name)
        return _object

    def getGroupAttribute(self, group_name, attr_name):
        self.assertFileOpen()
        return self._getGroupAttribute_(self._hdf5_file_, group_name, attr_name)

    def getGroupAttributes(self, group_name):
        self.assertFileOpen()
        return self._getGroupAttributes_(self._hdf5_file_, group_name)

    def groupExists(self, group_name, parent_name=None):
        if parent_name in('__file__', None):
            return group_name in self._group_names
        else: return group_name in self.listGroupsIn(parent_name)
    hasGroup = groupExists

    def getGroupHierarchy(self, group_name):
        _object = self.getGroup(group_name)
        return tuple(self._getObjectHierarchy_(_object, '.'))

    def listGroups(self):
        return self.listGroupsIn('__file__')

    def listGroupsIn(self, parent_name):
        self.assertFileOpen()
        if parent_name == '__file__': _object = self._hdf5_file_
        else: _object = self._getObject_(self._hdf5_file_, parent_name)
        keys = [ self.dotPath(key) for key in self._getObjectKeys_(_object)
                                   if isinstance(_object[key], h5py.Group) ]
        return list(keys)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getObject(self, object_name):
        self.assertFileOpen()
        if object_name.lower() == '__file__': return self._hdf5_file_
        return self._getObject_(self._hdf5_file_, object_name)

    def getObjectAttribute(self, object_name, attr_name):
        self.assertFileOpen()
        return self._getObjectAttribute_(self.getObject(object_name), attr_name)

    def getObjectAttributes(self, object_name):
        self.assertFileOpen()
        return self._getObjectAttributes_(self.getObject(object_name))

    def getObjectHierarchy(self, object_name):
        _object = self.getObject(object_name)
        return tuple(self._getObjectHierarchy_(_object, '.'))

    def getObjectShape(self, object_name):
        self.assertFileOpen()
        return self._getObjectShape_(self.getObject(object_name))

    def objectExists(self, object_name, parent_name=None):
        return object_name in self.listObjects(parent_name)

    def listObjects(self):
        return self.listObjectsIn('__file__')

    def listObjectsIn(self, parent_name=None):
        self.assertFileOpen()
        if parent_name == '__file__': _object = self._hdf5_file_
        else: _object = self.getObject(self._hdf5_file_, parent_name)
        return list(self.dotPaths(self._getObjectKeys_(_object)))

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _dotPathToHdf5Path(self, path):
        return '/%s' % key.replace('.','/')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _pathToNameAndParent(self, root_object, object_key):
        dot = object_key.rfind('.')
        if dot < 0: dot = object_key.rfind('/')

        if dot < 0: return object_key, root_object
        else:
            parent_path = object_key[:dot]
            object_name = object_key[dot+1:]
            return object_name, self._getObject_(root_object, parent_path)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _processDataOut(self, dataset_name, data, **kwargs):
        if kwargs.get('raw', False): return data
        data = self._unpackData(dataset_name, data, **kwargs)
        return self._postUnpack(dataset_name, data, **kwargs)

    def _getUnpacker(self, dataset_name):
        return self._unpackers.get(dataset_name,
                                   self._unpackers.get('default', None))

    def _postUnpack(self, dataset_name, data, **kwargs):
        return data

    def _unpackData(self, dataset_name, data, **kwargs):
        unpack = self._getUnpacker(dataset_name)
        if unpack is None: return data
        else: return unpack(data)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _where(self, criteria):
        if criteria:
            errmsg = 'Key for filter criteria is not a valid dataset name : %s'
            where = None
            constraint_data = { }
            dataset_names = self.allDatasetNames()

            if isinstance(criteria, dict):
                for key, constraint in criteria.items():
                    if constraint is None: continue
                    if key in dataset_names:
                        if key not in constraint_data:
                            constraint_data[key] = self.getData(key)
                    else: raise KeyError, errmsg % key
                if constraint_data:
                    where = dictToWhere(criteria)

            elif isinstance(criteria, (list,tuple)):
                for rule in criteria:
                    key = rule[0]
                    if key in dataset_names:
                        if key not in constraint_data:
                            constraint_data[key] = self.getData(key)
                    else: raise KeyError, errmsg % key
                if constraint_data:
                    where = listToWhere(criteria)

            if where is not None:
                return eval(where, globals(), constraint_data)

        return None

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _clearManagerAttributes_(self):
        pass

    def _loadManagerAttributes_(self):
        groups, datasets = self.getFileHierarchy(grouped=True)
        self._dataset_names = list(datasets)
        self._group_names = list(groups)
        attributes = self.getFileAttributes()
        for attr_name, attr_value in attributes.items():
            if attr_name in ('created', 'updated'):
                try:
                    self.__dict__[attr_name] = asDatetime(attr_value)
                except:
                    self.__dict__[attr_name] = attr_value
            else: self.__dict__[attr_name] = attr_value

    def _open_(self, filepath, mode, load=True):
        self._hdf5_file_ = self._openFile_(filepath, mode)
        self._hdf5_filepath = filepath
        self._hdf5_file_mode = mode
        self._loadManagerAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5FileManager(Hdf5DataWriterMixin, Hdf5FileReader):
    """ Provides read/write access to datasets, groups and other obsects
    in Hdf5-encoded files.
    """

    def __init__(self, hdf5_filepath, mode='r', **kwargs):
        self._packers = { }
        if not hasattr(self, '_access_authority'):
            self._access_authority = ('r','a')
            if mode not in self._access_authority:
                errmsg = "'%s' is not in list of modes allowed by this manager."
                raise ValueError, errmsg % mode
        Hdf5FileReader.__init__(self, hdf5_filepath)
        self._open_(hdf5_filepath, mode)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def copy(self, to_object, object_names=()):
        self.assertFileWritable()

        if object_names:
            for object_name in object_names:
                self._hdf5_file_.copy(object_name, to_object)
        else: # none specified, copy all contained objects
            for object_name in self._hdf5_file_.keys():
                self._hdf5_file_.copy(object_name, to_object)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createDataset(self, dataset_name, numpy_array, **kwargs):
        self.assertFileWritable()

        name, parent = self._pathToNameAndParent(self._hdf5_file_, dataset_name)
        dataset = self._createDataset_(parent, name,
                  self._processDataIn(dataset_name, numpy_array, **kwargs), **kwargs)
        self._registerDatasetName(dataset)
        return dataset

    def createEmptyDataset(self, dataset_name, shape, dtype, fill_value,
                                 **kwargs):
        self.assertFileWritable()

        kwargs['dtype'] = dtype 
        kwargs['fillvalue']  = fill_value

        name, parent = self._pathToNameAndParent(self._hdf5_file_, dataset_name)
        dataset = self._createDataset_(parent, name, shape, **kwargs)
        self._registerDatasetName(dataset)
        return dataset

    def createExtensibleDataset(self, dataset_name, initial_shape, max_shape,
                                      dtype, fill_value, **kwargs):
        self.assertFileWritable()

        kwargs['dtype'] = dtype 
        kwargs['fillvalue']  = fill_value
        kwargs['maxshape'] = max_shape

        name, parent = self._pathToNameAndParent(self._hdf5_file_, dataset_name)
        dataset = self._createDataset_(parent, name, initial_shape, **kwargs)
        self._registerDatasetName(dataset)
        return dataset

    def registerDataPacker(dataset_name, function):
        self._packers[dataset_name] = function

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def replaceDataset(self, dataset_name, data, attributes):
        self.deleteDataset(dataset_name)
        attributes['updated'] = self._timestamp_()
        self.createDataset(dataset_name, data, attributes)

    def resizeDataset(self, dataset_name, max_index):
        self.assertFileOpen()
        dataset = self.getDataset(dataset_name)
        old_shape = self._hdf5_file_[dataset_name].shape
        new_size = (max_index,) + old_shape[1:]
        self._hdf5_file_[dataset_name].resize(new_size)

    def updateDataset(self, dataset_name, numpy_array, attributes={}, **kwargs):
        self.assertFileWritable()
        
        name, parent = self._pathToNameAndParent(self._hdf5_file_, dataset_name)
        if name in self._dataset_names:
            dataset = self._updateDataset_(parent, name, 
                            self._processDataIn(dataset_name, numpy_array, **kwargs), 
                            attributes, **kwargs)
        else:
            dataset = self.createDataset(dataset_name, numpy_array, attributes,
                                         **kwargs)
        return dataset

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteDataset(self, dataset_name):
        self.assertFileWritable()
        self._deleteDataset_(self._hdf5_file_, dataset_name, attr_name)

    def deleteDatasetAttribute(self, dataset_name, attr_name):
        self.assertFileWritable()
        self._deleteDatasetAttribute_(self._hdf5_file_, dataset_name, attr_name)

    def setDatasetAttribute(self, dataset_name, attr_name, attr_value):
        self.assertFileWritable()
        self._setDatasetAttribute_(self._hdf5_file_, dataset_name,
                                  attr_name, attr_value)

    def setDatasetAttributes(self, dataset_name, **kwargs):
        self.assertFileWritable()
        self._setDatasetAttributes_(self._hdf5_file_, dataset_name, kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def assertFileWritable(self):
        if self._hdf5_file_ is None: raise IOError, 'No open Hdf5 file.'
        if self._hdf5_file_mode not in ('w','a'): 
            raise IOError, 'Hdf5 file is not writable.'

    def deleteFileAttribute(self, attr_name):
        self.assertFileWritable()
        self._deleteFileAttribute_(self._hdf5_file_, attr_name)

    def setFileAttribute(self, attr_name, attr_value):
        self.assertFileWritable()
        self._setFileAttribute_(self._hdf5_file_, attr_name, attr_value)

    def setFileAttributes(self, **kwargs):
        self.assertFileWritable()
        for attr_name, attr_value in kwargs.items():
            self._setFileAttribute_(self._hdf5_file_, attr_name, attr_value)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def createGroup(self, group_name, **attributes):
        """ Creates a new group in the parent and returns a pointer to
        it. Raises IOError exception if the group already exists.
        """
        attrs = safedict(attributes)
        if 'created' not in attrs:
            attrs['created'] = self._timestamp_()

        name, parent = self._pathToNameAndParent(self._hdf5_file_, group_name)
        if name in parent.keys():
            errmsg = "'%s' group already exists in current data file."
            raise IOError, errmsg % group_name

        group = self._createGroup_(parent, name, **attrs)
        self._registerGroupName(group)
        return group

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteGroup(self, group_name):
        self.assertFileWritable()
        self._deleteGroup_(self._hdf5_file_, group_name)

    def deleteGroupAttribute(self, group_name, attr_name):
        self.assertFileWritable()
        group = self.getGroup(group_name)
        self._deleteGroupAttribute_(self._hdf5_file_, group_name, attr_name)

    def setGroupAttribute(self, group_name, attr_name, attr_value):
        self.assertFileWritable()
        self._setGroupAttribute_(self._hdf5_file_, group_name, attr_name,
                                  attr_value)

    def setGroupAttributes(self, group_name, **kwargs):
        self.assertFileWritable()
        self._setGroupAttributes_(self._hdf5_file_, group_name, kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def deleteObject(self, object_name):
        self.assertFileWritable()
        name, parent = self._pathToNameAndParent(self._hdf5_file_, dataset_name)
        self._deleteObject_(parent, object_name)

    def deleteObjectAttribute(self, object_name, attr_name):
        self._deleteObjectAttribute_(self.getObject(object_name), attr_name)

    def setObjectAttribute(self, object_name, attr_name, attr_value):
        self.assertFileWritable()
        _object = self.getObject(object_name)
        self._setObjectAttribute_(_object, attr_name, attr_value)

    def setObjectAttributes(self, object_name, **kwargs):
        self.assertFileWritable()
        self._setObjectAttributes_(self.getObject(object_name), kwargs)

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _processDataIn(self, dataset_name, data, **kwargs):
        data = self._prePack(dataset_name, data, **kwargs)
        return self._packData(dataset_name, data, **kwargs)

    def _getPacker(self, dataset_name):
        return self._packers.get(dataset_name,
                                 self._packers.get('default', None))

    def _packData(self, dataset_name, data, **kwargs):
        pack = self._getPacker(dataset_name)
        if pack is None: return data
        else: return pack(data)

    def _prePack(self, dataset_name, data, **kwargs):
        return data

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _registerDatasetName(self, dataset):
        if isinstance(dataset, h5py.Dataset):
            path = self.dotPath(dataset.name)
            if path not in self._dataset_names:
                names = list(self._dataset_names)
                names.append(path)
                names.sort()
                self._dataset_names = tuple(names)
        else:
            errmsg = 'Invalid type for "dataset" argumnent : %s'
            raise TypeError, errmsg % type(dataset)

    def _registerGroupName(self, group):
        if isinstance(group, h5py.Group):
            path = self.dotPath(group.name)
            if path not in self._group_names:
                names = list(self._group_names)
                names.append(path)
                names.sort()
                self._group_names = tuple(names)
        else:
            errmsg = 'Invalid type for "group" argumnent : %s'
            raise TypeError, errmsg % type(group)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Hdf5FileBuilder(Hdf5FileManager):
    """ Provides read/write access to datasets, groups and other obsects
    in Hdf5-encoded files.
    """

    def __init__(self, hdf5_filepath, mode='w'):
        self._access_authority = ('r','a','w')
        if mode not in self._access_authority:
            errmsg = "'%s' is not in list of modes allowed by this manager."
            raise ValueError, errmsg % mode

        Hdf5FileManager.__init__(self, hdf5_filepath, mode)

        self.setFileAttribute('created', self.timestamp)
        self.close()
        self.open(mode='a')

