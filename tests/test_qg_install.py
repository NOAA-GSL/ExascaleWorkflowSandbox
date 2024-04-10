import parsl
import pytest

import chiltepin.config
from chiltepin.jedi.qg import install


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def load_config(config_file, platform, request):
    yaml_config = chiltepin.config.parse_file(config_file)
    resource_config, environments = chiltepin.config.factory(yaml_config, platform)
    environment = environments[platform]
    parsl.load(resource_config)
    request.addfinalizer(parsl.clear)
    return {"config": resource_config, "environment": environment}


# Test JEDI QG install
def test_qg_install(load_config):
    install_future = install.run(
        install_path="./jedi-bundle-test",
        tag="develop",
        jobs=8,
        stdout=("qg_install.out", "w"),
        stderr=("qg_install.err", "w"),
        environment=load_config["environment"],
    ).result()
    assert install_future == 0
