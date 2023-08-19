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

# Install Spack
RUN git clone -c feature.manyFiles=true -c core.sharedRepository=true https://github.com/spack/spack.git /opt/spack \
 && cd /opt/spack \
 && git checkout v0.19.2 \
 && chgrp -R admin /opt/spack \
 && chmod -R g+rw /opt/spack

# Copy the install scripts
COPY ./install /tmp/install

USER admin
SHELL ["/bin/bash", "-c"]

# Install the Spack flux environment
RUN . /opt/spack/share/spack/setup-env.sh \
 && cd /tmp/install \
 && ./install_flux.sh

# Install parsl into the flux environment
RUN . /opt/spack/share/spack/setup-env.sh \
 && cd /tmp/install \
 && ./install_parsl.sh

# Re-install the Spack flux environment to rebuild view after pip install of parsl
RUN . /opt/spack/share/spack/setup-env.sh \
 && cd /tmp/install \
 && ./install_flux.sh

# Set up user shell init
RUN echo ". /opt/spack/share/spack/setup-env.sh" >> /home/admin/.bash_profile \
 && echo "source /opt/intel/oneapi/setvars.sh" >> /home/admin/.bash_profile \
 && chown admin:admin /home/admin/.bash_profile

SHELL ["/bin/bash"]
