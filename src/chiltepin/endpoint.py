import os
import pathlib
import re
import subprocess
import sys
from typing import Dict

import yaml

multi_endpoint_template = """# This is the default user-template provided with newly-configured Multi-User
# endpoints.  User endpoints generate a user-endpoint-specific configuration by
# processing this YAML file as a Jinja template against user-provided
# variables -- please modify this template to suit your site's requirements.
#
# Optionally, you can define a JSON schema for the user-provided variables in a
# file named `user_config_schema.json` within the same directory. The variables
# will be validated against the schema before rendering this template.
#
# For more information, please see the `user_endpoint_config` in Globus Compute
# SDK's Executor.
#
# Some common options site-administrators may want to set:
#  - address
#  - provider (e.g., SlurmProvider, TorqueProvider, CobaltProvider, etc.)
#  - account
#  - scheduler_options
#  - walltime
#  - worker_init
#
# There are a number of example configurations available in the documentation:
#    https://globus-compute.readthedocs.io/en/stable/endpoints.html#example-configurations

debug: True

endpoint_setup: {{ endpoint_setup|default() }}

engine:
  type: {{ engine_type|default("GlobusComputeEngine") }}
  {% if engine_type == '"GlobusMPIEngine"' %}
  max_workers_per_block: {{ max_mpi_apps|default(1) }}
  mpi_launcher: srun
  {% endif %}
  run_in_sandbox: True

  provider:
    type: SlurmProvider
    launcher:
      type: SimpleLauncher
    cores_per_node: {{ cores_per_node|default(1) }}
    nodes_per_block: {{ nodes_per_block|default(1) }}
    min_blocks: {{ min_blocks|default(1) }}
    max_blocks: {{ max_blocks|default(1) }}
    init_blocks: {{ init_blocks|default(0) }}
    partition: {{ partition|default() }}
    account: {{ account|default() }}
    walltime: {{ walltime|default("00:10:00") }}
    worker_init: {{ worker_init|default() }}

# Endpoints will be restarted when a user submits new tasks to the
# web-services, so eagerly shut down if endpoint is idle.  At 30s/hb (default
# value), 10 heartbeats is 300s.
idle_heartbeats_soft: 10

# If endpoint is *apparently* idle (e.g., outstanding tasks, but no movement)
# for this many heartbeats, then shutdown anyway.  At 30s/hb (default value),
# 5,760 heartbeats == "48 hours".  (Note that this value will be ignored if
# idle_heartbeats_soft is 0 or not set.)
idle_heartbeats_hard: 5760
"""


def configure(
    name: str,
    config_dir: str | None = None,
    multi: bool = False,
    timeout: int = 5,
):
    """Configure a Globus Compute Endpoint

    This is a thin wrapper around the globus-compute-endpoint configure command. If the
    endpoint is configured in multi mode, additional configuration steps are taken to
    customize it for use in Chiltepin workflows.

    Parameters
    ----------

    name: str
        Name of the endpoint to configure

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is to be stored. If None (the default), then $HOME/.globus_compute
        is used

    multi: bool
        Configure a multi templatable endpoint instead of the default user endpoint

    timeout: int
        Number of seconds to wait for the command to complete before timing out
    """
    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("configure")
    if multi:
        command.append("--multi-user")
    command.append(name)
    # Run the command as a sub process
    p = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    assert p.returncode == 0, p.stdout

    # Additional configuration is needed for multi endpoints
    if multi:
        # Get the path to the globus compute endpoint configuration
        if config_dir:
            config_path = pathlib.Path(f"{os.path.abspath(config_dir)}/{name}")
        else:
            config_path = pathlib.Path(f"{pathlib.Path.home()}/.globus_compute/{name}")

        # Remove example user mapping file
        pathlib.Path.unlink(config_path / "example_identity_mapping_config.json")

        # Update the config.yaml file
        with open(config_path / "config.yaml", "r") as f:
            config_str = f.read()
            config_str = re.sub(
                "identity_mapping_config_path:.*\n",
                "",
                config_str,
            )
            config_str = re.sub(
                "display_name: null",
                f"display_name: {name}",
                config_str,
            )
        with open(config_path / "config.yaml", "w") as f:
            f.write(config_str)

        # setup the user config jinja template
        with open(config_path / "user_config_template.yaml.j2", "w") as f:
            f.write(multi_endpoint_template)

        # setup the user environment PATH
        p = subprocess.run(
            ["env", "-i", "HOME=$HOME", "bash", "-l", "-c", "echo $PATH"],
            capture_output=True,
            text=True,
        )
        assert p.returncode == 0, p.stderr
        login_path = p.stdout.strip()
        chiltepin_path = pathlib.Path(sys.argv[0]).parent.resolve()
        with open(config_path / "user_environment.yaml", "a") as f:
            f.write(f"PATH={chiltepin_path}:{login_path}\n")


