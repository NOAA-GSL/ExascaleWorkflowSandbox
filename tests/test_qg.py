#!/usr/bin/env python3

from datetime import datetime, timedelta
import parsl
import sys
import textwrap

from chiltepin.config import factory, parse_file
from chiltepin.jedi import leadtime
from chiltepin.jedi.qg import install, forecast
from chiltepin.jedi.qg.osse import Experiment

workdir="/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.qg/tests"
experiment = Experiment(textwrap.dedent(f"""
jedi:
  install path: {workdir}
  tag: develop
experiment:
  path: {workdir}/experiments/QG
  begin: "2024-01-01T00:00:00Z"
  length: P1D
  frequency: PT6H
truth:
  nx: 80
  ny: 40
  tstep: PT1M
obs:
  stream:
    begin: PT1H
    period: PT30M
  wind:
    begin: PT2H
    period: PT1H
  wspeed:
    begin: PT1H
    period: PT1H
assimilation:
  window:
    begin: MT3H
    length: PT6H
forecast:
  nx: 40
  ny: 20
  tstep: PT1H
  length: P2D
  frequency: PT1H
""").strip())

exp_begin = datetime.strptime(experiment.config["experiment"]["begin"], "%Y-%m-%dT%H:%M:%SZ")
exp_end = exp_begin + timedelta(0, leadtime.fcst_to_seconds(experiment.config["experiment"]["length"]))

config_file = sys.argv[1]
yaml_config = parse_file(config_file)
resource_config, environment = factory(yaml_config)
parsl.load(resource_config)

# Install JEDI bundle
install = install.run(environment,
                      install_path=experiment.jedi_path,
                      tag=experiment.jedi_tag,
                      stdout=f"{experiment.path}/install_jedi.out",
                      stderr=f"{experiment.path}/install_jedi.err")

# Run the "truth" forecast
truth = experiment.make_truth(environment, install)

# Cycle through experiment analysis times
background = None
analysis = None
t = exp_begin
while (t <= exp_end):
    # Get the cycle date in string format
    t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Running cycle: {t_str}")

    # Run the assimilation (except for first cycle)
    if (t > exp_begin):

        # Create observations for this cycle
        obs = experiment.make_obs(environment, t, truth)

        # Run assimilation for this cycle
        analysis = experiment.run_3dvar(environment, t, obs, background)

    # Run the forecast
    fcst = experiment.run_forecast(environment, t, install, analysis)

    # Set analysis dependency for next cycle
    background = fcst

    # Increment experiment cycle
    t = t + timedelta(0, leadtime.fcst_to_seconds(experiment.config["experiment"]["frequency"]))

# Wait for the experiment to finish
fcst.result()

parsl.clear
