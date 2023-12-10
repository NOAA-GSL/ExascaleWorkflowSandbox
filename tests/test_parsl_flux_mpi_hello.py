import os
import parsl
from parsl.app.app import python_app, bash_app
import pytest
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
def resource_list(env=""):
    return '''
    {}
    flux resource list > parsl_flux_resource_list.txt
    '''.format(env)

# Test Flux PMI launch
@bash_app
def pmi_barrier(env="", parsl_resource_specification={}):
    return '''
    {}
    flux pmi barrier > parsl_flux_pmi_barrier.txt
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
    r = resource_list(env=load_config).result()
    
# Test Flux pmi barrier
def test_flux_pmi(load_config):
    p = pmi_barrier(env=load_config, parsl_resource_specification={"num_tasks": 6, "num_nodes": 3}).result()

def test_compile_app(load_config):
    shared_dir = "./"
    compile_app(dirpath=shared_dir,
                stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.out"),
                stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.err"),
                env=load_config,
                ).result()

def test_mpi_hello(load_config):
    shared_dir = "./"
    hello = mpi_hello(dirpath=shared_dir,
                      stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.out"),
                      stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.err",),
                      env=load_config,
                      parsl_resource_specification={"num_tasks": 6, "num_nodes": 3})
    # Wait for the MPI app with chiltepin stack to finish
    hello.result()
