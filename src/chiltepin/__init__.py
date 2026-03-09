# SPDX-License-Identifier: Apache-2.0

"""Chiltepin: Federated NWP Workflow Tools.

This package provides tools for building scientific workflows that can execute
on distributed computing resources using Parsl and Globus services.
"""

__all__ = [
    "run_workflow",
    "run_workflow_from_file",
    "run_workflow_from_dict",
]


def __getattr__(name):
    """Lazy import of workflow functions to avoid loading Parsl unnecessarily.

    This allows users to import other chiltepin submodules (like configure, tasks)
    without triggering the import of Parsl and its dependencies unless they
    actually use the workflow context managers.
    """
    if name in __all__:
        from chiltepin.workflow import (  # noqa: F401
            run_workflow,
            run_workflow_from_dict,
            run_workflow_from_file,
        )

        globals()[name] = locals()[name]
        return locals()[name]

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
