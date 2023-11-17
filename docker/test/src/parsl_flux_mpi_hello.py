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

# Update to import config for your machine
config = Config(
    executors=[
        FluxExecutor(
            label="flux",
            # Start Flux with srun and tell it there are 40 cores per node
            launch_cmd='srun --mpi=pmi2 --tasks-per-node=1 -c2 ' + FluxExecutor.DEFAULT_LAUNCH_CMD,
            provider=SlurmProvider(
                channel=LocalChannel(),
                nodes_per_block=3,
                init_blocks=1,
                partition='slurmpar',
                account='',
                walltime='00:10:00',
                launcher=SimpleLauncher(),
                worker_init='''
source /opt/conda_init.sh
conda activate chiltepin 
''',
            ),
        )
    ],
)


import os

parsl.load(config)

remote = False
shared_dir = './'

# Print out resources that Flux sees after it starts
@bash_app
def resource_list():
    return '''
    . /opt/conda_init.sh
    conda activate chiltepin
    flux resource list > parsl_flux_resource_list.txt
    '''

# Test Flux PMI launch
@bash_app
def pmi_barrier(parsl_resource_specification={}):
    return '''
    . /opt/conda_init.sh
    conda activate chiltepin
    env | grep -i flux > parsl_flux_pmi_barrier.txt
    env | grep -i pmi >> parsl_flux_pmi_barrier.txt
    export FLUX_PMI_LIBRARY_PATH=/opt/miniconda3/envs/chiltepin/lib/flux/libpmi.so
    flux pmi --method=libpmi:$FLUX_PMI_LIBRARY_PATH barrier >> parsl_flux_pmi_barrier.txt
    '''

# Compile the hello MPI program with Intel
@bash_app
def compile_app(dirpath, stdout=None, stderr=None, compiler="mpif90", parsl_resource_specification={"num_tasks": 1}):
    return '''
    . /opt/conda_init.sh
    conda activate chiltepin
    #. /opt/jedi_init.sh
    cd {}
    {} -o mpi_hello.exe mpi_hello.f90
    '''.format(dirpath, compiler)

# Run the hello MPI program with Intel
@bash_app
def mpi_hello(dirpath, stdout=None, stderr=None, app="./mpi_hello.exe", parsl_resource_specification={}):
    return '''
    . /opt/conda_init.sh
    conda activate chiltepin
    #. /opt/jedi_init.sh
    export FLUX_PMI_LIBRARY_PATH=/opt/miniconda3/envs/chiltepin/lib/flux/libpmi.so
    cd {}
    {}
    '''.format(dirpath, app)

# Check the Flux resource list
r = resource_list().result()

# Check the Flux pmi status
p = pmi_barrier(parsl_resource_specification={"num_tasks": 6, "num_nodes": 3}).result()

# complile the app and wait for it to complete (.result())
compile_app(dirpath=shared_dir,
            stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.out"),
            stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.err"),
           ).result()

# run the mpi app
hello = mpi_hello(dirpath=shared_dir,
                  stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.out"),
                  stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.err",),
                  parsl_resource_specification={"num_tasks": 6, "num_nodes": 3})

# Wait for the MPI app to finish
hello.result()

parsl.clear()
