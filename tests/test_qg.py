#!/usr/bin/env python3

from datetime import datetime, timedelta
import parsl
import sys
import textwrap
import yaml

from chiltepin.config import factory, parse_file
from chiltepin.jedi import leadtime
from chiltepin.jedi.qg import install, forecast, hofx
from chiltepin.jedi.qg.config import merge_config, forecast_default, makeobs3d_default

def configure_truth(exp_path, t):
    truth_config = forecast_default()
    truth_config["geometry"]["nx"] = 80
    truth_config["geometry"]["ny"] = 40
    truth_config["initial condition"]["date"] = t.strftime("%Y-%m-%dT%H:%M:%SZ")
    truth_config["initial condition"]["read_from_file"] = 0
    truth_config["output"]["exp"] = "truth"
    truth_config["output"]["datadir"] = f"{exp_path}/truth"
    return truth_config

def configure_makeobs(exp_path, t, exp_start, window_offset, window_length):
    window_begin = t + timedelta(0, leadtime.fcst_to_seconds(window_offset))
    truth_leadtime = leadtime.seconds_to_fcst(int((window_begin - exp_start).total_seconds()))
    makeobs_config = makeobs3d_default()
    makeobs_config["geometry"]["nx"] = 80
    makeobs_config["geometry"]["ny"] = 40
    makeobs_config["initial condition"]["date"] = window_begin.strftime("%Y-%m-%dT%H:%M:%SZ")
    makeobs_config["initial condition"]["filename"] = f"{workdir}/experiments/QG/truth/truth.fc.{exp_start.strftime('%Y-%m-%dT%H:%M:%SZ')}.{truth_leadtime}.nc"
    makeobs_config["forecast length"] = window_length
    makeobs_config["time window"]["begin"] = window_begin.strftime("%Y-%m-%dT%H:%M:%SZ")
    makeobs_config["time window"]["length"] = window_length
    for observer in makeobs_config["observations"]["observers"]:
        obsfile = f'{exp_path}/forecast/{t.strftime("%Y-%m-%dT%H:%M:%SZ")}/qg.truth.3d.{t.strftime("%Y-%m-%dT%H:%M:%SZ")}.nc'
        observer["obs space"]["obsdataout"]["obsfile"] = obsfile
        if (observer["obs operator"]["obs type"] == "Stream"):
            observer["obs space"]["generate"]["begin"] = "PT1H"
            observer["obs space"]["generate"]["obs period"] = "PT30M"
        elif (observer["obs operator"]["obs type"] == "Wind"):
            observer["obs space"]["generate"]["begin"] = "PT2H"
            observer["obs space"]["generate"]["obs period"] = "PT1H"
        elif (observer["obs operator"]["obs type"] == "WSpeed"):
            observer["obs space"]["generate"]["begin"] = "PT1H"
            observer["obs space"]["generate"]["obs period"] = "PT1H"
    return makeobs_config

workdir = "/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.qg/tests"

config_file = sys.argv[1]
yaml_config = parse_file(config_file)
resource_config, environment = factory(yaml_config)
parsl.load(resource_config)

# Set up experiment parameters
exp_start_str = "2024-01-01T00:00:00Z"
exp_start_date = datetime.strptime(exp_start_str, "%Y-%m-%dT%H:%M:%SZ")
exp_length = leadtime.fcst_to_seconds("P1D")
exp_freq = leadtime.fcst_to_seconds("PT6H")
exp_end_date = exp_start_date + timedelta(0, exp_length) - timedelta(0, exp_freq)

# Install JEDI bundle
#install = install.run(environment,
#                      install_path=f"{workdir}",
#                      stdout=f"{workdir}/install.out",
#                      stderr=f"{workdir}/install.err",
#                      tag="develop")

install = None

# Run the "truth" forecast
truth = forecast.run(environment,
                     install_path=f"{workdir}",
                     tag="develop",
                     rundir=f"{workdir}/experiments/QG/truth",
                     config=configure_truth(f"{workdir}/experiments/QG", exp_start_date),
                     stdout=f"{workdir}/truth.out",
                     stderr=f"{workdir}/truth.err",
                     install=install)

# Run each cycle of the experiment
t = exp_start_date
obs=[]
while (t <= exp_end_date):

    # Get the cycle date in string format
    t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Running cycle: {t_str}")

    # Create obs for 3dvar
    if (t > exp_start_date):
        obs.append(hofx.makeobs3d(environment,
                                  install_path=f"{workdir}",
                                  tag="develop",
                                  rundir=f"{workdir}/experiments/QG/forecast/{t.strftime('%Y-%m-%dT%H:%M:%SZ')}",
                                  config=configure_makeobs(f"{workdir}/experiments/QG", t, exp_start_date, "MT3H", "PT6H"),
                                  stdout=f"{workdir}/makeobs.2024-01-01T06:00:00Z.out",
                                  stderr=f"{workdir}/makeobs.2024-01-01T06:00:00Z.err",
                                  forecast=truth))

# Run 3dvar
#var3d = variational.var3d(environment,
#                          install_path=f"{workdir}",
#                          tag="develop",
#                          rundir=f"{workdir}/experiments/QG/obs",
#                          config=configure_var3d(f"{workdir}/experiments/QG", t, exp_start_date, "MT3H", "PT6H")
#                          stdout=f"{workdir}/makeob.out",
#                          stderr=f"{workdir}/makeob.err",
#                          forecast=truth)

    t = t + timedelta(0, exp_freq)

for ob in obs:
    done = ob.result()

parsl.clear

