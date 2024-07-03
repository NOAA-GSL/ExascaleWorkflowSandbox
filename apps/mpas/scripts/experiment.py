import os

import parsl
import pytest

import chiltepin.configure
from chiltepin.mpas.wrapper import MPAS
from chiltepin.utils.chiltepin_get_data import retrieve_data

# Get resources and platform from command options
config_file = "../parm/resources.yml"
platform = "hercules"

# Load Parsl
yaml_config = chiltepin.configure.parse_file(config_file)
resources, environments = chiltepin.configure.factory(yaml_config, platform)
environment = environments[platform]
with parsl.load(resources):

    ## Instantiate MPAS object
    #mpas = MPAS(
    #    environment=environment,
    #    install_path="../",
    #    tag="cbba5a4",
    #)
    #
    ## Install MPAS
    #install_mpas = mpas.install(
    #    stdout="install_mpas.out",
    #    stderr="install_mpas.err",
    #)
    #
    #
    ## Instantiate WRF object
    #wrf = WRF(
    #    environment=environment,
    #    install_path="../",
    #    tag="cbba5a4",
    #)
    #
    ## Intall WRF
    #install_mpas = wrf.install(
    #    stdout="install_wrf.out",
    #    stderr="install_wrf.err",
    #)
    #
    #install_mpas.result()
    #install_wrf.result()


    ics = retrieve_data(stdout="get_ics.out",
                        stderr="get_ics.err",
                        ics_or_lbcs="ICS",
                        time_offset_hrs=0,
                        fcst_len=24,
                        lbc_intvl_hrs=6,
                        yyyymmddhh="2024070300",
                        output_path=".")
    lbcs = retrieve_data(stdout="get_lbcs.out",
                         stderr="get_lbcs.err",
                         ics_or_lbcs="LBCS",
                         time_offset_hrs=0,
                         fcst_len=24,
                         lbc_intvl_hrs=6,
                         yyyymmddhh="2024070300",
                         output_path=".")
    ics.result()
    lbcs.result()

parsl.clear()


