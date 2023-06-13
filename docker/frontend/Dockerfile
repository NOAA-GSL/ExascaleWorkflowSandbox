FROM noaagsl/slurm-frontend:latest

RUN apt update -y \
 && apt install -y \
        curl \
        libpmi2-0-dev \
        python3 \
	python3-pip \
        python3-distutils \
        python3-venv

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
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends -o=Dpkg::Use-Pty=0 \
        intel-oneapi-dev-utilities \
        intel-oneapi-mpi-devel \
        intel-oneapi-openmp \
        intel-oneapi-compiler-fortran \
        intel-oneapi-compiler-dpcpp-cpp-and-cpp-classic

# Set up Intel compiler in user environment
RUN echo "source /opt/intel/oneapi/setvars.sh" >> /home/admin/.bash_profile
