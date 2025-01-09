import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Dict

import yaml
from globus_compute_sdk import Client
from globus_compute_sdk.sdk.auth.globus_app import get_globus_app
from globus_sdk import ClientApp, GlobusApp, TransferClient, UserApp
from globus_sdk.gare import GlobusAuthorizationParameters

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
  type: {{ engine|default("GlobusComputeEngine") }}
  {% if engine == '"GlobusMPIEngine"' %}
  max_workers_per_block: {{ max_mpi_apps|default(1) }}
  mpi_launcher: srun
  {% endif %}
  run_in_sandbox: True

  provider:
    type: SlurmProvider
    launcher:
      type: SimpleLauncher
    exclusive: {{ exclusive|default("True") }}
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

# Set the UUID of the default Chiltepin thick client
CHILTEPIN_CLIENT_UUID = "42e9e804-0bcd-4c3d-881b-8e270e3c2163"


def get_chiltepin_apps() -> (GlobusApp, GlobusApp):
    """Log in to the Chiltepin app

    This instantiates GlobusApp objects for use in creating Globus Compute
    and Globus Transfer clients.  If the environment contains settings that
    specify client ids and/or client secrets, those will be used to create the
    Globus Apps.  Otherwise, the default Chiltepin thick client will be used.
    If a secret is present in the environment, ClientApp objects will be created.
    Otherwise, UserApp objects will be created. This is used by the login() and
    logout() functions where login and logout flows are initiated after the apps
    are retreived. A tuple is returned where the first item is the compute app
    and the second item is the transfer app.

    Returns
    -------

    (GlobusApp, GlobusApp)
    """
    # Get client id and secret from environment if they are set
    client_id = os.environ.get("GLOBUS_COMPUTE_CLIENT_ID", None)
    client_secret = os.environ.get("GLOBUS_COMPUTE_CLIENT_SECRET", None)

    # If a client secret was found, make sure a client id was also found
    if client_secret and not client_id:
        raise Exception(
            "$GLOBUS_COMPUTE_CLIENT_SECRET is set but $GLOBUS_COMPUTE_CLIENT_ID is not"
        )

    # If a secret and id were both found, set the corresponding Globus CLI env vars
    if client_secret:
        os.environ["GLOBUS_CLI_CLIENT_ID"] = client_id
        os.environ["GLOBUS_CLI_CLIENT_SECRET"] = client_secret

    # If a client id was not found in the environment, use the default Chiltepin client id
    if not client_id:
        client_id = CHILTEPIN_CLIENT_UUID
        os.environ["GLOBUS_COMPUTE_CLIENT_ID"] = client_id
        # NOTE: $GLOBUS_CLI_CLIENT_ID should only be set if $GLOBUS_CLI_CLIENT_SECRET is also set

    # Get the Globus App the compute client will use
    compute_app = get_globus_app()

    # Create a Globus App for the transfer client
    if client_secret:
        # Use a ClientApp for Service Client credentials
        transfer_app = ClientApp(
            "chiltepin",
            client_id=client_id,
            client_secret=client_secret,
        )
    else:
        # Use a UserApp for user credentials
        transfer_app = UserApp(
            "chiltepin",
            client_id=client_id,
        )

    # Return the Apps
    return (compute_app, transfer_app)


def login() -> Dict[str, Client | TransferClient]:
    """Log in to the Chiltepin app

    This initiates the Globus login flow to log the user in to the Globus compute
    and transfer services. The login will use the registered Chiltepin thick client
    by default, or the client id and/or secret specified in the environment. This
    returns a Globus Compute client and a Globus Transfer client in a dictionary.
    Those clients can then be used for accessing those services.

    Returns
    -------

    Dict[str, Client | TransferClient]
    """
    # Get the Globus Apps for use in creating the clients
    compute_app, transfer_app = get_chiltepin_apps()

    # Initialize the compute client
    compute_client = Client(app=compute_app)

    # Initialize the transfer client
    transfer_client = TransferClient(app=transfer_app)

    # transfer_client.add_app_data_access_scope("d75f3e86-df3c-4734-8b9d-f182346b4bbd")

    # Initiate login for compute client if necessary
    if compute_app.login_required():
        compute_app.login()

    # Initiate login for transfer client if necessary
    if transfer_app.login_required():
        transfer_app.login(
            auth_params=GlobusAuthorizationParameters(
                session_required_single_domain=["rdhpcs.noaa.gov"],
                prompt="login",
            )
        )

    return {"compute": compute_client, "transfer": transfer_client}


def logout():
    """Log out of the Chiltepin app

    This logs the user out of the Globus compute and transfer services and revokes
    all credentials associated with them.
    """
    # Get the Globus Apps for use in creating the clients
    compute_app, transfer_app = get_chiltepin_apps()
    compute_app.logout()
    transfer_app.logout()


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
            f.write(f"PATH: {chiltepin_path}:{login_path}\n")


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


def is_running(name: str, config_dir: str | None = None) -> bool:
    """Return True if the endpoint is running, otherwise False

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
    # Get a list of endpoints
    ep_list = list(config_dir)

    # Get the endpoint info
    ep_info = ep_list.get(name, {})

    # Return whether endpoint state is "Running"
    return ep_info.get("state", None) == "Running"


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
        # Wait for endpoint to enter "Running" state
        while not is_running(name, config_dir):
            time.sleep(1)

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
    if is_multi(name, config_dir):
        # Wait for endpoint to enter "Stopped" state
        while is_running(name, config_dir):
            time.sleep(1)
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
    command.append("--force")
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
