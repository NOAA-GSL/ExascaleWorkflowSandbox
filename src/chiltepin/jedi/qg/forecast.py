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
def _configure(workdir,
               nx=40, ny=20,
               dt="PT10M",
               duration="P2D",
               frequency="PT1H",
               atime="2009-12-31T00:00:00Z",
               background=None,
               install=None):
    # Get forecast default configuration file path
    config_file = os.path.dirname(__file__) + "/config/forecast.yaml"

    # Load the base configuration
    with open(config_file, "r") as stream:
        fcst_yaml = yaml.safe_load(stream)

    # Create overriding config from options
    options_yaml = yaml.load(textwrap.dedent(f"""
    geometry:
      nx: {nx}
      ny: {ny}
    output:
      datadir: {workdir}
    """).strip())

    # Merge options into default config
    _merge_nested_dicts(fcst_yaml, options_yaml)

    # Turn on read from file is background is provided
    if (background is not None):
        fcst_yaml["initial condition"]["read_from_file"] = 1

    # Make an empty forecast run directory
    if (os.path.exists(workdir)):
        shutil.rmtree(workdir)
    os.makedirs(workdir)

    # Dump the yaml config for input to forecast execution 
    with open(f"{workdir}/truth.yaml", "w") as yaml_file:
        yaml.dump(fcst_yaml, yaml_file, default_flow_style=False)

    # Return the configuration string
    return fcst_yaml

@bash_app(executors=['parallel'])
def _execute(env, workdir, install_path, tag="develop", stdout=None, stderr=None, configure=None):
    # Run the forecast executable
    return env + textwrap.dedent(f'''
    echo Started at $(date)
    echo Executing on $(hostname)
    {install_path}/jedi-bundle/{tag}/build/bin/qg_forecast.x {workdir}/truth.yaml
    echo Completed at $(date)        
    ''')

@join_app
def run(env,
        install_path,
        workdir,
        nx=40, ny=20,
        dt="PT10M",
        duration="P2D",
        frequency="PT1H",
        atime="2009-12-31T00:00:00Z",
        tag="develop",
        stderr=None,
        stdout=None,
        background=None,
        install=None):

    configure = _configure(workdir,
                           nx=nx, ny=ny,
                           dt=dt,
                           duration=duration,
                           frequency=frequency,
                           atime=atime,
                           background=background,
                           install=install)
    execute = _execute(env,
                       workdir,
                       install_path,
                       stdout=stdout,
                       stderr=stderr,
                       tag=tag,
                       configure=configure)
    return(execute)
