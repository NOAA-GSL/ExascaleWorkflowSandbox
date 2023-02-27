#!/bin/env bash

# These can be customized to suit individual needs
DEFAULT_GCC_VERSION=$(gcc --version | head -1 | sed -e 's/([^()]*)//g' | awk '{print $2}')  # Verison of system defauilt gcc
DEFAULT_COMPILER="gcc@${DEFAULT_GCC_VERSION}"  # Default system compiler used to build newer gcc

SPACK_ENV_NAME="exaworkssdk"     # Name of spack environment for ExaWorks SDK
SPACK_ENV_COMPILER="gcc@9.4.0"   # Compiler to use to build ExaWorks  SDK
TARGET_ARCH_OPT="target=x86_64"  # Compiler architecture build target

################################################################################
# help                                                                         #
################################################################################
help()
{
   # Display help
   echo "Installs the exaworks Spack package into exaworkssdk Spack environment"
   echo
   echo "Usage: install_exaworks.sh <exaworks mirror path>"
   echo
}

# Get install path
if [[ $# -ne 1 ]]; then
  help
  exit 1
else
  EXAWORKS_DIR=$1
fi

# Check for existing exaworks mirror
if [[ -d ${EXAWORKS_DIR} ]]; then
  echo "An exaworks mirror already exists at ${EXAWORKS_DIR}."
  echo
  echo "Please choose another location or remove ${EXAWORKS_DIR} and try again."
  exit 1
fi

# Get the location of Spack so we can update permissions
if [[ $(which spack 2>/dev/null) ]]; then
  SPACK_DIR=$(dirname $(dirname $(which spack)))
else
  echo "Cannot find Spack."
  echo
  echo "Please install Spack and/or source Spack's environment setup script: .../spack/share/setup-env.sh"
  echo
  exit 1
fi

set -eu

# Configure spack environment
spack env create ${SPACK_ENV_NAME}
spack env activate ${SPACK_ENV_NAME}
spack config add concretizer:unify:true
spack config add concretizer:reuse:false
spack config add config:db_lock_timeout:300
spack config add config:install_tree:padded_length:128
spack compiler find

# Install $COMPILER in Spack environment
spack add ${SPACK_ENV_COMPILER} %${DEFAULT_COMPILER} ${TARGET_ARCH_OPT}
spack install
spack compiler add $(spack location -i ${SPACK_ENV_COMPILER})
chmod -fR 02770 ${SPACK_DIR}

# Install exaworks
#spack add exaworks%${SPACK_ENV_COMPILER} ^python@3.9 py-pytest%${SPACK_ENV_COMPILER}
spack add rust@1.60.0%gcc@9.4.0+analysis+clippy~rls+rustfmt+src build_system=generic extra_targets=none arch=linux-ubuntu22.04-x86_64
spack concretize -f
spack install
chmod -fR 02770 ${SPACK_DIR} || true

exit 
# Create source mirror
rm -rf ${EXAWORKS_DIR}
spack mirror create -d ${EXAWORKS_DIR} --all

# Create GPG keys
spack gpg create "Christopher Harrop" "<christopher.w.harrop@noaa.gov>"
cp ${SPACK_DIR}/opt/spack/gpg/pubring.* ${EXAWORKS_DIR}

# Create build cache
spack buildcache create --allow-root --force -d ${EXAWORKS_DIR} $(spack find --format /{hash})

exit 0
