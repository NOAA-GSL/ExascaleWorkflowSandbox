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

# Get the analysis time from the command line
analysis_time_str = sys.argv[2]
analysis_time = datetime.strptime(analysis_time_str, "%Y-%m-%dT%H:%M:%SZ")

# Get the assimilation mode from the command line
assim_on_off = sys.argv[3]

# Extract path to experiment configuration
exp_config_path = os.path.dirname(os.path.abspath(exp_config_file))

# Load the experiment configuration
with open(exp_config_file, 'r') as file:
    exp_config = yaml.safe_load(file)

# Load the forecast config template
with open(f'{exp_config_path}/forecast.yaml') as file:
    fcst_config = yaml.safe_load(file)

# Get the experiment path
exp_path = f"{exp_config['experiment']['path']}/{exp_config['experiment']['name']}"

# Create forecast output directory
fcst_path = f'{exp_path}/forecasts/{analysis_time_str}/{assim_on_off}'
if not os.path.exists(fcst_path):
    os.makedirs(fcst_path)

# Set name of analysis file
analysis_file = f'forecast.an.{analysis_time_str}.PT0S.nc'

# Copy the analysis file into forecast output directory
if exp_config['experiment']['begin'] == analysis_time_str:
    # This is the first cycle, get the analysis from input_data
    shutil.copy(f'{exp_path}/truth/truth.fc.{analysis_time_str}.PT0S.nc', f'{fcst_path}/{analysis_file}')
elif assim_on_off == "off":
    # Assimilation is turned off, get the analysis from previous cycle of the "assimilation on" forecast
    cycle_freq = exp_config['experiment']['cycle frequency']
    prev_cycle = analysis_time - timedelta(0, leadtime.fcst_to_seconds(cycle_freq))
    prev_cycle_str = prev_cycle.strftime("%Y-%m-%dT%H:%M:%SZ")
    bkg_file = f'forecast.fc.{prev_cycle_str}.{cycle_freq}.nc'
    shutil.copy(f'{exp_path}/forecasts/{prev_cycle_str}/on/{bkg_file}', f'{fcst_path}/{analysis_file}')
elif assim_on_off == "on":
    # Assimilation is turned on, use the analysis provided by the assimilation step
    shutil.copy(f"{fcst_path}/{exp_config['assimilation']['type']}.an.{analysis_time_str}.nc", f"{fcst_path}/{analysis_file}")

# Set the forecast configuration initial conditions
if exp_config['experiment']['begin'] == analysis_time_str:
    fcst_config['initial condition']['read_from_file'] = 0
else:
    fcst_config['initial condition']['filename'] = f'{fcst_path}/{analysis_file}'
fcst_config['initial condition']['date'] = analysis_time_str

# Set the forecast configuration length
fcst_config['forecast length'] = exp_config['forecast']['length']

# Set the forecast configuraiton output
fcst_config['output']['datadir'] = fcst_path
fcst_config['output']['date'] = analysis_time_str
fcst_config['output']['frequency'] = exp_config['forecast']['frequency']

# Write out the forecast configuration
if (not os.path.exists(f'{exp_path}/yaml')):
    os.makedirs(f'{exp_path}/yaml')
with open(f"{exp_path}/yaml/forecast.{analysis_time_str}.yaml", 'w') as file:
    yaml.dump(fcst_config, file)

# Run the forecast
#with open(f'{fcst_path}/runForecast.{analysis_time_str}.log', 'w') as logfile:
#    subprocess.run([f"{exp_config['jedi path']}/bin/qg_forecast.x", f'{exp_path}/yaml/forecast.{analysis_time_str}.yaml'], stdout = logfile, stderr = sys.stdout)

