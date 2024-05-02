import os

import parsl
import pytest

import chiltepin.configure
from chiltepin.jedi.qg.wrapper import QG


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    yaml_config = chiltepin.configure.parse_file(config_file)
    resources, environments = chiltepin.configure.factory(yaml_config, platform)
    environment = environments[platform]
    with parsl.load(resources):
        yield {"resources": resources, "environment": environment}
    parsl.clear()


# Test JEDI QG install
def test_qg_install(config):

    qg = QG(
        environment=config["environment"],
        install_path="jedi-bundle-test",
        tag="develop",
    )

    install_result = qg.install(
        jobs=8,
        stdout="qg_install.out",
        stderr="qg_install.err",
        clone_executors=["service"],
        configure_executors=["service"],
        make_executors=["serial"],
    ).result()

    assert install_result == 0
    assert os.path.exists("jedi-bundle-test/jedi-bundle/develop/bin/qg_forecast.x")
    assert os.path.exists("jedi-bundle-test/jedi-bundle/develop/bin/qg_hofx.x")
    assert os.path.exists("jedi-bundle-test/jedi-bundle/develop/bin/qg_4dvar.x")
