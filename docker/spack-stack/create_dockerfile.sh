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

# Remove unneeded spack-stack install
popd
rm -rf spack-stack

# Modify the Dockerfile to use buildcache mirror at our ghcr
perl -p -i -e 's:cd /opt/spack-environment && spack env activate . && spack install --fail-fast && spack gc -y:foobar:g' Dockerfile
perl -p -i -e 's:foobar:foobar1 \\\n&&  foobar2 \\\n&&  foobar3 \\\n&&  foobar4 \\\n&&  foobar5 \\\n&&  foobar6 \\\n&&  foobar7\n:g' Dockerfile
perl -p -i -e 's:foobar1:--mount=type=secret,id=mirrors,target=/opt/spack/etc/spack/mirrors.yaml:g' Dockerfile
perl -p -i -e 's:foobar2:cd /opt/spack-environment:s' Dockerfile
perl -p -i -e 's:foobar3:\. \$SPACK_ROOT/share/spack/setup-env.sh:s' Dockerfile
perl -p -i -e 's:foobar4:spack env activate \.:s' Dockerfile
perl -p -i -e 's:foobar5:spack install --fail-fast --no-check-signature:s' Dockerfile
perl -p -i -e 's:foobar6:spack buildcache push --unsigned ghcr_registry:s' Dockerfile
perl -p -i -e 's:foobar7:spack gc -y:s' Dockerfile
