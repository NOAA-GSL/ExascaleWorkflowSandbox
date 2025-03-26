import textwrap
from concurrent.futures import Future
from typing import List, Optional

from chiltepin.tasks import bash_task


class LimitedArea:
    """Chiltepin task drivers for installing and running LimitedArea.

    Parameters
    ----------

    environment: List[str] | None
        A list of bash environment commands to run before executing LimitedArea
        tasks. These commands are run after the execution resource's environment
        settings have been applied. If None (the default), no environment setup
        commands are run.

    install_path: str | None
        The installation path for LimitedArea. If None (the default) the current
        working directory is used.

    tag: str | None
        The tag of LimitedArea to use. If None (the default) "develop" will be
        used to clone and install LimitedArea.
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

    def install(
        self,
        *,
        executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> Future:
        """Install LimitedArea

        Schedules and executes a workflow task to install the LimitedArea code.
        This is a non-blocking call that returns a Future representing the
        eventual result of the install operation.

        Parameters
        ----------

        executor: List[str]
            List of names of executors where the install task may execute.

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
            executor=executor,
            stdout=stdout,
            stderr=stderr,
        )

    def create_region(
        self,
        resolution: float,
        region: str,
        *,
        executor: List[str],
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
    ) -> Future:
        """Run create_region to create an MPAS grid for the specified region
        and resolution.

        Parameters
        ----------

        resolution: float
            The horizontal resolution in Km. Must be one of (480, 384, 240, 120,
            60, 48, 30, 24, 15, 12, 10, 7.5, 5, 4, 3.75, 3)

        region: str
            The name of the grid region. Currently supported values: "conus".

        executor: List[str]
            List of names of executors where the create_region task may execute.

        stdout: str | None
            Full path to the file where stdout of the create_region task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the create_region task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the install task that must
            finish successfully before the create_region task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.

        Returns
        -------

        Future
            The future result of the create_region task's execution
        """
        return self._create_region(
            resolution=resolution,
            region=region,
            executor=executor,
            stdout=stdout,
            stderr=stderr,
            install=install,
        )

    @bash_task
    def _install(
        self,
        *,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> str:
        """A bash task to install LimitedArea.

        Parameters
        ----------

        stdout: str | None
            Full path to the file where stdout of the install task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the install task is to be
            written. If not specified, output to stderr will not be captured.

        Returns
        -------

        str
            A string containing the bash script that implements the LimitedArea
            install task. This string is consumed by the @bash_task decorator
            that wraps this method to create a workflow task.
        """
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            git lfs install --skip-repo
            rm -rf {self.install_path}/mpas-limited-area/{self.tag}
            mkdir -p {self.install_path}/mpas-limited-area/{self.tag}
            cd {self.install_path}/mpas-limited-area/{self.tag}
            wget https://github.com/MPAS-Dev/MPAS-Limited-Area/archive/refs/tags/v{self.tag}.tar.gz
            tar --strip-components=1 -xzf v{self.tag}.tar.gz
            rm -f v{self.tag}.tar.gz
            echo Completed at $(date)
            """
        )

    @bash_task
    def _create_region(
        self,
        resolution: float,
        region: str,
        *,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
        install: Optional[Future] = None,
    ) -> str:
        """A bash task to run create_region to create an MPAS grid for the
        specified region and resolution.

        Parameters
        ----------

        resolution: float
            The horizontal resolution in Km. Must be one of (480, 384, 240, 120,
            60, 48, 30, 24, 15, 12, 10, 7.5, 5, 4, 3.75, 3)

        region: str
            The name of the grid region. Currently supported values: "conus".

        stdout: str | None
            Full path to the file where stdout of the create_region task is to be
            written. If not specified, output to stdout will not be captured.

        stderr: str | None
            Full path to the file where stderr of the create_region task is to be
            written. If not specified, output to stderr will not be captured.

        install: Future | None
            A future that represents the results of the install task that must
            finish successfully before the create_region task can execute.
            If left unspecified (the default), no dependency for this task will
            be enforced.

        Returns
        -------

        str
            A string containing the bash script that implements the LimitedArea
            create_region task. This string is consumed by the @bash_task
            decorator that wraps this method to create a workflow task.
        """
        resolution_cells = {
            480: 2562,
            384: 4002,
            240: 10242,
            120: 40962,
            60: 163842,
            48: 256002,
            30: 655362,
            24: 1024002,
            15: 2621442,
            12: 4096002,
            10: 5898242,
            7.5: 10485762,
            5: 23592962,
            4: 36864002,
            3.75: 41943042,
            3: 65536002,
        }

        static_url = "https://www2.mmm.ucar.edu/projects/mpas/atmosphere_meshes"

        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            echo downloading static files
            rm -rf {self.install_path}/mesh-data
            mkdir {self.install_path}/mesh-data
            cd {self.install_path}/mesh-data
            wget {static_url}/x1.{resolution_cells[resolution]}_static.tar.gz
            tar -xzf x1.{resolution_cells[resolution]}_static.tar.gz
            rm -rf x1.{resolution_cells[resolution]}_static.tar.gz
            {self.install_path}/mpas-limited-area/{self.tag}/create_region \
                {self.install_path}/mpas-limited-area/{self.tag}/docs/points-examples/{region}.custom.pts \
                x1.{resolution_cells[resolution]}.static.nc
            echo Completed at $(date)
            """
        )
