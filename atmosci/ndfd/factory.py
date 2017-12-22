# Copyright (c) 2007-2018 Rick Moore and Cornell University Atmospheric
#                         Sciences
# All Rights Reserved
# Principal Author : Rick Moore
#
# ndfd is part of atmosci - Scientific Software for Atmosphic Science
#
# see copyright.txt file in this directory for details

import os
import datetime
import urllib

from atmosci.utils import tzutils
from atmosci.utils.config import ConfigObject
from atmosci.utils.timeutils import lastDayOfMonth

from atmosci.seasonal.methods.access  import BasicFileAccessorMethods
from atmosci.seasonal.methods.factory import MinimalFactoryMethods
from atmosci.seasonal.methods.paths   import PathConstructionMethods
from atmosci.seasonal.methods.static  import StaticFileAccessorMethods


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.ndfd.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# just-in-time registration of static file access classe
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _registerStaticFileReader(factory):
    from atmosci.seasonal.static import StaticGridFileReader
    factory._registerAccessManager('static', 'read', StaticGridFileReader)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NDFDFactoryMethods(StaticFileAccessorMethods, PathConstructionMethods,
                         BasicFileAccessorMethods, MinimalFactoryMethods):
    """ Methods for managing grib files from NDFD and generating directory
    and file paths for the downloaded NDFD grib files.
    """

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def asFileTime(self, time_obj):
        return tzutils.asHourInTimezone(time_obj, self.file_tzinfo)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def asLocalTime(self, time_obj):
        return tzutils.asHourInTimezone(time_obj, self.local_tzinfo)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def fileAccessorClass(self, file_type, access_type):
        Classes = self.AccessClasses.get(file_type, None)
        if Classes is None or access_type not in Classes:
            self._registerNdfdFileAccessor(file_type, access_type)
            Classes = self.AccessClasses[file_type]
        return Classes[access_type]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def monthTimespan(self, reference_date, **kwargs):
        if reference_date.day == 1: ref_date = reference_date
        else: ref_date = reference_date.replace(day=1) 
        ref_time = \
            datetime.datetime.combine(ref_date,datetime.time(hour=0))

        timezone = kwargs.get('timezone', self.file_tzinfo)
        start_time = ref_time = tzutils.asHourInTimezone(ref_time, timezone)
        num_days = lastDayOfMonth(ref_date.year, ref_date.month)
        end_time = start_time.replace(day=num_days, hour=23)

        return start_time, end_time


    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def regionToDirpath(self, region):
        if isinstance(region, ConfigObject):
            path = region.get('tag', None)
            if path is not None: return path
            path = region.name
        else: path = region
        if len(path) in (1, 2): return path.upper()
        else: return path.lower()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def regionToFilepath(self, region, title=True):
        if isinstance(region, ConfigObject):
            path = region.get('tag', None)
            if path is not None: return path
            path = region.name
        else: path = region
        if len(path) in (1, 2): return path.upper()
        if title:
            path = path.replace('_',' ').replace('.',' ').title()
            return path.replace(' ','-')
        else: return path.replace('_','-').replace('.','-')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setFileTimezone(self, timezone):
        if tzutils.isValidTimezone(timezone):
            self.file_timezone = tzutils.timezoneAsString(timezone)
            self.file_tzinfo = timezone
        else:
            self.file_timezone = timezone
            self.file_tzinfo = tzutils.asTimezoneObj(timezone)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setLocalTimezone(self, timezone):
        if tzutils.isValidTimezone(timezone):
            self.local_timezone = tzutils.timezoneAsString(timezone)
            self.local_tzinfo = timezone
        else:
            self.local_timezone = timezone
            self.local_tzinfo = tzutils.asTimezoneObj(timezone)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def sourceToDirpath(self, source):
        if isinstance(source, ConfigObject):
            subdir = source.get('subdir', None)
            if subdir is not None:
                return subdir
            else: return source.name.lower()
        return source.lower()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def sourceToFilepath(self, source):
        if isinstance(source, ConfigObject):
            path = source.get('tag', source.name.lower())
        else: path = source.lower()
        return path.replace(' ','-').replace('_','-').replace('.','-')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timeOfLatestForecast(self):
        latest_time = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
        return latest_time.replace(minute=0, second=0, microsecond=0)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timeToFilepath(self, fcast_date):
        return { 'date':fcast_date.strftime('%Y%m%d'),
                 'month':fcast_date.strftime('%Y%m'),
                 'year':fcast_date.year }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def variableConfig(self, variable, timespan='001-003'):
        return self.ndfd.variables[timespan][variable.lower()]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessClasses(self):
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)
        if not hasattr(self, 'AccessRegistrars'):
            self.AccessRegistrars = ConfigObject('AccessRegistrars', None)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerNdfdFileAccessor(self, file_type, access_type):
        self.AccessRegistrars[file_type][access_type](self)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initNdfdFactory_(self, config_object, **kwargs):
        self.ndfd = config_object.sources.ndfd
        timezone = kwargs.get('local_timezone', self.project.local_timezone)
        self.setLocalTimezone(timezone)
        if not hasattr(self, 'AccessRegistrars'):
            self.AccessRegistrars = ConfigObject('AccessRegistrars', None)
        # static file reader must be registered on init because code in
        # StaticFileAccessorMethods doesn't support just-in-time registration
        _registerStaticFileReader(self)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# just-in-time registration of grib file access classes
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _registerNdfdGribIterator(factory):
    from atmosci.ndfd.grib import NdfdGribFileIterator
    factory._registerAccessManager('ndfd_grib', 'iter', NdfdGribFileIterator)

