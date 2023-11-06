#!/usr/bin/bash

#SBATCH -A zrtrr 
#SBATCH --time=01:00:00
#SBATCH -N 1
#SBATCH -n 1
#SBATCH --partition=service
#SBATCH --qos=batch

source /etc/bashrc

# Run ecbuild
cd ${JEDI_BUILD}
ctest -R get_  > ${JEDI_ROOT}/get_test_data.out 2>&1
