import textwrap

from parsl.app.app import bash_app, join_app
from uwtools.api import config as uwconfig
from datetime import datetime


class LimitedArea:

    def __init__(
        self,
        environment="",
        install_path="./",
        tag="develop",
    ):
        self.environment = environment
        self.install_path = install_path
        self.tag = tag

    def get_clone_task(
        self,
        executors=["service"],
    ):
        def clone(
            stdout=None,
            stderr=None,
        ):

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

        return bash_app(clone, executors=executors)


    def get_install_task(
        self,
        clone_executors=["service"],
    ):
        def install(
            stdout=None,
            stderr=None,
        ):
            clone_task = self.get_clone_task(executors=clone_executors)

            clone = clone_task(
                stdout=(stdout, "w"),
                stderr=(stderr, "w"),
            )
            return clone

        return join_app(install)

    def get_create_region_task(
        self,
        executors=["service"],
    ):
        def create_region(
            resolution,
            region,
            stdout=None,
            stderr=None,
            parsl_resource_specification={},
        ):
            resolution_cells={
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
            static_url="https://www2.mmm.ucar.edu/projects/mpas/atmosphere_meshes"

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
            {self.install_path}/mpas-limited-area/{self.tag}/create_region {self.install_path}/mpas-limited-area/{self.tag}/docs/points-examples/{region}.custom.pts x1.{resolution_cells[resolution]}.static.nc
            echo Completed at $(date)
            """
            )

        return bash_app(create_region, executors=executors)


    def clone(
        self,
        stdout=None,
        stderr=None,
        executors=["service"],
    ):
        return self.get_clone_task(executors=executors)(
            stdout=stdout,
            stderr=stderr,
        )

    def install(
        self,
        stdout=None,
        stderr=None,
        clone_executors=["service"],
    ):
        return self.get_install_task(
            clone_executors=clone_executors,
        )(
            stdout=stdout,
            stderr=stderr,
        )

    def create_region(
        self,
        resolution,
        region,
        stdout=None,
        stderr=None,
        executors=["service"],
    ):
        return self.get_create_region_task(executors=executors)(
            resolution,
            region,
            stdout=stdout,
            stderr=stderr,
        )
