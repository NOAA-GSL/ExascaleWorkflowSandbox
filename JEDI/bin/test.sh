#!/usr/bin/bash

# Set location of JEDI source and build
export WORK=/scratch2/BMC/zrtrr/Naureen.Bharwani
#export WORK=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export JEDI_ROOT=${WORK}
export JEDI_SRC=${JEDI_ROOT}/fv3-bundle
export JEDI_BUILD=${JEDI_ROOT}/build

for r in crtm femps fv3-jedi gsw ioda oops saber soca ufo ufo-data vader; do
  sbatch ctest.sh ${WORK} $r
done
