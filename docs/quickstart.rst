Quickstart
===========

Chiltepin is powered by `Parsl <https://parsl.readthedocs.io/en/stable/index.html>`_
and `Globus Compute <https://globus-compute.readthedocs.io/en/latest/>`_. It wraps
Parsl and Globus Compute capabilities to deliver federated numerical weather
prediction workflows to users. A review of the Parsl and Globus Compute
quickstart and tutorial documentation at those links may be helpful to provide
additional context and understanding of important underlying concepts needed for
constructing and running federated workflows with Chiltepin.

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
#. Configuring local and remote resources
#. Creating and executing workflow tasks

Acquiring federated identity credentials
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Chiltepin uses `Globus <https://www.globus.org/>`_, and
`Globus Auth <https://www.globus.org/globus-auth-service/>`_ specifically,
for federated identity management. Globus is ubiquitous in the
high-performance computing (HPC) community and many users of HPC systems are
already familiar with the `Globus web interface <https://app.globus.org/>`_ which
provides them access using their institution's authentication method. Globus Auth
provides secure federated access and management of scoped credentials. It also
allows users to link identities from multiple institutions, enabling federated
access to resources distributed across administrative boundaries.

The Globus web application itself does not provide users with credentials for
all the scopes necessary for running a federated workflow. For this reason,
Chiltepin provides a command-line interface for managing credentials. The
``chiltepin login`` command prompts the user to log in to Globus and obtains
credentials for both remote computing and for transfering data across remote
endpoints. Credentials for both transfer and compute scopes are needed, so the
login flow for Chiltepin prompts users twice, once for the compute credentials
and once for the transfer credentials. Once logged in, users can access remote
compute endpoints and transfer data without being prompted until the credentials
expire days later.

.. code-block:: console

    $ chiltepin login

    Please authenticate with Globus here:
    -------------------------------------
    https://auth.globus.org/v2/oauth2/authorize?client_id=blah-blah-blah-blah-*****************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
    -------------------------------------

    Enter the resulting Authorization Code here: **********************

    Please authenticate with Globus here:
    -------------------------------------
    https://auth.globus.org/v2/oauth2/authorize?client_id=blah-blah-blah-blah-*****************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************************
    -------------------------------------

    Enter the resulting Authorization Code here: **********************
    $

Managing Workflow Endpoint Life cycles
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Remote workflow endpoints must be provisioned by the user before a workflow can
use them. Chiltepin uses
`Globus Compute Endpoints <https://globus-compute.readthedocs.io/en/latest/quickstart.html>`_
to provision remote resources for federated workflow execution. The compute
endpoints are managed using the ``chiltepin endpoint`` command. There are five
subcommands for configuring, starting, stopping, deleting, and listing endpoints.
Globus Compute credentials are required for managing compute endpoints so the
user must first be logged in (with ``chiltepin login``) in order for these
commands to work. A quick illustration of command usage:

.. code-block:: console

    $ chiltepin endpoint list
    No endpoints are configured

    $ chiltepin endpoint configure --multi foobar

    $ chiltepin endpoint list
    foobar None                                 Initialized

    $ chiltepin endpoint start foobar

    $ chiltepin endpoint list
    foobar 7cee4356-9843-41a3-a662-5c3d2b39b49e Running

    $ chiltepin endpoint stop foobar

    $ chiltepin endpoint list
    foobar 7cee4356-9843-41a3-a662-5c3d2b39b49e Stopped

    $ chiltepin endpoint delete foobar

    $ chiltepin endpoint list
    No endpoints are configured


Configuring local and remote resources
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Chiltepin can deploy workflow tasks to both local and remote resources. The local
and remote resources required by a particular workflow are configured with a
YAML file that describes their properties. The configuration for each resource
consists of two parts: a description of the resource's pool of nodes, and an
optional list of commands to set up the resource's execution environment. The
resource pools are described by their type. HTEX and MPI resource types specify
local resources for generic tasks and parallel MPI tasks, respectively.
GlobusComputeEngine and GlobusMPIEngine types specify remote resources
provisioned on remote compute endpoints for generic tasks and MPI tasks,
respectively. Descriptions of the local and remote resource pools include
items such as number of nodes, queue partitions, and account. The following
sample provides a quick introduction:

