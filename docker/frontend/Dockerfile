FROM noaagsl/slurm-frontend:latest

RUN apt-get update -y && apt-get install -y \
    curl \
    libpmi2-0-dev \
    python3 \
    python3-distutils \
    python3-pip \
    python3-venv \
    unzip

# Add apt repository public key for Intel OneAPI
ARG url=https://apt.repos.intel.com/intel-gpg-keys/GPG-PUB-KEY-INTEL-SW-PRODUCTS-2023.PUB
ADD $url ./
RUN file=$(basename "$url") && \
    apt-key add "$file" && \
    rm "$file"

# Configure the apt repository
ARG repo=https://apt.repos.intel.com/oneapi
RUN echo "deb [trusted=yes] $repo all main" > /etc/apt/sources.list.d/oneAPI.list

# Install Intel oneapi packages and set up modules
RUN apt-get update -y && apt-get install -y --no-install-recommends -o=Dpkg::Use-Pty=0 \
    intel-oneapi-compiler-dpcpp-cpp-and-cpp-classic \
    intel-oneapi-compiler-fortran \
    intel-oneapi-mpi-devel

# Create directory in /opt for Spack install
RUN mkdir -p /opt/spack \
 && chown admin:admin /opt/spack

# Copy the install scripts
COPY ./install /tmp/install

USER admin
SHELL ["/bin/bash", "-c"]

# Install Spack
RUN cd /tmp/install \
 && ./install_spack.sh /opt/spack v0.19.2

# Install the bootstrap compiler if necessary
RUN cd /tmp/install \
 && . /opt/spack/share/spack/setup-env.sh \
 && ./install_bootstrap.sh

# Install the base compiler if necessary
RUN cd /tmp/install \
 && . /opt/spack/share/spack/setup-env.sh \
 && ./install_base.sh

# Install the Spack Parsl/Flux environment
RUN cd /tmp/install \
 && . /opt/spack/share/spack/setup-env.sh \
 && ./install_flux_parsl.sh

# Re-install the Spack Parsl/Flux environment to work around bug
RUN cd /tmp/install \
 && . /opt/spack/share/spack/setup-env.sh \
 && ./install_flux_parsl.sh

USER root

# Set up Intel and Spack initialization
RUN echo ". /opt/spack/share/spack/setup-env.sh" > /etc/profile.d/spack.sh
RUN echo "spack env activate flux" >> /etc/profile.d/spack.sh
RUN echo "source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1" > /etc/profile.d/intel_oneapi.sh

USER admin
