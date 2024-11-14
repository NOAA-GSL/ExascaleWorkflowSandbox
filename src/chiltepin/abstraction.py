import os
import pathlib
import textwrap
import parsl
from parsl.config import Config
from parsl.executors import ThreadPoolExecutor, MPIExecutor, HighThroughputExecutor, GlobusComputeExecutor
from parsl.launchers import SimpleLauncher
from parsl.providers import SlurmProvider
from chiltepin.wrappers import python_task, bash_task #, mpi_task

from globus_compute_sdk import Client, Executor
from globus_compute_sdk.serialize import CombinedCode


class HelloPythonTest:

    def __init__(
        self,
    ):
        self.foo = "foo"

    @python_task
    def hello(self, name):
        import socket
        import datetime
        return f"Hello {self.foo} {name} on {socket.gethostname()} at {datetime.datetime.now()}"


class HelloBashTest:

    def __init__(
        self,
    ):
        self.foo = "foo"
        pass

    @bash_task
    def hello(self, name, stdout=None, stderr=None, dependency=None):
        return f"""
        echo "Hello {self.foo} {name} on $(hostname) at $(date)"
        """


class HelloMPITest:

    def __init__(
        self,
    ):
        self.foo = "foo"

    #@mpi_task
    @bash_task
    def hello(self, name, stdout=None, stderr=None, dependency=None, parsl_resource_specification=None):
        return f"""
         #$PARSL_MPI_PREFIX --overcommit echo "Hello {self.foo} {name} on $(hostname) at $(date)"
         echo $PARSL_MPI_PREFIX
         $PARSL_MPI_PREFIX --overcommit hostname
        """

if __name__ == "__main__":
    from chiltepin.abstraction import HelloPythonTest
    from chiltepin.abstraction import HelloBashTest    
    from chiltepin.abstraction import HelloMPITest
    #pwd = pathlib.Path(__file__).parent.resolve()
    pwd = "/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox.wrap/tests"
    default_ep_id = "bae38bf7-d345-4e8c-9073-eacb68417478"
    mpi_ep_id = "78cfd4a8-732b-47f8-ab9f-b02087996321"
    
    with parsl.load(
        Config(
            executors=[
                HighThroughputExecutor(
                    label="default",
                    cores_per_worker=1,
                    max_workers_per_node=80,
                    provider=SlurmProvider(
                        exclusive=False,
                        cores_per_node=80,
                        nodes_per_block=1,
                        init_blocks=1,
                        min_blocks=1,
                        max_blocks=3,
                        partition="hercules",
                        account="gsd-hpcs",
                        walltime="00:30:00",
                        launcher=SimpleLauncher(),
                        worker_init="""
                        """,
                    ),
                ),
                
                MPIExecutor(
                    label="mpi",
                    mpi_launcher="srun",
                    max_workers_per_block=2,
                    provider=SlurmProvider(
                        exclusive=True,
                        cores_per_node=80,
                        nodes_per_block=3,
                        init_blocks=1,
                        partition="hercules",
                        account="gsd-hpcs",
                        walltime="00:30:00",
                        launcher=SimpleLauncher(),
                        worker_init="""
                        """,
                    ),
                ),
                
                GlobusComputeExecutor(
                    label="gc_mpi",
                    #endpoint_id=mpi_ep_id,
                    endpoint_id=default_ep_id,
                    user_endpoint_config = {
                        "engine_type": "GlobusMPIEngine",
                        "max_mpi_apps": 2,
                        "partition": "hercules",
                        "account": "gsd-hpcs",
                        "cores_per_node": 80,
                        "nodes_per_block": 3,
                    },
                ),
                
                GlobusComputeExecutor(
                    label="gc_default",
                    endpoint_id=default_ep_id,
                    user_endpoint_config = {
                        "engine_type": "GlobusComputeEngine",
                        "partition": "hercules",
                        "account": "gsd-hpcs",
                        "cores_per_node": 80,
                        "nodes_per_block": 1,
                    },
                ),
            ]
        )
    ):

        # Test Python decorators
        python = HelloPythonTest()
        python_parsl = python.hello(
            "from Parsl",
            executor="default",
        )
        python_gc = python.hello(
            "from Globus Compute",
            executor="gc_default",
        )
        print(python_parsl)
        print(python_gc)
        
        # Test Bash decorators
        bash = HelloBashTest()
        bash_parsl = bash.hello(
            "from Parsl",
            executor="default",
            stdout=os.path.join(pwd, "bash_parsl.out"),
            stderr=os.path.join(pwd, "bash_parsl.err"),
            dependency=python_parsl,
        )
        bash_gc = bash.hello(
            "from Globus Compute",
            executor="gc_default",
            stdout=os.path.join(pwd, "bash_gc.out"),
            stderr=os.path.join(pwd, "bash_gc.err"),
            dependency=python_gc,
        )
        print(bash_parsl)
        print(bash_gc)
        
        # Test MPI decorators
        mpi = HelloMPITest()
        mpi_parsl = mpi.hello(
            "from Parsl",
            executor="mpi",
            stdout=os.path.join(pwd, "mpi_parsl.out"),
            stderr=os.path.join(pwd, "mpi_parsl.err"),
            parsl_resource_specification = {
                "num_nodes": 3,  # Number of nodes required for the application instance
                "num_ranks": 6,  # Number of ranks in total
                "ranks_per_node": 2,  # Number of ranks / application elements to be launched per node
            },
            dependency=bash_parsl,
        )
        mpi_gc = mpi.hello(
            "from Globus Compute",
            executor="gc_mpi",
            stdout=os.path.join(pwd, "mpi_gc.out"),
            stderr=os.path.join(pwd, "mpi_gc.err"),
            parsl_resource_specification = {
                "num_nodes": 3,  # Number of nodes required for the application instance
                "num_ranks": 6,  # Number of ranks in total
                "ranks_per_node": 2,  # Number of ranks / application elements to be launched per node
            },
            dependency=bash_gc,
        )
        print(mpi_parsl)
        print(mpi_gc)
        
        print(python_parsl.result())
        print(python_gc.result())
        print(bash_parsl.result())
        print(bash_gc.result())
        print(mpi_parsl.result())
        print(mpi_gc.result())
