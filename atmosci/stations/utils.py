
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from nrcc.stations.client import ALL_PRECIP_ELEMENTS, ALL_TEMP_ELEMENTS
from nrcc.stations.client import ALL_NON_NUMERIC_ELEMS


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

INDEXABLE_ELEMENT_IDS = { 1:'maxt',2:'mint',4:'pcpn',
                          '1':'maxt','2':'mint','4':'pcpn'
                        }

def elementID(element):
    if isinstance(element,  basestring):
        if element.isdigit():
            return int(element)
        else:
            return element
    elif type(element) == int:
        return element
    elif isinstance(element,  dict):
        if 'vX' in element:
            return int(element['vX'])
        else:
            return element['name']

def indexableElementID(element):
    if isinstance(element,  basestring):
        if element.isdigit():
            return INDEXABLE_ELEMENT_IDS(element,'vX_%s' % element)
        else:
            return element
    elif type(element) == int:
        return INDEXABLE_ELEMENT_IDS(element,'vX_%d' % element)
    elif isinstance(element,  dict):
        if 'vX' in element:
            return INDEXABLE_ELEMENT_IDS(element['vX'],'vX_%d' % element['vX'])
        else:
            return element['name']

    errmsg = 'Invalid element identification, %s is an unsupported type'
    raise ValueError, errmsg % type(element)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

POSTAL_NCDC_MAP = { 'AL':'01','AK':'50','AZ':'02','AR':'03',
                    'CA':'04','CO':'05','CT':'06',
                    'DE':'07','FL':'08','GA':'09','HI':'51',
                    'ID':'10','IL':'11','IN':'12', 'IA':'13',
                    'KS':'14','KY':'15','LA':'16',
                    'ME':'17','MD':'18', 'MA':'19','MI':'20',
                    'MN':'21','MS':'22','MO':'23','MT':'24',
                    'NE':'25','NV':'26','NH':'27','NJ':'28',
                    'NM':'29','NY':'30', 'NC':'31','ND':'32',
                    'OH':'33','OK':'34','OR':'35',
                    'PA':'36', 'PR':'66','PI':'91',
                    'RI':'37','SC':'38','SD':'39',
                    'TN':'40','TZ':'41','UT':'42',
                    'VT':'43','VA':'44', 'VI':'67',
                    'WA':'45','WV':'46','WI':'47','WY':'48' }

NCDC_POSTAL_MAP = { }
for postal, ncdc in POSTAL_NCDC_MAP.items():
    NCDC_POSTAL_MAP[ncdc] = postal

def postal2ncdc(postal):
    return POSTAL_NCDC_MAP.get(postal.upper(),None)

def ncdc2postal(nrcc):
    return NCDC_POSTAL_MAP.get(str(nrcc), None)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def isMorningStation(state, station_dict):
    return True

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def stationInBBox(lon,lat,bbox):
    if lon < bbox[0]: return False
    if lon > bbox[2]: return False
    if lat < bbox[1]: return False
    if lat > bbox[3]: return False
    return True

