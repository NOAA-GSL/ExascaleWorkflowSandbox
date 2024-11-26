import os
import re
import subprocess
from typing import Dict


def configure(name: str, config_dir: str | None = None, timeout: int = 5):
    """Configure a Globus Compute Endpoint

    This is a thin wrapper around the globus-compute-endpoint configure command

    Parameters
    ----------

    name: str
        Name of the endpoint to configure

    config_dir: str | None
        Path to endpoint configuration directory where endpoint information
        is to be stored. If None (the default), then $HOME/.globus_compute
        is used

    timeout: int
        Number of seconds to wait for the command to complete before timing out
    """
    # Build the globus-compute-endpoint command to run
    command = ["globus-compute-endpoint"]
    if config_dir:
        command.append("-c")
        command.append(f"{os.path.abspath(config_dir)}")
    command.append("configure")
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
    # Run the command as a subprocess
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
