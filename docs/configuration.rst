Configuration
=============

Chiltepin uses YAML configuration files to specify a collection of resources for use
during workflow execution. Each resource in the configuration describes a pool of computational
resources to which tasks can be submitted for execution.

Overview
--------

Resources can be:

- **Local**: Your laptop or workstation
- **HPC systems**: Accessed through job schedulers like Slurm or PBS Pro
- **Remote systems**: Accessed through Globus Compute endpoints

The configuration file defines named resources, where each resource represents a pool
of nodes and/or cores on which tasks can be executed.

Default "local" Resource
^^^^^^^^^^^^^^^^^^^^^^^^

Chiltepin automatically provides a default resource named **"local"** that is always
available, even if you don't define any resources in your configuration file. This
default resource:

- Uses the current machine (localhost provider)
- Has 1 core per worker and 1 maximum worker
- Starts with 0 blocks and can scale up to 1 block
- Is useful for testing and light computational tasks

You can use this default resource without any configuration:

.. code-block:: python

   from chiltepin import run_workflow
   from chiltepin.tasks import python_task

   @python_task
   def my_task():
       return "Hello from local!"

   # Works even with an empty config
   with run_workflow({}):
       result = my_task(executor=["local"]).result()

You can override the default "local" resource by defining your own resource with
that name in your configuration file. This is useful if you need different settings
for local execution:

.. code-block:: yaml

   local:
     provider: "localhost"
     max_blocks: 2
     max_workers_per_node: 4
     cores_per_worker: 2

Basic Structure
---------------

A Chiltepin configuration file contains one or more named resource definitions:

.. code-block:: yaml

   resource-name-1:
     provider: "slurm"
     partition: "compute"
     cores_per_node: 4
     nodes_per_block: 2
     # ... additional options
   
   resource-name-2:
     endpoint: "uuid-of-globus-compute-endpoint"
     mpi: True
     max_mpi_apps: 4
     # ... additional options

Understanding Resource Configuration
------------------------------------

Three key options determine how resources are accessed and used:

Provider: How Resources Are Acquired
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``provider`` option specifies how computational resources for running your workflow are
obtained:

- ``"localhost"`` - Use CPU resources on the current machine
- ``"slurm"`` - Obtain a pool of resources via a Slurm scheduler pilot job
- ``"pbspro"`` - Obtain a pool of resources via a PBS Pro scheduler pilot job

When using HPC providers (Slurm or PBS Pro), you can specify scheduler-specific
options like partition, queue, account, and walltime.

Endpoint: Remote Resource Access
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``endpoint`` option specifies a Globus Compute endpoint UUID for accessing
remote resources:

.. code-block:: yaml

   remote-hpc:
     endpoint: "12345678-1234-1234-1234-123456789abc"
     mpi: True
     provider: "slurm"
     partition: "gpu"

When an endpoint is specified, tasks are sent to the remote system via Globus Compute.
All other configuration options (provider, mpi, etc.) are passed to the endpoint's
configuration template (created automatically by Chiltepin when an endpoint is configured)
to describe the resource pool on the remote system.

MPI: Support for Parallel Applications
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``mpi`` option indicates whether the resource pool supports MPI (Message Passing Interface)
applications:

.. code-block:: yaml

   mpi-resource:
     mpi: True
     max_mpi_apps: 4
     provider: "slurm"
     nodes_per_block: 8

When ``mpi: True``, the resource is configured to run parallel MPI applications.
You can control how many concurrent MPI applications can run with ``max_mpi_apps``.

Resource Types
--------------

Based on the configuration options, Chiltepin automatically determines the resource type:

**Remote Resources**
  Use Globus Compute to access remote systems. Specified by providing an ``endpoint`` UUID.

**MPI Resources**
  Run parallel MPI applications on HPC systems (local or remote). Specified by setting
  ``mpi: True``.

**High-Throughput Resources**
  Run many independent tasks concurrently. This is the default when ``mpi`` is not specified
  (or is set to ``False``), whether the resources are local or remote.

Configuration Options
---------------------

Common Options
^^^^^^^^^^^^^^

