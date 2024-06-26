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
pip install -e .  # Do not forget the dot at the end
```

Alternatively, a conda environment (anaconda3, miniconda3, miniforge, etc.)
can be used. NOTE: Dependencies must still be installed with pip because
of certain known (and accepted) dependency conflicts that must be ignored.

```
conda create -n "chiltepin" python=3.10
source activate chiltepin
pip --use-deprecated=legacy-resolver install -r requirements.txt
pip install -e .  # Do not forget the dot at the end
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

# Running the test suite

The test suite is run with `pytest` and requires an editable installation of the Chiltepin
repository (achieved using the `pip install -e .` installation step from above)

```
cd tests
PYTHONPATH=.. pytest --assert=plain --config=config.yaml --platform=<platform>
```

Where `<platform>` is the specific platform where you are running the tests:

1. `ci`         #  Platform used in CI testing
2. `chiltepin`  #  Platform used for the container
3. `hercules`
3. `hera`

# Building and running the Chiltepin container

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

Once in the container, you can install Chiltepin in editable mode (using the pip from the
container environment), and run the tests

```
cd chiltepin
pip install -e .
cd tests
PYTHONPATH=.. pytest --assert=plain --config=config.yaml --platform=chiltepin
```

NOTE: Depending on how many cores your machine has and how many you've allocated to Docker,
you may need to modify the `cores per node` setting in the configuration yaml file to match
your machine's specifications to get all tests to pass.

# Developer Notes

The Chiltepin containers implement a functioning Slurm cluster with [Spack-Stack](https://spack-stack.readthedocs.io/en/latest/)
installed in it. This containerized Slurm cluster is used for continuous integration testing and it can also be used for general
development and testing as needed.  The containerized cluster consists of four parts: A spack-stack container, a frontend
container, a master container, and a node container.  The spack-stack container houses the spack-stack installation and it is
copied into the frontend container at a volume mount point that is shared with the other containers.  The frontend container
serves as the so-called cluster "login" node and is where users will log in and run commands to interact with the cluster. The
master container implements the Slurm controller node which runs the Slurm controller daemons for managing scheduling of jobs
on the cluster.  The node container implements Slurm "compute" nodes where Slurm jobs execute.  Several instances of the node
cluster are used to construct multiple Slurm "compute" nodes.  The container runs, of course, on a single host machine with
limited resources, so the "frontend", "master", and "compute" nodes all share the same physical resources.  The "compute" nodes
are configured to have a core count equal to the number of CPUs given to the Docker VM.

## Modifying the spack-stack container
Developers that modify the spack-stack container in order to update the development software stack will need to rebuild it.
Depending on what is needed, this may not be a straightforward process due to the complexity of spack-stack and the need to
customize the spack-stack container to meet the needs of Chiltepin. An addition complication is that a Spack buildcache mirror
is used to speed up build times by caching builds of Spack packages.  Read-only access to the buildcache is always provided
via the Dockerfile.  However, if the stack has changed and new packages are built from source, those must get pushed to the
buildcache, which resides on S3.  Write access requires AWS authentication and is only granted to authorized users.


To do a basic build of a spack-stack Dockerfile (from the `docker/spack-stack` directory) where read-only access to the
buildcache is sufficient:

```
docker buildx build --progress=plain -t ghcr.io/noaa-gsl/exascaleworkflowsandbox/spack-stack-gnu-openmpi:latest -f Dockerfile .
```

To do an advanced build of the spack-stack container, several steps are required:

1. Make sure the awscli package is installed so that the `aws` command is available

2. Create an AWS profile in `$HOME/.aws/config`:
```
[profile myprofile]
sso_start_url = https://<my start address>/start#/
sso_region = <region for sso authentication>
sso_account_id = <sso account id>
sso_role_name = <sso role name>
region = us-east-2
```

3. Log in to AWS
NOTE: These credentials are only valid for one hour
```
aws sso login --profile <myprofile>
```

4. Create the Spack mirror file (mirrors.yaml) 

WARNING: DO NOT COMMIT THE `mirrors.yaml` FILE TO THE REPOSITORY!!
```
cd docker/spack-stack
./get_sso_credentials.sh <myprofile>
```

5. Export the AWS credentials into your environment
```
cd docker/spack-stack
aws configure export-credentials --format env --profile <myprofile>
```

Run the export commands output by the above command

6. Build the container, passing AWS credentials in as Docker secrets 
```
docker buildx build --secret id=mirrors,src=mirrors.yaml --secret id=access_key_id,env=AWS_ACCESS_KEY_ID --secret id=secret_access_key,env=AWS_SECRET_ACCESS_KEY --secret id=session_token,env=AWS_SESSION_TOKEN --progress=plain -t ghcr.io/noaa-gsl/exascaleworkflowsandbox/spack-stack-gnu-openmpi:latest -f Dockerfile .
```

The above allows Spack to push the rebuilt packages to the Spack buildcache on AWS S3.
Once in the buildcache, those packages do not need to be rebuilt for subsequent container
builds.
