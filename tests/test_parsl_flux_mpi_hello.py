import os
from datetime import datetime as dt
import parsl
from parsl.app.app import python_app, bash_app
import pytest
import re
import yaml

from chiltepin.config.factory import config_factory

# Define function to parse yaml config
def parse_config(filename):
    # Open and parse the yaml config
    with open(filename, "r") as stream:
        try:
            yaml_config = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print("Invalid taml configuration")
            raise(e)
    return yaml_config

# Print out resources that Flux sees after it starts
@bash_app
def resource_list(stdout=None, stderr=None, env=""):
    return '''
    {}
    flux resource list
    '''.format(env)

# Test Flux PMI launch
@bash_app
def pmi_barrier(stdout=None, stderr=None, env="", parsl_resource_specification={}):
    return '''
    {}
    flux pmi barrier
    '''.format(env)

# Compile the hello MPI program with environment passed in
@bash_app
def compile_mpi_hello(dirpath, stdout=None, stderr=None, env="", parsl_resource_specification={"num_tasks": 1}):
    return '''
    {}
    cd {}
    $CHILTEPIN_MPIF90 -o mpi_hello.exe mpi_hello.f90
    '''.format(env,dirpath)

# Run the hello MPI program with environment passed in
@bash_app
def run_mpi_hello(dirpath, stdout=None, stderr=None, env="", parsl_resource_specification={}):
    return '''
    {}
    cd {}
    ./mpi_hello.exe
    '''.format(env, dirpath)

# Compile the pi approximation MPI program with environment passed in
@bash_app
def compile_mpi_pi(dirpath, stdout=None, stderr=None, env="", parsl_resource_specification={"num_tasks": 1}):
    return '''
    {}
    cd {}
    $CHILTEPIN_MPIF90 -o mpi_pi.exe mpi_pi.f90
    '''.format(env,dirpath)

# Run the pi approximation MPI program with environment passed in
@bash_app
def run_mpi_pi(dirpath, stdout=None, stderr=None, env="", parsl_resource_specification={}):
    return '''
    {}
    cd {}
    ./mpi_pi.exe
    '''.format(env, dirpath)

# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def load_config(config_file, request):
    yaml_config = parse_config(config_file)
    config, environment = config_factory(yaml_config)
    parsl.load(config)
    request.addfinalizer(parsl.clear)
    return {"config": config, "environment": environment}

# Test Flux resource list
def test_flux_resource_list(load_config):
    r = resource_list(stdout=('parsl_flux_resource_list.out', 'w'),
                      stderr=('parsl_flux_resource_list.err', 'w'),
                      env=load_config["environment"]).result()
    assert r == 0

    pattern = re.compile(
      r'(\s+)STATE(\s+)NNODES(\s+)NCORES(\s+)NGPUS(\s+)NODELIST\n'
      r'(\s+)free(\s+)(3)(\s+)(\d+)(\s+)(0)(\s+)(\S+)\n'
      r'(\s+)allocated(\s+)(1)(\s+)(1)(\s+)(0)(\s+)(\S+)\n'
      r'(\s+)down(\s+)(0)(\s+)(0)(\s+)(0)',
    re.DOTALL)

    with open("parsl_flux_resource_list.out", "r") as f:
        assert pattern.match(f.read())
    
# Test Flux pmi barrier
def test_flux_pmi(load_config):
    p = pmi_barrier(stdout=('parsl_flux_pmi_barrier.out', 'w'),
                    stderr=('parsl_flux_pmi_barrier.err', 'w'),
                    env=load_config["environment"],
                    parsl_resource_specification={"num_tasks": 6, "num_nodes": 3},
                    ).result()
    assert p == 0
    with open("parsl_flux_pmi_barrier.out", "r") as f:
        assert re.match(r'[fƒ]\S+: completed pmi barrier on 6 tasks in [0-9.]+s.', f.read())

