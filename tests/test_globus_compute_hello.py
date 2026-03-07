# SPDX-License-Identifier: Apache-2.0

import logging
import os.path
import pathlib

import pytest

import chiltepin.configure
import chiltepin.endpoint as endpoint
from chiltepin import workflow
from chiltepin.tasks import bash_task, python_task


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file):
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

    # Parse the configuration
    yaml_config = chiltepin.configure.parse_file(config_file)

    # Ensure PYTHONPATH is set in the environment so that pytest
    # can import this test module on the remote workers
    yaml_config["gc-service"]["environment"] = yaml_config["gc-service"][
        "environment"
    ].copy()
    yaml_config["gc-service"]["environment"].append(
        f"export PYTHONPATH=${{PYTHONPATH}}:{pwd.parent.resolve()}"
    )

    # Delete test endpoint if it already exists from a previous test run
    ep_list = endpoint.show(config_dir=f"{output_dir}/.globus_compute")
    if "test" in ep_list:
        endpoint.delete("test", config_dir=f"{output_dir}/.globus_compute", timeout=15)

    # Configure the test endpoint
    endpoint.configure("test", config_dir=f"{output_dir}/.globus_compute", timeout=15)

    # Start the test endpoint
    endpoint.start("test", config_dir=f"{output_dir}/.globus_compute", timeout=15)

    # Update YAML config with the test endpoint id
    ep_info = endpoint.show(config_dir=f"{output_dir}/.globus_compute")
    endpoint_id = ep_info["test"]["id"]
    assert len(endpoint_id) == 36
    yaml_config["gc-service"]["endpoint"] = f"{endpoint_id}"

    # Use workflow context manager for Parsl lifecycle
    with workflow(
        yaml_config,
        include=["gc-service"],
        client=compute_client,
        run_dir=str(output_dir / "test_globus_compute_hello_runinfo"),
        log_file=str(output_dir / "test_globus_compute_hello_parsl.log"),
        log_level=logging.DEBUG,
    ):
        # Run the tests with the loaded resources
        yield {"output_dir": output_dir}

    # Stop the test endpoint now that tests are done
    endpoint.stop("test", config_dir=f"{output_dir}/.globus_compute", timeout=15)

    # Delete the test endpoint
    endpoint.delete("test", config_dir=f"{output_dir}/.globus_compute", timeout=15)


def test_endpoint_hello_python(config):
    @python_task
    def hello():
        return "Hello"

    future = hello(executor=["gc-service"])
    assert future.result() == "Hello"


def test_endpoint_hello_bash(config):
    output_dir = config["output_dir"]

    @bash_task
    def hello():
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
