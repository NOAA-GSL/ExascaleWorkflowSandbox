Quick Start
===========

This guide walks you through a complete Chiltepin workflow, from setting up an
endpoint to submitting tasks.

Overview
--------

Chiltepin is a collection of tools for implementing distributed exascale numerical
weather prediction workflows using Parsl and Globus Compute.

.. warning::

   This collection of resources is not intended for use in operational production
   environments, and is for research purposes only.

Prerequisites
-------------

Before starting, ensure you have:

1. Installed Chiltepin (see :doc:`installation`)
2. Access to an HPC system (or use local execution for testing)
3. A `Globus account <https://www.globus.org/>`_ and a web browser for Globus authentication

Complete Workflow Example
--------------------------

This example demonstrates the full workflow: configure an endpoint, start it, and submit tasks.

Step 1: Authenticate
^^^^^^^^^^^^^^^^^^^^

First, log in to Globus services. This should be done on the machine where you want to run
tasks:

.. code-block:: bash

   $ chiltepin login

This opens a browser for authentication or, if one is not available, provides a URL to complete
the authentication manually. Follow the prompts to authorize Chiltepin.

Step 2: Configure an Endpoint
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a new Globus Compute endpoint to which you will submit tasks. This should be done on the
machine where you want to run tasks:

.. code-block:: bash

   $ chiltepin endpoint configure my-endpoint

This creates the endpoint configuration in ``~/.globus_compute/my-endpoint/``.

Step 3: Start the Endpoint
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Launch the endpoint:

.. code-block:: bash

   $ chiltepin endpoint start my-endpoint

The endpoint will register with Globus Compute and begin accepting tasks.

Step 4: Get the Endpoint UUID
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Retrieve your endpoint's UUID:

.. code-block:: bash

   $ chiltepin endpoint list

Example output:

.. code-block:: text

   my-endpoint  a1b2c3d4-1234-5678-90ab-cdef12345678  Running

Note the UUID (``a1b2c3d4-1234-5678-90ab-cdef12345678``) for the next step.

Step 5: Create a Configuration File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create ``my_config.yaml`` with your endpoint UUID:

.. code-block:: yaml

   # Local resource for small tasks
   local:
     provider: "localhost"
     init_blocks: 1
     max_blocks: 1
   
   # Remote endpoint for HPC tasks
   remote:
     endpoint: "a1b2c3d4-1234-5678-90ab-cdef12345678"  # Use your UUID
     provider: "slurm"
     cores_per_node: 4
     nodes_per_block: 1
     partition: "compute"
     account: "myproject"
     walltime: "00:30:00"
     environment:
       - "module load python/3.11"

Replace the endpoint UUID with your actual UUID from Step 4.

Step 6: Write Your Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create ``my_workflow.py``:

.. code-block:: python

   from chiltepin import workflow
   from chiltepin.tasks import bash_task, python_task
   
   # Define tasks
   @python_task
   def hello_local():
       import platform
       return f"Hello from {platform.node()}"
   
   @bash_task
   def hello_remote():
       return "hostname"
   
   @python_task
   def compute_task(n):
       """Simple computation task"""
       result = sum(i**2 for i in range(n))
       return result
   
   if __name__ == "__main__":
       # Load configuration and run workflow
       with chiltepin.workflow("my_config.yaml", include=["local", "remote"], run_dir="./runinfo"):
           # Run local task on "local" resource
           local_future = hello_local(executor=["local"])
           
           # Run remote bash task on "remote" resource (returns exit code: 0 = success)
           remote_future = hello_remote(executor=["remote"])
           
           # Run multiple compute tasks on "remote" resource
           futures = [compute_task(i, executor=["remote"]) for i in range(1, 5)]
           
           # Get the results
           print(f"Local: {local_future.result()}")
           print(f"Remote exit code: {remote_future.result()}")
           print(f"Computation results: {[f.result() for f in futures]}")
           
           print("All tasks completed!")

Step 7: Run Your Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^

Execute the workflow:

.. code-block:: bash

   $ python my_workflow.py

Expected output:

.. code-block:: text

   Local: Hello from my-laptop.local
   Remote exit code: 0
   Computation results: [0, 1, 5, 14]
   All tasks completed!

Step 8: Stop the Endpoint
^^^^^^^^^^^^^^^^^^^^^^^^^^

When finished:

.. code-block:: bash

   $ chiltepin endpoint stop my-endpoint

.. note::
   Endpoints automatically scale down resources after idle periods, so manual stopping is
   optional.

Local-Only Quickstart
---------------------

For testing without an HPC system, use local execution:

