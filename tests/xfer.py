import chiltepin.endpoint as endpoint
import globus_sdk

clients = endpoint.login()
transfer_client = clients["transfer"]

# Find my laptop endpoint
for ep in transfer_client.endpoint_search("harrop-lt", filter_non_functional=False):
    if ep["display_name"] == "harrop-lt":
        HARROP_LAPTOP = ep["id"]
        HARROP_PATH = "/Users/christopher.w.harrop/work/SENA/1GB"

# Find the RDHPCS endpoints
for ep in transfer_client.endpoint_search("noaardhpcs", filter_non_functional=False):
    match ep["display_name"]:
        case "noaardhpcs#niagara_untrusted":
            NIAGARA = ep["id"]
            NIAGARA_PATH = "/collab1/data_untrusted/Christopher.W.Harrop/1GB"
        case "noaardhpcs#hera_untrusted":
            HERA = ep["id"]
            HERA_PATH = "/scratch2/data_untrusted/Christopher.W.Harrop/1GB"
        case "noaardhpcs#jet_untrusted":
            JET = ep["id"]
            JET_PATH = "/lfs5/data_untrusted/Christopher.W.Harrop/1GB"
        case "noaardhpcs#gaea":
            GAEA = ep["id"]
            GAEA_PATH = ""

# Find the MSU endpoints
for ep in transfer_client.endpoint_search("msuhpc2", filter_non_functional=False):
    match ep["display_name"]:
        case "msuhpc2#Hercules-dtn":
            HERCULES = ep["id"]
            HERCULES_PATH = "/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.transfer/tests/1GB"

#src_ep = HARROP_LAPTOP
#src_path = HARROP_PATH
src_ep = HERA
src_path = HERA_PATH

dst_ep = HERCULES
dst_path = HERCULES_PATH
#dst_ep = NIAGARA
#dst_path = NIAGARA_PATH
#dst_ep = HERA
#dst_path = HERA_PATH
#dst_ep = JET
#dst_path = JET_PATH

task_data = globus_sdk.TransferData(
    source_endpoint=src_ep, destination_endpoint=dst_ep
)
task_data.add_item(
    src_path,  # source
    dst_path,  # dest
    #recursive=True,
)

try:
    #transfer_client.add_app_data_access_scope(dst_ep)
    task_doc = transfer_client.submit_transfer(task_data)
    task_id = task_doc["task_id"]
    print(f"submitted transfer, task_id={task_id}")
except globus_sdk.TransferAPIError as err:
    if not err.info.consent_required:
        raise
    print(
        "Encountered a ConsentRequired error.\n"
        "You must login a second time to grant consents.\n\n"
    )
    print(f"{err.info.consent_required.required_scopes}")
    #clients = endpoint.login()
    #transfer_client = clients["transfer"]
    #task_doc = transfer_client.submit_transfer(task_data)
    #task_id = task_doc["task_id"]
    #print(f"submitted transfer, task_id={task_id}")
    
    #self.login_and_get_transfer_client(
    #    scopes=err.info.consent_required.required_scopes
    #)
    #task_doc = self.transfer_client.submit_transfer(task_data)
    #task_id = task_doc["task_id"]
    #print(f"submitted transfer, task_id={task_id}")
    
