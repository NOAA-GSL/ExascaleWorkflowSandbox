# mpas_app

App for building, configuring, and running the MPAS forecast model.

# Steps

1. Configuring the Model
2. Building the Model
3. Running the Model

# Instructions for configuring the model

- `default_config.yaml` is the default configuration used to run the MPAS App. `default_config.yaml` is located in the `config` directory of the MPAS App.

- `user_config.yaml` is used to update the default configuration. The `user_config.yaml` will be used to render the `default_config.yaml` provided by the user. The `experiment.py` script will use the configuration scripts to run the experiment. Both `user_config.yaml` and `experiment.py` are located in the `config` directory.

    - Edit `user_config.yaml` to set the platform and experiment directory for running the forecast.

- `resources.yaml` provides platform details and contains `environment` commands, allowing users to update the default `environment`, providing flexibility to use additional modules.

# Instructions for building the model

`experiment.py` will contain the content to build and run the forecast. Building the forecast will cover several steps including:

1. Build the experiment directory using the supplied `default_config.yaml` and `user_config.yaml`.
2. Fetch the Metis, WPS, MPAS packages automatically and install packages into the experiment directory provided from the `user_config.yaml`. These packages are needed to run the experiment to generate the forecast.

# Instructions for running the MPAS App

## Running the ungrib component

### Generation of gribfiles. 
Run the ungrib pre-processing component of the MPAS forecast model. 
MPAS App supports generation of the mesh and grid files needed to run the forecast.

Retrieve initial conditions and lateral boundary conditions automatically from AWS.
1. Retrieve `create_ics` data task that creates the MPAS initial conditions.
2. Retrieve `creat_lbcs` data task that creates the MPAS lateral boundary conditions.

## Running the MPAS Init component

Create initial conditions and lateral boundary conditions.
1. Run `create_ics` data task to generate MPAS initial conditions.
2. Run `creat_lbcs` data task to generate MPAS lateral boundary conditions.

## Running the MPAS Atmosphere component
Run the `mpas_forecast` task.

```
cd bin
python experiment.py ../config/user_config.yaml
```

Monitor runs with `squeue` and viewing logs in experiment directory.
