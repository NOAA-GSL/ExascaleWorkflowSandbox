#!/usr/bin/env python3

import parsl
import sys
import textwrap
import yaml

from chiltepin.config import factory, parse_file
from chiltepin.jedi.qg import install, forecast, hofx
from chiltepin.jedi.qg.config import merge_config, forecast_default

workdir = "/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.qg/tests"

config_file = sys.argv[1]
yaml_config = parse_file(config_file)
resource_config, environment = factory(yaml_config)
parsl.load(resource_config)

# Install JEDI bundle
#install = install.run(environment,
#                      install_path=f"{workdir}",
#                      stdout=f"{workdir}/install.out",
#                      stderr=f"{workdir}/install.err",
#                      tag="develop")

# Make the "truth" forecast configuration
#truth_config = yaml.safe_load(textwrap.dedent(f"""
#               geometry:
#                   nx: 80
#                   ny: 40
#               initial condition:
#                   read_from_file: 0
#               output:
#                   exp: truth
#                   datadir: {workdir}/experiments/QG/truth
#  
#               """).strip())
#
#truth = forecast.run(environment,
#                     install_path=f"{workdir}",
#                     tag="develop",
#                     rundir=f"{workdir}/experiments/QG/truth",
#                     config=truth_config,
#                     stdout=f"{workdir}/truth.out",
#                     stderr=f"{workdir}/truth.err",
#                     install=install)

truth = None

# Create obs for 3dvar
obs = hofx.makeobs3d(environment,
                     install_path=f"{workdir}",
                     tag="develop",
                     rundir=f"{workdir}/experiments/QG/obs",
                     config=yaml.safe_load(textwrap.dedent(f"""
                     geometry:
                       nx: 80
                       ny: 40
                       depths: [4500.0, 5500.0]
                     initial condition:
                       date: "2009-12-31T03:00:00Z"
                       filename: {workdir}/experiments/QG/truth/truth.fc.2009-12-31T00:00:00Z.PT3H.nc
                     model:
                       name: QG
                       tstep: PT10M
                     forecast length: PT6H
                     time window:
                       begin: "2009-12-31T03:00:00Z"
                       length: PT6H
                     observations:
                       observers:
                       - obs operator:
                           obs type: Stream
                         obs space:
                           obsdataout:
                             obsfile: {workdir}/experiments/QG/obs/truth.obs3d.nc
                           obs type: Stream
                           generate:
                             begin: PT2H
                             nval: 1
                             obs density: 100
                             obs error: 4.0e6
                             obs period: PT1H
                       - obs operator:
                           obs type: Wind
                         obs space:
                           obsdataout:
                             obsfile: {workdir}/experiments/QG/obs/truth.obs3d.nc
                           obs type: Wind
                           generate:
                             begin: PT3H
                             nval: 2
                             obs density: 100
                             obs error: 6.0
                             obs period: PT2H
                       - obs operator:
                           obs type: WSpeed
                         obs space:
                           obsdataout:
                             obsfile: {workdir}/experiments/QG/obs//truth.obs3d.nc
                           obs type: WSpeed
                           generate:
                             begin: PT4H
                             nval: 1
                             obs density: 100
                             obs error: 12.0
                             obs period: PT2H
                     make obs: true
                     """).strip()),
                     stdout=f"{workdir}/makeob.out",
                     stderr=f"{workdir}/makeob.err",
                     forecast=truth)

done = obs.result()

parsl.clear

