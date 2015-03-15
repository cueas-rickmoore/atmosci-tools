
from atmosci.acis.client import AcisWebServicesClient
from atmosci.acis.gridinfo import acisGridNumber

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

from atmosci.acis.client import DEFAULT_URL
VALID_ELEMS = ['maxt','mint','pcpn','cdd','cddNN','hdd','hddNN','gdd','gddNN']

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class AcisGridDataClient(AcisWebServicesClient):

    def __init__(self, base_url=DEFAULT_URL, valid_elems=VALID_ELEMS,
                       debug=False):
        super(AcisGridDataClient, self).\
        __init__(base_url=base_url, valid_elems=valid_elems,
                 loc_keys=('bbox','loc','state'), date_required=True,
                 debug=debug)
        #!TODO " list of valid metadata

    def request(self, grid_id, **request_dict):
        grid_num = acisGridNumber(grid_id)
        return self.submitRequest('GridData', grid=grid_num, **request_dict)

    def query(self, json_query_string):
        return self.submitQuery('GridData', json_query_string)

    def _classSpecificRequirements(self, request_dict):
        return { 'grid':request_dict['grid'] }

