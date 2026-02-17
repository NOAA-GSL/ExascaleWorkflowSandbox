import pathlib

import parsl
import pytest
import yaml
from jinja2 import BaseLoader, Environment

import chiltepin.configure
import chiltepin.endpoint as endpoint
from chiltepin.tasks import python_task


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()

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

    # Configure the test endpoint
    endpoint.configure("test", config_dir=f"{pwd}/.globus_compute")

    # Start the test endpoint
    endpoint.start("test", config_dir=f"{pwd}/.globus_compute")

    # Update resource config with the test endpoint id
    resource_config = _set_endpoint_ids(resource_config)

    # Load the finalized resource configuration
    resources = chiltepin.configure.load(
        resource_config,
        include=["gc-service"],
        client=compute_client,
    )

    # Load the resources in Parsl
    dfk = parsl.load(resources)

    # Run the tests with the loaded resources
    yield

    # Cleanup Parsl after tests are done
    dfk.cleanup()
    dfk = None
    parsl.clear()

    # Stop the test endpoint now that tests are done
    endpoint.stop("test", config_dir=f"{pwd}/.globus_compute", timeout=15)

    # Delete the test endpoint
    endpoint.delete("test", config_dir=f"{pwd}/.globus_compute", timeout=15)


# Set endpoint ids in configuration
def _set_endpoint_ids(config):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Set endpoint id in resource config using Jinja2 tempates
    ep_info = endpoint.show(config_dir=f"{pwd}/.globus_compute")
    endpoint_id = ep_info["test"]["id"]
    assert len(endpoint_id) == 36

    config_string = yaml.dump(config)
    template = Environment(loader=BaseLoader()).from_string(config_string)
    content = template.render(service_endpoint_id=endpoint_id)
    content_yaml = yaml.safe_load(content)
    return content_yaml


def test_hello_endpoint(config):
    @python_task
    def hello():
        return "Hello"

    future = hello(executor=["gc-service"])
    assert future.result() == "Hello"
