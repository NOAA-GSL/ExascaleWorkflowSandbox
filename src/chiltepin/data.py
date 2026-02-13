from concurrent.futures import Future
from typing import Optional

from globus_sdk import TransferClient

import chiltepin.endpoint as endpoint
from chiltepin.tasks import python_task


@python_task
def transfer_task(
    src_ep: str,
    dst_ep: str,
    src_path: str,
    dst_path: str,
    timeout: int = 3600,
    polling_interval: int = 30,
    client: Optional[TransferClient] = None,
    recursive: bool = False,
    dependencies: Optional[Future] = None,
):
    """Transfer data asynchronously in a Parsl task

    This wraps synchronous Globus data transfer into a Parsl python_app task.
    Calling this function will immediately return a future. The result of the
    future will be True if the transfer completed successfully, or False if
    it did not.

    Parameters
    ----------

    src_ep: str
        Name of the source endpoint for the transfer.  Can be a display name
        or a UUID string.

    dst_ep: str
        Name of the destination endpoint for the transfer.  Can be a display
        name or a UUID string.

    src_path: str
        Path to the file or directory on the source endpoint that is to be
        transferred.

    dst_path: str
        Path to the file or directory on the destination endpoint where the
        data is to be transferred.

    timeout: int
        Number of seconds to wait for the transfer to complete.

    polling_interval: int
        Number of seconds to wait between checking the status of the transfer

    client: TransferClient | None
        Transfer client to use for submitting the transfers. If None, one
        will be retreived via the login process. If a login has already been
        performed, no login flow prompts will be issued.

    recursive: bool
        Whether or not a recursive transfer should be performed

    dependencies: Future | None
        Future to wait for completion before running the transfer task. If
        None, the transfer will be run at the next available scheduling
        opportunity
    """
    # Run the transfer
    completed = transfer(
        src_ep,
        dst_ep,
        src_path,
        dst_path,
        timeout=3600,
        polling_interval=30,
        client=None,
        recursive=False,
    )
    return completed


@python_task
def delete_task(
    src_ep: str,
    src_path: str,
    timeout: int = 3600,
    polling_interval: int = 30,
    client: Optional[TransferClient] = None,
    recursive: bool = False,
    dependencies: Optional[Future] = None,
):
    """Delete data asynchronously in a Parsl task

    This wraps synchronous Globus data deletion into a Parsl python_app task.
    Calling this function will immediately return a future. The result of the
    future will be True if the deletion completed successfully, or False if
    it did not.

    Parameters
    ----------

    src_ep: str
        Name of the source endpoint for the data to be deleted.  Can be a
        display name or a UUID string.

    src_path: str
        Path to the file or directory on the source endpoint that is to be
        deleted.

    timeout: int
        Number of seconds to wait for the deletion to complete.

    polling_interval: int
        Number of seconds to wait between checking the status of the deletion

    client: TransferClient | None
        Transfer client to use for submitting the deletion. If None, one
        will be retreived via the login process. If a login has already been
        performed, no login flow prompts will be issued.  NOTE: Yes, deletion
        is done using a TransferClient.

    recursive: bool
        Whether or not a recursive deletion should be performed

    dependencies: Future | None
        Future to wait for completion before running the deletion task. If
        None, the deletion will be run at the next available scheduling
        opportunity
    """
    completed = delete(
        src_ep,
        src_path,
        timeout=3600,
        polling_interval=30,
        client=None,
        recursive=False,
    )
    return completed


