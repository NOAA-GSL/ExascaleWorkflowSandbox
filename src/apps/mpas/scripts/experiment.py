import os

import parsl
import pytest

import chiltepin.configure
import chiltepin.utils
from chiltepin.mpas.wrapper import MPAS

# Get resources and platform from command options
config_file = "../parm/resources.yml"
platform = "hercules"

# Load Parsl
yaml_config = chiltepin.configure.parse_file(config_file)
resources, environments = chiltepin.configure.factory(yaml_config, platform)
environment = environments[platform]
with parsl.load(resources):
    r = chiltein.utils.retrieve_data(stdout="get_ics.out", stderr="get_ics.err", ICS_or_LBCS="ICS", TIME_OFFSET_HRS=0, FCST_LEN=24, LBC_INTVL_HRS=6, YYYYMMDDHH="2024070300", OUTPUT_PATH=".")
    r.result()
#    # Instantiate MPAS object
#    mpas = MPAS(
#        environment=environment,
#        install_path="../",
#        tag="cbba5a4",
#    )
#
#    # Clone the MPAS repository
#    install_mpas = mpas.install(
#        #stdout=("install_mpas.out", "w"),
#        #stderr=("install_mpas.err", "w"),
#        stdout="install_mpas.out",
#        stderr="install_mpas.err",
#    )
#
#    install_mpas.result()

parsl.clear()