These options apply to all resource types:

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Option
     - Type
     - Default
     - Description
   * - ``mpi``
     - boolean
     - ``False``
     - Enable MPI support for parallel applications
   * - ``provider``
     - string
     - ``"localhost"``
     - How to acquire resources: ``"localhost"``, ``"slurm"``, or ``"pbspro"``
   * - ``init_blocks``
     - integer
     - ``0``
     - Number of resource blocks to provision at startup
   * - ``min_blocks``
     - integer
     - ``0``
     - Minimum number of resource blocks to maintain
   * - ``max_blocks``
     - integer
     - ``1``
     - Maximum number of resource blocks allowed
   * - ``environment``
     - list
     - ``[]``
     - Shell commands to run before executing tasks (e.g., module loads)

MPI-Specific Options
^^^^^^^^^^^^^^^^^^^^

When ``mpi: True``:

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Option
     - Type
     - Default
     - Description
   * - ``max_mpi_apps``
     - integer
     - ``1``
     - Maximum number of concurrent MPI applications
   * - ``mpi_launcher``
     - string
     - ``"srun"`` (Slurm) or ``"mpiexec"``
     - MPI launcher command to use

HPC Provider Options
^^^^^^^^^^^^^^^^^^^^

When ``provider`` is ``"slurm"`` or ``"pbspro"``:

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Option
     - Type
     - Default
     - Description
   * - ``cores_per_node``
     - integer
     - ``1``
     - Number of cores per compute node (ignored for MPI resources)
   * - ``nodes_per_block``
     - integer
     - ``1``
     - Number of nodes per block/job
   * - ``exclusive``
     - boolean
     - ``True``
     - Request exclusive node allocation (Slurm only)
   * - ``partition``
     - string
     - None
     - Scheduler partition to use (Slurm only)
   * - ``queue``
     - string
     - None
     - QOS (Slurm) or queue name (PBS Pro)
   * - ``account``
     - string
     - None
     - Account/project to charge for resources
   * - ``walltime``
     - string
     - ``"00:10:00"``
     - Maximum walltime for jobs (HH:MM:SS)

High-Throughput Resource Options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For non-MPI resources:

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Option
     - Type
     - Default
     - Description
   * - ``cores_per_worker``
     - integer
     - ``1``
     - Number of cores per worker process
   * - ``max_workers_per_node``
     - integer
     - Auto
     - Maximum workers per node (auto-calculated if not specified)

Remote Resource Options
^^^^^^^^^^^^^^^^^^^^^^^

When ``endpoint`` is specified:

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Option
     - Type
     - Default
     - Description
   * - ``endpoint``
     - string
     - **Required**
     - UUID of the Globus Compute endpoint

.. note::
   All other options (provider, mpi, cores_per_node, etc.) are passed to the endpoint's
   configuration template that Chiltepin creates automatically when endpoints are configured.

Example Configurations
----------------------

Local Execution
^^^^^^^^^^^^^^^

Simple local resource for testing:

.. code-block:: yaml

   local:
     provider: "localhost"
     init_blocks: 1
     max_blocks: 1

Slurm HPC System
^^^^^^^^^^^^^^^^

Single-node computation:

.. code-block:: yaml

   compute:
     provider: "slurm"
     cores_per_node: 128
     nodes_per_block: 1
     partition: "compute"
     account: "myproject"
     walltime: "01:00:00"
     environment:
       - "module load python/3.11"
       - "module load gcc/11.2"

Multi-node MPI:

.. code-block:: yaml

   mpi:
     mpi: True
     max_mpi_apps: 2
     mpi_launcher: "srun"
     provider: "slurm"
     cores_per_node: 128
     nodes_per_block: 4
     exclusive: True
     partition: "compute"
     account: "myproject"
     walltime: "02:00:00"
     environment:
       - "module load openmpi/4.1"
       - "export MPIF90=$MPIF90"

PBS Pro System
^^^^^^^^^^^^^^

.. code-block:: yaml

   pbs-compute:
     provider: "pbspro"
     cores_per_node: 36
     nodes_per_block: 2
     queue: "normal"
     account: "MYACCT123"
     walltime: "00:30:00"
     environment:
       - "module load intel/2021"

