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

# Modify spack.yaml to increase parallelism
perl -p -i -e "s/build_jobs: 2/build_jobs: 8/g" spack.yaml

# Modify spack.yaml to add flux-core and flux-sched
perl -p -i -e "s/fms:/flux-core:\n      version: [0.53.0]\n    fms:/g" spack.yaml
perl -p -i -e "s/fms:/flux-sched:\n      version: [0.28.0]\n    fms:/g" spack.yaml
perl -p -i -e "s/fms\@/flux-core\@0.53.0\n  - fms\@/g" spack.yaml
perl -p -i -e "s/fms\@/flux-sched\@0.28.0\n  - fms\@/g" spack.yaml

# Modify spack.yaml to adjust boost variants for flux compatibility
export boost_variants=$(
cat<<'BOOST_EOF'
      variants: ~atomic +chrono ~clanglibcpp +container ~context ~contract ~coroutine +date_time
        ~debug +exception ~fiber +filesystem +graph ~graph_parallel ~icu ~iostreams ~json
        ~locale ~log ~math ~mpi +multithreaded ~nowide ~numpy +pic +program_options +python
        ~random +regex +serialization +shared ~signals ~singlethreaded ~stacktrace +system
        ~taggedlayout +test +thread +timer ~type_erasure ~versionedlayout ~wave cxxstd=17
        visibility=hidden
BOOST_EOF
)
perl -i -p0e 's/      variants\:.*visibility=hidden/$ENV{boost_variants}/s' spack.yaml

# Modify spack.yaml to install py-pytest
perl -p -i -e "s/# To avoid/py-pytest:\n      require: ['\@7.3.2']\n    # To avoid/g" spack.yaml
perl -p -i -e "s/py-pyyaml\@6.0/py-pytest\@7.3.2\n  - py-pyyaml\@6.0/g" spack.yaml

# Create the spack-stack Dockerfile
spack containerize > ../../../Dockerfile

# Remove unneeded spack-stack install
popd
rm -rf spack-stack

# Create spack build command patch
export docker_patch=$(
cat<<'END_HEREDOC'
RUN --mount=type=secret,id=mirrors,target=/opt/spack/etc/spack/mirrors.yaml <<EOF
  set -e
  cd /opt/spack-environment
  . $SPACK_ROOT/share/spack/setup-env.sh
  spack env activate .
  spack mirror add --s3-access-key-id "" --s3-access-key-secret "" s3_spack_stack_buildcache_ro s3://chiltepin/spack-stack/
  spack install --fail-fast --no-check-signature
  python -m pip install parsl[monitoring]==2023.12.4
  spack mirror list
  if [ "$(spack mirror list | wc -l)" = "3" ]; then
    spack buildcache push --unsigned --update-index s3_spack_stack_buildcache_rw
  fi
  spack gc -y
EOF
END_HEREDOC
)

# Patch the Dockerfile to use buildcache mirrors on AWS S3
perl -p -i -e 's:RUN cd /opt/spack-environment && spack env activate . && spack install --fail-fast && spack gc -y:$ENV{docker_patch}:g' Dockerfile
