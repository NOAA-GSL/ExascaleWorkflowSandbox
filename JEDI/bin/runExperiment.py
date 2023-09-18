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

# Get the driver path
driver_path = os.path.dirname(os.path.abspath(sys.argv[0]))

# Get the experiment forecast time range parameters
exp_start_str = exp_config['experiment']['begin']
exp_start_time = datetime.strptime(exp_start_str, "%Y-%m-%dT%H:%M:%SZ")
exp_length = leadtime.fcst_to_seconds(exp_config['experiment']['length'])
exp_freq = leadtime.fcst_to_seconds(exp_config['experiment']['cycle frequency'])
exp_end = exp_start_time + timedelta(0, exp_length) - timedelta(0, exp_freq)

# Create "truth" forecast
subprocess.run([f'{driver_path}/makeTruth.py', f'{exp_config_file}'], stdout = sys.stdout, stderr = sys.stdout)

# Create simulate obs from truth
subprocess.run([f'{driver_path}/makeObs.py', f'{exp_config_file}'], stdout = sys.stdout, stderr = sys.stdout)

# Run experiment cycles
t = exp_start_time
while t <= exp_end:

    t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f'Running cycle {t_str}')

    # Run the assimilation if needed
    if t > exp_start_time:
        # Run the assimilation
        subprocess.run([f'{driver_path}/runAssimilation.py', f'{exp_config_file}', f'{t_str}'], stdout = sys.stdout, stderr = sys.stdout)

    # Run the forecast
    subprocess.run([f'{driver_path}/runForecast.py', f'{exp_config_file}', f'{t_str}'], stdout = sys.stdout, stderr = sys.stdout)

    # Increment cycle
    t = t + timedelta(0, exp_freq)

# Run experiment verification
subprocess.run([f'{driver_path}/runVerify.py', f'{exp_config_file}'], stdout = sys.stdout, stderr = sys.stdout)
