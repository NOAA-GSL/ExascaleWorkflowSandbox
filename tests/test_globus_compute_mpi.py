import os.path
import pathlib
import re
import subprocess
from datetime import datetime as dt

import pytest
from globus_compute_sdk import Executor, MPIFunction, ShellFunction
from jinja2 import Environment, FileSystemLoader

import chiltepin.configure


# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def config(config_file, platform):
    pwd = pathlib.Path(__file__).parent.resolve()
    yaml_config = chiltepin.configure.parse_file(config_file)
    yaml_config[platform]["resources"]["gc-compute"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )
    yaml_config[platform]["resources"]["gc-mpi"]["environment"].append(
        f"export PYTHONPATH={pwd.parent.resolve()}"
    )
    resources = yaml_config[platform]["resources"]
    return {"resources": resources}


# Local function to get endpoint ids
def _get_endpoint_ids():
    pwd = pathlib.Path(__file__).parent.resolve()

    # Get a listing of the endpoints
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "list",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0

    # Get the uuid of the gc-mpi endpoint
    mpi_endpoint_regex = re.compile(
        r"\| ([0-9a-f\-]{36}) \| Running\s+\| gc-mpi\s+\|"
    )
    match = mpi_endpoint_regex.search(p.stdout)
    gc_mpi_endpoint_id = match.group(1)
    assert len(gc_mpi_endpoint_id) == 36

    # Get the uuid of the gc-compute endpoint
    compute_endpoint_regex = re.compile(
        r"\| ([0-9a-f\-]{36}) \| Running\s+\| gc-compute\s+\|"
    )
    match = compute_endpoint_regex.search(p.stdout)
    gc_compute_endpoint_id = match.group(1)
    assert len(gc_compute_endpoint_id) == 36

    return gc_mpi_endpoint_id, gc_compute_endpoint_id


# Test endpoint configure
def test_endpoint_configure(config):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Configure gc-compute endpoint
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "configure",
            "gc-compute",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0

    # Configure gc-mpi endpoint
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "configure",
            "gc-mpi",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0

    # Customize endpoint configs for this platform using Jinja2 templates
    jinja_env = Environment(loader=FileSystemLoader(f"{pwd}/templates/"))
    for endpoint in ["gc-compute", "gc-mpi"]:
        template = jinja_env.get_template(f"{endpoint}.yaml")
        content = template.render(
            partition=config["resources"][endpoint]["partition"],
            account=config["resources"][endpoint]["account"],
            worker_init=";".join(config["resources"][endpoint]["environment"])
        )
        with open(
            f"{pwd}/globus_compute/{endpoint}/config.yaml", mode="w", encoding="utf-8"
        ) as gc_config:
            gc_config.write(content)


# Test endpoint startup
def test_endpoint_start():
    pwd = pathlib.Path(__file__).parent.resolve()

    # Start gc-compute endpoint
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "start",
            "gc-compute",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0

    # Start gc-mpi endpoint
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "start",
            "gc-mpi",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0


# Test endpoint use
def test_endpoint_mpi_hello(config):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Define a ShellFunction to compile the MPI code
    compile_func = ShellFunction(
        """
        cd {dirpath}
        $CHILTEPIN_MPIF90 -o mpi_hello.exe mpi_hello.f90
        """,
        stdout=os.path.join(pwd, "globus_compute_mpi_hello_compile.out"),
        stderr=os.path.join(pwd, "globus_compute_mpi_hello_compile.err"),
    )

    # Define a MPIFunction to run the MPI program
    hello_func = MPIFunction(
        """true;  # Force the default prefix to launch a no-op
        cd {dirpath}
        $PARSL_MPI_PREFIX --overcommit ./mpi_hello.exe
        """,
        stdout=os.path.join(pwd, "globus_compute_mpi_hello_run.out"),
        stderr=os.path.join(pwd, "globus_compute_mpi_hello_run.err"),
    )

    # Get a listing of the endpoints
    gc_mpi_endpoint_id, gc_compute_endpoint_id = _get_endpoint_ids()

    # Remove any previous output if necessary
    if os.path.exists(pwd / "globus_compute_mpi_hello_compile.out"):
        os.remove(pwd / "globus_compute_mpi_hello_compile.out")
    if os.path.exists(pwd / "globus_compute_mpi_hello_compile.err"):
        os.remove(pwd / "globus_compute_mpi_hello_compile.err")
    if os.path.exists(pwd / "globus_compute_mpi_hello_run.out"):
        os.remove(pwd / "globus_compute_mpi_hello_run.out")
    if os.path.exists(pwd / "globus_compute_mpi_hello_run.err"):
        os.remove(pwd / "globus_compute_mpi_hello_run.err")

    # Compile the MPI program in the gc-compute endpoint
    with Executor(endpoint_id=gc_compute_endpoint_id) as gce:
        future = gce.submit(
            compile_func,
            dirpath=pwd,
        )
        r = future.result()
        assert r.returncode == 0

    # Run the MPI program in the gc-mpi endpoint
    with Executor(endpoint_id=gc_mpi_endpoint_id) as gce:
        gce.resource_specification = {
            "num_nodes": 3,  # Number of nodes required for the application instance
            "num_ranks": 6,  # Number of ranks in total
            "ranks_per_node": 2,  # Number of ranks / application elements to be launched per node
        }
        future = gce.submit(
            hello_func,
            dirpath=pwd,
        )
        r = future.result()
        assert r.returncode == 0

    # Check output
    with open(pwd / "globus_compute_mpi_hello_run.out", "r") as f:
        for line in f:
            assert re.match(r"Hello world from host \S+, rank \d+ out of 6", line)


