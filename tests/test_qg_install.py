import os
import os.path
import pathlib

import parsl
import pytest

import chiltepin.configure
from chiltepin.jedi.qg.wrapper import QG


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()
    yaml_config = chiltepin.configure.parse_file(config_file)
    yaml_config[platform]["resources"]["service"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )
    yaml_config[platform]["resources"]["compute"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )
    resources = chiltepin.configure.load(yaml_config[platform]["resources"], resources=["service", "compute"])

    with parsl.load(resources):
        yield {"resources": resources}
    parsl.clear()


# Test JEDI QG install
def test_qg_install(config):
    pwd = pathlib.Path(__file__).parent.resolve()
    qg = QG(
        install_path=pwd / "jedi-bundle-test",
        tag="develop",
    )

    install_result = qg.install(
        jobs=8,
        stdout=pwd / "qg_install.out",
        stderr=pwd / "qg_install.err",
        clone_executor="service",
        configure_executor="service",
        make_executor="compute",
    ).result()

    assert install_result == 0
    assert os.path.exists(
        pwd / "jedi-bundle-test/jedi-bundle/develop/bin/qg_forecast.x"
    )
    assert os.path.exists(pwd / "jedi-bundle-test/jedi-bundle/develop/bin/qg_hofx.x")
    assert os.path.exists(pwd / "jedi-bundle-test/jedi-bundle/develop/bin/qg_4dvar.x")
