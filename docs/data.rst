Data Transfer and Management
============================

Chiltepin provides specialized tasks for transferring and deleting data between Globus
Transfer endpoints. These tasks integrate seamlessly with Chiltepin workflows, allowing
you to stage data, process it, and clean up afterward.

.. important::
   **Transfer Endpoints vs Compute Endpoints**: Globus has two types of endpoints:
   
   - **Transfer Endpoints**: Used for moving and managing files (documented here)
   - **Compute Endpoints**: Used for executing tasks (see :doc:`endpoints`)
   
   These are configured and managed separately through the Globus service.

Overview
--------

The data module provides two Chiltepin tasks for workflow data management:

- **transfer_task**: Transfer files/directories between Globus Transfer endpoints
- **delete_task**: Delete files/directories from Globus Transfer endpoints

These are standard Chiltepin tasks that return futures. You can create dependencies by:

- Using the ``inputs`` parameter to pass a list of futures (non-blocking)
- Passing futures as function arguments (when the task signature supports it)
- Calling ``.result()`` to wait synchronously (blocking)

Data Transfer Task
------------------

The ``transfer_task`` function transfers data between two Globus Transfer endpoints.

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   from chiltepin.data import transfer_task
   
   # Transfer a single file
   transfer_future = transfer_task(
       src_ep="my-laptop",
       dst_ep="hpc-scratch",
       src_path="/Users/me/data/input.dat",
       dst_path="/scratch/project/input.dat",
       executor=["local"]
   )
   
   # Wait for transfer to complete
   success = transfer_future.result()
   if success:
       print("Transfer completed successfully")

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Parameter
     - Type
     - Default
     - Description
   * - ``src_ep``
     - string
     - **Required**
     - Source Transfer endpoint name or UUID
   * - ``dst_ep``
     - string
     - **Required**
     - Destination Transfer endpoint name or UUID
   * - ``src_path``
     - string
     - **Required**
     - Path to file/directory on source Transfer endpoint
   * - ``dst_path``
     - string
     - **Required**
     - Path to file/directory on destination Transfer endpoint
   * - ``timeout``
     - integer
     - ``3600``
     - Seconds to wait for transfer completion
   * - ``polling_interval``
     - integer
     - ``30``
     - Seconds between status checks
   * - ``client``
     - TransferClient
     - ``None``
     - Globus TransferClient (auto-created if None)
   * - ``recursive``
     - boolean
     - ``False``
     - Transfer directories recursively
   * - ``executor``
     - string
     - **Required**
     - Resource name for running the transfer task (must have internet access)

Recursive Transfer
^^^^^^^^^^^^^^^^^^

Transfer entire directories recursively:

.. code-block:: python

   # Transfer a directory and all its contents
   transfer_future = transfer_task(
       src_ep="my-laptop",
       dst_ep="hpc-scratch",
       src_path="/Users/me/project/data/",
       dst_path="/scratch/project/data/",
       recursive=True,
       executor=["local"]
   )

Endpoint Names vs UUIDs
^^^^^^^^^^^^^^^^^^^^^^^

You can specify endpoints by their display name or UUID:

.. code-block:: python

   # Using display names
   transfer_task(
       src_ep="My Laptop",
       dst_ep="HPC Scratch Space",
       ...
   )
   
   # Using UUIDs
   transfer_task(
       src_ep="12345678-1234-1234-1234-123456789abc",
       dst_ep="87654321-4321-4321-4321-cba987654321",
       ...
   )

.. tip::
   UUIDs are more reliable than display names, which can change. Find your endpoint
   UUIDs at `app.globus.org <https://app.globus.org/file-manager>`_.

Data Deletion Task
------------------

The ``delete_task`` function removes files or directories from a Globus Transfer endpoint.

Basic Usage
^^^^^^^^^^^

.. code-block:: python

   from chiltepin.data import delete_task
   
   # Delete a single file
   delete_future = delete_task(
       src_ep="hpc-scratch",
       src_path="/scratch/project/temp.dat",
       executor=["local"]
   )
   
   # Wait for deletion to complete
   success = delete_future.result()
   if success:
       print("File deleted successfully")

Parameters
^^^^^^^^^^

.. list-table::
   :header-rows: 1
   :widths: 20 15 15 50

   * - Parameter
     - Type
     - Default
     - Description
   * - ``src_ep``
     - string
     - **Required**
     - Transfer endpoint name or UUID where data will be deleted
   * - ``src_path``
     - string
     - **Required**
     - Path to file/directory to delete
   * - ``timeout``
     - integer
     - ``3600``
     - Seconds to wait for deletion completion
   * - ``polling_interval``
     - integer
     - ``30``
     - Seconds between status checks
   * - ``client``
     - TransferClient
     - ``None``
     - Globus TransferClient (auto-created if None)
   * - ``recursive``
     - boolean
     - ``False``
     - Delete directories recursively
   * - ``executor``
     - string
     - **Required**
     - Resource name for running the deletion task (must have internet access)

