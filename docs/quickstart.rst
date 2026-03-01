Quick Start
===========

This guide walks you through a complete Chiltepin workflow, from setting up an endpoint to submitting tasks.

Overview
--------

Chiltepin is a collection of tools for exploring and testing technologies for 
implementing exascale scientific workflows using Parsl and Globus Compute.

.. warning::

   This collection of resources is not intended for production use, and is for
   research purposes only.

Prerequisites
-------------

Before starting, ensure you have:

1. Installed Chiltepin (see :doc:`installation`)
2. Access to an HPC system (or use local execution for testing)
3. A web browser for Globus authentication

Complete Workflow Example
--------------------------

This example demonstrates the full workflow: configure an endpoint, start it, and submit tasks.

Step 1: Authenticate
^^^^^^^^^^^^^^^^^^^^

First, log in to Globus services:

.. code-block:: bash

   $ chiltepin login

This opens a browser for authentication. Follow the prompts to authorize Chiltepin.

Step 2: Configure an Endpoint
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create a new Globus Compute endpoint:

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

   # Local executor for small tasks
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

   import parsl
   import chiltepin.configure
   from chiltepin.tasks import bash_task, python_task
   
   # Load configuration
   config_dict = chiltepin.configure.parse_file("my_config.yaml")
   parsl_config = chiltepin.configure.load(
       config_dict,
       include=["local", "remote"],
       run_dir="./runinfo"
   )
   parsl.load(parsl_config)
   
   # Define tasks
   @python_task(executors=["local"])
   def hello_local():
       import platform
       return f"Hello from {platform.node()}"
   
   @bash_task(executors=["remote"])
   def hello_remote():
       return "hostname && echo 'Hello from remote endpoint!'"
   
   @python_task(executors=["remote"])
   def compute_task(n):
       """Simple computation task"""
       result = sum(i**2 for i in range(n))
       return result
   
   # Submit tasks
   if __name__ == "__main__":
       # Run local task
       local_future = hello_local()
       print(f"Local: {local_future.result()}")
       
       # Run remote bash task
       remote_future = hello_remote()
       print(f"Remote: {remote_future.result()}")
       
       # Run multiple compute tasks
       futures = [compute_task(i * 1000) for i in range(1, 5)]
       results = [f.result() for f in futures]
       print(f"Computation results: {results}")
       
       print("All tasks completed!")

Step 7: Run Your Workflow
^^^^^^^^^^^^^^^^^^^^^^^^^^

Execute the workflow:

.. code-block:: bash

   $ python my_workflow.py

Expected output:

.. code-block:: text

   Local: Hello from my-laptop.local
   Remote: my-hpc-node001
   Hello from remote endpoint!
   Computation results: [0, 1333333000, 10666664000, 35999995000]
   All tasks completed!

Step 8: Stop the Endpoint
^^^^^^^^^^^^^^^^^^^^^^^^^^

When finished:

.. code-block:: bash

   $ chiltepin endpoint stop my-endpoint

.. note::
   Endpoints automatically shut down after idle periods, so manual stopping is optional.

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

   import parsl
   import chiltepin.configure
   from chiltepin.tasks import bash_task, python_task
   
   # Load configuration  
   config_dict = chiltepin.configure.parse_file("local_config.yaml")
   parsl_config = chiltepin.configure.load(config_dict, run_dir="./runinfo")
   parsl.load(parsl_config)
   
   # Define and run tasks
   @python_task
   def multiply(a, b):
       return a * b
   
   @bash_task
   def system_info():
       return "uname -a"
   
   if __name__ == "__main__":
       result = multiply(6, 7).result()
       print(f"6 * 7 = {result}")
       
       info = system_info().result()
       print(f"System: {info}")

Run it:

.. code-block:: bash

   $ python simple_workflow.py

Working with MPI Tasks
----------------------

Chiltepin supports MPI applications on HPC systems:

Configuration (``mpi_config.yaml``)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   mpi-executor:
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

   import parsl
   import chiltepin.configure
   from chiltepin.tasks import bash_task
   
   config_dict = chiltepin.configure.parse_file("mpi_config.yaml")
   parsl_config = chiltepin.configure.load(config_dict, run_dir="./runinfo")
   parsl.load(parsl_config)
   
   @bash_task(executors=["mpi-executor"])
   def compile_mpi():
       return "$MPIF90 -o mpi_app mpi_app.f90"
   
   @bash_task(executors=["mpi-executor"])
   def run_mpi(ranks=4):
       return f"srun -n {ranks} ./mpi_app"
   
   if __name__ == "__main__":
       # Compile MPI application
       compile_result = compile_mpi().result()
       print(f"Compilation: {compile_result}")
       
       # Run with different rank counts
       results = []
       for ranks in [4, 8, 16]:
           future = run_mpi(ranks)
           results.append(future.result())
       
       for i, result in enumerate(results, 1):
           print(f"Run {i}: {result}")

Key Concepts
------------

Executors
^^^^^^^^^

Executors define where and how tasks run:

- **Local**: Runs on the current machine
- **HPC**: Submits jobs to schedulers (Slurm, PBS Pro)
- **Globus Compute**: Runs on remote endpoints

Task Decorators
^^^^^^^^^^^^^^^

Chiltepin provides task decorators:

- ``@python_task``: Execute Python functions
- ``@bash_task``: Execute shell commands
- ``@mpi_task``: Execute MPI applications

Specify executors with the ``executors`` parameter:

.. code-block:: python

   @python_task(executors=["remote"])
   def my_task():
       return "Runs on remote executor"

Configuration Loading
^^^^^^^^^^^^^^^^^^^^^

The ``include`` parameter selects specific executors:

.. code-block:: python

   # Load only specific executors
   parsl_config = chiltepin.configure.load(
       config_dict,
       include=["local", "compute"],  # Only these executors
       run_dir="./runinfo"
   )

If ``include`` is omitted, all executors in the configuration are loaded.

Directory Structure
-------------------

After running workflows, you'll see:

.. code-block:: text

   .
   ├── my_config.yaml              # Configuration file
   ├── my_workflow.py              # Workflow script
   └── runinfo/                    # Parsl runtime directory
       ├── 000/                     # Run directory
       │   ├── local/               # Local executor files
       │   ├── remote/              # Remote executor files
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
- Ensure walltime is sufficient
- Confirm node/core requests are within limits

Next Steps
----------

* Detailed configuration options: :doc:`configuration`
* Endpoint management: :doc:`endpoints`
* Run the test suite: :doc:`testing`
* Set up Docker environment: :doc:`container`
* Explore the API: :doc:`api`
