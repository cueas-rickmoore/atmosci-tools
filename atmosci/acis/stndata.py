
from .client import AcisWebServicesClient

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AcisStationDataClient(AcisWebServicesClient):

    def request(self, **kwargs):
        return AcisWebServicesClient.request(self, 'StnData', **kwargs)

    def query(self, json_query_string):
        return AcisWebServicesClient.query(self, 'StnData', json_query_string)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AcisMultiStationDataClient(AcisWebServicesClient):
    
    def request(self, **kwargs):
        return AcisWebServicesClient.request(self, 'MultiStnData', **kwargs)

    def query(self, json_query_string):
        return AcisWebServicesClient.query(self, 'MultiStnData',
                                           json_query_string)

