#!/bin/bash

# Try skipping the update because it takes too long
#yum -y update

sudo yum update -y ca-certificates

# Compilers - this includes environment module support
sudo yum -y install gcc-toolset-11-gcc-c++
sudo yum -y install gcc-toolset-11-gcc-gfortran
sudo yum -y install gcc-toolset-11-gdb

# Do *not* install MPI with yum, this will be done with spack-stack

# Misc
sudo yum -y install m4
sudo yum -y install wget
# Do not install cmake (it's 3.20.2, which doesn't work with eckit)
sudo yum -y install git
sudo yum -y install git-lfs
sudo yum -y install bash-completion
sudo yum -y install bzip2 bzip2-devel
sudo yum -y install unzip
sudo yum -y install patch
sudo yum -y install automake
sudo yum -y install xorg-x11-xauth
sudo yum -y install xterm
sudo yum -y install perl-IPC-Cmd
sudo yum -y install gettext-devel
sudo yum -y install texlive
# Do not install qt@5 for now

# Note - only needed for running JCSDA's
# JEDI-Skylab system (using R2D2 localhost)
sudo yum -y --allowerasing install mysql-server

# For screen utility (optional)
#yum -y remove https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
#yum -y update --nobest
#yum -y install screen

# Python
sudo yum -y install python39-devel
sudo alternatives --set python3 /usr/bin/python3.9

sudo python3 -m pip install boto3