Configuration File (``local_config.yaml``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   local:
     provider: "localhost"
     init_blocks: 1
     max_blocks: 1

Simple Workflow (``simple_workflow.py``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from chiltepin import workflow
   from chiltepin.tasks import bash_task, python_task
   
   # Define tasks
   @python_task
   def multiply(a, b):
       return a * b
   
   @bash_task
   def system_info():
       return "echo 'Task completed successfully'"
   
   if __name__ == "__main__":
       # Load configuration and run workflow
       with chiltepin.workflow("local_config.yaml", run_dir="./runinfo"):
           result = multiply(6, 7, executor=["local"]).result()
           print(f"6 * 7 = {result}")
           
           exit_code = system_info(executor=["local"]).result()
           print(f"Bash task exit code: {exit_code}")

Run it:

.. code-block:: bash

   $ python simple_workflow.py

Working with MPI Tasks
----------------------

Chiltepin supports MPI applications on HPC systems:

Configuration (``mpi_config.yaml``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   mpi-resource-name:
     endpoint: "your-endpoint-uuid"
     mpi: True
     max_mpi_apps: 2
     mpi_launcher: "srun"
     provider: "slurm"
     cores_per_node: 128
     nodes_per_block: 4
     partition: "compute"
     account: "myproject"
     walltime: "01:00:00"
     environment:
       - "module load openmpi/4.1"
       - "export MPIF90=$MPIF90"

MPI Workflow
^^^^^^^^^^^^

.. code-block:: python

   from chiltepin import workflow
   from chiltepin.tasks import bash_task
   
   @bash_task
   def compile_mpi():
       return "$MPIF90 -o mpi_app mpi_app.f90"
   
   @bash_task
   def run_mpi(ranks=4):
       return f"srun -n {ranks} ./mpi_app"
   
   if __name__ == "__main__":
       with chiltepin.workflow("mpi_config.yaml", run_dir="./runinfo"):
           # Compile MPI application on the MPI resource (returns exit code)
           compile_result = compile_mpi(executor=["mpi-resource-name"]).result()
           print(f"Compilation exit code: {compile_result}")
           
           # Run with different rank counts on the MPI resource
           results = []
           for ranks in [4, 8, 16]:
               future = run_mpi(ranks, executor=["mpi-resource-name"])
               results.append(future.result())
           
           for i, result in enumerate(results, 1):
               print(f"Run {i} exit code: {result}")

Key Concepts
------------

Resources
^^^^^^^^^

Resources define where and how tasks run:

- **Local**: Runs on the current machine
- **HPC**: Submits jobs to schedulers (Slurm, PBS Pro)
- **Globus Compute**: Runs on remote endpoints

See :doc:`configuration` for detailed resource configuration options.

Task Decorators
^^^^^^^^^^^^^^^

Chiltepin provides three task decorators to define workflow tasks:

- ``@python_task``: Execute Python functions
- ``@bash_task``: Execute shell commands (returns exit code)
- ``@join_task``: Coordinate multiple tasks without blocking

When calling a task, use the ``executor`` parameter to specify which resource to use:

.. code-block:: python

   @python_task
   def my_task():
       return "result"
   
   # Specify which resource to use
   result = my_task(executor="compute").result()

The ``executor`` value must match a resource name from your configuration file.

.. seealso::
   For comprehensive documentation on defining and using tasks, including advanced
   patterns, error handling, and best practices, see :doc:`tasks`.

Configuration Loading
^^^^^^^^^^^^^^^^^^^^^

The ``include`` parameter selects specific resources to load from the configuration.

**Loading from a file:**

.. code-block:: python

   # Load only specific resources from YAML file
   with workflow(
       "my_config.yaml",
       include=["local", "compute"],  # Only these resources
       run_dir="./runinfo"
   ):
       # Run tasks using selected resources
       result = my_task(executor=["compute"]).result()

**Loading from a dict:**

.. code-block:: python

   # Define configuration as a dictionary
   config = {
       "local": {
           "provider": "localhost",
           "cores_per_node": 4,
       },
       "compute": {
           "provider": "slurm",
           "partition": "compute",
           "nodes_per_block": 1,
       }
   }

   # Load only specific resources from dict
   with workflow(
       config,
       include=["local", "compute"],  # Only these resources
       run_dir="./runinfo"
   ):
       # Run tasks using selected resources
       result = my_task(executor=["compute"]).result()

If ``include`` is omitted, all resources in the configuration are loaded.

Directory Structure
-------------------

After running workflows, you'll see:

.. code-block:: text

   .
   ├── my_config.yaml              # Configuration file
   ├── my_workflow.py              # Workflow script
   └── runinfo/                    # Parsl runtime directory
       ├── 000/                     # Run directory
       │   ├── local/               # Local resource files
       │   ├── remote/              # Remote resource files
       │   └── submit_scripts/      # Job submission scripts
       └── parsl.log                # Parsl log file

The ``runinfo`` directory contains execution logs, job scripts, and task outputs.

Troubleshooting
---------------

Tasks Not Running
^^^^^^^^^^^^^^^^^

1. Verify endpoint is running: ``chiltepin endpoint list``
2. Check you're using the correct endpoint UUID
3. Review logs in ``runinfo/`` directory
4. Check endpoint logs: ``~/.globus_compute/my-endpoint/endpoint.log``

Authentication Expired
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   $ chiltepin logout
   $ chiltepin login

Configuration Errors
^^^^^^^^^^^^^^^^^^^^

Validate your YAML syntax:

.. code-block:: python

   import yaml
   with open("my_config.yaml") as f:
       config = yaml.safe_load(f)
       print(config)

Resource Limits
^^^^^^^^^^^^^^^

If jobs fail to start:

- Check partition/queue names
- Verify account/project is valid  
- Confirm node/core requests are within limits
- Machine may be busy and resource pool job may be pending or may be full

Next Steps
----------

* Comprehensive task documentation: :doc:`tasks`
* Detailed configuration options: :doc:`configuration`
* Endpoint management: :doc:`endpoints`
* Run the test suite: :doc:`testing`
* Set up Docker environment: :doc:`container`
* Explore the API: :doc:`api`
