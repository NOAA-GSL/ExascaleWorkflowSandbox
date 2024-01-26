#!/usr/bin/env python3

import os
import parsl
from parsl.app.app import python_app, bash_app
import re
import sys

from chiltepin.config import factory, parse_file
from chiltepin.jedi.qg import QG

workdir="/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.develop/tests"

config_file = sys.argv[1]
yaml_config = parse_file(config_file)
config, environment = factory(yaml_config)
parsl.load(config)

qgmodel = QG(config, environment)

result = qgmodel.clone(environment,
                       install_path=f"{workdir}",
                       stdout=f"{workdir}/clone.out",
                       stderr=f"{workdir}/clone.err",
                       tag="develop").result()

result = qgmodel.configure(environment,
                           install_path=f"{workdir}",
                           stdout=f"{workdir}/configure.out",
                           stderr=f"{workdir}/configure.err",
                           tag="develop").result()

result = qgmodel.make(environment,
                      install_path=f"{workdir}",
                      stdout=f"{workdir}/make.out",
                      stderr=f"{workdir}/make.err",
                      tag="develop").result()

parsl.clear
