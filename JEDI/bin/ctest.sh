#!/usr/bin/bash

#SBATCH -A zrtrr 
#SBATCH --time=08:00:00
#SBATCH -N 1
#SBATCH --partition=hera
#SBATCH --qos=batch

source /etc/bashrc

# Get repository to test
export TEST_REPO=$2

# Run ecbuild
cd ${JEDI_BUILD}/${TEST_REPO}
ctest -E get_  --timeout=3600 --rerun-failed --output-on-failure > ${JEDI_ROOT}/ctest.${TEST_REPO}.out 2>&1
