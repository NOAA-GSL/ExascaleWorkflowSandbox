import os
import pathlib
import re
import subprocess
import sys
import time
from typing import Dict, Optional, Union

import yaml
from globus_compute_sdk import Client
from globus_compute_sdk.sdk.auth.auth_client import ComputeAuthClient
from globus_compute_sdk.sdk.auth.globus_app import get_globus_app
from globus_compute_sdk.sdk.web_client import WebClient
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
  {% if mpi %}
  type: GlobusMPIEngine
  max_workers_per_block: {{ max_mpi_apps|default(1) }}
  {% if provider == '"slurm"' %}
  {% set default_mpi_launcher = "srun" %}
  {% else %}
  {% set default_mpi_launcher = "mpiexec" %}
  {% endif %}
  mpi_launcher: {{ mpi_launcher|default(default_mpi_launcher) }}
  {% else %}
  type: GlobusComputeEngine
  {% endif %}
  run_in_sandbox: True

  provider:
    {% if provider == '"slurm"' %}
    type: SlurmProvider
    {% elif provider == '"pbspro"' %}
    type: PBSProProvider
    {% else %}
    type: LocalProvider
    {% endif %}
    launcher:
      {% if mpi %}
      type: SimpleLauncher
      {% else %}
      {% if provider == '"slurm"' %}
      type: SrunLauncher
      {% elif provider == '"pbspro"' %}
      type: MpiExecLauncher
      {% else %}
      type: SingleNodeLauncher
      {% endif %}
      {% endif %}

    init_blocks: {{ init_blocks|default(0) }}
    min_blocks: {{ min_blocks|default(0) }}
    max_blocks: {{ max_blocks|default(1) }}
    worker_init: {{ worker_init|default() }}

    {% if provider != '"localhost"' %}
    {% if not mpi %}
    {% if provider == '"slurm"' %}
    cores_per_node: {{ cores_per_node|default(1) }}
    {% elif provider == '"pbspro"' %}
    cpus_per_node: {{ cores_per_node|default(1) }}
    {% endif %}
    {% endif %}
    nodes_per_block: {{ nodes_per_block|default(1) }}
    {% if provider == '"slurm"' %}
    exclusive: {{ exclusive|default("True") }}
    partition: {{ partition|default() }}
    qos: {{ queue|default() }}
    {% elif provider == '"pbspro"' %}
    queue: {{ queue|default() }}
    {% endif %}
    account: {{ account|default() }}
    walltime: {{ walltime|default("00:10:00") }}
    {% endif %}

# Endpoints will be restarted when a user submits new tasks to the
# web-services, so eagerly shut down if endpoint is idle.  At 30s/hb (default
# value), 10 heartbeats is 300s.
idle_heartbeats_soft: 120

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
    compute_app.add_scope_requirements(
        {
            WebClient.scopes.resource_server: WebClient.default_scope_requirements,
            ComputeAuthClient.scopes.resource_server: ComputeAuthClient.default_scope_requirements,  # noqa E501
        }
    )

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


def login() -> Dict[str, Union[Client, TransferClient]]:
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

    # Return the clients
    return {"compute": compute_client, "transfer": transfer_client}


