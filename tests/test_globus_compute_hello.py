import logging
import os.path
import pathlib

import parsl
import pytest
import yaml
from jinja2 import BaseLoader, Environment

import chiltepin.configure
import chiltepin.endpoint as endpoint
from chiltepin.tasks import bash_task, python_task


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Create directory for test output
    output_dir = pwd / "test_output"
    output_dir.mkdir(exist_ok=True)

    # Make sure we are logged in
    if endpoint.login_required():
        raise RuntimeError("Chiltepin login is required")

    # Get compute client
    clients = endpoint.login()
    compute_client = clients["compute"]

    # Parse the configuration for the chosen platform
    yaml_config = chiltepin.configure.parse_file(config_file)
    resource_config = yaml_config[platform]["resources"]

    # Ensure PYTHONPATH is set in the environment so that pytest
    # can import this test module on the remote workers
    resource_config["gc-service"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )

    # Delete test endpoint if it already exists from a previous test run
    ep_list = endpoint.show(config_dir=f"{output_dir}/.globus_compute")
    if "test" in ep_list:
        endpoint.delete("test", config_dir=f"{output_dir}/.globus_compute", timeout=15)

    # Configure the test endpoint
    endpoint.configure("test", config_dir=f"{output_dir}/.globus_compute", timeout=15)

    # Start the test endpoint
    endpoint.start("test", config_dir=f"{output_dir}/.globus_compute", timeout=15)

    # Update resource config with the test endpoint id
    resource_config = _set_endpoint_ids(resource_config, output_dir)

    # Set Parsl logging to DEBUG and redirect to a file in the output directory
    logger_handler = parsl.set_file_logger(
        filename=str(output_dir / "test_globus_compute_hello_parsl.log"),
        level=logging.DEBUG,
    )

    # Load the finalized resource configuration
    resources = chiltepin.configure.load(
        resource_config,
        include=["gc-service"],
        client=compute_client,
        run_dir=str(output_dir / "test_globus_compute_hello_runinfo"),
    )

    # Load the resources in Parsl
    dfk = parsl.load(resources)

    # Run the tests with the loaded resources
    yield {"output_dir": output_dir}

    # Cleanup Parsl after tests are done
    dfk.cleanup()
    dfk = None
    parsl.clear()
    logger_handler()

    # Stop the test endpoint now that tests are done
    endpoint.stop("test", config_dir=f"{output_dir}/.globus_compute", timeout=15)

    # Delete the test endpoint
    endpoint.delete("test", config_dir=f"{output_dir}/.globus_compute", timeout=15)


# Set endpoint ids in configuration
def _set_endpoint_ids(resource_config, output_dir):
    # Set endpoint id in resource config using Jinja2 templates
    ep_info = endpoint.show(config_dir=f"{output_dir}/.globus_compute")
    endpoint_id = ep_info["test"]["id"]
    assert len(endpoint_id) == 36

    config_string = yaml.dump(resource_config)
    template = Environment(loader=BaseLoader()).from_string(config_string)
    content = template.render(service_endpoint_id=endpoint_id)
    content_yaml = yaml.safe_load(content)
    return content_yaml


def test_endpoint_hello_python(config):
    @python_task
    def hello():
        return "Hello"

    future = hello(executor=["gc-service"])
    assert future.result() == "Hello"


def test_endpoint_hello_bash(config):
    output_dir = config["output_dir"]

    @bash_task
    def hello(stdout=None, stderr=None):
        return "echo Hello"

    # Remove previous test output if it exists
    if os.path.exists(output_dir / "test_endpoint_hello_bash.out"):
        os.remove(output_dir / "test_endpoint_hello_bash.out")
    if os.path.exists(output_dir / "test_endpoint_hello_bash.err"):
        os.remove(output_dir / "test_endpoint_hello_bash.err")

    future = hello(
        stdout=os.path.join(output_dir, "test_endpoint_hello_bash.out"),
        stderr=os.path.join(output_dir, "test_endpoint_hello_bash.err"),
        executor=["gc-service"],
    )

    # Verify exit status is 0
    assert future.result() == 0

    # Check output
    with open(output_dir / "test_endpoint_hello_bash.out", "r") as f:
        content = f.read().strip()
        assert content == "Hello"
