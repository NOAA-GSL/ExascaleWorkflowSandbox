[![ExascaleSandboxTests](https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/test-suite.yaml/badge.svg)](https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/test-suite.yaml)
[![Documentation](https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/docs.yaml/badge.svg)](https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/docs.yaml)

# Chiltepin

## Overview

This repository is a collection of tools and demonstrations used to explore
and test various technologies for implementing exascale scientific workflows.
This collection of resources is not intended for production use, and is for
research purposes only.

Chiltepin provides Python decorators and utilities for building scientific workflows
that can execute on distributed computing resources using [Parsl](https://parsl-project.org/)
and [Globus](https://www.globus.org/) services.

## Documentation

**📚 Full documentation is available at [Read the Docs](https://exascaleworkflowsandbox.readthedocs.io/)**

Key documentation sections:
- [Installation Guide](https://exascaleworkflowsandbox.readthedocs.io/en/latest/installation.html) - Installing Chiltepin on Linux, macOS, Windows, and Docker
- [Quick Start](https://exascaleworkflowsandbox.readthedocs.io/en/latest/quickstart.html) - Your first Chiltepin workflow
- [Tasks](https://exascaleworkflowsandbox.readthedocs.io/en/latest/tasks.html) - Python, Bash, and Join task decorators
- [Configuration](https://exascaleworkflowsandbox.readthedocs.io/en/latest/configuration.html) - Configuring compute resources
- [Endpoints](https://exascaleworkflowsandbox.readthedocs.io/en/latest/endpoints.html) - Managing Globus Compute endpoints
- [Data Transfer](https://exascaleworkflowsandbox.readthedocs.io/en/latest/data.html) - Using Globus for data movement
- [Testing Guide](https://exascaleworkflowsandbox.readthedocs.io/en/latest/testing.html) - Running the test suite

## Quick Start

Install Chiltepin in a Python virtual environment:

```bash
python -m venv .chiltepin
source .chiltepin/bin/activate
pip install -e .
```

For detailed installation instructions including conda, Docker, and platform-specific guidance,
see the [Installation Guide](https://exascaleworkflowsandbox.readthedocs.io/en/latest/installation.html).

## Contributing

Contributions are welcome! For information on running tests and contributing to development,
see the [Testing Guide](https://exascaleworkflowsandbox.readthedocs.io/en/latest/testing.html).

## License

See [LICENSE](LICENSE) for details.

