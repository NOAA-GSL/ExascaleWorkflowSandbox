module purge
module use /scratch1/NCEPDEV/jcsda/jedipara/spack-stack/modulefiles
module load miniconda/3.9.12
module load ecflow/5.5.3
module load mysql/8.0.31

module use /scratch1/NCEPDEV/nems/role.epic/spack-stack/spack-stack-1.5.0/envs/unified-env/install/modulefiles/Core
module load stack-intel/2021.5.0
module load stack-intel-oneapi-mpi/2021.5.1
module load stack-python/3.10.8

module load jedi-fv3-env/1.0.0
module load soca-env/1.0.0

module unload crtm

module list
