import pathlib
import textwrap

import parsl
from parsl.app.app import bash_app


@bash_app(executors=["service"])
def retrieve_data(
    stdout=None,
    stderr=None,
    ics_or_lbcs="ICS",
    time_offset_hrs=0,
    fcst_len=0,
    lbc_intvl_hrs=6,
    yyyymmddhh=None,
    output_path=".",
):

    # Calculate args for file retrieval script
    path = pathlib.Path(__file__).parent.resolve()
    file_set = "fcst"
    if ics_or_lbcs == "ICS":
        fcst_hours = time_offset_hrs
        if time_offset_hrs == 0:
            file_set = "anl"
    else:
        first_time = time_offset_hrs + lbc_intvl_hrs
        last_time = time_offset_hrs + fcst_len
        fcst_hours = f"{first_time} {last_time} {lbc_intvl_hrs}"

    return textwrap.dedent(
        f"""
    set -eux

    python -u {path}/retrieve_data.py \
        --debug \
        --file_set {file_set} \
        --config {path}/data_locations.yml \
        --cycle_date {yyyymmddhh} \
        --data_stores aws \
        --data_type GFS \
        --fcst_hrs {fcst_hours} \
        --file_fmt grib2 \
        --ics_or_lbcs {ics_or_lbcs} \
        --output_path {output_path}
    """
    )
