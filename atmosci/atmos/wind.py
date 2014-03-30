
import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def uWind(direction, speed):
    """ calcualte u (Zonal Velocity) component of wind vector
    """
    return speed * -N.sin(N.radians(direction))

def vWind(direction, speed):
    """ calcualte v (Meridional Velocity) component of wind vector
    """
    return speed * -N.cos(N.radians(direction))

