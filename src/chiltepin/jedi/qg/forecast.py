from parsl.app.app import bash_app, python_app, join_app
import os
import shutil
import textwrap
import yaml

def _merge_nested_dicts(d1, d2):
    for key, value in d2.items():
        if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
            _merge_nested_dicts(d1[key], value)
        else:
            d1[key] = value


@python_app(executors=['serial'])
def _configure(rundir,
               config,
               install=None,
               assimilation=None):
    # Get forecast default configuration file path
    config_file = os.path.dirname(__file__) + "/config/forecast.yaml"

    # Load the base configuration
    with open(config_file, "r") as stream:
        fcst_yaml = yaml.safe_load(stream)

    # Merge input configuration
    _merge_nested_dicts(fcst_yaml, config)

    # Make an empty forecast run directory
    if (os.path.exists(rundir)):
        shutil.rmtree(rundir)
    os.makedirs(rundir)

    # Dump the yaml config for input to forecast execution 
    with open(f"{rundir}/forecast.yaml", "w") as yaml_file:
        yaml.dump(fcst_yaml, yaml_file, default_flow_style=False)

    # Return the configuration string
    return fcst_yaml

@bash_app(executors=['parallel'])
def _execute(env, rundir, install_path, tag="develop", stdout=None, stderr=None, configure=None, assimilation=None):
    # Run the forecast executable
    return env + textwrap.dedent(f'''
    echo Started at $(date)
    echo Executing on $(hostname)
    {install_path}/jedi-bundle/{tag}/build/bin/qg_forecast.x {rundir}/forecast.yaml
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
                       tag=tag,
                       stdout=stdout,
                       stderr=stderr,
                       configure=configure,
                       assimilation=assimilation)
    return(execute)
