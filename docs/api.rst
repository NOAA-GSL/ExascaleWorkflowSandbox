API Reference guide
*******************

Core
========

.. autosummary::
    :toctree: stubs
    :nosignatures:

    chiltepin.tasks.bash_task
    chiltepin.tasks.python_task

Configuration
=============

.. autosummary::
    :toctree: stubs
    :nosignatures:

    chiltepin.configure.parse_file
    chiltepin.configure.load

Data
====

.. autosummary::
    :toctree: stubs
    :nosignatures:

    chiltepin.data.transfer
    chiltepin.data.delete
    chiltepin.data.retrieve_data

Endpoint
========

.. autosummary::
    :toctree: stubs
    :nosignatures:

    chiltepin.endpoint.get_chiltepin_apps
    chiltepin.endpoint.login
    chiltepin.endpoint.logout
    chiltepin.endpoint.configure
    chiltepin.endpoint.is_multi
    chiltepin.endpoint.list
    chiltepin.endpoint.is_running
    chiltepin.endpoint.start
    chiltepin.endpoint.stop
    chiltepin.endpoint.delete

Drivers
=======

.. autosummary::
    :toctree: stubs
    :nosignatures:

    chiltepin.drivers.metis.driver.Metis
    chiltepin.drivers.mpas.driver.MPAS
    chiltepin.drivers.mpas.limited_area.driver.LimitedArea
    chiltepin.drivers.wrf.driver.WRF
    chiltepin.drivers.wps.driver.WPS
    chiltepin.drivers.jedi.leadtime
    chiltepin.drivers.jedi.qg.driver.QG
