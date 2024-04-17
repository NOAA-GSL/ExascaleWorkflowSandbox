import os
import re
from datetime import datetime as dt

import parsl
import pytest
from parsl.app.app import bash_app

import chiltepin.configure


# Print out resources that Flux sees after it starts
@bash_app(executors=["parallel"])
def resource_list(stdout=None, stderr=None, env=""):
    return f"""
    {env}
    flux resource list
    """


# Test Flux PMI launch
@bash_app(executors=["parallel"])
def pmi_barrier(stdout=None, stderr=None, env="", parsl_resource_specification={}):
    return f"""
    {env}
    flux pmi barrier
    """


# Compile the hello MPI program with environment passed in
@bash_app(executors=["parallel"])
def compile_mpi_hello(
    dirpath,
    stdout=None,
    stderr=None,
    env="",
    parsl_resource_specification={"num_tasks": 1},
):
    return f"""
    {env}
    cd {dirpath}
    $CHILTEPIN_MPIF90 -o mpi_hello.exe mpi_hello.f90
    """


# Run the hello MPI program with environment passed in
@bash_app(executors=["parallel"])
def run_mpi_hello(
    dirpath, stdout=None, stderr=None, env="", parsl_resource_specification={}
):
    return f"""
    {env}
    cd {dirpath}
    ./mpi_hello.exe
    """


# Compile the pi approximation MPI program with environment passed in
@bash_app(executors=["parallel"])
def compile_mpi_pi(
    dirpath,
    stdout=None,
    stderr=None,
    env="",
    parsl_resource_specification={"num_tasks": 1},
):
    return f"""
    {env}
    cd {dirpath}
    $CHILTEPIN_MPIF90 -o mpi_pi.exe mpi_pi.f90
    """


# Run the pi approximation MPI program with environment passed in
@bash_app(executors=["parallel"])
def run_mpi_pi(
    dirpath, stdout=None, stderr=None, env="", parsl_resource_specification={}
):
    return f"""
    {env}
    cd {dirpath}
    ./mpi_pi.exe
    """


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    yaml_config = chiltepin.configure.parse_file(config_file)
    resources, environments = chiltepin.configure.factory(yaml_config, platform)
    environment = environments[platform]
    with parsl.load(resources):
        yield {"resources": resources, "environment": environment}
    parsl.clear()


# Test Flux resource list
def test_flux_resource_list(config):
    r = resource_list(
        stdout=("parsl_flux_resource_list.out", "w"),
        stderr=("parsl_flux_resource_list.err", "w"),
        env=config["environment"],
    ).result()
    assert r == 0

    pattern = re.compile(
        r"(\s+)STATE(\s+)NNODES(\s+)NCORES(\s+)NGPUS(\s+)NODELIST\n"
        r"(\s+)free(\s+)(3)(\s+)(\d+)(\s+)(0)(\s+)(\S+)\n"
        r"(\s+)allocated(\s+)(1)(\s+)(1)(\s+)(0)(\s+)(\S+)\n"
        r"(\s+)down(\s+)(0)(\s+)(0)(\s+)(0)",
        re.DOTALL,
    )

    with open("parsl_flux_resource_list.out", "r") as f:
        assert pattern.match(f.read())


# Test Flux pmi barrier
def test_flux_pmi(config):
    p = pmi_barrier(
        stdout=("parsl_flux_pmi_barrier.out", "w"),
        stderr=("parsl_flux_pmi_barrier.err", "w"),
        env=config["environment"],
        parsl_resource_specification={"num_tasks": 6, "num_nodes": 3},
    ).result()
    assert p == 0
    with open("parsl_flux_pmi_barrier.out", "r") as f:
        assert re.match(
            r"[fƒ]\S+: completed pmi barrier on 6 tasks in [0-9.]+s.", f.read()
        )


