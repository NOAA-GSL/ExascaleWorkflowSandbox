FROM ghcr.io/noaa-gsl/exascaleworkflowsandbox/spack-stack-gnu-openmpi:latest as JEDI

FROM noaagsl/slurm-frontend:latest

#Set environment variables for installing tzdata
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC
ENV CC=gcc
ENV CXX=g++
ENV FC=gfortran

RUN apt-get -yqq update && apt-get -yqq upgrade && apt-get -yqq install \
    bc \
    build-essential \
    ca-certificates \
    cpp \
    curl \
    file \
    g++ \
    gcc \
    gfortran \
    git \
    git-lfs \
    gnupg2 \
    gpg \
    iproute2 \
    libpmi2-0-dev \
    libqt5svg5-dev \
    locales \
    make \
    python3 \
    python3-pip \
    python3-setuptools \
    qt5-default \
    qt5dxcb-plugin \
    unzip \
    vim \
    wget \
 && rm -rf /var/lib/apt/lists/*

# Copy JEDI stack from JEDI stage
COPY --from=JEDI /opt/software /opt/software
COPY --from=JEDI /opt/view /opt/view
COPY --from=JEDI /opt/views /opt/views
COPY --from=JEDI /opt/spack-environment /opt/spack-environment

# Copy conda and jedi init scripts
COPY ./install/jedi_init.sh /opt/jedi_init.sh
COPY ./install/conda_init.sh /tmp/conda_init.sh

# Copy conda install scripts
COPY ./install/install_miniconda.sh /tmp/install_miniconda.sh
COPY ./install/chiltepin.yml /tmp/chiltepin.yml

RUN mkdir -p /opt/admin \
 && chown admin:admin /opt/admin

USER admin

# Install Miniconda3 and chiltepin environment
RUN cd /tmp \
 && ./install_miniconda.sh /opt/admin/miniconda3 \
 && . /tmp/conda_init.sh \
 && conda env create --name chiltepin --file chiltepin.yml \
 && conda clean -afy \
 && cat /tmp/conda_init.sh >> /home/admin/.bash_profile