def test_compile_mpi_hello(load_config):
    shared_dir = "./"
    c = compile_mpi_hello(dirpath=shared_dir,
                          stdout=(os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.out"), 'w'),
                          stderr=(os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.err"), 'w'),
                          env=load_config["environment"],
                          ).result()
    assert c == 0
    assert os.path.isfile("mpi_hello.exe")
    assert os.stat("parsl_flux_mpi_hello_compile.out").st_size == 0

def test_run_mpi_hello(load_config):
    shared_dir = "./"
    # Remove any previous output if necessary
    if os.path.exists("parsl_flux_mpi_hello_run.out"):
        os.remove("parsl_flux_mpi_hello_run.out")
    if os.path.exists("parsl_flux_mpi_hello_run.err"):
        os.remove("parsl_flux_mpi_hello_run.err")
    hello = run_mpi_hello(dirpath=shared_dir,
                          stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.out"),
                          stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.err"),
                          env=load_config["environment"],
                          parsl_resource_specification={"num_tasks": 6, "num_nodes": 3},
                          ).result()
    assert hello == 0
    with open('parsl_flux_mpi_hello_run.out', 'r') as f:
        for line in f:
            assert re.match(r'Hello world from host \S+, rank \d+ out of 6', line)

def test_compile_mpi_pi(load_config):
    shared_dir = "./"
    c = compile_mpi_pi(dirpath=shared_dir,
                       stdout=(os.path.join(shared_dir, "parsl_flux_mpi_pi_compile.out"), 'w'),
                       stderr=(os.path.join(shared_dir, "parsl_flux_mpi_pi_compile.err"), 'w'),
                       env=load_config["environment"],
                       ).result()
    assert c == 0
    assert os.path.isfile("mpi_pi.exe")
    assert os.stat("parsl_flux_mpi_pi_compile.out").st_size == 0

def test_run_mpi_pi(load_config):
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
    cores_per_node = load_config["config"].executors[0].provider.cores_per_node
    pi1 = run_mpi_pi(dirpath=shared_dir,
                     stdout=os.path.join(shared_dir, "parsl_flux_mpi_pi1_run.out"),
                     stderr=os.path.join(shared_dir, "parsl_flux_mpi_pi1_run.err"),
                     env=load_config["environment"],
                     parsl_resource_specification={"num_tasks": cores_per_node * 2, "num_nodes": 2},
                     )
    pi2 = run_mpi_pi(dirpath=shared_dir,
                     stdout=os.path.join(shared_dir, "parsl_flux_mpi_pi2_run.out"),
                     stderr=os.path.join(shared_dir, "parsl_flux_mpi_pi2_run.err"),
                     env=load_config["environment"],
                     parsl_resource_specification={"num_tasks": cores_per_node, "num_nodes": 1},
                     )
    assert pi1.result() == 0
    assert pi2.result() == 0
    # Extract the hostnames used by pi1
    with open("parsl_flux_mpi_pi1_run.out", "r") as f:
        pi1_hosts=[]
        for line in f:
            if re.match(r"Host ", line):
                pi1_hosts.append(line.split()[1])
    # Extract the hostnames used by pi2
    with open("parsl_flux_mpi_pi2_run.out", "r") as f:
        pi2_hosts=[]
        for line in f:
            if re.match(r"Host ", line):
                pi2_hosts.append(line.split()[1])
    # Verify each pi test ran on a different set of nodes
    assert set(pi1_hosts).intersection(pi2_hosts) == set()

    with open("parsl_flux_mpi_pi1_run.out", "r") as pi1: 
        for line in pi1:
            if re.match(r"Start Time ", line):
                line = line.strip().lstrip("Start Time = ")
                pi1_start_time = dt.strptime(line, "%d/%m/%Y %H:%M:%S")
            if re.match(r"End Time ", line):
                line = line.strip().lstrip("End Time = ")
                pi1_end_time = dt.strptime(line, "%d/%m/%Y %H:%M:%S")

    with open("parsl_flux_mpi_pi2_run.out", "r") as pi2: 
        for line in pi2:
            if re.match(r"Start Time ", line):
                line = line.strip().lstrip("Start Time = ")
                pi2_start_time = dt.strptime(line, "%d/%m/%Y %H:%M:%S")
            if re.match(r"End Time ", line):
                line = line.strip().lstrip("End Time = ")
                pi2_end_time = dt.strptime(line, "%d/%m/%Y %H:%M:%S")
    assert pi1_start_time < pi2_start_time and pi2_start_time < pi1_end_time
