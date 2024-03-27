import os
import textwrap

import yaml
from chiltepin.jedi.qg.config import make_obs3d_default, merge_config_dict
from parsl.app.app import bash_app, join_app, python_app


@python_app(executors=["serial"])
def _configure_make_obs3d(rundir, config, truth=None):

    # Set makeobs3d configuration to the default
    make_obs3d_config = make_obs3d_default()

    # Merge input configuration overrides into default
    merge_config_dict(make_obs3d_config, config)

    # Make makeobs3d run directory if necessary
    if not os.path.exists(rundir):
        os.makedirs(rundir)

    # Dump the yaml config for input to makeobs3d execution
    config_filename = f"{rundir}/make_obs3d.yaml"
    with open(config_filename, "w") as yaml_file:
        yaml.dump(make_obs3d_config, yaml_file, default_flow_style=False)

    # Return the configuration file path
    return config_filename


@bash_app(executors=["parallel"])
def _execute_make_obs3d(
    env, rundir, install_path, config_file, tag="develop", stdout=None, stderr=None
):
    # Run the hofx executable
    return env + textwrap.dedent(
        f"""
    echo Started at $(date)
    echo Executing on $(hostname)
    {install_path}/jedi-bundle/{tag}/build/bin/qg_hofx.x {config_file}
    echo Completed at $(date)
    """
    )


@join_app
def makeobs3d(
    env, install_path, tag, rundir, config, stdout=None, stderr=None, truth=None
):

    configure = _configure_make_obs3d(rundir, config=config, truth=truth)

    execute = _execute_make_obs3d(
        env,
        rundir,
        install_path,
        config_file=configure,
        tag=tag,
        stdout=stdout,
        stderr=stderr,
    )

    return execute
