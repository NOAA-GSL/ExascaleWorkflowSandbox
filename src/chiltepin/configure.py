from typing import Any, Dict, List, Optional

import yaml
from globus_compute_sdk import Client, Executor
from parsl.config import Config
from parsl.executors import GlobusComputeExecutor, HighThroughputExecutor, MPIExecutor
from parsl.launchers import SimpleLauncher, SrunLauncher
from parsl.providers import LocalProvider, SlurmProvider

from dataclasses import dataclass, field

@dataclass(frozen=True)
class Default:

    MPI: bool = False
    MAX_MPI_APPS: int = 1
    MAX_WORKERS_PER_NODE: int = 1
    CORES_PER_WORKER: int = 1
    CORES_PER_NODE: int = 1
    NODES_PER_BLOCK: int = 1
    INIT_BLOCKS: int = 0
    MIN_BLOCKS: int = 0
    MAX_BLOCKS: int = 1
    EXCLUSIVE: bool = True
    PARTITION: str = ""
    ACCOUNT: str = ""
    WALLTIME: str = "00:10:00"
    #ENVIRONMENT: List[str] = []
    ENVIRONMENT: List[str] = field(default_factory=list)


def parse_file(filename: str) -> Dict[str, Any]:
    """Parse a YAML resource comfiguration file and return its contents as a dict


    Parameters
    ----------

    filename: str
        Name of configuration file to parse

    Returns
    -------

    Dict[str, Any]
    """
    # Open and parse the yaml config
    with open(filename, "r") as stream:
        try:
            yaml_config = yaml.safe_load(stream)
        except yaml.YAMLError as e:
            print("Invalid yaml configuration")
            raise (e)
    return yaml_config


def make_htex_executor(name: str, config: Dict[str, Any]) -> HighThroughputExecutor:
    """Construct a HighThroughputExecutor from the input configuration


    Parameters
    ----------

    name: str
        A label that will be assigned to the returned HighThroughputExecutor
        for naming purposes

    config: Dict[str, Any]
        YAML configuration block that contains the following configuration options:

        Option key                Defaulit value
        "cores per node":         1
        "cores per worker":       1
        "max workers per node":   value of "cores per node"
        "nodes per block":        1
        "init blocks":            0
        "min blocks":             0
        "max blocks":             1
        "exclusive":              True
        "partition":              None
        "account":                None
        "walltime":               1:00:00
        "environment":            []

    Returns
    -------

    HighThroughputExecutor
    """
    e = HighThroughputExecutor(
        label=name,
        cores_per_worker=config.get("cores per worker", Default().CORES_PER_WORKER),
        max_workers_per_node=config.get("max workers per node", Default().MAX_WORKERS_PER_NODE),
        provider=SlurmProvider(
            cores_per_node=config.get("cores per node", Default().CORES_PER_NODE),
            nodes_per_block=config.get("nodes per block", Default().NODES_PER_BLOCK),
            init_blocks=config.get("init blocks", Default().INIT_BLOCKS),
            min_blocks=config.get("min blocks", Default().MIN_BLOCKS),
            max_blocks=config.get("max blocks", Default().MAX_BLOCKS),
            exclusive=config.get("exclusive", Default().EXCLUSIVE),
            partition=config.get("partition", Default().PARTITION),
            account=config.get("account", Default().ACCOUNT),
            walltime=config.get("walltime", Default().WALLTIME),
            worker_init="\n".join(config.get("environment", Default().ENVIRONMENT)),
            #launcher=SimpleLauncher(),
            launcher=SrunLauncher(),
        ),
    )
    return e


def make_mpi_executor(name: str, config: Dict[str, Any]) -> MPIExecutor:
    """Construct a MPIExecutor from the input configuration


    Parameters
    ----------

    name: str
        A label that will be assigned to the returned MPIExecutor
        for naming purposes

    config: Dict[str, Any]
        YAML configuration block that contains the following configuration options:

        Option key                Defaulit value
        "max mpi apps":           1
        "cores per node":         1
        "nodes per block":        1
        "init blocks":            0
        "min blocks":             0
        "max blocks":             1
        "exclusive":              True
        "partition":              None
        "account":                None
        "walltime":               1:00:00
        "environment":            []

    Returns
    -------

    MPIExecutor
    """
    e = MPIExecutor(
        label=name,
        mpi_launcher="srun",
        max_workers_per_block=config.get("max mpi apps", Default().MAX_MPI_APPS),
        provider=SlurmProvider(
            #cores_per_node=config.get("cores per node", Default().CORES_PER_NODE),
            nodes_per_block=config.get("nodes per block", Default().NODES_PER_BLOCK),
            init_blocks=config.get("init blocks", Default().INIT_BLOCKS),
            min_blocks=config.get("min blocks", Default().MIN_BLOCKS),
            max_blocks=config.get("max blocks", Default().MAX_BLOCKS),
            exclusive=config.get("exclusive", Default().EXCLUSIVE),
            partition=config.get("partition", Default().PARTITION),
            account=config.get("account", Default().ACCOUNT),
            walltime=config.get("walltime", Default().WALLTIME),
            worker_init="\n".join(config.get("environment", Default().ENVIRONMENT)),
            launcher=SimpleLauncher(),
        ),
    )
    return e


