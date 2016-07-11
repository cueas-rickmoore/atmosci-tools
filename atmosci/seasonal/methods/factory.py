
import os

from copy import deepcopy
import datetime

from atmosci.utils.config import ConfigObject
from atmosci.utils.timeutils import timeSpanToIntervals, yearFromDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# CONVENIENCE FUNCTIONS COMMON TO MULTIPLE PROJECT TYPES
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class BasicProjectFactoryMethods:

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # configuration access functions 
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def fromConfig(self, config_item_path, **kwargs):
        try:
            item = self.config.get(config_item_path)
        except KeyError as e:
            if 'default' in kwargs: return kwargs['default']
            errmsg = 'full path = "%s"' % config_object_path
            e.args += (errmsg,)
            raise e
        if isinstance(item, ConfigObject): return item.copy()
        else: return deepcopy(item)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def datasetConfig(self, dataset_key):
        return self.config.datasets[dataset_key]
    getDatasetConfig = datasetConfig

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def filetypeConfig(self, filetype_key):
        if '.' in filetype_key:
            filetype, source_key = filetype_key.split('.')
            ft_cfg = self.config.filetypes.get(filetype, None)
            if ft_cfg is not None:
                src_cfg = ft_cfg.get(source_key, None)
                if src_cfg is not None: return src_cfg
        else:
            ft_cfg = self.config.filetypes.get(filetype_key, None)
        return ft_cfg
    getFiletypeConfig = filetypeConfig

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def groupConfig(self, group_key):
        return self.config.groups[group_key]
    getGroupConfig = groupConfig

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def projectConfig(self):
        return self.config.project
    getProjectConfig = projectConfig

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def provenanceConfig(self, provenance_key):
        return self.config.provenance[provenance_key]
    getProvenanceConfig = provenanceConfig

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def regionConfig(self, region_key):
        return self.config.regions[region_key]
    getRegionConfig = regionConfig

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def registryConfig(self): return self.registry
    getRegistryConfig = registryConfig

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    def sourceConfig(self, source_key):
        return self.config.sources[source_key]
    getSourceConfig = sourceConfig

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def sourceName(self, source):
        if isinstance(source, ConfigObject):
            return source.name
        elif isinstance(source, basestring):
            return source.lower()
        else:
            errmsg = 'Unsupported type for "source" argument : %s'
            return TypeError, errmsg % str(type(source))

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    # date and time span utilities
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def dateInSeason(self, date):
        year = self.targetYearFromDate(date)
        start_date = self.seasonStartDate(year)
        end_date = self.seasonEndDate(year)
        return (date >= start_date and date <= end_date)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def listDatesBetween(self, start_date, end_date):
        if end_date is None: return (start_date,)
        else: return timeSpanToIntervals(start_date, end_date, 'day', 1)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def seasonConfig(self, filetype=None):
        if filetype is None: return self.config.project
        else: 
            return self.config.filetypes[filetype].get('season',
                                                       self.config.project)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def seasonEndDate(self, target_year, filetype=None):
        season = self.seasonConfig(filetype)
        # end date is always in the target year
        return datetime.date(target_year, *season.end_day)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def seasonStartDate(self, target_year, filetype=None):
        # end day is always in the target year
        season = self.seasonConfig(filetype)
        # if start month is later in the year than to end month,
        # start date is in the year previous to the target year
        if season.start_day[0] > season.end_day[0]:
            return datetime.date(target_year-1, *season.start_day)
        # start day and end day are both in the same year
        else: return datetime.date(target_year, *season.start_day)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def targetYearFromDate(self, date, filetype=None):
        season = self.seasonConfig(filetype)
        if date.month > season.end_day[0]: return date.year + 1
        else: return date.year

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def targetDateSpan(self, year_or_date, filetpye=None):
        if isinstance(year_or_date, int):
            # input year is assumed to be the target year
            target_year = year_or_date

        elif isinstance(year_or_date, (tuple,list)):
            # input is a date tuple (year, month, day)
            target_year = \
                self.targetYearFromDate(datetime.date(year_or_date), filetype)

        elif isinstance(year_or_date, (datetime.datetime,datetime.date)):
            # year_or_start_date == datetime instance
            target_year = self.targetYearFromDate(year_or_date, filetype)

        else:
            errmsg = "Invalid type for 'year_or_date' argument : %s"
            raise TypeError, errmsg % type(year_or_date)

        end_date = self.seasonEndDate(target_year)
        start_date = self.seasonStartDate(target_year)
        return start_date, end_date

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def timestamp(self, as_file_path=False):
        if as_file_path:
            return datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        else: return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class BaseProjectFactory(BasicProjectFactoryMethods, object):
    """ Base class containing functions common to all factory subclasses.
    """

    def __init__(self, config_object, registry_object=None, project=None):
        self.config = config_object.copy()

        if project is None:
            self.project = self.config.project
        elif isinstance(project, ConfigObject):
            self.project = project.copy('project',None)
        elif isinstance(project, basestring):
            if projects in self.config:
                proj = self.config.projects.get(project, None)
                if proj is None:
                    msg = '"%s" project not found in config.projects'
                    raise AttributeError, msg % project
                self.project = proj.copy()
            else:
                raise LookupError, '"projects" object not found in config'
        else:
            msg = '%s is an invalid type for the "project" argument'
            raise TypeError, msg % str(type(project))

        if registry_object is not None:
            self.registry = registry_object.copy()
        else: self.registry = None

        # allow override of targetYearFromDate() from project's config object
        tyFunction = config_object.get('targetYearFromDate', None)
        if tyFunction is not None:
            self.targetYearFromDate = tyFunction

        # initilaize file access managers
        self._initFileManagerClasses_()

        # simple hook for subclasses to initialize additonal attributes  
        self.completeInitialization()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def completeInitialization(self):
        """ Pass thru so derived classes can assert minor initialization
        requirements.
        """
        pass

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _initFileManagerClasses_(self):
        # create a dictionary for registration of file access classes
        if not hasattr(self, 'AccessClasses'):
            self.AccessClasses = ConfigObject('AccessClasses', None)
        # register the factory-specific accessors
        self._registerAccessClasses()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessClasses(self):
        raise NotImplementedError

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _registerAccessManager(self, file_type, mgr_type, accessor_class):
        accessor = '%s.%s' % (file_type, mgr_type)
        self.AccessClasses[accessor] = accessor_class

    def _registerAccessManagers(self, file_type, reader, manager, builder):
        self.AccessClasses[file_type] = \
             { 'read':reader, 'manage':manager, 'build':builder }


