#!/bin/sh

export SPACK_VERSION=develop

# Install Spack via repository clone
git clone -c feature.manyFiles=true -c core.sharedRepository=true https://github.com/spack/spack.git
pushd spack
git checkout ${SPACK_VERSION}
popd

# Initialize spack
. spack/share/spack/setup-env.sh

# Create and activate chiltepin environment
spack env create chiltepin
spack env activate chiltepin

# Add flux and pytest to chiltepin environment
spack add python
spack add py-pip
spack add py-pytest
spack add flux-core@0.53.0
spack add flux-sched@0.28.0

# Concretize and install
spack install

# Install parsl
python -m pip install parsl[monitoring]==2023.12.4

