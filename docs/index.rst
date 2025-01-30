Chiltepin - Federated Workflows for Numerical Weather Prediction
================================================================

Chiltepin is a Python library for building and running numerical weather
prediction (NWP) workflows across federated high-performance computing (HPC)
resources. With Chiltepin, your workflows are Python programs that can execute
tasks seamlessly across diverse, distributed resources. You can use Chiltepin's
existing library of NWP tasks as bulding blocks, and/or create your own workflow
tasks using simple decorators that transform a simple function or method into a
workflow task.


Chiltepin uses `Parsl <https://parsl.readthedocs.io/en/stable/index.html>`_
for workflow automation and `Globus Compute <https://globus-compute.readthedocs.io/en/latest/>`_
for deploying workflows onto federated, remote, distributed resources.


Check out the :doc:`quickstart` section for further information, including
how to :ref:`install <installation>` the project.

.. note::

   This project is under active development.

Contents
++++++++

.. toctree::
   :maxdepth: 2

   quickstart
   api
