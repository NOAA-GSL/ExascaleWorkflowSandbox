#!/bin/bash

#=====================================
# Install spack-stack for use with UFS
#
# Run this script in a gcc-toolset-11
# enabled bash shell to access gcc11,
# i.e.:
#
# scl enable gcc-toolset-11 bash
# ./step_02_spack-stack.sh
#
# Based on the instructions at:
# https://spack-stack.readthedocs.io/en/latest/NewSiteConfigs.html#newsiteconfigs-linux
#=====================================

# Clone spack-stack
#spack_stack_version=1.6.0
#git clone -b $spack_stack_version --recursive https://github.com/JCSDA/spack-stack.git
#
## Create the spack-stack spack.yaml file
#pushd spack-stack
#. ./setup.sh


# Select gcc compiler to use
gcc_ver=11
source /opt/rh/gcc-toolset-${gcc_ver}/enable

# Download Spack, start it, and add the buildcache
# mirror to Spack.

#==========================================
# Step 1: Where do you want to put Spack?

# Default location for spack-stack?
#spack_dir=/contrib

spack_dir=$HOME/spack-stack
spack_stack_version=1.6.0
git clone -b $spack_stack_version --recursive https://github.com/JCSDA/spack-stack.git $spack_dir

# Create the spack-stack spack.yaml file
. $spack_dir/setup.sh

if [ -f mirrors.yaml ]; then
  cp mirrors.yaml $spack_dir/spack/etc/spack/defaults/
fi
spack mirror list


# Try $HOME for now...

#===========================================
# Step 2: Grab Spack

#mkdir -p $spack_dir
#cd $spack_dir

# Standard spack
#git clone -c feature.manyFiles=true https://github.com/spack/spack.git
# source ${PWD}/spack/share/spack/setup-env.sh

# JCSDA spack-stack, UFS is probably at 1.5.1
#git clone --recurse-submodules -b spack-stack-1.6.0 https://github.com/jcsda/spack-stack.git
#cd spack-stack
# Sources Spack from submodule and sets ${SPACK_STACK_DIR}
#source setup.sh

#==========================================
# Step 3: Connect to a buildcache
# Note that here we assume you have already exported
# your cloud bucket credentials into environment
# variables to use a bucket-based buildcache.
# You can replace the s3:// URL here with a path
# if using an attached storage based buildcache.
#spack mirror add aws-mirror s3://$BUCKET_NAME
spack compiler find
#spack buildcache list

#=========================================
# Step 4: Create a Spack environment based
# on the existing template provided by
# spack-stack.

# Very out of date?
#template_name="gfs-v16.2"

#template_name="ufs-weather-model"
template_name="unified-dev"
spack stack create env --site linux.default --template ${template_name} --name ${template_name}.mylinux
pushd $spack_dir/envs/${template_name}.mylinux

# Modify spack.yaml to turn off openmpi static libraries
perl -p -i -e "s/variants: \+internal-hwloc \+two_level_namespace/variants: \+internal-hwloc \+two_level_namespace \~static/g" common/packages.yaml
#
## Modify spack.yaml to increase parallelism
#perl -p -i -e "s/build_jobs: 2/build_jobs: 8/g" spack.yaml
#
## Modify spack.yaml to add flux-core and flux-sched
perl -p -i -e "s/fms:/flux-core:\n      version: [0.58.0]\n    fms:/g" common/packages.yaml
perl -p -i -e "s/fms:/flux-sched:\n      version: [0.32.0]\n    fms:/g" common/packages.yaml
#perl -p -i -e "s/fms\@/flux-core\@0.58.0\n  - fms\@/g" common/packages.yaml
#perl -p -i -e "s/fms\@/flux-sched\@0.32.0\n  - fms\@/g" common/packages.yaml
#
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

# Modify spack.yaml to install py-pytest, py-flake8, and py-pytest-flake8
#perl -p -i -e "s/# To avoid/py-pytest:\n      require: ['\@7.3.2']\n    # To avoid/g" common/packages.yaml
#perl -p -i -e "s/# To avoid/py-flake8:\n      version: [6.1.0]\n    # To avoid/g" common/packages.yaml
#perl -p -i -e "s/# To avoid/py-pytest-flake8:\n      version: [0.8.1]\n    # To avoid/g" common/packages.yaml
#perl -p -i -e "s/py-pyyaml\@6.0/py-pytest\@7.3.2\n  - py-pyyaml\@6.0/g" spack.yaml
#perl -p -i -e "s/py-pyyaml\@6.0/py-flake8\@6.1.0\n  - py-pyyaml\@6.0/g" spack.yaml
#perl -p -i -e "s/py-pyyaml\@6.0/py-pytest-flake8\@0.8.1\n  - py-pyyaml\@6.0/g" spack.yaml

export spack_package_url=https://raw.githubusercontent.com/spack/spack/develop/var/spack/repos/builtin/packages
export spack_package_path=$spack_dir/spack/var/spack/repos/builtin/packages
curl -L ${spack_package_url}/flux-core/package.py -o ${spack_package_path}/flux-core/package.py
curl -L ${spack_package_url}/flux-sched/package.py -o ${spack_package_path}/flux-sched/package.py
spack env activate -p .

spack add flux-core@0.58.0
spack add flux-sched@0.32.0
spack add py-pytest
spack add py-flake8
spack add py-pytest-flake8

#=========================================
# Step 5: Find external packages
# Use SPACK_SYSTEM_CONFIG_PATH to modify site config
# files in envs/${template_name}.mylinux/site
export SPACK_SYSTEM_CONFIG_PATH="$PWD/site"

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

# For JCSDA's JEDI-Skylab experiments using 
# R2D2 with a local MySQL server:
#spack config add "packages:ewok-env:variants:+mysql"

#=====================================
# Step 6: Process the specs and install
# Save the output of concretize in a log file
# so you can inspect that log with show_duplicate_packages.py.
# Duplicate package specifications can cause 
# issues in the module creation step below. 
spack concretize 2>&1 | tee log.concretize
#${SPACK_STACK_DIR}/util/show_duplicate_packages.py -d -c log.concretize
#spack install --verbose --fail-fast 2>&1 | tee log.install
spack install --no-check-signature --fail-fast 2>&1 | tee log.install
exit
# Create tcl module files (replace tcl with lmod?)
spack module tcl refresh

# Create meta-modules for compiler, MPI, Python
spack stack setup-meta-modules

echo "You now have a spack-stack environment" 
echo "that can be accessed by running:"
echo "module use ${SPACK_STACK_DIR}/envs/${template_name}.mylinux/install/modulefiles/Core"
echo "The modules defined here can be loaded" 
echo "to build and run code as described at: "
echo "https://spack-stack.readthedocs.io/en/latest/UsingSpackEnvironments.html#usingspackenvironments"
echo "This script was based on the Linux instructions at: "
echo "https://spack-stack.readthedocs.io/en/latest/NewSiteConfigs.html#newsiteconfigs-linux"
