import pathlib
import textwrap

from concurrent.futures import Future
from chiltepin.tasks import bash_task
import chiltepin
import importlib.resources

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
