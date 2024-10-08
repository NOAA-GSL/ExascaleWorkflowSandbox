import textwrap
from datetime import datetime

from parsl.app.app import bash_app, join_app
from uwtools.api import config as uwconfig


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
            repo_url = (
                "https://raw.githubusercontent.com/NOAA-GSL/ExascaleWorkflowSandbox/"
            )
            patch_url = repo_url + "main/apps/mpas/patches"
            return self.environment + textwrap.dedent(
                f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            cd {self.install_path}/mpas/{self.tag}
            mkdir exe
            export PIO=$parallelio_ROOT
            curl -L {patch_url}/src.framework.Makefile.patch -o src.framework.Makefile.patch
            patch -p 0 < src.framework.Makefile.patch
            compiler=$(basename $CC)
            # Set the MPAS build target to match compiler
            if [[ $compiler = "gcc" ]]; then
              build_target="gfortran"
            elif [[ $compiler = "icc" ]]; then
              build_target="intel-mpi"
            else
              echo "Unsupported compiler: $CC"
              exit 1
            fi
            make $build_target CORE=init_atmosphere -j {jobs}
            cp -v init_atmosphere_model exe/
            make clean CORE=init_atmosphere

            make $build_target CORE=atmosphere -j {jobs}
            cp -v atmosphere_model exe/

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

    def get_mpas_init_task(
        self,
        executors=["mpi"],
    ):
        def mpas_init(
            config_path,
            cycle_str,
            key_path,
            stdout=None,
            stderr=None,
            install=None,
            parsl_resource_specification={},
        ):

            cycle = datetime.fromisoformat(cycle_str)

            # Extract driver config from experiment config
            expt_config = uwconfig.get_yaml_config(config_path)
            expt_config.dereference(context={"cycle": cycle, **expt_config})

            return self.environment + textwrap.dedent(
                f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            export PATH=$PATH:.
            uw mpas_init provisioned_run_directory --cycle {cycle_str} \
               --config-file {config_path} --key-path {key_path} --verbose
            cd {expt_config[key_path]['mpas_init']['run_dir']}
            echo "Run Command: '$PARSL_MPI_PREFIX {self.install_path}/mpas/{self.tag}/exe/init_atmosphere_model'"
            $PARSL_MPI_PREFIX --overcommit {self.install_path}/mpas/{self.tag}/exe/init_atmosphere_model
            echo Completed at $(date)
            """
            )

        return bash_app(mpas_init, executors=executors)

    def get_mpas_forecast_task(
        self,
        executors=["mpi"],
    ):
        def mpas_forecast(
            config_path,
            cycle_str,
            key_path,
            stdout=None,
            stderr=None,
            install=None,
            parsl_resource_specification={},
        ):

            cycle = datetime.fromisoformat(cycle_str)

            # Extract driver config from experiment config
            expt_config = uwconfig.get_yaml_config(config_path)
            expt_config.dereference(context={"cycle": cycle, **expt_config})

            return self.environment + textwrap.dedent(
                f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            export PATH=$PATH:.
            uw mpas provisioned_run_directory --cycle {cycle_str} \
                --config-file {config_path} --key-path {key_path} --verbose
            cd {expt_config[key_path]['mpas']['run_dir']}
            echo "Run Command: '$PARSL_MPI_PREFIX {self.install_path}/mpas/{self.tag}/exe/atmosphere_model'"
            $PARSL_MPI_PREFIX --overcommit {self.install_path}/mpas/{self.tag}/exe/atmosphere_model
            echo Completed at $(date)
            """
            )

        return bash_app(mpas_forecast, executors=executors)

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

    def mpas_init(
        self,
        config_path,
        cycle_str,
        key_path,
        stdout=None,
        stderr=None,
        install=None,
        executors=["mpi"],
        parsl_resource_specification={
            "num_nodes": 1,  # Number of nodes required for the application instance
            "num_ranks": 4,  # Number of ranks in total
            "ranks_per_node": 4,  # Number of MPI ranks per node
        },
    ):
        return self.get_mpas_init_task(executors=executors)(
            config_path,
            cycle_str,
            key_path,
            stdout=stdout,
            stderr=stderr,
            install=install,
            parsl_resource_specification=parsl_resource_specification,
        )

    def mpas_forecast(
        self,
        config_path,
        cycle_str,
        key_path,
        stdout=None,
        stderr=None,
        install=None,
        executors=["mpi"],
        parsl_resource_specification={
            "num_nodes": 1,  # Number of nodes required for the application instance
            "num_ranks": 32,  # Number of ranks in total
            "ranks_per_node": 32,  # Number of MPI ranks per node
        },
    ):
        return self.get_mpas_forecast_task(executors=executors)(
            config_path,
            cycle_str,
            key_path,
            stdout=stdout,
            stderr=stderr,
            install=install,
            parsl_resource_specification=parsl_resource_specification,
        )
