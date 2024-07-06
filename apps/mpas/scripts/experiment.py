import os

import parsl
import pytest

import chiltepin.configure
from chiltepin.mpas.wrapper import MPAS
from chiltepin.wrf.wrapper import WRF
from chiltepin.wps.wrapper import WPS
from chiltepin.metis.wrapper import Metis
from chiltepin.utils.chiltepin_get_data import retrieve_data

from shutil import copy

# Get resources and platform from command options
config_file = "../parm/resources.yml"
platform = "hercules"

# Load Parsl
yaml_config = chiltepin.configure.parse_file(config_file)
resources, environments = chiltepin.configure.factory(yaml_config, platform)
environment = environments[platform]
with parsl.load(resources):

    # Instantiate MPAS object
    mpas = MPAS(
        environment=environment,
        install_path="../",
        tag="cbba5a4",
    )
    #
    ## Install MPAS
    #install_mpas = mpas.install(
    #    stdout="install_mpas.out",
    #    stderr="install_mpas.err",
    #)
    #
    #
    # Instantiate WRF object
    #wrf = WRF(
    #    environment=environment,
    #    install_path="../",
    #    tag="4.6.0",
    #)
    #
    ## Intall WRF
    #install_wrf = wrf.install(
    #    stdout="install_wrf.out",
    #    stderr="install_wrf.err",
    #)
    #
    # Instantiate WPS object
    wps = WPS(
        environment=environment,
        install_path="../",
        tag="4.6.0",
    )

    ## Intall WPS
    #install_wps = wps.install(
    #    stdout="install_wps.out",
    #    stderr="install_wps.err",
    #    WRF_dir=None,
    #)

    ## Instantiate Metis object
    #metis = Metis(
    #    environment=environment,
    #    install_path="/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.mpas-app-skeleton/apps/mpas",
    #    tag="5.1.0",
    #)

    ## Intall Metis
    #install_metis = metis.install(
    #    stdout="install_metis.out",
    #    stderr="install_metis.err",
    #)

    #install_mpas.result()
    #install_wrf.result()
    #install_wps.result()
    #install_metis.result()

    # Set up mesh files
    #mesh_file_path = "/work/noaa/gsd-hpcs/charrop/mpas/mpas-dev/test-mesh/conus.graph.info"
    #copy(src=mesh_file_path, dst=".")
    #gpm = metis.gpmetis("conus.graph.info", 4, stdout="gpmetis_4.out", stderr="gpmetis_4.err")
    #gpm.result()
    #copy(src=mesh_file_path, dst=".")
    #gpm = metis.gpmetis("conus.graph.info", 32, stdout="gpmetis_32.out", stderr="gpmetis_32.err")
    #gpm.result()
    #
    #ics = retrieve_data(stdout="get_ics.out",
    #                    stderr="get_ics.err",
    #                    ics_or_lbcs="ICS",
    #                    time_offset_hrs=0,
    #                    fcst_len=24,
    #                    lbc_intvl_hrs=6,
    #                    yyyymmddhh="2024070300",
    #                    output_path=".")
    #lbcs = retrieve_data(stdout="get_lbcs.out",
    #                     stderr="get_lbcs.err",
    #                     ics_or_lbcs="LBCS",
    #                     time_offset_hrs=0,
    #                     fcst_len=24,
    #                     lbc_intvl_hrs=6,
    #                     yyyymmddhh="2024070300",
    #                     output_path=".")
    #ics.result()
    #lbcs.result()

    #ungrib = wps.ungrib("./experiment.yml",
    #                    "2024-07-03T00:00:00",
    #                    stdout="ungrib.out",
    #                    stderr="ungrib.err")
    #
    #ungrib.result()

    mpas_init = mpas.mpas_init("./experiment.yml",
                        "2024-07-03T00:00:00",
                        stdout="mpas_init.out",
                        stderr="mpas_init.err")

    mpas_init.result()

parsl.clear()
