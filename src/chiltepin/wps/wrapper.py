import textwrap

from chiltepin.tasks import bash_task, join_task


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

    @bash_task
    def clone(self, stdout=None, stderr=None):
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

    @bash_task
    def make(self, WRF_dir=None, jobs=8, stdout=None, stderr=None, clone=None):
        if WRF_dir is None:
            no_wrf = "--nowrf"
        else:
            no_wrf = ""
        repo_url = "https://raw.githubusercontent.com/spack/"
        patch_url = repo_url + "spack/develop/var/spack/repos/builtin/packages/wps"
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            cd {self.install_path}/WPS/{self.tag}
            export WRF_DIR={WRF_dir}
            # Jasper may be in /lib or /lib64
            export JASPERLIB=$(dirname $(find -L $jasper_ROOT -name libjasper.so))
            export JASPERINC=$jasper_ROOT/include
            export NETCDF=$netcdf_c_ROOT
            export NETCDFF=$netcdf_fortran_ROOT
            export J="-j {jobs}"
            curl -L {patch_url}/patches/4.2/arch.Config.pl.patch -o arch.Config.pl.patch
            curl -L {patch_url}/patches/4.2/preamble.patch -o preamble.patch
            curl -L {patch_url}/patches/4.4/configure.patch -o configure.patch
            patch -p 1 < arch.Config.pl.patch
            patch -p 1 < preamble.patch
            patch -p 1 < configure.patch
            os=$(uname -m)
            if [[ $os = "aarch64" ]]; then
              curl -L {patch_url}/for_aarch64.patch -o configure.aarch64.patch
              patch -p 1 < configure.aarch64.patch
            fi
            compiler=$(basename $CC)
            # Set the WPS build option to match compiler
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

    @join_task
    def install(
        self,
        WRF_dir=None,
        jobs=None,
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
            WRF_dir=WRF_dir,
            stdout=(stdout, "a"),
            stderr=(stderr, "a"),
            executor=make_executor,
            clone=clone,
        )
        return make

    @bash_task
    def ungrib(self, config_path, cycle_str, stdout=None, stderr=None, install=None):
        return self.environment + textwrap.dedent(
            f"""
            echo Started at $(date)
            echo Executing on $(hostname)
            export PATH=$PATH:.
            uw ungrib run --cycle {cycle_str} --config-file {config_path} --key-path prepare_grib --verbose
            echo Completed at $(date)
            """
        )
