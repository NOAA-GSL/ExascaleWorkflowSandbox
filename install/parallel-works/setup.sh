#!/usr/bin/bash

module purge
module unuse /usr/share/Modules/modulefiles
module unuse /usr/share/modulefiles
module use /home/Christopher.W.Harrop/spack-stack/envs/unified-dev.mylinux/install/modulefiles/Core
module load stack-gcc
module load stack-openmpi
module load stack-python

module load jedi-fv3-env
module load flux-sched
