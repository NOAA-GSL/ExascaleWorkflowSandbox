FROM noaagsl/slurm-frontend:latest

RUN apt-get update -y && apt-get install -y \
    curl \
    libpmi2-0-dev \
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

# Copy install scripts
COPY ./install/install_miniconda.sh /tmp/install_miniconda.sh
COPY ./install/chiltepin.yml /tmp/chiltepin.yml

# Copy conda init script
COPY ./install/conda_init.sh /etc/profile.d/conda_init.sh

# Install Miniconda3 and chiltepin environment
SHELL ["/bin/bash", "-l", "-c"]
RUN cd /tmp \
 && ./install_miniconda.sh /opt/miniconda3 \
 && conda env create --name chiltepin --file chiltepin.yml \
 && conda clean -afy

SHELL ["/bin/bash", "-c"]
USER admin

RUN echo "source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1" >> /home/admin/.bashrc
RUN echo "source /etc/profile.d/conda_init.sh > /dev/null 2>&1" >> /home/admin/.bashrc
RUN echo "conda activate chiltepin" >> /home/admin/.bashrc
RUN echo "source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1" >> /home/admin/.bash_profile
RUN echo "source /etc/profile.d/conda_init.sh > /dev/null 2>&1" >> /home/admin/.bash_profile
RUN echo "conda activate chiltepin" >> /home/admin/.bash_profile

SHELL ["/bin/bash"]
