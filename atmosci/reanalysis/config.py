
import os, sys

from atmosci.utils.config import ConfigObject

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.hourly.config import CONFIG as HOURLY_CONFIG
GRID_SUBDIR_PATH = \
    ('grid','%(region)s','%(analysis)s','%(num_hours)dhours','%(utc_date)s')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

CONFIG = HOURLY_CONFIG.copy()
del HOURLY_CONFIG

# add reanalysis as a source
CONFIG.sources.reanalysis = {
    'description':'NWS reanalysis model resampled to fit ACIS grid 3',
    'bbox':{ 'conus':CONFIG.regions.conus.data,
             'NE':CONFIG.regions.NE.data },
    'grid_dimensions':CONFIG.sources.acis.grid_dimensions,
    'node_spacing':CONFIG.sources.acis.node_spacing,
    'search_radius':CONFIG.sources.acis.search_radius,
    'subdir':GRID_SUBDIR_PATH,
    'tag':'reanalysis'
}

CONFIG.sources.reanalysis.project = {
    'grib_bbox':{'conus':'-125.25,23.749,-65.791,50.208',
                 'NE':'-83.125,36.75,-66.455,48.075'},
    'grib_bbox_offset':{'lat':0.375,'lon':0.375},
    'grib_dimensions':{'conus':{'lat':1377,'lon':2145},
                       'NE':{'lat':598,'lon':635}
                      },
    'grib_indexes':{'conus':{'x':(0,-1),'y':(0,-1)},
                    'NE':{'x':(1468,2104),'y':(641,1240)}
                   },
    'grib_subdir':('reanalysis','%(region)s','%(analysis)s','%(utc_date)s'),
    'grid_dimensions':CONFIG.sources.acis.grid_dimensions,
    'grid_subdir':GRID_SUBDIR_PATH,
    'lat_spacing':(0.0198,0.0228),
    'lon_spacing':(0.0238,0.0330),
    'resolution':'~2.5km',
    'search_radius':0.0413,
    'shared_grib_dir': True,
    'shared_grid_dir': True,
    'tag':'reanalysis'
}

# map the individual reanalysis data types to filename templates
# 'data' files shold contain multiple data types
CONFIG.sources.reanalysis.project.grid_file_map = {
    'data':'%(utc_time)s-%(num_hours)shour-Data.h5',
    'APCP':'%(utc_time)s-%(num_hours)shour-Accumulated-Precip.h5',
    'CEIL':'%(utc_time)s-%(num_hours)shour-Cloud-Ceiling.h5',
    'DPT':'%(utc_time)s-%(num_hours)shour-Dewpoint.h5',
    'GUST':'%(utc_time)s-%(num_hours)shour-Wind-Gust.h5',
    'HGT':'%(utc_time)s-%(num_hours)shour-Geopotential-Height.h5',
    'PCPN':'%(utc_time)s-%(num_hours)shour-Precipitation.h5',
    'PRES':'%(utc_time)s-%(num_hours)shour-Surface-Pressure.h5',
    'RHUM':'%(utc_time)s-%(num_hours)shour-Relative-Humidity.h5',
    'SPFH':'%(utc_time)s-%(num_hours)shour-Specific-Humidity.h5',
    'TCDC':'%(utc_time)s-%(num_hours)shour-Total-Cloud-Cover.h5',
    'TMP':'%(utc_time)s-%(num_hours)shour-Temperature.h5',
    'UGRD':'%(utc_time)s-%(num_hours)shour-U-Wind,h5',
    'VGRD':'%(utc_time)s-%(num_hours)shour-U-Wind,h5',
    'VIS':'%(utc_time)s-%(num_hours)shour-Visibility,h5',
    'WDIR':'%(utc_time)s-%(num_hours)shour-Wind-Direction,h5',
    'WIND':'%(utc_time)s-%(num_hours)shour-Wind-Speed,h5',
}

