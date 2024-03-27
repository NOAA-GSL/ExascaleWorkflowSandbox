#!/usr/bin/env python3

import sys
import textwrap

from chiltepin.config import parse_file
from globus_compute_sdk import Client, Executor


def runExperiment(resource_config, exp_config, platform):

    from datetime import datetime, timedelta

    import parsl
    from chiltepin.config import factory
    from chiltepin.jedi import leadtime
    from chiltepin.jedi.qg.osse import Experiment

    resource_config, environments = factory(resource_config, platform)
    environment = environments[platform]

    parsl.load(resource_config)

    experiment = Experiment(exp_config)

    exp_begin = datetime.strptime(
        experiment.config["experiment"]["begin"], "%Y-%m-%dT%H:%M:%SZ"
    )
    exp_end = exp_begin + timedelta(
        0, leadtime.leadtime_to_seconds(experiment.config["experiment"]["length"])
    )

    # Install JEDI bundle
    install = experiment.install_jedi(environment)
    # install = None

    # Run the "truth" forecast
    truth = experiment.make_truth(environment, install)

    # Cycle through experiment analysis times
    background = None
    analysis = None
    t = exp_begin
    while t <= exp_end:
        # Get the cycle date in string format
        t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")

        print(f"Running cycle: {t_str}")

        # Run the assimilation (except for first cycle)
        if t > exp_begin:

            # Create observations for this cycle
            obs = experiment.make_obs(environment, t, truth)

            # Run assimilation for this cycle
            analysis = experiment.run_3dvar(environment, t, obs, background)

        # Run the forecast
        fcst = experiment.run_forecast(environment, t, install, analysis)

        # Set analysis dependency for next cycle
        background = fcst

        # Increment experiment cycle
        t = t + timedelta(
            0, leadtime.leadtime_to_seconds(experiment.config["experiment"]["frequency"])
        )

    # Wait for the experiment to finish
    fcst.result()

    parsl.clear


# Configure the resources
# platform = "hercules"
# platform = "hera"
platform = "chiltepin"
config_file = sys.argv[1]
yaml_config = parse_file(config_file)
# hercules_default = "75056f35-0523-487b-bb90-037dad5756d3"
# hera_default = "37fbbb9e-d676-4615-8bc6-02237c0fd777"
chiltepin_default = "c42e4a3c-7f13-40ab-a270-f997b5f2c1fa"

# Configure the experiment
# workdir = "/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.qg/tests"
# workdir = "/scratch2/BMC/gsd-hpcs/Christopher.W.Harrop/SENA/ExascaleWorkflowSandbox.qg/tests"
workdir = "/home/admin/chiltepin/tests"
exp_config = textwrap.dedent(
    f"""
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
"""
).strip()

# Run the experiment
with Executor(endpoint_id=chiltepin_default) as gce:
    future = gce.submit(runExperiment, yaml_config, exp_config, platform)
    future.result()
