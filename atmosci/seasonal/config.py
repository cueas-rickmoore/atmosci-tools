
import os, sys
from collections import OrderedDict
import copy

import numpy as N
from scipy import stats as scipy_stats

from atmosci.utils.config import ConfigObject, OrderedConfigObject
from atmosci.utils.timeutils import asAcisQueryDate

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

# ACIS grids built by NRCC all have the same attributes
from atmosci.acis.gridinfo import ACIS_GRID_DIMENSIONS, ACIS_NODE_SPACING, \
                                  ACIS_SEARCH_RADIUS, PRISM_GRID_DIMENSIONS

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
from atmosci.config import ATMOSCFG
# import any default directory paths
ATMOSCFG.dirpaths.copy('dirpaths', CFGBASE)
# inport regional coordinate bounding boxes
ATMOSCFG.regions.copy('regions', CFGBASE)
# import mode-dependent defaults
ATMOSCFG.modes.copy('modes', CFGBASE)
del ATMOSCFG

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# default project configuration
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
ConfigObject('project', CFGBASE)
CFGBASE.project.bbox = { 'NE':CFGBASE.regions.NE.data,
                         'conus':CFGBASE.regions.conus.data }
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
# dataset parameter definitions
#
#    description = brief description of data contained in dataset (string)
#
#    dtype = type for raw data when added to file
#            also used as type for extracted data
#    dtype_packed = type used when data is store in the file
#
#    missing_data = missing value in raw data when added to file
#                   also used as missing value for extracted data
#    missing_packed = value used for missing when stored in the file
#
#    units = units for values in raw data
#    packed_units = units for values in stored data
#                   if not specified, input units are used
#               
#    period = period of time covered by a single entry in the dataset
#             date = one calendar day per entry
#             doy = one day of an ideal year (0-365 or 0-366)
#                   used to map historical summary data to specific dates
#             year = one calendar year per entry
#
#    scope = time covered by entire dataset
#            year = a single year
#            season = dataset spansparts of two or more years
#            por = dataset spans multiple years
#
#    view = layout of the dataset
#           lat = latitude dimension
#           lon = longitude dimension
#           time dimensions :
#               date = dimension is span of dates 
#               doy = dimension is span of normalized days
#               year = dimension is years 
#               time = time in days, hour, minutes, seconds
#        example : 'view':('day','lat','lon')
#
#    time span parameters :
#        for date dimension :
#            start_day = first day in dataset ... as int tuple (MM,DD)
#            end_day = last day in dataset ... as int tuple (MM,DD)
#        for doy dimension :
#            start_doy = first doy in dataset ... as int tuple (MM,DD)
#            end_doy = last doy in dataset ... as int tuple (MM,DD)
#        for year dimension :  
#            start_year = first year in dataset ... as int
#            end_year = last year in dataset ... as int
#
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
# dataset view mappings
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
CFGBASE.view_map = { ('date','lat','lon'):'tyx', ('lat','lon','date'):'yxt',
                     ('date','lon','lat'):'txy', ('lon','lat','date'):'xyt',
                     ('doy','lat','lon'):'tyx', ('doy','lon','time'):'yxt',
                     ('doy','lon','lat'):'txy', ('doy','lat','time'):'xyt',
                     ('time','lat','lon'):'tyx', ('lat','lon','time'):'yxt',
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
                              'provenance':'datestats', 
                              'chunk_type':('date','gzip') }

CFGBASE.datasets.doygrid = { 'dtype':float, 'dtype_packed':'<i2',
                             'missing_packed':-32768, 'missing_data':N.nan,
                             'scope':'season', 'period':'doy',
                             'view':('time','lat','lon'),
                             'start_day':(1,1), 'end_day':(12,31),
                             'provenance':'doystats',
                             'chunk_type':('doy','gzip') }

# temperature datasets
CFGBASE.datasets.dategrid.copy('maxt', CFGBASE.datasets)
CFGBASE.datasets.maxt.description = 'Daily maximum temperature' 
CFGBASE.datasets.maxt.scope = 'year'
CFGBASE.datasets.maxt.units = 'F'

CFGBASE.datasets.dategrid.copy('mint', CFGBASE.datasets)
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

CFGBASE.sources.ndfd.copy('rtma', CFGBASE.sources)
CFGBASE.sources.rtma.tag = 'RTMA'
CFGBASE.sources.rtma.description = 'Real-Time Mesoscale Analysis'
del CFGBASE.sources.rtma['cache_server']
del CFGBASE.sources.rtma['download_template']

CFGBASE.sources.rtma.copy('urma', CFGBASE.sources)
CFGBASE.sources.urma.tag = 'URMA'
CFGBASE.sources.urma.description = 'Unrestricted Mesoscale Analysis'


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

