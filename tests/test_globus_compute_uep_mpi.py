import os.path
import pathlib
import re
from datetime import datetime as dt

import parsl
import pytest
import yaml
from jinja2 import BaseLoader, Environment, FileSystemLoader

import chiltepin.configure
import chiltepin.endpoint as endpoint
from chiltepin.tasks import bash_task


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()

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

    # Configure the test endpoints
    endpoint.configure("gc-compute", config_dir=f"{pwd}/.globus_compute")
    endpoint.configure("gc-mpi", config_dir=f"{pwd}/.globus_compute")

    # Apply endpoint configuration template for the chosen platform
    _apply_endpoint_template(resource_config)

    # Start the test endpoints
    endpoint.start("gc-compute", config_dir=f"{pwd}/.globus_compute")
    endpoint.start("gc-mpi", config_dir=f"{pwd}/.globus_compute")

    # Update resource config with the test endpoint ids
    resource_config = _set_endpoint_ids(resource_config)

    # Load the finalized resource configuration
    resources = chiltepin.configure.load(
        resource_config,
        resources=["gc-compute", "gc-mpi"],
    )

    # Run the tests with the loaded resources
    with parsl.load(resources):
        yield

    # Stop the test endpoints now that tests are done
    endpoint.stop("gc-compute", config_dir=f"{pwd}/.globus_compute")
    endpoint.stop("gc-mpi", config_dir=f"{pwd}/.globus_compute")

    # Delete the test endpoints
    endpoint.delete("gc-compute", config_dir=f"{pwd}/.globus_compute")
    endpoint.delete("gc-mpi", config_dir=f"{pwd}/.globus_compute")


# Test endpoint configure
def _apply_endpoint_template(config):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Customize endpoint configs for this platform using Jinja2 templates
    jinja_env = Environment(loader=FileSystemLoader(f"{pwd}/templates/"))
    for name in ["gc-compute", "gc-mpi"]:
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

    # Get a listing of the endpoints
    ep_list = endpoint.list(config_dir=f"{pwd}/.globus_compute")
    gc_compute_endpoint_id = ep_list["gc-compute"]["id"]
    gc_mpi_endpoint_id = ep_list["gc-mpi"]["id"]
    assert len(gc_mpi_endpoint_id) == 36
    assert len(gc_compute_endpoint_id) == 36

    config_string = yaml.dump(config)
    template = Environment(loader=BaseLoader()).from_string(config_string)
    content = template.render(
        compute_endpoint_id=gc_compute_endpoint_id,
        mpi_endpoint_id=gc_mpi_endpoint_id,
    )
    content_yaml = yaml.safe_load(content)
    return content_yaml


