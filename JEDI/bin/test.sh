#!/usr/bin/bash

# Get version to install
export JEDI_VERSION=${1:-develop}

# Set location of JEDI source and build
export WORK=/work/noaa/gsd-hpcs/charrop/hercules/SENA/JEDI
#export WORK=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export JEDI_ROOT=${WORK}/${JEDI_VERSION}
export JEDI_SRC=${JEDI_ROOT}/jedi-bundle
export JEDI_BUILD=${JEDI_ROOT}/build

for r in coupling crtm femps fv3-jedi gsw ioda oops saber soca ufo ufo-data vader; do
  sbatch ctest.sh ${JEDI_VERSION} $r
done