def is_multi(name: str, config_dir: str | None = None) -> bool:
    """Return True if the endpoint is a multi endpoint, False otherwise

    Parameters
    ----------

    name: str
        Name of the endpoint to check

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    Returns
    -------

    bool
    """
    # Get the path to the globus compute endpoint configuration
    if config_dir:
        config_path = pathlib.Path(f"{os.path.abspath(config_dir)}/{name}")
    else:
        config_path = pathlib.Path(f"{pathlib.Path.home()}/.globus_compute/{name}")
    # Parse the configuration
    with open(config_path / "config.yaml", "r") as stream:
        try:
            yaml_config = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print("Invalid yaml configuration")
            raise (e)
    # Look for multi_user
    return yaml_config.get("multi_user", False)


def list(config_dir: str | None = None, timeout: int = 60) -> Dict[str, str]:
    """Return a list of configured Globus Compute Endpoints

    This is a thin wrapper around the globus-compute-endpoint list command.
    The endpoint listing is returned as a dict with keys corresponding to
    the endpoint names.

    Parameters
    ----------

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    timeout: int
        Number of seconds to wait for the command to complete before timing out

    Returns
    -------

    Dict[str, str]
    """
    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("list")
    # Run the command as a subprocess
    p = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    assert p.returncode == 0, p.stdout
    # Build a dict from the output and return it
    ep_list = {}
    for line in p.stdout.split("\n"):
        endpoint_regex = re.compile(
            r"\|\s+([0-9a-f\-]{36}|None)\s+\|\s+([^\|\s]+)\s+\|\s+([^\|\s]+)\s+\|"
        )
        match = endpoint_regex.search(line)
        if match is not None:
            assert match.group(1) == "None" or len(match.group(1)) == 36
            ep_list[match.group(3)] = {"id": match.group(1), "state": match.group(2)}
    return ep_list


def start(name: str, config_dir: str | None = None, timeout: int = 60):
    """Start the specified Globus Compute Endpoint

    This is a thin wrapper around the globus-compute-endpoint start command

    Parameters
    ----------

    name: str
        Name of the endpoint to start

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    timeout: int
        Number of seconds to wait for the command to complete before timing out
    """
    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("start")
    command.append(name)

    if is_multi(name, config_dir):
        # Run the command as a detatched daemon process
        p = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        assert p.pid > 0
        # Get the path to the globus compute endpoint configuration
        if config_dir:
            config_path = pathlib.Path(f"{os.path.abspath(config_dir)}/{name}")
        else:
            config_path = pathlib.Path(f"{pathlib.Path.home()}/.globus_compute/{name}")
        # Write the pid to the endpoint pid file
        with open(config_path / "daemon.pid", "w") as f:
            f.write(f"{p.pid}\n")
    else:
        # Run the command as a normal subprocess
        p = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        assert p.returncode == 0, p.stdout


def stop(name: str, config_dir: str | None = None, timeout: int = 60):
    """Stop the specified Globus Compute Endpoint

    This is a thin wrapper around the globus-compute-endpoint stop command

    Parameters
    ----------

    name: str
        Name of the endpoint to stop

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    timeout: int
        Number of seconds to wait for the command to complete before timing out
    """
    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("stop")
    command.append(name)
    # Run the command as a subprocess
    p = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    assert p.returncode == 0, p.stdout


def delete(name: str, config_dir: str | None = None, timeout: int = 60):
    """Delete the specified Globus Compute Endpoint

    This is a thin wrapper around the globus-compute-endpoint delete command

    Parameters
    ----------

    name: str
        Name of the endpoint to delete

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    timeout: int
        Number of seconds to wait for the command to complete before timing out
    """
    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("delete")
    command.append("--yes")
    command.append(name)
    # Run the command as a subprocess
    p = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
    )
    assert p.returncode == 0, p.stdout
