
import math
import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def handleSequence(values):
    """ handle list, tuple and numpy arrays correctly
    returns:
        list_in : boolean : input was a list
        tuple_in : boolean : input was a tuple
        array : numpy array or None
    """
    if isinstance(values, N.ndarray):
        return False, False, values
    if isinstance(values, list):
        return True, False, N.array(values, dtype=float)
    elif isinstance(values, tuple):
        return False, True,  N.array(values, dtype=float)
    else return False, False, None
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def mixingRatio(pressure, temp, dewpt):
    """ calculate mixing ratio
    arguments:
        pressure in millibars (hectopascals)
        temperature in degrees Kelvin
        dew point in degrees Kelvin
    """
    e = (0.0000000000253) * N.exp((-5420. / dewpt)
    e_pressure = e / 100.
    return ((0.622 * e_pressure) / (pressure - e_pressure)) * 1000.

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def heatIndex(temp_in, rhum_in):
    """ calculate heat index using formulas laid out on NOAA web page
    http://www.hpc.ncep.noaa.gov/html/heatindex_equation.shtml

    arguments:
        temperature in degrees Fahrenheit
        humidity in (as a decimal number 0 to 100)
    """
    list_in, tuple_in, temp = handleSequence(temp_in)
    # sequence was input
    if temp is not None:
        if isinstance(rhum_in, (list, tuple, N.ndarray)):
            rhum = N.array(rhum_in, dtype=float)
        else: rhum = N.array([rhum_in for n in range(len(_temp))], dtype=float)
        # only temps above 80 F may have an associated Heat Index
        indexes = N.where(temp >= 80.)
        if len(indexes) > 0 and len(indexes[0]) > 0:
            heat = N.array(temp)
            rhum_80 = rhum[indexes]
            rhum_sq = rhum_80 * rhum_80
            temp_80 = temp[indexes]
            temp_sq = temp_80 * temp_80
            heat[indexes] = ( -42.379 
                + (2.04901523 * temp_80) + (10.14333127 * rhum_80)
                + (-0.22475541 * temp_80 * rhum_80) + (-6.83783e-03 * temp_sq)
                + (-5.481717e-02 * rhum_sq) + (1.22874e-03 * temp_sq * rhum_80)
                + (8.5282e-04 * temp_80 * rhum_sq)
                + (-1.99e-06 * temp_sq * rhum_sq) )
            lh_indexes = N.where(rhum < 13. & temp >= 80. & temp <= 112.)
            if len(lh_indexes) > 0 and len(lh_indexes[0]) > 0:
                heat[lh_indexes] -= ( ((13. - rhum[lh_indexes]) / 4.)
                    * N.sqrt((17. - N.absolute(temp[lh_indexes] - 95.)) / 17.) )
            hh_indexes = N.where(rhum > 85. & temp >= 80. & temp <= 87.)
            if len(hh_indexes) > 0 and len(hh_indexes[0]) > 0:
                heat[hh_indexes] += ( ((rhum[hh_indexes] - 85.) / 10.)
                    * ((87. - temp[hh_indexes]) / 5.) )

            if list_in: return list(heat)
            elif tuple_in: return tuple(heat)
            else: return heat

        # all temps are below 80 F
        else: return N.array(temp)

    # assume we got a single value
    if (temp_in < 80): return temp_in
    # only temps above 80 F may have an associated Heat Index
    rhum_sq = rhum_in * rhum_in
    temp_sq = temp_in * temp_in
    heat = ( -42.379 + (2.04901523 * temp_in) + (10.14333127 * rhum_in)
           + (-0.22475541 * temp_in * rhum_in) + (-6.83783e-03 * temp_sq)
           + (-5.481717e-02 * rhum_sq) + (1.22874e-03 * temp_sq * rhum_in)
           + (8.5282e-04 * temp_in * rhum_sq)
           + (-1.99e-06 * temp_sq * rhum_sq) )
    if rhum_in < 13. and temp_in >= 80. and temp_in <= 112.:
        heat -= ( ((13. - rhum_in) / 4.)
                * math.sqrt((17. - abs(temp_in-95.)) / 17.) )
    elif rhum_in > 85. and temp_in >= 80. and temp_in <= 87.:
        heat += ( ((rhum_in - 85.) / 10.) * ((87. - temp_in) / 5.) )
    return heat

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def potentialTemp(temp_in, pressure_in):
    """ calculate theta (potential temperature)
    arguments:
        pressure in millibars (hectopascals)
        temperature in degrees Kelvin
    """
    list_in, tuple_in, temp = handleSequence(temp_in)
    if temp is not None:
        dl, dt, pressure = handleSequence(pressure_in)
        theta = temp * N.power((1000./pressure), 0.286 )

        if list_in: return list(theta)
        elif tuple_in: return tuple(theta)
        else: return theta

    return temp_in * math.pow((1000./pressure_in), 0.286 )

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
  
def equivPotentialTemp(temp_in, pressure_in, dewpt_in):
    """ calculate theta e (equivalent potential temperature)
    arguments:
        pressure in millibars (hectopascals)
        temperature in degrees Kelvin
        dew point in degrees Kelvin
    """
    list_in, tuple_in, temp = handleSequence(temp_in)

    list_in, tuple_in, temp = handleSequence(temp_in)
    if temp is not None:
        l, t, pressure = handleSequence(pressure_in)
        l, t, dewpt = handleSequence(dewpt_in)
        theta = temp * N.power((1000./pressure), 0.286 )
        mix_ratio = mixingRatio(pressure, temp, dewpt) / 1000.
        equiv = theta * N.exp( (0.00000250 * mix_ratio) / (1005. * temp) )

        if list_in: return list(equiv)
        elif tuple_in: return tuple(equiv)
        else: return equiv

    theta = temp_in * math.pow((1000./pressure_in), 0.286)
    mix_ratio = mixingRatio(pressure_in, temp_in, dewpt_in) / 1000.
    return theta * math.exp( (0.00000250 * mix_ratio) / (1005. * temp_in) )
