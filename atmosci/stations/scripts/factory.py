
import os

from nrcc.region.factory import RegionDataManagerFactory
from nrcc.stations.manager import StationDataFileManager
from nrcc.stations.cleaner import StationDirectoryCleaner

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from nrcc.config import STATIONS

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class StationDataManagerFactory(RegionDataManagerFactory):

    def __init__(self, date, options):
        RegionDataManagerFactory.__init__(self, date, options, STATIONS)

    def _setLocalAttrs(self, options):
        RegionDataManagerFactory._setLocalAttrs(self, options)
        if hasattr(options, 'base_url') and options.base_url is not None:
            self.base_url = options.base_url
        else:
            self.base_url = STATIONS.download_url

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def getDirectoryCleaner(self):
        return StationDirectoryCleaner(self.getDirectory('working'))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerDataFilepaths(self, options):
        data_filepaths = { }
        
        if hasattr(options,'station_filepath') and\
           options.station_filepath is not None:
            station_filepath = os.path.normpath(options.station_filepath)
            if os.path.isdir(station_filepath):
                filename = STATIONS.cache_file % (self.region_name, 
                                                  self.date[0], self.date[1],
                                                  self.date[2])
                station_filepath = os.path.join(station_filepath, filename)
            else:
                dirpath, filename = os.path.split(station_filepath)
                if dirpath and not os.path.isdir(dirpath):
                    errmsg = "Could not find directory for station file : %s"
                    raise IOError, errmsg % dirpoath
        else:
            working_dir = self.getDirectory('working')
            if not os.path.isdir(working_dir):
                errmsg = "Working directory could not be found : %s"
                raise IOError, errmsg % working_dir

            filename = STATIONS.cache_file % (self.region_name, self.date[0],
                                              self.date[1], self.date[2])
            station_filepath = os.path.join(working_dir, filename)

        data_filepaths['region'] = station_filepath
        data_filepaths['stn'] = station_filepath
        data_filepaths['station'] = station_filepath
        data_filepaths['stations'] = station_filepath

        return data_filepaths

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerDataManagers(self, options):
        manager_classes = { }

        manager_classes['region'] = StationDataFileManager
        manager_classes['stn'] = StationDataFileManager
        manager_classes['station'] = StationDataFileManager
        manager_classes['stations'] = StationDataFileManager

        return manager_classes

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerDirectories(self, options):
        directories = { }
        date = self.date

        if hasattr(options,'working_dir') and\
           options.working_dir is not None:
            working_dir = os.path.normpath(options.working_dir)
            if not os.path.isdir(self.working_dir):
                errmsg = "working directory could not be found : %s"
                raise IOError, errmsg % working_dir
        else:
            working_dir = os.path.normpath(STATIONS.working_dir)
        directories['working'] = working_dir

        return directories
