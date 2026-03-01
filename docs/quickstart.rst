Quick Start
===========

This guide will help you get started with Chiltepin quickly.

Overview
--------

Chiltepin is a collection of tools for exploring and testing technologies for 
implementing exascale scientific workflows using Parsl and Globus Compute.

.. warning::

   This collection of resources is not intended for production use, and is for
   research purposes only.

Basic Usage
-----------

After installing Chiltepin (see :doc:`installation`), you can start using it by 
importing the modules you need:

.. code-block:: python

   import chiltepin.configure
   import chiltepin.tasks
   import chiltepin.endpoint

Configuration
-------------

Chiltepin uses YAML configuration files to define compute resources. Example 
configurations for various platforms can be found in the ``tests/configs/`` directory:

* ``docker.yaml`` - For Docker container environments
* ``hera.yaml`` - For NOAA Hera HPC system
* ``hercules.yaml`` - For NOAA Hercules HPC system
* ``ursa.yaml`` - For NOAA Ursa HPC system

You can load a configuration using:

.. code-block:: python

   import chiltepin.configure
   import parsl
   
   # Parse the Chiltepin configuration file
   config = chiltepin.configure.parse_file("tests/configs/docker.yaml")
   
   # Create a Parsl Config from the Chiltepin configuration
   parsl_config = chiltepin.configure.load(
       config,
       include=["service"],
       run_dir="./runinfo"
   )

   # Load the Parsl configuration to initialize executors
   parsl.load(parsl_config)

Working with Tasks
------------------

Chiltepin provides decorators for creating tasks that can run on remote executors:

.. code-block:: python

   from chiltepin.tasks import bash_task, python_task
   
   @python_task
   def hello():
       return "Hello from Chiltepin!"
   
   @bash_task
   def run_command():
       return "echo 'Running on remote executor'"

Next Steps
----------

* Learn how to run the test suite: :doc:`testing`
* Set up the Docker container environment: :doc:`container`
* Explore the full API documentation: :doc:`api`
