import pathlib
import subprocess

import parsl
from chiltepin.tasks import python_task
import pytest
from globus_compute_sdk import Executor
from jinja2 import BaseLoader, Environment, FileSystemLoader
import yaml

import chiltepin.configure


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()
    yaml_config = chiltepin.configure.parse_file(config_file)
    yaml_config[platform]["resources"]["gc-service"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )
    resources = yaml_config[platform]["resources"]
    return resources


def test_endpoint_configure(config):
    pwd = pathlib.Path(__file__).parent.resolve()
    endpoint = "gc-service"
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "configure",
            f"{endpoint}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0

    # Customize endpoint configs for this platform using Jinja2 templates
    jinja_env = Environment(loader=FileSystemLoader(f"{pwd}/templates/"))
    template = jinja_env.get_template(f"{endpoint}.yaml")
    content = template.render(
        partition=config[endpoint]["partition"],
        account=config[endpoint]["account"],
        worker_init=";".join(config[endpoint]["environment"])
    )
    with open(
        f"{pwd}/globus_compute/{endpoint}/config.yaml", mode="w", encoding="utf-8"
    ) as gc_config:
        gc_config.write(content)


def test_endpoint_start():
    pwd = pathlib.Path(__file__).parent.resolve()
    endpoint = "gc-service"
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "start",
            f"{endpoint}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0


def test_hello_endpoint(config):
    @python_task
    def hello():
        return "Hello"

    pwd = pathlib.Path(__file__).parent.resolve()
    endpoint = "gc-service"
    p = subprocess.run(
        f"globus-compute-endpoint -c {pwd}/globus_compute list | grep {endpoint} | cut -d' ' -f 2",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
        shell=True,
    )
    assert p.returncode == 0
    hello_endpoint_id = p.stdout.strip()
    assert len(hello_endpoint_id) == 36

    config_string = yaml.dump(config)
    template = Environment(loader=BaseLoader()).from_string(config_string)
    content = template.render(
        service_endpoint_id=hello_endpoint_id
    )

    content_yaml = yaml.safe_load(content)
    resources = chiltepin.configure.load(content_yaml, resources=[endpoint])
    with parsl.load(resources):
        future = hello(executor=endpoint)
        assert future.result() == "Hello"

def test_endpoint_stop():
    pwd = pathlib.Path(__file__).parent.resolve()
    endpoint = "gc-service"
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "stop",
            f"{endpoint}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0


def test_endpoint_delete():
    pwd = pathlib.Path(__file__).parent.resolve()
    endpoint = "gc-service"
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "delete",
            "--yes",
            f"{endpoint}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0
