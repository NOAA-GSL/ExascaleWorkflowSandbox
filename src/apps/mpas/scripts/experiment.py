import os

import parsl
import pytest

import chiltepin.configure
from chiltepin.mpas.wrapper import MPAS

# Get resources and platform from command options
config_file = "parm/resources.yml"
platform = "hercules"

# Load Parsl
yaml_config = chiltepin.configure.parse_file(config_file)
resources, environments = chiltepin.configure.factory(yaml_config, platform)
environment = environments[platform]
with parsl.load(resources):

    # Instantiate MPAS object
    mpas = MPAS(
        environment=config["environment"],
        install_path="mpas-model",
        tag="cbba5a4",
    )

    # Clone the MPAS repository
    clone = mpas.clone(
        stdout=("clone.out", "w"),
        stderr=("clone.err", "w"),
    )

    clone.result()

parsl.clear()


