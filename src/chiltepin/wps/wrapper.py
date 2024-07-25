import textwrap

from parsl.app.app import bash_app, join_app, python_app
from uwtools.api import config as uwconfig
from uwtools.api import ungrib as ungrib_driver
from datetime import datetime
import yaml

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
            WRF_dir=None,
            jobs=8,
            clone=None,
            parsl_resource_specification={"num_nodes": 1},
        ):
            if WRF_dir is None:
                no_wrf="--nowrf"
            else:
                no_wrf=""
            patch_url="https://raw.githubusercontent.com/spack/spack/develop/var/spack/repos/builtin/packages/wps/patches"
            return self.environment + textwrap.dedent(
                f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            cd {self.install_path}/WPS/{self.tag}
            export WRF_DIR={WRF_dir}
            export JASPERLIB=$jasper_ROOT/lib64
            export JASPERINC=$jasper_ROOT/include
            export NETCDF=$netcdf_c_ROOT
            export NETCDFF=$netcdf_fortran_ROOT
            export J="-j {jobs}"
            curl -L {patch_url}/4.2/arch.Config.pl.patch -o arch.Config.pl.patch
            curl -L {patch_url}/4.2/preamble.patch -o preamble.patch
            curl -L {patch_url}/4.4/configure.patch -o configure.patch
            patch -p 1 < arch.Config.pl.patch
            patch -p 1 < preamble.patch
            patch -p 1 < configure.patch
            compiler=$(basename $CC)
            if [[ $compiler = "gcc" ]]; then
              build_option=3
            elif [[ $compiler = "icc" ]]; then
              sed 's:mpicc:mpiicc:' -i configure.wps
              sed 's:mpif90:mpiifort:' -i configure.wps
              build_option=19
            else
              echo "Unsupported compiler: $CC"
              exit 1
            fi
            echo $build_option | ./configure {no_wrf}
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
            WRF_dir=None,
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
                WRF_dir=WRF_dir,
                stdout=(stdout, "a"),
                stderr=(stderr, "a"),
                clone=clone,
            )
            return make

        return join_app(install)

    def get_ungrib_task(
        self,
        executors=["compute"],
    ):
        def ungrib(
            config_path,
            cycle_str,
            stdout=None,
            stderr=None,
        ):

            cycle = datetime.fromisoformat(cycle_str)

            # Extract driver config from experiment config
            #expt_config = uwconfig.get_yaml_config(config_path)
            #expt_config.dereference(context={"cycle": cycle, **expt_config})

            # Run ungrib
            #ungrib_driver.execute(task="run", config=config_path, cycle=cycle,
            #                      key_path=["prepare_grib"])

            return self.environment + textwrap.dedent(
                f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            export PATH=$PATH:.
            uw ungrib run --cycle {cycle_str} --config-file {config_path} --key-path prepare_grib --verbose
            echo Completed at $(date)
            """
            )

        #return python_app(ungrib, executors=executors)
        return bash_app(ungrib, executors=executors)

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
        WRF_dir=None,
        stdout=None,
        stderr=None,
        executors=["service"],
        parsl_resource_specification={"num_nodes": 1},
    ):
        return self.get_make_task(executors=executors)(
            clone=clone,
            jobs=jobs,
            WRF_dir=WRF_dir,
            stdout=stdout,
            stderr=stderr,
            parsl_resource_specification=parsl_resource_specification,
        )

    def install(
        self,
        jobs=8,
        WRF_dir=None,
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
            WRF_dir=WRF_dir,
            stdout=stdout,
            stderr=stderr,
        )

    def ungrib(
        self,
        config_path,
        cycle_str,
        stdout=None,
        stderr=None,
        executors=["compute"],
    ):
        return self.get_ungrib_task(executors=executors)(
            config_path,
            cycle_str,
            stdout=stdout,
            stderr=stderr,
        )
