
import os
import datetime

from atmosci.utils import tzutils
from atmosci.utils.timeutils import lastDayOfMonth

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

    def fcastObsTimespan(self, reference_date_or_time, **kwargs):
        if isinstance(reference_date_or_time, datetime.date):
            target = kwargs.get('target_hour', self.project.target_hour)
            ref_time = datetime.datetime.combine(reference_date_or_time,
                                                 datetime.time(target))
        else: # assume it is already a datetime.datetime
            ref_time = reference_date_or_time

        timezone = kwargs.get('timezone', 'UTC')
        ref_time = tzutils.asHourInTimezone(ref_time, timezone)
        
        fcast_days = kwargs.get('fcast_days',self.project.fcast_days)
        fcast_hours = fcast_days * 24
        end_time = ref_time + datetime.timedelta(hours=fcast_hours)

        obs_days = kwargs.get('obs_days',self.project.obs_days)
        obs_hours = obs_days * 24
        start_time = ref_time - datetime.timedelta(hours=obs_hours)

        return start_time, ref_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribVariableName(self, key):
        var_name = self.reanalysis.grib.variable_map.get(key, key.upper())
        if var_name in self.reanalysis.grib.variable_names:
            return var_name
        raise KeyError, '"%s" is not a valid GRIB variable key' % key

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridVariableName(self, key):
        var_name = self.reanalysis.grid.variable_map.get(key, key.upper())
        if var_name in self.reanalysis.grid.variable_names:
            return var_name
        raise KeyError, '"%s" is not a valid GRID variable key' % key

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def monthTimespan(self, reference_date, **kwargs):
        if reference_date.day == 1: ref_date = reference_date
        else: ref_date = reference_date.replace(day=1) 
        ref_time = \
            datetime.datetime.combine(ref_date,datetime.time(hour=0))

        timezone = kwargs.get('timezone', 'UTC')
        start_time = ref_time = tzutils.asHourInTimezone(ref_time, timezone)
        num_days = lastDayOfMonth(ref_date.year, ref_date.month)
        end_time = start_time.replace(day=num_days, hour=23)

        return start_time, end_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def fileTimespan(self, reference_date, **kwargs):
        if isinstance(reference_date, tuple):
            if len(reference_date == 2):
                ref_date = reference_date + (1,)
            else: ref_date = reference_date
        else: # assume it is datetime.date or datetime.date_time
            ref_date = \
                (reference_date.year, reference_date.month, reference_date.day)

        ref_date = datetime.date(*ref_date)
        if kwargs.get('grid_subdir_by_hours',False):
            # timespan based number of hours in obs_days + fcast_days
            start_time, ref_time, end_time = \
                self.fcastObsTimespan(reference_date, **kwargs)

        else: # timespan based on number of days in a month 
            start_time, end_time = self.monthTimespan(ref_date, **kwargs)
            ref_time = start_time
        
        num_hours = tzutils.hoursInTimespan(start_time, end_time)
        return start_time, ref_time, end_time, num_hours

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setDataSource(self, data_source, **kwargs):
        if isinstance(data_source, basestring):
            self.source = self.anal_config[data_source]
        else: # assume it is an atmosci.utils.config ConfigObject
            self.source = data_source.copy()

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
        elif kwargs.get('use_time_in_path', False):
            return tzutils.utcTimeStrings(datetime_hour)
        else: 
            utc_times = tzutils.utcTimeStrings(datetime_hour)
            utc_times['utc_time'] = utc_times['utc_date']
            return utc_times

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initReanalysisFactory_(self, analysis_type, **kwargs):
        self.project = self.config.project
        self.reanalysis = self.config.sources.reanalysis
        self.setAnalysisType(analysis_type) # also sets source

        timezone = kwargs.get('timezone', self.source.get('timezone', 'UTC'))
        self.setTimezone(timezone)

        if kwargs.get('use_dev_env', False):
            self.useDirpathsForMode('dev')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGribFactoryMethods(ReanalysisFactoryMethods):

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribDirpath(self, target_hour, region, **kwargs):
        if self.project.get('shared_grib_dir', False):
            root_dir = self.sharedRootDir()
        else:
            root_dir = self.project.get('grib_dirpath', self.appDataRootDir())
        # check for subdir path definition
        subdir = self.gribSubdir()
        if subdir is not None: root_dir = os.path.join(root_dir, subdir)
        # get all possible template arguments for the directory path
        arg_dict = self.utcTimes(target_hour)
        arg_dict['analysis'] = self.analysis
        arg_dict['region'] = region
        arg_dict['source'] = self.source.name
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
        arg_dict = \
            self._templateArgs(target_hour, variable, region, **kwargs)
        if kwargs: arg_dict.update(dict(kwargs))
        return template % arg_dict

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribFilenameTemplate(self, variable, **kwargs):
        template = self.source.local_file_map.get(variable,
                        self.source.local_file_map.get('default', None))
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
        source = kwargs.get('source', self.source)
        return Class(filepath, source, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gribSubdir(self):
        subdir = self.source.get('grib_subdir',
                      self.reanalysis.get('grib.subdir', None))
        if isinstance(subdir, tuple): return os.path.join(*subdir)
        return subdir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setAnalysisType(self, analysis_type, **kwargs):
        analysis, source = analysis_type.split('.')
        self.analysis = analysis

        if self.analysis == 'rtma':
            from atmosci.reanalysis.rtma.config import RTMA_SOURCES
            self.anal_config = RTMA_SOURCES
        elif self.analysis == 'urma':
            from atmosci.reanalysis.urma.config import URMA_SOURCES
            self.anal_config = URMA_SOURCES
        else:
            errmsg = '"%s" is an unsupported reanalysis.'
            raise KeyError, errmsg % self.analysis

        self.setDataSource(source, **kwargs)
        self.region = kwargs.get('region',
                             self.anal_config.get('region',
                                  self.source.get('region', 'conus')))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def serverURL(self, server_type='http'):
        return self.source.get(server_type, None)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _templateArgs(self, target_hour, variable, region, **kwargs):
        template_args = tzutils.utcTimeStrings(target_hour)
        template_args['analysis'] = self.analysis
        template_args['region'] = region
        template_args['source'] = self.source.name
        template_args['variable'] = variable
        return template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessClasses(self):
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)

        from atmosci.reanalysis.grib import ReanalysisGribReader
        self._registerAccessManager('grib', 'read', ReanalysisGribReader)

        from atmosci.seasonal.static import StaticGridFileReader
        self._registerAccessManager('static', 'read', StaticGridFileReader)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initReanalysisGribFactory_(self, analysis_source, **kwargs):
        self._initReanalysisFactory_(analysis_source, **kwargs)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGribFileFactory(StaticFileAccessorMethods,
                                ReanalysisGribFactoryMethods, object):
    """
    Basic factory for accessing data in Reanalysis grib files.
    """
    def __init__(self, analysis_source, config_object=CONFIG, **kwargs):
        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, 'project')

        # initialize reanalysis grib-specific configuration
        self._initReanalysisGribFactory_(analysis_source, **kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGridFactoryMethods(ReanalysisFactoryMethods):
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def analysisGridDirpath(self, reference_time, variable, region, **kwargs):
        if self.project.get('shared_grid_dir', False):
            root_dir = self.sharedRootDir()
        else:
            root_dir = self.config.dirpaths.get(self.analysis,
                            self.config.dirpaths.get('reanalysis',
                                 self.projectRootDir()))
        subdir = self.gridSubdir(**kwargs)
        if subdir is not None: root_dir = os.path.join(root_dir, subdir)
        arg_dict = \
            self._templateArgs(reference_time, variable, region, **kwargs)
        arg_dict['region'] = self.regionToDirpath(arg_dict['region'])
        grid_dirpath = root_dir % arg_dict
        if not os.path.exists(grid_dirpath):
            if kwargs.get('file_must_exist', False):
                errmsg = 'Reanalysis directory does not exist :\n%s'
                raise IOError, errmsg % grid_dirpath
            elif kwargs.get('make_grid_dirs', True):
                os.makedirs(grid_dirpath)
        return grid_dirpath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def analysisGridFilename(self, ref_time, variable, region, **kwargs):
        template = self.gridFilenameTemplate(variable, **kwargs)
        if template is None:
            raise LookupError, 'No template for "%s" grid file name' % variable
        arg_dict = self._templateArgs(ref_time, variable, region, **kwargs)
        arg_dict['region'] = self.regionToFilepath(arg_dict['region'])
        return template % arg_dict
 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def analysisGridFilepath(self, reference_time, variable, region, **kwargs):
        filepath = kwargs.get('filepath', None)
        if filepath is None:
            root_dir = self.analysisGridDirpath(reference_time, variable,
                                                region, **kwargs)
            filename = self.analysisGridFilename(reference_time, variable,
                                                region, **kwargs)
            filepath = os.path.join(root_dir, filename)
        if kwargs.get('file_must_exist', False):
            if not os.path.isfile(filepath):
                errmsg = 'Reanalysis grid file does not exist :\n    %s'
                raise IOError, errmsg % filepath
        return filepath

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def availableMonths(self, reference_time, region, variable=None):
        months = [ ]

        ref_time = reference_time.replace(day=1, hour=0)
        dirpath = self. analysisGridDirpath(ref_time, variable, region,
                                            make_grid_dirs=False)
        if os.path.exists(dirpath): months.append(ref_time.month)
        prev_month_str = ref_time.strftime('%Y%m')

        if ref_time.month < 12:
            for month in range(ref_time.month+1, 13):
                ref_time = ref_time.replace(month=month)
                month_str = ref_time.strftime('%Y%m')
                dirpath = dirpath.replace(prev_month_str, month_str)
                if os.path.exists(dirpath):
                    months.append(ref_time)
                prev_month_str = month_str

        return tuple(months)

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

    def gridFileBuilder(self, reference_time, variable, region, timezone,
                              lons=None, lats=None, **kwargs):
        filepath = kwargs.get('filepath', None)
        if filepath is None:
            filepath = self.analysisGridFilepath(reference_time, variable,
                                                 region, **kwargs)
        kwargs['timezone'] = timezone
        kwargs.update(self._extractTimes(reference_time, **kwargs))
        del kwargs['timezone']
        Class = self.fileAccessorClass('build')
        return Class(filepath, CONFIG, variable, region, self.source,
                     reference_time, timezone, lons, lats, kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFileManager(self, reference_time, variable, region, **kwargs):
        filepath = self.analysisGridFilepath(reference_time, variable,
                                             region, **kwargs)
        Class = self.fileAccessorClass('manage')
        return Class(filepath, kwargs.get('mode','r'))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFileReader(self, reference_time, variable, region, **kwargs):
        filepath = self.analysisGridFilepath(reference_time, variable,
                                             region, **kwargs)
        Class = self.fileAccessorClass('read')
        return Class(filepath)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridFilenameTemplate(self, variable, **kwargs):
        if kwargs.get('subdir_by_hours',False):
            template = self.fcast_obs_file_map.get(variable, None)
        else: template = self.month_file_map.get(variable, None)
        if template is None:
            errmsg = 'No template found for "%s" variable.'
            raise ValueError, errmsg % variable
        return template

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def gridSubdir(self, **kwargs):
        if kwargs.get('subdir_by_hours',False):
            subdir = self.source.subdir_by_hours
        else: subdir = self.source.subdir_by_year

        if isinstance(subdir, tuple): return os.path.join(*subdir)
        else: return subdir

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setAnalysisType(self, analysis_type, **kwargs):
        self.analysis = analysis_type
        self.anal_config = None
        self.source = self.config.sources.reanalysis.grid
        self.region = kwargs.get('region',
                             self.source.get('region', 'conus'))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _extractTimes(self, ref_time, **kwargs):
        start_time = kwargs.get('start_time', None)
        if start_time is None:
            if kwargs.get('grid_subdir_by_hours',False):
                start_time, xxx, end_time = \
                    self.fcastObsTimespan(ref_time, **kwargs)
            else:
                start_time, end_time = self.monthTimespan(ref_time, **kwargs)
        else: end_time = kwargs.get('end_time')
        num_hours = tzutils.hoursInTimespan(start_time, end_time)
                
        return { 'end_time': end_time,
                 'num_hours': num_hours,
                 'start_time': start_time }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _templateArgs(self, ref_time, variable, region, **kwargs):
        template_args = tzutils.tzaTimeStrings(ref_time, 'target')
        times = self._extractTimes(ref_time, **kwargs)
        if kwargs.get('grid_subdir_by_hours',False):
            template_args['num_hours'] = times['num_hours']

        template_args['analysis'] = self.analysis
        template_args['region'] = region
        if self.source is not None:
            template_args['source'] = self.source.get('tag', self.source.name)
        if variable is not None:
            template_args['variable'] = variable
        return template_args

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initReanalysisGridFactory_(self, analysis_type, **kwargs):
        self._initReanalysisFactory_(analysis_type, **kwargs)
        self.month_file_map = self.reanalysis.grid_file_maps.month
        self.fcast_obs_file_map = self.reanalysis.grid_file_maps.fcast_obs
        if kwargs.get('use_dev_env', False): self.useDirpathsForMode('dev')

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessClasses(self):
        # make sure there is a dictionary for registering file access classes
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)

        from atmosci.reanalysis.grid import ReanalysisGridFileReader, \
                                            ReanalysisGridFileManager, \
                                            ReanalysisGridFileBuilder
        self._registerAccessManagers('reanalysis', ReanalysisGridFileReader,
                                                   ReanalysisGridFileManager,
                                                   ReanalysisGridFileBuilder)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ReanalysisGridFileFactory(StaticFileAccessorMethods,
                                ReanalysisGridFactoryMethods, object):
    """
    Basic factory for accessing data in Reanalysis grib files.
    """
    def __init__(self, config_object=CONFIG, analysis_type='reanalysis',
                       **kwargs):

        # initialize common configuration structure
        self._initFactoryConfig_(config_object, None, None)

        # initialize reanalysis grib-specific configuration
        self._initReanalysisGridFactory_(analysis_type, **kwargs)

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization(**kwargs)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def buildReanalysisGridFile(self, reference_time, variable, grid_region,
                                timezone):
        builder = self.gridFileBuilder(reference_time, variable, grid_region,
                                       timezone, None, None)
        region = factory.regionConfig(grid_region)
        source = factory.sourceConfig('acis')
        reader = factory.staticFileReader(source, region)
        lats = reader.getData('lat')
        lons = reader.getData('lon')
        reader.close()
        del reader

        # build all of the datasets
        builder.build(lons=lons, lats=lats)
        del lats, lons
        print '\nBuilt "%s" reanalysis grid file :' % variable
        print '    ', builder.filepath
        builder.close()

