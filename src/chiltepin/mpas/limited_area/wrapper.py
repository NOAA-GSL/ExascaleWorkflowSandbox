import textwrap

from chiltepin.tasks import bash_task


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

    @bash_task
    def install(self, stdout=None, stderr=None):
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
    def create_region(self, resolution, region, stdout=None, stderr=None, install=None):
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
