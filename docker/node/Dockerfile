FROM noaagsl/slurm-node:latest

RUN apt-get update -y && apt-get install -y \
    libpmi2-0-dev

# Set up user shell init
RUN echo ". /opt/spack/share/spack/setup-env.sh" >> /home/admin/.bash_profile \
 && echo "spack env activate flux" >> /home/admin/.bash_profile \
 && echo "source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1" >> /home/admin/.bash_profile \
 && chown admin:admin /home/admin/.bash_profile
