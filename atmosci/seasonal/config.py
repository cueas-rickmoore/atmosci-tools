
import os, sys
from collections import OrderedDict
import copy

import numpy as N
from scipy import stats as scipy_stats

from atmosci.utils.config import ConfigObject, OrderedConfigObject
from atmosci.utils.timeutils import asAcisQueryDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# ACIS grids built by NRCC are all the same shape
ACIS_GRID_DIMENSIONS = { 'conus':{'lat':624,'lon':1416},
                         'NE':{'lat':255,'lon':384} }
# 0.0416667 is lat/lon increment for ACIS DEM 5k node spacing 
ACIS_NODE_SPACING = 0.0416667
# grid diagonal = sqrt(2*0.0416667**2) = 0.05892604
# node search radius is 1/2 of diagonal = 0.2946302 + a litle fudge
ACIS_SEARCH_RADIUS = 0.03125

# PRISM has slightly smaller CONUS dimensions that ACIS
PRISM_GRID_DIMENSIONS = { 'conus':{'lat':621,'lon':1405},
                          'NE':{'lat':255,'lon':384} }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# specialize the ConfigObject slightly
class SeasonalConfig(ConfigObject):

    def getFiletype(self, filetype_key):
        if '.' in filetype_key:
           filetype, other_key = filetype_key.split('.')
           return self[filetype][other_key]
        else: return self.filetypes[filetype_key]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CFGBASE = SeasonalConfig('seasonal_config', None)


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# directory paths
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
if 'win32' in sys.platform:
    CFGBASE.dirpaths = { 'shared':'C:\\Work\\app_data\\shared',
                         'static':'C:\\Work\\app_data\\shared\\static',
                         'working':'C:\\Work\\app_data' }
else:
    CFGBASE.dirpaths = { 'shared':'/Volumes/data/app_data/shared',
                         'static':'/Volumes/data/app_data/shared/static',
                         'working':'/Volumes/data/app_data' }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# regional coordinate bounding boxes for data and maps
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('regions', CFGBASE)
CFGBASE.regions.conus = { 'description':'Continental United States',
                          'data':'-125.00001,23.99999,-66.04165,49.95834',
                          'maps':'-125.,24.,-66.25,50.' }
CFGBASE.regions.NE = { 'description':'NOAA Northeast Region (U.S.)',
                       'data':'-82.75,37.125,-66.83,47.70',
                       'maps':'-82.70,37.20,-66.90,47.60' }

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# default project configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('project', CFGBASE)
CFGBASE.project.compression = 'gzip'
CFGBASE.project.end_day = (12,31)
CFGBASE.project.forecast = 'ndfd'
CFGBASE.project.region = 'conus'
CFGBASE.project.root = 'shared'
CFGBASE.project.source = 'acis'
CFGBASE.project.shared_forecast = True
CFGBASE.project.shared_source = True
CFGBASE.project.start_day = (1,1)
CFGBASE.project.subproject_by_region = True


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# dataset view mapping
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CFGBASE.view_map = { ('time','lat','lon'):'tyx', ('lat','lon','time'):'yxt',
                     ('time','lon','lat'):'txy', ('lon','lat','time'):'xyt',
                     ('lat','lon'):'yx', ('lon','lat'):'xy',
                     ('lat','time'):'yt', ('time',):'t',
                   }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# dataset configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('datasets', CFGBASE)

# generic time series datasets
CFGBASE.datasets.dateaccum = { 'dtype':float, 'dtype_packed':'<i2',
                              'missing_packed':-32768, 'missing_data':N.nan,
                              'scope':'season', 'period':'date',
                              'view':('time','lat','lon'),
                              'start_day':(1,1), 'end_day':(12,31),
                              'provenance':'dateaccum' }

CFGBASE.datasets.doyaccum = { 'dtype':float, 'dtype_packed':'<i2',
                             'missing_packed':-32768, 'missing_data':N.nan,
                             'scope':'season', 'period':'doy',
                             'view':('time','lat','lon'),
                             'start_day':(1,1), 'end_day':(12,31),
                             'provenance':'doyaccum' }

CFGBASE.datasets.dategrid = { 'dtype':float, 'dtype_packed':'<i2',
                             'missing_packed':-32768, 'missing_data':N.nan,
                             'scope':'season', 'period':'date',
                             'view':('time','lat','lon'),
                             'start_day':(1,1), 'end_day':(12,31),
                             'provenance':'datestats' }

CFGBASE.datasets.doygrid = { 'dtype':float, 'dtype_packed':'<i2',
                            'missing_packed':-32768, 'missing_data':N.nan,
                            'scope':'season', 'period':'doy',
                            'view':('time','lat','lon'),
                            'start_day':(1,1), 'end_day':(12,31),
                            'provenance':'doystats' }

