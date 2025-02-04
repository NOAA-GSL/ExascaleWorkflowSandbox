import textwrap

from concurrent.futures import Future
from typing import List, Optional
from chiltepin.tasks import bash_task, join_task


class WPS:
    """Chiltepin task drivers for installing and running WRF Preprocessing
    System.

    Parameters
    ----------

    environment: List[str] | None
        A list of bash environment commands to run before executing WPS tasks.
        These commands are run after the execution resource's environment
        settings have been applied. If None (the default), no environment setup
        commands are run.

    install_path: str | None
        The installation path for WPS. If None (the default) the current
        working directory is used.

    tag: str | None
        The tag of WPS to use. If None (the default) "develop" will be used
        to clone and install WPS.
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
        """Clone the WPS repository.

        Schedules and executes a workflow task to clone the WPS repository
        into the install path set when the WPS object was initialized. This
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
        WRF_dir: Optional[str] = None,
        jobs: int = 8,
        executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        clone: Optional[Future] = None,
    ) -> Future:
        """Build the WPS code that have previously been cloned.

        Schedules and executes a workflow task to build the WPS code. This
        is a non-blocking call that returns a Future representing the eventual
        result of the make operation.

        Parameters
        ----------

        WRF_dir: str | None
            Full installation path of WRF. If None (the default), WPS will
            be built without WRF, and executables requiring wrf_io libraries
            will not be built.

        jobs: int
            The number of threads to use when building WPS.

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
            WRF_dir=WRF_dir,
            jobs=jobs,
            executor=executor,
            stdout=stdout,
            stderr=stderr,
            clone=clone,
        )

    def install(
        self,
        *,
        WRF_dir: Optional[str] = None,
        jobs: int = 8,
        clone_executor: List[str],
        make_executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> Future:
        """Clone and build WPS.

        Schedules and executes a workflow task to clone and build the WPS code.
        This is a non-blocking call that returns a Future representing the
        eventual result of the install operation.

        Parameters
        ----------

        WRF_dir: str | None
            Full installation path of WRF. If None (the default), WPS will
            be built without WRF, and executables requiring wrf_io libraries
            will not be built.

        jobs: int
            The number of threads to use when building WPS.

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
            WRF_dir=WRF_dir,
            jobs=jobs,
            clone_executor=clone_executor,
            make_executor=make_executor,
            stdout=stdout,
            stderr=stderr,
        )

    def ungrib(
        self,
        config_path: str,
        cycle_str: str,
        *,
        executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
    ) -> Future:
        """Run ungrib to extract fields from grib files and create input files
        for use by WPS's metgrid or MPAS's init_atmosphere_model codes.

        Parameters
        ----------

        config_path: str
            The full path to the ungrib YAML configuration file.

        cycle_str: str
            The cycle time in ISO format (%Y-%m-%dT%H:%M:%S) for running ungrib
            that will be realized in the configuration file.

        executor: List[str]
            List of names of executors where the ungrib task may execute.

        stdout: str | None
            Full path to the file where stdout of the ungrib task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the ungrib task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the make or install task
            that must finish successfully before the ungrib task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.

        Returns
        -------
        Future
            The future result of the ungrib task's execution
        """
        return self._ungrib(
            config_path=config_path,
            cycle_str=cycle_str,
            executor=executor,
            stdout=stdout,
            stderr=stderr,
            install=install,
        )

    @bash_task
    def _clone(
        self,
        *,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> str:
        """A bash task to clone the WPS repository.

        The repository will be cloned into ``<install_path>/WPS/<tag>/``.

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
            A string containing the bash script that implements the WPS clone
            task. This string is consumed by the @bash_task decorator that wraps
            this method to create a workflow task.
        """
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            git lfs install --skip-repo
            rm -rf {self.install_path}/WPS/{self.tag}
            mkdir -p {self.install_path}/WPS/{self.tag}
            cd {self.install_path}/WPS/{self.tag}
            wget https://github.com/wrf-model/WPS/archive/refs/tags/v{self.tag}.tar.gz
            tar --strip-components=1 -xzf v{self.tag}.tar.gz
            rm -f v{self.tag}.tar.gz
            echo Completed at $(date)
            """
        )

    @bash_task
    def _make(
        self,
        *,
        WRF_dir: Optional[str] = None,
        jobs: int = 8,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        clone: Optional[Future] = None,
    ) -> str:
        """A bash task to build WPS code that has previously been cloned.

        Parameters
        ----------

        WRF_dir: str | None
            Full installation path of WRF. If None (the default), WPS will
            be built without WRF, and executables requiring wrf_io libraries
            will not be built.

        jobs: int
            The number of threads to use when building WPS.

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
            A string containing the bash script that implements the WPS make
            task. This string is consumed by the @bash_task decorator that wraps
            this method to create a workflow task.
        """
        if WRF_dir is None:
            no_wrf = "--nowrf"
        else:
            no_wrf = ""
        repo_url = "https://raw.githubusercontent.com/spack/"
        patch_url = repo_url + "spack/develop/var/spack/repos/builtin/packages/wps"
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            cd {self.install_path}/WPS/{self.tag}
            export WRF_DIR={WRF_dir}
            # Jasper may be in /lib or /lib64
            export JASPERLIB=$(dirname $(find -L $jasper_ROOT -name libjasper.so))
            export JASPERINC=$jasper_ROOT/include
            export NETCDF=$netcdf_c_ROOT
            export NETCDFF=$netcdf_fortran_ROOT
            export J="-j {jobs}"
            curl -L {patch_url}/patches/4.2/arch.Config.pl.patch -o arch.Config.pl.patch
            curl -L {patch_url}/patches/4.2/preamble.patch -o preamble.patch
            curl -L {patch_url}/patches/4.4/configure.patch -o configure.patch
            patch -p 1 < arch.Config.pl.patch
            patch -p 1 < preamble.patch
            patch -p 1 < configure.patch
            os=$(uname -m)
            if [[ $os = "aarch64" ]]; then
              curl -L {patch_url}/for_aarch64.patch -o configure.aarch64.patch
              patch -p 1 < configure.aarch64.patch
            fi
            compiler=$(basename $CC)
            # Set the WPS build option to match compiler
            if [[ $compiler = "gcc" ]]; then
              build_option=3
            elif [[ $compiler = "icc" ]]; then
              sed 's:mpicc:mpiicc:' -i configure.wps
              sed 's:mpif90:mpiifort:' -i configure.wps
              build_option=19
            else
              echo "Unsupported compiler: $CC"
              exit 1
            fi
            echo $build_option | ./configure {no_wrf}
            ./compile
            echo Completed at $(date)
            """
        )

    @join_task
    def _install(
        self,
        *,
        WRF_dir: Optional[str] = None,
        jobs: int = 8,
        clone_executor: List[str] = ["service"],
        make_executor: List[str] = ["service"],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> Future:
        """A join task to install WPS

        Parameters
        ----------

        WRF_dir: str | None
            Full installation path of WRF. If None (the default), WPS will
            be built without WRF, and executables requiring wrf_io libraries
            will not be built.

        jobs: int
            The number of threads to use when building WPS.

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
            installs WPS.
        """
        clone = self._clone(
            stdout=(stdout, "w"),
            stderr=(stderr, "w"),
            executor=clone_executor,
        )
        make = self._make(
            jobs=jobs,
            WRF_dir=WRF_dir,
            stdout=(stdout, "a"),
            stderr=(stderr, "a"),
            executor=make_executor,
            clone=clone,
        )
        return make

    @bash_task
    def _ungrib(
        self,
        config_path: str,
        cycle_str: str,
        *,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
    ) -> str:
        """A bash task to run ungrib to extract fields from grib files and
        create input files for use by WPS's metgrid or MPAS's
        init_atmosphere_model codes.

        Parameters
        ----------

        config_path: str
            The full path to the ungrib YAML configuration file.

        cycle_str: str
            The cycle time in ISO format (%Y-%m-%dT%H:%M:%S) for running ungrib
            that will be realized in the configuration file.

        stdout: str | None
            Full path to the file where stdout of the ungrib task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the ungrib task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the make or install  task
            that must finish successfully before the ungrib task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.

        Returns
        -------
        str
            A string containing the bash script that implements the WPS ungrib
            task. This string is consumed by the @bash_task decorator that wraps
            this method to create a workflow task.
        """
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            export PATH=$PATH:.
            uw ungrib run --cycle {cycle_str} --config-file {config_path} --key-path prepare_grib --verbose
            echo Completed at $(date)
            """
        )
