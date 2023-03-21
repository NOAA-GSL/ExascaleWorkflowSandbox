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

case ${MIRROR_NAME} in

  bootstrap | Bootstrap | BOOTSTRAP)
	
    # Register bootstrap mirror
    spack bootstrap add --trust local-sources ${MIRROR_DIR}/${MIRROR_NAME}_mirror/metadata/sources
    spack bootstrap add --trust local-binaries ${MIRROR_DIR}/${MIRROR_NAME}_mirror/metadata/binaries
    ;;

  *)

    # Add mirror
    spack mirror add ${MIRROR_NAME}_mirror file://${MIRROR_DIR}/${MIRROR_NAME}_mirror

    # Trust GPG key
    spack gpg trust ${MIRROR_DIR}/${MIRROR_NAME}_mirror/${MIRROR_NAME}key.pub
    spack buildcache keys --install --trust

    # Index build cache
    spack buildcache update-index --mirror-url file://${MIRROR_DIR}/${MIRROR_NAME}_mirror
    ;;

esac

exit 0