# temperature datasets
CFGBASE.datasets.maxt = CFGBASE.datasets.dategrid.copy()
CFGBASE.datasets.maxt.description = 'Daily maximum temperature' 
CFGBASE.datasets.maxt.scope = 'year'
CFGBASE.datasets.maxt.units = 'F'

CFGBASE.datasets.mint = CFGBASE.datasets.dategrid.copy()
CFGBASE.datasets.mint.description = 'Daily minimum temperature' 
CFGBASE.datasets.maxt.scope = 'year'
CFGBASE.datasets.mint.units = 'F'

# location datasets
CFGBASE.datasets.elev = { 'dtype':float, 'dtype_packed':'<i2', 'units':'meters',
                         'missing_packed':-32768, 'missing_data':N.nan,
                         'view':('lat','lon'),
                         'description':'Elevation' }
CFGBASE.datasets.lat = { 'dtype':float, 'dtype_packed':float, 'units':'degrees',
                        'missing_packed':N.nan, 'missing_data':N.nan,
                        'view':('lat','lon'),
                        'description':'Latitude' }
CFGBASE.datasets.lon = { 'dtype':float, 'dtype_packed':float, 'units':'degrees',
                        'missing_packed':N.nan, 'missing_data':N.nan,
                        'view':('lat','lon'),
                        'description':'Longitude' }

# mask datasets
CFGBASE.datasets.land_mask = { 'dtype':bool, 'dtype_packed':bool,
                              'view':('lat','lon'),
                              'description':'Land Mask (Land=True, Water=False)'
                             }
CFGBASE.datasets.interp_mask = { 'dtype':bool, 'dtype_packed':bool,
                                'view':('lat','lon'),
                                'description':'Interpolation Mask (Use=True)' }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# directory paths
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('dirpaths', CFGBASE)
# 
if 'win32' in sys.platform:
    CFGBASE.dirpaths.working = 'C:\\Work\\app_data'
else:
    CFGBASE.dirpaths.working = '/Volumes/data/app_data'
    #
    # set the following parameter to the location of temporary forecast files
    CFGBASE.dirpaths.forecast = '/Volumes/data/app_data/shared/forecast'
    # only set the following configuration parameter when multiple apps are
    # using the same data source file - set it in each application's config
    # file - NEVER set it in the default (global) config file.
    # CONFIG.dirpaths.source = '/Volumes/data/app_data/shared'
    #
    # set the following parameter when multiple projects share static data
    # files - it is OK to set this in the global config file
    CFGBASE.dirpaths.static = '/Volumes/data/app_data/static'


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# filename templates
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('filenames', CFGBASE)
CFGBASE.filenames.project = '%(year)d-%(project)s-%(source)s-%(region)s.h5'
CFGBASE.filenames.source = '%(year)d-%(source)s-%(region)s-Daily.h5'
CFGBASE.filenames.static = '%(type)s_%(region)s_static.h5'
CFGBASE.filenames.temps = '%(year)d-%(source)s-%(region)s-Daily.h5'
CFGBASE.filenames.variety = '%(year)d-%(project)-%(source)s-%(variety)s.h5'


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# filetypes
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('filetypes', CFGBASE)

CFGBASE.filetypes.source = { 'scope':'year',
                  'groups':('tempexts',), 'datasets':('lon','lat'), 
                  'description':'Data downloaded from %(source)s' }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# data group configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('groups', CFGBASE)

# groups of observed data
CFGBASE.groups.tempexts = { 'path':'temps', 'description':'Daily temperatures',
                            'datasets':('maxt','mint','provenance:tempexts') }
CFGBASE.groups.maxt = { 'description':'Maximum daily temperature',
                        'datasets':('daily:maxt','provenance:observed') }
CFGBASE.groups.mint = { 'description':'Minimum daily temperature',
                        'datasets':('daily:mint','provenance:observed') }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# provenance dataset configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
PROVENANCE = ConfigObject('provenance', CFGBASE, 'generators', 'types', 'views')

# provenance time series views
CFGBASE.provenance.views.date = ('date','obs_date')
CFGBASE.provenance.views.doy = ('day','doy')

# configure provenance type defintions
# statistics for time series data with accumulation
accum = { 'empty':('',N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,''),
          'formats':['|S10','f4','f4','f4','f4','f4','f4','f4','f4','|S20'],
          'names':['time','min','max','mean','median', 'min accum','max accum',
                   'mean accum','median accum','processed'],
          'type':'cumstats' }
# date series - data with accumulation
CFGBASE.provenance.types.dateaccum = copy.deepcopy(accum)
CFGBASE.provenance.types.dateaccum.names[0] = 'date'
CFGBASE.provenance.types.dateaccum.period = 'date'
# day of year series - data with accumulation
CFGBASE.provenance.types.doyaccum = copy.deepcopy(accum)
CFGBASE.provenance.types.doyaccum.formats[0] = '<i2'
CFGBASE.provenance.types.doyaccum.names[0] = 'doy'
CFGBASE.provenance.types.doyaccum.period = 'doy'

