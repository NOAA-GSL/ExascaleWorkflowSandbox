# mpas_app

App for building, configuring, and running the MPAS forecast model.

# Steps

1. Configuring the Model
2. Building the Model
3. Running the Model

# 1. Instructions for configuring the model

`default_config.yaml` is the default configuration used to run the MPAS App. `default_config.yaml` is located in the `config` directory of the MPAS App.

`user_config.yaml` is used to update the default configuration. The `user_config.yaml` will be used to render the `default_config.yaml` provided by the user. The `experiment.py` script will use the configuration scripts to run the experiment. Both `user_config.yaml` and `experiment.py` are located in the `config` directory.

- Edit `user_config.yaml` to set the platform and experiment directory for running the forecast.

`resources.yaml` provides platform details and contains `environment` commands, allowing users to update the default `environment`, providing flexibility to use additional modules.

# 2. Instructions for building the model

# 3. Instructions for running the MPAS App

```
cd bin
python experiment.py user_config.yaml
```

Monitor runs with `squeue` and viewing logs in experiment directory.