def login_required() -> bool:
    """Check whether a chiltepin login is required to use the requested Globus
    scopes needed by the Chiltepin transfer and computer Apps.

    Returns
    -------

    bool
    """
    # Get the Globus Apps for use in creating the clients
    compute_app, transfer_app = get_chiltepin_apps()

    return compute_app.login_required() or transfer_app.login_required()


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
    config_dir: Optional[str] = None,
    timeout: Optional[int] = None,
) -> bool:
    """Configure a Globus Compute Endpoint

    This is a thin wrapper around the globus-compute-endpoint configure command.
    Additional configuration steps, usually done manually by the user after
    configuration, are taken to hide complexity from the user.

    Parameters
    ----------

    name: str
        Name of the endpoint to configure

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is to be stored. If None (the default), then $HOME/.globus_compute
        is used

    timeout: int | None
        Number of seconds to wait for the command to complete before timing out.
        Default is None, meaning the command will never time out.
    """
    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("configure")
    command.append(name)

    p = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        start_new_session=True,
    )
    assert p.returncode == 0, p.stdout

    # Get the path to the globus compute endpoint configuration
    if config_dir:
        config_path = pathlib.Path(f"{os.path.abspath(config_dir)}/{name}")
    else:
        config_path = pathlib.Path(f"{pathlib.Path.home()}/.globus_compute/{name}")

    # Read the default endpoint configuration that was just created
    with open(config_path / "config.yaml", "r") as f:
        try:
            yaml_config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            print(f"Error reading endpoint config file: {e}")
            return False

    # Set the display name
    yaml_config["display_name"] = name

    # Update the configuration with the new settings
    with open(config_path / "config.yaml", "w") as f:
        try:
            yaml.dump(yaml_config, f)
        except yaml.YAMLError as e:
            print(f"Error writing endpoint config file: {e}")
            return False

    # Setup the user config jinja template
    with open(config_path / "user_config_template.yaml.j2", "w") as f:
        f.write(multi_endpoint_template)

    # Capture the required system PATH for the endpoint environment.
    # Do not capture custom user settings set in shell init scripts (e.g., .bashrc)
    # since those may not be applicable to the endpoint environment and could cause issues.
    p = subprocess.run(
        ["env", "-i", "HOME=foobar", "bash", "-l", "-c", "echo $PATH"],
        capture_output=True,
        text=True,
        start_new_session=True,
    )
    assert p.returncode == 0, p.stderr
    login_path = p.stdout.strip()
    chiltepin_path = pathlib.Path(sys.argv[0]).parent.resolve()

    # Set the custom user environment path configuration for the endpoint
    with open(config_path / "user_environment.yaml", "a") as f:
        f.write(f"PATH: {chiltepin_path}:{login_path}\n")

    # Return success
    return True


def show(
    config_dir: Optional[str] = None,
    timeout: Optional[int] = None,
) -> Dict[str, Dict[str, str]]:
    """Return a list of configured Globus Compute Endpoints

    This is a thin wrapper around the globus-compute-endpoint list command.
    The endpoint listing is returned as a dict with keys corresponding to
    the endpoint names.

    Parameters
    ----------

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    timeout: int | None
        Number of seconds to wait for the command to complete before timing out
        Default is None, meaning the command will never time out.

    Returns
    -------

    Dict[str, Dict[str, str]]
    """
    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("list")

    p = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        start_new_session=True,
    )
    assert p.returncode == 0, p.stdout

    # Build a dictionary from the output and return it
    endpoint_info = {}
    endpoint_regex = re.compile(
        r"\|\s+([0-9a-f\-]{36}|None)\s+\|\s+([^\|\s]+)\s+\|\s+([^\|\s]+)\s+\|"
    )
    for line in p.stdout.split("\n"):
        match = endpoint_regex.search(line)
        if match is not None:
            assert match.group(1) == "None" or len(match.group(1)) == 36
            endpoint_info[match.group(3)] = {
                "id": match.group(1),
                "state": match.group(2),
            }
    return endpoint_info


def exists(
    name: str,
    config_dir: Optional[str] = None,
    timeout: Optional[int] = None,
) -> bool:
    """Return True if the endpoint exists, otherwise False

    Parameters
    ----------

    name: str
        Name of the endpoint to check

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    timeout: int | None
        Number of seconds to wait for the command to complete before timing out.
        Default is None, meaning the command will never time out.

    Returns
    -------

    bool
    """
    # Get the endpoint info
    endpoints = show(config_dir, timeout)

    # Return whether the endpoint exists in the listing
    return name in endpoints


def is_running(
    name: str,
    config_dir: Optional[str] = None,
    timeout: Optional[int] = None,
) -> bool:
    """Return True if the endpoint is running, otherwise False

    Parameters
    ----------

    name: str
        Name of the endpoint to check

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    timeout: int | None
        Number of seconds to wait for the command to complete before timing out.
        Default is None, meaning the command will never time out.

    Returns
    -------

    bool
    """
    # Get the endpoint info
    endpoints = show(config_dir, timeout)

    # Extract the endpoint record
    endpoint = endpoints.get(name, {})

    # Return whether the endpoint state is "Running"
    return endpoint.get("state", None) == "Running"


