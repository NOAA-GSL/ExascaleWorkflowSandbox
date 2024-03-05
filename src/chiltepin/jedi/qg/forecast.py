from parsl.app.app import bash_app, python_app, join_app
import os
import shutil
import textwrap
import yaml
from chiltepin.jedi.qg.config import merge_config, forecast_default

@python_app(executors=['serial'])
def _configure(rundir,
               config,
               install=None,
               assimilation=None):
    # Set forecast configuration to the default
    forecast_config = forecast_default()

    # Merge input configuration overrides into default
    merge_config(forecast_config, config)

    # Make an empty forecast run directory
    if (os.path.exists(rundir)):
        shutil.rmtree(rundir)
    os.makedirs(rundir)

    # Dump the yaml config for input to forecast execution
    config_filename = f"{rundir}/forecast.yaml"
    with open(config_filename, "w") as yaml_file:
        yaml.dump(forecast_config, yaml_file, default_flow_style=False)

    # Return the configuration yaml
    return config_filename

@bash_app(executors=['parallel'])
def _execute(env, rundir, install_path, config_file, tag="develop", stdout=None, stderr=None, assimilation=None):
    # Run the forecast executable
    return env + textwrap.dedent(f'''
    echo Started at $(date)
    echo Executing on $(hostname)
    {install_path}/jedi-bundle/{tag}/build/bin/qg_forecast.x {config_file}
    echo Completed at $(date)        
    ''')

@join_app
def run(env,
        install_path,
        tag,
        rundir,
        config,
        stdout=None,
        stderr=None,
        install=None,
        assimilation=None):

    configure = _configure(rundir,
                           config=config,
                           install=install,
                           assimilation=assimilation)
    execute = _execute(env,
                       rundir,
                       install_path,
                       config_file=configure,
                       tag=tag,
                       stdout=stdout,
                       stderr=stderr,
                       assimilation=assimilation)
    return(execute)
