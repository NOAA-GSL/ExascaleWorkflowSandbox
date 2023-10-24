#!/usr/bin/bash

#SBATCH -A zrtrr 
#SBATCH --time=08:00:00
#SBATCH -N 1
#SBATCH --partition=hera
#SBATCH --qos=batch

source /etc/bashrc

# Get repository to test
export TEST_REPO=$2

# Set location of JEDI source and build
export WORK=/scratch2/BMC/zrtrr/Naureen.Bharwani
#export WORK=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
export JEDI_ROOT=${WORK}
export JEDI_SRC=${JEDI_ROOT}/fv3-bundle
export JEDI_BUILD=${JEDI_ROOT}/build

# Setup software environment
. ${WORK}/setupenv-hera.sh

# Run ecbuild
cd ${JEDI_BUILD}/${TEST_REPO}
ctest -E get_  --timeout=3600 --rerun-failed --output-on-failure > ${JEDI_ROOT}/ctest.${TEST_REPO}.out 2>&1
