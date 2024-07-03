import parsl
from parsl.app.app import bash_app 
import pathlib

@bash_app(executors=["service"])
def retrieve_data(stdout=None, stderr=None, ICS_or_LBCS="ICS", TIME_OFFSET_HRS=0, FCST_LEN=0, LBC_INTVL_HRS=6, 
                  YYYYMMDDHH=None, OUTPUT_PATH="."):
    path = pathlib.Path(__file__).parent.resolve()
    return f"""
    set -eu

file_set=fcst
if [[ {ICS_or_LBCS} == "ICS" ]] ; then
  fcst_hours={TIME_OFFSET_HRS}
  if [[ {TIME_OFFSET_HRS} -eq 0 ]] ; then
    file_set=anl
  fi
else
  ((first_time={TIME_OFFSET_HRS} + {LBC_INTVL_HRS}))
  ((last_time={TIME_OFFSET_HRS} + {FCST_LEN}))
  fcst_hours="$first_time $last_time {LBC_INTVL_HRS}"
fi

set -x
python -u {path}/retrieve_data.py \
    --debug \
    --file_set $file_set \
    --config {path}/data_locations.yml \
    --cycle_date {YYYYMMDDHH} \
    --data_stores aws \
    --data_type GFS \
    --fcst_hrs $fcst_hours \
    --file_fmt grib2 \
    --ics_or_lbcs {ICS_or_LBCS} \
    --output_path {OUTPUT_PATH}
    """
