#!/bin/bash -l

# Get installation directory
export MINICONDA_PATH=${1:-$HOME/miniconda3}

# Check for an existing conda install
if [[ $(which conda) ]]; then
    echo "Conda is already installed"
    exit 1
fi

# Create the install directory
if [[ -d ${MINICONDA_PATH} ]]; then
    echo "Miniconda appears to already be installed at: ${MINICONDA_PATH}"
    exit 1
else
    mkdir -p ${MINICONDA_PATH}
fi

# Download installation script and install it
export PATH=${MINICONDA_PATH}/bin:${PATH}
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ${MINICONDA_PATH}/miniconda.sh
bash ${MINICONDA_PATH}/miniconda.sh -b -u -p ${MINICONDA_PATH}
rm -f ${MINICONDA_PATH}/miniconda.sh
conda update -y conda
conda init
