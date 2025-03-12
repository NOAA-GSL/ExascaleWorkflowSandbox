import textwrap
from concurrent.futures import Future
from datetime import datetime
from typing import List, Optional

from uwtools.api import config as uwconfig

from chiltepin.tasks import bash_task, join_task


class MPAS:
    """Chiltepin task drivers for installing and running MPAS.

    Parameters
    ----------

    environment: List[str] | None
        A list of bash environment commands to run before executing MPAS tasks.
        These commands are run after the execution resource's environment
        settings have been applied. If None (the default), no environment setup
        commands are run.

    install_path: str | None
        The installation path for MPAS. If None (the default) the current
        working directory is used.

    tag: str | None
        The tag of MPAS to use. If None (the default) "develop" will be used
        to clone and install MPAS.
    """

    def __init__(
        self,
        environment: Optional[List[str]] = None,
        install_path: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> None:

        self.environment = "\n".join(environment or [""])
        self.install_path = install_path or "./"
        self.tag = tag or "develop"

    def clone(
        self,
        *,
        executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> Future:
        """Clone the MPAS repository.

        Schedules and executes a workflow task to clone the MPAS repository
        into the install path set when the MPAS object was initialized. This
        is a non-blocking call that returns a Future representing the eventual
        result of the clone operation.

        Parameters
        ----------

        executor: List[str]
            List of names of executors where the clone task may execute.

        stdout: str | None
            Full path to the file where stdout of the clone task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the clone task is to be
            written. If not specified, output to stderr will not be captured.

        Returns
        -------

        Future
            The future result of the clone task's execution.
        """
        return self._clone(
            executor=executor,
            stdout=stdout,
            stderr=stderr,
        )

    def make(
        self,
        *,
        jobs: int = 8,
        executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        clone: Optional[Future] = None,
    ) -> Future:
        """Build the MPAS code that has previously been cloned.

        Schedules and executes a workflow task to build the MPAS code. This
        is a non-blocking call that returns a Future representing the eventual
        result of the make operation.

        Parameters
        ----------

        jobs: int
            The number of threads to use when building MPAS.

        executor: List[str]
            List of names of executors where the make task may execute.

        stdout: str | None
            Full path to the file where stdout of the make task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the make task is to be
            written. If not specified, output to stderr will not be captured.

        clone: Future | None
            A future that represents the results of the clone task that must
            finish successfully before the make task can execute. If left
            unspecified (the default), no dependency for this task will be
            enforced.

        Returns
        -------

        Future
            The future result of the make task's execution.
        """
        return self._make(
            jobs=jobs,
            executor=executor,
            stdout=stdout,
            stderr=stderr,
            clone=clone,
        )

    def install(
        self,
        *,
        jobs: int = 8,
        clone_executor: List[str],
        make_executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> Future:
        """Clone and build MPAS.

        Schedules and executes a workflow task to clone and build the MPAS code.
        This is a non-blocking call that returns a Future representing the
        eventual result of the install operation.

        Parameters
        ----------

        jobs: int
            The number of threads to use when building MPAS.

        clone_executor: List[str]
            List of names of executors where the clone subtask may execute.

        make_executor: List[str]
            List of names of executors where the make subtask may execute.

        stdout: str | None
            Full path to the file where stdout of the make task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the make task is to be
            written. If not specified, output to stderr will not be captured.

        Returns
        -------

        Future
            The future result of the install task's execution.
        """
        return self._install(
            jobs=jobs,
            clone_executor=clone_executor,
            make_executor=make_executor,
            stdout=stdout,
            stderr=stderr,
        )

    def mpas_init(
        self,
        config_path: str,
        cycle_str: str,
        key_path: str,
        *,
        executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
        resource_specification={},
    ) -> Future:
        """Run MPAS init_atmosphere_model to produce initial or boundary
        condition files for later input to the MPAS forecast task.

        Parameters
        ----------

        config_path: str
            The full path to the mpas_init YAML configuration file.

        cycle_str: str
            The cycle time in ISO format (%Y-%m-%dT%H:%M:%S) for running
            mpas_init that will be realized in the configuration file.

        key_path: str
            YAML configuration key path containing the mpas init config.

        executor: List[str]
            List of names of executors where the mpas_init task may execute.

        stdout: str | None
            Full path to the file where stdout of the mpas_init task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the mpas_init task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the make or install task
            that must finish successfully before the mpas_init task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.

        resource_specification: Dict[str, int]
            A dictionary specifying the MPI task geometry for running mpas_init.

            For example::

                resource_specification = {
                     'num_nodes': <int>,        # Number of nodes required for the application instance
                     'ranks_per_node': <int>,   # Number of ranks / application elements to be launched per node
                     'num_ranks': <int>,        # Number of ranks in total
                }

        Returns
        -------
        Future
            The future result of the mpas_init task's execution
        """
        return self._mpas_init(
            config_path=config_path,
            cycle_str=cycle_str,
            key_path=key_path,
            executor=executor,
            stdout=stdout,
            stderr=stderr,
            install=install,
            parsl_resource_specification=resource_specification,
        )

    def mpas_forecast(
        self,
        config_path: str,
        cycle_str: str,
        key_path: str,
        *,
        executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
        resource_specification={},
    ) -> Future:
        """Run MPAS atmosphere_model to produce an MPAS forecast.

        Parameters
        ----------

        config_path: str
            The full path to the mpas_forecast YAML configuration file.

        cycle_str: str
            The cycle time in ISO format (%Y-%m-%dT%H:%M:%S) for running
            mpas_forecast that will be realized in the configuration file.

        key_path: str
            YAML configuration key path containing the mpas forecast config.

        executor: List[str]
            List of names of executors where the mpas_forecast task may execute.

        stdout: str | None
            Full path to the file where stdout of the mpas_forecast task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the mpas_forecast task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the make or install task
            that must finish successfully before the mpas_forecast task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.

        resource_specification: Dict[str, int]
            A dictionary specifying the MPI task geometry for running mpas_forecast.

            For example::

                resource_specification = {
                     'num_nodes': <int>,        # Number of nodes required for the application instance
                     'ranks_per_node': <int>,   # Number of ranks / application elements to be launched per node
                     'num_ranks': <int>,        # Number of ranks in total
                }

        Returns
        -------
        Future
            The future result of the mpas_forecast task's execution
        """
        return self._mpas_forecast(
            config_path=config_path,
            cycle_str=cycle_str,
            key_path=key_path,
            executor=executor,
            stdout=stdout,
            stderr=stderr,
            install=install,
            parsl_resource_specification=resource_specification,
        )

    @bash_task
    def _clone(
        self,
        *,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> str:
        """A bash task to clone the MPAS repository.

        The repository will be cloned into ``<install_path>/MPAS/<tag>/``.

        Parameters
        ----------

        stdout: str | None
            Full path to the file where stdout of the clone task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the clone task is to be
            written. If not specified, output to stderr will not be captured.

        Returns
        -------

        str
            A string containing the bash script that implements the MPAS clone
            task. This string is consumed by the @bash_task decorator that wraps
            this method to create a workflow task.
        """
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            git lfs install --skip-repo
            rm -rf {self.install_path}/mpas/{self.tag}
            mkdir -p {self.install_path}/mpas/{self.tag}
            cd {self.install_path}/mpas/{self.tag}
            git clone https://github.com/NOAA-GSL/MPAS-Model.git .
            git checkout {self.tag}
            echo Completed at $(date)
            """
        )

    @bash_task
    def _make(
        self,
        *,
        jobs: int = 8,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        clone: Optional[Future] = None,
    ) -> str:
        """A bash task to build MPAS code that has previously been cloned.

        Parameters
        ----------

        jobs: int
            The number of threads to use when building MPAS.

        stdout: str | None
            Full path to the file where stdout of the make task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the make task is to be
            written. If not specified, output to stderr will not be captured.

        clone: Future | None
            A future that represents the results of the clone task that must
            finish successfully before the make task can execute. If left
            unspecified (the default), no dependency for this task will be
            enforced.

        Returns
        -------

        str
            A string containing the bash script that implements the MPAS make
            task. This string is consumed by the @bash_task decorator that wraps
            this method to create a workflow task.
        """
        repo_url = "https://raw.githubusercontent.com/NOAA-GSL/ExascaleWorkflowSandbox/"
        patch_url = repo_url + "main/apps/mpas/patches"
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            cd {self.install_path}/mpas/{self.tag}
            mkdir exe
            export PIO=$parallelio_ROOT
            curl -L {patch_url}/src.framework.Makefile.patch -o src.framework.Makefile.patch
            patch -p 0 < src.framework.Makefile.patch
            compiler=$(basename $CC)
            # Set the MPAS build target to match compiler
            if [[ $compiler = "gcc" ]]; then
              build_target="gfortran"
            elif [[ $compiler = "icc" ]]; then
              build_target="intel-mpi"
            else
              echo "Unsupported compiler: $CC"
              exit 1
            fi
            make $build_target CORE=init_atmosphere -j {jobs}
            cp -v init_atmosphere_model exe/
            make clean CORE=init_atmosphere

            make $build_target CORE=atmosphere -j {jobs}
            cp -v atmosphere_model exe/

            echo Completed at $(date)
            """
        )

    @join_task
    def _install(
        self,
        *,
        jobs: int = 8,
        clone_executor: List[str] = ["service"],
        make_executor: List[str] = ["service"],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> Future:
        """A join task to install MPAS

        Parameters
        ----------

        jobs: int
            The number of threads to use when building MPAS.

        clone_executor: List[str]
            A list of executors where the clone subtask is allowed to execute.

        make_executor: List[str]
            A list of executors where the make subtask is allowed to execute.

        stdout: str | None
            Full path to the file where stdout of the make task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the make task is to be
            written. If not specified, output to stderr will not be captured.

        Returns
        -------

        Future
            A Future that represents the result of the @join_task that
            installs MPAS.
        """
        clone = self._clone(
            stdout=(stdout, "w"),
            stderr=(stderr, "w"),
            executor=clone_executor,
        )
        make = self._make(
            jobs=jobs,
            stdout=(stdout, "a"),
            stderr=(stderr, "a"),
            executor=make_executor,
            clone=clone,
        )
        return make

    @bash_task
    def _mpas_init(
        self,
        config_path: str,
        cycle_str: str,
        key_path: str,
        *,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
        parsl_resource_specification={},
    ) -> str:
        """A bash task to run init_atmosphere_model to produce initial or
        boundary condition files for later input to the MPAS forecast task.

        Parameters
        ----------

        config_path: str
            The full path to the mpas_init YAML configuration file.

        cycle_str: str
            The cycle time in ISO format (%Y-%m-%dT%H:%M:%S) for running
            mpas_init that will be realized in the configuration file.

        key_path: str
            YAML configuration key path containing the mpas init config.

        executor: List[str]
            List of names of executors where the mpas_init task may execute.

        stdout: str | None
            Full path to the file where stdout of the mpas_init task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the mpas_init task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the make or install task
            that must finish successfully before the mpas_init task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.

        parsl_resource_specification: Dict[str, int]
            A dictionary specifying the MPI task geometry for running mpas_init.

            For example::

                parsl_resource_specification = {
                     'num_nodes': <int>,        # Number of nodes required for the application instance
                     'ranks_per_node': <int>,   # Number of ranks / application elements to be launched per node
                     'num_ranks': <int>,        # Number of ranks in total
                }

        Returns
        -------
        str
            A string containing the bash script that implements the MPAS init
            task. This string is consumed by the @bash_task decorator that wraps
            this method to create a workflow task.
        """
        cycle = datetime.fromisoformat(cycle_str)

        # Extract driver config from experiment config
        expt_config = uwconfig.get_yaml_config(config_path)
        expt_config.dereference(context={"cycle": cycle, **expt_config})

        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            export PATH=$PATH:.
            uw mpas_init provisioned_rundir --cycle {cycle_str} \
               --config-file {config_path} --key-path {key_path} --verbose
            cd {expt_config[key_path]['mpas_init']['rundir']}
            echo "Run Command: '$PARSL_MPI_PREFIX {self.install_path}/mpas/{self.tag}/exe/init_atmosphere_model'"
            $PARSL_MPI_PREFIX --overcommit {self.install_path}/mpas/{self.tag}/exe/init_atmosphere_model
            echo Completed at $(date)
            """
        )

    @bash_task
    def _mpas_forecast(
        self,
        config_path: str,
        cycle_str: str,
        key_path: str,
        *,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
        parsl_resource_specification={},
    ) -> str:
        """A bash task to run atmosphere_model to produce an MPAS forecast.

        Parameters
        ----------

        config_path: str
            The full path to the mpas_forecast YAML configuration file.

        cycle_str: str
            The cycle time in ISO format (%Y-%m-%dT%H:%M:%S) for running
            mpas_forecast that will be realized in the configuration file.

        key_path: str
            YAML configuration key path containing the mpas forecast config.

        executor: List[str]
            List of names of executors where the mpas_forecast task may execute.

        stdout: str | None
            Full path to the file where stdout of the mpas_forecast task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the mpas_forecast task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the make or install task
            that must finish successfully before the mpas_forecast task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.

        parsl_resource_specification: Dict[str, int]
            A dictionary specifying the MPI task geometry for running mpas_forecast.

            For example::

                parsl_resource_specification = {
                     'num_nodes': <int>,        # Number of nodes required for the application instance
                     'ranks_per_node': <int>,   # Number of ranks / application elements to be launched per node
                     'num_ranks': <int>,        # Number of ranks in total
                }

        Returns
        -------
        str
            A string containing the bash script that implements the MPAS forecast
            task. This string is consumed by the @bash_task decorator that wraps
            this method to create a workflow task.
        """
        cycle = datetime.fromisoformat(cycle_str)

        # Extract driver config from experiment config
        expt_config = uwconfig.get_yaml_config(config_path)
        expt_config.dereference(context={"cycle": cycle, **expt_config})

        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            export PATH=$PATH:.
            uw mpas provisioned_rundir --cycle {cycle_str} \
                --config-file {config_path} --key-path {key_path} --verbose
            cd {expt_config[key_path]['mpas']['rundir']}
            echo "Run Command: '$PARSL_MPI_PREFIX {self.install_path}/mpas/{self.tag}/exe/atmosphere_model'"
            $PARSL_MPI_PREFIX --overcommit {self.install_path}/mpas/{self.tag}/exe/atmosphere_model
            echo Completed at $(date)
            """
        )
