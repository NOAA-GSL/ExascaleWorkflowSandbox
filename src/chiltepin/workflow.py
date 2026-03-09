# SPDX-License-Identifier: Apache-2.0

"""Workflow context managers for Chiltepin.

This module provides context managers that wrap Parsl configuration and lifecycle
management, eliminating the need for users to directly import or interact with Parsl.
"""

import logging
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import parsl
from globus_compute_sdk import Client

from chiltepin import configure

# Module-level logger for cleanup warnings
_logger = logging.getLogger(__name__)


@contextmanager
def run_workflow(
    config: Union[str, Path, Dict[str, Any]],
    *,
    include: Optional[List[str]] = None,
    run_dir: Optional[str] = None,
    client: Optional[Client] = None,
    log_file: Optional[str] = None,
    log_level: Optional[int] = None,
):
    """Context manager for Chiltepin workflows.

    This wraps Parsl configuration and lifecycle management, eliminating the need
    for users to directly import or interact with Parsl.

    Parameters
    ----------
    config : str, Path, or dict
        Either a path to a YAML configuration file or a configuration dictionary
    include : list of str, optional
        List of resource labels to load. If None, all resources are loaded.
    run_dir : str, optional
        Directory for Parsl runtime files. If None, uses Parsl's default.
    client : globus_compute_sdk.Client, optional
        Globus Compute client for Globus Compute resources. If None, one will
        be created automatically if needed.
    log_file : str, optional
        Path to Parsl log file. If None, no file logging is configured.
    log_level : int, optional
        Logging level (e.g., logging.DEBUG). Only used if log_file is provided.

    Yields
    ------
    None
        The context manager doesn't yield anything. Tasks can be submitted
        within the context.

    Examples
    --------
    From a configuration file:

    >>> from chiltepin import run_workflow
    >>> from chiltepin.tasks import python_task
    >>>
    >>> @python_task
    >>> def my_task():
    ...     return "Hello from workflow!"
    >>>
    >>> with run_workflow("config.yaml"):
    ...     result = my_task(executor=["compute"])
    ...     print(result.result())

    From a configuration dictionary:

    >>> config = {"laptop": {"provider": "localhost", "cores_per_node": 4}}
    >>> with run_workflow(config):
    ...     result = my_task(executor=["laptop"])
    ...     print(result.result())

    With logging and selective resources:

    >>> import logging
    >>> with run_workflow("config.yaml", include=["compute"],
    ...               log_file="workflow.log", log_level=logging.DEBUG):
    ...     # only "compute" resource is available
    ...     result = my_task(executor=["compute"])
    """
    # Parse config if it's a file path
    if isinstance(config, (str, Path)):
        config_dict = configure.parse_file(str(config))
    else:
        config_dict = config

    # Set up logging if requested
    logger_handler = None
    if log_file is not None:
        import logging as log_module

        level = log_level if log_level is not None else log_module.INFO
        logger_handler = parsl.set_file_logger(filename=log_file, level=level)

    # Initialize dfk to None before attempting to load
    dfk = None

    try:
        # Load configuration
        parsl_config = configure.load(
            config_dict,
            include=include,
            client=client,
            run_dir=run_dir,
        )

        # Load Parsl with the configuration
        dfk = parsl.load(parsl_config)

        yield
    finally:
        # Check if we're cleaning up during exception handling
        # If so, don't mask the user's exception with cleanup exceptions
        user_exception = sys.exc_info()[0] is not None
        cleanup_exception = None
        cleanup_tb = None  # Preserve original traceback

        # Attempt all cleanup operations, catching exceptions
        if dfk is not None:
            try:
                dfk.cleanup()
            except Exception as e:
                if user_exception:
                    _logger.warning(
                        "Exception during dfk.cleanup() while handling user exception",
                        exc_info=True,
                    )
                else:
                    cleanup_exception = e
                    cleanup_tb = sys.exc_info()[2]

        # Always call parsl.clear()
        try:
            parsl.clear()
        except Exception as e:
            if user_exception:
                _logger.warning(
                    "Exception during parsl.clear() while handling user exception",
                    exc_info=True,
                )
            elif cleanup_exception is None:
                cleanup_exception = e
                cleanup_tb = sys.exc_info()[2]
            else:
                e.__cause__ = cleanup_exception
                cleanup_exception = e
                cleanup_tb = sys.exc_info()[2]

        # Cleanup logger handler
        if logger_handler is not None:
            try:
                logger_handler()
            except Exception as e:
                if user_exception:
                    _logger.warning(
                        "Exception during logger cleanup while handling user exception",
                        exc_info=True,
                    )
                elif cleanup_exception is None:
                    cleanup_exception = e
                    cleanup_tb = sys.exc_info()[2]
                else:
                    e.__cause__ = cleanup_exception
                    cleanup_exception = e
                    cleanup_tb = sys.exc_info()[2]

        # Only raise cleanup exceptions if there wasn't a user exception
        # Preserve the original traceback so the error location is clear
        if cleanup_exception is not None and not user_exception:
            raise cleanup_exception.with_traceback(cleanup_tb)


# Convenience aliases for clarity
@contextmanager
def run_workflow_from_file(
    config_file: Union[str, Path],
    **kwargs,
):
    """Context manager for workflows using a YAML configuration file.

    This is an alias for run_workflow() that makes it explicit that a file
    path is expected.

    Parameters
    ----------
    config_file : str or Path
        Path to YAML configuration file
    **kwargs
        Additional arguments passed to run_workflow()

    Examples
    --------
    >>> from chiltepin import run_workflow_from_file
    >>> from chiltepin.tasks import python_task
    >>>
    >>> @python_task
    >>> def my_task():
    ...     return 42
    >>>
    >>> with run_workflow_from_file("my_config.yaml", include=["compute"]):
    ...     result = my_task(executor=["compute"])
    ...     print(result.result())
    """
    with run_workflow(config_file, **kwargs):
        yield


@contextmanager
def run_workflow_from_dict(
    config_dict: Dict[str, Any],
    **kwargs,
):
    """Context manager for workflows using a configuration dictionary.

    This is an alias for run_workflow() that makes it explicit that a dict
    is expected.

    Parameters
    ----------
    config_dict : dict
        Configuration dictionary
    **kwargs
        Additional arguments passed to run_workflow()

    Examples
    --------
    >>> from chiltepin import run_workflow_from_dict
    >>> from chiltepin.tasks import python_task
    >>>
    >>> @python_task
    >>> def my_task():
    ...     return 42
    >>>
    >>> config = {"laptop": {"provider": "localhost"}}
    >>> with run_workflow_from_dict(config):
    ...     result = my_task(executor=["laptop"])
    ...     print(result.result())
    """
    with run_workflow(config_dict, **kwargs):
        yield


__all__ = [
    "run_workflow",
    "run_workflow_from_file",
    "run_workflow_from_dict",
]
