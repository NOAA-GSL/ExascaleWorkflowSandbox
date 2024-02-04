#!/usr/bin/env python3

import parsl
import sys
import yaml

from chiltepin.config import factory, parse_file
from chiltepin.jedi.qg import forecast, install

workdir = "/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.develop/tests"

config_file = sys.argv[1]
yaml_config = parse_file(config_file)
config, environment = factory(yaml_config)
parsl.load(config)

# Install JEDI bundle
install = install.run(environment,
                      install_path=f"{workdir}",
                      stdout=f"{workdir}/install.out",
                      stderr=f"{workdir}/install.err",
                      tag="develop")

# Run a "truth" forecast
truth = forecast.run(environment,
                     install_path=f"{workdir}",
                     workdir=f"{workdir}/experiments/QG/truth",
                     nx=80, ny=40,
                     stdout=f"{workdir}/truth.out",
                     stderr=f"{workdir}/truth.err",
                     tag="develop",
                     install=install)

done = truth.result()

parsl.clear
