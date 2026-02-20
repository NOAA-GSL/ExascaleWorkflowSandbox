from typing import Any, Dict, List, Optional

import yaml
from globus_compute_sdk import Client, Executor
from parsl.config import Config
from parsl.executors import GlobusComputeExecutor, HighThroughputExecutor, MPIExecutor
from parsl.executors.base import ParslExecutor
from parsl.launchers import (
    MpiExecLauncher,
    SimpleLauncher,
    SingleNodeLauncher,
    SrunLauncher,
)
from parsl.providers import LocalProvider, PBSProProvider, SlurmProvider
from parsl.providers.base import ExecutionProvider


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


def create_provider(config: Dict[str, Any]) -> ExecutionProvider:
    """Create the appropriate ExecutionProvider from the given configuration

    Parameters
    ----------

    config: Dict[str, Any]
        YAML configuration block that contains the following configuration options.
        Not all options are valid for all providers.

        Options for all providers:

        Option key                Default value
        "mpi"                     False
        "provider":               "localhost"
        "init blocks":            0
        "min blocks":             0
        "max blocks":             1
        "environment":            []

        Options for Slurm provider:
        "cores per node":         1
        "nodes per block":        1
        "exclusive":              True
        "partition":              None
        "queue":                  None
        "account":                None
        "walltime":               "00:10:00"

        Options for PBSPro provider:
        "cores per node":         1
        "nodes per block":        1
        "queue":                  None
        "account":                None
        "walltime":               "00:10:00"

    Returns
    -------

    ExecutionProvider
    """

    provider = config.get("provider", "localhost")

    if provider == "slurm":
        return SlurmProvider(
            cores_per_node=(
                None if config.get("mpi", False) else config.get("cores_per_node")
            ),
            nodes_per_block=config.get("nodes_per_block", 1),
            init_blocks=config.get("init_blocks", 0),
            min_blocks=config.get("min_blocks", 0),
            max_blocks=config.get("max_blocks", 1),
            exclusive=config.get("exclusive", True),
            partition=config.get("partition"),
            qos=config.get("queue"),
            account=config.get("account"),
            walltime=config.get("walltime", "00:10:00"),
            worker_init="\n".join(config.get("environment", [])),
            launcher=(SimpleLauncher() if config.get("mpi", False) else SrunLauncher()),
        )
    elif provider == "pbspro":
        return PBSProProvider(
            cpus_per_node=(
                None if config.get("mpi", False) else config.get("cores_per_node")
            ),
            nodes_per_block=config.get("nodes_per_block", 1),
            init_blocks=config.get("init_blocks", 0),
            min_blocks=config.get("min_blocks", 0),
            max_blocks=config.get("max_blocks", 1),
            queue=config.get("queue"),
            account=config.get("account"),
            walltime=config.get("walltime", "00:10:00"),
            worker_init="\n".join(config.get("environment", [])),
            launcher=(
                SimpleLauncher() if config.get("mpi", False) else MpiExecLauncher()
            ),
        )
    elif provider == "localhost":
        return LocalProvider(
            init_blocks=config.get("init_blocks", 0),
            min_blocks=config.get("min_blocks", 0),
            max_blocks=config.get("max_blocks", 1),
            worker_init="\n".join(config.get("environment", [])),
            launcher=(
                SimpleLauncher() if config.get("mpi", False) else SingleNodeLauncher()
            ),
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def create_htex_executor(name: str, config: Dict[str, Any]) -> HighThroughputExecutor:
    """Construct a HighThroughputExecutor from the input configuration

    Parameters
    ----------

    name: str
        A label that will be assigned to the returned HighThroughputExecutor
        for naming purposes

    config: Dict[str, Any]
        YAML configuration block that contains the following configuration options:

        Option key                Default value
        "provider":               "localhost"
        "cores per node":         1
        "nodes per block":        1
        "init blocks":            0
        "min blocks":             0
        "max blocks":             1
        "exclusive":              True
        "partition":              None
        "queue":                  None
        "account":                None
        "walltime":               "00:10:00"
        "environment":            []

    Returns
    -------

    HighThroughputExecutor
    """

    e = HighThroughputExecutor(
        label=name,
        cores_per_worker=config.get("cores_per_worker", 1),
        max_workers_per_node=config.get("max_workers_per_node"),
        provider=create_provider(config),
    )
    return e


def create_mpi_executor(
    name: str,
    config: Dict[str, Any],
) -> MPIExecutor:
    """Construct a MPIExecutor from the input configuration

    Parameters
    ----------

    name: str
        A label that will be assigned to the returned MPIExecutor
        for naming purposes

    config: Dict[str, Any]
        YAML configuration block that contains the following configuration options:

        Option key                Default value
        "max mpi apps":           1
        "mpi_launcher":           "srun" for Slurm, otherwise "mpiexec"
        "provider":               "localhost"
        "cores per node":         1
        "nodes per block":        1
        "init blocks":            0
        "min blocks":             0
        "max blocks":             1
        "exclusive":              True
        "partition":              None
        "queue":                  None
        "account":                None
        "walltime":               "00:10:00"
        "environment":            []

    Returns
    -------

    MPIExecutor
    """
    default_launcher = (
        "srun" if config.get("provider", "localhost") == "slurm" else "mpiexec"
    )
    e = MPIExecutor(
        label=name,
        mpi_launcher=config.get("mpi_launcher", default_launcher),
        max_workers_per_block=config.get("max_mpi_apps", 1),
        provider=create_provider(config),
    )
    return e


def create_globus_compute_executor(
    name: str,
    config: Dict[str, Any],
    client: Optional[Client] = None,
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
        "mpi"                     False
        "max mpi apps":           1
        "mpi_launcher":           "srun" for Slurm, otherwise "mpiexec"
        "provider":               "localhost"
        "cores per node":         1
        "nodes per block":        1
        "init blocks":            0
        "min blocks":             0
        "max blocks":             1
        "exclusive":              True
        "partition":              ""
        "queue":                  ""
        "account":                ""
        "walltime":               "00:10:00"
        "environment":            []

    client: Client | None
        The Globus Compute client to use for instantiating the GlobusComputeExecutor.
        If not specified, Globus Compute will instantiate and use a default client.

    Returns
    -------

    GlobusComputeExecutor
    """

    default_launcher = (
        "srun" if config.get("provider", "localhost") == "slurm" else "mpiexec"
    )
    e = GlobusComputeExecutor(
        label=name,
        executor=Executor(
            endpoint_id=config["endpoint"],
            client=client,
            user_endpoint_config={
                "mpi": config.get("mpi", False),
                "max_mpi_apps": config.get("max_mpi_apps", 1),
                "mpi_launcher": config.get("mpi_launcher", default_launcher),
                "provider": config.get("provider", "localhost"),
                "cores_per_node": config.get("cores_per_node", 1),
                "nodes_per_block": config.get("nodes_per_block", 1),
                "init_blocks": config.get("init_blocks", 0),
                "min_blocks": config.get("min_blocks", 0),
                "max_blocks": config.get("max_blocks", 1),
                "exclusive": config.get("exclusive", True),
                "partition": config.get("partition", ""),
                "queue": config.get("queue", ""),
                "account": config.get("account", ""),
                "walltime": config.get("walltime", "00:10:00"),
                "worker_init": "\n".join(config.get("environment", [])),
            },
        ),
    )
    return e


def create_executor(
    name: str,
    config: Dict[str, Any],
    client: Optional[Client] = None,
) -> ParslExecutor:
    """Create an Executor specified by the given resource configuration

    Parameters
    ----------

    name: str
        The name of the resource

    config: Dict[str, Any]
        YAML configuration block that contains the resource's configuration

    client: Client | None
        A Globus Compute client to use when instantiating Globus Compute resources.
        The default is None.  If None, one will be instantiated automatically for
        any Globus Compute resources in the configuration. Only applies to Globus
        Compute resources

    Returns
    -------

    ParslExecutor
    """

    if config.get("endpoint"):
        return create_globus_compute_executor(name, config, client)
    else:
        if config.get("mpi", False):
            return create_mpi_executor(name, config)
        else:
            return create_htex_executor(name, config)


def load(
    config: Dict[str, Any],
    include: Optional[List[str]] = None,
    client: Optional[Client] = None,
    run_dir: Optional[str] = None,
) -> Config:
    """Return a Parsl Config initialized by a list of Executors created  from
    the input configuration dictionary.

    The Config object returned by this function is used in parsl.load(config)

    Parameters
    ----------

    config: Dict[str, Any]
        YAML configuration block that contains the configuration for a list of
        resources

    include: List[str] | None
        A list of the labels of the resource configurations to load. The
        default is None. If None, all resource configurations are loaded.
        Otherwise the configurations for resources whose labels are in the
        list will be loaded.

    client: Client | None
        A Globus Compute client to use when instantiating Globus Compute resources.
        The default is None.  If None, one will be instantiated automatically for
        any Globus Compute resources in the configuration.

    run_dir: str | None
        The directory to use for runtime files. The default is None, which means
        Parsl's default runinfo directory location will be used.

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
            max_workers_per_node=1,
            provider=LocalProvider(
                init_blocks=0,
                max_blocks=1,
            ),
        )
    ]

    # Add an Executor for each resource
    if include is None:
        resources = config
    else:
        resources = {key: config[key] for key in include if key in config}
    for resource_name, resource_config in resources.items():
        executors.append(
            create_executor(
                resource_name,
                resource_config,
                client,
            ),
        )

    config_kwargs = {"executors": executors}
    if run_dir is not None:
        config_kwargs["run_dir"] = run_dir
    return Config(**config_kwargs)
