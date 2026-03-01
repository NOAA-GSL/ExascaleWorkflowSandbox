Endpoint Management
===================

Chiltepin provides command-line tools for managing Globus Compute endpoint lifecycles. This page describes how to configure, start, stop, and manage endpoints.

Overview
--------

Globus Compute endpoints enable you to run tasks on remote compute resources. Chiltepin's CLI simplifies endpoint management by:

- Automatically configuring endpoints with appropriate templates
- Managing authentication flows
- Providing lifecycle management commands
- Tracking endpoint status

The ``chiltepin`` Command
-------------------------

All endpoint management is done through the ``chiltepin`` command-line interface.

.. code-block:: bash

   $ chiltepin --help
   usage: chiltepin [-h] {login,logout,endpoint} ...
   
   options:
     -h, --help            show this help message and exit
   
   chiltepin commands:
     {login,logout,endpoint}
                           Chiltepin commands
       login               login to the Chiltepin App
       logout              logout of the Chiltepin App
       endpoint            endpoint commands

Authentication
--------------

Before using Globus Compute endpoints, you must authenticate with Globus services.

Login
^^^^^

.. code-block:: bash

   $ chiltepin login

This will:

1. Open a browser window for Globus authentication
2. Prompt you to authorize the Chiltepin application
3. Save authentication tokens for future use

The login uses the default Chiltepin client ID. You can override this with environment variables:

.. code-block:: bash

   export GLOBUS_COMPUTE_CLIENT_ID="your-client-id"
   export GLOBUS_COMPUTE_CLIENT_SECRET="your-client-secret"  # Optional
   
   chiltepin login

.. note::
   Login credentials are cached, so you typically only need to login once per system.

Logout
^^^^^^

.. code-block:: bash

   $ chiltepin logout

This revokes all authentication tokens and clears cached credentials.

Endpoint Commands
-----------------

All endpoint operations use the ``chiltepin endpoint`` subcommand.

.. code-block:: bash

   $ chiltepin endpoint --help
   usage: chiltepin endpoint [-h] [-c CONFIG_DIR]
                            {configure,list,start,stop,delete} ...

Configure an Endpoint
^^^^^^^^^^^^^^^^^^^^^

Create and configure a new endpoint:

.. code-block:: bash

   $ chiltepin endpoint configure my-endpoint

This will:

1. Create a new endpoint configuration directory (``~/.globus_compute/my-endpoint/``)
2. Generate a default configuration with user endpoint template support
3. Set the endpoint display name
4. Enable debug logging
5. Capture the system PATH for the endpoint environment

**Custom Configuration Directory**

By default, endpoints are stored in ``~/.globus_compute/``. You can specify a custom location:

.. code-block:: bash

   $ chiltepin endpoint -c /path/to/config configure my-endpoint

**What Gets Created**

After configuration, you'll have:

.. code-block:: text

   ~/.globus_compute/my-endpoint/
   ├── config.yaml                      # Main endpoint configuration
   └── user_config_template.yaml.j2    # Jinja2 template for user configs

The ``config.yaml`` includes:

- Display name matching your endpoint name
- Debug mode enabled
- User endpoint configuration template path
- System PATH configuration

List Endpoints
^^^^^^^^^^^^^^

View all configured endpoints:

.. code-block:: bash

   $ chiltepin endpoint list

Output format:

.. code-block:: text

   endpoint-name    endpoint-uuid                         status
   my-endpoint      12345678-1234-1234-1234-123456789abc  Running
   test-endpoint    87654321-4321-4321-4321-cba987654321  Stopped

With custom configuration directory:

.. code-block:: bash

   $ chiltepin endpoint -c /path/to/config list

Start an Endpoint
^^^^^^^^^^^^^^^^^

Start a configured endpoint:

.. code-block:: bash

   $ chiltepin endpoint start my-endpoint

The endpoint will:

1. Register with Globus Compute services (first time only)
2. Start accepting tasks
3. Run in the background
4. Automatically scale resources based on task demand

**Starting with Custom Config**

.. code-block:: bash

   $ chiltepin endpoint -c /path/to/config start my-endpoint

**What Happens at Startup**

- Endpoint UUID is registered with Globus Compute (if first start)
- Background daemon process is started
- Endpoint begins polling for tasks
- User endpoint configurations are validated

.. tip::
   After starting an endpoint for the first time, note its UUID from ``chiltepin endpoint list``. You'll need this UUID to reference the endpoint in your Chiltepin configuration files.

Stop an Endpoint
^^^^^^^^^^^^^^^^

Stop a running endpoint:

.. code-block:: bash

   $ chiltepin endpoint stop my-endpoint

This will:

1. Stop accepting new tasks
2. Wait for running tasks to complete (graceful shutdown)
3. Terminate the endpoint daemon

.. code-block:: bash

   $ chiltepin endpoint -c /path/to/config stop my-endpoint

Delete an Endpoint
^^^^^^^^^^^^^^^^^^

Remove an endpoint configuration:

.. code-block:: bash

   $ chiltepin endpoint delete my-endpoint

This will:

1. Stop the endpoint (if running)
2. Delete the endpoint configuration directory
3. Remove all associated files

.. warning::
   This operation is permanent and cannot be undone. The endpoint UUID will be deregistered from Globus Compute services.

