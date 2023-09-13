#!//usr/bin/bash

#SBATCH -A gsd-hpcs
#SBATCH --time=00:10:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --partition=service
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

# Make sure git-lfs activated
git lfs install --skip-repo

# Clone jedi-bundle
rm -rf ${JEDI_ROOT}
mkdir -p ${JEDI_ROOT}
cd ${JEDI_ROOT}
git clone --branch ${JEDI_VERSION} https://github.com/JCSDA-internal/jedi-bundle > ${JEDI_ROOT}/clone.out 2>&1
