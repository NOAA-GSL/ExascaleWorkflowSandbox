#!//usr/bin/bash

#SBATCH -A gsd-hpcs
#SBATCH --time=00:30:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --partition=service
#SBATCH --qos=batch

source /etc/bashrc

# Get version to install
#export JEDI_VERSION=${1:-develop}

# Set location of JEDI source and build
#export WORK=/work/noaa/gsd-hpcs/charrop/hercules/SENA/JEDI
#export WORK=/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox/JEDI
#export WORK=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export JEDI_ROOT=/work/noaa/gsd-hpcs/charrop/hercules/SENA/ExascaleWorkflowSandbox/JEDI
#export JEDI_SRC=${JEDI_ROOT}/jedi-bundle
export JEDI_SRC=${JEDI_ROOT}/exascale-workflow-bundle
export JEDI_BUILD=${JEDI_ROOT}/build

# Setup software environment
. ${JEDI_ROOT}/bin/setupenv-hercules.sh

# Run ecbuild
rm -rf ${JEDI_BUILD}
mkdir -p ${JEDI_BUILD}
cd ${JEDI_BUILD}
ecbuild -DCMAKE_INSTALL_PREFIX=${JEDI_SRC} ${JEDI_SRC} > ${JEDI_ROOT}/ecbuild.out 2>&1
