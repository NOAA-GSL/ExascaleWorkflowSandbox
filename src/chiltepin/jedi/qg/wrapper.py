import textwrap

from chiltepin.tasks import bash_task, join_task


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
            rm -rf {self.install_path}/jedi-bundle/{self.tag}/src
            mkdir -p {self.install_path}/jedi-bundle/{self.tag}
            cd {self.install_path}/jedi-bundle/{self.tag}
            git clone --branch {self.tag} https://github.com/JCSDA/jedi-bundle.git src
            echo Completed at $(date)
            """
        )

    @bash_task
    def configure(
        self,
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

    @bash_task
    def make(
        self,
        jobs=8,
        stdout=None,
        stderr=None,
        configure=None,
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

    @join_task
    def install(
        self,
        jobs=8,
        stdout=None,
        stderr=None,
        clone_executor="service",
        configure_executor="service",
        make_executor="compute",
    ):
        clone = self.clone(
            stdout=(stdout, "w"),
            stderr=(stderr, "w"),
            executor=clone_executor,
        )
        configure = self.configure(
            stdout=(stdout, "a"),
            stderr=(stderr, "a"),
            executor=configure_executor,
            clone=clone,
        )
        make = self.make(
            jobs=jobs,
            stdout=(stdout, "a"),
            stderr=(stderr, "a"),
            executor=make_executor,
            configure=configure,
        )
        return make
