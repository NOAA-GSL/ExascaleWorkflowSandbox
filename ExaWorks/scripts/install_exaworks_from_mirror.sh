#!/bin/env bash                                                                                                                                                                      
# These can be customized to suit individual needs
DEFAULT_GCC_VERSION=$(gcc --version | head -1 | sed -e 's/([^()]*)//g' | awk '{print $2}')  # Version of system default gcc
DEFAULT_COMPILER="gcc@${DEFAULT_GCC_VERSION}"  # Default system compiler used to build newer gcc

SPACK_ENV_NAME="exaworkssdk"     # Name of spack environment to create
SPACK_ENV_COMPILER="gcc@9.4.0"   # Compiler to use to build the spack environment
TARGET_ARCH_OPT="target=x86_64"  # Compiler architecture build target


################################################################################
# help                                                                         #
################################################################################
help()
{
   # Display help
   echo "Installs the exaworks Spack package into exaworkssdk Spack environment"
   echo "using a Spack source mirror or build-cache"
   echo
   echo "Usage: install_exaworks_from_mirror.sh <exaworks mirror path>"
   echo
}

# Get mirror path
if [[ $# -ne 1 ]]; then
  help
  exit 1
else
  MIRROR_DIR=$1
fi

# Check for existing exaworks mirror
if [[ ! -d ${MIRROR_DIR} ]]; then
  echo "An exaworks mirror does not exist at ${EXAWORKS_DIR}."
  echo
  echo "Please choose another location or copy the mirror to ${EXAWORKS_DIR} and try again."
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

# Activate the build caches
./activate_buildcache.sh ${MIRROR_DIR} bootstrap
./activate_buildcache.sh ${MIRROR_DIR} compiler-bootstrap
./activate_buildcache.sh ${MIRROR_DIR} base
./activate_buildcache.sh ${MIRROR_DIR} exaworks

# Install exaworks
./install_bootstrap.sh
./install_base.sh
./install_exaworks.sh

exit 0
