# Instructions for running the mpas App

Edit `ush/user_config.yaml` to set the platform and experiment directory for your runs.

Also add any other customizations necessary to override the `default_config.yaml`.

```
cd ush
python experiment.py user_config.yaml &
```

Monitor runs with `squeue` and viewing logs in experiment directory.


