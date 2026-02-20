import logging
import os.path
import pathlib
import re
from datetime import datetime as dt

import parsl
import pytest
import yaml
from jinja2 import BaseLoader, Environment

import chiltepin.configure
import chiltepin.endpoint as endpoint
from chiltepin.tasks import bash_task


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
    resource_config["gc-compute"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )
    resource_config["gc-mpi"]["environment"].append(
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

    # Update resource config with the test endpoint ids
    resource_config = _set_endpoint_ids(resource_config, output_dir)

    # Set Parsl logging to DEBUG and redirect to a file in the output directory
    logger_handler = parsl.set_file_logger(
        filename=str(output_dir / "test_globus_compute_mpi_parsl.log"),
        level=logging.DEBUG,
    )

    # Load the finalized resource configuration
    resources = chiltepin.configure.load(
        resource_config,
        include=["gc-compute", "gc-mpi"],
        client=compute_client,
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
    # Get a listing of the endpoints
    ep_info = endpoint.show(config_dir=f"{output_dir}/.globus_compute")
    endpoint_id = ep_info["test"]["id"]
    assert len(endpoint_id) == 36

    config_string = yaml.dump(resource_config)
    template = Environment(loader=BaseLoader()).from_string(config_string)
    content = template.render(
        compute_endpoint_id=endpoint_id,
        mpi_endpoint_id=endpoint_id,
    )
    content_yaml = yaml.safe_load(content)
    return content_yaml


# Test endpoint use
def test_endpoint_hello_mpi(config):
    output_dir = config["output_dir"]

    # Define a bash task to compile the MPI code
    @bash_task
    def compile_func(
        dirpath,
        stdout=None,
        stderr=None,
    ):
        return f"""
        cd {dirpath}
        $CHILTEPIN_MPIF90 -o mpi_hello.exe ../mpi_hello.f90
        """

    # Define a bash task to run the MPI program
    @bash_task
    def hello_func(
        dirpath,
        stdout=None,
        stderr=None,
        parsl_resource_specification=None,
    ):
        return f"""
        cd {dirpath}
        $PARSL_MPI_PREFIX --overcommit ./mpi_hello.exe
        """

    # Remove any previous output if necessary
    if os.path.exists(output_dir / "test_endpoint_hello_mpi_compile.out"):
        os.remove(output_dir / "test_endpoint_hello_mpi_compile.out")
    if os.path.exists(output_dir / "test_endpoint_hello_mpi_compile.err"):
        os.remove(output_dir / "test_endpoint_hello_mpi_compile.err")
    if os.path.exists(output_dir / "test_endpoint_hello_mpi_run.out"):
        os.remove(output_dir / "test_endpoint_hello_mpi_run.out")
    if os.path.exists(output_dir / "test_endpoint_hello_mpi_run.err"):
        os.remove(output_dir / "test_endpoint_hello_mpi_run.err")

    future = compile_func(
        output_dir,
        stdout=os.path.join(output_dir, "test_endpoint_hello_mpi_compile.out"),
        stderr=os.path.join(output_dir, "test_endpoint_hello_mpi_compile.err"),
        executor=["gc-compute"],
    )
    r = future.result()
    assert r == 0
    assert os.path.isfile(output_dir / "mpi_hello.exe")
    assert os.stat(output_dir / "test_endpoint_hello_mpi_compile.out").st_size == 0

    future = hello_func(
        output_dir,
        stdout=os.path.join(output_dir, "test_endpoint_hello_mpi_run.out"),
        stderr=os.path.join(output_dir, "test_endpoint_hello_mpi_run.err"),
        executor=["gc-mpi"],
        parsl_resource_specification={
            "num_nodes": 3,  # Number of nodes required for the application instance
            "num_ranks": 6,  # Number of ranks in total
            "ranks_per_node": 2,  # Number of ranks / application elements to be launched per node
        },
    )
    r = future.result()
    assert r == 0

    # Check output
    with open(output_dir / "test_endpoint_hello_mpi_run.out", "r") as f:
        for line in f:
            assert re.match(r"Hello world from host \S+, rank \d+ out of 6", line)


# Test endpoint use
def test_endpoint_pi_mpi(config):
    output_dir = config["output_dir"]

    # Define a bash task to compile the MPI code
    @bash_task
    def compile_func(dirpath, stdout=None, stderr=None):
        return f"""
        cd {dirpath}
        $CHILTEPIN_MPIF90 -o mpi_pi.exe ../mpi_pi.f90
        """

    # Define a bash task to run the MPI program
    @bash_task
    def pi_func(dirpath, stdout=None, stderr=None, parsl_resource_specification=None):
        return f"""
        cd {dirpath}
        $PARSL_MPI_PREFIX --overcommit ./mpi_pi.exe
        """

    # Remove any previous output if necessary
    if os.path.exists(output_dir / "test_endpoint_pi_mpi_compile.out"):
        os.remove(output_dir / "test_endpoint_pi_mpi_compile.out")
    if os.path.exists(output_dir / "test_endpoint_pi_mpi_compile.err"):
        os.remove(output_dir / "test_endpoint_pi_mpi_compile.err")
    if os.path.exists(output_dir / "test_endpoint_pi_mpi_run1.out"):
        os.remove(output_dir / "test_endpoint_pi_mpi_run1.out")
    if os.path.exists(output_dir / "test_endpoint_pi_mpi_run1.err"):
        os.remove(output_dir / "test_endpoint_pi_mpi_run1.err")
    if os.path.exists(output_dir / "test_endpoint_pi_mpi_run2.out"):
        os.remove(output_dir / "test_endpoint_pi_mpi_run2.out")
    if os.path.exists(output_dir / "test_endpoint_pi_mpi_run2.err"):
        os.remove(output_dir / "test_endpoint_pi_mpi_run2.err")

    cores_per_node = 8
    future = compile_func(
        output_dir,
        stdout=os.path.join(output_dir, "test_endpoint_pi_mpi_compile.out"),
        stderr=os.path.join(output_dir, "test_endpoint_pi_mpi_compile.err"),
        executor=["gc-compute"],
    )
    r = future.result()
    assert r == 0
    assert os.path.isfile(output_dir / "mpi_pi.exe")
    assert os.stat(output_dir / "test_endpoint_pi_mpi_compile.out").st_size == 0

    future1 = pi_func(
        output_dir,
        stdout=os.path.join(output_dir, "test_endpoint_pi_mpi_run1.out"),
        stderr=os.path.join(output_dir, "test_endpoint_pi_mpi_run1.err"),
        executor=["gc-mpi"],
        parsl_resource_specification={
            "num_nodes": 2,  # Number of nodes required for the application instance
            "num_ranks": 2 * cores_per_node,  # Number of ranks in total
            "ranks_per_node": cores_per_node,  # Number of ranks / application elements to be launched per node
        },
    )

    future2 = pi_func(
        output_dir,
        stdout=os.path.join(output_dir, "test_endpoint_pi_mpi_run2.out"),
        stderr=os.path.join(output_dir, "test_endpoint_pi_mpi_run2.err"),
        executor=["gc-mpi"],
        parsl_resource_specification={
            "num_nodes": 1,  # Number of nodes required for the application instance
            "num_ranks": cores_per_node,  # Number of ranks in total
            "ranks_per_node": cores_per_node,  # Number of ranks / application elements to be launched per node
        },
    )

    r1 = future1.result()
    assert r1 == 0
    r2 = future2.result()
    assert r2 == 0

    # Extract the hostnames used by pi1
    with open(output_dir / "test_endpoint_pi_mpi_run1.out", "r") as f:
        pi1_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi1_hosts.append(line.split()[1])
    # Extract the hostnames used by pi2
    with open(output_dir / "test_endpoint_pi_mpi_run2.out", "r") as f:
        pi2_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi2_hosts.append(line.split()[1])
    # Verify each pi test ran on a different set of nodes
    assert set(pi1_hosts).intersection(pi2_hosts) == set()

    # Verify pi tests ran concurrently
    start_time = []
    end_time = []
    files = ["test_endpoint_pi_mpi_run1.out", "test_endpoint_pi_mpi_run2.out"]
    for f in files:
        with open(output_dir / f, "r") as pi:
            for line in pi:
                if re.match(r"Start Time ", line):
                    line = line.strip().lstrip("Start Time = ")
                    start_time.append(dt.strptime(line, "%d/%m/%Y %H:%M:%S"))
                if re.match(r"End Time ", line):
                    line = line.strip().lstrip("End Time = ")
                    end_time.append(dt.strptime(line, "%d/%m/%Y %H:%M:%S"))
    assert start_time[0] < end_time[1] and start_time[1] < end_time[0]
