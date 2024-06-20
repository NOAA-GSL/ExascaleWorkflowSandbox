FROM ghcr.io/noaa-gsl/exascaleworkflowsandbox/spack-stack-gnu-openmpi:latest as JEDI

FROM ghcr.io/noaa-gsl/dockerslurmcluster/slurm-frontend:latest

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
    libqt5svg5-dev \
    locales \
    make \
    python3 \
    python3-pip \
    python3-setuptools \
    qtbase5-dev \
    qt5-qmake \
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

# Set up spack-stack environment
RUN echo ". /opt/spack-environment/activate.sh" >> /home/admin/.bashrc \
 && echo ". /opt/spack-environment/activate.sh" >> /home/admin/.bash_profile
