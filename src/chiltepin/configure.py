from typing import Any, Dict, List, Optional

import yaml
from globus_compute_sdk import Client, Executor
from parsl.config import Config
from parsl.executors import GlobusComputeExecutor, HighThroughputExecutor, MPIExecutor
from parsl.launchers import SimpleLauncher
from parsl.providers import LocalProvider, SlurmProvider


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
        cores_per_worker=config.get("cores per worker", 1),
        max_workers_per_node=config.get("max workers per node", 1),
        provider=SlurmProvider(
            exclusive=config.get("exclusive", True),
            cores_per_node=config.get("cores per node", None),
            nodes_per_block=config.get("nodes per block", 1),
            init_blocks=config.get("init blocks", 0),
            min_blocks=config.get("min blocks", 0),
            max_blocks=config.get("max blocks", 1),
            partition=config.get("partition", None),
            account=config.get("account", None),
            walltime=config.get("walltime", "01:00:00"),
            worker_init="\n".join(config.get("environment", [])),
            launcher=SimpleLauncher(),
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
        max_workers_per_block=config.get("max mpi apps", 1),
        provider=SlurmProvider(
            exclusive=config.get("exclusive", True),
            cores_per_node=config.get("cores per node", None),
            nodes_per_block=config.get("nodes per block", 1),
            init_blocks=config.get("init blocks", 0),
            min_blocks=config.get("min blocks", 0),
            max_blocks=config.get("max blocks", 1),
            partition=config.get("partition", None),
            account=config.get("account", None),
            walltime=config.get("walltime", "01:00:00"),
            worker_init="\n".join(config.get("environment", [])),
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
            endpoint_id=config["endpoint id"],
            client=client,
            user_endpoint_config={
                "engine": config.get("engine", "GlobusComputeEngine"),
                "max_mpi_apps": config.get("max mpi apps", 1),
                "cores_per_node": config.get("cores per node", 1),
                "nodes_per_block": config.get("nodes per block", 1),
                "init_blocks": config.get("init blocks", 0),
                "min_blocks": config.get("min blocks", 0),
                "max_blocks": config.get("max blocks", 1),
                "exclusive": config.get("exclusive", True),
                "partition": config["partition"],
                "account": config["account"],
                "worker_init": "\n".join(config.get("environment", [])),
            },
        ),
    )
    return e


def load(
    config: Dict[str, Any],
    resources: Optional[List[str]] = None,
    client: Optional[Client] = None,
) -> Config:
    """Construct a list of Executors from the input configuration dictionary

    The list returned by this function can be used to construct a Parsl Config
    object which is then used in parsl.load(config)


    Parameters
    ----------

    config: Dict[str, Any]
        YAML configuration block that contains the configuration for a list of
        resources

    resources: List[str] | None
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
    for name, spec in config.items():
        if resources is None or name in resources:
            if spec["engine"] == "HTEX":
                # Make a HighThroughputExecutor
                executors.append(make_htex_executor(name, spec))
            elif spec["engine"] == "MPI":
                # Make an MPIExecutor
                executors.append(make_mpi_executor(name, spec))
            elif spec["engine"] == "GlobusComputeEngine":
                # Make a GlobusComputeExecutor for non-MPI jobs
                executors.append(make_globus_compute_executor(name, spec, client))
            elif spec["engine"] == "GlobusMPIEngine":
                # Make a GlobusComputeExecutor for MPI jobs
                executors.append(make_globus_compute_executor(name, spec, client))
    return Config(executors)