def make_globus_compute_executor(
    name: str, config: Dict[str, Any], client: Optional[Client] = None
) -> GlobusComputeExecutor:
    """Construct a GlobusComputeExecutor from the input configuration


    Parameters
    ----------

    name: str
        A label that will be assigned to the returned GlobusComputeExecutor
        for naming purposes

    config: Dict[str, Any]
        YAML configuration block that contains the following configuration options:

        Option key                Default value
        "endpoint id":            No default, this option is required

        For multi-user endpoints, the following additional options are recognized:

        Option key                Defaulit value
        "engine":                 GlobusComputeEngine
        "max mpi apps":           1
        "cores per node":         1
        "nodes per block":        1
        "init blocks":            0
        "min blocks":             0
        "max blocks":             1
        "exclusive":              True
        "partition":              None
        "account":                None
        "walltime":               1:00:00
        "environment":            []

    client: Client | None
        The Globus Compute client to use for instantiating the GlobusComputeExecutor.
        If not specified, Globus Compute will instantiate and use a default client.

    Returns
    -------

    GlobusComputeExecutor
    """
    e = GlobusComputeExecutor(
        label=name,
        executor=Executor(
            endpoint_id=config["endpoint"],
            client=client,
            user_endpoint_config={
                "mpi": config.get("mpi", Default().MPI),
                "max_mpi_apps": config.get("max mpi apps", Default().MAX_MPI_APPS),
                "cores_per_node": config.get("cores per node", Default().CORES_PER_NODE),
                "nodes_per_block": config.get("nodes per block", Default().NODES_PER_BLOCK),
                "init_blocks": config.get("init blocks", Default().INIT_BLOCKS),
                "min_blocks": config.get("min blocks", Default().MIN_BLOCKS),
                "max_blocks": config.get("max blocks", Default().MAX_BLOCKS),
                "exclusive": config.get("exclusive", Default().EXCLUSIVE),
                "partition": config.get("partition", Default().PARTITION),
                "account": config.get("account", Default().ACCOUNT),
                "worker_init": "\n".join(config.get("environment", Default().ENVIRONMENT)),
            },
        ),
    )
    return e


def load(
    yaml_config: Dict[str, Any],
    include: Optional[List[str]] = None,
    client: Optional[Client] = None,
) -> Config:
    """Construct a list of Executors from the input configuration dictionary

    The list returned by this function can be used to construct a Parsl Config
    object which is then used in parsl.load(config)


    Parameters
    ----------

    yaml_config: Dict[str, Any]
        YAML configuration block that contains the configuration for a list of
        resources

    include: List[str] | None
        A list of the labels of the resources to load. The default is None.
        If None, all resources are loaded.  Otherwise the resources whose
        labels are in the list will be loaded.

    client: Client | None
        A Globus Compute client to use when instantiating Globus Compute resources.
        The default is None.  If None, one will be instantiated automatically for
        any Globus Compute resources in the configuration.

    Returns
    -------

    Config
    """
    # Define a default HTEX Executor with a local provider
    executors = [
        HighThroughputExecutor(
            label="local",
            worker_debug=True,
            cores_per_worker=1,
            provider=LocalProvider(
                init_blocks=0,
                max_blocks=1,
            ),
        )
    ]

    # Add an Executor for each resource
    if include is None:
        resources = yaml_config
    else:
        resources = { key: yaml_config[key] for key in include if key in yaml_config }
    for resource_name, resource_config in resources.items():
        if resource_config.get("endpoint"):
            executors.append(make_globus_compute_executor(resource_name, resource_config, client))
        else:
            if resource_config.get("mpi", False):
                executors.append(make_mpi_executor(resource_name, resource_config))
            else:
                executors.append(make_htex_executor(resource_name, resource_config))

    return Config(executors)
