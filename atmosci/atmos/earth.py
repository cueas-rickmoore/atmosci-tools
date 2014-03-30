import os,sys

import math
DEG_PER_RAD = math.pi/180.0

try:
    import numpy as N
    SIN = N.sin
    COS = N.cos
    ATAN2 = N.arctan2
    ARCCOS = N.arccos
except:
    N = None
    SIN = math.sin
    COS = math.cos
    ATAN2 = math.atan2
    ARCCOS = math.acos

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

DISTANCE_FUNCTIONS

# all radius values are in kilometers

WGS66_SEMI_MAJOR = 6378.145
WGS66_FLATTENING = 1./298.25
WGS66_SEMI_MINOR = WGS66_SEMI_MAJOR - (WGS66_SEMI_MAJOR * WGS66_FLATTENING)
WGS66_MEAN_RADIUS = ((WGS66_SEMI_MAJOR * 2.) + WGS66_SEMI_MINOR) /3. 

WGS72_SEMI_MAJOR = 6378.135
WGS72_FLATTENING = 1./298.26
WGS72_SEMI_MINOR = WGS72_SEMI_MAJOR - (WGS72_SEMI_MAJOR * WGS72_FLATTENING)
WGS72_MEAN_RADIUS = ((WGS72_SEMI_MAJOR * 2.) + WGS72_SEMI_MINOR) /3. 

GRS80_SEMI_MAJOR = 6378.137
GRS80_FLATTENING = 1./298.257222100882711
GRS80_SEMI_MINOR = GRS80_SEMI_MAJOR - (GRS80_SEMI_MAJOR * GRS80_FLATTENING)
GRS80_MEAN_RADIUS = ((GRS80_SEMI_MAJOR * 2.) + GRS80_SEMI_MINOR) / 3.

WGS84_SEMI_MAJOR = 6378.137
WGS84_FLATTENING = 1./298.257223563
WGS80_SEMI_MINOR = WGS80_SEMI_MAJOR - (WGS80_SEMI_MAJOR * WGS80_FLATTENING)
WGS80_MEAN_RADIUS = ((WGS80_SEMI_MAJOR * 2.) + WGS80_SEMI_MINOR) /3. 

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class SphericalEarth(object):

    def __init__(self, radius=WGS84_SEMI_MAJOR):
        """
        Arguments:
        ---------
            radius = radius of the spherical Earth in meters. The default is the
            radius of the WGS84 semi-major
        """
        self.radius = radius
        self.distanceMethods = { }

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def distance(self, lat_1, lon_1, lat_2, lon_2, method="haversine"):
        """ calculates the distnace between two points (lon_1, lat_1) and
        (lon_2, lat_2).

        Two different methods give slightly different distances.

        If NUMPY is available :
           1. you can calculate the distance between a group of points
              and a single point by passing NUMPY arrays for one lon/lat
              pair and single float values for the other lon/lat pair.
           2. you can calculate the distance between two equal sized
              groups of points by passing NUMPY arrays for both lon/lat
              pairs. Returned distances will match up as follows:
                 distance[0] = distance b/w lon_1[0],lat_1[0] and
                                            lon_2[0],lat_2[0] 
                 distance[1] = distance b/w lon_1[1],lat_1[1] and
                                            lon_2[1],lat_2[1] 
                 etc.
        """
        distanceMethod = self['_%sDistance' % method]
        return self.distanceMethod(lat_1, lon_1, lat_2, lon_2)

    def _simpleDistance(self, lat_1, lon_1, lat_2, lon_2):
        # need all angular values (i.e. lat/lon) in radians
        # phi = 90 - latitude
        phi_1 = lat_1 * DEG_PER_RAD
        phi_2 = lat_2 * DEG_PER_RAD
        # theta = longitude
        theta_1 = lon_1 * DEG_PER_RAD
        theta_2 = lon_2 * DEG_PER_RAD
        # calculate cosine of angle of circular arc between points
        cosine_of_arc = (SIN(phi_1) * SIN(phi_2)) + ( COS(phi_1) * COS(phi_2) *
                                                      COS(theta_2 - theta_1) )
        # check for valid values
        if N is not None and isinstance(cosine_of_arc, N.ndarray):
            cosine_of_arc[N.where(cosine_of_arc < -1.0)] = N.nan
            cosine_of_arc[N.where(cosine_of_arc > 1.0)] = N.nan
            # compute spherical distance
            return ARCOS(cosine_of_arc) * self.radius
        else:
            if cosine_of_arc >=-1.0 and cosine_of_arc<=1.0:
                # compute spherical distance
                return ARCOS(cosine_of_arc) * self.radius
            else: return -32768.

    def _haversineDistance(self, lat_1, lon_1, lat_2, lon_2):
        # for a description of the Haversign Formula see :
        # http://en.wikipedia.org/wiki/Haversine_formula
        # the basic python implemention is available at : 
        # http://www.platoscave.net/blog/2009/oct/5/calculate-distance-latitude-longitude-python/
        #
        # need all angular values (i.e. lat/lon) in radians
        rlat_1 = lat_1 * DEG_PER_RAD
        rlat_2 = lat_2 * DEG_PER_RAD
        dlat = (rlat_2 - rlat_1) / 2
        rlon_1 = lon_1 * DEG_PER_RAD
        rlon_2 = lon_2 * DEG_PER_RAD
        dlon = (rlon_2 - rlon_1) / 2
        # calculate cosine of angle of circular arc between points
        cosine_of_arc = (SIN(dlat) * SIN(dlat)) + ( COS(rlat_1) * COS(rlat_2) *
                                                    SIN(dlon) * SIN(dlon) )
        # calculate relative length circular arc (percentage of radius)
        circular_arc = 2 * ATAN2(SQRT(cosine_of_arc), SQRT(1-cosine_of_arc))
        return circular_arc * self.radius

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def indexesWithinRadius(lons, lats, center_lon, center_lat, search_radius):
        """ returns indexes into the array of the points that are within the
        search radius from the center point.
        
        Arguments:
            lons, lats : coordinates of points to compare, they must
                         be numpy arrays or this method won't work
            center_lon, center_lat : location of point at center of
                        search area
            radiius : radius of search area
        """
        if N is None:
            raise ImportError, 'NUMPY is not available in this environment.'
        if not isinstance(lons, N.ndarray):
            raise TypeError, 'Input coordinates are not in a NUMPY array.'

        distance = self.distance(lons, lats, center_lon, center_lat)
        return N.where(distances <= search_radius)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def pointWithinRadius(lon, lat, center_lon, center_lat, radius):
        distance = self.distance(lon, lat, center_lon, center_lat)
        return distance <= radius

    def pointsWithinRadius(lons, lats, center_lon, center_lat, search_radius):
        """ returns lat/lon coordinate of only the points that are within
        the search radius from the center point.
        
        Arguments:
            lons, lats : coordinates of points to compare, they must
                         be numpy arrays or this method won't work
            center_lon, center_lat : location of point at center of
                        search area
            radiius : radius of search area
        """
        if N is None:
            raise ImportError, 'NUMPY is not available in this environment.'
        if not isinstance(lons, N.ndarray):
            raise TypeError, 'Input coordinates are not in a NUMPY array.'

        distance = self.distance(lons, lats, center_lon, center_lat)
        return distances[N.where(distances <= search_radius)]

