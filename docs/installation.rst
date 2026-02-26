Installation
============

This software can be installed on Linux systems. macOS is not currently supported,
but can be used on Macs via the Docker container (see :doc:`container`).

Prerequisites
-------------

* Python 3.10 or higher
* Linux operating system (or Docker for Mac/Windows)

Using Python venv (Recommended)
--------------------------------

The recommended method for installation is to use a Python virtual environment:

.. code-block:: console

   $ python -m venv .chiltepin
   $ source .chiltepin/bin/activate
   $ pip install -e .[test]

.. note::

   The ``[test]`` option ensures that dependencies required for running the tests are installed.

Using Conda
-----------

Alternatively, you can use a conda environment (anaconda3, miniconda3, miniforge, etc.):

.. code-block:: console

   $ conda create -n "chiltepin" python=3.10
   $ conda activate chiltepin
   $ pip install -e .[test]

Activating the Environment
---------------------------

Once installed, Chiltepin can be used simply by activating the environment using
the command appropriate for your environment type:

**For venv:**

.. code-block:: console

   $ source .chiltepin/bin/activate

**For conda:**

.. code-block:: console

   $ conda activate chiltepin

Dependencies
------------

Chiltepin has the following core dependencies:

* ``globus-compute-sdk`` (4.5.0)
* ``globus-compute-endpoint`` (4.5.0)
* ``parsl`` (>=2026.1.5)

These will be automatically installed when you install Chiltepin.