def start(
    name: str,
    config_dir: Optional[str] = None,
    timeout: Optional[int] = None,
):
    """Start the specified Globus Compute Endpoint

    This is a thin wrapper around the globus-compute-endpoint start command

    Parameters
    ----------

    name: str
        Name of the endpoint to start

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    timeout: int | None
        Number of seconds to wait for the command to complete before timing out
        Default is None, meaning the command will never time out.
    """
    # Make sure we are logged in
    if login_required():
        raise RuntimeError("Chiltepin login is required")

    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("start")
    command.append(name)

    # Run the command as a detached daemon process using double-fork
    # to completely disconnect from the parent process tree.
    # NOTE: subprocess.Popen with start_new_session=True does not work to
    # fully detach the process because globus-compute-endpoint uses psutil
    # to manage subprocesses, and psutil requires the parent process to still
    # be alive to avoid orphaning the child processes it creates. The double-fork
    # method is used here to create a new session and then immediately exit
    # the first child, leaving the grandchild process running as a daemon that
    # is not a child of the original parent process.
    pid = os.fork()
    if pid == 0:
        # First child - create new session
        os.setsid()
        # Fork again
        pid2 = os.fork()
        if pid2 == 0:
            # Second child (grandchild) - this becomes the daemon
            # Redirect all output to /dev/null
            devnull = os.open(os.devnull, os.O_RDWR)
            os.dup2(devnull, 0)  # Redirect stdin to /dev/null
            os.dup2(devnull, 1)  # Redirect stdout to /dev/null
            os.dup2(devnull, 2)  # Redirect stderr to /dev/null
            if devnull > 2:
                os.close(devnull)
            # Execute the endpoint command
            os.execvp(command[0], command)
        else:
            # First child exits immediately
            os._exit(0)
    else:
        # Parent waits for first child to exit
        os.waitpid(pid, 0)

    # Wait for endpoint to enter "Running" state
    while not is_running(name, config_dir):
        time.sleep(1)


def stop(
    name: str,
    config_dir: Optional[str] = None,
    timeout: Optional[int] = None,
):
    """Stop the specified Globus Compute Endpoint

    This is a thin wrapper around the globus-compute-endpoint stop command

    Parameters
    ----------

    name: str
        Name of the endpoint to stop

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    timeout: int | None
        Number of seconds to wait for the command to complete before timing out
        Default is None, meaning the command will never time out.
    """
    # Make sure we are logged in
    if login_required():
        raise RuntimeError("Chiltepin login is required")

    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("stop")
    command.append(name)

    p = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        start_new_session=True,
    )

    # Check for success unless running under pytest
    # NOTE: pytest interferes with psutil and causes ChildProcessError to be raised even when
    # the command succeeds, so we skip the check when running under pytest. Either way, we still
    # verify that the endpoint eventually enters the "Stopped" state in the following loop,
    # which will raise an error if the command did not succeed in stopping the endpoint.
    if "PYTEST_CURRENT_TEST" not in os.environ:
        assert p.returncode == 0, p.stdout

    # Wait for endpoint to enter "Stopped" state
    start_time = time.time()
    while is_running(name, config_dir, timeout):
        if timeout is not None and (time.time() - start_time) > timeout:
            raise TimeoutError(
                f"Timeout of {timeout}s exceeded while waiting for endpoint '{name}' to stop"
            )
        time.sleep(1)


def delete(
    name: str,
    config_dir: Optional[str] = None,
    timeout: Optional[int] = None,
):
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
        Default is None, meaning the command will never time out.
    """
    # Make sure we are logged in
    if login_required():
        raise RuntimeError("Chiltepin login is required")

    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("delete")
    command.append("--yes")
    command.append("--force")
    command.append(name)

    p = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        start_new_session=True,
    )

    # Check for success unless running under pytest
    # NOTE: pytest interferes with psutil and causes ChildProcessError to be raised even when
    # the command succeeds, so we skip the check when running under pytest. Either way, we still
    # verify that the endpoint eventually gets deleted in the following loop,
    # which will raise an error if the command did not succeed in deleting the endpoint.
    if "PYTEST_CURRENT_TEST" not in os.environ:
        assert p.returncode == 0, p.stdout

    # Wait for endpoint to disappear from the listing
    start_time = time.time()
    while exists(name, config_dir, timeout):
        if timeout is not None and (time.time() - start_time) > timeout:
            raise TimeoutError(
                f"Timeout of {timeout}s exceeded while waiting for endpoint '{name}' to be deleted"
            )
        time.sleep(1)
