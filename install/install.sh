#!/usr/bin/env bash

set -e

profile=$1

export SPACK_VERSION=develop

# Install Spack via repository clone
git clone -c feature.manyFiles=true -c core.sharedRepository=true https://github.com/spack/spack.git
pushd spack
git checkout ${SPACK_VERSION}
popd

# Initialize spack
. spack/share/spack/setup-env.sh

# Configure spack
spack config add concretizer:unify:true
spack config add concretizer:reuse:true
spack config add config:db_lock_timeout:300
spack config add config:install_tree:padded_length:128

# Create and activate chiltepin environment
spack env create chiltepin
spack env activate chiltepin

# Set up read-only mirror
spack mirror add --s3-access-key-id "" --s3-access-key-secret "" s3_spack_stack_buildcache_ro s3://chiltepin-us-east-2/spack-stack/
if [ -n "${profile}" ]; then
  source ./get_sso_credentials.sh $profile
  cp mirrors.yaml spack/etc/spack/mirrors.yaml
  chmod 600 spack/etc/spack/mirrors.yaml
fi
spack mirror list

# Add flux, pytest and flake8 to chiltepin spack environment
spack add python@3.10.13
spack add py-pip
spack add flux-core@0.58.0
spack add flux-sched@0.32.0
spack add py-flake8@6.1.0
spack add py-pytest-flake8@0.8.1

# Concretize and install the spack packages 
spack install --fail-fast --no-check-signature --deprecated

# Install parsl, black, and isort
python -m pip install globus-compute-sdk
python -m pip install globus-compute-endpoint
python -m pip uninstall -y dill pyzmq
python -m pip install dill==0.3.8 pyzmq==25.1.2
python -m pip install parsl[monitoring]==2024.4.8
python -m pip install pytest-black
python -m pip install pytest-isort
python -m pip install 'uwtools @ git+https://github.com/ufs-community/uwtools@main#subdirectory=src'
python -m pip install pytest==7.3.2

# Push the packages to the mirror
if [ "$(spack mirror list | wc -l)" = "3" ]; then
  spack buildcache push --unsigned --update-index s3_spack_stack_buildcache_rw
fi
