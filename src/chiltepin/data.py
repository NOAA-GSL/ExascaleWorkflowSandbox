from concurrent.futures import Future
from typing import Optional
import textwrap
from globus_sdk import TransferClient

import chiltepin
import chiltepin.endpoint as endpoint
from chiltepin.tasks import bash_task, python_task
import importlib.resources

@python_task
def transfer_async(
    src_ep: str,
    dst_ep: str,
    src_path: str,
    dst_path: str,
    timeout: int = 3600,
    polling_interval: int = 30,
    client: Optional[TransferClient] = None,
    recursive: bool = False,
    dependencies: Optional[Future] = None,
) -> Future:
    """Trnsfer data asynchronously in a Parsl task

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

    Returns
    -------

    Future
        The future boolean result of the transfer's success or failure
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
def delete_async(
    src_ep: str,
    src_path: str,
    timeout: int = 3600,
    polling_interval: int = 30,
    client: Optional[TransferClient] = None,
    recursive: bool = False,
    dependencies: Optional[Future] = None,
) -> Future:
    """Delete data asynchronously in a Parsl task

    This wraps synchronous Globus data deletion into a Parsl python_app task.
    Calling this function will immediately return a future. The result of the
    future will be True if the deletion completed successfully, or False if
    it did not.

    Parameters
    ----------

    src_ep: str
        Name of the source endpoint for the data to be deletd.  Can be a
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

    Returns
    -------

    Future
        The future boolean result of the deletion's success or failure
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
) -> bool:
    """Trnsfer data synchronously with Globus

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

    Returns
    -------

    bool
        True if the transfer succeeded, False otherwise
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
) -> bool:
    """Delete data synchronously with Globus.

    This deletes data from a Globus endpoint. This function will not return
    until the deletion has completed or failed.

    Parameters
    ----------

    src_ep: str
        Name of the source endpoint for the data to be deletd.  Can be a
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

    Returns
    -------

    bool
        True if the deletion succeeded, False otherwise
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


def retrieve_data(
    *,
    executor,
    yyyymmddhh,
    file_set,
    ics_or_lbcs,
    fcst_hours,
    data_stores,
    data_type,
    file_format,
    output_path=".",
    config_path=None,
    stdout=None,
    stderr=None,
) -> Future:
    """Retrieve the specified data from the specified locations.

    Schedules and executes a workflow task to retrieve data. The type of
    data to retrieve, and the locations from which to retrieve it from
    are given by the tasks arguments. This is a non-blocking call that
    returns a Future representing the eventual result of the data retrieval
    operation.

    Parameters
    ----------

    executor: List[str]
        List of names of executors where the retrieval task may execute.

    yyyymmddhh: str
        Cycle date of the data to be retrieved in YYYYMMDDHH format.

    file_set: str
        Flag for whether analysis, forecast, fix, or observation files should
        be gathered. Must be one of: "anl", "fcst", "obs", "fix"

    fcst_hours: str
        A list describing forecast hours.  If one argument, one fhr will be
        processed.  If 2 or 3 arguments, a sequence of forecast hours
        [start, stop, [increment]] will be processed.  If more than 3
         arguments, the list is processed as-is.

    data_stores: str
        List of priority data stores. Tries the first list item first.
        Choices: hpss, nomads, aws, disk, remote.

    data_type: str
        External model label. This input is case-sensitive. Allowed values
        correspond to keys in the data locations configuration file. Default
        options include: "GFS", "GDAS", "GEFS", "GSMGFS", "RAP", "HRRR",
        "NAM", "UFS-CASE-STUDY", "CCPA_obs", "MRMS_obs", "NDAS_obs",
        "NOHRSC_obs".

    file_format: str
        External model file format. Must be one of "grib2", "nemsio",
        "netcdf", "prepbufr", "tcvitals".

    output_path: str
        Path to location on disk where the retrieved files will be staged.
        Path is expected to exist.

    config_path: str
        Full path to a configuration file containing paths and naming
        conventions for known data streams. The default included in this
        repository is in src/chiltepin/data_locations.yml",

    stdout: str | None
        Full path to the file where stdout of the data retrieval task is to
        be written. If not specified, output to stdout will not be captured.

    stderr: str | None
        Full path to the file where stderr of the data retrieval task is to
        be written. If not specified, output to stderr will not be captured.

    Returns
    -------

    Future
        The future result of the retrieval task's execution.
    """
    # Get path to data retrieval config
    if config_path is None:
        # Use default config
        config_path = str(importlib.resources.path(chiltepin, "data_locations.yml"))

    return _retrieve_data(
        executor=executor,
        yyyymmddhh=yyyymmddhh,
        file_set=file_set,
        ics_or_lbcs=ics_or_lbcs,
        fcst_hours=fcst_hours,
        data_stores=data_stores,
        data_type=data_type,
        file_format=file_format,
        output_path=output_path,
        config_path=config_path,
        stdout=stdout,
        stderr=stderr,
    )

@bash_task
def _retrieve_data(
    *,
    yyyymmddhh,
    file_set,
    ics_or_lbcs,
    fcst_hours,
    data_stores,
    data_type,
    file_format,
    output_path=".",
    config_path,
    stdout=None,
    stderr=None,
) -> str:
    """
    A bash task to Retrieve the specified data from the specified locations.

    Parameters
    ----------

    yyyymmddhh: str
        Cycle date of the data to be retrieved in YYYYMMDDHH format.

    file_set: str
        Flag for whether analysis, forecast, fix, or observation files should
        be gathered. Must be one of: "anl", "fcst", "obs", "fix"

    fcst_hours: str
        A list describing forecast hours.  If one argument, one fhr will be
        processed.  If 2 or 3 arguments, a sequence of forecast hours
        [start, stop, [increment]] will be processed.  If more than 3
         arguments, the list is processed as-is.

    data_stores: str
        List of priority data stores. Tries the first list item first.
        Choices: hpss, nomads, aws, disk, remote.

    data_type: str
        External model label. This input is case-sensitive. Allowed values
        correspond to keys in the data locations configuration file. Default
        options include: "GFS", "GDAS", "GEFS", "GSMGFS", "RAP", "HRRR",
        "NAM", "UFS-CASE-STUDY", "CCPA_obs", "MRMS_obs", "NDAS_obs",
        "NOHRSC_obs".

    file_format: str
        External model file format. Must be one of "grib2", "nemsio",
        "netcdf", "prepbufr", "tcvitals".

    output_path: str
        Path to location on disk where the retrieved files will be staged.
        Path is expected to exist.

    config_path: str
        Full path to a configuration file containing paths and naming
        conventions for known data streams. The default included in this
        repository is in src/chiltepin/data_locations.yml",

    stdout: str | None
        Full path to the file where stdout of the data retrieval task is to
        be written. If not specified, output to stdout will not be captured.

    stderr: str | None
        Full path to the file where stderr of the data retrieval task is to
        be written. If not specified, output to stderr will not be captured.

    Returns
    -------

    str
        A string containing the bash script that implements the data
        retrieval task. This string is consumed by the @bash_task decorator
        that wraps this function to create a workflow task.
    """
    return textwrap.dedent(
        f"""
    set -eux
    export PYTHONUNBUFFERED=1
    retrieve_data \
        --debug \
        --file_set {file_set} \
        --config {config_path} \
        --cycle_date {yyyymmddhh} \
        --data_stores {data_stores} \
        --data_type {data_type} \
        --fcst_hrs {fcst_hours} \
        --file_fmt {file_format} \
        --ics_or_lbcs {ics_or_lbcs} \
        --output_path {output_path}
    """
    )
