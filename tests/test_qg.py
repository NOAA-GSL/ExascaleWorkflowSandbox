#!/usr/bin/env python3

import parsl
import sys

from chiltepin.config import factory, parse_file
from chiltepin.jedi.qg import QG

workdir = "/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.develop/tests"

config_file = sys.argv[1]
yaml_config = parse_file(config_file)
config, environment = factory(yaml_config)
parsl.load(config)

qgmodel = QG(config, environment)

clone = qgmodel.clone(environment,
                      install_path=f"{workdir}",
                      stdout=f"{workdir}/clone.out",
                      stderr=f"{workdir}/clone.err",
                      tag="develop")

configure = qgmodel.configure(environment,
                              install_path=f"{workdir}",
                              stdout=f"{workdir}/configure.out",
                              stderr=f"{workdir}/configure.err",
                              tag="develop",
                              clone=clone)

make = qgmodel.make(environment,
                    install_path=f"{workdir}",
                    stdout=f"{workdir}/make.out",
                    stderr=f"{workdir}/make.err",
                    tag="develop",
                    configure=configure)

done = make.result()

parsl.clear
