#!/bin/sh

set -e

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

# Set up read-only mirror
spack mirror add --s3-access-key-id "" --s3-access-key-secret "" s3_spack_stack_buildcache_ro s3://chiltepin/spack-stack/
if [ -n "${S3_BUILD_CACHE_KEY}" ]; then
  cat mirrors.in.yaml | envsubst > spack/etc/spack/mirrors.yaml
  chmod 600 spack/etc/spack/mirrors.yaml
fi
spack mirror list

# Add flux, pytest and flake8 to chiltepin spack environment
spack add python
spack add py-pip
spack add py-pytest
spack add flux-core@0.53.0
spack add flux-sched@0.28.0
python -m pip install flake8
python -m flake8 . /src/chiltepin

# Concretize and install the spack packages
spack install --fail-fast --no-check-signature

# Install parsl and flake8
python -m pip install parsl[monitoring]==2023.12.4


# Push the packages to the mirror
if [ "$(spack mirror list | wc -l)" = "3" ]; then
  export AWS_ACCESS_KEY_ID=${S3_BUILD_CACHE_KEY}
  export AWS_SECRET_ACCESS_KEY=${S3_BUILD_CACHE_SECRET_KEY}
  spack buildcache push --unsigned --update-index s3_spack_stack_buildcache_rw
fi