def _registerNdfdGribReader(factory):
    from atmosci.ndfd.grib import NdfdGribFileReader
    factory._registerAccessManager('ndfd_grib', 'read', NdfdGribFileReader)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NdfdGribFactoryMethods(NDFDFactoryMethods):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def datasetName(self, variable, timespan='001-003'):
        return self.ndfd.variables[timespan][variable.lower()].grib_dataset

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdDownloadDir(self, fcast_date, region, dir_must_exist=True):
        # determine root directory of forecast tree
        shared_grib_dir = self.ndfd.get('shared_grib_dir',
                               self.project.get('shared_forecast', False))
        if shared_grib_dir:
            root_dir = self.sharedRootDir()
        else:
            root_dir = self.config.dirpaths.get('forecast', default=None)
            if root_dir is None: root_dir = self.projectRootDir()

        template = self.config.sources.ndfd.grib.subdirs
        if isinstance(template, (tuple, list)):
            template = os.sep.join(template)
        template_args = self.timeToFilepath(fcast_date)
        template_args['region'] = self.regionToDirpath(region)
        template_args['source'] = self.sourceToDirpath(self.ndfd)
        download_dir = os.path.join(root_dir, template % template_args)

        # make sure directory exists before return
        if dir_must_exist and not os.path.exists(download_dir):
            os.makedirs(download_dir)
        return download_dir

    ndfdGribDirpath = ndfdDownloadDir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGribFileAccessor(self, access_type):
        Classes = self.AccessClasses.get('ndfd_grib', None)
        if Classes is None or access_type not in Classes:
            self._registerNdfdGridAccessor(access_type)
        return self.AccessClasses.ndfd_grid[access_type]

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGribFilename(self, fcast_date, variable, timespan, region='conus'):
        template_args = { 'region':self.regionToFilepath(region),
                          'source':self.sourceToFilepath(self.ndfd),
                          'timespan':timespan, 'variable':variable.lower() }
        return self.ndfd.grib.file_template % template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGribFilepath(self, fcast_date, variable, timespan, region='conus',
                               source='nws', **kwargs):
        forecast_dir = self.ndfdDownloadDir(fcast_date, region)
        filename = \
           self.ndfdGribFilename(fcast_date, variable, timespan, **kwargs)
        return os.path.join(forecast_dir, filename)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGribIterator(self, fcast_date, variable, timespan, region='conus',
                                **kwargs):
        filepath = self.ndfdGribFilepath(fcast_date, variable, timespan,
                                         region, **kwargs)
        Class = self.fileAccessorClass('ndfd_grib','iter')
        return Class(filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGribReader(self, fcast_date, variable, timespan, region='conus',
                             **kwargs):
        filepath = \
            self.ndfdGribFilepath(fcast_date, variable, timespan, **kwargs)
        Class = self.fileAccessorClass('ndfd_grib','read')
        return Class(filepath, timespan, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def pathTemplateArgs(self, source, region):
        return { 'region':self.regionToFilepath(region),
                 'source':self.sourceToFilepath(source) }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setNdfdGribSource(self, source):
        self.ndfd_source = ndfd_source = self.ndfd[source]
        self.ndfd_server = ndfd_source.server_url
        self.ndfd_file_template = ndfd_source.filename
        self.ndfd_timespans = ndfd_source.timespans
        subdirs = ndfd_source.server_subdirs
        if isinstance(subdirs, basestring):
            self.ndfd_server_subdirs = subdirs
        else: self.ndfd_server_subdirs = os.path.join(subdirs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initNdfdGribFactory_(self, config_object, **kwargs):
        self._initNdfdFactory_(config_object, **kwargs)
        self.setNdfdGribSource(kwargs.get('source', self.ndfd.default_source))
        self.setFileTimezone(kwargs.get('grib_timezone',
                                        self.ndfd.grib.timezone))

        self.AccessRegistrars.ndfd_grib = { 'iter': _registerNdfdGribIterator,
                                            'read': _registerNdfdGribReader }


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NdfdGribFileFactory(NdfdGribFactoryMethods, object):
    """
    Factory for downloading and accessing data in NDFD grib files.
    """
    def __init__(self, config_object=CONFIG, **kwargs):
        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, 'project')

        # initialize reanalysis grib-specific configuration
        self._initNdfdGribFactory_(config_object, **kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def downloadLatestForecast(self, variables, periods=('001-003','004-007'),
                                     region='conus', verbose=False):
        target_date = self.timeOfLatestForecast()
        url_template = self.ndfdUrlTemplate()
        template_args = {'region':region.lower(), }

        filepaths = [ ]
        for variable in variables:
            template_args['variable'] = variable
            for period in periods:
                template_args['period'] = period
                ndfd_url = url_template % template_args
                if verbose: print '\ndownloading :', ndfd_url
                local_filepath = self.ndfdGribFilepath(self.ndfd_config,
                                      target_date, period, filetype)
                if verbose: print 'to :', local_filepath
            
                urllib.urlretrieve(ndfd_url, local_filepath)
                filepaths.append(local_filepath)

        return target_date, tuple(filepaths)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdUrlTemplate(self):
        return '/'.join( (self.ndfd_server, self.ndfd_subdir_path,
                          self.ndfd_file_template) )

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setDownloadAttempts(self, attempts):
        if isinstance(attempts, int): self.wait_attempts = attempts
        else: self.wait_attempts = int(attempts)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setDownloadWaitTime(self, seconds):
        if isinstance(seconds, float): self.wait_seconds = seconds
        else: self.wait_seconds = float(seconds)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# just-in-time registration of grid file access classes
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def _registerNdfdGridBuilder(factory):
    from atmosci.ndfd.grid import NdfdGridFileBuilder
    factory._registerAccessManager('ndfd_grid', 'build', NdfdGridFileBuilder)

def _registerNdfdGridManager(factory):
    from atmosci.ndfd.grid import NdfdGridFileManager
    factory._registerAccessManager('ndfd_grid', 'manage', NdfdGridFileManager)

def _registerNdfdGridReader(factory):
    from atmosci.ndfd.grid import NdfdGridFileReader
    factory._registerAccessManager('ndfd_grid', 'read', NdfdGridFileReader)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NdfdGridFactoryMethods(NDFDFactoryMethods):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def buildForecastGridFile(self, forecast_date, variable, **kwargs):
        debug = kwargs.get('debug',False)
        region = kwargs.get('region',self.ndfd.grid.region)
        source = kwargs.get('source',self.ndfd.grid)
        timezone = kwargs.get('timezone',self.ndfd.grid.file_timezone)
        verbose = kwargs.get('verbose',False)
        
        build_args = { 'source':source, 'debug':debug, 'verbose':verbose }
        builder = self.ndfdGridFileBuilder(forecast_date, variable, region, 
                                           timezone, None, None, **build_args)
        if verbose: print '\nbuilding grid file :', builder.filepath
        builder.close()

        # get lat, lon grids for the source/region couplet
        reader = self.staticFileReader(self.sourceConfig(self.ndfd.grid.source), region)
        lats = reader.getData('lat')
        lons = reader.getData('lon')
        reader.close()
        del reader

        # build the file
        builder.open('a')
        builder.build(lons=lons, lats=lats)
        builder.close()
        del lats, lons

        if debug:
            builder.open('r')
            time_attrs = builder.timeAttributes(self.datasetName(variable))
            builder.close()
            print '\nbuild file time attrs :'
            for key, value in time_attrs.items():
                print '    %s : %s' % (key, repr(value))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def datasetName(self, variable, timespan='001-003'):
        return self.ndfd.variables[timespan][variable.lower()].grid_dataset

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGridDirpath(self, fcast_date, variable, region, **kwargs):
        if self.project.get('shared_grid_dir', False):
            root_dir = self.sharedRootDir()
        else:
            root_dir = self.config.dirpaths.get('ndfd',
                            self.config.dirpaths.get('forecast',
                                 self.projectRootDir()))

        subdirs = kwargs.get('subdirs', self.ndfd.grid.subdirs)
        if isinstance(subdirs, tuple): subdirs = os.sep.join(subdirs)
        dirpath_template = os.path.join(root_dir, subdirs)

        template_args = { 'month': fcast_date.strftime('%Y%m'),
                          'region': self.regionToDirpath(region),
                          'source': self.sourceToDirpath(self.ndfd),
                          'year': fcast_date.year }
        template_args['variable'] = self.variableConfig(variable).grid_filetype

        grid_dirpath = dirpath_template % template_args
        if not os.path.exists(grid_dirpath):
            if kwargs.get('file_must_exist', False):
                errmsg = 'Reanalysis directory does not exist :\n%s'
                raise IOError, errmsg % grid_dirpath
            elif kwargs.get('make_grid_dirs', True):
                os.makedirs(grid_dirpath)
        return grid_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGridFilename(self, fcast_date, variable, region, **kwargs):
        filename_args = dict(kwargs)
        filename_args['month'] = fcast_date.strftime('%Y%m')
        filename_args['region'] = self.regionToFilepath(region)
        filename_args['source'] = self.sourceToFilepath(self.ndfd)

        var_key = filename_args.get('variable', variable)
        var_config = self.variableConfig(var_key)
        filename_args['variable'] = var_config.grid_filetype

        filetype = self.config.filetypes[var_config.grid_filetype]
        return filetype.filename % filename_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGridFilepath(self, fcast_date, variable, region, **kwargs):
        forecast_dir = \
            self.ndfdGridDirpath(fcast_date, variable, region, **kwargs)
        filename = \
            self.ndfdGridFilename(fcast_date, variable, region, **kwargs)
        return os.path.join(forecast_dir, filename)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGridFileBuilder(self, fcast_date, variable, region, timezone,
                                  lons=None, lats=None, **kwargs):
        filepath = \
            self.ndfdGridFilepath(fcast_date, variable, region, **kwargs)
        start_time, end_time = self.monthTimespan(fcast_date, **kwargs)

        file_type = self.variableConfig(variable).grid_filetype
        Class = self.fileAccessorClass('ndfd_grid', 'build')
        return Class(filepath, self.config, file_type, region, start_time, 
                     end_time, timezone, lons, lats, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGridFileManager(self, fcast_date, variable, region, **kwargs):
        filepath = \
            self.ndfdGridFilepath(fcast_date, variable, region, **kwargs)

        Class = self.fileAccessorClass('ndfd_grid', 'manage')
        return Class(filepath, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGridFileReader(self, fcast_date, variable, region, **kwargs):
        filepath = \
            self.ndfdGridFilepath(fcast_date, variable, region, **kwargs)

        Class = self.fileAccessorClass('ndfd_grid', 'read')
        return Class(filepath, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def ndfdGridDatasetName(self, variable):
        return self.variableConfig(variable).grid_dataset

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initNdfdGridFactory_(self, config_object, **kwargs):
        self._initNdfdFactory_(config_object, **kwargs)
        timezone = kwargs.get('grid_timezone', self.ndfd.grid.timezone)
        self.setFileTimezone(timezone)

        self.AccessRegistrars.ndfd_grid = {
                              'build': _registerNdfdGridBuilder,
                              'manage': _registerNdfdGridManager,
                              'read': _registerNdfdGridReader }


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class NdfdGridFileFactory(NdfdGridFactoryMethods, object):
    """
    Factory for managing data in NDFD forecast grid files.
    """
    def __init__(self, config_object=CONFIG, **kwargs):
        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, 'project')

        # initialize NDFD grid-specific configuration
        self._initNdfdGridFactory_(config_object, **kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)

