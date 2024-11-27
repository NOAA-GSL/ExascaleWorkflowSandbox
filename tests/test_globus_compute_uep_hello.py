import pathlib

import parsl
import pytest
import yaml
from jinja2 import BaseLoader, Environment, FileSystemLoader

import chiltepin.configure
import chiltepin.endpoint as endpoint
from chiltepin.tasks import python_task


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Parse the configuration for the chosen platform
    yaml_config = chiltepin.configure.parse_file(config_file)
    resource_config = yaml_config[platform]["resources"]

    # Ensure PYTHONPATH is set in the environment so that pytest
    # can import this test module on the remote workers
    resource_config["gc-service"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )

    # Configure the test endpoint
    endpoint.configure("gc-service", config_dir=f"{pwd}/.globus_compute")

    # Apply endpoint configuration template for the chosen platform
    _apply_endpoint_template(resource_config)

    # Start the test endpoint
    endpoint.start("gc-service", config_dir=f"{pwd}/.globus_compute")

    # Update resource config with the test endpoint id
    resource_config = _set_endpoint_ids(resource_config)

    # Load the finalized resource configuration
    resources = chiltepin.configure.load(resource_config, resources=["gc-service"])

    # Run the tests with the loaded resources
    with parsl.load(resources):
        yield

    # Stop the test endpoint now that tests are done
    endpoint.stop("gc-service", config_dir=f"{pwd}/.globus_compute")

    # Delete the test endpoint
    endpoint.delete("gc-service", config_dir=f"{pwd}/.globus_compute")


def _apply_endpoint_template(config):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Customize endpoint configs for this platform using Jinja2 templates
    jinja_env = Environment(loader=FileSystemLoader(f"{pwd}/templates/"))
    for name in ["gc-service"]:
        template = jinja_env.get_template(f"{name}.yaml")
        content = template.render(
            partition=config[name]["partition"],
            account=config[name]["account"],
            worker_init=";".join(config[name]["environment"]),
        )
        with open(
            f"{pwd}/.globus_compute/{name}/config.yaml", mode="w", encoding="utf-8"
        ) as gc_config:
            gc_config.write(content)


# Set endpoint ids in configuration
def _set_endpoint_ids(config):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Set endpoint id in resource config using Jinja2 tempates
    ep_list = endpoint.list(config_dir=f"{pwd}/.globus_compute")
    endpoint_id = ep_list["gc-service"]["id"]
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

    future = hello(executor="gc-service")
    assert future.result() == "Hello"
