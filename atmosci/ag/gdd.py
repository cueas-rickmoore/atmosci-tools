
try:
    import numpy as N
except:
    N = None

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class GDDCalculator(object):

    def __init__(self, low_threshold, high_threshold=None):
        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, mint, maxt, debug=False):
        return self.estimateGDD(mint, maxt, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateGDD(self, mint, maxt, debug=False):
        low_threshold = self.low_threshold
        high_threshold = self.high_threshold
    
        if mint < low_threshold: _mint = low_threshold
        # works when low_threshold is None becuase
        # None < anything else is always False
        elif mint > high_threshold: _mint = high_threshold
        else: _mint = mint
        if debug: print '\nmint after threshold applied :', _mint
    
        if maxt < low_threshold: _maxt = low_threshold
        # works when high_threshold is None becuase
        # None > anything else is always False
        elif maxt > high_threshold: _maxt = high_threshold
        else: _maxt = maxt
        if debug: print '\nmint after threshold applied :', _mint
    
        avgt = (_mint + _mint) / 2.
        if debug: print '\nadjusted average temp :', avgt

        return round(avgt) - low_threshold

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ArrayGDDCalculator(object):

    def __init__(self, low_threshold, high_threshold=None):
        if N is None:
            errmsg = 'Numpy is not available.'
            errmsg += 'Numpy is required for GDD array operations.'
            raise RuntimeError, errmsg

        self.low_threshold = low_threshold
        self.high_threshold = high_threshold

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, mint, maxt, debug=False):
        return self.estimateGDD(mint, maxt, debug)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def estimateGDD(self, mint, maxt, debug=False):
        low_threshold = self.low_threshold
        high_threshold = self.high_threshold

        adjusted_mint = N.copy(mint)
        adjusted_mint[N.where(mint < low_threshold)] = low_threshold
        if high_threshold is not None: # no high threshold
            adjusted_mint[N.where(mint > high_threshold)] = high_threshold
        if debug:
            print '\nmint after threshold applied :'
            print adjusted_mint
    
        adjusted_maxt = N.copy(maxt)
        adjusted_maxt[N.where(maxt < low_threshold)] = low_threshold
        if high_threshold is not None: # no high threshold
            adjusted_maxt[N.where(maxt > high_threshold)] = high_threshold
        if debug:
            print '\nmaxt after threshold applied :'
            print adjusted_maxt
    
        adjusted_avgt = (adjusted_mint + adjusted_maxt) / 2.
        if debug:
            print '\nadjusted average temp :'
            print adjusted_avgt

        return N.round(adjusted_avgt, decimals=0) - low_threshold

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# grid class clone of ArrayGDDCalculator ... provides consistency with other
# modules that require different methods for handling arrays and 3D grids

class GridGDDCalculator(ArrayGDDCalculator):
    pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class ArrayGDDAccumulator(ArrayGDDCalculator):

    def __init__(self, low_threshold, high_threshold=None,
                       previously_accumulated_gdd=None):
        if N is None:
            errmsg = 'Numpy is not available.'
            errmsg += 'Numpy is required for GDD grid operations.'
            raise RuntimeError, errmsg

        ArrayGDDCalculator.__init__(self, low_threshold, high_threshold)

        self.accumulated_gdd = previously_accumulated_gdd
        self.daily_gdd = None

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def __call__(self, mint, maxt, debug=False):
        daily_gdd = self.estimateGDD(mint, maxt, debug)
        if self.daily_gdd is not None:
            self.daily_gdd = N.vstack((self.daily_gdd, daily_gdd))
        else: self.daily_gdd = daily_gdd

        accumulated = self.accumulate(daily_gdd, debug)
        if self.accumulated_gdd is not None:
            self.accumulated_gdd = N.vstack((self.accumulated_gdd, accumulated))
        else: self.accumulated_gdd = accumulated

        return daily_gdd, accumulated

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def accumulate(self, daily_gdd, debug=False):
        previous = self._previouslyAccumulated(daily_gdd.shape)
        accumulated = N.copy(daily_gdd)
        accumulated[0] = previous + accumulated[0]
        return N.cumsum(accumulated, axis=0)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _previouslyAccumulated(self, grid_shape):
        if self.accumulated_gdd is None:
            return N.zeros(grid_shape[1:], dtype=float)
        else: return self.accumulated_gdd[-1]

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# grid class clone of ArrayGDDAccumulator ... provides consistency with other
# modules that require different methods for handling arrays and 3D grids

class GridGDDAccumulator(ArrayGDDAccumulator):
    pass

