#!/bin/bash

# Clone spack-stack
spack_stack_version=1.7.0
git clone -b $spack_stack_version --recursive https://github.com/JCSDA/spack-stack.git

# Create the spack-stack spack.yaml file
pushd spack-stack
. ./setup.sh
spack stack create ctr --container=docker-ubuntu-gcc-openmpi --specs=jedi-ci

# Modify spack.yaml to increase parallelism
cd envs/docker-ubuntu-gcc-openmpi
perl -p -i -e "s/build_jobs: 2/build_jobs: 8/g" spack.yaml

# Modify spack.yaml to turn on Slurm support
#perl -p -i -e "s/variants: \+internal-hwloc \+two_level_namespace/variants: \+internal-hwloc \+two_level_namespace \schedulers=slurm/g" spack.yaml

# Modify spack.yaml to install py-pytest, py-flake8, and py-pytest-flake8
#perl -p -i -e "s/# To avoid/py-flake8:\n      version: [6.1.0]\n    # To avoid/g" spack.yaml
#perl -p -i -e "s/# To avoid/py-pytest-flake8:\n      version: [0.8.1]\n    # To avoid/g" spack.yaml
#perl -p -i -e "s/py-pyyaml\@6.0/py-pytest\@7.3.2\n  - py-pyyaml\@6.0/g" spack.yaml
#perl -p -i -e "s/py-pyyaml\@6.0/py-flake8\@6.1.0\n  - py-pyyaml\@6.0/g" spack.yaml
#perl -p -i -e "s/py-pyyaml\@6.0/py-pytest-flake8\@0.8.1\n  - py-pyyaml\@6.0/g" spack.yaml

# Create the spack-stack Dockerfile
spack containerize > ../../../Dockerfile

# If necessary move spack-ext-* for use in COPY during container build
rm -rf ../../../spack-ext-*
find . -type d -name 'spack-ext-*' -exec mv {} ../../../ \;

# Remove unneeded spack-stack install
cp spack.yaml ../../../spack.yaml
popd
rm -rf spack-stack

# Create spack build command patch
export docker_patch=$(
cat<<'END_HEREDOC'
RUN --mount=type=secret,id=mirrors,target=/opt/spack/etc/spack/mirrors.yaml \
    --mount=type=secret,id=access_key_id \
    --mount=type=secret,id=secret_access_key \
    --mount=type=secret,id=session_token <<EOF
  set -e
  cd /opt/spack-environment
  . $SPACK_ROOT/share/spack/setup-env.sh
  spack env activate .
  spack mirror add --s3-access-key-id "" --s3-access-key-secret "" s3_spack_stack_buildcache_ro s3://chiltepin-us-east-2/spack-stack/
  spack install --fail-fast --no-check-signature
  #python -m pip install globus-compute-sdk
  #python -m pip install globus-compute-endpoint
  #python -m pip uninstall -y dill pyzmq
  #python -m pip install dill==0.3.8 pyzmq==25.1.2
  #python -m pip install parsl[monitoring]==2024.6.3
  #python -m pip install pytest-black
  #python -m pip install pytest-isort
  #python -m pip install 'uwtools @ git+https://github.com/ufs-community/uwtools@main#subdirectory=src'
  #python -m pip install pytest==7.4.0
  spack mirror list
  if [ "$(spack mirror list | wc -l)" = "3" ]; then
    export AWS_ACCESS_KEY_ID=$(cat /run/secrets/access_key_id)
    export AWS_SECRET_ACCESS_KEY=$(cat /run/secrets/secret_access_key)
    export AWS_SESSION_TOKEN=$(cat /run/secrets/session_token)
    spack buildcache push --unsigned --update-index s3_spack_stack_buildcache_rw
  fi
  spack gc -y
EOF
END_HEREDOC
)

# Patch the Dockerfile to use buildcache mirrors on AWS S3
perl -p -i -e 's:RUN cd /opt/spack-environment && spack env activate . && spack install --fail-fast && spack gc -y:$ENV{docker_patch}:g' Dockerfile

# Create a patched Dockerfile that only includes Flux packages
# This Dockerfile can be built first so that Flux packages get pushed to binary cache
# This allows the main Dockerfile to build correctly avoiding Spack Flux build bug
#cp Dockerfile Dockerfile.flux-only
#perl -i -p0e "s|&&   echo '    awscli:'.*&&   echo '    flux-core:'|&&   echo '    flux-core:'|s" Dockerfile.flux-only
#perl -i -p0e "s|&&   echo '    fms:'.*?&&   echo ''|&&   echo ''|s" Dockerfile.flux-only
#perl -i -p0e "s|&&   echo '  - base-env.*&&   echo '  - flux-core|&&   echo '  - flux-core|s" Dockerfile.flux-only
#perl -i -p0e "s|&&   echo '  - fms.*?&&   echo ''|&&   echo ''|s" Dockerfile.flux-only
#perl -i -p -e "s|python -m pip install|#python -m pip install|g" Dockerfile.flux-only
#perl -i -p -e "s|python -m pip uninstall|#python -m pip uninstall|g" Dockerfile.flux-only
