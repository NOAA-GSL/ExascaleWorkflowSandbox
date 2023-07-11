#!/bin/env bash

# These can be customized to suit individual needs
DEFAULT_GCC_VERSION=$(gcc --version | head -1 | sed -e 's/([^()]*)//g' | awk '{print $2}')  # Version of system default gcc
DEFAULT_COMPILER="gcc@${DEFAULT_GCC_VERSION}"  # Default system compiler used to build newer gcc

SPACK_ENV_NAME="base"            # Name of spack environment to create
SPACK_ENV_COMPILER="gcc@11.2.0"  # Compiler to use to build the spack environment
TARGET_ARCH_OPT="target=x86_64"  # Compiler architecture build target

################################################################################
# help                                                                         #
################################################################################
help()
{
  # Display help
  echo "Installs a bootstrap compiler built by the default system compiler into a bootstrap environment."
  echo "This bootstrap compiler can then be used to build other packages without incurring"
  echo "dependencies on the system default compiler."
  echo
  echo "Usage: install_bootstrap.sh"
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
spack add ${SPACK_ENV_COMPILER}%${DEFAULT_COMPILER} ${TARGET_ARCH_OPT}
spack install

exit 0
