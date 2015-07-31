
import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def roundGDD(gdd):
    return N.round(gdd + .01)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def accumulateGDD(gdd, axis=None):
    """ Calculate accumulated GDD from a NumPy array of daily GDD values.

    Arguments
    --------------------------------------------------------------------
    gdd  : NumPy float array of daily GDD
    axis : array axis along whihc to calculate average. Not used for 1D
           arrray. Defaults to 0 for multi-dimension arrays. 

    Returns
    --------------------------------------------------------------------
    NumPy array af the same dimensions as the input gdd array.
    """
    if axis is None: return N.cumsum(gdd, axis=0)
    else: return N.cumsum(gdd, axis=axis)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcAvgGDD(gdd, axis=None):
    """ Calculate the average for a NumPy array of GDD values.

    Arguments
    --------------------------------------------------------------------
    gdd  : NumPy float array
    axis : array axis along whihc to calculate average. Not used for 1D
           arrray. Defaults to 0 for multi-dimension arrays. 

    Returns
    --------------------------------------------------------------------
    float value for 1D input
    OR
    NumPy array with 1 fewer dimensions than the input gdd array.
    """
    if not isinstance(gdd, N.ndarray):
        raise TypeError, 'gdd argument must be a NumPy array'
    if gdd.ndim == 1:
        return N.round(N.nanmean(gdd) + .01)
    else:
        if axis is None:
            return N.round(N.nanmean(gdd, axis=0) + .01)
        else: return N.round(N.nanmean(gdd, axis=axis) + .01)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcAvgTemp(maxt, mint, threshold):
    """ Calculate the average temperature based on commonly accepted GDD
    threshold rules.

    Arguments
    --------------------------------------------------------------------
    maxt      : maximum temperature
    mint      : minimum temperature
    threshold : GDD threshold specification. Pass a single int for 
                caculatations using only a low temperature threshold.
                Pass a tuple/list for calculations using both upper and
                lower GDD thresholds.

    NOTE: maxt and mint arguments may be either a single float or int or
          a NumPy array of floats. 

    Returns
    --------------------------------------------------------------------
    calculated average temperature of same type and size as input temps
    """
    if isinstance(threshold, (list,tuple)):
        if threshold[0] > threshold[1]:
            hi_thold, lo_thold = threshold
        else: lo_thold, hi_thold = threshold
        if isinstance(maxt, N.ndarray):
            _mint = mint.copy()
            _mint[N.where(_mint < lo_thold)] = lo_thold 
            _mint[N.where(_mint > hi_thold)] = hi_thold
            _maxt = maxt.copy()
            _maxt[N.where(_maxt < lo_thold)] = lo_thold 
            _maxt[N.where(_maxt > hi_thold)] = hi_thold
        else:
            if mint < lo_thold: _mint = lo_thold 
            elif mint > hi_thold: _mint = hi_thold
            else: _mint = mint
            if maxt < lo_thold: _maxt = lo_thold 
            elif maxt > hi_thold: _maxt = hi_thold
            else: _maxt = maxt
        return N.round(((_maxt + _mint) * 0.5) + .01)
    else: return N.round(((maxt + mint) * 0.5) + .01)

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

