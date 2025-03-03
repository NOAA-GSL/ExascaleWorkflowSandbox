from globus_compute_sdk import Client
import chiltepin.endpoint as endpoint
import globus_sdk.services.compute

# Get compute client
clients = endpoint.login()
c = clients["compute"]

eps = []
for ep in c.get_endpoints():
    uuid = ep["uuid"]
    name = ep["name"]
    print(uuid)
    try:
        status = c.get_endpoint_status(uuid)["status"]
        metadata = c.get_endpoint_metadata(uuid)
        host = metadata["hostname"]
        eps.append({"uuid": uuid, "name": name, "host": host, "status": status})
        name_len = max(len(ep["name"]) for ep in eps)
        host_len = max(len(ep["host"]) for ep in eps)
        status_len = max(len(ep["status"]) for ep in eps)
    except globus_sdk.services.compute.errors.ComputeAPIError as e:
        c.delete_endpoint(uuid)
        print(e)

for ep in eps:
    uuid = ep["uuid"]
    name = ep["name"]
    status = ep["status"]
    host = ep["host"]
    yes_no = input(
        f"""Delete {uuid} :: {status:<{status_len}} :: {host:<{host_len}} :: {name:<{name_len}}? (y/N): """
    )
    if yes_no.lower() in ["yes", "y"]:
        c.delete_endpoint(uuid)
