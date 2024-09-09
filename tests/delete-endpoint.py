import sys

from globus_compute_sdk import Client

ep = sys.argv[1]


print(f"Deleting endpoint: {ep}")
c = Client()
c.delete_endpoint(ep)
# GlobusHTTPResponse({"result":301})
