#!/bin/bash

# Clone spack-stack
spack_stack_version=1.7.0
git clone -b $spack_stack_version --recursive https://github.com/JCSDA/spack-stack.git

# Create the spack-stack spack.yaml file
pushd spack-stack
. ./setup.sh
spack stack create ctr --container=docker-ubuntu-gcc-openmpi --specs=jedi-ci

# Create the spack-stack Dockerfile
cd envs/docker-ubuntu-gcc-openmpi
spack containerize > ../../../Dockerfile

# If necessary move spack-ext-* for use in COPY during container build
rm -rf ../../../spack-ext-*
find . -type d -name 'spack-ext-*' -exec mv {} ../../../ \;

# Remove unneeded spack-stack install
popd
rm -rf spack-stack

# Patch the Dockerfile to add our customizations
patch -p1 < Dockerfile.patch
