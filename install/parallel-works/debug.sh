#!/usr/bin/bash
gcc_ver=11
source /opt/rh/gcc-toolset-${gcc_ver}/enable


spack_dir=$HOME/spack-stack
spack_stack_version=1.6.0
git clone -b $spack_stack_version --recursive https://github.com/JCSDA/spack-stack.git $spack_dir

# Create the spack-stack spack.yaml file
. $spack_dir/setup.sh

spack mirror add --s3-access-key-id "" --s3-access-key-secret "" s3_spack_stack_buildcache_ro s3://chiltepin-us-east-2/spack-stack/
if [ -f mirrors.yaml ]; then
  cp mirrors.yaml $spack_dir/spack/etc/spack/mirrors.yaml
fi
spack mirror list

template_name="unified-dev"
spack stack create env --site linux.default --template ${template_name} --name ${template_name}.mylinux

export spack_package_url=https://raw.githubusercontent.com/spack/spack/develop/var/spack/repos/builtin/packages
export spack_package_path=$spack_dir/spack/var/spack/repos/builtin/packages
curl -L ${spack_package_url}/flux-core/package.py -o ${spack_package_path}/flux-core/package.py
#curl -L ${spack_package_url}/flux-sched/package.py -o ${spack_package_path}/flux-sched/package.py
# Get package.py for flux-sched from Spack bigfix PR instead of Spack develop
curl -L https://raw.githubusercontent.com/trws/spack/fix-ver-handling/var/spack/repos/builtin/packages/flux-sched/package.py -o ${spack_package_path}/flux-sched/package.py

pushd $spack_dir/envs/${template_name}.mylinux

perl -p -i -e "s/variants: \+internal-hwloc \+two_level_namespace/variants: \+internal-hwloc \+two_level_namespace \~static/g" common/packages.yaml

## Modify spack.yaml to adjust boost variants for flux compatibility
export boost_variants=$(
cat<<'BOOST_EOF'
      variants: ~atomic +chrono ~clanglibcpp +container ~context ~contract ~coroutine +date_time
        ~debug +exception ~fiber +filesystem +graph ~graph_parallel ~icu ~iostreams ~json
        ~locale ~log ~math ~mpi +multithreaded ~nowide ~numpy +pic +program_options +python
        ~random +regex +serialization +shared ~signals ~singlethreaded ~stacktrace +system
        ~taggedlayout +test +thread +timer ~type_erasure ~versionedlayout ~wave cxxstd=17
        visibility=hidden
BOOST_EOF
)
perl -i -p0e 's/      variants\:.*visibility=hidden/$ENV{boost_variants}/s' common/packages.yaml

spack env activate -p .

spack add py-pip
spack add py-pytest@7.3.2
spack add flux-core@0.58.0
spack add flux-sched@0.32.0
spack add py-flake8@6.1.0
spack add py-pytest-flake8@0.8.1

export SPACK_SYSTEM_CONFIG_PATH="$PWD/site"
# Env vars to work around bug in flux-sched spack package.py file
# Not needed after patch to Spack
#export FLUX_SCHED_VERSION=0.32.0
#export FLUX_SCHED_VER=0.32.0

spack external find --scope system \
    --exclude bison --exclude cmake \
    --exclude curl --exclude openssl \
    --exclude openssh --exclude python

spack external find --scope system wget

# Note - only needed for running JCSDA's
# JEDI-Skylab system (using R2D2 localhost)
spack external find --scope system mysql

# Note - only needed for generating documentation
spack external find --scope system texlive

spack compiler find --scope system

# Done finding external packages, so unset
unset SPACK_SYSTEM_CONFIG_PATH

# Set default compiler and MPI library
spack config add "packages:all:compiler:[gcc@11.2.1]"
spack config add "packages:all:providers:mpi:[openmpi@4.1.6]"

# Set a few more package variants and versions 
# to avoid linker errors and duplicate packages 
# being built
spack config add "packages:fontconfig:variants:+pic"
spack config add "packages:pixman:variants:+pic"
spack config add "packages:cairo:variants:+pic"

spack concretize

spack install --no-check-signature --fail-fast

spack buildcache push --unsigned --update-index s3_spack_stack_buildcache_rw 

# Create tcl module files (replace tcl with lmod?)
spack module tcl refresh -y

# Create meta-modules for compiler, MPI, Python
spack stack setup-meta-modules

# Load modules
module use /home/Christopher.W.Harrop/spack-stack/envs/unified-dev.mylinux/install/modulefiles/Core
module load stack-gcc/11.2.1
module load stack-openmpi/4.1.6
module load stack-python/3.10.13
module load pip

# Install parsl, black, and isort
python -m pip install globus-compute-sdk
python -m pip install globus-compute-endpoint
python -m pip uninstall -y dill pyzmq
python -m pip install dill==0.3.8 pyzmq==25.1.2
python -m pip install parsl[monitoring]==2024.3.4
python -m pip install pytest-black
python -m pip install pytest-isort
