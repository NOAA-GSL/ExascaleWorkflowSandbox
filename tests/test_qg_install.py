import os

import parsl
import pytest

import chiltepin.config
from chiltepin.jedi.qg import install


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def conf(config_file, platform):
    yaml_config = chiltepin.config.parse_file(config_file)
    resource_config, environments = chiltepin.config.factory(yaml_config, platform)
    environment = environments[platform]
    with parsl.load(resource_config):
        yield {"config": resource_config, "environment": environment}
    parsl.clear()


# Test JEDI QG install
def test_qg_install(conf):
    install_future = install.run(
        install_path="./jedi-bundle-test",
        tag="develop",
        jobs=8,
        stdout=("qg_install.out", "w"),
        stderr=("qg_install.err", "w"),
        environment=conf["environment"],
    ).result()
    assert install_future == 0
    assert os.path.exists("jedi-bundle-test/jedi-bundle/develop/bin/qg_forecast.x")
    assert os.path.exists("jedi-bundle-test/jedi-bundle/develop/bin/qg_hofx.x")
    assert os.path.exists("jedi-bundle-test/jedi-bundle/develop/bin/qg_4dvar.x")
