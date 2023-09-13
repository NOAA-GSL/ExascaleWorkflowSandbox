#!/usr/bin/bash

#SBATCH -A gsd-hpcs
#SBATCH --time=02:00:00
#SBATCH -N 1
#SBATCH -n 24
#SBATCH --partition=hercules
#SBATCH --qos=batch

source /etc/bashrc

# Get version to install
export JEDI_VERSION=${1:-develop}

# Set location of JEDI source and build
export WORK=/work/noaa/gsd-hpcs/charrop/hercules/SENA/JEDI
#export WORK=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export JEDI_ROOT=${WORK}/${JEDI_VERSION}
export JEDI_SRC=${JEDI_ROOT}/jedi-bundle
export JEDI_BUILD=${JEDI_ROOT}/build

# Setup software environment
. ${WORK}/setupenv-hercules.sh

# Run ecbuild
cd ${JEDI_BUILD}
make -j 24 VERBOSE=1 > ${JEDI_ROOT}/make.out 2>&1
