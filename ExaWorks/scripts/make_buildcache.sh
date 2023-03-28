#!/bin/env bash

# Get mirror install path and name
if [[ $# -ne 2 ]]; then
  help
  exit 1
else
  MIRROR_DIR=$1
  MIRROR_NAME=$2
fi

################################################################################
# help                                                                         #
################################################################################
help()
{
  # Display help
  echo "Creates a buildcache at the location and name specified."
  echo "If the buildcache name is 'bootstrap' a bootstrap cache is created."
  echo
  echo "Usage: make_buildcache.sh <install path> <name>"
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

# Check for existing mirror
if [[ -d ${MIRROR_DIR}/${MIRROR_NAME}_mirror ]]; then
  echo "A mirror already exists at ${MIRROR_DIR}/${MIRROR_NAME}_mirror."
  echo
  echo "Please choose another location or remove ${MIRROR_DIR}/${MIRROR_NAME}_mirror and try again."
  exit 1
fi

# Create empty mirror directory
[[ -d ${MIRROR_DIR}/${MIRROR_NAME}_mirror ]] || mkdir -p ${MIRROR_DIR}/${MIRROR_NAME}_mirror

set -eu

case ${MIRROR_NAME} in

  bootstrap | Bootstrap | BOOTSTRAP)
	
    # Create a boostrap build cache
    spack bootstrap mirror --binary-packages ${MIRROR_DIR}/${MIRROR_NAME}_mirror
    ;;

  *)
      
    # Create build cache for installed environment packages
    spack gpg create --export ${MIRROR_DIR}/${MIRROR_NAME}_mirror/${MIRROR_NAME}key.pub "Foo Bar" "foobar@foobar.com"
    spack buildcache create --allow-root -d ${MIRROR_DIR}/${MIRROR_NAME}_mirror $(spack find --format /{hash})
    ;;

esac

exit 0
