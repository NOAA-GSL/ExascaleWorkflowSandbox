module purge
module use /work/noaa/epic-ps/role-epic-ps/spack-stack/modulefiles
module load ecflow/5.8.4-hercules
module load mysql/8.0.31-hercules

module use /work/noaa/epic-ps/role-epic-ps/spack-stack/spack-stack-1.4.0-hercules/envs/unified-env-v2/install/modulefiles/Core
module load stack-intel/2021.7.1
module load stack-intel-oneapi-mpi/2021.7.1
module load stack-python/3.9.14

module load jedi-fv3-env/unified-dev
module load ewok-env/unified-dev
module load soca-env/unified-dev

module unload crtm

module list

ulimit -s unlimited
ulimit -v unlimited
export SLURM_EXPORT_ENV=ALL
export HDF5_USE_FILE_LOCKING=FALSE
