import os
import pathlib
import textwrap
import parsl
from parsl.app.app import bash_app, join_app, python_app
from globus_compute_sdk import Executor, ShellFunction, MPIFunction
from parsl.config import Config
from parsl.executors import ThreadPoolExecutor, MPIExecutor, HighThroughputExecutor
from parsl.launchers import SimpleLauncher
from parsl.providers import SlurmProvider

from functools import wraps

def python_task(func):
    @wraps(func)
    def func_wrapper(
            *args,
            executor=None,
            **kwargs,
    ):
        if isinstance(executor, str):
            return python_app(func, executors=[executor])(*args, **kwargs)
        elif isinstance(executor, Executor):
            # Wrap gc call in a Join Parsl App to enforce dependencies passed in as Futures in arguments
            @join_app
            def dependency_wrapper(gce, *args, **kwargs):
                return gce.submit(
                    func,
                    *args,
                    **kwargs,
                )
            return dependency_wrapper(executor, *args, **kwargs)
        else:
            raise "Invalid executor"
    
    return func_wrapper


def bash_task(func):
    @wraps(func)
    def func_wrapper(
            *args,
            executor=None,
            **kwargs,
    ):
        if isinstance(executor, str):
            return bash_app(func, executors=[executor])(*args, **kwargs)
        elif isinstance(executor, Executor):
            sf = ShellFunction(f"""{func(*args, **kwargs)}""", stdout=kwargs.get("stdout"), stderr=kwargs.get("stderr"))
            # Wrap gc call in a Join Parsl App to enforce dependencies passed in as Futures in arguments
            @join_app
            def dependency_wrapper(gce, *args, **kwargs):
                return gce.submit(
                    sf,
                )
            return dependency_wrapper(executor, *args, **kwargs)
        else:
            raise "Invalid executor"
    
    return func_wrapper


def mpi_task(func):
    @wraps(func)
    def func_wrapper(
            *args,
            executor=None,
            **kwargs,
    ):
        if isinstance(executor, str):
            app = bash_app(func, executors=[executor])
            return app(*args, **kwargs)
        elif isinstance(executor, Executor):
            # Set GC executor parsl_resource_specification and remove it from kwargs
            executor.resource_specification = kwargs.pop("parsl_resource_specification", None)
            mpif = MPIFunction(f"""{func(*args, **kwargs)}""", stdout=kwargs.get("stdout"), stderr=kwargs.get("stderr"))
            # Wrap gc call in a Join Parsl App to enforce dependencies passed in as Futures in arguments
            @join_app
            def dependency_wrapper(gce, *args, **kwargs):
                return gce.submit(
                    mpif,
                )
            return dependency_wrapper(executor, *args, **kwargs)
        else:
            raise "Invalid executor"
    
    return func_wrapper


class HelloPythonTest:

    def __init__(
        self,
    ):
        pass

    @python_task
    def hello(self, name):
        import socket
        import datetime
        return f"Hello {name} on {socket.gethostname()} at {datetime.datetime.now()}"


class HelloBashTest:

    def __init__(
        self,
    ):
        pass

    @bash_task
    def hello(self, name, stdout=None, stderr=None, dependency=None):
        return f"""
        echo "Hello {name} on $(hostname) at $(date)"
        """


class HelloMPITest:

    def __init__(
        self,
    ):
        pass

    @mpi_task
    def hello(self, name, stdout=None, stderr=None, dependency=None, parsl_resource_specification=None):
        return f"""
        echo "Hello {name} on $(hostname) at $(date)"
        """

if __name__ == "__main__":
    from abstraction import HelloPythonTest
    from abstraction import HelloBashTest    
    from abstraction import HelloMPITest
    pwd = pathlib.Path(__file__).parent.resolve()
    default_ep_id = "1c4d10d1-913f-4339-98c9-3cc5e0630dc0"
    mpi_ep_id = "bf938d9b-7479-4450-a098-e03e7aaf7e1d"
    gce_default = Executor(endpoint_id=default_ep_id)
    gce_mpi = Executor(endpoint_id=mpi_ep_id)
    with parsl.load(
            Config(executors=[
                ThreadPoolExecutor(
                    label='threads', 
                    max_threads=2, 
                    storage_access=None, 
                    thread_name_prefix='', 
                    working_dir=None
                ),
                
                
                HighThroughputExecutor(
                    label="default",
                    cores_per_worker=1,
                    max_workers_per_node=40,
                    provider=SlurmProvider(
                        exclusive=False,
                        cores_per_node=40,
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
                        cores_per_node=40,
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
            executor=gce_default,
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
            executor=gce_default,
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
            executor=gce_mpi,
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
        
    gce_default.shutdown()
    gce_mpi.shutdown()