# datasets common to all reanalysis sources
CONFIG.datasets.timegrid.copy('APCP', CONFIG.datasets)
CONFIG.datasets.APCP.description = 'Accumulated precipitation'
CONFIG.datasets.APCP.timezone = 'UTC'
CONFIG.datasets.APCP.units = 'kg/m^2'
CONFIG.datasets.APCP.hours = 6
CONFIG.datasets.APCP.copy('CEIL', CONFIG.datasets)
CONFIG.datasets.CEIL.description = 'Cloud ceiling'
CONFIG.datasets.CEIL.units = 'm'
CONFIG.datasets.CEIL.hours = 1
CONFIG.datasets.CEIL.copy('DPT', CONFIG.datasets)
CONFIG.datasets.DPT.description = 'Dew point temperature'
CONFIG.datasets.DPT.units = 'K'
CONFIG.datasets.CEIL.copy('HGT', CONFIG.datasets)
CONFIG.datasets.HGT.description = 'Geopotential height @ surface'
CONFIG.datasets.HGT.units = 'gpm'
CONFIG.datasets.CEIL.copy('GUST', CONFIG.datasets)
CONFIG.datasets.GUST.description = 'Speed of wind gust'
CONFIG.datasets.GUST.units = 'm/s'
CONFIG.datasets.CEIL.copy('PCPN', CONFIG.datasets)
CONFIG.datasets.PCPN.description = 'Hourly precipitation'
CONFIG.datasets.PCPN.units = 'in'
CONFIG.datasets.CEIL.copy('PRES', CONFIG.datasets)
CONFIG.datasets.PRES.description = 'Surface pressure'
CONFIG.datasets.PRES.units = 'Pa'
CONFIG.datasets.CEIL.copy('RHUM', CONFIG.datasets)
CONFIG.datasets.RHUM.description = 'Relative humidity'
CONFIG.datasets.RHUM.units = '%'
CONFIG.datasets.CEIL.copy('SPFH', CONFIG.datasets)
CONFIG.datasets.SPFH.description = 'Specific humidity'
CONFIG.datasets.SPFH.units = 'kg/kg'
CONFIG.datasets.CEIL.copy('TCDC', CONFIG.datasets)
CONFIG.datasets.TCDC.description = 'Total cloud cover over entire atmosphere'
CONFIG.datasets.TCDC.units = '%'
CONFIG.datasets.DPT.copy('TMP', CONFIG.datasets)
CONFIG.datasets.TMP.description = '2 meter temperature'
CONFIG.datasets.GUST.copy('UGRD', CONFIG.datasets)
CONFIG.datasets.UGRD.description = 'U wind component @ 10 meters'
CONFIG.datasets.GUST.copy('VGRD', CONFIG.datasets)
CONFIG.datasets.VGRD.description = 'V wind component @ 10 meters'
CONFIG.datasets.CEIL.copy('VIS', CONFIG.datasets)
CONFIG.datasets.VIS.description = 'Visibility at surface'
CONFIG.datasets.VIS.units = 'm'
CONFIG.datasets.CEIL.copy('WDIR', CONFIG.datasets)
CONFIG.datasets.WDIR.description = 'Wind direction'
CONFIG.datasets.WDIR.units = 'degtrue'
CONFIG.datasets.GUST.copy('WIND', CONFIG.datasets)
CONFIG.datasets.WIND.description = 'Wind speed @ 10 meters'

# filetypes common to all reanalysis sources
CONFIG.filetypes.APCP = { 'scope':'hours',
       'datasets':('APCP','lon','lat','provenance:timestats'),
       'description':'Hourly precipition from reanalysis models'}
CONFIG.filetypes.CEIL = { 'scope':'hours',
       'datasets':('CEIL','lon','lat','provenance:timestamp'),
       'description':'Hourly cloud ceiling from reanalysis models'}
CONFIG.filetypes.DPT = { 'scope':'hours',
       'datasets':('DPT','lon','lat','provenance:timestats'),
       'description':'Hourly dew point temperature from reanalysis models'}
CONFIG.filetypes.HGT = { 'scope':'hours',
       'datasets':('HGT','lon','lat','provenance:timestats'),
       'description':'Hourly geopotential height from reanalysis models'}
CONFIG.filetypes.GUST = { 'scope':'hours',
       'datasets':('GUST','lon','lat','provenance:timestats'),
       'description':'Hourly wind gust from reanalysis models'}
CONFIG.filetypes.PCPN = { 'scope':'hours',
       'datasets':('PCPN','lon','lat','provenance:timestats'),
       'description':'Hourly precipition from reanalysis models'}
CONFIG.filetypes.PRES = { 'scope':'hours',
       'datasets':('PRES','lon','lat','provenance:timestats'),
       'description':'Hourly surface pressure from reanalysis models'}
CONFIG.filetypes.RHUM = { 'scope':'hours',
       'datasets':('RHUM','lon','lat','provenance:timestats'),
       'description':'Hourly relative humidity from reanalysis models'}
CONFIG.filetypes.SPFH = { 'scope':'hours',
       'datasets':('SPFH','lon','lat',' provenance:timestats'),
       'description':'Hourly specific humidity from reanalysis models'}
CONFIG.filetypes.TCDC = { 'scope':'hours',
       'datasets':('TCDC','lon','lat','provenance:timestamp'),
       'description':'Hourly total cloud cover from reanalysis models'}
CONFIG.filetypes.TMP = { 'scope':'hours',
       'datasets':('TMP','lon','lat','provenance:timestats'),
       'description':'Hourly temperature from reanalysis models'}
CONFIG.filetypes.UGRD = { 'scope':'hours',
       'datasets':('UGRD','lon','lat','provenance:timestamp'),
       'description':'Hourly U wind component from reanalysis models'}
CONFIG.filetypes.VGRD = { 'scope':'hours',
       'datasets':('VGRD','lon','lat','provenance:timestamp'),
       'description':'Hourly V wind component from reanalysis models'}
CONFIG.filetypes.VIS = { 'scope':'hours',
       'datasets':('VIS','lon','lat','provenance:timestats'),
       'description':'Hourly surface visibility from reanalysis models'}
CONFIG.filetypes.WDIR = { 'scope':'hours',
       'datasets':('WDIR','lon','lat','provenance:timestamp'),
       'description':'Hourly wind direction from reanalysis models'}
CONFIG.filetypes.WIND = { 'scope':'hours',
       'datasets':('WIND','lon','lat','provenance:timestats'),
       'description':'Hourly wind speed from reanalysis models'}

