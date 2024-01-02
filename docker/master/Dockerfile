FROM noaagsl/slurm-master:latest

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

# Set up spack-stack environment
RUN echo ". /opt/spack-environment/activate.sh" >> /home/admin/.bashrc \
 && echo ". /opt/spack-environment/activate.sh" >> /home/admin/.bash_profile
