from parsl.app.app import bash_app, python_app, join_app
import os
import shutil
import textwrap
import yaml

@bash_app(executors=['service'])
def _clone(env, install_path, tag="develop", stdout=None, stderr=None):
    return env + textwrap.dedent(f'''
    echo Started at $(date)
    echo Executing on $(hostname)
    git lfs install --skip-repo
    rm -rf {install_path}/jedi-bundle/{tag}/src
    mkdir -p {install_path}/jedi-bundle/{tag}
    cd {install_path}/jedi-bundle/{tag}
    git clone --branch {tag} https://github.com/JCSDA/jedi-bundle.git src
    echo Completed at $(date)
    ''')

@bash_app(executors=['service'])
def _configure(env, install_path, tag="develop", stdout=None, stderr=None, clone=None):
    return env + textwrap.dedent(f'''
    echo Started at $(date)
    echo Executing on $(hostname)
    cd {install_path}/jedi-bundle/{tag}
    rm -rf build
    mkdir build
    cd build
    # Comment out the parts of the bundle we do not need
    perl -p -i -e 's/(.* PROJECT fv3)/#\\1/g' ../src/CMakeLists.txt
    perl -p -i -e 's/(.* PROJECT femps)/#\\1/g' ../src/CMakeLists.txt
    perl -p -i -e 's/(.* PROJECT soca)/#\\1/g' ../src/CMakeLists.txt
    perl -p -i -e 's/(.* PROJECT mom6)/#\\1/g' ../src/CMakeLists.txt
    perl -p -i -e 's/(.* PROJECT coupling)/#\\1/g' ../src/CMakeLists.txt
    perl -p -i -e 's/(.*mpas)/#\\1/ig' ../src/CMakeLists.txt
    ecbuild -DCMAKE_INSTALL_PREFIX=../ ../src
    echo Completed at $(date)
    ''')

@bash_app(executors=['serial'])
def _make(env, install_path, tag="develop", stdout=None, stderr=None, configure=None):
    return env + textwrap.dedent(f'''
    echo Started at $(date)
    echo Executing on $(hostname)
    spack env list
    spack env deactivate
    cd {install_path}/jedi-bundle/{tag}/build
    make -j16 VERBOSE=1
    make install
    echo Completed at $(date)    ''')


@join_app
def run(environment, install_path, tag="develop", stdout=None, stderr=None):

    clone = _clone(environment,
                   install_path=install_path,
                   stdout=stdout,
                   stderr=stderr,
                   tag=tag)

    configure = _configure(environment,
                           install_path=install_path,
                           stdout=stdout,
                           stderr=stderr,
                           tag=tag,
                           clone=clone)

    make = _make(environment,
                 install_path=install_path,
                 stdout=stdout,
                 stderr=stderr,
                 tag=tag,
                 configure=configure)

    return(make)
