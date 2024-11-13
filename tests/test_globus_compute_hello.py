import pathlib
import subprocess

import pytest
from globus_compute_sdk import Executor
from jinja2 import Environment, FileSystemLoader

import chiltepin.configure


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    yaml_config = chiltepin.configure.parse_file(config_file)
    resources = yaml_config[platform]["resources"]
    environment = "\n".join(yaml_config[platform]["environment"])

    return {"resources": resources, "environment": environment}


def test_endpoint_configure(config):
    pwd = pathlib.Path(__file__).parent.resolve()
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "configure",
            "service",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0

    # Customize endpoint configs for this platform using Jinja2 templates
    jinja_env = Environment(loader=FileSystemLoader(f"{pwd}/templates/"))
    for endpoint in ["service"]:
        template = jinja_env.get_template(f"{endpoint}.yaml")
        content = template.render(
            partition=config["resources"][endpoint]["partition"],
            account=config["resources"][endpoint]["account"],
        )
        with open(
            f"{pwd}/globus_compute/{endpoint}/config.yaml", mode="w", encoding="utf-8"
        ) as gc_config:
            gc_config.write(content)


def test_endpoint_start():
    pwd = pathlib.Path(__file__).parent.resolve()
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "start",
            "service",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0


def test_hello_endpoint():
    def hello():
        return "Hello"

    pwd = pathlib.Path(__file__).parent.resolve()
    p = subprocess.run(
        f"globus-compute-endpoint -c {pwd}/globus_compute list | grep service | cut -d' ' -f 2",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
        shell=True,
    )
    assert p.returncode == 0

    hello_endpoint_id = p.stdout.strip()
    assert len(hello_endpoint_id) == 36
    with Executor(endpoint_id=hello_endpoint_id) as gce:
        future = gce.submit(hello)
        assert future.result() == "Hello"


def test_endpoint_stop():
    pwd = pathlib.Path(__file__).parent.resolve()
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "stop",
            "service",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0


def test_endpoint_delete():
    pwd = pathlib.Path(__file__).parent.resolve()
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "delete",
            "--yes",
            "service",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0
