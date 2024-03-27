import os
import textwrap

import yaml
from chiltepin.jedi.qg.config import merge_config_dict, var3d_default
from parsl.app.app import bash_app, join_app, python_app


@python_app(executors=["serial"])
def _configure_var3d(rundir, config, obs=None, background=None):

    # Set var3d configuration to the default
    var3d_config = var3d_default()

    # Merge input configuration overrides into default
    merge_config_dict(var3d_config, config)

    # Make var3d run directory if necessary
    if not os.path.exists(rundir):
        os.makedirs(rundir)

    # Dump the yaml config for input to var3d execution
    config_filename = f"{rundir}/var3d.yaml"
    with open(config_filename, "w") as yaml_file:
        yaml.dump(var3d_config, yaml_file, default_flow_style=False)

    # Return the configuration file path
    return config_filename


@bash_app(executors=["parallel"])
def _execute_var3d(
    env, rundir, install_path, config_file, tag="develop", stdout=None, stderr=None
):
    # Run the 3dvar executable
    return env + textwrap.dedent(
        f"""
    echo Started at $(date)
    echo Executing on $(hostname)
    {install_path}/jedi-bundle/{tag}/build/bin/qg_4dvar.x {config_file}
    echo Completed at $(date)
    """
    )


@join_app
def run_3dvar(
    env,
    install_path,
    tag,
    rundir,
    config,
    stdout=None,
    stderr=None,
    obs=None,
    background=None,
):

    configure = _configure_var3d(rundir, config=config, obs=obs, background=background)

    execute = _execute_var3d(
        env,
        rundir,
        install_path,
        config_file=configure,
        tag=tag,
        stdout=stdout,
        stderr=stderr,
    )

    return execute
