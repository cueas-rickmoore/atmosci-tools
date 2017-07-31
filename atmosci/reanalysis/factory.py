
import os
import datetime

from atmosci.utils import tzutils

from atmosci.seasonal.methods.access  import BasicFileAccessorMethods
from atmosci.seasonal.methods.factory import MinimalFactoryMethods
from atmosci.seasonal.methods.paths   import PathConstructionMethods
from atmosci.seasonal.methods.static  import StaticFileAccessorMethods


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.reanalysis.config import CONFIG


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisFactoryMethods(PathConstructionMethods,
                               BasicFileAccessorMethods,
                               MinimalFactoryMethods):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def asLocalHour(self, datetime_hour, local_timezone=None):
        return tzutils.asLocalHour(datetime_hour, local_timezone)

    def asUtcHour(self, datetime_hour, local_timezone=None):
        return tzutils.asUtcHour(datetime_hour, local_timezone)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def availableTimeSpan(self, num_hours=3):
        latest_time = datetime.datetime.utcnow()
        if latest_time.minute < 30: previous_hour = 2
        else: previous_hour = 1
        latest_time.replace(minute=0, second=0, microsecond=0)
        latest_time -= datetime.timedelta(hours=previous_hour)
        return (latest_time-datetime.timedelta(hours=num_hours), lastest_time)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def fileTimespan(self, reference_date, obs_days, fcast_days, target_hour=7,
                           timezone='UTC'):
        reference_time = datetime.datetime.combine(reference_date,
                                           datetime.time(target_hour,0,0,0))
        reference_time = tzutils.asHourInTimezone(reference_time, timezone)
        fcast_hours = fcast_days * 24
        end_time = reference_time + datetime.timedelta(hours=fcast_hours)
        obs_hours = obs_days * 24
        start_time = reference_time - datetime.timedelta(hours=obs_hours)

        return start_time, reference_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setAnalysisSource(self, analysis_type):
        if '.' in analysis_type:
            analysis, grib_source = analysis_type.split('.')
            self.analysis = analysis
            self.anal_config = self.config.sources[analysis]
            self.setGribSource(grib_source)
        else:
            self.analysis = analysis_type
            self.anal_config = self.config.sources[analysis_type]
            self.grib_source = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setGribSource(self, grib_source):
        if isinstance(grib_source, basestring):
            self.grib_source = self.anal_config[grib_source]
        else: self.grib_source = grib_source.copy()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setTimezone(self, timezone):
        if tzutils.isValidTimezone(timezone):
            self.timezone = tzutils.timezoneAsString(timezone)
            self.tzinfo = timezone
        else:
            self.timezone = timezone
            self.tzinfo = tzutils.asTimezoneObj(timezone)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def utcTimes(self, datetime_hour, **kwargs):
        if kwargs.get('use_latest_time', False):
            return {'utc_date':'latest', 'utc_time':'latest',
                    'utc_hour':'latest'}
        elif kwargs.get('use_previous_time', False):
            return {'utc_date':'previous', 'utc_time':'previous',
                    'utc_hour':'previous'}
        elif kwargs.get('use_time_in_path', True):
            return tzutils.utcTimeStrings(datetime_hour)
        else: 
            utc_times = tzutils.utcTimeStrings(datetime_hour)
            utc_times['utc_time'] = utc_times['utc_date']
            return utc_times

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initReanalysisFactory_(self, analysis_type, timezone='UTC', **kwargs):
        if kwargs.get('use_dev_env', False):
            self.useDirpathsForMode('dev')
        self.reanalysis = self.config.sources.reanalysis.project
        self.setAnalysisSource(analysis_type)
        self.setTimezone(timezone)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGribFactoryMethods(ReanalysisFactoryMethods):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribDirpath(self, target_hour, region, **kwargs):
        if self.project.get('shared_grib_dir',
                self.reanalysis.get('shared_grib_dir', False) ):
            root_dir = self.sharedRootDir()
        else:
            root_dir = self.project.get('grib_dirpath',
                            self.reanalysis.get('grib_dirpath',
                                 self.appDataRootDir() ) )
        # check for subdir path definition
        subdir = self.gribSubdir()
        if subdir is not None: root_dir = os.path.join(root_dir, subdir)
        # get all possible template arguments for the directory path
        arg_dict = self.utcTimes(target_hour)
        arg_dict['analysis'] = self.analysis
        arg_dict['region'] = region
        arg_dict['source'] = self.grib_source.name
        grib_dirpath = root_dir % arg_dict
        # check for existence of the directory
        if not os.path.exists(grib_dirpath):
            # user is expecting the file to exist, fail when missing
            if kwargs.get('file_must_exist', False):
                errmsg = 'Reanalysis directory does not exist :\n%s'
                raise IOError, errmsg % grib_dirpath
            else: os.makedirs(grib_dirpath)
        return grib_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribFilename(self, target_hour, variable, region, **kwargs):
        template = self.gribFilenameTemplate(variable)
        template_args = \
            self._templateArgs(target_hour, variable, region, **kwargs)
        if kwargs: template_args.update(dict(kwargs))
        return template % template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribFilenameTemplate(self, variable):
        template = self.grib_source.local_file_map.get(variable,
                        self.grib_source.local_file_map.get('default', None))
        if template is None:
            errmsg = 'No filename template for "%s" variable.'
            raise LookupError, errmsg % variable
        return template
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribFilepath(self, target_hour, variable, region, **kwargs):
        filepath = kwargs.get('filepath', None)
        if filepath is None:
            root_dir = self.gribDirpath(target_hour, region, **kwargs)
            filename =  self.gribFilename(target_hour, variable, region,
                                          **kwargs)
            filepath = os.path.join(root_dir, filename)
        # check for existence of the file
        if kwargs.get('file_must_exist', False):
            # user is expecting the file to exist, fail when missing
            if not os.path.isfile(filepath):
                errmsg = 'Reanalysis grib file does not exist :\n    %s'
                raise IOError, errmsg % filepath
        return filepath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribFileReader(self, target_hour, variable, region, **kwargs):
        filepath = self.gribFilepath(target_hour, variable, region, **kwargs)
        Class = self.fileAccessorClass('grib', 'read')
        debug = kwargs.get('debug',False)
        grib_source = kwargs.get('grib_source', self.grib_source)
        return Class(filepath, grib_source, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribSubdir(self):
        subdir = self.grib_source.get('grib_subdir',
                      self.project.get('grib_subdir',
                           self.reanalysis.get('grib_subdir', None) ) )
        if isinstance(subdir, tuple): return os.path.join(*subdir)
        return subdir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def serverURL(self, server_type='http'):
        return self.grib_source.get(server_type, None)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _templateArgs(self, target_hour, variable, region, **kwargs):
        template_args = tzutils.utcTimeStrings(target_hour)
        template_args['analysis'] = self.analysis
        template_args['region'] = region
        template_args['source'] = self.grib_source.name
        template_args['variable'] = variable
        return template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initReanalysisGribFactory_(self, grib_source_path, **kwargs):
        self.setAnalysisSource(grib_source_path)
        self._initReanalysisFactory_(grib_source_path, **kwargs)

    def _registerAccessClasses(self):
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)

        from atmosci.reanalysis.grib import ReanalysisGribReader
        self._registerAccessManager('grib', 'read', ReanalysisGribReader)

        from atmosci.seasonal.static import StaticGridFileReader
        self._registerAccessManager('static', 'read', StaticGridFileReader)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGribFileFactory(ReanalysisGribFactoryMethods,
                                StaticFileAccessorMethods, object):
    """
    Basic factory for accessing data in Reanalysis grib files.
    """
    def __init__(self, grib_source_path, config_object=CONFIG, **kwargs):
        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, 'project')

        # initialize reanalysis grib-specific configuration
        self._initReanalysisGribFactory_(grib_source_path, **kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGridFactoryMethods(ReanalysisFactoryMethods):
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def analysisGridDirpath(self, variable, region, **kwargs):
        if self.project.get('shared_grid_dir', 
                self.reanalysis.get('shared_grid_dir', False) ):
            root_dir = self.sharedRootDir()
        else:
            root_dir = self.config.dirpaths.get(self.analysis,
                            self.config.dirpaths.get('reanalysis',
                                 self.projectRootDir()))
        subdir = self.gridSubdir()
        if subdir is not None: root_dir = os.path.join(root_dir, subdir)
        template_args = self._templateArgs(variable, region, **kwargs)
        grid_dirpath = root_dir % template_args
        if not os.path.exists(grid_dirpath):
            if kwargs.get('file_must_exist', False):
                errmsg = 'Reanalysis directory does not exist :\n%s'
                raise IOError, errmsg % grid_dirpath
            else: os.makedirs(grid_dirpath)
        return grid_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def analysisGridFilename(self, variable, region, **kwargs):
        template = self.gridFilenameTemplate(variable)
        if template is None:
            raise LookupError, 'No template for "%s" grid file name' % variable
        template_args = self._templateArgs(variable, region, **kwargs)
        return template % template_args
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def analysisGridFilepath(self, variable, region, **kwargs):
        filepath = kwargs.get('filepath', None)
        if filepath is None:
            root_dir = self.analysisGridDirpath(variable, region, **kwargs)
            filename = self.analysisGridFilename(variable, region, **kwargs)
            filepath = os.path.join(root_dir, filename)
        if kwargs.get('file_must_exist', False):
            if not os.path.isfile(filepath):
                errmsg = 'Reanalysis grid file does not exist :\n    %s'
                raise IOError, errmsg % filepath
        return filepath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def fileAccessorClass(self, access_type):
        Classes = self.AccessClasses.get(self.analysis, None)
        if Classes is None:
            errmsg = 'No file accessors are registered for "%s"' 
            raise KeyError, errmsg % self.analysis
        accessor = Classes.get(access_type, None)
        if accessor is None:
            errmsg = 'No file %s accessor registered for "%s"' 
            raise KeyError, errmsg % (access_type, self.analysis)
        return accessor

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFileBuilder(self, variable, region, lons=None, lats=None, 
                              **kwargs):
        filepath = self.analysisGridFilepath(variable, region, **kwargs)
        Class = self.fileAccessorClass('build')
        # filetype == variable
        # source = self.analysis = self.anal_config
        return Class(filepath, CONFIG, variable, region, self.anal_config,
                     self.tzinfo, lons, lats, **kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFileManager(self, variable, region, **kwargs):
        filepath = self.analysisGridFilepath(variable, region, **kwargs)
        Class = self.fileAccessorClass('manage')
        return Class(filepath, kwargs.get('mode','r'))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFileReader(self, variable, region, **kwargs):
        filepath = self.analysisGridFilepath(variable, region, **kwargs)
        Class = self.fileAccessorClass('read')
        return Class(filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFilenameTemplate(self, variable):
        template = self.reanalysis.grid_file_map.get(variable, None)
        if template is None:
            errmsg = 'No template found for "%s" variable.'
            raise ValueError, errmsg % variable
        return template

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridSubdir(self):
        if self.grib_source is None:
            subdir = self.project.get('grid_subdir',
                          self.reanalysis.get('grid_subdir', None) )
        else:
            subdir = self.grib_source.get('grid_subdir',
                          self.project.get('grid_subdir',
                               self.reanalysis.get('grid_subdir', None) ) )
        if isinstance(subdir, tuple): return os.path.join(*subdir)
        return subdir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _extractTimes(self, **kwargs):
        times_missing = 'Neither "start_time" nor "end_time" were found in'
        times_missing += ' **kwargs. One of them MUST be specified.'
        hours_mising = '"num_hours" must be passed via **kwargs when only' 
        hours_mising = ' "%s" is specified' 

        timezone = kwargs.get('timezone', self.tzinfo)
        if tzutils.isValidTimezone(timezone): tzinfo = timezone
        else: tzinfo = tzutils.asTimezoneObj(timezone)

        start_time = kwargs.get('start_time', None)
        if start_time is None:
            end_time = kwargs.get('end_time', None)
            assert(end_time is not None), times_missing
            end_time = tzutils.asHourInTimezone(end_time, tzinfo)
            num_hours = kwargs.get('num_hours', None)
            assert(num_hours is not None), hours_missing % 'end_time'
            start_time = end_time - datetime.timedelta(hours=num_hours)
        else:
            start_time = tzutils.asHourInTimezone(start_time, tzinfo)
            end_time = kwargs.get('end_time', None)
            if end_time is None:
                num_hours = kwargs.get('num_hours', None)
                assert(num_hours is not None), hours_missing % 'start_time'
                end_time = start_time + datetime.timedelta(hours=num_hours)
            else:
                end_time = tzutils.asHourInTimezone(end_time, tzinfo)
                num_hours = tzutils.timeDifferenceInHours(start_time, end_time)

        times = self.utcTimes(end_time, **kwargs)
        times['end_time'] = end_time
        times['num_hours'] = num_hours
        times['start_time'] = start_time
        return times

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _templateArgs(self, variable, region, **kwargs):
        template_args = self._extractTimes(**kwargs)
        template_args['analysis'] = self.analysis
        template_args['region'] = region
        if self.grib_source is not None:
            template_args['source'] = self.grib_source.name
        if variable is not None:
            template_args['variable'] = variable
        return template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initReanalysisGridFactory_(self, analysis_type, timezone='UTC',
                                          **kwargs):
        self._initReanalysisFactory_(analysis_type, timezone)
        if kwargs.get('use_dev_env', False): self.useDirpathsForMode('dev')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessClasses(self):
        # make sure there is a dictionary for registering file access classes
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)

        from atmosci.hourly.grid import HourlyGridFileReader, \
                                        HourlyGridFileManager
        from atmosci.hourly.builder import HourlyGridFileBuilder
        self._registerAccessManagers('reanalysis', HourlyGridFileReader,
                                                   HourlyGridFileManager,
                                                   HourlyGridFileBuilder)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGridFileFactory(ReanalysisGridFactoryMethods, object):
    """
    Basic factory for accessing data in Reanalysis grib files.
    """
    def __init__(self, analysis_type='reanalysis',
                       config_object=CONFIG, **kwargs):
        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, None)

        # initialize reanalysis grib-specific configuration
        self._initReanalysisGridFactory_(analysis_type, **kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)

