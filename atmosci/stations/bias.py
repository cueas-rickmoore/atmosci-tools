
import os, sys
from datetime import datetime

import numpy as N

from atmosci.utils.report import Reporter
from atmosci.analysis import interp

from atmosci.utils.proximity import allQuadrants
from atmosci.utils.proximity import indexesOfNeighborNodes

from atmosci.utils.units import convertUnits

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class StationBiasTool(object):

    def __init__(self, region_bbox, search_radius, c_parm, vicinity,
                       relative_nodes, node_reach, reporter_or_filepath=None):

        self.c_parm = c_parm
        self.node_reach = node_reach
        self.region_bbox = region_bbox
        self.relative_nodes = relative_nodes
        self.search_radius = search_radius
        self.vicinity = vicinity

        # create a reporter for perfomance and debug
        if isinstance(reporter_or_filepath, Reporter):
            self.reporter = reporter_or_filepath
        else:
            self.reporter = Reporter(self.__class__.__name__,
                                     reporter_or_filepath)
            self.reporter.close()

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def applyBias(self, dem_lons, dem_lats, dem_data, dem_data_units,
                        stn_lons, stn_lats, stn_bias, stn_bias_units,
                        report_rate=1000, debug=False, performance=False):
        """ Apply the calculated station temperature bias to the grid nodes. 
        """
        PERF_MSG = 'processed %d grid nodes in'
        PERF_MSG_SUFFIX = ' ... total = %d of %d'
        reporter = self.reporter

        search_radius = self.search_radius
        c_parm = self.c_parm
        vicinity = self.vicinity

        min_count = report_rate - 1

        dem_grid_shape = dem_lons.shape
        dem_grid_size = dem_lons.size

        # create empty in-memory arrays for calculated grids
        biased_data = N.empty(shape=dem_grid_shape, dtype=float)
        dem_data_bias = N.empty(shape=dem_grid_shape, dtype=float)

        num_nodes_processed = 0
        no_change = 0
        start_count = datetime.now()

        # make sure station and dem data are in the same units
        if stn_bias_units != dem_data_units:
            stn_bias = convertUnits(stn_bias, stn_bias_units, dem_data_units)

        # loop thru the nodes of the raw grid and apply the station bias
        for x in range(dem_grid_shape[0]):
            for y in range(dem_grid_shape[1]):
                if performance:
                    # report performance every 'report_rate' passes thru loop
                    if num_nodes_processed > min_count and\
                       num_nodes_processed % report_rate == 0:
                        msg = PERF_MSG % (report_rate)
                        sfx = PERF_MSG_SUFFIX % (num_nodes_processed,
                                                 dem_grid_size)
                        reporter.logPerformance(start_count, msg, sfx)
                        start_count = datetime.now()

                node_lon = dem_lons[x,y]
                node_lat = dem_lats[x,y]
                node_value = dem_data[x,y]
                if not self._passesApplyBiasTest(node_value, node_lon, node_lat,
                                                 stn_bias, stn_lons, stn_lats):
                    biased_data[x,y] = dem_data[x,y]
                    dem_data_bias[x,y] = 0.
                    num_nodes_processed += 1
                    no_change += 1
                    continue

                # get indexes of all stations within search radius of grid node
                # bbox will be different for each grid node
                bbox = (node_lon-search_radius, node_lon+search_radius,
                        node_lat-search_radius, node_lat+search_radius)
                indexes = N.where( (stn_lons >= bbox[0]) &
                                   (stn_lons <= bbox[1]) &
                                   (stn_lats >= bbox[2]) &
                                   (stn_lats <= bbox[3]) )

                # no stations within search radius
                if len(indexes[0]) < 1:
                    # NO ADJUSTMENT CAN BE MADE
                    biased_data[x,y] = dem_data[x,y]
                    dem_data_bias[x,y] = 0.
                    num_nodes_processed += 1
                    no_change += 1
                    continue

                # coordinates of all station in search area
                area_lons = stn_lons[indexes]
                area_lats = stn_lats[indexes]

                # test stations for 'nearness' to the grid node
                bbox = (node_lon-vicinity, node_lon+vicinity,
                        node_lat-vicinity, node_lat+vicinity)
                nearby = N.where( (area_lons >= bbox[0]) &
                                  (area_lons <= bbox[1]) &
                                  (area_lats >= bbox[2]) &
                                  (area_lats <= bbox[3]) )
                
                # in order to use MQ we must have either 2 'nearby' stations
                # or 2 in each quadrant surrounding the node 
                if ( len(nearby[0]) < 1 and not
                     allQuadrants(node_lon, node_lat, area_lons, area_lats) ):
                    # NO ADJUSTMENT CAN BE MADE
                    biased_data[x,y] = dem_data[x,y]
                    dem_data_bias[x,y] = 0.
                    num_nodes_processed += 1
                    no_change += 1
                    continue

                # run multiquadric interpolation on BIAS
                data_bias = interp.mq(node_lat, node_lon, area_lats, area_lons,
                                      stn_bias[indexes], c_parm)
                if N.isfinite(data_bias):
                    # apply valid bias
                    value = dem_data[x,y] - data_bias
                else:
                    # invalid bias ... NO ADJUSTMENT CAN BE MADE
                    value = dem_data[x,y]
                    data_bias = 0.
                    no_change += 1

                if N.isfinite(value):
                    biased_data[x,y] = value
                    dem_data_bias[x,y] = data_bias
                else:
                    biased_data[x,y] = dem_data[x,y]
                    dem_data_bias[x,y] = 0.
                    no_change += 1

                num_nodes_processed += 1

        # log performance for nodes not yet reported 
        unreported = num_nodes_processed % report_rate
        if performance and unreported > 0:
            msg = PERF_MSG % (unreported)
            sfx = PERF_MSG_SUFFIX % (num_nodes_processed, dem_grid_size)
            reporter.logPerformance(start_count, msg, sfx)

        return biased_data, dem_data_bias, (num_nodes_processed, no_change)

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def calculateBias(self, algorithm, stn_uids,
                            stn_lons, stn_lats, stn_data, stn_data_units,
                            raw_lons, raw_lats, raw_data, raw_data_units,
                            report_rate=100, debug=False, performance=False):
        """ Calculate the weighted difference between the data value at
        each station and the nearby grid nodes. It will use multiquadric
        interpolation except when there are an insufficient number of grid
        nodes nearby, then it will use a simple inverse distance weighted
        average.
        """
        # local refernces to instance attributes
        reporter = self.reporter
        vicinity = self.vicinity

        min_count = report_rate - 1
        PERF_MSG = 'processed %d stations (%d total) in'

        # initialize station temperature bias arrays
        stn_interp_data = [ ]
        stn_data_bias = [ ]
        num_stations = len(stn_uids)

        # initialize tracking variables
        algorithm_counts = [0,0,0]
        station_count = 0
        stations_bad_data = 0
        stations_outside = 0
        insufficient_coverage = 0
        bias_not_calculated = 0
        start_report = datetime.now()

        # make sure station and dem data are in the same units
        if raw_data_units != stn_data_units:
            raw_data = convertUnits(raw_data, raw_data_units, stn_data_units)

        # loop though list of stations making adjustments to both station and
        # grid node temperature extremes
        for indx in range(num_stations):
        # the following is good for a limited test loop
        #for indx in (84,85,278,330,337,345,360,368,444,476):
            # report performance every 'report_rate' passes thru the loop
            if performance and ( station_count > min_count and
                                 station_count % report_rate == 0 ):
                reporter.logPerformance(start_report,
                                        PERF_MSG % (report_rate,station_count))
                start_report = datetime.now()

            # extract observation data for this station
            stn_id = stn_uids[indx]
            stn_lon = stn_lons[indx]
            stn_lat = stn_lats[indx]
            stn_info = 'station %d (%s) at [%-9.5f, %-9.5f]' % (indx,
                            stn_id, stn_lon, stn_lat)

            # station is not within the bounding boxx for this run
            if not self._pointInBounds(stn_lon, stn_lat):
                stn_interp_data.append(N.inf)
                stn_data_bias.append(N.inf)
                stations_outside += 1
                station_count += 1
                continue

            stn_value = stn_data[indx]
            # check for invalid data value for this station
            # this shouldn't happen if station data prep is done right !!!
            if not N.isfinite(stn_value):
                # set missing values and skip to next iteration
                stn_interp_data.append(N.inf)
                stn_data_bias.append(N.inf)
                stations_bad_data += 1
                station_count += 1
                if debug:
                    print 'skipped ', stn_info
                    print '... bad data value', stn_values
                continue

            # additional check that may be required by sub-classed data types
            if not self._passesCalcBiasTest(stn_value, stn_lon, stn_lat,
                                            raw_data, raw_lons, raw_lats):
                stn_interp_data.append(stn_value)
                stn_data_bias.append(0.)
                station_count += 1
                bias_not_calculated += 1
                continue

            # apply appripriate bias calculation algorithm
            if algorithm == 'mq':
                result = self.doMQInterp(stn_lon, stn_lat, stn_info,
                                         raw_lons, raw_lats, raw_data,
                                         debug)
            else:
                result = self.doIDWInterp(stn_lon, stn_lat, stn_info,
                                          raw_lons, raw_lats, raw_data,
                                          debug)

            if result is None:
                # set missing values and skip to next iteration
                stn_interp_data.append(N.inf)
                stn_data_bias.append(N.inf)
                insufficient_coverage += 1
                station_count += 1
                continue

            interpolated_value = result[1]
            data_bias = interpolated_value - stn_value
            estimated_value = interpolated_value - data_bias

            stn_data_bias.append(data_bias)
            stn_interp_data.append(estimated_value)

            station_count += 1
            algorithm_counts[result[0]] += 1

        if performance:
            unreported = station_count % report_rate
            if unreported > 0:
                reporter.logPerformance(start_report,
                                        PERF_MSG % (unreported,station_count))

        # convert the interpolated precip and bias to numpy arrays
        stn_interp_data = N.array(stn_interp_data, dtype=float)
        stn_data_bias = N.array(stn_data_bias, dtype=float)
        indexes = N.where(N.isnan(stn_data_bias) | N.isinf(stn_data_bias) )
        bad_bias_count = len(indexes[0])
    
        statistics = (station_count, algorithm_counts[2], algorithm_counts[1],
                      bad_bias_count, stations_bad_data, stations_outside,
                      insufficient_coverage, bias_not_calculated)
        return stn_interp_data, stn_data_bias, statistics

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def doMQInterp(self, stn_lon, stn_lat, stn_info, node_lons, node_lats,
                         node_data, debug):
        """ determine value at station from values at nearby grid nodes
        using Multi-Quadric Distance algorithm
        """
        c_param = self.c_parm
        search_radius = self.search_radius

        # get indexes of all grid nodes within search radius of station
        # that have valid data values
        bbox = (stn_lon-search_radius, stn_lon+search_radius,
                stn_lat-search_radius, stn_lat+search_radius)
        indexes = N.where( (node_lons >= bbox[0]) & (node_lats >= bbox[2]) &
                           (node_lons <= bbox[1]) & (node_lats <= bbox[3]) &
                           N.isfinite(node_data) )

        # no grid nodes near this station
        if len(indexes) == 0 or len(indexes[0]) == 0:
            # set missing values and skip to next iteration
            if debug:
                print 'skipped ', stn_info
                print ' ... no grid nodes within search radius.'
            return None

        min_x = min(indexes[0])
        max_x = max(indexes[0]) + 1
        min_y = min(indexes[1])
        max_y = max(indexes[1]) + 1

        # must have at least one node in each quadrant
        area_lons = node_lons[min_x:max_x,min_y:max_y]
        area_lons = area_lons.flatten()

        area_lats = node_lats[min_x:max_x,min_y:max_y]
        area_lats = area_lats.flatten()

        area_values = node_data[min_x:max_x,min_y:max_y]
        area_values = area_values.flatten()
        num_nodes = len(area_values)

        # grid nodes are present in all 4 quadrants around staton
        # so, we can use Multiquadric interpolation
        if allQuadrants(stn_lon, stn_lat, area_lons, area_lats):
            interp_value = interp.mq(stn_lat, stn_lon, area_lats, area_lons,
                                    area_values, c_param)
            algorithm = 2

        # grid nodes NOT present in all 4 quadrants around staton
        # so we must use Inverse Distance Weighted Average
        elif num_temps > 3:
            interp_value = interp.idw(stn_lat, stn_lon, area_lats, area_lons,
                                      area_values)
            algorithm = 1
        # too few nodes, take simple average
        else:
            interp_value = area_values.sum() / float(num_nodes)
            algorithm = 0

        return algorithm, interp_value

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def doIDWInterp(self, stn_lon, stn_lat, stn_info, node_lons, node_lats,
                          node_data, debug):
        """ determine value at station from values at nearby grid nodes
        using Inverse Distance Weigthed algorithm
        """
        relative_nodes = self.relative_nodes
        node_reach = self.node_reach

        # indexes of all grid nodes within search domain
        indexes = indexesOfNeighborNodes(stn_lon, stn_lat, relative_nodes,
                                         node_lons, node_lats, node_reach)
        rel_lons = node_lons[indexes]
        rel_lats = node_lats[indexes]
        rel_data = node_data[indexes]

        # narrow it doen to those with valid values
        indexes = N.where(N.isfinite(rel_data))
        rel_lons = rel_lons[indexes]
        rel_lats = rel_lats[indexes]
        rel_data = rel_data[indexes]

        num_relatives = len(rel_data)
        # Inverse Distance Weighted Average
        if num_relatives > 3:
            interp_value = interp.idw(stn_lat, stn_lon, rel_lats, rel_lons,
                                      rel_data)
            algorithm = 1
        # too few nodes, take simple average
        elif num_relatives > 0:
            interp_value = min_temps.sum() / float(total_temps)
            algorithm = 0
        # no valid nearby nodes, no bias ?
        else:
            if debug:
                print 'skipped ', stn_info
                print "... no valid grid nodes within relative neighborhood"
            return None

        return algorithm, interp_value

    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

    def _pointInBounds(self, lon, lat):
        # check whether input point is within bounds for this run
        bbox = self.region_bbox
        if lon < bbox[0]: return False
        if lon > bbox[2]: return False
        if lat < bbox[1]: return False
        if lat > bbox[3]: return False
        return True

    def _passesApplyBiasTest(self, node_value, node_lon, node_lat,
                                   stn_bias, stn_lons, stn_lats):
        return True

    def _passesCalcBiasTest(self, stn_value, stn_lon, stn_lat,
                                  raw_data, raw_lons, raw_lats):
        return True

