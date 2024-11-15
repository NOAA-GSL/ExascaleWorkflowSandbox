import textwrap
from datetime import datetime

from uwtools.api import config as uwconfig

from chiltepin.tasks import bash_task, join_task


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
            rm -rf {self.install_path}/mpas/{self.tag}
            mkdir -p {self.install_path}/mpas/{self.tag}
            cd {self.install_path}/mpas/{self.tag}
            git clone https://github.com/NOAA-GSL/MPAS-Model.git .
            git checkout {self.tag}
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
        repo_url = "https://raw.githubusercontent.com/NOAA-GSL/ExascaleWorkflowSandbox/"
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

    @bash_task
    def mpas_init(
        self,
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

    @bash_task
    def mpas_forecast(
        self,
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
