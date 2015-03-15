
GRID_DESCRIPTIONS = {
            'acis' : 'ACIS station data interpolated with NOAA high res grid input',
       'acishires' : 'ACIS station data interpolated with NOAA high res grid input',
       '    hires' : 'ACIS station data interpolated with NOAA high res grid input',
          'interp' : 'ACIS station data interpolated to 30 arc second grid',
    'interpolated' : 'ACIS station data interpolated to 30 arc second grid',
'nrccinterpolated' : 'ACIS station data interpolated to 30 arc second grid',
      'nrccinterp' : 'ACIS station data interpolated to 30 arc second grid',
       'nrcchires' : 'ACIS station data interpolated with NOAA high res grid input',
        'xrcmncep' : 'CRCM run using NCEP boundary conditions',
        'crcmccsm' : 'CRCM run using CCSM boundary conditions',
       'crcmcgcm3' : 'CRCM run using CGCM3 boundary conditions',
        'mmsincep' : 'CRCM run using NCEP boundary conditions',
        'mmsiccsm' : 'MMSI run using CCSM boundary conditions',
        'rcm3ncep' : 'RCM3 run using NCEP boundary conditions',
        'rcm3ccsm' : 'RCM3 run using CCSM boundary conditions',
        'rcm3gdfl' : 'RCM3 run using GDFL boundary conditions',
        'wrfgncep' : 'WRFG run using NCEP boundary conditions',
        'wrfgccsm' : 'WRFG run using CCSM boundary conditions',
       'wrfgcgcm3' : 'WRFG run using CGCM3 boundary conditions',
           'prism' : 'PRISM high reolution grid',
    }

GRID_NAME_MAP = {  'acis' : 'NRCC Hi-Res',
              'acishires' : 'NRCC Hi-Res',
                  'hires' : 'NRCC Hi-Res',
                 'interp' : 'NRCC Interpolated',
           'interpolated' : 'NRCC Interpolated',
              'nrcchires' : 'NRCC Hi-Res',
             'nrccinterp' : 'NRCC Interpolated',
       'nrccinterpolated' : 'NRCC Interpolated',
               'crcmncep' : 'CRCM + NCEP',
               'crcmccsm' : 'CRCM + CCSM',
              'crcmcgcm3' : 'CRCM + CGCM3',
               'mmsincep' : 'MM5I + NCEP',
               'mmsiccsm' : 'MM5I + CCSM',
               'rcm3ncep' : 'RCM3 + NCEP',
               'rcm3ccsm' : 'RCM3 + CCSM',
               'rcm3gdfl' : 'RCM3 + GDFL',
               'wrfgncep' : 'WRFG + NCEP',
               'wrfgccsm' : 'WRFG + CCSM',
              'wrfgcgcm3' : 'WRFG + CGCM3',
                  'prism' : 'PRISM',
                }

GRID_NUMBER_MAP = { 'interp' :  1,
                'nrccinterp' :  1,
              'interpolated' :  1,
          'nrccinterpolated' :  1,
                      'acis' :  2,
                 'acishires' :  2, 
                     'hires' :  2, 
                 'nrcchires' :  2,  
                  'crcmncep' :  4,
                  'crcmccsm' :  5, 
                 'crcmcgcm3' :  6,
                  'mmsincep' :  9, 
                  'mmsiccsm' :  10,
                  'rcm3ncep' :  11,
                  'rcm3ccsm' :  12,
                  'rcm3gdfl' :  13,
                  'wrfgncep' :  14,
                  'wrfgccsm' :  15, 
                 'wrfgcgcm3' :  16,
                     'prism' :  21,
                  }
GRID_KEYS = GRID_NUMBER_MAP.keys()
GRID_NUMBERS = GRID_NUMBER_MAP.values() 
GRID_KEY_MAP = dict(zip(GRID_NUMBERS,GRID_KEYS))

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def acisGridIdToKey(grid_id):
    print 'acisGridIdToKey', grid_id, type(grid_id)
    if isinstance(grid_id, int):
        if grid_id in GRID_NUMBERS: return GRID_KEY_MAP[grid_id]
    elif isinstance(grid_id, basestring):
        if grid_id.isdigit():
            grid_num = int(grid_id)
            if grid_num in GRID_NUMBERS: return GRID_KEY_MAP[grid_num]
            raise TypeError, '%s is not a valid grid number.' % grid_id
        else:
            grid_key = grid_id.lower().replace(' ','')
            grid_key = grid_key.replace('+','').replace('-','')
    else:
        ERRMSG = '%s is an unsupported type for "grid_id".'
        raise TypeError, ERRMSG % type(grid_id)
    if grid_key in GRID_KEYS: return grid_key

    ERRMSG = '"%s" is not recognized as a supported ACIS grid.'
    raise ValueError, ERRMSG % grid_id 

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def acisGridDescription(grid_id):
    return GRID_DESCRIPTIONS[acisGridIdToKey(grid_id)]

def acisGridName(grid_id):
    return GRID_NAME_MAP[acisGridIdToKey(grid_id)]

def acisGridNumber(grid_id):
    return GRID_NUMBER_MAP[acisGridIdToKey(grid_id)]

