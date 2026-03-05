Configuration
=============

Chiltepin uses YAML configuration files to define compute resources for workflow execution. This page
documents the configuration format and available options.

Configuration Structure
-----------------------------

A Chiltepin configuration defines one or more named resources. Each resource can use
either local resources, HPC resources acquired via schedulers (Slurm, PBS Pro), or Globus
Compute endpoints for remote execution.

Basic Structure
^^^^^^^^^^^^^^^

.. code-block:: yaml

   executor-name-1:
     mpi: False
     provider: "slurm"
     cores_per_node: 4
     # ... additional options
   
   executor-name-2:
     endpoint: "uuid-of-globus-compute-endpoint"
     mpi: True
     # ... additional options

Resource Types
--------------

Chiltepin supports three types of resources:

1. **Local**: Run tasks on the local machine using Parsl's HighThroughputExecutor
2. **HPC**: Submit tasks to local HPC schedulers (Slurm, PBS Pro) using Parsl's HighThroughputExecutor or MPIExecutor
3. **Remote**: Submit tasks to remote Globus Compute endpoints using Parsl's GlobusComputeExecutor

The resource type is determined automatically:

- If ``endpoint`` is specified → Globus Compute resource
- If ``mpi: True`` → MPI executor (for HPC systems)
- Otherwise → HighThroughput executor

Configuration Options
---------------------

Common Options
^^^^^^^^^^^^^^

These options apply to all executor types:

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
     - Enable MPI support for parallel jobs
   * - ``provider``
     - string
     - ``"localhost"``
     - Execution provider: ``"localhost"``, ``"slurm"``, or ``"pbspro"``
   * - ``init_blocks``
     - integer
     - ``0``
     - Number of blocks to provision at startup
   * - ``min_blocks``
     - integer
     - ``0``
     - Minimum number of blocks to maintain
   * - ``max_blocks``
     - integer
     - ``1``
     - Maximum number of blocks allowed
   * - ``environment``
     - list
     - ``[]``
     - List of shell commands to run before executing tasks (e.g., module loads)

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
     - Number of cores per compute node (ignored for MPI executors)
   * - ``nodes_per_block``
     - integer
     - ``1``
     - Number of nodes per block/job
   * - ``exclusive``
     - boolean
     - ``True``
     - Request exclusive node allocation
   * - ``partition``
     - string
     - None
     - Scheduler partition/queue to use (Slurm only)
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

HighThroughput Executor Options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For non-MPI executors:

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

Globus Compute Executor Options
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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
     - UUID of the Globus Compute endpoint (can use Jinja2 template variables)

.. note::
   All other options (provider, mpi, cores_per_node, etc.) are passed to the endpoint's user configuration template.

Example Configurations
----------------------

Local Execution
^^^^^^^^^^^^^^^

Simple local executor for testing:

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

Globus Compute Endpoint
^^^^^^^^^^^^^^^^^^^^^^^^

Using a remote endpoint with Jinja2 template variable:

.. code-block:: yaml

   remote-mpi:
     endpoint: "{{ my_endpoint_id }}"
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

When using this configuration, replace the template variable:

.. code-block:: python

   from jinja2 import Template
   
   with open("config.yaml") as f:
       template = Template(f.read())
   
   rendered = template.render(my_endpoint_id="12345678-1234-1234-1234-123456789abc")
   config = yaml.safe_load(rendered)

Multiple Executors
^^^^^^^^^^^^^^^^^^

Combine multiple executor types in one file:

.. code-block:: yaml

   # Local service tasks
   service:
     provider: "localhost"
     max_blocks: 1
   
   # HPC compute tasks
   compute:
     provider: "slurm"
     cores_per_node: 64
     partition: "standard"
     account: "myproject"
     walltime: "01:00:00"
   
   # Remote MPI tasks via Globus Compute
   remote-mpi:
     endpoint: "{{ endpoint_uuid }}"
     mpi: True
     max_mpi_apps: 2
     provider: "slurm"
     nodes_per_block: 16

Loading Configurations
----------------------

Parse and Load
^^^^^^^^^^^^^^

.. code-block:: python

   import chiltepin.configure
   import parsl
   
   # Parse YAML configuration file
   config_dict = chiltepin.configure.parse_file("my_config.yaml")
   
   # Create Parsl configuration
   parsl_config = chiltepin.configure.load(
       config_dict,
       include=["compute", "mpi"],  # Only load specific executors
       run_dir="./runinfo"           # Directory for Parsl runtime files
   )
   
   # Initialize Parsl with configuration
   parsl.load(parsl_config)

The ``include`` parameter lets you selectively load only specific executors from your configuration file. If omitted, all executors are loaded.

Environment Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

The ``environment`` option accepts a list of shell commands that are executed before running tasks. This is commonly used for:

- Loading environment modules
- Setting environment variables
- Activating virtual environments
- Exporting paths

.. code-block:: yaml

   executor-name:
     environment:
       - "module purge"
       - "module load python/3.11 gcc/11.2 openmpi/4.1"
       - "export MY_VAR=value"
       - "source /path/to/venv/bin/activate"

.. tip::
   Use YAML anchors to share common environment setup across multiple executors:
   
   .. code-block:: yaml
   
      common_env: &common_env
        - "module load python/3.11"
        - "export PYTHONPATH=/my/path:$PYTHONPATH"
      
      executor1:
        environment: *common_env
      
      executor2:
        environment: *common_env

Configuration Best Practices
-----------------------------

1. **Start Small**: Begin with short walltimes and small resource requests while testing
2. **Use Anchors**: Share common configuration blocks (like ``environment``) using YAML anchors
3. **Template Variables**: Use Jinja2 templates for endpoint UUIDs to keep configurations portable
4. **Resource Limits**: Set appropriate ``min_blocks`` and ``max_blocks`` to control scaling
5. **Test Locally**: Validate configurations with ``provider: "localhost"`` before using HPC resources
6. **Environment Modules**: Always include necessary module loads in the ``environment`` section
7. **MPI Variables**: Export MPI compiler variables (like ``$MPIF90``) in MPI executor environments

See Also
--------

- :doc:`quickstart` - Complete workflow example
- :doc:`endpoints` - Managing Globus Compute endpoints
- :doc:`api` - Python API reference
