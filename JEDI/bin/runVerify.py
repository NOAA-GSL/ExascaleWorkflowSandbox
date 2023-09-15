#!/bin/env python3

import sys
import os
import shutil
import yaml
import re
from datetime import datetime, timedelta
import subprocess
import matplotlib.pyplot as plt

import leadtime

# Get experiment yaml file path from comand line
exp_config_file = sys.argv[1]

# Extract path to experiment configuration
exp_config_path = os.path.dirname(os.path.abspath(exp_config_file))

# Load the experiment configuration
with open(exp_config_file, 'r') as file:
    exp_config = yaml.safe_load(file)

# Get the experiment path
exp_path = f"{exp_config['experiment']['path']}/{exp_config['experiment']['name']}"

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

# Initialize dictionary for storing MSE for each forecast lead time
mses = { "on" : {}, "off" : {} }

# Loop over lead times and cacluate MSE/RMSE for each
f=0
while f <= leadtime.fcst_to_seconds(exp_config['forecast']['length']):
    mses["on"][f] = []
    mses["off"][f] = []

    print(f'Verifying forecast lead time: {leadtime.seconds_to_fcst(f)}')
    
    # Verify this forecast lead time, f, for each cycle, t
    t = exp_start_time + timedelta(0, spinup)
    t_str = t.strftime("%Y-%m-%dT%H:%M:%SZ")
    while t <= exp_end:
        # Calculate the valid time for this cycle and lead time
        valid_time = t + timedelta(0, f)

        # Find truth forecast lead time corresponding to the valid time
        valid_truth_fcst = leadtime.seconds_to_fcst(int((valid_time - exp_start_time).total_seconds()))

        # Construct the truth forecast filename
        truth_filename = f'{exp_path}/truth/truth.fc.{exp_start_str}.{valid_truth_fcst}.nc'

        # Get MSE for forecasts with and without assimilation turned on
        for assim_on_off in ["on", "off"]:

            # Get the forecast directory
            fcst_path = f'{exp_path}/forecasts/{t_str}/{assim_on_off}'

            # Construct the forecast file name
            fcst_filename = f"{fcst_path}/forecast.fc.{t_str}.{leadtime.seconds_to_fcst(f)}.nc"

            # Calculate the MSE
            proc = subprocess.run(['cdo', '-s', '-infon', '-fldmean', '-sqr', '-selname,q,u,v', '-sellevel,1', '-sub', truth_filename, fcst_filename ], capture_output = True, text=True)
            mse_q_pattern = re.compile('(\S+)\s* : q')
            mse_u_pattern = re.compile('(\S+)\s* : u')
            mse_v_pattern = re.compile('(\S+)\s* : v')
            match_q = mse_q_pattern.search(proc.stdout)
            match_u = mse_u_pattern.search(proc.stdout)
            match_v = mse_v_pattern.search(proc.stdout)
            if (match_q):
                mse_q = float(match_q.group(1))
            if (match_u):
                mse_u = float(match_u.group(1))
            if (match_v):
                mse_v = float(match_v.group(1))
            mses[assim_on_off][f].append(mse_q)
            #mses[assim_on_off][f].append(mse_q)
            #mses[assim_on_off][f].append(mse_q)

        # Increment cycle
        t = t + timedelta(0, exp_freq)

    # Increment forecast lead time
    f = f + leadtime.fcst_to_seconds(exp_config['forecast']['frequency'])

# Write out the verification stats
with open(f'{exp_path}/verify/verify.dat', 'w') as datafile:

    # Write column headers
    datafile.write("LeadTime AssimilationOn AssimilationOff\n")

    # Write mean MSE for each lead time to data file
    f = 0
    while f <= leadtime.fcst_to_seconds(exp_config['forecast']['length']):

        mseOn = 0
        mseOff = 0
        i = 0
        size = len(mses["on"][f])
        while i < size:
            mseOn += mses["on"][f][i]
            mseOff += mses["off"][f][i]
            i += 1

        datafile.write(f"{leadtime.seconds_to_fcst(f)} {mseOn / size} {mseOff / size}\n")

        f = f + leadtime.fcst_to_seconds(exp_config['forecast']['frequency'])


