import os

import yaml
from parsl.channels import LocalChannel
from parsl.config import Config
from parsl.executors import FluxExecutor, HighThroughputExecutor
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


def factory(yaml_config={}):

    # Set FLUX_SSH
    os.environ["FLUX_SSH"] = "ssh"

    provider_config = yaml_config["provider"]

    execs = []
    for pc in provider_config:
        if pc["type"] == "flux":
            e = FluxExecutor(
                label=pc["name"],
                # Start Flux with srun and tell it how many cores per node to expect
                launch_cmd=f'srun --mpi=pmi2 --tasks-per-node=1 -c{pc["cores per node"]} '
                + FluxExecutor.DEFAULT_LAUNCH_CMD,
                provider=SlurmProvider(
                    channel=LocalChannel(),
                    cores_per_node=pc["cores per node"],
                    nodes_per_block=pc["nodes per block"],
                    init_blocks=1,
                    partition=pc["partition"],
                    account=pc["account"],
                    walltime="08:00:00",
                    launcher=SimpleLauncher(),
                    worker_init="""
                    """,
                ),
            )
            execs.append(e)
        if pc["type"] == "htex":
            e = HighThroughputExecutor(
                label=pc["name"],
                # address=address_by_hostname(),
                max_workers=1,
                cores_per_worker=1,
                provider=SlurmProvider(
                    channel=LocalChannel(),
                    exclusive=False,
                    cores_per_node=pc["cores per node"],
                    nodes_per_block=pc["nodes per block"],
                    init_blocks=1,
                    partition=pc["partition"],
                    account=pc["account"],
                    walltime="02:10:00",
                    launcher=SimpleLauncher(),
                    worker_init="""
                    """,
                ),
            )
            execs.append(e)
    env_init = "\n".join(yaml_config["environment"])
    config = Config(executors=execs)
    return config, env_init