# Test endpoint use
def test_endpoint_mpi_pi(config):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Define a ShellFunction to compile the MPI code
    compile_func = ShellFunction(
        """
        cd {dirpath}
        $CHILTEPIN_MPIF90 -o mpi_pi.exe mpi_pi.f90
        """,
        stdout=os.path.join(pwd, "globus_compute_mpi_pi_compile.out"),
        stderr=os.path.join(pwd, "globus_compute_mpi_pi_compile.err"),
    )

    # Define a MPIFunction to run the MPI program
    pi1_func = MPIFunction(
        """true;  # Force the default prefix to launch a no-op
        cd {dirpath}
        $PARSL_MPI_PREFIX --overcommit ./mpi_pi.exe
        """,
        stdout=os.path.join(pwd, "globus_compute_mpi_pi1_run.out"),
        stderr=os.path.join(pwd, "globus_compute_mpi_pi1_run.err"),
    )

    # Define a MPIFunction to run the MPI program
    pi2_func = MPIFunction(
        """true;  # Force the default prefix to launch a no-op
        cd {dirpath}
        $PARSL_MPI_PREFIX --overcommit ./mpi_pi.exe
        """,
        stdout=os.path.join(pwd, "globus_compute_mpi_pi2_run.out"),
        stderr=os.path.join(pwd, "globus_compute_mpi_pi2_run.err"),
    )

    # Get a listing of the endpoints
    gc_mpi_endpoint_id, gc_compute_endpoint_id = _get_endpoint_ids()

    # Remove any previous output if necessary
    if os.path.exists(pwd / "globus_compute_mpi_pi_compile.out"):
        os.remove(pwd / "globus_compute_mpi_pi_compile.out")
    if os.path.exists(pwd / "globus_compute_mpi_pi_compile.err"):
        os.remove(pwd / "globus_compute_mpi_pi_compile.err")
    if os.path.exists(pwd / "globus_compute_mpi_pi1_run.out"):
        os.remove(pwd / "globus_compute_mpi_pi1_run.out")
    if os.path.exists(pwd / "globus_compute_mpi_pi1_run.err"):
        os.remove(pwd / "globus_compute_mpi_pi1_run.err")
    if os.path.exists(pwd / "globus_compute_mpi_pi2_run.out"):
        os.remove(pwd / "globus_compute_mpi_pi2_run.out")
    if os.path.exists(pwd / "globus_compute_mpi_pi2_run.err"):
        os.remove(pwd / "globus_compute_mpi_pi2_run.err")

    # Compile the MPI program in the gc-compute endpoint
    with Executor(endpoint_id=gc_compute_endpoint_id) as gce:
        future = gce.submit(
            compile_func,
            dirpath=pwd,
        )
        r = future.result()
        assert r.returncode == 0

    # Run the MPI program in the gc-mpi endpoint
    with Executor(endpoint_id=gc_mpi_endpoint_id) as gce:
        cores_per_node = 8
        gce.resource_specification = {
            "num_nodes": 2,  # Number of nodes required for the application instance
            "num_ranks": 2 * cores_per_node,  # Number of ranks in total
            "ranks_per_node": cores_per_node,  # Number of ranks / application elements to be launched per node
        }
        future1 = gce.submit(
            pi1_func,
            dirpath=pwd,
        )

        gce.resource_specification = {
            "num_nodes": 1,  # Number of nodes required for the application instance
            "num_ranks": cores_per_node,  # Number of ranks in total
            "ranks_per_node": cores_per_node,  # Number of ranks / application elements to be launched per node
        }
        future2 = gce.submit(
            pi2_func,
            dirpath=pwd,
        )

        r1 = future1.result()
        assert r1.returncode == 0
        r2 = future2.result()
        assert r2.returncode == 0

    # Extract the hostnames used by pi1
    with open(pwd / "globus_compute_mpi_pi1_run.out", "r") as f:
        pi1_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi1_hosts.append(line.split()[1])
    # Extract the hostnames used by pi2
    with open(pwd / "globus_compute_mpi_pi2_run.out", "r") as f:
        pi2_hosts = []
        for line in f:
            if re.match(r"Host ", line):
                pi2_hosts.append(line.split()[1])
    # Verify each pi test ran on a different set of nodes
    assert set(pi1_hosts).intersection(pi2_hosts) == set()

    # Verify pi tests run concurrently
    start_time = []
    end_time = []
    files = ["globus_compute_mpi_pi1_run.out", "globus_compute_mpi_pi2_run.out"]
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


# Test stopping of  endpoints
def test_endpoint_stop():
    pwd = pathlib.Path(__file__).parent.resolve()

    # Stop the gc-compute endpoint
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "stop",
            "gc-compute",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0

    # Stop the gc-mpi endpoint
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "stop",
            "gc-mpi",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0


# Test endpoint delete
def test_endpoint_delete(config):
    pwd = pathlib.Path(__file__).parent.resolve()

    # Delete gc-compute endpoint
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "delete",
            "--yes",
            "gc-compute",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0

    # Delete gc-mpi endpoint
    p = subprocess.run(
        [
            "globus-compute-endpoint",
            "-c",
            f"{pwd}/globus_compute",
            "delete",
            "--yes",
            "gc-mpi",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=60,
    )
    assert p.returncode == 0
