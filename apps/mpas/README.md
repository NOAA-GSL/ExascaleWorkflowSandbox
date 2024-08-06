# mpas_app overview

App for building, configuring, and running the MPAS forecast model.

# Steps

1. Configuring the Model
2. Building the Model
3. Running the Model

# 1. Instructions for configuring the model

```
`default_config.yaml` is the default configuration used to run the MPAS App. `default_config.yaml` is located in the `bin` directory of the MPAS App. Users are able to change the default `envcmds`, alowing for flexibility to use additional modules. 
```

```
`user_config.yaml` is used to update the default configuration. The `user_config.yaml` will be used to render the `default_config.yaml` added in the information provided from the user. The `experiment.py` script will then use the configuration supplied by both scripts to run the experiment. Both `user_config.yaml` and `experiment.py` are located in the `bin` directory.

Edit `user_config.yaml` to set the platform and experiment directory for running the forecast.

```

# 2. Instructions for building the model

# 3. Instructions for running the MPAS AppEdit `ush/user_config.yaml` to set the platform and experiment directory for running theyour runs.

```
cd bin
python experiment.py user_config.yaml
```

Monitor runs with `squeue` and viewing logs in experiment directory.