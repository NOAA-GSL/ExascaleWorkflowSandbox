FROM noaagsl/slurm-master:latest

RUN apt-get update -y && apt-get install -y \
    libpmi2-0-dev

# Set up Intel and flux-parsl Spack environment initialization
RUN echo "source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1" > /etc/profile.d/intel-oneapi.sh \
 && echo "source /opt/etc/activate-parsl-flux.sh" > /etc/profile.d/parsl-flux.sh