def transfer(
    src_ep: str,
    dst_ep: str,
    src_path: str,
    dst_path: str,
    timeout: int = 3600,
    polling_interval: int = 30,
    client: Optional[TransferClient] = None,
    recursive: bool = False,
):
    """Transfer data synchronously with Globus

    This performs a Globus transfer of data from one Globus transfer endpoint
    to another. This function will not return until the transfer completes or
    fails.

    Parameters
    ----------

    src_ep: str
        Name of the source endpoint for the transfer.  Can be a display name
        or a UUID string.

    dst_ep: str
        Name of the destination endpoint for the transfer.  Can be a display
        name or a UUID string.

    src_path: str
        Path to the file or directory on the source endpoint that is to be
        transferred.

    dst_path: str
        Path to the file or directory on the destination endpoint where the
        data is to be transferred.

    timeout: int
        Number of seconds to wait for the transfer to complete.

    polling_interval: int
        Number of seconds to wait between checking the status of the transfer

    client: TransferClient | None
        Transfer client to use for submitting the transfers. If None, one
        will be retreived via the login process. If a login has already been
        performed, no login flow prompts will be issued.

    recursive: bool
        Whether or not a recursive transfer should be performed
    """
    import globus_sdk

    # Get transfer client
    if not client:
        clients = endpoint.login()
        client = clients["transfer"]

    # Get the source endpoint
    src_id = None
    for ep in client.endpoint_search(src_ep, filter_non_functional=False):
        if ep["display_name"] == src_ep or ep["id"] == src_ep:
            src_id = ep["id"]
    if not src_id:
        raise Exception(f"Source endpoint '{src_ep}' could not be found")

    # Get the destination endpoint
    dst_id = None
    for ep in client.endpoint_search(dst_ep, filter_non_functional=False):
        if ep["display_name"] == dst_ep or ep["id"] == dst_ep:
            dst_id = ep["id"]
    if not dst_id:
        raise Exception(f"Destination endpoint '{dst_ep}' could not be found")

    # Add data access scopes for both endpoints (just in case)
    # client.add_app_data_access_scope([src_id, dst_id])

    # Build the transfer data
    task_data = globus_sdk.TransferData(
        client,
        source_endpoint=src_id,
        destination_endpoint=dst_id,
    )
    task_data.add_item(
        src_path,
        dst_path,
        recursive=recursive,
    )

    # Submit the transfer request
    try:
        task_doc = client.submit_transfer(task_data)
        task_id = task_doc["task_id"]
        done = client.task_wait(
            task_id, timeout=timeout, polling_interval=polling_interval
        )
        return done
    except globus_sdk.TransferAPIError as err:
        if err.info.consent_required:
            raise Exception(
                "Encountered a ConsentRequired error.\n"
                "You must login a second time to grant consents.\n\n"
                "err.info"
            )
        else:
            raise Exception(err)

def delete(
    src_ep: str,
    src_path: str,
    timeout: int = 3600,
    polling_interval: int = 30,
    client: Optional[TransferClient] = None,
    recursive: bool = False,
):
    """Delete data synchronously with Globus.

    This deletes data from a Globus endpoint. This function will not return
    until the deletion has completed or failed.

    Parameters
    ----------

    src_ep: str
        Name of the source endpoint for the data to be deleted.  Can be a
        display name or a UUID string.

    src_path: str
        Path to the file or directory on the source endpoint that is to be
        deleted.

    timeout: int
        Number of seconds to wait for the deletion to complete.

    polling_interval: int
        Number of seconds to wait between checking the status of the deletion

    client: TransferClient | None
        Transfer client to use for submitting the deletion. If None, one
        will be retreived via the login process. If a login has already been
        performed, no login flow prompts will be issued.  NOTE: Yes, deletion
        is done using a TransferClient.

    recursive: bool
        Whether or not a recursive deletion should be performed
    """
    import globus_sdk

    # Get transfer client
    if not client:
        clients = endpoint.login()
        client = clients["transfer"]

    # Get the source endpoint
    src_id = None
    for ep in client.endpoint_search(src_ep, filter_non_functional=False):
        if ep["display_name"] == src_ep or ep["id"] == src_ep:
            src_id = ep["id"]
    if not src_id:
        raise Exception(f"Source endpoint '{src_ep}' could not be found")

    # Add data access scopes for both endpoints (just in case)
    # client.add_app_data_access_scope([src_id, dst_id])

    # Build the delete data payload
    task_data = globus_sdk.DeleteData(client, src_id, recursive=True)
    task_data.add_item(src_path)

    # Submit the deletion request
    try:
        task_doc = client.submit_delete(task_data)
        task_id = task_doc["task_id"]
        done = client.task_wait(
            task_id,
            timeout=timeout,
            polling_interval=polling_interval,
        )
        return done
    except globus_sdk.TransferAPIError as err:
        if err.info.consent_required:
            raise Exception(
                "Encountered a ConsentRequired error.\n"
                "You must login a second time to grant consents.\n\n"
                "err.info"
            )
        else:
            raise Exception(err)
