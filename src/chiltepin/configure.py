import os

import yaml
from parsl.channels import LocalChannel
from parsl.config import Config
from parsl.executors import FluxExecutor, HighThroughputExecutor, MPIExecutor
from parsl.launchers import SimpleLauncher
from parsl.providers import SlurmProvider


# Define function to parse yaml config
def parse_file(filename):
    # Open and parse the yaml config
    with open(filename, "r") as stream:
        try:
            yaml_config = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print("Invalid yaml configuration")
            raise (e)
    return yaml_config


def configure_flux_executor(name, config):

    # Setting FLUX_SSH is required on some systems
    os.environ["FLUX_SSH"] = "ssh"

    e = FluxExecutor(
        label=name,
        # Start Flux with srun and tell it how many cores per node to expect
        launch_cmd=f'srun --mpi=pmi2 --tasks-per-node=1 -c{config["cores per node"]} '
        + FluxExecutor.DEFAULT_LAUNCH_CMD,
        provider=SlurmProvider(
            channel=LocalChannel(),
            cores_per_node=config["cores per node"],
            nodes_per_block=config["nodes per block"],
            init_blocks=1,
            partition=config["partition"],
            account=config["account"],
            walltime="00:30:00",
            launcher=SimpleLauncher(),
            worker_init="""
            """,
        ),
    )
    return e


def configure_mpi_executor(name, config):

    e = MPIExecutor(
        label=name,
        mpi_launcher="srun",
        max_workers_per_block=config["max mpi apps"],
        provider=SlurmProvider(
            channel=LocalChannel(),
            exclusive=True,
            cores_per_node=config["cores per node"],
            nodes_per_block=config["nodes per block"],
            init_blocks=1,
            partition=config["partition"],
            account=config["account"],
            walltime="00:30:00",
            launcher=SimpleLauncher(),
            worker_init="""
            """,
        ),
    )
    return e


def configure_htex_executor(name, config):

    e = HighThroughputExecutor(
        label=name,
        cores_per_worker=1,
        max_workers_per_node=config["cores per node"],
        provider=SlurmProvider(
            channel=LocalChannel(),
            exclusive=False,
            cores_per_node=config["cores per node"],
            nodes_per_block=config["nodes per block"],
            init_blocks=1,
            min_blocks=1,
            partition=config["partition"],
            account=config["account"],
            walltime="00:30:00",
            launcher=SimpleLauncher(),
            worker_init="""
            """,
        ),
    )
    return e


def factory(yaml_config, platform):

    providers = yaml_config[platform]["resources"]
    executors = []

    # Make executors for mpi, service, and compute resources
    for provider, provider_config in providers.items():
        if provider == "mpi":
            executors.append(configure_mpi_executor(provider, provider_config))
        if provider == "service":
            executors.append(configure_htex_executor(provider, provider_config))
        if provider == "compute":
            executors.append(configure_htex_executor(provider, provider_config))

    resources = Config(executors=executors)
    environments = {}
    for platform, platform_config in yaml_config.items():
        environments[platform] = "\n".join(platform_config["environment"])

    return resources, environments