# Test endpoint use
def test_endpoint_mpi_hello(config):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Define a bash task to compile the MPI code
    @bash_task
    def compile_func(
        dirpath,
        stdout=None,
        stderr=None,
    ):
        return f"""
        cd {dirpath}
        $CHILTEPIN_MPIF90 -o mpi_hello.exe mpi_hello.f90
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
    if os.path.exists(pwd / "globus_compute_mpi_hello_compile_uep.out"):
        os.remove(pwd / "globus_compute_mpi_hello_compile_uep.out")
    if os.path.exists(pwd / "globus_compute_mpi_hello_compile_uep.err"):
        os.remove(pwd / "globus_compute_mpi_hello_compile_uep.err")
    if os.path.exists(pwd / "globus_compute_mpi_hello_run_uep.out"):
        os.remove(pwd / "globus_compute_mpi_hello_run_uep.out")
    if os.path.exists(pwd / "globus_compute_mpi_hello_run_uep.err"):
        os.remove(pwd / "globus_compute_mpi_hello_run_uep.err")

    future = compile_func(
        pwd,
        stdout=os.path.join(pwd, "globus_compute_mpi_hello_compile_uep.out"),
        stderr=os.path.join(pwd, "globus_compute_mpi_hello_compile_uep.err"),
        executor="gc-compute",
    )
    r = future.result()
    assert r == 0

    future = hello_func(
        pwd,
        stdout=os.path.join(pwd, "globus_compute_mpi_hello_run_uep.out"),
        stderr=os.path.join(pwd, "globus_compute_mpi_hello_run_uep.err"),
        executor="gc-mpi",
        parsl_resource_specification={
            "num_nodes": 3,  # Number of nodes required for the application instance
            "num_ranks": 6,  # Number of ranks in total
            "ranks_per_node": 2,  # Number of ranks / application elements to be launched per node
        },
    )
    r = future.result()
    assert r == 0

    # Check output
    with open(pwd / "globus_compute_mpi_hello_run_uep.out", "r") as f:
        for line in f:
            assert re.match(r"Hello world from host \S+, rank \d+ out of 6", line)


# Test endpoint use
def test_endpoint_mpi_pi(config):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Define a bash task to compile the MPI code
    @bash_task
    def compile_func(dirpath, stdout=None, stderr=None):
        return f"""
        cd {dirpath}
        $CHILTEPIN_MPIF90 -o mpi_pi.exe mpi_pi.f90
        """

    # Define a bash task to run the MPI program
    @bash_task
    def pi_func(dirpath, stdout=None, stderr=None, parsl_resource_specification=None):
        return f"""
        cd {dirpath}
        $PARSL_MPI_PREFIX --overcommit ./mpi_pi.exe
        """

    # Remove any previous output if necessary
    if os.path.exists(pwd / "globus_compute_mpi_pi_compile_uep.out"):
        os.remove(pwd / "globus_compute_mpi_pi_compile_uep.out")
    if os.path.exists(pwd / "globus_compute_mpi_pi_compile_uep.err"):
        os.remove(pwd / "globus_compute_mpi_pi_compile_uep.err")
    if os.path.exists(pwd / "globus_compute_mpi_pi1_run_uep.out"):
        os.remove(pwd / "globus_compute_mpi_pi1_run_uep.out")
    if os.path.exists(pwd / "globus_compute_mpi_pi1_run_uep.err"):
        os.remove(pwd / "globus_compute_mpi_pi1_run_uep.err")
    if os.path.exists(pwd / "globus_compute_mpi_pi2_run_uep.out"):
        os.remove(pwd / "globus_compute_mpi_pi2_run_uep.out")
    if os.path.exists(pwd / "globus_compute_mpi_pi2_run_uep.err"):
        os.remove(pwd / "globus_compute_mpi_pi2_run_uep.err")

    cores_per_node = 8
    future = compile_func(
        pwd,
        stdout=os.path.join(pwd, "globus_compute_mpi_pi_compile_uep.out"),
        stderr=os.path.join(pwd, "globus_compute_mpi_pi_compile_uep.err"),
        executor="gc-compute",
    )
    r = future.result()
    assert r == 0

    future1 = pi_func(
        pwd,
        stdout=os.path.join(pwd, "globus_compute_mpi_pi1_run_uep.out"),
        stderr=os.path.join(pwd, "globus_compute_mpi_pi1_run_uep.err"),
        executor="gc-mpi",
        parsl_resource_specification={
            "num_nodes": 2,  # Number of nodes required for the application instance
            "num_ranks": 2 * cores_per_node,  # Number of ranks in total
            "ranks_per_node": cores_per_node,  # Number of ranks / application elements to be launched per node
        },
    )

    future2 = pi_func(
        pwd,
        stdout=os.path.join(pwd, "globus_compute_mpi_pi2_run_uep.out"),
        stderr=os.path.join(pwd, "globus_compute_mpi_pi2_run_uep.err"),
        executor="gc-mpi",
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
    with open(pwd / "globus_compute_mpi_pi1_run_uep.out", "r") as f:
        pi1_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi1_hosts.append(line.split()[1])
    # Extract the hostnames used by pi2
    with open(pwd / "globus_compute_mpi_pi2_run_uep.out", "r") as f:
        pi2_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi2_hosts.append(line.split()[1])
    # Verify each pi test ran on a different set of nodes
    assert set(pi1_hosts).intersection(pi2_hosts) == set()

    # Verify pi tests run concurrently
    start_time = []
    end_time = []
    files = ["globus_compute_mpi_pi1_run_uep.out", "globus_compute_mpi_pi2_run_uep.out"]
    for f in files:
        with open(pwd / f, "r") as pi:
            for line in pi:
                if re.match(r"Start Time ", line):
                    line = line.strip().lstrip("Start Time = ")
                    start_time.append(dt.strptime(line, "%d/%m/%Y %H:%M:%S"))
                if re.match(r"End Time ", line):
                    line = line.strip().lstrip("End Time = ")
                    end_time.append(dt.strptime(line, "%d/%m/%Y %H:%M:%S"))
    assert start_time[0] < end_time[1] and start_time[1] < end_time[0]
