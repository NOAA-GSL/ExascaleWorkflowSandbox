import textwrap

from chiltepin.tasks import bash_task, join_task


class WRF:

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
    def clone(
        self,
        stdout=None,
        stderr=None,
    ):
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            git lfs install --skip-repo
            rm -rf {self.install_path}/WRF/{self.tag}
            mkdir -p {self.install_path}/WRF/{self.tag}
            cd {self.install_path}/WRF/{self.tag}
            wget https://github.com/wrf-model/WRF/releases/download/v{self.tag}/v{self.tag}.tar.gz
            tar --strip-components=1 -xzf v{self.tag}.tar.gz
            rm -f v{self.tag}.tar.gz
            echo Completed at $(date)
            """
        )

    @bash_task
    def make(
        self,
        jobs=8,
        stdout=None,
        stderr=None,
        clone=None,
    ):
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            cd {self.install_path}/WRF/{self.tag}
            export J="-j {jobs}"
            echo "15" | ./configure
            ./compile em_real
           echo Completed at $(date)
            """
        )

    @join_task
    def install(
        self,
        jobs=8,
        stdout=None,
        stderr=None,
        clone_executor="service",
        make_executor="service",
    ):
        clone = self.clone(
            stdout=(stdout, "w"),
            stderr=(stderr, "w"),
            executor=clone_executor,
        )
        make = self.make(
            jobs=jobs,
            stdout=(stdout, "a"),
            stderr=(stderr, "a"),
            executor=make_executor,
            clone=clone,
        )
        return make
