import os
import parsl
from parsl.app.app import python_app, bash_app
import pytest
import re

class QG:

    def __init__(self, config, env):
        self.config = config
        self.env = env

    def display(self):
        print(self.config)
        print(self.env)

    @bash_app(executors=['service'])
    def clone(env, install_path, tag="develop", stdout=None, stderr=None):
        return '''
        export INSTALL_PATH={}
        export TAG={}
        {}
        hostname
        git lfs install --skip-repo
        rm -rf $INSTALL_PATH/jedi-bundle/$TAG/src
        mkdir -p $INSTALL_PATH/jedi-bundle/$TAG
        cd $INSTALL_PATH/jedi-bundle/$TAG
        git clone --branch $TAG https://github.com/JCSDA/jedi-bundle.git src
        '''.format(install_path, tag, env)


    @bash_app(executors=['service'])
    def configure(env, install_path, tag="develop", stdout=None, stderr=None):
        return '''
        export INSTALL_PATH={}
        export TAG={}
        {}
        hostname
        cd $INSTALL_PATH/jedi-bundle/$TAG
        rm -rf build
        mkdir build
        cd build
        pwd
        ls ..
        perl -p -i -e "s/ecbuild_bundle\( PROJECT fv3/#ecbuild_bundle\( PROJECT fv3/g" ../src/CMakeLists.txt
        perl -p -i -e "s/ecbuild_bundle\( PROJECT femps/#ecbuild_bundle\( PROJECT femps/g" ../src/CMakeLists.txt
        perl -p -i -e "s/ecbuild_bundle\( PROJECT mom6/#ecbuild_bundle\( PROJECT mom6/g" ../src/CMakeLists.txt
        perl -p -i -e "s/ecbuild_bundle\( PROJECT soca/#ecbuild_bundle\( PROJECT soca/g" ../src/CMakeLists.txt
        perl -p -i -e "s/ecbuild_bundle\( PROJECT coupling/#ecbuild_bundle\( PROJECT coupling/g" ../src/CMakeLists.txt
        perl -p -i -e "s/set\(MPAS/#set\(MPAS/g" ../src/CMakeLists.txt
        perl -p -i -e "s/ecbuild_bundle\( PROJECT mpas/#ecbuild_bundle\( PROJECT mpas/g" ../src/CMakeLists.txt
        ecbuild -DCMAKE_INSTALL_PREFIX=../ ../src
        '''.format(install_path, tag, env)

    @bash_app(executors=['serial'])
    def make(env, install_path, tag="develop", stdout=None, stderr=None):
        return '''
        export INSTALL_PATH={}
        export TAG={}
        {}
        hostname
        spack env list
        spack env deactivate
        cd $INSTALL_PATH/jedi-bundle/$TAG/build
        make -j16 VERBOSE=1
        make install
        '''.format(install_path, tag, env)
