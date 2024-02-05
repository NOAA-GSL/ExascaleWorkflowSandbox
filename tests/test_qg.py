#!/usr/bin/env python3

import parsl
import sys
import textwrap
import yaml

from chiltepin.config import factory, parse_file
from chiltepin.jedi.qg import forecast, install

workdir = "/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.develop/tests"

config_file = sys.argv[1]
yaml_config = parse_file(config_file)
config, environment = factory(yaml_config)
parsl.load(config)

# Install JEDI bundle
#install = install.run(environment,
#                      install_path=f"{workdir}",
#                      stdout=f"{workdir}/install.out",
#                      stderr=f"{workdir}/install.err",
#                      tag="develop")
install=None

# Run a "truth" forecast
truth = forecast.run(environment,
                     install_path=f"{workdir}",
                     tag="develop",
                     rundir=f"{workdir}/experiments/QG/truth",
                     config=yaml.safe_load(textwrap.dedent(f"""
                     geometry:
                         nx: 40
                         ny: 20
                     initial condition:
                         read_from_file: 0
                     output:
                         datadir: {workdir}/experiments/QG/truth
                     """).strip()),
                     stdout=f"{workdir}/truth.out",
                     stderr=f"{workdir}/truth.err",
                     install=install)


done = truth.result()

parsl.clear
