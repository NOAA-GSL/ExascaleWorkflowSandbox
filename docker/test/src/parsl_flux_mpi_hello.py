#!/bin/env python3

import parsl
from parsl.app.app import python_app, bash_app
from parsl.config import Config
from parsl.channels import LocalChannel
from parsl.providers import SlurmProvider
from parsl.executors import FluxExecutor
from parsl.launchers import SimpleLauncher
from parsl.addresses import address_by_hostname
from parsl.data_provider.files import File

def config_factory(platform="chiltepin"):

    if (platform=="chiltepin"):
        cores_per_node=2
        partition="slurmpar"
        account=""
    elif (platform=="jedi"):
        pass
    elif (platform=="hercules"):
        cores_per_node=20
        partition="hercules"
        account="gsd-hpcs"
    else:
        raise Exception("Invalid platform")

    # Update to import config for your machine
    config = Config(
        executors=[
            FluxExecutor(
                label="flux",
                # Start Flux with srun and tell it how many cores per node to expect
                launch_cmd=f'srun --mpi=pmi2 --tasks-per-node=1 -c{cores_per_node} ' + FluxExecutor.DEFAULT_LAUNCH_CMD,
                provider=SlurmProvider(
                    channel=LocalChannel(),
                    nodes_per_block=3,
                    init_blocks=1,
                    partition=partition,
                    account=account,
                    walltime='00:10:00',
                    launcher=SimpleLauncher(),
                    worker_init='''
                    ''',
                ),
            )
        ],
    )

    return config


import os
import sys

# Set FLUX_SSH
os.environ["FLUX_SSH"] = "ssh"

# Load the configuration
config = config_factory(sys.argv[1])
parsl.load(config)

shared_dir = './'

def stack_factory(platform="chiltepin"):

    if (platform=="chiltepin"):
        return '''
        export FLUX_PMI_LIBRARY_PATH=/opt/miniconda3/envs/chiltepin/lib/flux/libpmi.so
        export OMPI_MCA_btl=self,tcp
        export CHILTEPIN_MPIF90=mpif90
        '''
    elif (platform=="jedi"):
        return '''
        #    . /opt/jedi_init.sh
        '''
    elif (platform=="hercules"):
        return '''
        module load intel-oneapi-compilers/2023.1.0
        module load intel-oneapi-mpi/2021.7.1
        unset I_MPI_PMI_LIBRARY
        export CHILTEPIN_MPIF90="mpiifort -fc=ifx"
        '''
    else:
        raise Exception("Invalid platform")

stack = stack_factory(sys.argv[1])

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