Remote Resource via Globus Compute
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   remote-mpi:
     endpoint: "12345678-1234-1234-1234-123456789abc"
     mpi: True
     max_mpi_apps: 4
     provider: "slurm"
     cores_per_node: 128
     nodes_per_block: 8
     partition: "gpu"
     account: "myproject"
     walltime: "04:00:00"
     environment:
       - "module load cuda/11.8"
       - "module load openmpi/4.1-cuda"

Multiple Resources
^^^^^^^^^^^^^^^^^^

Combine multiple resource types in one file:

.. code-block:: yaml

   # Local service tasks
   service:
     provider: "localhost"
     max_blocks: 1
     max_workers_per_node: 3
   
   # Local HPC compute tasks
   compute:
     provider: "slurm"
     cores_per_node: 64
     nodes_per_block: 10
     partition: "standard"
     account: "myproject"
     walltime: "01:00:00"
   
   # Remote MPI tasks via Globus Compute
   remote-mpi:
     endpoint: "12345678-1234-1234-1234-123456789abc"
     mpi: True
     max_mpi_apps: 2
     provider: "slurm"
     partition: "standard"
     account: "myproject"
     nodes_per_block: 16

Environment Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

The ``environment`` option accepts a list of shell commands that are executed before running
tasks. This is commonly used for:

- Loading environment modules
- Setting environment variables
- Activating virtual environments
- Exporting paths

.. code-block:: yaml

   resource-name:
     environment:
       - "module purge"
       - "module load python/3.11 gcc/11.2 openmpi/4.1"
       - "export MY_VAR=value"
       - "source /path/to/venv/bin/activate"

.. tip::
   Use YAML anchors to share common environment setup across multiple resources:
   
   .. code-block:: yaml
   
      common_env: &common_env
        - "module load python/3.11"
        - "export PYTHONPATH=/my/path:$PYTHONPATH"
      
      resource1:
        environment: *common_env
      
      resource2:
        environment: *common_env

Loading Configurations
----------------------

Parse and Load
^^^^^^^^^^^^^^

**Loading from a file:**

.. code-block:: python

   from chiltepin import run_workflow

   # Load configuration from YAML file and run workflow
   with run_workflow(
       "my_config.yaml",
       include=["compute", "mpi"],  # Only load specific resources
       run_dir="./runinfo"           # Directory for Parsl runtime files
   ):
       # Run your tasks here
       result = my_task(executor=["compute"]).result()

**Loading from a dict:**

.. code-block:: python

   from chiltepin import run_workflow

   # Define configuration as a dictionary
   config_dict = {
       "compute": {
           "provider": "slurm",
           "account": "my-account",
           "partition": "compute",
           "nodes_per_block": 1,
           "cores_per_node": 40,
           "walltime": "01:00:00",
       },
       "mpi": {
           "provider": "slurm",
           "account": "my-account",
           "partition": "compute",
           "nodes_per_block": 2,
           "launcher": "mpi",
           "walltime": "02:00:00",
       }
   }

   # Load configuration from dict and run workflow
   with run_workflow(
       config_dict,
       include=["compute", "mpi"],  # Only load specific resources
       run_dir="./runinfo"
   ):
       # Run your tasks here
       result = my_task(executor=["compute"]).result()

The ``include`` parameter lets you selectively load only specific resources from your
configuration. If omitted, all resources are loaded.

.. note::
   The default **"local"** resource is always available, regardless of the ``include``
   parameter. You do not need to add "local" to the include list to use it. This ensures
   you always have a fallback resource available for tasks.

   .. code-block:: python

      # "local" is available even though not in include list
      with run_workflow("config.yaml", include=["compute"]):
          local_result = my_task(executor=["local"]).result()  # Works!
          compute_result = my_task(executor=["compute"]).result()  # Works!

Configuration Best Practices
-----------------------------

1. **Start Small**: Begin with short walltimes and small resource requests while testing
2. **Use Anchors**: Share common configuration blocks (like ``environment``) using YAML anchors
3. **Resource Limits**: Set appropriate ``min_blocks`` and ``max_blocks`` to control scaling
4. **Environment Modules**: Always include necessary module loads in the ``environment`` section

See Also
--------

- :doc:`quickstart` - Complete workflow example
- :doc:`endpoints` - Managing Globus Compute endpoints
- :doc:`api` - Python API reference
