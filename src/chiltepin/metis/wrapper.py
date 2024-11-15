import textwrap

from chiltepin.tasks import bash_task, join_task

class Metis:

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
    def clone(self, stdout=None, stderr=None):
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
    def make(self, stdout=None, stderr=None, clone=None):
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
    def install(self, stdout=None, stderr=None, clone_executor="service", make_executor="service"):
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
    def gpmetis(self, mesh_file, nprocs, stdout=None, stderr=None, install=None):
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            {self.install_path}/metis/{self.tag}/bin/gpmetis -minconn -contig -niter=200 {mesh_file} {nprocs}
            echo Completed at $(date)
            """
        )
