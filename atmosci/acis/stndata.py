
from .client import AcisWebServicesClient

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AcisStationDataClient(AcisWebServicesClient):

    def request(self, **request_dict):
        return self.submitRequest( 'StnData', **request_dict)

    def query(self, json_query_string):
        return self.submitQuery('StnData', json_query_string)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AcisMultiStationDataClient(AcisWebServicesClient):
    
    def request(self, **request_dict):
        return self.submitRequest( 'MultiStnData', **request_dict)

    def query(self, json_query_string):
        return self.submitQuery('MultiStnData', json_query_string)