.. code-block:: yaml

    docker-env: &docker-env
      environment:
        - "source /usr/lmod/lmod/init/bash"
        - "module use /opt/spack-stack/envs/unified-env/install/modulefiles/Core"
        - "module load stack-gcc"
        - "module load stack-openmpi"
        - "module load stack-python"
        - "module load jedi-fv3-env"
        - "module unload py-attrs"
    local-mpi:
      engine: MPI
      cores per node: 8
      nodes per block: 3
      exclusive: True
      max mpi apps: 2
      partition: "slurmpar"
      account: ""
      <<: *docker-env
    local-service:
      engine: HTEX
      cores per node: 1
      nodes per block: 1
      exclusive: False
      partition: "slurmpar"
      account: ""
      <<: *docker-env
    remote-mpi:
      engine: GlobusMPIEngine
      endpoint id: "7cee4356-9843-41a3-a662-5c3d2b39b49e"
      cores per node: 8
      nodes per block: 3
      exclusive: True
      max mpi apps: 2
      partition: "slurmpar"
      account: ""
      <<: *docker-env
    remote-service:
      engine: GlobusComputeEngine
      endpoint id: "7cee4356-9843-41a3-a662-5c3d2b39b49e"
      cores per node: 1
      nodes per block: 1
      exclusive: False
      partition: "slurmpar"
      account: ""
      <<: *docker-env

When a workflow's resource configuration is loaded, a context is created for
execution of workflow tasks on those resources. Resources are shutdown when
the context is closed.  For example:

.. code-block:: python

    # Parse the configuration for the chosen platform
    import chitepin.configure

    # Read the configuration
    resource_config = chiltepin.configure.parse_file("config.yaml")

    # Load the resource configuration
    resources = chiltepin.configure.load(
        client=compute_client,
    )

    # Run the tests with the loaded resources
    with parsl.load(resources):
        yield


Creating and executing workflow tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Chiltepin tasks are defined using the ``@bash_task``, ``@python_task``, and
``@join_task`` decorators.  The decorators can be applied to functions and
class methods. Under the hood, these decorators create and return the
corresponding Parsl ``bash_app``, ``python_app``, or ``join_app``. Chiltepin's
decorators add two capabilities to Parsl's native apps that give Chiltepin
workflow users and developers more flexibility:

    #. They allow use of ``self`` when defining a task.
    #. They allow the destination executor to be chosen at call time rather than
       at parse time.

Otherwise, Chiltepin tasks behave the same as their native
`Parsl app <https://parsl.readthedocs.io/en/stable/userguide/apps/index.html>`_
counterparts. The main restriction of Chiltepin tasks is that they be
serializable. A consequence of this is that they must be self-contained and not
have dependencies external to the function or method. A review of the Parsl app
documentation at the aforementioned link is highly recommended.

When calling a Chiltepin task, a list of resources must be supplied to specify
where the task is allowed to execute.  Calling a task is a non-blocking operation
that immediately returns a future representing the eventual result of the task.
Execution of the workflow program can continue while Parsl acquires the target
resourcesm, schedules the task for execution, and captures its results, behind
the scenes.

A simple example:

.. code-block:: python

    @python_task
    def hello():
        return "Hello"

    future = hello(executor=["gc-service"])
    assert future.result() == "Hello"

The ``@bash_task`` also capture ``stdout`` and ``stderr`` of the bash script
that embodies the task's implementation.

A simple example:

.. code-block:: python

    @bash_task
    def hello():
        return """
	echo "hello"
	exit 0
	"""

    future = hello(
        executor=["gc-service"],
        stdout="/path/to/stdout",)
        stdout="/path/to/stderr",)
    assert future.result().return_code == 0


Tutorial
--------

A tutorial is in development