Recursive Deletion
^^^^^^^^^^^^^^^^^^

Delete entire directories:

.. code-block:: python

   # Delete a directory and all its contents
   delete_future = delete_task(
       src_ep="hpc-scratch",
       src_path="/scratch/project/temp_data/",
       recursive=True,
       executor=["local"]
   )

.. warning::
   Recursive deletion is permanent and cannot be undone. Use with caution.

Workflow Integration
--------------------

Transfer and deletion tasks integrate seamlessly with Chiltepin workflows using the
``inputs`` parameter for non-blocking dependencies.

Stage, Process, Cleanup Pattern
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A common pattern is to stage data, process it, then clean up:

.. code-block:: python

   from chiltepin import workflow
   from chiltepin.tasks import python_task
   from chiltepin.data import transfer_task, delete_task
   
   @python_task
   def analyze_data(input_path):
       # Process the data file
       import pandas as pd
       df = pd.read_csv(input_path)
       result = df.mean().to_dict()
       return result

   # Load configuration and start workflow
   with workflow("config.yaml"):
       # Stage data to compute resource
       stage_in = transfer_task(
           src_ep="my-laptop",
           dst_ep="hpc-scratch",
           src_path="/Users/me/data/dataset.csv",
           dst_path="/scratch/project/dataset.csv",
           executor=["local"]
       )
       
       # Process the staged data (waits for transfer via inputs)
       analysis = analyze_data(
           "/scratch/project/dataset.csv",
           executor=["compute"],
           inputs=[stage_in]  # Non-blocking dependency
       )
       
       # Clean up staged data (waits for processing via inputs)
       cleanup = delete_task(
           src_ep="hpc-scratch",
           src_path="/scratch/project/dataset.csv",
           executor=["local"],
           inputs=[analysis]  # Non-blocking dependency
       )
       
       # Get results (blocks until analysis completes)
       results = analysis.result()
       print(f"Analysis results: {results}")

       # Ensure cleanup completes before exiting
       cleanup.result()

Multiple File Transfers
^^^^^^^^^^^^^^^^^^^^^^^^

Transfer multiple files in parallel:

.. code-block:: python

   from chiltepin.data import transfer_task
   
   # Transfer multiple input files in parallel
   files = ["sim1.dat", "sim2.dat", "sim3.dat"]
   
   transfers = []
   for filename in files:
       future = transfer_task(
           src_ep="my-laptop",
           dst_ep="hpc-scratch",
           src_path=f"/Users/me/data/{filename}",
           dst_path=f"/scratch/project/{filename}",
           executor=["local"]
       )
       transfers.append(future)

   # Wait for all transfers to complete
   for t in transfers:
       assert t.result(), "Transfer failed"

Waiting for Multiple Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run a transfer or deletion after multiple tasks complete, pass them via the
``inputs`` parameter:

.. code-block:: python

   from chiltepin.data import transfer_task, delete_task
   from chiltepin.tasks import python_task
   
   @python_task
   def generate_config():
       # Generate config file
       with open("/scratch/config.json", "w") as f:
           f.write('{"param": 1}')
       return True

   @python_task
   def generate_input():
       # Generate input file
       with open("/scratch/input.dat", "w") as f:
           f.write("data")
       return True

   # Generate files in parallel
   config_ready = generate_config(executor=["compute"])
   input_ready = generate_input(executor=["compute"])

   # Wait for both files before transferring (non-blocking dependency)
   transfer = transfer_task(
       src_ep="hpc-scratch",
       dst_ep="my-laptop",
       src_path="/scratch/",
       dst_path="/results/",
       recursive=True,
       executor=["local"],
       inputs=[config_ready, input_ready]  # Multiple dependencies
   )

   transfer.result()  # Wait for transfer

Data Pipeline with Transfers
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Build complete data pipelines using the ``inputs`` parameter for non-blocking
dependencies:

