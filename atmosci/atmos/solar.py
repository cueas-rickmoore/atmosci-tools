
import datetime
import math
import numpy as N

from atmosci.utils.time import asDatetime

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

PI = math.pi
TWO_PI = PI * 2
DEG_PER_RAD = 180. / PI # degrees per RAD
RAD_PER_DEG = PI / 180. # RADs per degree

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

UNIT_CONVERTERS = { 'W/m2_BTU/ft2' : lambda x: x * 0.316,
                    'W/m2_langley' : lambda x: x * 0.0861,
                    'W/m2_MJ/m2' : lambda x: x * 0.0036,
                    'W/m2_W/m2' : lambda x: x,
                   }

def convertUnits(data, to_units, from_units='W/m2'):
    if to_units is not None:
        convert = UNIT_CONVERTERS.get('%s_%s' % (from_units,to_units), None)
        if convert is not None: return convert(data)
    return data

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class Solar(object):

    def __init__(self, longitude, latitude, utc_time_zone):
        self.longitude = longitude
        self.latitude = latitude
        self.setDate(datetime.datetime.now())
        self.utc_time_zone = utc_time_zone
        self.utc_offset = -utc_time_zone

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def hourlySolarRadiation(self, date, interval=6, units='langley'):
        # Return top of atmosphere solar radiation for each hour of the day.
        days_since_1980 = float(self.days_since_1980)
        time_offset = self.time_offset
        decimal_interval = float(interval) / 60.
        decimal_intervals = [(indx * decimal_interval) + decimal_interval
                             for indx in range(int(1./decimal_interval))]
        hourly_radiation = [ ]

        indx = 0
        for hour in range(24):
            radiation = 0.
            for intvl in decimal_intervals:
                decimal_hour = hour + intvl
                elapsed_time = days_since_1980 + (decimal_hour/24.0) +\
                               time_offset
                sl, ra, d, (Z, cos_Z) = self.positionOfSun(elapsed_time,
                                                           decimal_hour)
                radiation += self.solarRadiationAtTop(decimal_interval, cos_Z)
                indx += 1
            hourly_radiation.append(radiation)

        hourly_radiation = N.array(hourly_radiation, dtype=float)
        if units is not None: return convertUnits(hourly_radiation, units)
        else: return hourly_radiation

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def totalRadiationForHour(self, date_and_hour, interval=6, units='langley'):
        # Return top of atmosphere solar radiation for one hour.
        date_time = self.setDate(date_and_hour)
        hour = date_time.hour
        days_since_1980 = float(self.days_since_1980)
        time_offset = self.time_offset
        decimal_interval = float(interval) / 60.
        decimal_intervals = [(indx * decimal_interval) + decimal_interval
                             for indx in range(int(1./decimal_interval))]

        radiation = 0.
        for intvl in decimal_intervals:
            decimal_hour = hour + intvl
            elapsed_time = days_since_1980 + (decimal_hour/24.0) +\
                           time_offset
            sl, ra, d, (Z, cos_Z) = self.positionOfSun(elapsed_time,
                                                       decimal_hour)
            radiation += self.solarRadiationAtTop(decimal_interval, cos_Z)

        if units is not None: return convertUnits(radiation, units)
        else: return radiation

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def positionOfSun(self, elapsed_time, decimal_hour):
        """ calculate position of the sun on the celestial sphere

            Returns: sun_lon - longitude of Sun on Celestial Sphere
                     right_ascension - angle b/w hour circle of the Vernal
                               Equinox and the hour circle of the Sun 
                     declination - angular distance from the Sun to the
                                Celestial Equator
                     (zenith, cos_Z) - point on Celestial Sphere directly
                                overhead for observer on Earth
        """
        sid_time, local_sid_time = self.siderialTime(elapsed_time,decimal_hour)
        # equations for dterming solar angular location are based on :
        #    Walraven, 1978, "Calculating the position of the sun",
        #    Solar Energy, 20, 193

        # find longitude of the sun
        theta = TWO_PI * elapsed_time / 365.25
        # mean anomaly of the earth
        g = -0.031271 - (elapsed_time * 4.53963e-07) + theta
        # longitude of the sun
        sun_lon = 4.900968 + (elapsed_time * 3.67474e-07) +\
                  (math.sin(g) * (0.033434 - 2.3e-09 * elapsed_time)) + \
                  (math.sin(2. * g) * 0.000349) + theta

        # angle between ecliptic and the plane of the celestial equator
        ecliptic_angle = 23.440 - (elapsed_time * 3.56e-07)

        # calculate right ascension of the sun
        X = math.cos(ecliptic_angle * RAD_PER_DEG) * math.sin(sun_lon)
        Y = math.cos(sun_lon)
        right_ascension = math.atan2(X,Y)
        if right_ascension < 0.0: right_ascension += TWO_PI

        sin_declination = math.sin(ecliptic_angle * RAD_PER_DEG) *\
                          math.sin(sun_lon)
        declination = math.asin(sin_declination)

        # calculate Zenith distance
        lat_in_rads = self.latitude * RAD_PER_DEG
        hour_angle = right_ascension - local_sid_time
        cos_Z = (math.sin(lat_in_rads) * sin_declination) + \
                ( math.cos(lat_in_rads) * math.cos(declination) *
                  math.cos(hour_angle) )
        zenith = math.acos(cos_Z) * DEG_PER_RAD

        return sun_lon, right_ascension, declination, (zenith, cos_Z)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def setDate(self, date):
        date_time = asDatetime(date)

        self.year = year = date_time.year
        self.isLeapYear = ( year % 4 == 0 and 
                            (year % 100 != 0 or year % 400 == 0) )
        self.month = month = date_time.month

        self.julian = date_time.timetuple().tm_yday
        if month <= 2 and self.isLeapYear: self.julian -= 1

        self.years_since_1980 = years_since_1980 = year - 1980
        self.days_since_1980 = (years_since_1980 * 365) + \
                               (years_since_1980 / 4) + self.julian - 1 

        if self.isLeapYear or years_since_1980 < 0: self.time_offset = - 1.0
        else: self.time_offset = 0.0

        return date_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def siderialTime(self, elapsed_time, decimal_hour):
        # sideral time at Greenwich
        sidereal_time = ( 6.720165 + ( 24.0 *
                          ( (elapsed_time / 365.25) - self.years_since_1980 )
                          ) + (0.000001411 * elapsed_time)
                        ) * (15.0 * RAD_PER_DEG)
        # bnb: -180 < lon < +180
        if sidereal_time > TWO_PI: sidereal_time -= TWO_PI

        # calculate local sideral time by subtracting local longitude (in
        # hours west of Greenwich (1 hr = 15 degrees)) from sideral time
        local_sid_time = sidereal_time + (self.longitude * RAD_PER_DEG) + (
                         1.0027379 * (decimal_hour + self.utc_offset) *
                         (15.0 * RAD_PER_DEG) )

        # bnb: -180 < lon < +180
        if local_sid_time > TWO_PI: local_sid_time -= TWO_PI

        return sidereal_time, local_sid_time

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def solarRadiationAtTop(self, decimal_interval, cos_Z):
        I_O = 1367. * ( 1 +
              ( 0.034 * math.cos( TWO_PI * ((self.julian-1.)/365.) ) ) )
        # only calulate radiation when the solar_angle is above the horizon
        if I_O * cos_Z > 0: return I_O * cos_Z * decimal_interval
        else: return 0.

def test(longitude, latitude, date, utc_zone=-5):
    it = Solar(longitude, latitude, datetime.datetime(*date), utc_zone)
    hour = 1
    
    print 'Hourly data :'
    solar_radiation = it.hourlySolarRadiation()
    for srad in solar_radiation:
        print '    ', hour, srad
        hour += 1
    print "Daily sum :", sum(solar_radiation)
