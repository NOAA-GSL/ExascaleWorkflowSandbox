[![ExascaleSandboxTests](https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/docker-slurm.yaml/badge.svg)](https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/docker-slurm.yaml)
[![MPAS App](https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/mpas-app.yaml/badge.svg)](https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/mpas-app.yaml)

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
python -m venv .chiltepin
source .chiltepin/bin/activate
pip --use-deprecated=legacy-resolver install -e .[test]
```

Alternatively, a conda environment (anaconda3, miniconda3, miniforge, etc.)
can be used. NOTE: Dependencies must still be installed with pip because
of certain known (and accepted) dependency conflicts that must be ignored.

```
conda create -n "chiltepin" python=3.10
source activate chiltepin
pip --use-deprecated=legacy-resolver install -e .[test]
```

NOTE: The `[test]` ensures that dependencies required for running the tests are installed.

NOTE: There may be some warnings about incompatible package versions similar
to the following:

```
ERROR: pip's legacy dependency resolver does not consider dependency conflicts when selecting packages. This behaviour is the source of the following dependency conflicts.
globus-identity-mapping 0.3.0 requires typing-extensions<4.10,>=4.9, but you'll have typing-extensions 4.12.2 which is incompatible.
```

Those dependency conflicts can be safely ignored.

Once installed, Chiltepin can be used simply by activating the environment using
the command appropriate for your environment type (venv, conda, etc).

# Running the test suite

The test suite is run with `pytest` and requires an editable installation of the Chiltepin
repository (achieved using the `pip install -e .` installation step from above)

An additional step is required for successful completion of the Globus Compute tests. These
tests require users to authenticate to globus before running the pytest command. This is done
with the `globus-compute-endpoint login` command.

```
globus-compute-endpoint login
pytest --assert=plain --config=tests/config.yaml --platform=<platform>
```

Where `<platform>` is the specific platform where you are running the tests:

1. `docker`  #  Platform used for the container
2. `hercules`
3. `hera`

For more detailed information during testing
```
pytest -s -vvv --assert=plain --config=tests/config.yaml --platform=<platform>
```

# Building and running the Chiltepin container

Chiltepin provides a Docker container environment for building and running Parsl and Chiltepin
applications. It makes use of docker compose to build a multi-node Slurm cluster for use as a
backend for running the applications.  This repository is mounted from the host into the container's
chiltepin directory.

To build the container:

```
cd docker
docker compose -f docker-compose.yml up -d
```

To use the container after it is built and up, log in with a bash shell:

```
docker exec -it frontend bash -l
```

Once in the container, you can install Chiltepin in editable mode (using the pip from the
container environment), and run the tests

```
cd chiltepin
pip --use-deprecated=legacy-resolver install -e .[test]
pytest --assert=plain --config=tests/config.yaml --platform=docker
```

NOTE: the `[test]` ensures that dependencies required for running the tests are installed.

NOTE: Depending on how many cores your machine has and how many you've allocated to Docker,
you may need to modify the `cores per node` setting in the configuration yaml file to match
your machine's specifications to get all tests to pass.
