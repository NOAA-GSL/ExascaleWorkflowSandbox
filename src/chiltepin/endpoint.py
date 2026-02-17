import os
import pathlib
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, Optional, Union

import psutil
import yaml
from globus_compute_endpoint.endpoint.config.utils import get_config
from globus_compute_endpoint.endpoint.endpoint import Endpoint
from globus_compute_sdk.sdk.auth.auth_client import ComputeAuthClient
from globus_compute_sdk.sdk.auth.globus_app import get_globus_app
from globus_compute_sdk.sdk.web_client import WebClient
from globus_sdk import ClientApp, ComputeClientV2, GlobusApp, TransferClient, UserApp
from globus_sdk.gare import GlobusAuthorizationParameters

endpoint_template = """# This is the default user-endpoint-process (UEP) template provided with
# newly-configured endpoints.  Endpoints generate a UEP-specific configuration
# by processing this YAML file as a Jinja template against SDK-provided (user)
# variables -- please modify this template to suit your site's requirements.
#
# As an optional security and user-debugging aid, consider also specifying a
# JSON schema for the user-provided variables.  If `user_config_schema.json`
# exists within the same directory, then before starting the UEP, the MEP will
# validate the variables against the schema before rendering.  This provides
# an administrative peace of mind that users cannot specify invalid arguments.
# From a usability standpoint, however, it also can make invalid values
# prominently visible to users.
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


def login() -> Dict[str, Union[ComputeClientV2, TransferClient]]:
    """Log in to the Chiltepin app

    This initiates the Globus login flow to log the user in to the Globus compute
    and transfer services. The login will use the registered Chiltepin thick client
    by default, or the client id and/or secret specified in the environment. This
    returns a Globus Compute client and a Globus Transfer client in a dictionary.
    Those clients can then be used for accessing those services.

    Returns
    -------

    Dict[str, ComputeClientV2 | TransferClient]
    """
    # Get the Globus Apps for use in creating the clients
    compute_app, transfer_app = get_chiltepin_apps()

    # Initialize the compute client
    compute_client = ComputeClientV2(app=compute_app)

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
    """
    if platform.system() == "Windows":
        raise NotImplementedError(
            "Globus Compute endpoints are not supported on Windows"
        )

    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("configure")
    command.append(name)

    p = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    stdout, _ = p.communicate(timeout=5.0)
    assert p.returncode == 0, stdout

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

    # Enable debugging for the endpoint to help with troubleshooting
    yaml_config["debug"] = True

    # Update the configuration with the new settings
    with open(config_path / "config.yaml", "w") as f:
        try:
            yaml.dump(yaml_config, f)
        except yaml.YAMLError as e:
            print(f"Error writing endpoint config file: {e}")
            return False

    # Setup the user config jinja template
    with open(config_path / "user_config_template.yaml.j2", "w") as f:
        f.write(endpoint_template)

    # Capture the required system PATH for the endpoint environment.
    # Set $HOME to an empty temporary directory to avoid capturing user-specific settings
    # that could cause issues in the endpoint environment.  Use a temporary directory for
    # $HOME to avoid security issues with /tmp. Providing an empty $HOME is the only way
    # to reliably capture a clean PATH that doesn't include user-specific directories.
    # NOTE: This may fail on systems with badly written system init scripts that attempt
    # to source user-specific files without checking for their existence first, but this
    # scenario is very unlikely and we will accept that risk until we have a better solution.
    temp_home = tempfile.mkdtemp(prefix="chiltepin_home_")
    try:
        p = subprocess.Popen(
            ["env", "-i", f"HOME={temp_home}", "bash", "-l", "-c", "echo $PATH"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout, stderr = p.communicate(timeout=3.0)
        assert p.returncode == 0, stderr
        login_path = stdout.strip()
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_home, ignore_errors=True)
    chiltepin_path = pathlib.Path(sys.executable).parent.resolve()

    # Set the custom user environment path configuration for the endpoint
    with open(config_path / "user_environment.yaml", "a") as f:
        f.write(f"PATH: {chiltepin_path}:{login_path}\n")

    # Return success
    return True


def show(
    config_dir: Optional[str] = None,
) -> Dict[str, Dict[str, str]]:
    """Return a dictionary of configured Globus Compute Endpoints

    This returns endpoint information in a dict with keys corresponding to
    the endpoint names.

    Parameters
    ----------

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is stored. If None (the default), then $HOME/.globus_compute is used

    Returns
    -------

    Dict[str, Dict[str, str]]
    """

    config_dir_path = (
        Path(config_dir) if config_dir else Path.home() / ".globus_compute"
    )
    endpoint_info = Endpoint.get_endpoints(config_dir_path)

    return endpoint_info


def exists(
    name: str,
    config_dir: Optional[str] = None,
) -> bool:
    """Return True if the endpoint exists, otherwise False

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
    # Get the endpoint info
    endpoints = show(config_dir)

    # Return whether the endpoint exists in the listing
    return name in endpoints


def is_running(
    name: str,
    config_dir: Optional[str] = None,
) -> bool:
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
    # Get the endpoint info
    endpoints = show(config_dir)

    # Extract the endpoint record
    endpoint = endpoints.get(name, {})

    # Return whether the endpoint state is "Running"
    return endpoint.get("status", None) == "Running"


def start(
    name: str,
    config_dir: Optional[str] = None,
    timeout: Optional[float] = None,
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

    timeout: float | None
        Number of seconds to wait for the command to complete before timing out
        Default is None, meaning the command will never time out.
    """
    if platform.system() == "Windows":
        raise NotImplementedError(
            "Globus Compute endpoints are not supported on Windows"
        )

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

    # Create a temporary file to capture initial stderr for failure detection
    temp_stderr = tempfile.NamedTemporaryFile(
        mode="w+", prefix=f"chiltepin_start_{name}_", suffix=".err", delete=False
    )
    temp_stderr_path = temp_stderr.name
    temp_stderr.close()

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
            # Redirect stdin and stdout to /dev/null, but stderr to temp file
            # so we can capture immediate failures
            devnull = os.open(os.devnull, os.O_RDWR)
            os.dup2(devnull, 0)  # Redirect stdin to /dev/null
            os.dup2(devnull, 1)  # Redirect stdout to /dev/null
            # Redirect stderr to temp file for failure detection
            stderr_fd = os.open(
                temp_stderr_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND
            )
            os.dup2(stderr_fd, 2)
            if devnull > 2:
                os.close(devnull)
            if stderr_fd > 2:
                os.close(stderr_fd)
            # Execute the endpoint command
            os.execvp(command[0], command)
        else:
            # First child exits immediately
            os._exit(0)
    else:
        # Parent waits for first child to exit
        os.waitpid(pid, 0)

    # Wait for endpoint to enter "Running" state
    start_time = time.time()
    try:
        while True:
            # Calculate remaining timeout for this iteration
            if timeout is not None:
                elapsed = time.time() - start_time
                if elapsed > timeout:
                    # Check for error output before timing out
                    error_msg = _read_startup_errors(temp_stderr_path)
                    timeout_msg = f"Timeout of {timeout}s exceeded while waiting for endpoint '{name}' to start"
                    if error_msg:
                        raise TimeoutError(
                            f"{timeout_msg}\n\nStartup errors:\n{error_msg}"
                        )
                    raise TimeoutError(timeout_msg)

            # Check if endpoint is running, passing remaining timeout to prevent hanging
            if is_running(name, config_dir):
                break

            # Check for errors immediately - if the endpoint failed, report it
            error_msg = _read_startup_errors(temp_stderr_path)
            if error_msg:
                raise RuntimeError(
                    f"Endpoint '{name}' failed to start. Error output:\n{error_msg}"
                )

            time.sleep(1)
    finally:
        # Clean up temporary error file
        try:
            os.unlink(temp_stderr_path)
        except OSError:
            pass


def _read_startup_errors(stderr_path: str, max_size: int = 10240) -> str:
    """Read initial error output from endpoint startup.

    Parameters
    ----------
    stderr_path : str
        Path to the temporary stderr file
    max_size : int
        Maximum number of bytes to read from the file

    Returns
    -------
    str
        Error content if any, empty string otherwise
    """
    try:
        if os.path.exists(stderr_path) and os.path.getsize(stderr_path) > 0:
            with open(stderr_path, "r") as f:
                content = f.read(max_size)
                return content.strip()
    except (OSError, IOError):
        pass
    return ""


def stop(
    name: str,
    config_dir: Optional[str] = None,
    timeout: Optional[float] = None,
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

    timeout: float | None
        Number of seconds to wait for the command to complete before timing out
        Default is None, meaning the command will never time out.
    """
    if platform.system() == "Windows":
        raise NotImplementedError(
            "Globus Compute endpoints are not supported on Windows"
        )

    # Make sure we are logged in
    if login_required():
        raise RuntimeError("Chiltepin login is required")

    # Get the path to the globus compute endpoint configuration
    config_path = (
        Path(config_dir) / name
        if config_dir
        else Path.home() / ".globus_compute" / name
    )

    # Track elapsed time to enforce timeout across both subprocess and wait loop
    start_time = time.time()

    try:
        Endpoint.stop_endpoint(config_path, get_config(config_path), remote=False)
    except psutil.TimeoutExpired:
        # Try one more time if we get a psutil timeout, since that can happen if the endpoint
        # enters a bad state and fails to stop within the expected time.
        Endpoint.stop_endpoint(config_path, get_config(config_path), remote=False)

    # Wait for endpoint to enter "Stopped" state
    while True:
        # Calculate remaining timeout for this iteration
        if timeout is not None:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Timeout of {timeout}s exceeded while waiting for endpoint '{name}' to stop"
                )

        # Check if endpoint is still running, passing remaining timeout to prevent hanging
        if not is_running(name, config_dir):
            break

        time.sleep(1)


def delete(
    name: str,
    config_dir: Optional[str] = None,
    timeout: Optional[float] = None,
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

    timeout: float | None
        Number of seconds to wait for the command to complete before timing out
        Default is None, meaning the command will never time out.
    """
    if platform.system() == "Windows":
        raise NotImplementedError(
            "Globus Compute endpoints are not supported on Windows"
        )

    # Make sure we are logged in
    if login_required():
        raise RuntimeError("Chiltepin login is required")

    # Get the path to the globus compute endpoint configuration
    config_path = (
        Path(config_dir) / name
        if config_dir
        else Path.home() / ".globus_compute" / name
    )

    # Track elapsed time to enforce timeout
    start_time = time.time()

    # Get the endpoint config
    try:
        ep_config = None
        force = False
        ep_config = get_config(config_path)
    except Exception:
        force = True

    # Delete the endpoint
    try:
        Endpoint.delete_endpoint(config_path, ep_config, force=force, ep_uuid=None)
    except Exception as e:
        raise RuntimeError(f"Error deleting endpoint: {e}")

    # Wait for endpoint to disappear from the listing
    while True:
        # Calculate remaining timeout for this iteration
        if timeout is not None:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(
                    f"Timeout of {timeout}s exceeded while waiting for endpoint '{name}' to be deleted"
                )

        # Check if endpoint still exists
        if not exists(name, config_dir):
            break

        time.sleep(1)
