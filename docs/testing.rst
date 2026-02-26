Running Tests
=============

The Chiltepin test suite uses pytest and requires an editable installation of the 
package (achieved using the ``pip install -e .`` installation step).

Prerequisites
-------------

Before running tests, ensure you have:

1. Installed Chiltepin with test dependencies: ``pip install -e .[test]``
2. Authenticated with Globus Compute (for Globus Compute tests)

Globus Authentication
---------------------

The Globus Compute tests require authentication before running. Use the following 
command to authenticate:

.. code-block:: console

   $ globus-compute-endpoint login

This will open a web browser for you to complete the authentication flow.

Running Tests
-------------

Basic Test Execution
~~~~~~~~~~~~~~~~~~~~

To run the full test suite:

.. code-block:: console

   $ pytest --assert=plain --config=tests/configs/<platform>.yaml

Where ``<platform>`` is one of:

* ``docker`` - For the Docker container environment
* ``hera`` - For NOAA Hera HPC system
* ``hercules`` - For NOAA Hercules HPC system
* ``ursa`` - For NOAA Ursa HPC system

Verbose Output
~~~~~~~~~~~~~~

For more detailed information during testing:

.. code-block:: console

   $ pytest -s -vvv --assert=plain --config=tests/configs/<platform>.yaml

Running Specific Tests
~~~~~~~~~~~~~~~~~~~~~~

To run a specific test file:

.. code-block:: console

   $ pytest -vvv --config=tests/configs/docker.yaml tests/test_endpoint.py

To run a specific test function:

.. code-block:: console

   $ pytest -vvv --config=tests/configs/docker.yaml tests/test_endpoint.py::TestEndpointIntegration::test_configure

Coverage Reports
----------------

To run tests with coverage:

.. code-block:: console

   $ pytest --cov=src/chiltepin --cov-report=term --config=tests/configs/<platform>.yaml

This will display a coverage report showing which lines of code were executed during tests.

Test Organization
-----------------

The test suite is organized into several files:

* ``test_configure.py`` - Tests for configuration parsing and executor creation
* ``test_cli.py`` - Tests for command-line interface functionality
* ``test_tasks.py`` - Tests for task decorators and execution
* ``test_endpoint.py`` - Tests for Globus Compute endpoint management
* ``test_data.py`` - Tests for data handling utilities
* ``test_parsl_hello.py`` - Basic Parsl integration tests
* ``test_parsl_mpi.py`` - MPI-enabled Parsl tests
* ``test_globus_compute_hello.py`` - Basic Globus Compute tests
* ``test_globus_compute_mpi.py`` - MPI-enabled Globus Compute tests

Docker Container Testing
------------------------

When running tests in the Docker container, you may need to adjust the 
``cores_per_node`` setting in the configuration file to match the number of cores 
allocated to Docker on your system.

See :doc:`container` for more information on using the Docker environment.