def test_compile_mpi_hello(config):
    shared_dir = "./"
    c = compile_mpi_hello(
        dirpath=shared_dir,
        stdout=(os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.out"), "w"),
        stderr=(os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.err"), "w"),
        env=config["environment"],
    ).result()
    assert c == 0
    assert os.path.isfile("mpi_hello.exe")
    assert os.stat("parsl_flux_mpi_hello_compile.out").st_size == 0


def test_run_mpi_hello(config):
    shared_dir = "./"
    # Remove any previous output if necessary
    if os.path.exists("parsl_flux_mpi_hello_run.out"):
        os.remove("parsl_flux_mpi_hello_run.out")
    if os.path.exists("parsl_flux_mpi_hello_run.err"):
        os.remove("parsl_flux_mpi_hello_run.err")
    hello = run_mpi_hello(
        dirpath=shared_dir,
        stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.out"),
        stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.err"),
        env=config["environment"],
        parsl_resource_specification={"num_tasks": 6, "num_nodes": 3},
    ).result()
    assert hello == 0
    with open("parsl_flux_mpi_hello_run.out", "r") as f:
        for line in f:
            assert re.match(r"Hello world from host \S+, rank \d+ out of 6", line)


def test_compile_mpi_pi(config):
    shared_dir = "./"
    c = compile_mpi_pi(
        dirpath=shared_dir,
        stdout=(os.path.join(shared_dir, "parsl_flux_mpi_pi_compile.out"), "w"),
        stderr=(os.path.join(shared_dir, "parsl_flux_mpi_pi_compile.err"), "w"),
        env=config["environment"],
    ).result()
    assert c == 0
    assert os.path.isfile("mpi_pi.exe")
    assert os.stat("parsl_flux_mpi_pi_compile.out").st_size == 0


def test_run_mpi_pi(config):
    shared_dir = "./"
    # Remove any previous output if necessary
    if os.path.exists("parsl_flux_mpi_pi1_run.out"):
        os.remove("parsl_flux_mpi_pi1_run.out")
    if os.path.exists("parsl_flux_mpi_pi1_run.err"):
        os.remove("parsl_flux_mpi_pi1_run.err")
    if os.path.exists("parsl_flux_mpi_pi2_run.out"):
        os.remove("parsl_flux_mpi_pi2_run.out")
    if os.path.exists("parsl_flux_mpi_pi2_run.err"):
        os.remove("parsl_flux_mpi_pi2_run.err")
    cores_per_node = config["resources"].executors[0].provider.cores_per_node
    assert config["resources"].executors[0].label == "parallel"
    pi1 = run_mpi_pi(
        dirpath=shared_dir,
        stdout=os.path.join(shared_dir, "parsl_flux_mpi_pi1_run.out"),
        stderr=os.path.join(shared_dir, "parsl_flux_mpi_pi1_run.err"),
        env=config["environment"],
        parsl_resource_specification={"num_tasks": cores_per_node * 2, "num_nodes": 2},
    )
    pi2 = run_mpi_pi(
        dirpath=shared_dir,
        stdout=os.path.join(shared_dir, "parsl_flux_mpi_pi2_run.out"),
        stderr=os.path.join(shared_dir, "parsl_flux_mpi_pi2_run.err"),
        env=config["environment"],
        parsl_resource_specification={"num_tasks": cores_per_node, "num_nodes": 1},
    )
    assert pi1.result() == 0
    assert pi2.result() == 0
    # Extract the hostnames used by pi1
    with open("parsl_flux_mpi_pi1_run.out", "r") as f:
        pi1_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi1_hosts.append(line.split()[1])
    # Extract the hostnames used by pi2
    with open("parsl_flux_mpi_pi2_run.out", "r") as f:
        pi2_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi2_hosts.append(line.split()[1])
    # Verify each pi test ran on a different set of nodes
    assert set(pi1_hosts).intersection(pi2_hosts) == set()

    # Verify pi tests un concurrently
    start_time = []
    end_time = []
    files = ["parsl_flux_mpi_pi1_run.out", "parsl_flux_mpi_pi2_run.out"]
    for f in files:
        with open(f, "r") as pi:
            for line in pi:
                if re.match(r"Start Time ", line):
                    line = line.strip().lstrip("Start Time = ")
                    start_time.append(dt.strptime(line, "%d/%m/%Y %H:%M:%S"))
                if re.match(r"End Time ", line):
                    line = line.strip().lstrip("End Time = ")
                    end_time.append(dt.strptime(line, "%d/%m/%Y %H:%M:%S"))
    assert start_time[0] < end_time[1] and start_time[1] < end_time[0]
