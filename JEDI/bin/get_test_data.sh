#!/usr/bin/bash

#SBATCH -A zrtrr 
#SBATCH --time=01:00:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --partition=service
#SBATCH --qos=batch

source /etc/bashrc

# Set location of JEDI source and build
export WORK=/scratch2/BMC/zrtrr/Naureen.Bharwani
#export WORK=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export JEDI_ROOT=${WORK}
export JEDI_SRC=${JEDI_ROOT}/fv3-bundle
export JEDI_BUILD=${JEDI_ROOT}/build

# Setup software environment
. ${WORK}/setupenv-hera.sh

# Run ecbuild
cd ${JEDI_BUILD}
ctest -R get_  > ${JEDI_ROOT}/get_test_data.out 2>&1
