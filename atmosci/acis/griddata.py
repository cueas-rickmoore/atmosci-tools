
from atmosci.acis.client import AcisWebServicesClient
from atmosci.acis.gridinfo import gridNumFromString

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AcisGridDataClient(AcisWebServicesClient):

    def request(self, grid_id, **request_dict):
        if isinstance(grid_id, basestring):
            grid_num = gridNumFromString(grid_id)
        else: grid_num = grid_id
        return self.submitRequest('GridData', grid=grid_num, **request_dict)

    def query(self, json_query_string):
        return self.submitQuery('GridData', json_query_string)

