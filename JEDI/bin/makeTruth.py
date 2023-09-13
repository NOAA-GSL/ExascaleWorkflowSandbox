#!/bin/env python3

import sys
import os
import shutil
import yaml
import subprocess

import leadtime

# Get experiment yaml file path from comand line
exp_config_file = sys.argv[1]

# Extract path to experiment configuration
exp_config_path = os.path.dirname(os.path.abspath(exp_config_file))

# Load the experiment configuration
with open(exp_config_file, 'r') as file:
    exp_config = yaml.safe_load(file)

# Load the truth config template
with open(f'{exp_config_path}/truth.yaml') as file:
    truth_config = yaml.safe_load(file)

# Create the experiment directory
exp_path = f"{exp_config['experiment']['path']}/{exp_config['experiment']['name']}"
if os.path.exists(exp_path):
    shutil.rmtree(exp_path)
else:
    os.makedirs(exp_path)

# Configure truth's initial conditions
truth_config['initial condition']['date'] = exp_config['experiment']['begin']

# Configure truth's length
exp_length = exp_config['experiment']['length']
fcst_length = exp_config['forecast']['length']
truth_config['forecast length'] = leadtime.seconds_to_fcst(leadtime.fcst_to_seconds(exp_length) + leadtime.fcst_to_seconds(fcst_length))

# Configure truth's output
truth_config['output']['datadir'] = f'{exp_path}/truth'
truth_config['output']['frequency'] = exp_config['forecast']['frequency']
truth_config['output']['date'] = exp_config['experiment']['begin']

# Write out the truth configuration
os.makedirs(f'{exp_path}/yaml')
with open(f'{exp_path}/yaml/truth.yaml', 'w') as file:
    yaml.dump(truth_config, file)

# Save the experiment configuration with the experiment
with open(f"{exp_path}/yaml/{exp_config['experiment']['name']}.yaml", 'w') as file:
    yaml.dump(exp_config, file)

# Run the truth forecast
os.makedirs(f'{exp_path}/truth')
with open(f'{exp_path}/truth/makeTruth.log', 'w') as logfile:
    subprocess.run([f"{exp_config['jedi path']}/bin/qg_forecast.x", f'{exp_path}/yaml/truth.yaml'], stdout = logfile, stderr = sys.stdout)

