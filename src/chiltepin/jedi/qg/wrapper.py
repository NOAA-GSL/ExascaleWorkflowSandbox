import textwrap

from parsl.app.app import bash_app, join_app


class QG:

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
            rm -rf {self.install_path}/jedi-bundle/{self.tag}/src
            mkdir -p {self.install_path}/jedi-bundle/{self.tag}
            cd {self.install_path}/jedi-bundle/{self.tag}
            git clone --branch {self.tag} https://github.com/JCSDA/jedi-bundle.git src
            echo Completed at $(date)
            """
            )

        return bash_app(clone, executors=executors)

    def get_configure_task(
        self,
        executors=["service"],
    ):
        def configure(
            stdout=None,
            stderr=None,
            clone=None,
        ):
            return self.environment + textwrap.dedent(
                f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            cd {self.install_path}/jedi-bundle/{self.tag}
            rm -rf build
            mkdir build
            cd build
            # Comment out the parts of the bundle we do not need
            perl -p -i -e 's/(.* PROJECT vader)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.* PROJECT saber)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.* PROJECT ioda)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.* PROJECT crtm)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.* PROJECT ufo)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.* PROJECT gsw)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.* PROJECT fv3)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.* PROJECT femps)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.* PROJECT soca)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.* PROJECT mom6)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.* PROJECT coupling)/#\\1/g' ../src/CMakeLists.txt
            perl -p -i -e 's/(.*mpas)/#\\1/ig' ../src/CMakeLists.txt
            ecbuild -DCMAKE_INSTALL_PREFIX=../ ../src
            echo Completed at $(date)
            """
            )

        return bash_app(configure, executors=executors)

    def get_make_task(
        self,
        executors=["serial"],
    ):
        def make(
            stdout=None,
            stderr=None,
            jobs=8,
            configure=None,
            parsl_resource_specification={"num_nodes": 1},
        ):
            return self.environment + textwrap.dedent(
                f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            spack env list
            spack env deactivate
            cd {self.install_path}/jedi-bundle/{self.tag}/build
            make -j{jobs} VERBOSE=1
            make install
            echo Completed at $(date)
            """
            )

        return bash_app(make, executors=executors)

    def get_install_task(
        self,
        clone_executors=["service"],
        configure_executors=["service"],
        make_executors=["serial"],
    ):
        def install(
            jobs=8,
            stdout=None,
            stderr=None,
        ):
            clone_task = self.get_clone_task(executors=clone_executors)
            configure_task = self.get_configure_task(executors=configure_executors)
            make_task = self.get_make_task(executors=make_executors)

            clone = clone_task(
                stdout=(stdout, "w"),
                stderr=(stderr, "w"),
            )
            configure = configure_task(
                stdout=(stdout, "a"),
                stderr=(stderr, "a"),
                clone=clone,
            )
            make = make_task(
                jobs=jobs,
                stdout=(stdout, "a"),
                stderr=(stderr, "a"),
                configure=configure,
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

    def configure(
        self,
        clone=None,
        stdout=None,
        stderr=None,
        executors=["service"],
    ):
        return self.get_configure_task(executors=executors)(
            stdout=stdout,
            stderr=stderr,
            clone=clone,
        )

    def make(
        self,
        configure=None,
        jobs=8,
        stdout=None,
        stderr=None,
        executors=["serial"],
        parsl_resource_specification={"num_nodes": 1},
    ):
        return self.get_make_task(executors=executors)(
            configure=configure,
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
        configure_executors=["service"],
        make_executors=["serial"],
    ):
        return self.get_install_task(
            clone_executors=clone_executors,
            configure_executors=configure_executors,
            make_executors=make_executors,
        )(
            jobs=jobs,
            stdout=stdout,
            stderr=stderr,
        )
