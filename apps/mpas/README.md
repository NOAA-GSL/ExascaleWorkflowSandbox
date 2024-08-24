# mpas_app

App for building, configuring, and running the MPAS forecast model.

The App runs the workflow depicted below. As shown in the diagram, in addition to the execution of the
preprocessing and forecast steps, the workflow also downloads and builds the packages needed for those
steps.  This includes MPAS_Limited_Area, Metis, WPS (for ungrib), and MPAS. The app also downloads
and generates the required MPAS mesh files.  In this sense the App is self-contained and does not
rely on installations of gpmetis, ungrib, or MPAS.  However, the software stack
(such as [spack-stack](https://spack-stack.readthedocs.io/en/1.4.0/PreConfiguredSites.html#)) required
for building those packages must be pre-installed for those builds to succeed.

![Diagram of MPAS App workflow](./assets/mpas_app_workflow.png)

# Steps

1. Configure the Workflow Steps
2. Run the Workflow

# Instructions for Configuring the workflow Steps

- `config/default_config.yaml` is the default configuration used to run the MPAS App.

- `config/user_config.yaml` is used to override the default configuration with select customizations.

    - Edit `user_config.yaml` to set the platform, experiment directory, and model resolution for running the forecast.

- `resources.yaml` provides platform details and contains `environment` commands that load the software stack needed by the app.

# Instructions for running the MPAS App

Once `user_config.yaml` is updated with user customizations (e.g. experiment directory, platform, model resolution) run the App:

```
cd bin
python experiment.py ../config/user_config.yaml &
```

HINT: Use `&` to put the run command in the background to allow you to use the shell for monitoring workflow progress.

You can use `squeue` to monitor the workflow pilot jobs in which the workflow tasks run.

You can view workflow task logs in the experiment directory to monitor workflow progress and check for errors.

# Overview of workflow steps

This gives a brief description of each step of the MPAS App workflow

## Install MPAS_Limited_Area

This task installs the [MPAS-Limited-Area](https://github.com/MPAS-Dev/MPAS-Limited-Area) application into the experiment directory.
This application is later used to generate a CONUS mesh file from the global `static.nc` and `graph.info` files.

Output logs for this task are written to: `install_limited_area.[out | err]`

## Install Metis

This task installs the [Metis](https://github.com/KarypisLab/METIS) package which provides the `gpmetis` utility.  The `gpmetis`
utility is later used to partition the MPAS mesh files for each MPI domain decomposition to be used by the workflow.  The MPAS
Init and MPAS Atmosphere tasks each use a given number of MPI ranks at runtime.  The `gpmetis` utility is used to create a
partitioned mesh file corresponding to the total number of MPI ranks needed for each of those steps.

Output logs for this task are written to: `install_metis.[out | err]`

## Install WPS

This task installs a minimal build of the [WRF Preprocessing System (WPS)](https://github.com/wrf-model/WPS). This package
provides the `ungrib` utility which is used in the first preprocessing step to prepare initial and boundary conditions for
use by the MPAS initialization.

***NOTE:*** This task does not build all WPS executables because only `ungrib` is needed for the
MPAS App.

Output logs for this task are written to: `install_wps.[out | err]`

## Install MPAS

This task installs the [MPAS Model](https://github.com/MPAS-Dev/MPAS-Model).  This provides the `init_atmosphere_model` and
`atmosphere_model` executables that are later used to initialize MPAS and to run the MPAS forecast.

Output logs for this task are written to: `install_mpas.[out | err]`

## Fetch ICS Data

This task fetches the raw grib input data that provide the initial conditions for the forecast that is run by the MPAS App.

Output logs for this task are written to: `get_ics_[YYYYMMDDHHMM].[out | err]`

## Fetch LBCS Data

This task fetches the raw grib input data that provide the lateral boundary conditions for the forecast that is run by the
MPAS App.

Output logs for this task are written to: `get_lbcs_[YYYYMMDDHHMM].[out | err]`

## Generate CONUS Mesh

This task downloads the global mesh data from [here](https://mpas-dev.github.io/atmosphere/atmosphere_meshes.html) that
corresponds to the requested horizontal resolution.  It then uses the `create_region` utility from MPAS-Limited-Area
to generate the CONUS mesh data from the global mesh.

Output logs for this task are written to: `create_region.[out | err]`

## Create Mesh Partitions

This task runs the `gpmetis` utility provided by the Metis install to create partitioned CONUS mesh files for use by the
MPAS model executables. One partitioned mesh file is needed for each number of ranks used by MPI for those executables.

Output logs for this task are written to: `gpmetis_[RANKS].[out | err]`

## Ungrib

This task runs the `ungrib` utility provided by the WPS installation.  The `ungrib` utility reads the grib files that
were downloaded for the initial conditions and lateral boundary conditions and produces output for use by the MPAS model
initialization code.

Output logs for this task are written to: `ungrib_[YYYYMMDDHHMM].[out | err]`

## MPAS Init ICS

This task runs the `init_atmosphere_model` executable provided by the MPAS install to process the initial condition file
provided by `ungrib`.  This generates the initial conditions for the forecast step.

Output logs for this task are written to: `mpas_init_ics_[YYYYMMDDHHMM].[out | err]`

## MPAS Init LBCS

This task runs the `init_atmosphere_model` executable provided by the MPAS install to process the lateral boundary
condition files provided by `ungrib`.  This generates the lateral boundary conditions for the forecast step.

Output logs for this task are written to: `mpas_init_lbcs_[YYYYMMDDHHMM].[out | err]`

## MPAS Atmosphere

This task runs the `atmosphere_model` executable provided by the MPAS install to run the requested forecast.

Output logs for this task are written to: `mpas_forecast_[YYYYMMDDHHMM].[out | err]`
