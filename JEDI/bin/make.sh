#!/usr/bin/bash

#SBATCH -A zrtrr
#SBATCH --time=02:00:00
#SBATCH -N 1
#SBATCH -n 24
#SBATCH --partition=hera
#SBATCH --qos=batch

source /etc/bashrc

# Run ecbuild
cd ${JEDI_BUILD}
make -j 24 VERBOSE=1 > ${JEDI_ROOT}/make.out 2>&1
make install >> ${JEDI_ROOT}/make.out 2>&1
