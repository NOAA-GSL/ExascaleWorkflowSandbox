from parsl.config import Config
from parsl.channels import LocalChannel
from parsl.providers import SlurmProvider
from parsl.executors import FluxExecutor
from parsl.launchers import SimpleLauncher

import os

def config_factory(yaml_config={}):
    # Set FLUX_SSH
    os.environ["FLUX_SSH"] = "ssh"
    provider_config = yaml_config["provider"]
    cores_per_node = provider_config["cores per node"]
    partition = provider_config["partition"]
    account = provider_config["account"]

    env_init = "\n".join(yaml_config["environment"])

    # Update to import config for your machine
    config = Config(
        executors=[
            FluxExecutor(
                label="flux",
                # Start Flux with srun and tell it how many cores per node to expect
                launch_cmd=f'srun --mpi=pmi2 --tasks-per-node=1 -c{cores_per_node} ' + FluxExecutor.DEFAULT_LAUNCH_CMD,
                provider=SlurmProvider(
                    channel=LocalChannel(),
                    cores_per_node=cores_per_node,
                    nodes_per_block=3,
                    init_blocks=1,
                    partition=partition,
                    account=account,
                    walltime='00:10:00',
                    launcher=SimpleLauncher(),
                    worker_init='''
                    ''',
                ),
            )
        ],
    )

    return config, env_init