def calcGDD(avgt, threshold):
    """ Calculate the GDD using average temperature based on commonly accepted
    GDD threshold rules.

    Arguments
    --------------------------------------------------------------------
    avgt      : average temperature
    threshold : GDD threshold specification. Pass a single int for 
                caclutations using only a low temperature threshold.
                Pass a tuple/list for calculations using both upper and
                lower GDD thresholds.

    NOTE: avgt argument may be float, int or a NumPy array of floats.

    Returns
    --------------------------------------------------------------------
    GDD calculated average temperature of same type and size as avgt
    """
    if isinstance(threshold, (list,tuple)):
        if threshold[0] > threshold[1]:
            hi_thold, lo_thold = threshold
        else: lo_thold, hi_thold = threshold

        if isinstance(avgt, N.ndarray):
            nans = N.where(N.isnan(avgt))
            gdd = N.zeros(avgt.shape, dtype=avgt.dtype)
            gdd[N.where(avgt > hi_thold)] = hi_thold - lo_thold
            avgt_gt_low = N.where(avgt > lo_thold)
            gdd[avgt_gt_low] = avgt[avgt_gt_low] - lo_thold
            gdd[nans] = N.nan
            return gdd
        else:
            if avgt > hi_thold: return type(avgt)(hi_thold)
            elif avgt > lo_thold: return type(avgt)(avgt - lo_thold)
            return type(avgt)(0)
    # single value - kower threshold only
    else:
        if isinstance(avgt, N.ndarray):
            nans = N.where(N.isnan(avgt))
            gdd = N.zeros(avgt.shape, dtype=avgt.dtype)
            avgt_gt_low = N.where(avgt > threshold)
            gdd[avgt_gt_low] = avgt[avgt_gt_low] - threshold
            gdd[nans] = N.nan
            return gdd
        else:
            if avgt > threshold: return type(avgt)(avgt - threshold)
            return type(avgt)(0)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GDDFunctionsMixin:

    def accumulateGDD(self, daily_gdd, axis=None):
        return accumulateGDD(gdd, axis)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcAvgGDD(self, gdd, axis=None):
        """ Calculate average GDD from a NumPy array of GDD values.

        Arguments
        --------------------------------------------------------------------
        gdd  : NumPy float array
        axis : array axis along whihc to calculate average. Not used for 1D
               arrray. Defaults to 0 for multi-dimension arrays. 

        Returns
        --------------------------------------------------------------------
        float value for 1D input
        OR
        NumPy array with 1 fewer dimensions than the input gdd array.
        """
        return calcAvgGDD(gdd, axis)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcAvgTemp(self, maxt, mint, threshold):
        """ Calculate the average temperature based on commonly accepted GDD
        threshold rules.

        Arguments
        --------------------------------------------------------------------
        maxt      : maximum temperature
        mint      : minimum temperature
        threshold : GDD threshold specification. Pass a single int for 
                    caculatations using only a low temperature threshold.
                    Pass a tuple/list for calculations using both upper and
                    lower GDD thresholds.

        NOTE: maxt and mint arguments may be either a single float or int or
              a NumPy array of floats. 

        Returns
        --------------------------------------------------------------------
        calculated average temperature of same type and size as input temps
        """
        return calcAvgTemp(maxt, mint, threshold)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calcGDD(self, daily_gdd, axis=None):
        return calcGDD(gdd, axis)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GDDCalculatorMixin(GDDFunctionsMixin):

    def __call__(self, maxt, mint, gdd_threshold, axis=None):
        """ Calculate the growoing degree days from max & min temperatures
        using on commonly accepted GDD threshold rules.

        Arguments
        --------------------------------------------------------------------
        maxt      : maximum temperature
        mint      : minimum temperature
        threshold : GDD threshold specification. Pass a single int for 
                    caculatations using only a low temperature threshold.
                    Pass a tuple/list for calculations using both upper and
                    lower GDD thresholds.

        NOTE: maxt and mint arguments may be either a single float or int or
              a NumPy array of floats or ints. 

        Returns
        --------------------------------------------------------------------
        calculated average temperature of same type and size as input temps
        """
        return calcGDD(calcAvgTemp(maxt, mint, threshold), threshold)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GDDCalculator(GDDCalculatorMixin, object):

    def __init__(self, low_threshold, high_threshold=None):
        if high_threshold is None:
            self.threshold = low_threshold
        else: self.threshold = (low_threshold, high_threshold)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, mint, maxt):
        return self.estimateGDD(mint, maxt, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateGDD(self, mint, maxt):
        return calcGDD(calcAvgTemp(maxt, mint, self.threshold), self.threshold)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# The following classes are DEPRECATED provided for compatabillity with
# previous versions. DO NOTUSE --- THEY WILL BE DELETED VERY SOON.
#
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# clone of GDDCalculator ... provides consistency with other modules
# that require different methods ofr handling arrays and 3D grids
class ArrayGDDCalculator(GDDCalculator):
    pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# clone of GDDCalculator ... provides consistency with other modules
# that require different methods for handling arrays and 3D grids
class GridGDDCalculator(GDDCalculator):
    pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GDDAccumulator(GDDCalculator):

    def __init__(self, low_threshold, high_threshold=None,
                       previously_accumulated_gdd=None):
        if high_threshold is None:
            self.threshold = low_threshold
        else: self.threshold = (low_threshold, high_threshold)
        self.accumulated_gdd = previously_accumulated_gdd

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, mint, maxt):
        daily_gdd = self.estimateGDD(mint, maxt)
        if self.daily_gdd is not None:
            self.daily_gdd = N.vstack((self.daily_gdd, daily_gdd))
        else: self.daily_gdd = daily_gdd

        accumulated = self.accumulate(daily_gdd, debug)
        if self.accumulated_gdd is not None:
            self.accumulated_gdd = N.vstack((self.accumulated_gdd, accumulated))
        else: self.accumulated_gdd = accumulated

        return daily_gdd, accumulated

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def accumulate(self, daily_gdd):
        if self.accumulated_gdd is not None:
            return self.accumulateGDD(daily_gdd, axis) + \
                   self._previouslyAccumulated(daily_grid.shape)
        else: return self.accumulateGDD(daily_gdd, axis)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _previouslyAccumulated(self, grid_shape):
        if self.accumulated_gdd is None:
            return N.zeros(grid_shape[1:], dtype=float)
        else:
            if self.accumulated_gdd.ndim == 2:
                return self.accumulated_gdd
            else: return self.accumulated_gdd[-1,:,:]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# clone of GDDAccumulator ... provides consistency with other modules
# that require different methods ofr handling arrays and 3D grids
class ArrayGDDAccumulator(GDDAccumulator):
    pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# clone of GDDAccumulator ... provides consistency with other modules
# that require different methods for handling arrays and 3D grids

class GridGDDAccumulator(GDDAccumulator):
    pass

