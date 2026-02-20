import logging
import os
import os.path
import pathlib
import re
from datetime import datetime as dt

import parsl
import pytest

import chiltepin.configure
from chiltepin.tasks import bash_task


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Create directory for test output
    output_dir = pwd / "test_output"
    output_dir.mkdir(exist_ok=True)

    yaml_config = chiltepin.configure.parse_file(config_file)
    yaml_config[platform]["resources"]["compute"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )
    yaml_config[platform]["resources"]["mpi"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )

    # Set Parsl logging to DEBUG and redirect to a file in the output directory
    logger_handler = parsl.set_file_logger(
        filename=str(output_dir / "test_parsl_mpi_parsl.log"),
        level=logging.DEBUG,
    )

    resources = chiltepin.configure.load(
        yaml_config[platform]["resources"],
        include=["compute", "mpi"],
        run_dir=str(output_dir / "test_parsl_mpi_runinfo"),
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


def test_parsl_hello_mpi(config):
    output_dir = config["output_dir"]

    # Define a bash task to compile the MPI code
    @bash_task
    def compile_mpi_hello(
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
    def run_mpi_hello(
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
    if os.path.exists(output_dir / "test_parsl_hello_mpi_compile.out"):
        os.remove(output_dir / "test_parsl_hello_mpi_compile.out")
    if os.path.exists(output_dir / "test_parsl_hello_mpi_compile.err"):
        os.remove(output_dir / "test_parsl_hello_mpi_compile.err")
    if os.path.exists(output_dir / "test_parsl_hello_mpi_run.out"):
        os.remove(output_dir / "test_parsl_hello_mpi_run.out")
    if os.path.exists(output_dir / "test_parsl_hello_mpi_run.err"):
        os.remove(output_dir / "test_parsl_hello_mpi_run.err")

    future = compile_mpi_hello(
        output_dir,
        stdout=(os.path.join(output_dir, "test_parsl_hello_mpi_compile.out"), "w"),
        stderr=(os.path.join(output_dir, "test_parsl_hello_mpi_compile.err"), "w"),
        executor=["compute"],
    )
    r = future.result()
    assert r == 0
    assert os.path.isfile(output_dir / "mpi_hello.exe")
    assert os.stat(output_dir / "test_parsl_hello_mpi_compile.out").st_size == 0

    future = run_mpi_hello(
        output_dir,
        stdout=os.path.join(output_dir, "test_parsl_hello_mpi_run.out"),
        stderr=os.path.join(output_dir, "test_parsl_hello_mpi_run.err"),
        executor=["mpi"],
        parsl_resource_specification={
            "num_nodes": 3,  # Number of nodes required for the application instance
            "num_ranks": 6,  # Number of ranks in total
            "ranks_per_node": 2,  # Number of ranks / application elements to be launched per node
        },
    )
    r = future.result()
    assert r == 0

    # Check output
    with open(output_dir / "test_parsl_hello_mpi_run.out", "r") as f:
        for line in f:
            assert re.match(r"Hello world from host \S+, rank \d+ out of 6", line)


def test_parsl_pi_mpi(config):
    output_dir = config["output_dir"]

    # Define a bash task to compile the MPI code
    @bash_task
    def compile_mpi_pi(
        dirpath,
        stdout=None,
        stderr=None,
        env="",
    ):
        return f"""
        {env}
        cd {dirpath}
        $CHILTEPIN_MPIF90 -o mpi_pi.exe ../mpi_pi.f90
        """

    # Define a bash task to run the MPI program
    @bash_task
    def run_mpi_pi(
        dirpath, stdout=None, stderr=None, env="", parsl_resource_specification=None
    ):
        return f"""
        {env}
        cd {dirpath}
        $PARSL_MPI_PREFIX --overcommit ./mpi_pi.exe
        """

    # Remove any previous output if necessary
    if os.path.exists(output_dir / "test_parsl_pi_mpi_compile.out"):
        os.remove(output_dir / "test_parsl_pi_mpi_compile.out")
    if os.path.exists(output_dir / "test_parsl_pi_mpi_compile.err"):
        os.remove(output_dir / "test_parsl_pi_mpi_compile.err")
    if os.path.exists(output_dir / "test_parsl_pi_mpi_run1.out"):
        os.remove(output_dir / "test_parsl_pi_mpi_run1.out")
    if os.path.exists(output_dir / "test_parsl_pi_mpi_run1.err"):
        os.remove(output_dir / "test_parsl_pi_mpi_run1.err")
    if os.path.exists(output_dir / "test_parsl_pi_mpi_run2.out"):
        os.remove(output_dir / "test_parsl_pi_mpi_run2.out")
    if os.path.exists(output_dir / "test_parsl_pi_mpi_run2.err"):
        os.remove(output_dir / "test_parsl_pi_mpi_run2.err")

    future = compile_mpi_pi(
        output_dir,
        stdout=(os.path.join(output_dir, "test_parsl_pi_mpi_compile.out"), "w"),
        stderr=(os.path.join(output_dir, "test_parsl_pi_mpi_compile.err"), "w"),
        executor=["compute"],
    )
    r = future.result()
    assert r == 0
    assert os.path.isfile(output_dir / "mpi_pi.exe")
    assert os.stat(output_dir / "test_parsl_pi_mpi_compile.out").st_size == 0

    # Set the cores per node for the pilot job
    cores_per_node = 8

    # Run MPI pi on two nodes
    pi1 = run_mpi_pi(
        output_dir,
        stdout=os.path.join(output_dir, "test_parsl_pi_mpi_run1.out"),
        stderr=os.path.join(output_dir, "test_parsl_pi_mpi_run1.err"),
        executor=["mpi"],
        parsl_resource_specification={
            "num_nodes": 2,  # Number of nodes required for the application instance
            "num_ranks": 2 * cores_per_node,  # Number of ranks in total
            "ranks_per_node": cores_per_node,  # Number of ranks / application elements to be launched per node
        },
    )

    # Run MPI pi on one node
    pi2 = run_mpi_pi(
        output_dir,
        stdout=os.path.join(output_dir, "test_parsl_pi_mpi_run2.out"),
        stderr=os.path.join(output_dir, "test_parsl_pi_mpi_run2.err"),
        executor=["mpi"],
        parsl_resource_specification={
            "num_nodes": 1,  # Number of nodes required for the application instance
            "num_ranks": cores_per_node,  # Number of ranks in total
            "ranks_per_node": cores_per_node,  # Number of ranks / application elements to be launched per node
        },
    )
    assert pi1.result() == 0
    assert pi2.result() == 0
    # Extract the hostnames used by pi1
    with open(output_dir / "test_parsl_pi_mpi_run1.out", "r") as f:
        pi1_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi1_hosts.append(line.split()[1])
    # Extract the hostnames used by pi2
    with open(output_dir / "test_parsl_pi_mpi_run2.out", "r") as f:
        pi2_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi2_hosts.append(line.split()[1])
    # Verify each pi test ran on a different set of nodes
    assert set(pi1_hosts).intersection(pi2_hosts) == set()

    # Verify pi tests ran concurrently
    start_time = []
    end_time = []
    files = ["test_parsl_pi_mpi_run1.out", "test_parsl_pi_mpi_run2.out"]
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
