
from dateutil.relativedelta import relativedelta

import numpy as N

from atmosci.utils.timeutils import asDatetime
from atmosci.utils.units import convertUnits

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def vaporPressureFromTemp(temp, temp_units, debug=False):
    # need temperature in degrees Kelvin
    k_temp = convertUnits(temp, temp_units, 'K')
    # calculate saturation vapor pressure (sat_vp)
    vp = 6.11 * N.exp( 5420. * ( (k_temp - 273.15) / (273.15 * k_temp) ) )
    if debug: print 'vaporPressureFromTemp', vp, k_temp, temp
    return vp

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def dewpointFromHumidityAndTemp(relative_humidity, temp, temp_units,
                                debug=False):
    # saturation vapor pressure (sat_vp)
    sat_vp = vaporPressureFromTemp(temp, temp_units, debug)
    if debug:
        print 'dewpointFromHumidityAndTemp', relative_humidity, temp, temp_units
        print '    saturation vapor pressure', sat_vp
    # actual vapor pressure (vp)
    if isinstance(relative_humidity, N.ndarray):
        relative_humidity[N.where(relative_humidity==0)] = N.nan
        vp = (relative_humidity * sat_vp) / 100.
    else:
        if relative_humidity == 0: vp = N.nan
        else: vp = (relative_humidity * sat_vp) / 100.
    if debug: print '    actual vapor pressure', vp
    # dewpoint temperature in degrees Kelvin
    k_dew_point = 1. / ( (1./273.15) - (N.log(vp/6.11) / 5420.) )
    # convert back to units of input temperature
    dew_point = convertUnits(k_dew_point, 'K', temp_units)
    if debug: print '    dew_point', k_dew_point, dew_point
    return dew_point

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def dewpointDepression(relative_humidity, temp, temp_units):
    return temp - dewpointFromHumidityAndTemp(relative_humidity,temp,temp_units)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def relativeHumidityFromdDewpointAndTemp(dew_point, temp, temp_units):
    # saturation vapor pressure (sat_vp)
    sat_vp = vaporPressureFromTemp(temp, temp_units)
    # dewpoint (actual) vapor pressure (vp)
    vp = vaporPressureFromTemp(dew_point, temp_units)
    # relative humidity
    return (vp / sat_vp)*100

