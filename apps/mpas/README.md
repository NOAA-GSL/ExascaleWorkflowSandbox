# mpas_app

App for building, configuring, and running the MPAS forecast model.

The App runs the workflow depicted below. As shown in the diagram, in addition to the execution of the
preprocessing and forecast steps, the workflow also downloads and builds the packages needed for those
steps.  This includes MPAS_Limited_Area, Metis, WPS (for ungrib), and MPAS. The app also downloads
and generates the required MPAS mesh files.  In this sense the App is self-contained and does not
rely on installations of gpmetis, ungrib, or MPAS.  However, the software stack
(such as [spack-stack](https://spack-stack.readthedocs.io/en/1.4.0/PreConfiguredSites.html#) required
for building those packages must be pre-installed for those builds to succeed.

![Diagram of MPAS App workflow](./assets/mpas_app_workflow.png)

# Steps

1. Configure the Workflow Steps
2. Run the Workflow

# Instructions for Configuring the workflow Steps

- `config/default_config.yaml` is the default configuration used to run the MPAS App.

- `config/user_config.yaml` is used to override the default configuration with select customizations.

    - Edit `user_config.yaml` to set the platform, experiment directory, and model resolution, for running the forecast.

- `resources.yaml` provides platform details and contains `environment` commands that load the software stack needed by the app.

# Instructions for running the MPAS App

Once `user_config.yaml` is updated with user customizations (e.g. experiment directory, platform, model resolution), run the App:

```
cd bin
python experiment.py ../config/user_config.yaml &
```

HINT: Use `&` to put the run command in the background to allow you to use the shell for monitoring workflow progress.

You can use `squeue` to monitor the workflow pilot jobs in which the workflow tasks run.

You can view workflow task logs in the experiment directory to monitor workflow progress and check for errors.
