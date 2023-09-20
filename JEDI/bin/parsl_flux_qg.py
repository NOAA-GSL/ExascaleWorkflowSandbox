#!/bin/env python3

import sys
import yaml
from datetime import datetime, timedelta

import leadtime

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
    export JEDI_PATH={}
    . $JEDI_PATH/bin/setupenv-hercules.sh
    unset I_MPI_PMI_LIBRARY
    $JEDI_PATH/bin/makeTruth.py $JEDI_PATH/yaml/qg_experiment.yaml
    mkdir -p $JEDI_PATH/experiments/qg.3dvar/truth
    cd $JEDI_PATH/experiments/qg.3dvar/truth
    $JEDI_PATH/exascale-workflow-bundle/bin/qg_forecast.x $JEDI_PATH/experiments/qg.3dvar/yaml/truth.yaml
    '''.format(jedi_path)

# Create simulate obs
@bash_app
def obs_app(jedi_path, t, assimilation_type, stdout=None, stderr=None, parsl_resource_specification={}):
    return '''
    export JEDI_PATH={}
    export ANALYSIS_TIME={}
    export TYPE={}
    . $JEDI_PATH/bin/setupenv-hercules.sh
    unset I_MPI_PMI_LIBRARY
    $JEDI_PATH/bin/makeOb.py $JEDI_PATH/yaml/qg_experiment.yaml $ANALYSIS_TIME
    mkdir -p $JEDI_PATH/experiments/qg.3dvar/obs
    cd $JEDI_PATH/experiments/qg.3dvar/obs
    $JEDI_PATH/exascale-workflow-bundle/bin/qg_hofx.x $JEDI_PATH/experiments/qg.3dvar/yaml/makeobs.$TYPE.$ANALYSIS_TIME.yaml
    '''.format(jedi_path, t, assimilation_type)


# Run assimilation
@bash_app
def obs_app(jedi_path, t, assimilation_type, stdout=None, stderr=None, parsl_resource_specification={}):
    return '''
    export JEDI_PATH={}
    export ANALYSIS_TIME={}
    export TYPE={}
    export ALGORITHM={}
    . $JEDI_PATH/bin/setupenv-hercules.sh
    unset I_MPI_PMI_LIBRARY
    $JEDI_PATH/bin/runAssimilation.py $JEDI_PATH/yaml/qg_experiment.yaml $ANALYSIS_TIME
    cd $JEDI_PATH/experiments/qg.3dvar/forecasts/$ANALYSIS_TIME/on
    $JEDI_PATH/exascale-workflow-bundle/bin/qg_4dvar.x $JEDI_PATH/experiments/qg.3dvar/yaml/$TYPE.$ALGORITHM.$ANALYSIS_TIME.yaml
    '''.format(jedi_path, t, assimilation_type, assimilation_algorithm)

#############################
#
# Begin workflow program
#
#############################

# Get experiment yaml file path from comand line
exp_config_file = sys.argv[1]

# Extract path to experiment configuration
exp_config_path = os.path.dirname(os.path.abspath(exp_config_file))

# Load the experiment configuration
with open(exp_config_file, 'r') as file:
    exp_config = yaml.safe_load(file)

# Get the driver path
driver_path = os.path.dirname(os.path.abspath(sys.argv[0]))

# Get the experiment forecast time range parameters
exp_start_str = exp_config['experiment']['begin']
exp_start_time = datetime.strptime(exp_start_str, "%Y-%m-%dT%H:%M:%SZ")
exp_length = leadtime.fcst_to_seconds(exp_config['experiment']['length'])
exp_freq = leadtime.fcst_to_seconds(exp_config['experiment']['cycle frequency'])
exp_end = exp_start_time + timedelta(0, exp_length) - timedelta(0, exp_freq)

# Check the Flux resource list
r = resource_list().result()

# Run the truth forecast
truth = truth_app(jedi_path='/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox/JEDI',
                  stdout=os.path.join(jedi_path, 'truth.out'),
                  stderr=os.path.join(jedi_path, 'truth.err'),
                  parsl_resource_specification={"num_tasks": 1, "num_nodes": 1}
                  ).result()

# Run experiment cycles
t = exp_start_time
while t <= exp_end:

    t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f'Running cycle {t_str}')

    # Run the assimilation if needed
    if t > exp_start_time:

        # Create simulated obs for this analysis time
        obs = obs_app(jedi_path='/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox/JEDI',
                      t=t_str,
                      assimilation_type='3dvar',
                      stdout=os.path.join(jedi_path, 'obs.out'),
                      stderr=os.path.join(jedi_path, 'obs.err'),
                      parsl_resource_specification={"num_tasks": 1, "num_nodes": 1}
                      ).result()

        # Run the assimilation
        3dvar = obs_app(jedi_path='/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox/JEDI',
                        t=t_str,
                        assimilation_type='3dvar',
                        assimilation_algorithm='dripcg',
                        stdout=os.path.join(jedi_path, '3dvar.out'),
                        stderr=os.path.join(jedi_path, '3dvar.err'),
                        parsl_resource_specification={"num_tasks": 1, "num_nodes": 1}
                        ).result()

    # Run the forecast
    #subprocess.run([f'{driver_path}/runForecast.py', f'{exp_config_file}', f'{t_str}'], stdout = sys.stdout, stderr = sys.stdout)

    # Increment cycle
    t = t + timedelta(0, exp_freq)

parsl.clear()