Endpoint Lifecycle
------------------

Typical Workflow
^^^^^^^^^^^^^^^^

1. **Configure** - Set up a new endpoint

   .. code-block:: bash
   
      chiltepin endpoint configure my-hpc-endpoint

2. **Start** - Launch the endpoint

   .. code-block:: bash
   
      chiltepin endpoint start my-hpc-endpoint

3. **Get UUID** - Retrieve the endpoint UUID

   .. code-block:: bash
   
      chiltepin endpoint list
      # Note the UUID for my-hpc-endpoint

4. **Use in Config** - Add to your Chiltepin YAML configuration

   .. code-block:: yaml
   
      my-executor:
        endpoint: "12345678-1234-1234-1234-123456789abc"
        mpi: True
        provider: "slurm"
        # ... additional options

5. **Submit Tasks** - Run your workflow

6. **Stop** - When finished (or let it auto-shutdown)

   .. code-block:: bash
   
      chiltepin endpoint stop my-hpc-endpoint

Endpoint Auto-Scaling
^^^^^^^^^^^^^^^^^^^^^

Globus Compute endpoints automatically scale based on task demand:

- **Idle Shutdown**: Endpoints automatically stop after extended idle periods
- **On-Demand Start**: Endpoints can be automatically restarted when new tasks arrive
- **Resource Scaling**: Blocks (job submissions) scale between ``min_blocks`` and ``max_blocks``

The endpoint configuration includes:

- ``idle_heartbeats_soft: 120`` - Shutdown after ~60 minutes of inactivity (at 30s/heartbeat)
- ``idle_heartbeats_hard: 5760`` - Force shutdown after ~48 hours even if tasks are stuck

User Endpoint Configuration
----------------------------

When you use a Globus Compute executor in your Chiltepin configuration, the executor options are passed to the endpoint's user configuration template (``user_config_template.yaml.j2``).

Template Variables
^^^^^^^^^^^^^^^^^^

Your configuration options become Jinja2 template variables:

**Chiltepin Config**:

.. code-block:: yaml

   my-executor:
     endpoint: "uuid-here"
     mpi: True
     max_mpi_apps: 4
     provider: "slurm"
     partition: "gpu"
     cores_per_node: 128
     nodes_per_block: 8

**Template Variables**:

.. code-block:: jinja

   {% if mpi %}
   max_workers_per_block: {{ max_mpi_apps }}
   {% endif %}
   
   partition: {{ partition }}

This allows each task submission to dynamically configure the endpoint's execution environment.

Advanced Configuration
^^^^^^^^^^^^^^^^^^^^^^

The user endpoint template (``~/.globus_compute/my-endpoint/user_config_template.yaml.j2``) can be customized for site-specific requirements:

- Modify provider configurations
- Add custom environment setup
- Define scheduler options
- Set resource limits

See the `Globus Compute documentation <https://globus-compute.readthedocs.io/>`_ for advanced endpoint configuration.

Troubleshooting
---------------

Check Endpoint Status
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   $ chiltepin endpoint list

If an endpoint shows as "Unknown", it may not be running or may have crashed.

View Endpoint Logs
^^^^^^^^^^^^^^^^^^

Logs are stored in the endpoint directory:

.. code-block:: bash

   $ ls -la ~/.globus_compute/my-endpoint/
   
   # View the main endpoint log
   $ tail -f ~/.globus_compute/my-endpoint/endpoint.log

Authentication Issues
^^^^^^^^^^^^^^^^^^^^^

If you encounter authentication errors:

.. code-block:: bash

   $ chiltepin logout
   $ chiltepin login

Endpoint Won't Start
^^^^^^^^^^^^^^^^^^^^

Common causes:

1. **Not logged in**: Run ``chiltepin login``
2. **Port conflicts**: Another endpoint may be using the same port
3. **Permission issues**: Check file permissions in ``~/.globus_compute/``
4. **Invalid configuration**: Review ``~/.globus_compute/my-endpoint/config.yaml``

Enable debug logging by ensuring ``debug: True`` in your endpoint config.

Tasks Not Running
^^^^^^^^^^^^^^^^^

Verify:

1. Endpoint is running: ``chiltepin endpoint list``
2. Correct endpoint UUID in your configuration
3. User configuration template is valid
4. Resource limits (walltime, nodes) are appropriate
5. Environment modules are available on the target system

Check the endpoint logs and the Parsl runinfo directory for detailed error messages.

Python API
----------

You can also manage endpoints programmatically:

.. code-block:: python

   import chiltepin.endpoint as endpoint
   
   # Login
   clients = endpoint.login()
   compute_client = clients["compute"]
   
   # Configure endpoint
   endpoint.configure("my-endpoint")
   
   # Start endpoint
   endpoint.start("my-endpoint")
   
   # List endpoints
   ep_info = endpoint.show()
   for name, props in ep_info.items():
       print(f"{name}: {props['id']}")
   
   # Stop endpoint
   endpoint.stop("my-endpoint")
   
   # Logout
   endpoint.logout()

See Also
--------

- :doc:`configuration` - Configuration file format
- :doc:`quickstart` - Complete workflow example
- :doc:`api` - Full Python API reference
