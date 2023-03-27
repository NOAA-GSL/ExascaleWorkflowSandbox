#!/bin/env bash

# These can be customized to suit individual needs
DEFAULT_GCC_VERSION=$(gcc --version | head -1 | sed -e 's/([^()]*)//g' | awk '{print $2}')  # Version of system default gcc
DEFAULT_COMPILER="gcc@${DEFAULT_GCC_VERSION}"  # Default system compiler used to build newer gcc

SPACK_ENV_NAME="base"            # Name of spack environment to create
SPACK_ENV_COMPILER="gcc@9.4.0"   # Compiler to use to build the spack environment
TARGET_ARCH_OPT="target=x86_64"  # Compiler architecture build target

################################################################################
# help                                                                         #
################################################################################
help()
{
  # Display help
  echo "Installs a base Spack environment to use for building exaworks packages." 
  echo "This includes: gcc, python, pytest, pylint, flake8, mypy, and black."
  echo
  echo "Usage: install_base.sh"
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

# Configure spack
spack config add concretizer:unify:true
spack config add concretizer:reuse:true
spack config add config:db_lock_timeout:300
spack config add config:install_tree:padded_length:128

# Create a compiler bootstrap environment
spack env create bootstrap || true
spack env activate bootstrap
spack compiler find

# Install bootstrap $COMPILER in bootstrap environment
spack add ${SPACK_ENV_COMPILER} %${DEFAULT_COMPILER} ${TARGET_ARCH_OPT}
spack install

# Get the location of the bootstrap compiler
BOOTSTRAP_COMPILER=$(spack location -i ${SPACK_ENV_COMPILER})

# Create the base environment
spack env create ${SPACK_ENV_NAME} || true
spack env activate ${SPACK_ENV_NAME}
spack compiler add ${BOOTSTRAP_COMPILER}

# Use the boostrap compiler to install the compiler in the base environment
spack add ${SPACK_ENV_COMPILER}%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack concretize
spack install
spack compiler remove ${SPACK_ENV_COMPILER}%${DEFAULT_COMPILER}
spack compiler add $(spack location -i ${SPACK_ENV_COMPILER}%${SPACK_ENV_COMPILER})

# Install python tools
spack add python@3.9%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack add py-pytest%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack add py-pylint%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack add py-flake8%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack add py-mypy%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack add py-black%${SPACK_ENV_COMPILER} ${TARGET_ARCH_OPT}
spack concretize
spack install

# Remove bootstrap environment
spack env deactivate
if [ "${SPACK_ENV_COMPILER}" != "${DEFAULT_COMPILER}" ]; then
  spack env activate bootstrap
  spack uninstall -y ${SPACK_ENV_COMPILER}%${DEFAULT_COMPILER}
  spack gc -y
  spack env deactivate
fi
spack env remove -y bootstrap

exit 0
