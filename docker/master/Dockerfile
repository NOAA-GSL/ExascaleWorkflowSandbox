FROM noaagsl/slurm-master:latest

RUN apt-get update -y && apt-get install -y \
    libpmi2-0-dev

# Set up Intel and Chiltepin environment initialization
USER admin
RUN echo "source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1" >> /home/admin/.bashrc
RUN echo "source /etc/profile.d/conda_init.sh > /dev/null 2>&1" >> /home/admin/.bashrc
RUN echo "conda activate chiltepin" >> /home/admin/.bashrc
RUN echo "source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1" >> /home/admin/.bash_profile
RUN echo "source /etc/profile.d/conda_init.sh > /dev/null 2>&1" >> /home/admin/.bash_profile
RUN echo "conda activate chiltepin" >> /home/admin/.bash_profile
