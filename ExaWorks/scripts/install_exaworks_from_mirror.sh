#!/bin/env bash                                                                                                                                                                      
# These can be customized to suit individual needs                                        
SPACK_ENV_NAME="exaworkssdk"     # Name of spack environment for ExaWorks SDK
DEFAULT_COMPILER="gcc@4.8.5"     # Default system compiler used to build newer gcc
SPACK_ENV_COMPILER="gcc@9.4.0"   # Compiler to use to build ExaWorks  SDK
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
  EXAWORKS_DIR=$1
fi

# Check for existing exaworks mirror
if [[ ! -d ${EXAWORKS_DIR} ]]; then
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

# Configure spack environment
spack env create ${SPACK_ENV_NAME}
spack env activate ${SPACK_ENV_NAME}
spack config add concretizer:unify:true
spack config add concretizer:reuse:false
spack config add config:db_lock_timeout:300
spack config add config:install_tree:padded_length:128
spack compiler find

# Add mirror
spack mirror add exaworks-mirror file://${EXAWORKS_DIR}

# Trust GPG key
spack gpg trust ${EXAWORKS_DIR}/pubring.gpg
spack buildcache keys --install --trust

# Index build cache
spack buildcache update-index --mirror-url file://${EXAWORKS_DIR}

# Install $COMPILER in Spack environment
spack add ${SPACK_ENV_COMPILER} %${DEFAULT_COMPILER} ${TARGET_ARCH_OPT}
spack install
spack compiler add $(spack location -i ${SPACK_ENV_COMPILER})
chmod -fR 02770 ${SPACK_DIR}

# Install exaworks
spack add exaworks%${SPACK_ENV_COMPILER} ^python@3.9 py-pytest%${SPACK_ENV_COMPILER}
spack concretize -f
spack install
chmod -fR 02770 ${SPACK_DIR} || true

exit 0