.. code-block:: python

   @python_task
   def preprocess(input_path, output_path):
       # Preprocessing step
       import pandas as pd
       df = pd.read_csv(input_path)
       df_clean = df.dropna()
       df_clean.to_csv(output_path, index=False)
       return output_path

   @python_task  
   def analyze(clean_data_path):
       # Analysis step
       import pandas as pd
       df = pd.read_csv(clean_data_path)
       return df.describe().to_dict()

   # Stage raw data
   stage_raw = transfer_task(
       src_ep="my-laptop",
       dst_ep="hpc-scratch",
       src_path="/data/raw.csv",
       dst_path="/scratch/raw.csv",
       executor=["local"]
   )

   # Preprocess (waits for transfer via inputs)
   preprocess_future = preprocess(
       "/scratch/raw.csv",
       "/scratch/clean.csv",
       executor=["compute"],
       inputs=[stage_raw]  # Wait for transfer non-blocking
   )

   # Analyze (waits for preprocess completing and passing output path)
   analysis_future = analyze(
       preprocess_future,  # Parsl waits for this future and passes the output path
       executor=["compute"]
   )

   # Stage results back (waits for analysis via inputs)
   stage_out = transfer_task(
       src_ep="hpc-scratch",
       dst_ep="my-laptop",
       src_path="/scratch/clean.csv",
       dst_path="/data/cleaned_output.csv",
       executor=["local"],
       inputs=[analysis_future]  # Wait for analysis non-blocking
   )

   # Cleanup remote files (waits for stage_out via inputs)
   cleanup = delete_task(
       src_ep="hpc-scratch",
       src_path="/scratch/",
       recursive=True,
       executor=["local"],
       inputs=[stage_out]  # Wait for stage out non-blocking
   )

   # Get results when needed
   results = analysis_future.result()
   print(f"Analysis results: {results}")

   # Ensure cleanup completes before exiting
   cleanup.result()

Authentication
--------------

Data transfer tasks require Globus authentication. Use the Chiltepin login command:

.. code-block:: bash

   $ chiltepin login

This authenticates you with Globus and grants the necessary permissions for data
transfers. The authentication persists across workflow runs until you log out.

.. note::
   You only need to authenticate once. The credentials are cached and reused for
   subsequent transfers.

Setting Up Data Endpoints
--------------------------

To use data transfer tasks, you need access to Globus Transfer endpoints:

1. **Personal Endpoints**: Install Globus Connect Personal on your laptop/workstation
   (`globus.org/globus-connect-personal <https://www.globus.org/globus-connect-personal>`_)

2. **Institutional Endpoints**: Many HPC centers provide pre-configured Globus endpoints.
   Check with your institution's documentation.

3. **Guest Collections**: Create shareable collections for specific directories

Visit the `Globus File Manager <https://app.globus.org/file-manager>`_ to view and
manage your endpoints.

Best Practices
--------------

1. **Use Descriptive Endpoint Names**: Clear names make workflows easier to understand
   and maintain.

2. **Check Transfer Success**: Always check the result of transfer/delete tasks:

   .. code-block:: python

      success = transfer_future.result()
      assert success, "Transfer failed"

3. **Handle Permissions**: Ensure you have read permissions on source endpoints and
   write permissions on destination endpoints.

4. **Set Appropriate Timeouts**: Large transfers may need longer timeouts. The default
   is 1 hour (3600 seconds).

5. **Create Dependencies Properly**: Use the ``inputs`` parameter to create non-blocking
   dependencies between tasks. Reserve ``.result()`` for when you actually need the data
   or must wait synchronously.

6. **Cleanup Staged Data**: Always delete temporary staged data to avoid filling up
   scratch space.

7. **Test Endpoints First**: Verify endpoints are set up correctly by doing a manual
   transfer through the Globus web interface before automating.

8. **Use Absolute Paths**: Always use absolute paths for both source and destination
   to avoid ambiguity.

Troubleshooting
---------------

Transfer Not Starting
^^^^^^^^^^^^^^^^^^^^^

- Verify you've authenticated: ``chiltepin login``
- Check endpoint names/UUIDs are correct
- Ensure both endpoints are activated (visit Globus File Manager)

Permission Denied
^^^^^^^^^^^^^^^^^

- Verify you have read permissions on the source endpoint
- Verify you have write permissions on the destination endpoint
- Some endpoints require explicit activation in the Globus web interface

Transfer Timing Out
^^^^^^^^^^^^^^^^^^^

- Increase the ``timeout`` parameter for large transfers
- Check network connectivity between endpoints
- Verify endpoints are online and not in maintenance mode

Endpoint Not Found
^^^^^^^^^^^^^^^^^^

- Check endpoint name spelling (case-sensitive)
- Try using the endpoint UUID instead of display name
- Verify the endpoint is visible in your Globus File Manager

See Also
--------

- :doc:`tasks` - General task documentation
- :doc:`endpoints` - Globus Compute endpoints for task execution
- :doc:`api` - Full API reference for the data module
- `Globus Documentation <https://docs.globus.org/>`_ - Official Globus guides

