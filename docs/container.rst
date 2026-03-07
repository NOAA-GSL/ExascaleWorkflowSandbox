Docker Container
================

Chiltepin provides a Docker container environment for building and running 
Chiltepin applications. The container uses Docker Compose to build a multi-node 
Slurm cluster that serves as a backend for running workflow applications.

This is particularly useful for:

* Development and testing on macOS or Windows
* Creating a consistent testing environment
* Demonstrating Chiltepin capabilities without access to HPC systems

Prerequisites
-------------

You need to have Docker and Docker Compose installed on your system:

* `Docker <https://docs.docker.com/get-docker/>`_
* `Docker Compose <https://docs.docker.com/compose/install/>`_

Building the Container
----------------------

To build the Docker container environment:

.. code-block:: console

   $ cd docker
   $ docker compose -f docker-compose.yml up -d

This will build and start a multi-node Slurm cluster. The process may take several 
minutes the first time as it downloads and builds the necessary images.

Accessing the Container
-----------------------

Once the container is built and running, you can access it with a bash shell:

.. code-block:: console

   $ docker exec -it frontend bash -l

This will log you into the frontend node of the Slurm cluster.

Installing Chiltepin in the Container
--------------------------------------

Inside the container, the repository is mounted at ``~/chiltepin``. To install 
Chiltepin in editable mode:

.. code-block:: console

   (container) $ cd chiltepin
   (container) $ pip install -e .[test]

.. note::

   The ``[test]`` option ensures that dependencies required for running the tests 
   are installed.

Running Tests in the Container
-------------------------------

After installation, you can run the test suite using the Docker-specific configuration:

.. code-block:: console

   (container) $ pytest --config=tests/configs/docker.yaml

For more verbose output:

.. code-block:: console

   (container) $ pytest -s -vvv --config=tests/configs/docker.yaml

Adjusting Core Count
--------------------

Depending on how many cores your machine has and how many you've allocated to Docker, 
you may need to modify the ``cores_per_node`` setting in ``tests/configs/docker.yaml`` 
to match your machine's specifications for all tests to pass.

Container Architecture
----------------------

The Docker environment consists of:

* **Frontend node**: Where you interact with the system and submit jobs
* **Compute nodes**: Multiple Slurm compute nodes for running jobs
* **Master node**: The Slurm controller that manages job scheduling and resource allocation
* **Shared volume**: A shared directory for data and code accessible by all nodes

This simulates a real HPC cluster environment with job scheduling and multi-node execution.

Stopping the Container
----------------------

To stop the container environment:

.. code-block:: console

   $ cd docker
   $ docker compose -f docker-compose.yml down

To stop and remove all data:

.. code-block:: console

   $ cd docker
   $ docker compose -f docker-compose.yml down -v

Troubleshooting
---------------

**Container won't start:**
   Check that Docker has sufficient resources allocated (CPU, memory, disk space).

**Tests fail with resource errors:**
   Reduce the ``cores_per_node`` values in the Docker configuration file.

**Cannot access mounted repository:**
   Ensure Docker has permission to access the repository directory on your host system. If not,
   clone the repository directly inside the container and install Chiltepin there.
