#!/bin/env bash                                                                                                                                                                                                              

################################################################################
# help                                                                         #
################################################################################
help()
{
   # Display help
   echo "Installs Spack"
   echo
   echo "Usage: install_spack.sh <install path>"
   echo
}

# Get install path
if [[ $# -ne 1 ]]; then
  help
  exit 1
else
  SPACK_DIR=$1
fi

# Check for existing Spack configuration
if [[ -d ~/.spack ]]; then
  echo "Spack may already be installed."
  echo
  echo  "To reinstall Spack, please remove the existing configuration directory ~/.spack and try again"
  exit 1
fi

# Check for existing Spack installation
if [[ -d ${SPACK_DIR} ]]; then
  echo "A Spack installation already exists at ${SPACK_DIR}."
  echo
  echo "Please choose another location or remove ${SPACK_DIR} and try again."
  exit 1
fi

# Create empty installation directory
[[ -d ${SPACK_DIR} ]] || mkdir -p ${SPACK_DIR}

# Install Spack via repository clone
git clone https://github.com/spack/spack.git ${SPACK_DIR}
chmod -fR 02770 ${SPACK_DIR}/spack || true
. ${SPACK_DIR}/share/spack/setup-env.sh

exit 0
