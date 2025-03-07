import os
import os.path
import pathlib
import re
from datetime import datetime as dt

import parsl
import pytest
from parsl.app.app import bash_app

import chiltepin.configure


# Compile the hello MPI program with environment passed in
@bash_app(executors=["compute"])
def compile_mpi_hello(
    dirpath,
    stdout=None,
    stderr=None,
    env="",
):
    return f"""
    {env}
    cd {dirpath}
    $CHILTEPIN_MPIF90 -o mpi_hello.exe mpi_hello.f90
    """


# Run the hello MPI program with environment passed in
@bash_app(executors=["mpi"])
def run_mpi_hello(
    dirpath, stdout=None, stderr=None, env="", parsl_resource_specification={}
):
    return f"""
    {env}
    cd {dirpath}
    $PARSL_MPI_PREFIX --overcommit ./mpi_hello.exe
    """


# Compile the pi approximation MPI program with environment passed in
@bash_app(executors=["compute"])
def compile_mpi_pi(
    dirpath,
    stdout=None,
    stderr=None,
    env="",
):
    return f"""
    {env}
    cd {dirpath}
    $CHILTEPIN_MPIF90 -o mpi_pi.exe mpi_pi.f90
    """


# Run the pi approximation MPI program with environment passed in
@bash_app(executors=["mpi"])
def run_mpi_pi(
    dirpath, stdout=None, stderr=None, env="", parsl_resource_specification={}
):
    return f"""
    {env}
    cd {dirpath}
    $PARSL_MPI_PREFIX --overcommit ./mpi_pi.exe
    """

@python_app(executors=["mpi"])
def get_cores_per_node(parsl_resource_specification={}):
    return os.environ['SLURM_CPUS_ON_NODE']

# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()
    yaml_config = chiltepin.configure.parse_file(config_file)
    yaml_config[platform]["resources"]["compute"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )
    yaml_config[platform]["resources"]["mpi"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )
    resources = chiltepin.configure.load(
        yaml_config[platform]["resources"],
        include=["compute", "mpi"],
    )
    with parsl.load(resources):
        yield {"resources": resources}
    parsl.clear()


def test_compile_mpi_hello(config):
    pwd = pathlib.Path(__file__).parent.resolve()
    c = compile_mpi_hello(
        dirpath=pwd,
        stdout=(os.path.join(pwd, "parsl_mpi_hello_compile.out"), "w"),
        stderr=(os.path.join(pwd, "parsl_mpi_hello_compile.err"), "w"),
    ).result()
    assert c == 0
    assert os.path.isfile(pwd / "mpi_hello.exe")
    assert os.stat(pwd / "parsl_mpi_hello_compile.out").st_size == 0


def test_run_mpi_hello(config):
    pwd = pathlib.Path(__file__).parent.resolve()
    # Remove any previous output if necessary
    if os.path.exists(pwd / "parsl_mpi_hello_run.out"):
        os.remove(pwd / "parsl_mpi_hello_run.out")
    if os.path.exists(pwd / "parsl_mpi_hello_run.err"):
        os.remove(pwd / "parsl_mpi_hello_run.err")
    hello = run_mpi_hello(
        dirpath=pwd,
        stdout=os.path.join(pwd, "parsl_mpi_hello_run.out"),
        stderr=os.path.join(pwd, "parsl_mpi_hello_run.err"),
        parsl_resource_specification={
            "num_nodes": 3,  # Number of nodes required for the application instance
            "num_ranks": 6,  # Number of ranks in total
            "ranks_per_node": 2,  # Number of ranks / application elements to be launched per node
        },
    ).result()
    assert hello == 0
    with open(pwd / "parsl_mpi_hello_run.out", "r") as f:
        for line in f:
            assert re.match(r"Hello world from host \S+, rank \d+ out of 6", line)


def test_compile_mpi_pi(config):
    pwd = pathlib.Path(__file__).parent.resolve()
    c = compile_mpi_pi(
        dirpath=pwd,
        stdout=(os.path.join(pwd, "parsl_mpi_pi_compile.out"), "w"),
        stderr=(os.path.join(pwd, "parsl_mpi_pi_compile.err"), "w"),
    ).result()
    assert c == 0
    assert os.path.isfile(pwd / "mpi_pi.exe")
    assert os.stat(pwd / "parsl_mpi_pi_compile.out").st_size == 0


def test_run_mpi_pi(config):
    pwd = pathlib.Path(__file__).parent.resolve()
    # Remove any previous output if necessary
    if os.path.exists(pwd / "parsl_mpi_pi1_run.out"):
        os.remove(pwd / "parsl_mpi_pi1_run.out")
    if os.path.exists(pwd / "parsl_mpi_pi1_run.err"):
        os.remove(pwd / "parsl_mpi_pi1_run.err")
    if os.path.exists(pwd / "parsl_mpi_pi2_run.out"):
        os.remove(pwd / "parsl_mpi_pi2_run.out")
    if os.path.exists(pwd / "parsl_mpi_pi2_run.err"):
        os.remove(pwd / "parsl_mpi_pi2_run.err")

    # Get the cores per node from the pilot job's SLURM variables
    #cores_per_node = get_cores_per_node(
    #    parsl_resource_specification={
    #        "num_nodes": 1,  # Number of nodes required for the application instance
    #    },
    #).result()
    cores_per_node = 8

    # Run MPI pi on two nodes
    pi1 = run_mpi_pi(
        dirpath=pwd,
        stdout=os.path.join(pwd, "parsl_mpi_pi1_run.out"),
        stderr=os.path.join(pwd, "parsl_mpi_pi1_run.err"),
        parsl_resource_specification={
            "num_nodes": 2,  # Number of nodes required for the application instance
            "num_ranks": 2 * cores_per_node,  # Number of ranks in total
            "ranks_per_node": cores_per_node,  # Number of ranks / application elements to be launched per node
        },
    )

    # Run MPI pi on one node
    pi2 = run_mpi_pi(
        dirpath=pwd,
        stdout=os.path.join(pwd, "parsl_mpi_pi2_run.out"),
        stderr=os.path.join(pwd, "parsl_mpi_pi2_run.err"),
        parsl_resource_specification={
            "num_nodes": 1,  # Number of nodes required for the application instance
            "num_ranks": cores_per_node,  # Number of ranks in total
            "ranks_per_node": cores_per_node,  # Number of ranks / application elements to be launched per node
        },
    )
    assert pi1.result() == 0
    assert pi2.result() == 0
    # Extract the hostnames used by pi1
    with open(pwd / "parsl_mpi_pi1_run.out", "r") as f:
        pi1_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi1_hosts.append(line.split()[1])
    # Extract the hostnames used by pi2
    with open(pwd / "parsl_mpi_pi2_run.out", "r") as f:
        pi2_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi2_hosts.append(line.split()[1])
    # Verify each pi test ran on a different set of nodes
    assert set(pi1_hosts).intersection(pi2_hosts) == set()

    # Verify pi tests un concurrently
    start_time = []
    end_time = []
    files = ["parsl_mpi_pi1_run.out", "parsl_mpi_pi2_run.out"]
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
