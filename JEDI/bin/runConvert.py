#!/bin/env python3

import sys
import os
import shutil
import yaml
import re
from datetime import datetime, timedelta
import subprocess

import leadtime

# Get experiment yaml file path from comand line
exp_config_file = sys.argv[1]

# Get the leadtime to convert from command line
fcst_lead = sys.argv[2]

# Extract path to experiment configuration
exp_config_path = os.path.dirname(os.path.abspath(exp_config_file))

# Load the experiment configuration
with open(exp_config_file, 'r') as file:
    exp_config = yaml.safe_load(file)

# Get the experiment path
exp_path = f"{exp_config['experiment']['path']}/{exp_config['experiment']['name']}"

# Load the convertstate config template
with open(f'{exp_config_path}/convertstate.yaml') as file:
    convertstate_config = yaml.safe_load(file)

    # Load the diffstates config template
with open(f'{exp_config_path}/diffstates.yaml') as file:
    diffstates_config = yaml.safe_load(file)

# Get the driver path
driver_path = os.path.dirname(os.path.abspath(sys.argv[0]))

# Get the experiment forecast time range parameters
exp_start_str = exp_config['experiment']['begin']
exp_start_time = datetime.strptime(exp_start_str, "%Y-%m-%dT%H:%M:%SZ")
exp_length = leadtime.fcst_to_seconds(exp_config['experiment']['length'])
exp_freq = leadtime.fcst_to_seconds(exp_config['experiment']['cycle frequency'])
exp_end = exp_start_time + timedelta(0, exp_length) - timedelta(0, exp_freq)

# Get the verification spinup seconds
spinup = leadtime.fcst_to_seconds(exp_config['verification']['spinup'])

# Create the verification output directory
verify_path = f'{exp_path}/verify'
if not os.path.exists(verify_path):
    os.makedirs(verify_path)

print(f'Converting forecast lead time: {fcst_lead}')
    
# Construct the truth forecast filename
truth_filename = f'{exp_path}/truth/truth.fc.{exp_start_str}.{fcst_lead}.nc'

# Construct the interpolated truth forecast filename
convert_filename = f'{verify_path}/convert.fc.{exp_start_str}.{fcst_lead}.nc'

# Interpolate truth onto the forecast geometry
for state in convertstate_config['states']:
    state['input']['date'] = exp_start_str
    state['input']['filename'] = truth_filename
    state['output']['date'] = exp_start_str
    state['output']['datadir'] = verify_path
    with open(f'{exp_path}/yaml/convertstate.{fcst_lead}.yaml', 'w') as file:
        yaml.dump(convertstate_config, file)
    #with open(f'{verify_path}/convertstate.{exp_start_str}.{fcst_lead}.log', 'w') as logfile:
    #    subprocess.run([f"{exp_config['jedi path']}/bin/qg_convertstate.x", f'{exp_path}/yaml/convertstate.{exp_start_str}.{fcst_lead}.yaml'], stdout = logfile, stderr = sys.stdout)

