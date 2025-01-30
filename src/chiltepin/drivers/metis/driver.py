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

    @bash_task
    def clone(
        self,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> str:
        """Clone the Metis repository.

        The repository will be cloned into ``<install_path>/metis/build/<tag>/``.

        Parameters
        ----------

        stdout: str | None
            Full path to the file where stdout of the clone task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the clone task is to be
            written. If not specified, output to stderr will not be captured.
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
    def make(
        self,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        clone: Optional[Future] = None,
    ) -> str:
        """Build the Metis code that have previously been cloned.

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
    def install(
        self,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        clone_executor: List[str] = ["service"],
        make_executor: List[str] = ["service"],
    ):
        """Clone and build Metis.

        Parameters
        ----------

        stdout: str | None
            Full path to the file where stdout of the install task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the install task is to be
            written. If not specified, output to stderr will not be captured.

        clone_executor: List[str]
            A list of executors where the clone subtask is allowed to execute.

        make_executor: List[str]
            A list of executors where the make subtask is allowed to execute.
        """
        clone = self.clone(
            stdout=(stdout, "w"),
            stderr=(stderr, "w"),
            executor=clone_executor,
        )
        make = self.make(
            stdout=(stdout, "a"),
            stderr=(stderr, "a"),
            executor=make_executor,
            clone=clone,
        )
        return make

    @bash_task
    def gpmetis(
        self,
        mesh_file: str,
        nprocs: int,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
    ):
        """Run gpmetis to partition a mesh file for a given number of processors.

        Parameters
        ----------

        mesh_file: str
            The full path to the input mesh file to be partitioned.

        nprocs: int
            The number of processors (partitions) required for the output mesh
            file.

        stdout: str | None
            Full path to the file where stdout of the install task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the install task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the make or install  task
            that must finish successfully before the gpmetis task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.
        """
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            {self.install_path}/metis/{self.tag}/bin/gpmetis -minconn -contig -niter=200 {mesh_file} {nprocs}
            echo Completed at $(date)
            """
        )
