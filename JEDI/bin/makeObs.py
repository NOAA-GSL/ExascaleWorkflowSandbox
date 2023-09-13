#!/bin/env python3

import sys
import os
import shutil
import yaml
from datetime import datetime, timedelta
import subprocess

import leadtime

# Get experiment yaml file path from comand line
exp_config_file = sys.argv[1]

# Extract path to experiment configuration
exp_config_path = os.path.dirname(os.path.abspath(exp_config_file))

# Load the experiment configuration
with open(exp_config_file, 'r') as file:
    exp_config = yaml.safe_load(file)

# Load the makeobs config template
with open(f'{exp_config_path}/make_obs_3d.yaml') as file:
    obs_config = yaml.safe_load(file)

# Get the experiment path
exp_path = f"{exp_config['experiment']['path']}/{exp_config['experiment']['name']}"
if not os.path.exists(f'{exp_path}/obs'):
    os.makedirs(f'{exp_path}/obs')

# Get the assimilation type (3d, 4d)
assimilation_type = exp_config['assimilation']['type']
    
# Get the experiment forecast time range parameters
exp_start_str = exp_config['experiment']['begin']
exp_start_time = datetime.strptime(exp_start_str, "%Y-%m-%dT%H:%M:%SZ")
exp_length = leadtime.fcst_to_seconds(exp_config['experiment']['length'])
exp_freq = leadtime.fcst_to_seconds(exp_config['experiment']['cycle frequency'])
exp_end = exp_start_time + timedelta(0, exp_length) - timedelta(0, exp_freq)

# Create obs for each analysis time in the experiment
t = exp_start_time + timedelta(0, exp_freq)
while t <= exp_end:

    print(f'Making obs for cycle: {t}')

    t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Set up obs output file configuration
    for observer in obs_config['observations']['observers']:
        obsfile = f'{exp_path}/obs/qg.truth.{assimilation_type}.{t_str}.nc'
        observer['obs space']['obsdataout']['engine']['obsfile'] = obsfile

    # Set up obs generation window
    assim_start_time = t + timedelta(0, leadtime.fcst_to_seconds(exp_config['assimilation']['window begin']))
    assim_length = exp_config['assimilation']['window length']
    obs_config['window begin'] = assim_start_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    obs_config['window length'] = assim_length
    
    # Set up the obs initial condition
    truth_leadtime = leadtime.seconds_to_fcst(int((assim_start_time - exp_start_time).total_seconds()))
    obs_config['initial condition']['filename'] = f"{exp_path}/truth/truth.fc.{exp_start_str}.{truth_leadtime}.nc"
    obs_config['initial condition']['date'] = obs_config['window begin']
        
    # Write out the obs configuration
    if (not os.path.exists(f'{exp_path}/yaml')):
        os.makedirs(f'{exp_path}/yaml')
    with open(f"{exp_path}/yaml/makeobs.{assimilation_type}.{t_str}.yaml", 'w') as file:
        yaml.dump(obs_config, file)

    # Run hofx to create the obs
    with open(f'{exp_path}/obs/makeObs.{assimilation_type}.{t_str}.log', 'w') as logfile:
        subprocess.run([f"{exp_config['jedi path']}/bin/qg_hofx.x", f'{exp_path}/yaml/makeobs.{assimilation_type}.{t_str}.yaml'], stdout = logfile, stderr = sys.stdout)

    
    # Increment cycle
    t = t + timedelta(0, exp_freq)
