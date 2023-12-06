#!/bin/env python3

import parsl
from parsl.app.app import python_app, bash_app

import os
import sys
import yaml

import chiltepin_config

with open(sys.argv[1], "r") as stream:
    try:
        yaml_config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print("Invalid taml configuration")
        raise(exc)

# Load the configuration
config, env_init = chiltepin_config.config_factory(yaml_config)
parsl.load(config)

shared_dir = './'

stack = env_init

# Print out resources that Flux sees after it starts
@bash_app
def resource_list(stack=stack):
    return '''
    {}
    flux resource list > parsl_flux_resource_list.txt
    '''.format(stack)

# Test Flux PMI launch
@bash_app
def pmi_barrier(stack=stack, parsl_resource_specification={}):
    return '''
    {}
    flux pmi barrier > parsl_flux_pmi_barrier.txt
    '''.format(stack)

# Compile the hello MPI program with GNU and OpenMPI
@bash_app
def compile_app(dirpath, stdout=None, stderr=None, stack=stack, parsl_resource_specification={"num_tasks": 1}):
    return '''
    {}
    cd {}
    $CHILTEPIN_MPIF90 -o mpi_hello.exe mpi_hello.f90
    '''.format(stack,dirpath)

# Run the hello MPI program with GNU and OpenMPI
@bash_app
def mpi_hello(dirpath, stdout=None, stderr=None, stack=stack, parsl_resource_specification={}):
    return '''
    {}
    cd {}
    ./mpi_hello.exe
    '''.format(stack, dirpath)

# Check the Flux resource list
r = resource_list(stack=stack).result()

# Check the Flux pmi status
p = pmi_barrier(stack=stack, parsl_resource_specification={"num_tasks": 6, "num_nodes": 3}).result()

# complile the app with chiltepin stack and wait for it to complete (.result())
compile_app(dirpath=shared_dir,
            stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.out"),
            stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.err"),
            stack=stack,
           ).result()

# run the mpi app with chiltepin stack
hello = mpi_hello(dirpath=shared_dir,
                  stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.out"),
                  stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.err",),
                  stack=stack,
                  parsl_resource_specification={"num_tasks": 6, "num_nodes": 3})

# Wait for the MPI app with chiltepin stack to finish
hello.result()

## complile the app with spack-stack stack and wait for it to complete (.result())
#compile_app(dirpath=shared_dir,
#            stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.out"),
#            stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.err"),
#            stack=spack_stack,
#           ).result()
#
## run the mpi app with spack-stack stack
#hello = mpi_hello(dirpath=shared_dir,
#                  stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.out"),
#                  stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.err",),
#                  stack=spack_stack,
#                  parsl_resource_specification={"num_tasks": 6, "num_nodes": 3})
#
# Wait for the MPI app with spack-stack stack to finish
#hello.result()

parsl.clear()
