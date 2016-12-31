
from atmosci.utils.timeutils import asAcisQueryDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# take advantage of the default seasonal project configuration
# this helps keep common things consistent between projects
# which, in turn, means we can re-use scripts from the 
# atmosci.seasonal package without making changes 
from atmosci.seasonal.config import CFGBASE
CONFIG = CFGBASE.copy('config', None)
del CFGBASE


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# directory paths
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.dirpaths.project = '/Volumes/data/app_data/shared/grid'
CONFIG.dirpaths.shared  = '/Volumes/data/app_data/shared'
CONFIG.dirpaths.static  = '/Volumes/data/app_data/shared/grid/static'
CONFIG.dirpaths.working = '/Volumes/data/app_data'
CONFIG.dev_dirpaths = {
       'project':'/Volumes/Transport/data/app_data/shared/grid',
       'shared':'/Volumes/Transport/data/app_data/shared',
       'static':'/Volumes/Transport/data/app_data/shared/grid/static',
       'working':'/Volumes/Transport/data/app_data',
       }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# GDD project configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.project.bbox = { 'NE':'-82.75,37.125,-66.7916,47.708',
                        'conus':'-125.00001,23.99999,-66.04165,49.95834',
                      }
CONFIG.project.compression = 'gzip'
CONFIG.project.end_day = (12,31)
CONFIG.project.forecast = 'ndfd'
CONFIG.project.forecast_days = 6
CONFIG.project.region = 'NE'
CONFIG.project.source = 'acis'
CONFIG.project.start_day = (1,1)
CONFIG.project.subdir_path = ('grid','%(region)s','%(source)s','temps')
CONFIG.project.subproject_by_region = True

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# GDD project file names and file types
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.filenames.source = '%(year)d-%(source)s-%(region)s-Daily.h5'
CONFIG.filenames.tempexts = '%(year)d-%(source)s-%(region)s-Daily.h5'

CONFIG.filetypes.tempexts = { 'scope':'year', 'period':'date', 
       'datasets':('lon','lat'), 'groups':('temps',),
       'description':'Temerature extremes downloaded from %(source)s',
       'start_day':(1,1), 'end_day':(12,31) }
# some old code uses 'source' as the file type
CONFIG.filetypes.tempexts.copy('source', CONFIG.filetypes)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# project data groups
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CONFIG.groups.temps = { 'description':'Daily temperatures',
        'datasets':('maxt','mint','provenance:tempexts') }
