# SPDX-License-Identifier: Apache-2.0

"""Chiltepin: Federated NWP Workflow Tools.

This package provides tools for building scientific workflows that can execute
on distributed computing resources using Parsl and Globus services.
"""

from chiltepin.workflow import workflow, workflow_from_dict, workflow_from_file

__all__ = [
    "workflow",
    "workflow_from_file",
    "workflow_from_dict",
]
