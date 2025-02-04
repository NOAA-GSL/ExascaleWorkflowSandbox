import textwrap
from concurrent.futures import Future
from typing import List, Optional

from chiltepin.tasks import bash_task, join_task


class Metis:
    """Chiltepin task drivers for installing and running Metis.

    Parameters
    ----------

    environment: List[str] | None
        A list of bash environment commands to run before executing Metis tasks.
        These commands are run after the execution resource's environment
        settings have been applied. If None (the default), no environment setup
        commands are run.

    install_path: str | None
        The installation path for Metis. If None (the default) the current
        working directory is used.

    tag: str | None
        The tag of Metis to use. If None (the default) "develop" will be used
        to clone and install Metis.
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
        """Clone the Metis repository.

        Schedules and executes a workflow task to clone the Metis repository
        into the install path set when the Metis object was initialized. This
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
        executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        clone: Optional[Future] = None,
    ) -> Future:
        """Build the Metis code that have previously been cloned.

        Schedules and executes a workflow task to build the Metis code. This
        is a non-blocking call that returns a Future representing the eventual
        result of the make operation.

        Parameters
        ----------

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
            executor=executor,
            stdout=stdout,
            stderr=stderr,
            clone=clone,
        )

    def install(
        self,
        *,
        clone_executor: List[str],
        make_executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> Future:
        """Clone and build Metis.

        Schedules and executes a workflow task to clone and build the Metis code.
        This is a non-blocking call that returns a Future representing the
        eventual result of the install operation.

        Parameters
        ----------

        clone_executor: List[str]
            List of names of executors where the clone subtask may execute.

        make_executor: List[str]
            List of names of executors where the make subtask may execute.

        stdout: str | None
            Full path to the file where stdout of the install task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the install task is to be
            written. If not specified, output to stderr will not be captured.

        Returns
        -------

        Future
            The future result of the install task's execution.
        """
        return self._install(
            clone_executor=clone_executor,
            make_executor=make_executor,
            stdout=stdout,
            stderr=stderr,
        )

    def gpmetis(
        self,
        mesh_file: str,
        nprocs: int,
        *,
        executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
    ) -> Future:
        """Run gpmetis to partition a mesh file for a given number of processors.

        Parameters
        ----------

        mesh_file: str
            The full path to the input mesh file to be partitioned.

        nprocs: int
            The number of processors (partitions) required for the output mesh
            file.

        executor: List[str]
            List of names of executors where the gpmetis task may execute.

        stdout: str | None
            Full path to the file where stdout of the gpmetis task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the gpmetis task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the make or install task
            that must finish successfully before the gpmetis task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.

        Returns
        -------

        Future
            The future result of the gpmetis task's execution
        """
        return self._gpmetis(
            mesh_file=mesh_file,
            nprocs=nprocs,
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
        """A bash task to clone the Metis repository.

        The repository will be cloned into ``<install_path>/metis/build/<tag>/``.

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
            A string containing the bash script that implements the Metis clone
            task. This string is consumed by the @bash_task decorator that wraps
            this method to create a workflow task.
        """
        return self.environment + textwrap.dedent(
            f"""
            set +e
            echo Started at $(date)
            echo Executing on $(hostname)
            git lfs install --skip-repo
            rm -rf {self.install_path}/metis/build/{self.tag}
            mkdir -p {self.install_path}/metis/build/{self.tag}
            cd {self.install_path}/metis/build/{self.tag}
            # Clone GKlib tools needed by metis
            git clone https://github.com/KarypisLab/GKlib.git
            # Fetch and untar metis tarball
            wget -T 30 -t 3 https://github.com/KarypisLab/METIS/archive/refs/tags/v{self.tag}.tar.gz
            tar -xzf v{self.tag}.tar.gz
            rm -f metis-{self.tag}.tar.gz
            echo Completed at $(date)
            """
        )

    @bash_task
    def _make(
        self,
        *,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        clone: Optional[Future] = None,
    ) -> str:
        """A bash task to build Metis code that has previously been cloned.

        Parameters
        ----------

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
            A string containing the bash script that implements the Metis make
            task. This string is consumed by the @bash_task decorator that wraps
            this method to create a workflow task.
        """
        return self.environment + textwrap.dedent(
            f"""
            set +e
            echo Started at $(date)
            echo Executing on $(hostname)
            cd {self.install_path}/metis/build/{self.tag}/GKlib
            make config prefix={self.install_path}/metis/{self.tag}
            make install
            cd {self.install_path}/metis/build/{self.tag}/METIS-{self.tag}
            make config prefix={self.install_path}/metis/{self.tag}
            make install
            rm -rf {self.install_path}/metis/build
            echo Completed at $(date)
            """
        )

    @join_task
    def _install(
        self,
        *,
        clone_executor: List[str],
        make_executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> Future:
        """A join task to install Metis.

        Parameters
        ----------

        clone_executor: List[str]
            List of names of executors where the clone subtask may execute.

        make_executor: List[str]
            List of names of executors where the make subtask may execute.

        stdout: str | None
            Full path to the file where stdout of the install task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the install task is to be
            written. If not specified, output to stderr will not be captured.

        Returns
        -------

        Future
            A Future that represents the result of the @join_task that
            installs Metis.
        """
        clone = self._clone(
            executor=clone_executor,
            stdout=(stdout, "w"),
            stderr=(stderr, "w"),
        )
        make = self._make(
            executor=make_executor,
            stdout=(stdout, "a"),
            stderr=(stderr, "a"),
            clone=clone,
        )
        return make

    @bash_task
    def _gpmetis(
        self,
        mesh_file: str,
        nprocs: int,
        *,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
    ) -> str:
        """A bash task to Run gpmetis to partition a mesh file for a given number
         of processors.

        Parameters
        ----------

        mesh_file: str
            The full path to the input mesh file to be partitioned.

        nprocs: int
            The number of processors (partitions) required for the output mesh
            file.

        stdout: str | None
            Full path to the file where stdout of the gpmetis task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the gpmetis task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the make or install task
            that must finish successfully before the gpmetis task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.

        Returns
        -------

        str
            A string containing the bash script that implements the Metis gpmetis
            task. This string is consumed by the @bash_task decorator that wraps
            this method to create a workflow task.
        """
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            {self.install_path}/metis/{self.tag}/bin/gpmetis -minconn -contig -niter=200 {mesh_file} {nprocs}
            echo Completed at $(date)
            """
        )
