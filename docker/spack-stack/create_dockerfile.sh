#!/bin/bash

# Clone spack-stack develop branch
git clone -b develop --recursive https://github.com/JCSDA/spack-stack.git

# Create the spack-stack spack.yaml file
pushd spack-stack
. ./setup.sh
spack stack create ctr --container=docker-ubuntu-gcc-openmpi --specs=jedi-ci

# Modify spack.yaml to turn off openmpi static libraries
cd envs/docker-ubuntu-gcc-openmpi
perl -p -i -e "s/variants: \+internal-hwloc \+two_level_namespace/variants: \+internal-hwloc \+two_level_namespace \~static/g" spack.yaml

# Create the spack-stack Dockerfile
spack containerize > ../../../Dockerfile

# Implement workarounds so that container can build under qemu
# See https://github.com/spack/spack/issues/41639
perl -p -i -e 's:RUN cd /opt/spack-environment && spack env activate:RUN . \$SPACK_ROOT/share/spack/setup-env.sh && cd /opt/spack-environment && spack env activate:g' ../../../Dockerfile
perl -p -i -e 's:spack env activate --sh:. \$SPACK_ROOT/share/spack/setup-env.sh && \\\n    spack env activate --sh:s' ../../../Dockerfile

# Remove unneeded spack-stack install
popd
rm -rf spack-stack
