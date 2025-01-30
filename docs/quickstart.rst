Quickstart
===========

Chiltepin is powered by `Parsl <https://parsl.readthedocs.io/en/stable/index.html>`_
and `Globus Compute <https://globus-compute.readthedocs.io/en/latest/>`_. It wraps
Parsl and Globus Compute capabilities to deliver federated numerical weather
prediction workflows to users. A review of the Parsl and Globus Compute quickstart
and tutorial documentation may be helpful to provide additional context and
understanding of important underlying concepts needed for constructing and running
federated workflows with Chiltepin.

.. _installation:

Installation
------------

Chiltepin is available on `PyPI <https://pypi.org/project/chiltepin/>`_ and can
be installed with pip.

Python version 3.9+ is required.

Installation using a Python venv
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The recommended method for installation is to use a Python venv virtual
environment.

.. code-block:: console

   $ python -m venv .chiltepin
   $ source .chiltepin/bin/activate
   $ python -m pip install chiltepin

Installation using a Conda environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Alternatively, a conda environment (anaconda3, miniconda3, miniforge, etc.) can
be used. Note: Chiltepin is not available directly from conda as a conda package.
It must still be installed with pip into the conda environment.

.. code-block:: console

   $ conda create -n "chiltepin" python=3.12
   $ source activate chiltepin
   $ python -m pip install chiltepin

Installation options
^^^^^^^^^^^^^^^^^^^^

There are install options available that are useful for Chiltepin developers.

* [test] installs dependencies required for running the Chiltepin test suite
* [docs] installs dependencies required for building the documentation

Add extra options to the install command as desired.

.. code-block:: console

   $ python -m pip install chiltepin[test]
   $ python -m pip install chiltepin[docs]
   $ python -m pip install chiltepin[test,docs]

Getting Started
---------------

To get started with Chiltepin you will need to understand the following:

#. Acquiring federated identity credentials
#. Managing workflow endpoint life cycles
#. Configuring local and remote resources for a workflow
#. Creating and executing workflow tasks

Tutorial
--------

A tutorial is in development
