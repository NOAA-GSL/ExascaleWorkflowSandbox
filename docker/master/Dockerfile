FROM noaagsl/slurm-master:latest

RUN apt-get update -y && apt-get install -y \
    libpmi2-0-dev

# Set up user shell init
RUN echo ". /opt/spack/share/spack/setup-env.sh" > /etc/profile.d/spack.sh
RUN echo "spack env activate flux" >> /etc/profile.d/spack.sh
RUN echo "source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1" > /etc/profile.d/intel_oneapi.sh
