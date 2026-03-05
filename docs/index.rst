Chiltepin Documentation
=======================

.. image:: https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/docker-slurm.yaml/badge.svg
   :target: https://github.com/NOAA-GSL/ExascaleWorkflowSandbox/actions/workflows/docker-slurm.yaml
   :alt: ExascaleSandboxTests

**Chiltepin** is a Python library for exploring federated workflow capabilities
using Parsl and Globus Compute. It provides tools and demonstrations for
implementing distributed scientific workflows on HPC systems.

.. warning::

   This project is for research and exploration purposes only. It is not
   intended for use in operational production environments.

Overview
--------

This repository is a collection of tools and demonstrations used for
implementing distributed exascale scientific workflows. The
project focuses on:

* **Workflow management** using Parsl
* **Federated distributed computing** with Globus Compute
* **HPC integration** of multiple on-prem and/or cloud-based systems
* **Container-based testing** with Docker and Slurm

Key Features
------------

* Configuration-based resource management for both HPC platforms and laptops
* Support for both MPI (HPC) and non-MPI (HTC) applications
* Globus Compute endpoint management utilities
* Task decorators for seamless integration of Parsl and Globus Compute
* Dynamic distributed task execution across heterogeneous resources
* Docker container environment for development and testing
* Comprehensive test suite with 100% coverage for core modules

Getting Started
---------------

.. toctree::
   :maxdepth: 2

   installation
   quickstart
   configuration
   endpoints
   testing
   container

API Reference
-------------

.. toctree::
   :maxdepth: 2

   api

Legal Notice
------------

This repository is a scientific product and is not official communication of
the National Oceanic and Atmospheric Administration, or the United States
Department of Commerce. All NOAA GitHub project code is provided on an 'as is'
basis and the user assumes responsibility for its use.
