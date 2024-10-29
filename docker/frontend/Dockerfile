FROM ghcr.io/noaa-gsl/dockerslurmcluster/slurm-frontend:latest

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

SHELL ["/bin/bash", "-c"]

COPY cc.patch.aarch64 /tmp
COPY cc.patch.x86_64 /tmp
COPY openmpi.package.py.patch.aarch64 /tmp
COPY openmpi.package.py.patch.x86_64 /tmp


RUN --mount=type=secret,id=access_key_id --mount=type=secret,id=secret_access_key --mount=type=secret,id=session_token <<EOF
  set -e

  # Install OS packages
  apt-get -yqq update
  apt-get -yqq upgrade
  apt-get -yqq install --no-install-recommends \
        awscli \
        bc \
        build-essential \
        ca-certificates \
        curl \
	emacs \
        file \
        g++ \
        gcc \
        gfortran \
        git \
        gnupg2 \
        iproute2 \
        locales \
        make \
        mercurial \
        python3 \
        python3-pip \
        python3-setuptools \
        subversion \
	tcl-dev \
        unzip \
        zstd
  pip3 install boto3
  rm -rf /var/lib/apt/lists/*
  
  # Install Lua
  wget https://sourceforge.net/projects/lmod/files/lua-5.1.4.9.tar.bz2
  tar xvfj lua-5.1.4.9.tar.bz2
  pushd lua-5.1.4.9
  ./configure --prefix=/usr
  make -j 4
  make install
  popd

  # Install Lmod
  git clone --recursive https://github.com/TACC/Lmod.git
  pushd Lmod
  ./configure --prefix=/usr
  make -j 4
  make install
  popd
  rm -rf lua* Lmod
  echo "source /usr/lmod/lmod/init/bash" >> /etc/bash.bashrc

  # Install spack-stack
  cd /opt
  git clone -b release/1.8.0 --recurse-submodules https://github.com/jcsda/spack-stack.git
  pushd spack-stack
  . ./setup.sh
  pushd spack
  cp /tmp/cc.patch.$(uname -m) cc.patch
  cp /tmp/openmpi.package.py.patch.$(uname -m) openmpi.package.py.patch
  patch -f -p0 < openmpi.package.py.patch
  patch -f -p0 < cc.patch
  popd
  spack stack create env --site linux.default --template unified-dev --name unified-env --compiler gcc
  pushd envs/unified-env
  spack env activate .
  spack mirror add --s3-access-key-id "" --s3-access-key-secret "" s3_spack_stack_buildcache_ro s3://chiltepin-us-east-2/spack-stack/
  if [ -f /run/secrets/access_key_id ]; then
    export AWS_ACCESS_KEY_ID=$(cat /run/secrets/access_key_id)
    export AWS_SECRET_ACCESS_KEY=$(cat /run/secrets/secret_access_key)
    export AWS_SESSION_TOKEN=$(cat /run/secrets/session_token)
    spack mirror add --s3-access-key-id $AWS_ACCESS_KEY_ID --s3-access-key-secret $AWS_SECRET_ACCESS_KEY --s3-access-token $AWS_SESSION_TOKEN --autopush --unsigned s3_spack_stack_buildcache_rw s3://chiltepin-us-east-2/spack-stack/
  fi
  export SPACK_SYSTEM_CONFIG_PATH="$PWD/site"
  spack external find --scope system \
  --exclude cmake \
  --exclude curl \
  --exclude openssl \
  --exclude openssh \
  --exclude python
  spack external find --scope system wget
  spack compiler find --scope system
  unset SPACK_SYSTEM_CONFIG_PATH
  spack config add "packages:all:compiler:[gcc@11.4.0]"
  #spack config add "packages:all:providers:mpi:[openmpi@5.0.3]"
  spack config add "packages:all:providers:mpi:[openmpi@4.1.6]"
  spack config add "packages:fontconfig:variants:+pic"
  spack config add "packages:pixman:variants:+pic"
  spack config add "packages:cairo:variants:+pic"
  #spack config --scope env:/opt/spack-stack/envs/unified-env:common add "packages:openmpi:require:@4.1.6 ~internal-hwloc +two_level_namespace schedulers=slurm +pmi"
  spack config --scope env:/opt/spack-stack/envs/unified-env:common add "packages:openmpi:require:~internal-hwloc +two_level_namespace schedulers=slurm +pmi"
  echo "  slurm:" >> /opt/spack-stack/envs/unified-env/site/packages.yaml
  echo "    externals:" >> /opt/spack-stack/envs/unified-env/site/packages.yaml
  echo "    - spec: slurm@23.11.7" >> /opt/spack-stack/envs/unified-env/site/packages.yaml
  echo "      prefix: /usr" >> /opt/spack-stack/envs/unified-env/site/packages.yaml
  echo "    buildable: false" >> /opt/spack-stack/envs/unified-env/site/packages.yaml
  sed -i 's/tcl/lmod/g' site/modules.yaml
  sed -i 's/tcl/lmod/g' common/modules.yaml
  sed -i 's:{^mpi.name}/{^mpi.version}/{compiler.name}/{compiler.version}/{name}:{name}:' common/modules.yaml
  sed -i 's:{compiler.name}/{compiler.version}/{name}:{name}:' common/modules.yaml
  spack concretize 2>&1 | tee log.concretize
  spack mirror list
  spack install --no-check-signature 2>&1 | tee log.install
  if [ -f /run/secrets/access_key_id ]; then  
    spack buildcache update-index s3_spack_stack_buildcache_rw
  fi
  source /usr/lmod/lmod/init/bash
  spack module lmod refresh -y
  spack stack setup-meta-modules
  spack gc -y
  rm -rf ~/.spack 
EOF
