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
COPY --from=JEDI /opt/._view /opt/._view
COPY --from=JEDI /opt/spack-environment /opt/spack-environment

# Copy conda and jedi init scripts
COPY ./install/jedi_init.sh /opt/jedi_init.sh
COPY ./install/conda_init.sh /opt/conda_init.sh

# Copy conda install scripts
COPY ./install/install_miniconda.sh /tmp/install_miniconda.sh
COPY ./install/chiltepin.yml /tmp/chiltepin.yml

# Install Miniconda3 and chiltepin environment
RUN cd /tmp \
 && ./install_miniconda.sh /opt/miniconda3 \
 && . /opt/conda_init.sh \
 && conda env create --name chiltepin --file chiltepin.yml \
 && conda clean -afy
