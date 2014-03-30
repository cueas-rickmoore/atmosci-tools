#! /Users/rem63/venvs/atmosci/bin/python

import os
import datetime
from dateutil.relativedelta import relativedelta

from nrcc.utils.options import getBboxFromOptions, getRegionFromOptions
from nrcc.utils.string import tupleFromString

from nrcc.stations.client import BaseAcisDataClient
from nrcc.stations.multi  import AcisMultiStationDataClient
from nrcc.stations.single import AcisStationDataClient

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from nrcc.config import STATIONS, REGION

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def getStationsInState(date, state, elements, metadata, client, base_url):
    if client == 'base':
        return BaseAcisDataClient(base_url).request('MultiStnData', date=date,
                                            elems=elements, meta=metadata,
                                            state=state)
    else:
        return AcisMultiStationDataClient(base_url).allStationsInState(state,
                                                    elements, date, metadata,
                                                    state=state)

def getStationsInBbox(date, bbox, elements, metadata, client, base_url):
    if client == 'base':
        return BaseAcisDataClient(base_url).request('MultiStnData', date=date,
                                            elems=elements, meta=metadata,
                                            bbox=bbox)
    else:
        return AcisMultiStationDataClient(base_url).getRawData(state,
                                                    elements, date, metadata,
                                                    bbox=bbox)

def getStation(date, uid, elements, metadata, client, base_url):
    if client == 'base':
        if type(date) in (tuple,list):
            return BaseAcisDataClient(base_url).request('StnData', uid=uid,
                                                sDate=date[0], eDate=date[1],
                                                elems=elements, meta=metadata)
        else:
            return BaseAcisDataClient(base_url).request('StnData', uid=uid,
                                                date=date, elems=elements,
                                                meta=metadata)
    else:
        if type(date) in (tuple,list):
            return AcisStationDataClient(base_url).getRawData(elements, date[0], 
                                                   date[1], metadata, uid=uid)
        else:
            return AcisStationDataClient(base_url).getRawData(elements, date, 
                                                   meta=metadata, uid=uid)

def saveStationData(station_data, out_filepath):
    out_file = open(os.path.normpath(out_filepath),'w')
    if type(station_data) in (list,tuple):
        out_file.write(str(station_data[0]))
        out_file.write('\n')
        out_file.write(str(station_data[1]))
    else:
        out_file.write(str(station_data['elems']))
        for station in station_data['data']:
            out_file.write('\n')
            out_file.write(str(station))
    out_file.close()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from optparse import OptionParser
parser = OptionParser()
parser.add_option('-a', action='store_true', dest='add_flag_and_time',
                  default=False)
parser.add_option('-b', action='store', type='string', dest='bbox',
                  default=None)
parser.add_option('-c', action='store', type='string', dest='client',
                  default='base')
parser.add_option('-d', action='store', type='int', dest='num_days',
                  default=1)
parser.add_option('-e', action='store', type='string', dest='elements',
                  default='pcpn,maxt,mint')
parser.add_option('-i', action='store', type='string', dest='station_id',
                  default='18667')
parser.add_option('-m', action='store', type='string', dest='metadata',
                  default='uid,name,ll,elev')
parser.add_option('-o', action='store', type='string', dest='output_filepath',
                  default='acis_download_results.txt')
parser.add_option('-r', action='store', type='string', dest='region',
                  default=None)
parser.add_option('-s', action='store', type='string', dest='state',
                  default=None)
parser.add_option('-u', action='store', type='string', dest='base_url',
                  default=STATIONS.download_url)
parser.add_option('-z', action='store_true', dest='debug', default=False)
options, args = parser.parse_args()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if len(args) > 0:
    year = int(args[0])
    month = int(args[1])
    day = int(args[2])
else:
    today = datetime.datetime.now()
    year = today.year
    month = today.month
    day = today.day
start_date = datetime.date(year,month,day)
if options.num_days > 1:
    end_date = start_date + relativedelta(days=options.num_days)
    date = (start_date,end_date)
else:
    date = start_date

bbox = None
state = None
station_id = None
if options.bbox is not None:
    bbox = getBboxFromOptions(options)
elif options.region is not None:
    region = getRegionFromOptions(options)
    bbox = region.data_bbox
elif options.state is not None:
    state = options.state.upper()
else:
    station_id = options.station_id

elements = tupleFromString(options.elements)
metadata = tupleFromString(options.metadata)

add_flag_and_time = options.add_flag_and_time
if add_flag_and_time:
    elems = elements
    elements = [ ]
    for element in elems:
        if element.isdigit():
            elements.append( {'vX':element,'add':['f','t']} )
        else:
            elements.append( {'name':element,'add':['f','t']} )

if bbox is not None:
    stations = getStationsInBbox(sdate, bbox, elements, metadata,
                                 options.client, options.base_url)
    saveStationData(stations, options.output_filepath)
elif state is not None:
    stations = getStationsInState(date, state, elements, metadata,
                                  options.client, options.base_url)
    saveStationData(stations, options.output_filepath)
else:
    station = getStation(date, station_id, elements, metadata, options.client,
                         options.base_url)
    saveStationData(station, options.output_filepath)

