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
            launch_cmd='srun --mpi=pmi2 --tasks-per-node=1 -c40 ' + FluxExecutor.DEFAULT_LAUNCH_CMD,
            provider=SlurmProvider(
                channel=LocalChannel(),
                nodes_per_block=1,
                init_blocks=1,
                partition='hercules',
                account='gsd-hpcs',
                walltime='01:00:00',
                launcher=SimpleLauncher(),
                worker_init='''
. /work/noaa/gsd-hpcs/charrop/hercules/SENA/opt/spack/share/spack/setup-env.sh
spack env activate flux
''',
            ),
        )
    ],
)


import os

parsl.load(config)

remote = False
jedi_path = '/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox/JEDI'

# Print out resources that Flux sees after it starts
@bash_app
def resource_list():
    return '''
    . /work/noaa/gsd-hpcs/charrop/hercules/SENA/opt/spack/share/spack/setup-env.sh
    spack env activate flux
    flux resource list > parsl_flux_resource_list.txt
    '''

# Run "truth" forecasts
@bash_app
def truth_app(jedi_path, stdout=None, stderr=None, parsl_resource_specification={}):
    return '''
    . {}/bin/setupenv-hercules.sh
    unset I_MPI_PMI_LIBRARY
    {}/bin/makeTruth.py {}/yaml/qg_experiment.yaml
    mkdir -p {}/experiments/qg.3dvar/truth
    cd {}/experiments/qg.3dvar/truth
    ../../../exascale-workflow-bundle/bin/qg_forecast.x ../yaml/truth.yaml
    '''.format(jedi_path, jedi_path, jedi_path, jedi_path, jedi_path)

# Create simulate obs
@bash_app
def obs_app(jedi_path, stdout=None, stderr=None, parsl_resource_specification={"num_tasks": 1}):
    return '''
    #. {}/bin/setupenv-hercules.sh
    #unset I_MPI_PMI_LIBRARY
    {}/bin/makeObs.py {}/yaml/qg_experiment.yaml
    '''.format(jedi_path, jedi_path, jedi_path)

## Compile the hello MPI program with Intel
#@bash_app
#def compile_app(dirpath, stdout=None, stderr=None, compiler="mpiifort -fc=ifx", parsl_resource_specification={}):
#    return '''
#    module load intel-oneapi-compilers/2022.2.1 intel-oneapi-mpi/2021.7.1
#    cd {}
#    {} -o mpi_hello.exe mpi_hello.f90
#    '''.format(dirpath, compiler)

# Run the hello MPI program with Intel
#@bash_app
#def mpi_hello(dirpath, stdout=None, stderr=None, app="./mpi_hello.exe", parsl_resource_specification={}):
#    return '''
#    # Flux requires I_MPI_PMI_LIBRARY to be unset because it provides its own PMI
#    module load intel-oneapi-compilers/2022.2.1 intel-oneapi-mpi/2021.7.1
#    unset I_MPI_PMI_LIBRARY
#    cd {}
#    {}
#    '''.format(dirpath, app)

# Check the Flux resource list
r = resource_list().result()

# Run the truth forecast
truth = truth_app(jedi_path='/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox/JEDI',
                  stdout=os.path.join(jedi_path, 'truth.out'),
                  stderr=os.path.join(jedi_path, 'truth.err'),
                  parsl_resource_specification={"num_tasks": 1, "num_nodes": 1}
                  ).result()

# Create the simulated observations
#obs = obs_app(jedi_path='/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox/JEDI',
#              stdout=os.path.join(jedi_path, 'makeobs.out'),
#              stderr=os.path.join(jedi_path, 'makeobs.err')
#              ).result()

# Run cycled experiment
# t=0
# while t < exp_end_date:
# .....
#   Run assimilation
#   Run forecast
#

# Run verification



# complile the app and wait for it to complete (.result())
#compile_app(dirpath=shared_dir,
#            stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.out"),
#            stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_compile.err"),
#           ).result()
#
## run the mpi app
#hello = mpi_hello(dirpath=shared_dir,
#                  stdout=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.out"),
#                  stderr=os.path.join(shared_dir, "parsl_flux_mpi_hello_run.err",),
#                  parsl_resource_specification={"num_tasks": 120, "num_nodes": 3})
#
## Wait for the MPI app to finish
#hello.result()

parsl.clear()