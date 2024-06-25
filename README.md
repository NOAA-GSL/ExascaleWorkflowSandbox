[![ExascaleSandboxTests](https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/docker-slurm.yml/badge.svg)](https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/docker-slurm.yml)

```
This repository is a scientific product and is not official communication
of the National Oceanic and Atmospheric Administration, or the United States
Department of Commerce. All NOAA GitHub project code is provided on an ‘as
is’ basis and the user assumes responsibility for its use. Any claims against
the Department of Commerce or Department of Commerce bureaus stemming from
the use of this GitHub project will be governed by all applicable Federal
law. Any reference to specific commercial products, processes, or service
by service mark, trademark, manufacturer, or otherwise, does not constitute
or imply their endorsement, recommendation or favoring by the Department of
Commerce. The Department of Commerce seal and logo, or the seal and logo of
a DOC bureau, shall not be used in any manner to imply endorsement of any
commercial product or activity by DOC or the United States Government.
```

# Overview

NOTE: If you are reading this with a plain text editor, please note that this document is
formatted with Markdown syntax elements.  See https://www.markdownguide.org/cheat-sheet/
for more information.

This repository is a collection of tools and demonstrations used to explore
and test various technologies for implementing exascale scientific workflows.
This collection of resources is not intended for production use, and is for
research purposes only.

# Installation

This software can be installed on Linux systems.  MacOS is not currently
supported.  It can be used, however, on Macs in a container.  See below for
instructions for building and using the Docker container.

The recommended method for installation is to use a Python venv if
Python >= 3.9 is available.

```
python -m venv create .chiltepin
source .chiltepin/bin/activate
pip --use-deprecated=legacy-resolver install -r requirements.txt
pip install -e .
```

Alternatively, a conda environment (anaconda3, miniconda3, miniforge, etc.)
can be used. NOTE: Dependencies must still be installed with pip because
of certain known (and accepted) dependency conflicts that must be ignored.

```
conda create -n "chiltepin" python=3.10
conda activate chiltepin
pip --use-deprecated=legacy-resolver install -r requirements.txt
pip install -e .
```

NOTE: There may be some warnings about incompatible package versions similar
to the following:

```
ERROR: pip's legacy dependency resolver does not consider dependency conflicts when selecting packages. This behaviour is the source of the following dependency conflicts.
globus-compute-sdk 2.22.0 requires dill==0.3.6; python_version >= "3.11", but you'll have dill 0.3.8 which is incompatible.
globus-identity-mapping 0.3.0 requires typing-extensions<4.10,>=4.9, but you'll have typing-extensions 4.12.2 which is incompatible.
globus-compute-endpoint 2.22.0 requires jsonschema<4.20,>=4.19.0, but you'll have jsonschema 4.22.0 which is incompatible.
globus-compute-endpoint 2.22.0 requires parsl==2024.3.18, but you'll have parsl 2024.6.3 which is incompatible.
```

Those dependency conflicts can be safely ignored.

Once installed, Chiltepin can be used simply by activating the environment using
the command appropriate for your environment type (venv, conda, etc).


## Building and running the Chiltepin container

Chiltepin provides a Docker container environment for building and running Parsl and Chiltepin
applications. It makes use of docker compose to build a multi-node Slurm cluster for use as a
backend for running the applications.  This repository is mounted from the host into the container's
chiltepin directory.

To build the container:

```
cd docker
docker compose -f docker-compose.yml up -d --build
```

To use the container after it is built and up, log in with a bash shell:

```
docker exec -it frontend bash -l
```

Once in the container, you can install Chiltepin in editable mode, and run the tests

```
cd chiltepin
pip install -e .
cd tests
PYTHONPATH=.. pytest --assert=plain --config=config.yaml --platform=chiltepin
```

NOTE: Depending on how many cores your machine has and how many you've allocated to Docker,
you may need to modify the `cores per node` setting in the configuration yaml file to match
your machine's specifications to get all tests to pass.


# Running the test suite
The test suite is run with `pytest` and requires an editable installation of the Chiltepin
repository.  Before running the test suite:

```
cd <repository root>
pip install -e .
```

Once Chiltepin has been installed with `pip`, the tests can be run with:

```
cd tests
PYTHONPATH=.. pytest --assert=plain --config=config.yaml --platform=<platform>
```

Where `<platform>` is the specific platform where you are running the tests:

1. `ci`         #  Platform used in CI testing
2. `chiltepin`  #  Platform used for the container
3. `hercules`
3. `hera`