# provenance for time series statistics only
stats = { 'empty':('',N.nan,N.nan,N.nan,N.nan,''),
          'formats':['|S10','f4','f4','f4','f4','|S20'],
          'names':['time','min','max','mean','median','processed'],
          'type':'stats' }
# date series stats
CFGBASE.provenance.types.datestats = copy.deepcopy(stats)
CFGBASE.provenance.types.datestats.names[0] = 'date'
CFGBASE.provenance.types.datestats.period = 'date'
# day of year series stats
CFGBASE.provenance.types.doystats = copy.deepcopy(stats) 
CFGBASE.provenance.types.doystats.formats[0] = '<i2'
CFGBASE.provenance.types.doystats.names[0] = 'doy'
CFGBASE.provenance.types.doystats.period = 'doy'

# time series observations
observed = { 'empty':('',N.nan,N.nan,N.nan,N.nan,''),
             'formats':['|S10','f4','f4','f4','f4','|S20'],
             'names':['time','min','max','avg','median','dowmload'],
             'type':'stats' }
CFGBASE.provenance.types.observed = copy.deepcopy(observed)
CFGBASE.provenance.types.observed.names[0] = 'date'
CFGBASE.provenance.types.observed.period = 'date'

# temperature extremes group provenance
CFGBASE.provenance.types.tempexts = \
        { 'empty':('',N.nan,N.nan,N.nan,N.nan,N.nan,N.nan,'',''),
          'formats':['|S10','f4','f4','f4','f4','f4','f4','|S20','|S20'],
          'names':['date','min mint','max mint','avg mint','min maxt',
                   'max maxt','avg maxt','source','processed'],
          'period':'date', 'scope':'year', 'type':'tempexts' }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# data sources
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('sources', CFGBASE)

CFGBASE.sources.acis = { 'acis_grid':3, 'days_behind':0,
                'earliest_available_time':(10,30,0),
                'subdir':'acis_hires', 'tag':'ACIS-HiRes',
                'description':'ACIS HiRes grid 3',
                'bbox':{'NE':'-82.75,37.125,-66.83,47.70',
                        'conus':'-125.00001,23.99999,-66.04165,49.95834'},
                'grid_dimensions':ACIS_GRID_DIMENSIONS,
                'node_spacing':ACIS_NODE_SPACING,
                'search_radius':ACIS_SEARCH_RADIUS }

CFGBASE.sources.ndfd = { 'days_behind':0, 'tag':'NDFD',
                'description':'National Digital Forecast Database',
                'grid_dimensions':{'conus':{'lat':1377,'lon':2145},
                                   'NE':{'lat':598,'lon':635}},
                'bbox':{'conus':'-125.25,23.749,-65.791,50.208',
                        'NE':'-83.125,36.75,-66.455,48.075'},
                'bbox_offset':{'lat':0.375,'lon':0.375},
                'indexes':{'conus':{'x':(0,-1),'y':(0,-1)},
                           'NE':{'x':(1468,2104),'y':(641,1240)}},
                'cache_server':'http://ndfd.eas.cornell.edu/',
                'download_template':'%(timespan)s-%(variable)s.grib',
                'node_spacing':0.0248, 'resolution':'~2.5km',
                'lat_spacing':(0.0198,0.0228),
                'lon_spacing':(0.0238,0.0330),
                'search_radius':0.0413,
                }

CFGBASE.sources.prism = { 'acis_grid':21, 'days_behind':1,
                'earliest_available_time':(10,30,0), 'tag':'PRISM',
                'description':'PRISM Climate Data (ACIS grid 21)',
                'bbox':{'NE':'-82.75,37.125,-66.7916,47.708',
                        'conus':'-125.00001,23.99999,-66.04165,49.95834'},
                'grid_dimensions':PRISM_GRID_DIMENSIONS,
                'node_spacing':ACIS_NODE_SPACING,
                'search_radius':ACIS_SEARCH_RADIUS }


# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# static grid file configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('static', CFGBASE)

CFGBASE.static.acis = { 'type':'acis5k', 'tag':'ACIS',
              'description':'Static datasets for ACIS HiRes',
              'datasets':('lat', 'lon', 'elev'),
              'masks':('land_mask:cus_mask', 'interp_mask:cus_interp_mask'),
              'masksource':'dem5k_conus_static.h5', 'filetype':'static',
              'template':'acis5k_%(region)s_static.h5',
              }

CFGBASE.static.prism = { 'type':'prism5k', 'tag':'PRISM',
              'description':'Static datasets for PRISM model',
              'datasets':('lat', 'lon', 'elev'),
              'masks':('land_mask:cus_mask', 'interp_mask:cus_interp_mask'),
              'masksource':'dem5k_conus_static.h5', 'filetype':'static',
              'template':'prism5k_%(region)s_static.h5'
              }

