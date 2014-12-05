
GRID_NAME_MAP = { 'NRCC Interp':1,  'NRCC Interpolated':1,
                  'NRCC Hi-Res':2,
                  'CRCM + NCEP':4,  'CRCM + CCSM':5,  'CRCM + CGCM3':6,
                  'MM5I + NCEP':9,  'MM5I + CCSM':10,
                  'RCM3 + NCEP':11, 'RCM3 + CCSM':12, 'RCM3 + GDFL':13,
                  'WRFG + NCEP':14, 'WRFG + CCSM':15, 'WRFG + CGCM3':16,
                  'PRISM':21,
                  'nrccinterp':1,   'interp':1,
                  'nrcchires':2,    'hires':2,
                  'acishires':2,    'acis':2,
                  'crcmncep':4,     'crcmccsm':5,     'crcmcgcm3':6,
                  'mmsincep':9,     'mmsiccsm':10,
                  'rcm3ncep':11,    'rcm3ccsm':12,    'rcm3gdfl':13,
                  'wrfgncep':14,    'wrfgccsm':15,    'wrfgcgcm3':16,
                  'prism':21,
                }
GRID_NAMES = tuple(GRID_NAME_MAP.keys())

GRID_NUM_MAP =  { 1:'NRCC Interpolated', 2:'NRCC Hi-Res',
                  4:'CRCM + NCEP',  5:'CRCM + CCSM',  6:'CRCM + CGCM3',
                  9:'MM5I + NCEP',  10:'MM5I + CCSM',
                  11:'RCM3 + NCEP', 12:'RCM3 + CCSM', 13:'RCM3 + GDFL',
                  14:'WRFG + NCEP', 15:'WRFG + CCSM', 16:'WRFG + CGCM3',
                  21:'PRISM',
                }
GRID_KEYS = tuple(GRID_NUM_MAP.values())
GRID_NUMBERS = tuple(GRID_NUM_MAP.keys())

GRID_DESCRIPTIONS = {
    'NRCC Interpolated':'ACIS station data interpolated to 30 arc second grid',
    'NRCC Hi-Res' :'ACIS station data interpolated with NOAA high res grid input',
    'CRCM + NCEP' :'CRCM run using NCEP boundary conditions',
    'CRCM + CCSM' :'CRCM run using CCSM boundary conditions',
    'CRCM + CGCM3':'CRCM run using CGCM3 boundary conditions',
    'MM5I + NCEP' :'CRCM run using NCEP boundary conditions',
    'MM5I + CCSM' :'MMSI run using CCSM boundary conditions',
    'RCM3 + NCEP' :'RCM3 run using NCEP boundary conditions',
    'RCM3 + CCSM' :'RCM3 run using CCSM boundary conditions',
    'RCM3 + GDFL' :'RCM3 run using GDFL boundary conditions',
    'WRFG + NCEP' :'WRFG run using NCEP boundary conditions',
    'WRFG + CCSM' :'WRFG run using CCSM boundary conditions',
    'WRFG + CGCM3':'WRFG run using CGCM3 boundary conditions',
    'PRISM':'PRISM high reolution grid',
    }

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def gridDescription(grid_id):
    return GRID_DESCRIPTIONS[gridIdToKey(grid_id)]

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def gridIdToKey(grid_id):
    if grid_id in GRID_KEYS: return grid_id
    else: return gridNameFromNumber(gridNumFromString(grid_id))

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def gridNameFromNumber(grid_num):
    if isinstance(grid_num, basestring):
        if grid_num.isdigits(): grid_num = int(grid_num)
    else:
        errmsg = '"%s" is an invalid grid number. String must contain ONLY digits.'
        raise ValueError, errmsg % grid_num

    grid_name = GRID_NUM_MAP.get(grid_num, None)
    if grid_name is not None: return grid_name
    raise IndexError, 'Invalid grid number : %d' % grid_num

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def gridNumFromString(_string):
    if _string.isdigits():
        grid_num = int(_string)
        if grid_num in GRID_NUMBERS: return grid_num
    elif _string in GRID_NAMES: return GRID_MAP[_string]
    else:
        map_name = _string.lower().replace(' ','').replace('-','')
        map_name = map_name.replace('+','').replace('_','')
        grid_num = GRID_MAP.get(map_name, None)
        if grid_num is not None: return grid_num

    raise KeyError, '"%s" does not match any ACIS grid type' % _string

