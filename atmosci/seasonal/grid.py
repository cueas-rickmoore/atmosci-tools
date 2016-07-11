
from atmosci.hdf5.manager import Hdf5DateGridFileReader
from atmosci.hdf5.manager import Hdf5DateGridFileManager

from atmosci.seasonal.methods.tempext  import TempextAccessMethods
from atmosci.seasonal.methods.tempext  import TempextUpdateMethods
from atmosci.seasonal.methods.builder  import TimeGridFileBuildMethods
from atmosci.seasonal.methods.timegrid import TimeGridFileReaderMethods
from atmosci.seasonal.methods.timegrid import TimeGridFileManagerMethods

from atmosci.seasonal.methods.grid import hdf5ReaderPatch


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SeasonalGridFileReader(TempextAccessMethods,
                             TimeGridFileReaderMethods,
                             Hdf5DateGridFileReader):

    def __init__(self, filepath, registry):
        self._preInitProject_(registry)
        Hdf5DateGridFileReader.__init__(self, filepath)
        hdf5ReaderPatch(self)
        self._postInitProject_()

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        Hdf5DateGridFileReader._loadManagerAttributes_(self)
        self._loadProjectFileAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SeasonalGridFileManager(TempextUpdateMethods,
                              TimeGridFileManagerMethods,
                              Hdf5DateGridFileManager):

    def __init__(self, filepath, registry, mode='r'):
        self._preInitProject_(registry)
        Hdf5DateGridFileManager.__init__(self, filepath, mode)
        hdf5ReaderPatch(self)
        self._postInitProject_()

    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        Hdf5DateGridFileManager._loadManagerAttributes_(self)
        self._loadProjectFileAttributes_()


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SeasonalGridFileBuilder(TimeGridFileBuildMethods,
                              SeasonalGridFileManager):

    def __init__(self, filepath, registry, project_config, filetype, source,
                       target_year, region, **kwargs):

        self.preInitBuilder(project_config, filetype, source, target_year,
                            region, **kwargs)
        SeasonalGridFileManager.__init__(self, filepath, registry, 'w')
        self.initFileAttributes(**kwargs)
        self.postInitBuilder(**kwargs)
        self.close()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def updateDataset(self, dataset_path, start_time, data, **kwargs):
        self.open('a')
        SeasonalGridFileManager.updateDataset(self, dataset_path, start_time,
                                                    data, **kwargs)
        self.close()

    def updateProvenance(self, dataset_path, start_time, *data, **kwargs):
        self.open('a')
        SeasonalGridFileManager.updateProvenance(self, dataset_path, start_time,
                                                       *data, **kwargs)
        self.close()


    # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - # - - - #

    def _loadManagerAttributes_(self):
        SeasonalGridFileManager._loadManagerAttributes_(self)
        self._loadProjectFileAttributes_()

