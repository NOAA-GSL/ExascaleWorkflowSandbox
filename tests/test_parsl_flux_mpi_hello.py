import os
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

# Compile the hello MPI program with GNU and OpenMPI
@bash_app
def compile_app(dirpath, stdout=None, stderr=None, env="", parsl_resource_specification={"num_tasks": 1}):
    return '''
    {}
    cd {}
    $CHILTEPIN_MPIF90 -o mpi_hello.exe mpi_hello.f90
    '''.format(env,dirpath)

# Run the hello MPI program with GNU and OpenMPI
@bash_app
def mpi_hello(dirpath, stdout=None, stderr=None, env="", parsl_resource_specification={}):
    return '''
    {}
    cd {}
    ./mpi_hello.exe
    '''.format(env, dirpath)

# Set up fixture to initialize and cleanup Parsl
@pytest.fixture(scope="module")
def load_config(config_file, request):
    yaml_config = parse_config(config_file)
    config, environment = config_factory(yaml_config)
    parsl.load(config)
    request.addfinalizer(parsl.clear)
    return environment

# Test Flux resource list
def test_flux_resource_list(load_config):
    r = resource_list(stdout=('parsl_flux_resource_list.out', 'w'),
                      stderr=('parsl_flux_resource_list.err', 'w'),
                      env=load_config).result()
    assert r == 0
    
# Test Flux pmi barrier
def test_flux_pmi(load_config):
    p = pmi_barrier(stdout=('parsl_flux_pmi_barrier.out', 'w'),
                    stderr=('parsl_flux_pmi_barrier.err', 'w'),
                    env=load_config,
                    parsl_resource_specification={"num_tasks": 6, "num_nodes": 3},
                    ).result()
    assert p == 0
    with open("parsl_flux_pmi_barrier.out", "r") as f:
        assert re.match(r'ƒ\S+: completed pmi barrier on 6 tasks in [0-9.]+s.', f.read())

def test_compile_app(load_config):
    shared_dir = "./"
    c = compile_app(dirpath=shared_dir,
                    stdout=(os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.out"), 'w'),
                    stderr=(os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.err"), 'w'),
                    env=load_config,
                    ).result()
    assert c == 0
    assert os.path.isfile("mpi_hello.exe")
    assert os.stat("parsl_flux_mpi_hello_compile.out").st_size == 0

def test_mpi_hello(load_config):
    shared_dir = "./"
    # Remove any previous output if necessary
    if os.path.exists("parsl_flux_mpi_hello_run.out"):
        os.remove("parsl_flux_mpi_hello_run.out")
    if os.path.exists("parsl_flux_mpi_hello_run.err"):
        os.remove("parsl_flux_mpi_hello_run.err")
    hello = mpi_hello(dirpath=shared_dir,
                      stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.out"),
                      stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.err"),
                      env=load_config,
                      parsl_resource_specification={"num_tasks": 6, "num_nodes": 3},
                      ).result()
    assert hello == 0
