
import sys

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

ATMOSCFG = ConfigObject('atmosci', None)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# directory paths
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if 'win32' in sys.platform:
    ATMOSCFG.dirpaths = { 'data':'C:\\Work\\app_data',
                          'shared':'C:\\Work\\app_data\\shared',
                          'static':'C:\\Work\\app_data\\static',
                          'working':'C:\\Work' }
else:
    ATMOSCFG.dirpaths = { 'data':'/Volumes/data/app_data',
                          'shared':'/Volumes/data/app_data/shared',
                          'static':'/Volumes/data/app_data/static',
                          'working':'/Volumes/data' }
# set the following parameter to the location of temporary forecast files
ATMOSCFG.dirpaths.forecast = os.sep.join(ATMOSCFG.dirpaths.shared, 'forecast')
# set the following parameter to the location of temporary reanalysis files
ATMOSCFG.dirpaths.reanalysis = \
        os.sep.join(ATMOSCFG.dirpaths.shared, 'reanalysis')
# only set the following configuration parameter when multiple apps are
# using the same data source file - set it in each application's config
# file - NEVER set it in the default (global) config file.
# CONFIG.dirpaths.source = CONFIG.dirpaths.shared

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

CONFIG.modes = { 
'dev': {
    'dirpaths': {
        'forecast': '/Volumes/Transport/data/app_data/shared/forecast',
        'reanalysis': '/Volumes/Transport/data/app_data/shared/reanalysis',
        'shared':  '/Volumes/Transport/data/app_data/shared',
        'static':  '/Volumes/Transport/data/app_data/static',
        'working': '/Volumes/Transport/data/app_data'
        },
    },
}

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# regional coordinate bounding boxes for data and maps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ATMOSCFG.regions = {
         'conus': { 'description':'Continental United States',
                    'data':'-125.00001,23.99999,-66.04165,49.95834',
                    'maps':'-125.,24.,-66.25,50.' },
         'flny': { 'description':'NY Finger Lakes',
                   'data':'-78.0,42.0,-74.5,47.0',
                   'maps':'-77.9,41.9,-74.6,47.1' },
         'NE': { 'description':'NOAA Northeast Region (U.S.)',
                 'data':'-82.75,37.125,-66.83,47.708',
                 'maps':'-82.70,37.20,-66.90,47.60' },
}

