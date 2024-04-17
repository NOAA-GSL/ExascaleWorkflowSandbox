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

This software can be installed on Linux systems.  NOTE: MacOS is not supported
because the Flux scheduler does not support MacOS.  It can be used, however,
on Macs in a container.  See below for instructions for building and using
the Docker container.

## Dependencies

Installation and use of Chiltepin requires Python version 3.6 or higher.

Additionally, in order to take advantage of buildcache mirrors for faster
installation, the boto3 Python package is required.  Installation will work
without boto3, but will require the Chiltepin dependencies to be built from
scratch instead of being pulled from the buildcache.

NOTE: For Python 3.6, `botocore 1.25.0` is required:

```
python3 -m pip install --user boto3==1.23.10 botocore==1.25.0
```

For Python 3.7+ it should be sufficient to install the latest boto3

```
python3 -m pip install --user boto3
```

Alternatively, users can install their own Python using something like
miniconda3 or make use of virtual environments as appropriate.

## Install the Chiltepin spack environment

The Flux packages must be installed with Spack.  A convenience installation
script is provided which installs spack and then builds the chiltepin
environment containing the flux packages as well as pytest and parsl.

```
cd install
./install.sh
```

## Activate the Chiltepin spack environment

After the chiltepin spack environment is built it must be activated. While
the installation step above needs to be done only once, this step must be
done in each new shell where you want to use Chiltepin.  This step is very
similar to activation of conda environments.  First, spack must be
initialized, and then the environment activation command can be run.

```
cd install
. spack/share/spack/setup-env.sh
spack env activate chiltepin

```

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
pytest --assert=plain --config=config.yaml --platform=chiltepin
```

NOTE: Depending on how many cores your machine has and how many you've allocated to Docker,
you may need to modify the `cores per node` setting in the configuration yaml file to match
your machine's specifications to get all tests to pass.

# Running Parsl apps

If running Chiltepin in the container, the Chiltepin spack environment is activated
automatically when logging in to the front-end node.  If running on an HPC, it must be
activated  manually to run Parsl Chiltepin applications

```
cd install
. spack/share/spack/setup-env.sh
spack env activate chiltepin
```

# Running the test suite
The test suite is run with `pytest` and requires an editable installation of the Chiltepin
repository.  Before running the test suite:

```
cd <repository root>
pip install -e .
```

Once Chiltepin has been installed with `pip`, the tests can be run with:

```
pytest --assert=plain --config=config.yaml --platform=<platform>
```

Where `<platform>` is the specific platform where you are running the tests:

1. `ci`         #  Platform used in CI testing
2. `chiltepin`  #  Platform used for the container
3. `hercules`
3. `hera`
