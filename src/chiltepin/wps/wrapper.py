import textwrap

from parsl.app.app import bash_app, join_app


class WPS:

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
            rm -rf {self.install_path}/WPS/{self.tag}
            mkdir -p {self.install_path}/WPS/{self.tag}
            cd {self.install_path}/WPS/{self.tag}
            wget https://github.com/wrf-model/WPS/archive/refs/tags/v{self.tag}.tar.gz
            tar --strip-components=1 -xzf v{self.tag}.tar.gz
            rm -f v{self.tag}.tar.gz
            echo Completed at $(date)
            """
            )

        return bash_app(clone, executors=executors)


    def get_make_task(
        self,
        executors=["compute"],
    ):
        def make(
            stdout=None,
            stderr=None,
            jobs=8,
            clone=None,
            parsl_resource_specification={"num_nodes": 1},
        ):
            return self.environment + textwrap.dedent(
                f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            cd {self.install_path}/WPS/{self.tag}
            export WRF_DIR=../../WRF/{self.tag}
            export JASPERLIB=$jasper_ROOT/lib64
            export JASPERINC=$jasper_ROOT/include
            export NETCDF=$netcdf_fortran_ROOT
            export J="-j {jobs}"
            echo "23" | ./configure
            sed 's:-lnetcdff -lnetcdf:-lnetcdff:' -i configure.wps
            sed 's:mpif90:mpiifort:' -i configure.wps
            sed 's:mpicc:mpiicc:' -i configure.wps
            ./compile
            echo Completed at $(date)
            """
            )

        return bash_app(make, executors=executors)

    def get_install_task(
        self,
        clone_executors=["service"],
        make_executors=["service"],
    ):
        def install(
            jobs=8,
            stdout=None,
            stderr=None,
        ):
            clone_task = self.get_clone_task(executors=clone_executors)
            make_task = self.get_make_task(executors=make_executors)

            clone = clone_task(
                stdout=(stdout, "w"),
                stderr=(stderr, "w"),
            )
            make = make_task(
                jobs=jobs,
                stdout=(stdout, "a"),
                stderr=(stderr, "a"),
                clone=clone,
            )
            return make

        return join_app(install)

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


    def make(
        self,
        clone=None,
        jobs=8,
        stdout=None,
        stderr=None,
        executors=["service"],
        parsl_resource_specification={"num_nodes": 1},
    ):
        return self.get_make_task(executors=executors)(
            clone=clone,
            jobs=jobs,
            stdout=stdout,
            stderr=stderr,
            parsl_resource_specification=parsl_resource_specification,
        )

    def install(
        self,
        jobs=8,
        stdout=None,
        stderr=None,
        clone_executors=["service"],
        make_executors=["service"],
    ):
        return self.get_install_task(
            clone_executors=clone_executors,
            make_executors=make_executors,
        )(
            jobs=jobs,
            stdout=stdout,
            stderr=stderr,
        )

