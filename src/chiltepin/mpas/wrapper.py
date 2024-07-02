import textwrap

from parsl.app.app import bash_app, join_app


class MPAS:

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
            rm -rf {self.install_path}/mpas/{self.tag}
            mkdir -p {self.install_path}/mpas/{self.tag}
            cd {self.install_path}/mpas/{self.tag}
            git clone https://github.com/NOAA-GSL/MPAS-Model.git .
            git checkout {self.tag}
            echo Completed at $(date)
            """
            )

        return bash_app(clone, executors=executors)


    def get_make_task(
        self,
        executors=["service"],
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
            cd {self.install_path}/mpas/{self.tag}

            make intel-mpi CORE=init_atmosphere
            cp -v init_atmosphere_model ../init_atmosphere_model.exe
            make clean CORE=init_atmosphere -j {jobs}

            make intel-mpi CORE=atmosphere                                                                                                                                                                                                                      
            cp -v atmosphere_model ../atmosphere_model.exe                                                                                                                                                                                                    
            make clean CORE=atmosphere -j {jobs}                                                                                                                                                                                                           

            echo Completed at $(date)
            """
            )

        return bash_app(make, executors=executors)

#    def get_install_task(
#        self,
#        clone_executors=["service"],
#        configure_executors=["service"],
#        make_executors=["serial"],
#    ):
#        def install(
#            jobs=8,
#            stdout=None,
#            stderr=None,
#        ):
#            clone_task = self.get_clone_task(executors=clone_executors)
#            configure_task = self.get_configure_task(executors=configure_executors)
#            make_task = self.get_make_task(executors=make_executors)
#
#            clone = clone_task(
#                stdout=(stdout, "w"),
#                stderr=(stderr, "w"),
#            )
#            configure = configure_task(
#                stdout=(stdout, "a"),
#                stderr=(stderr, "a"),
#                clone=clone,
#            )
#            make = make_task(
#                jobs=jobs,
#                stdout=(stdout, "a"),
#                stderr=(stderr, "a"),
#                configure=configure,
#            )
#            return make
#
#        return join_app(install)

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

#    def install(
#        self,
#        jobs=8,
#        stdout=None,
#        stderr=None,
#        clone_executors=["service"],
#        configure_executors=["service"],
#        make_executors=["serial"],
#    ):
#        return self.get_install_task(
#            clone_executors=clone_executors,
#            configure_executors=configure_executors,
#            make_executors=make_executors,
#        )(
#            jobs=jobs,
#            stdout=stdout,
#            stderr=stderr,
#        )

