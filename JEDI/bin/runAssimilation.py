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

# Extract path to experiment configuration
exp_config_path = os.path.dirname(os.path.abspath(exp_config_file))

# Load the experiment configuration
with open(exp_config_file, 'r') as file:
    exp_config = yaml.safe_load(file)

# Get the assimilation type (3d, 4d)
assimilation_type = exp_config['assimilation']['type']
assimilation_algorithm = exp_config['assimilation']['algorithm']
    
# Load the assimilation config template
with open(f'{exp_config_path}/{assimilation_type}.{assimilation_algorithm}.yaml') as file:
    assim_config = yaml.safe_load(file)

# Get the experiment path
exp_path = f"{exp_config['experiment']['path']}/{exp_config['experiment']['name']}"

# Create the assimilation output directory
fcst_path = f'{exp_path}/forecasts/{analysis_time_str}/on'
if not os.path.exists(fcst_path):
    os.makedirs(fcst_path)

# Set up the assimilation window configuration
window_begin = analysis_time + timedelta(0, leadtime.fcst_to_seconds(exp_config['assimilation']['window begin']))
assim_config['cost function']['window begin'] = window_begin.strftime("%Y-%m-%dT%H:%M:%SZ")
assim_config['cost function']['window length'] = exp_config['assimilation']['window length']

# Get previous cycle time
prev_cycle = analysis_time - timedelta(0, leadtime.fcst_to_seconds(exp_config['experiment']['cycle frequency']))
prev_cycle_str = prev_cycle.strftime("%Y-%m-%dT%H:%M:%SZ")

# Set up the background file configuration
if assimilation_type == "4dvar":
    # 4DVar background files must be at the beginning of the assimilation window
    bkg_offset = leadtime.fcst_to_seconds(exp_config['assimilation']['window begin']) + \
                 leadtime.fcst_to_seconds(exp_config['experiment']['cycle frequency'])
else:
    # 3DVar background files must be at the center of the assimilation window
    bkg_offset = leadtime.fcst_to_seconds(exp_config['assimilation']['window begin']) + \
                 leadtime.fcst_to_seconds(exp_config['experiment']['cycle frequency']) + \
                 (leadtime.fcst_to_seconds(exp_config['assimilation']['window length']) // 2)
bkg_date = analysis_time - \
           timedelta(0, leadtime.fcst_to_seconds(exp_config['experiment']['cycle frequency'])) + \
           timedelta(0, bkg_offset)
bkg_date_str = bkg_date.strftime("%Y-%m-%dT%H:%M:%SZ")
assim_config['cost function']['background']['date'] = bkg_date_str
assim_config['cost function']['background']['filename'] = f'{exp_path}/forecasts/{prev_cycle_str}/on/forecast.fc.{prev_cycle_str}.{leadtime.seconds_to_fcst(bkg_offset)}.nc'

# Set up the obs file configuration
observers = assim_config['cost function']['observations']['observers']
for observer in observers:
    obs_space = observer['obs space']
    obs_space['obsdatain']['engine']['obsfile'] = f'{exp_path}/obs/qg.truth.{assimilation_type}.{analysis_time_str}.nc'
    obs_space['obsdataout']['engine']['obsfile'] = f'{fcst_path}/qg.{assimilation_type}.{analysis_time_str}.nc'
    
# Set up assimilation output configuration
assim_config['output']['datadir'] = fcst_path
iterations_config = assim_config['variational']['iterations']
for iteration in iterations_config:
    print(iteration)
    iteration['online diagnostics']['increment']['datadir'] = fcst_path
assim_config['final']['increment']['output']['datadir'] = fcst_path

# Write out the forecast configuration
if (not os.path.exists(f'{exp_path}/yaml')):
    os.makedirs(f'{exp_path}/yaml')
with open(f"{exp_path}/yaml/{assimilation_type}.{assimilation_algorithm}.{analysis_time_str}.yaml", 'w') as file:
    yaml.dump(assim_config, file)
        
# Run the forecast
with open(f'{fcst_path}/{assimilation_type}.{assimilation_algorithm}.{analysis_time_str}.log', 'w') as logfile:
    subprocess.run([f"{exp_config['jedi path']}/bin/qg_4dvar.x", f'{exp_path}/yaml/{assimilation_type}.{assimilation_algorithm}.{analysis_time_str}.yaml'], stdout = logfile, stderr = sys.stdout)
