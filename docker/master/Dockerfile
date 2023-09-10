FROM noaagsl/slurm-master:latest

RUN apt-get update -y && apt-get install -y \
    libpmi2-0-dev

# Set up user shell init
#RUN echo "source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1" >> /home/admin/.bash_profile \
# && echo ". /opt/spack/share/spack/setup-env.sh" >> /home/admin/.bash_profile \
# && echo "spack env activate flux" >> /home/admin/.bash_profile \
# && chown admin:admin /home/admin/.bash_profile

RUN echo ". /opt/spack/share/spack/setup-env.sh" > /etc/profile.d/spack.sh
RUN echo "spack env activate flux" >> /etc/profile.d/spack.sh
RUN echo "source /opt/intel/oneapi/setvars.sh > /dev/null 2>&1" > /etc/profile.d/intel_oneapi.sh
