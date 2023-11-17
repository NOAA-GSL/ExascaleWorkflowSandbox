FROM ubuntu:20.04 as bootstrap

ENV SPACK_ROOT=/opt/spack \
    CURRENTLY_BUILDING_DOCKER_IMAGE=1 \
    container=docker

ENV DEBIAN_FRONTEND=noninteractive   \
    LANGUAGE=en_US.UTF-8 \
    LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8

RUN apt-get -yqq update \
 && apt-get -yqq upgrade \
 && apt-get -yqq install --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        file \
        g++ \
        gcc \
        gfortran \
        git \
        gnupg2 \
        iproute2 \
        locales \
        make \
        python3 \
        python3-pip \
        python3-setuptools \
        unzip \
 && locale-gen en_US.UTF-8 \
 && pip3 install boto3 \
 && rm -rf /var/lib/apt/lists/*

RUN mkdir $SPACK_ROOT && cd $SPACK_ROOT && \
    git clone https://github.com/jcsda/spack . && git fetch origin spack-stack-1.5.1:container_branch && git checkout container_branch  && \
    mkdir -p $SPACK_ROOT/opt/spack

RUN ln -s $SPACK_ROOT/share/spack/docker/entrypoint.bash \
          /usr/local/bin/docker-shell \
 && ln -s $SPACK_ROOT/share/spack/docker/entrypoint.bash \
          /usr/local/bin/interactive-shell \
 && ln -s $SPACK_ROOT/share/spack/docker/entrypoint.bash \
          /usr/local/bin/spack-env

RUN mkdir -p /root/.spack \
 && cp $SPACK_ROOT/share/spack/docker/modules.yaml \
        /root/.spack/modules.yaml \
 && rm -rf /root/*.* /run/nologin $SPACK_ROOT/.git

# [WORKAROUND]
# https://superuser.com/questions/1241548/
#     xubuntu-16-04-ttyname-failed-inappropriate-ioctl-for-device#1253889
RUN [ -f ~/.profile ]                                               \
 && sed -i 's/mesg n/( tty -s \\&\\& mesg n || true )/g' ~/.profile \
 || true


WORKDIR /root
SHELL ["docker-shell"]

# Creates the package cache
RUN spack bootstrap now && spack spec hdf5+mpi

ENTRYPOINT ["/bin/bash", "/opt/spack/share/spack/docker/entrypoint.bash"]
CMD ["interactive-shell"]

# Build stage with Spack pre-installed and ready to be used
FROM bootstrap as builder

# Install OS packages needed to build the software
RUN apt-get -yqq update && apt-get -yqq upgrade \
 && apt-get -yqq install bc cpp g++ gcc gfortran git git-lfs make mysql-server qt5-default libqt5svg5-dev qt5dxcb-plugin wget \
 && rm -rf /var/lib/apt/lists/*


# What we want to install and how we want to install it
# is specified in a manifest file (spack.yaml)
RUN mkdir /opt/spack-environment \
&&  (echo spack: \
&&   echo '  concretizer:' \
&&   echo '    unify: true' \
&&   echo '  view: /opt/view' \
&&   echo '' \
&&   echo '  config:' \
&&   echo '    checksum: false' \
&&   echo '    build_jobs: 2' \
&&   echo '    connect_timeout: 60' \
&&   echo '' \
&&   echo '    install_tree: /opt/software' \
&&   echo '  compilers:' \
&&   echo '  - compiler:' \
&&   echo '      spec: gcc@9.4.0' \
&&   echo '      paths:' \
&&   echo '        cc: /usr/bin/gcc' \
&&   echo '        cxx: /usr/bin/g++' \
&&   echo '        f77: /usr/bin/gfortran' \
&&   echo '        fc: /usr/bin/gfortran' \
&&   echo '      flags: {}' \
&&   echo '      operating_system: ubuntu20.04' \
&&   echo '      modules: []' \
&&   echo '      environment: {}' \
&&   echo '      extra_rpaths: []' \
&&   echo '' \
&&   echo '  # Basic package config from configs/common/packages.yaml' \
&&   echo '  # Additional package config for container' \
&&   echo '  packages:' \
&&   echo '    all:' \
&&   echo '      require: '"'"'%gcc'"'"'' \
&&   echo '      target: [x86_64]' \
&&   echo '      providers:' \
&&   echo '        mpi: [openmpi@4.1.5]' \
&&   echo '        blas: [openblas]' \
&&   echo '        fftw-api: [fftw]' \
&&   echo '        gl: [opengl]' \
&&   echo '        glu: [openglu]' \
&&   echo '        jpeg: [libjpeg-turbo]' \
&&   echo '        lapack: [openblas]' \
&&   echo '        yacc: [bison]' \
&&   echo '      compiler: [gcc@9.4.0]' \
&&   echo '    gcc:' \
&&   echo '      buildable: false' \
&&   echo '      externals:' \
&&   echo '      - spec: gcc@9.4.0' \
&&   echo '        prefix: /usr' \
&&   echo '    # Try this next time, already used for clang/intel' \
&&   echo '    #gmake:' \
&&   echo '    #  buildable: false' \
&&   echo '    #  externals:' \
&&   echo '    #  - spec: gmake@4.2.1' \
&&   echo '    #    prefix: /usr' \
&&   echo '    diffutils:' \
&&   echo '      buildable: false' \
&&   echo '      externals:' \
&&   echo '      - spec: diffutils@3.7' \
&&   echo '        prefix: /usr' \
&&   echo '    git:' \
&&   echo '      buildable: false' \
&&   echo '      externals:' \
&&   echo '      - spec: git@2.25.1~tcltk' \
&&   echo '        prefix: /usr' \
&&   echo '    git-lfs:' \
&&   echo '      buildable: false' \
&&   echo '      externals:' \
&&   echo '      - spec: git-lfs@2.9.2' \
&&   echo '        prefix: /usr' \
&&   echo '    mysql:' \
&&   echo '      buildable: false' \
&&   echo '      externals:' \
&&   echo '      - spec: mysql@8.0.32' \
&&   echo '        prefix: /usr' \
&&   echo '    qt:' \
&&   echo '      buildable: false' \
&&   echo '      externals:' \
&&   echo '      - spec: qt@5.12.8' \
&&   echo '        prefix: /usr' \
&&   echo '      version: [5.15.3]' \
&&   echo '    wget:' \
&&   echo '      buildable: false' \
&&   echo '      externals:' \
&&   echo '      - spec: wget@1.20.3' \
&&   echo '        prefix: /usr' \
&&   echo '      version: [1.21.2]' \
&&   echo '    awscli:' \
&&   echo '      version: [1.27.84]' \
&&   echo '    bacio:' \
&&   echo '      version: [2.4.1]' \
&&   echo '    bison:' \
&&   echo '      version: [3.8.2]' \
&&   echo '    boost:' \
&&   echo '      version: [1.78.0]' \
&&   echo '      variants: ~atomic +chrono +date_time +exception +filesystem ~graph ~iostreams' \
&&   echo '        ~locale ~log ~math ~mpi ~numpy +pic +program_options +python ~random +regex' \
&&   echo '        +serialization ~signals +system +test +thread +timer ~wave cxxstd=17 visibility=hidden' \
&&   echo '    bufr:' \
&&   echo '      version: [12.0.1]' \
&&   echo '      variants: +python' \
&&   echo '    cairo:' \
&&   echo '      variants: +pic' \
&&   echo '    # Newer versions of CDO require the C++-17 standard, which doesn'"'"'t' \
&&   echo '    # work with all compilers that are currently in use in spack-stack' \
&&   echo '    # When making changes here, also check Hercules/Casper site configs' \
&&   echo '    cdo:' \
&&   echo '      version: [2.0.5]' \
&&   echo '      variants: ~openmp' \
&&   echo '    cmake:' \
&&   echo '      version: [3.23.1]' \
&&   echo '      variants: +ownlibs' \
&&   echo '    # Attention - when updating also check the various jcsda-emc-bundles env packages' \
&&   echo '    crtm:' \
&&   echo '      version: [2.4.0]' \
&&   echo '      variants: +fix' \
&&   echo '    ecbuild:' \
&&   echo '      version: [3.7.2]' \
&&   echo '    eccodes:' \
&&   echo '      version: [2.27.0]' \
&&   echo '      variants: +png' \
&&   echo '    ecflow:' \
&&   echo '      version: [5.8.4]' \
&&   echo '      variants: +ui' \
&&   echo '    eckit:' \
&&   echo '      version: [1.24.4]' \
&&   echo '      variants: linalg=eigen,lapack compression=lz4,bzip2' \
&&   echo '    ecmwf-atlas:' \
&&   echo '      version: [0.35.0]' \
&&   echo '      variants: +fckit +ectrans +tesselation +fftw' \
&&   echo '    ectrans:' \
&&   echo '      version: [1.2.0]' \
&&   echo '      variants: ~mkl +fftw' \
&&   echo '    eigen:' \
&&   echo '      version: [3.4.0]' \
&&   echo '    esmf:' \
&&   echo '      version: [8.5.0]' \
&&   echo '      variants: ~xerces ~pnetcdf snapshot=none ~shared +external-parallelio' \
&&   echo '      require:' \
&&   echo '      - any_of: [fflags="-fp-model precise" cxxflags="-fp-model precise"]' \
&&   echo '        when: '"'"'%intel'"'"'' \
&&   echo '        message: Extra ESMF compile options for Intel' \
&&   echo '      - any_of: ['"'"''"'"']' \
&&   echo '        when: '"'"'%gcc'"'"'' \
&&   echo '        message: Extra ESMF compile options for GCC' \
&&   echo '    fckit:' \
&&   echo '      version: [0.11.0]' \
&&   echo '      variants: +eckit' \
&&   echo '    fftw:' \
&&   echo '      version: [3.3.10]' \
&&   echo '    fiat:' \
&&   echo '      version: [1.2.0]' \
&&   echo '    fms:' \
&&   echo '      #version: ['"'"'2023.01'"'"']' \
&&   echo '      #variants: precision=32,64 +quad_precision +gfs_phys +openmp +pic constants=GFS build_type=Release' \
&&   echo '      version: [2023.02.01]' \
&&   echo '      variants: precision=32,64 +quad_precision +gfs_phys +openmp +pic constants=GFS' \
&&   echo '        build_type=Release +use_fmsio' \
&&   echo '    fontconfig:' \
&&   echo '      variants: +pic' \
&&   echo '    freetype:' \
&&   echo '      variants: +pic' \
&&   echo '    g2:' \
&&   echo '      version: [3.4.5]' \
&&   echo '    g2c:' \
&&   echo '      version: [1.6.4]' \
&&   echo '    g2tmpl:' \
&&   echo '      version: [1.10.2]' \
&&   echo '    gfsio:' \
&&   echo '      version: [1.4.1]' \
&&   echo '    gftl-shared:' \
&&   echo '      version: [1.6.1]' \
&&   echo '    grib-util:' \
&&   echo '      version: [1.3.0]' \
&&   echo '    gsibec:' \
&&   echo '      version: [1.1.3]' \
&&   echo '    gsi-ncdiag:' \
&&   echo '      version: [1.1.2]' \
&&   echo '    gsl-lite:' \
&&   echo '      version: [0.37.0]' \
&&   echo '    hdf:' \
&&   echo '      version: [4.2.15]' \
&&   echo '      variants: +external-xdr ~fortran ~netcdf' \
&&   echo '    hdf5:' \
&&   echo '      version: [1.14.0]' \
&&   echo '      variants: +hl +fortran +mpi ~threadsafe +szip' \
&&   echo '    ip:' \
&&   echo '      version: [4.3.0]' \
&&   echo '    ip2:' \
&&   echo '      version: [1.1.2]' \
&&   echo '    jasper:' \
&&   echo '      version: [2.0.32]' \
&&   echo '    jedi-cmake:' \
&&   echo '      version: [1.4.0]' \
&&   echo '    jpeg:' \
&&   echo '      version: [9.1.0]' \
&&   echo '    landsfcutil:' \
&&   echo '      version: [2.4.1]' \
&&   echo '    libjpeg-turbo:' \
&&   echo '      version: [2.1.0]' \
&&   echo '    libpng:' \
&&   echo '      version: [1.6.37]' \
&&   echo '      variants: +pic' \
&&   echo '    libyaml:' \
&&   echo '      version: [0.2.5]' \
&&   echo '    mapl:' \
&&   echo '      # 2.35.2 goes with esmf@8.4.2, 2.40.3 goes with esmf@8.5.0' \
&&   echo '      # turn off ~pflogger and extdata2g to avoid compilation' \
&&   echo '      # errors with intel@2021.7.0+, see' \
&&   echo '      # https://github.com/JCSDA/spack-stack/issues/769' \
&&   echo '      # also: ... extdata2g segfault UFS?' \
&&   echo '      version: [2.40.3]' \
&&   echo '      variants: ~shared ~extdata2g ~pflogger' \
&&   echo '    # If making changes here, also check the Discover site config and the CI workflows' \
&&   echo '    met:' \
&&   echo '      version: [11.1.0]' \
&&   echo '      variants: +python +grib2' \
&&   echo '    metplus:' \
&&   echo '      version: [5.1.0]' \
&&   echo '    mpich:' \
&&   echo '      variants: ~hwloc +two_level_namespace' \
&&   echo '    nco:' \
&&   echo '      version: [5.0.6]' \
&&   echo '      variants: ~doc' \
&&   echo '    # ncview - when adding information here, also check Orion' \
&&   echo '    # and Discover site configs' \
&&   echo '    nemsio:' \
&&   echo '      version: [2.5.4]' \
&&   echo '    nemsiogfs:' \
&&   echo '      version: [2.5.3]' \
&&   echo '    nccmp:' \
&&   echo '      version: [1.9.0.1]' \
&&   echo '    ncio:' \
&&   echo '      version: [1.1.2]' \
&&   echo '    netcdf-c:' \
&&   echo '      version: [4.9.2]' \
&&   echo '      # If using 4.9.1, turn off byterange variant to fix compile error: ~byterange' \
&&   echo '      variants: +dap +mpi ~parallel-netcdf' \
&&   echo '    netcdf-cxx4:' \
&&   echo '      version: [4.3.1]' \
&&   echo '    netcdf-fortran:' \
&&   echo '      version: [4.6.0]' \
&&   echo '    nlohmann-json:' \
&&   echo '      version: [3.10.5]' \
&&   echo '    nlohmann-json-schema-validator:' \
&&   echo '      version: [2.1.0]' \
&&   echo '    odc:' \
&&   echo '      version: [1.4.6]' \
&&   echo '      variants: ~fortran' \
&&   echo '    openblas:' \
&&   echo '      version: [0.3.19]' \
&&   echo '      variants: +noavx512' \
&&   echo '    openmpi:' \
&&   echo '      variants: +internal-hwloc +two_level_namespace ~static' \
&&   echo '    # Pin openssl to avoid duplicate packages being built' \
&&   echo '    openssl:' \
&&   echo '      version: [1.1.1u]' \
&&   echo '      variants: +shared' \
&&   echo '    p4est:' \
&&   echo '      version: ['"'"'2.8'"'"']' \
&&   echo '    parallelio:' \
&&   echo '      version: [2.5.10]' \
&&   echo '      variants: +pnetcdf' \
&&   echo '    parallel-netcdf:' \
&&   echo '      version: [1.12.2]' \
&&   echo '    pixman:' \
&&   echo '      variants: +pic' \
&&   echo '    # Do not build pkgconf - https://github.com/jcsda/spack-stack/issues/123' \
&&   echo '    pkgconf:' \
&&   echo '      buildable: false' \
&&   echo '    prod-util:' \
&&   echo '      version: [1.2.2]' \
&&   echo '    proj:' \
&&   echo '      version: [8.1.0]' \
&&   echo '      variants: ~tiff' \
&&   echo '    # Check site configs for the following systems when making changes here:' \
&&   echo '    # Derecho, Narwhal, Gaea-C5' \
&&   echo '    python:' \
&&   echo '      version: [3.10.8]' \
&&   echo '    py-attrs:' \
&&   echo '      # https://github.com/JCSDA/spack-stack/issues/740' \
&&   echo '      version: [21.4.0]' \
&&   echo '    py-cartopy:' \
&&   echo '      variants: +plotting' \
&&   echo '    py-click:' \
&&   echo '      version: [8.0.3]' \
&&   echo '    py-cryptography:' \
&&   echo '      version: [3.3.2]' \
&&   echo '    py-eccodes:' \
&&   echo '      version: [1.4.2]' \
&&   echo '    py-h5py:' \
&&   echo '      version: [3.7.0]' \
&&   echo '      variants: ~mpi' \
&&   echo '    # Comment out for now until build problems are solved' \
&&   echo '    # https://github.com/jcsda/spack-stack/issues/522' \
&&   echo '    # see also ewok-env virtual package and container' \
&&   echo '    # README.md' \
&&   echo '    #py-mysql-connector-python:' \
&&   echo '    #  version: ['"'"'8.0.32'"'"']' \
&&   echo '    py-netcdf4:' \
&&   echo '      version: [1.5.8]' \
&&   echo '      variants: ~mpi' \
&&   echo '    py-numpy:' \
&&   echo '      version: [1.22.3]' \
&&   echo '      variants: +blas +lapack' \
&&   echo '    py-openpyxl:' \
&&   echo '      version: [3.0.3]' \
&&   echo '    py-pandas:' \
&&   echo '      version: [1.5.3]' \
&&   echo '    py-poetry-core:' \
&&   echo '      version: [1.0.8]' \
&&   echo '    py-pybind11:' \
&&   echo '      version: [2.8.1]' \
&&   echo '    py-pycodestyle:' \
&&   echo '      version: [2.8.0]' \
&&   echo '    py-pygithub:' \
&&   echo '      version: ['"'"'1.55'"'"']' \
&&   echo '    py-pygrib:' \
&&   echo '      version: [2.1.4]' \
&&   echo '    py-pyhdf:' \
&&   echo '      version: [0.10.4]' \
&&   echo '    py-pyproj:' \
&&   echo '      version: [3.1.0]' \
&&   echo '    py-python-dateutil:' \
&&   echo '      version: [2.8.2]' \
&&   echo '    py-pythran:' \
&&   echo '      # Versions earlier than 0.11.0 don'"'"'t compile on macOS with llvm-clang/13.0.0 and Python/3.9,' \
&&   echo '      # and 0.11.0 leads to downstream errors in py-scipy with the Intel compilers' \
&&   echo '      version: [0.12.2]' \
&&   echo '    py-pyyaml:' \
&&   echo '      version: [5.4.1]' \
&&   echo '    py-scipy:' \
&&   echo '      version: [1.9.3]' \
&&   echo '    py-setuptools:' \
&&   echo '      version: [59.4.0]' \
&&   echo '    py-setuptools-scm:' \
&&   echo '      version: [7.0.5]' \
&&   echo '    py-shapely:' \
&&   echo '      version: [1.8.0]' \
&&   echo '    scotch:' \
&&   echo '      version: [7.0.4]' \
&&   echo '      variants: +mpi+metis~shared~threads~mpi_thread+noarch' \
&&   echo '    sfcio:' \
&&   echo '      version: [1.4.1]' \
&&   echo '    shumlib:' \
&&   echo '      version: [macos_clang_linux_intel_port]' \
&&   echo '    sigio:' \
&&   echo '      version: [2.3.2]' \
&&   echo '    sp:' \
&&   echo '      version: [2.3.3]' \
&&   echo '    udunits:' \
&&   echo '      version: [2.2.28]' \
&&   echo '    upp:' \
&&   echo '      version: [10.0.10]' \
&&   echo '    w3emc:' \
&&   echo '      version: [2.10.0]' \
&&   echo '    w3nco:' \
&&   echo '      version: [2.4.1]' \
&&   echo '    wgrib2:' \
&&   echo '      version: [2.0.8]' \
&&   echo '    wrf-io:' \
&&   echo '      version: [1.2.0]' \
&&   echo '    yafyaml:' \
&&   echo '      version: [0.5.1]' \
&&   echo '    zlib:' \
&&   echo '      version: [1.2.13]' \
&&   echo '    zstd:' \
&&   echo '      version: [1.5.2]' \
&&   echo '      variants: +programs' \
&&   echo '' \
&&   echo '  specs: [base-env@1.0.0, jedi-base-env@1.0.0, ewok-env@1.0.0, jedi-fv3-env@1.0.0,' \
&&   echo '    jedi-mpas-env@1.0.0, bacio@2.4.1, bison@3.8.2, bufr@12.0.0, ecbuild@3.7.2, eccodes@2.27.0,' \
&&   echo '    ecflow@5, eckit@1.24.4, ecmwf-atlas@0.35.0 +fckit +ectrans +tesselation +fftw,' \
&&   echo '    fiat@1.2.0, ectrans@1.2.0 +fftw, eigen@3.4.0, fckit@0.11.0, fms@release-jcsda,' \
&&   echo '    g2@3.4.5, g2tmpl@1.10.0, gftl-shared@1.6.1, gsibec@1.1.3, hdf@4.2.15, hdf5@1.14.0,' \
&&   echo '    ip@4.3.0, jasper@2.0.32, jedi-cmake@1.4.0, libpng@1.6.37, nccmp@1.9.0.1, netcdf-c@4.9.2,' \
&&   echo '    netcdf-cxx4@4.3.1, netcdf-fortran@4.6.0, nlohmann-json@3.10.5, nlohmann-json-schema-validator@2.1.0,' \
&&   echo '    parallelio@2.5.10, parallel-netcdf@1.12.2, py-eccodes@1.4.2, py-f90nml@1.4.3,' \
&&   echo '    py-gitpython@3.1.27, py-h5py@3.7.0, py-numpy@1.22.3, py-pandas@1.5.3, py-pip,' \
&&   echo '    py-pyyaml@5.4.1, py-scipy@1.9.3, py-shapely@1.8.0, py-xarray@2022.3.0, sp@2.3.3,' \
&&   echo '    udunits@2.2.28, w3nco@2.4.1, w3emc@2.10.0, nco@5.0.6, esmf@8.5.0, mapl@2.40.3,' \
&&   echo '    zlib@1.2.13, zstd@1.5.2, odc@1.4.6, shumlib@macos_clang_linux_intel_port, awscli@1.27.84,' \
&&   echo '    py-globus-cli@3.16.0]' \
&&   echo '  include: []') > /opt/spack-environment/spack.yaml

# Install the software, remove unnecessary deps
RUN cd /opt/spack-environment && spack env activate . && spack install --fail-fast && spack gc -y

# Modifications to the environment that are necessary to run
RUN cd /opt/spack-environment && \
    spack env activate --sh -d . > activate.sh

# Put output of spack find into a file
RUN cd /opt/spack-environment && \
spack env activate -d . && \
spack find 2>&1 | tee /root/spack_find.out


# Bare OS image to run the installed executables
FROM ubuntu:20.04

COPY --from=builder /opt/spack-environment /opt/spack-environment
COPY --from=builder /opt/software /opt/software
COPY --from=builder /opt/._view /opt/._view
COPY --from=builder /opt/view /opt/view

RUN { \
      echo '#!/bin/sh' \
      && echo '.' /opt/spack-environment/activate.sh \
      && echo 'exec "$@"'; \
    } > /entrypoint.sh \
&&  chmod a+x /entrypoint.sh


#Set environment variables for installing tzdata
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
ENV CC=gcc
ENV CXX=g++
ENV FC=gfortran


RUN apt-get -yqq update && apt-get -yqq upgrade \
 && apt-get -yqq install bc cpp g++ gcc gfortran git git-lfs make mysql-server qt5-default libqt5svg5-dev qt5dxcb-plugin wget build-essential ca-certificates curl file gnupg2 iproute2 locales python3 python3-pip python3-setuptools unzip vim \
 && rm -rf /var/lib/apt/lists/*

# Copy spack find output from builder
COPY --from=builder /root/spack_find.out /root/spack_find.out
# Make a non-root user:nonroot / group:nonroot for running MPI
RUN useradd -U -k /etc/skel -s /bin/bash -d /home/nonroot -m nonroot --uid 43891 && \
echo "ulimit -s unlimited" >> /home/nonroot/.bashrc && \
echo "ulimit -v unlimited" >> /home/nonroot/.bashrc && \
echo "export CC=gcc" >> /home/nonroot/.bashrc && \
echo "export CXX=g++" >> /home/nonroot/.bashrc && \
echo "export FC=gfortran" >> /home/nonroot/.bashrc && \
printf "[credential]\n    helper = cache --timeout=7200\n" >> /home/nonroot/.gitconfig && \
mkdir /home/nonroot/.openmpi && \
echo "rmaps_base_oversubscribe = 1" >> /home/nonroot/.openmpi/mca-params.conf && \
chown -R nonroot:nonroot /home/nonroot/.gitconfig /home/nonroot/.openmpi
# Replicate settings for root user
RUN echo "ulimit -s unlimited" >> /root/.bashrc && \
echo "ulimit -v unlimited" >> /root/.bashrc && \
echo "export CC=gcc" >> /root/.bashrc && \
echo "export CXX=g++" >> /root/.bashrc && \
echo "export FC=gfortran" >> /root/.bashrc && \
printf "[credential]\n    helper = cache --timeout=7200\n" >> /root/.gitconfig && \
mkdir /root/.openmpi && \
echo "rmaps_base_oversubscribe = 1" >> /root/.openmpi/mca-params.conf
# Also set necessary environment variables for openmpi
RUN echo "export OMPI_ALLOW_RUN_AS_ROOT=1" >> /root/.bashrc && \
echo "export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1" >> /root/.bashrc && \
echo "export OMPI_MCA_rmaps_base_oversubscribe=1" >> /root/.bashrc

LABEL "app"="empty"
LABEL "mpi"="openmpi"
ENTRYPOINT [ "/entrypoint.sh" ]
CMD [ "/bin/bash" ]

