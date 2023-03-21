#!/bin/env bash

# These can be customized to suit individual needs
DEFAULT_GCC_VERSION=$(gcc --version | head -1 | sed -e 's/([^()]*)//g' | awk '{print $2}')  # Verison of system defauilt gcc
DEFAULT_COMPILER="gcc@${DEFAULT_GCC_VERSION}"  # Default system compiler used to build newer gcc

SPACK_ENV_NAME="radical"         # Name of spack environment to create
SPACK_ENV_COMPILER="gcc@9.4.0"   # Compiler to use to build the spack environment
TARGET_ARCH_OPT="target=x86_64"  # Compiler architecture build target

################################################################################
# help                                                                         #
################################################################################
help()
{
   # Display help
   echo "Installs radical into radical Spack environment"
   echo
   echo "Usage: install_radical.sh"
   echo
}

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
spack env create ${SPACK_ENV_NAME} || true
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

# Install python tools
spack add python@3.9%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack add py-pytest%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack add py-pylint%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack add py-flake8%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack add py-mypy%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack add py-black%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack concretize -f
spack install

# Install radical components
spack add py-radical-entk@1.16.0%${SPACK_ENV_COMPILER} ^python@3.9 ${TARGET_ARCH_OPT}
spack add py-radical-gtod@1.16.0%${SPACK_ENV_COMPILER} ^python@3.9 ${TARGET_ARCH_OPT}
spack add py-radical-pilot@1.16.0%${SPACK_ENV_COMPILER} ^python@3.9 ${TARGET_ARCH_OPT}
spack add py-radical-saga@1.16.0%${SPACK_ENV_COMPILER} ^python@3.9 ${TARGET_ARCH_OPT}
spack add py-radical-utils@1.16.0%${SPACK_ENV_COMPILER} ^python@3.9 ${TARGET_ARCH_OPT}
spack concretize -f
spack install

exit 0
