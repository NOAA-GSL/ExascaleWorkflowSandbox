from parsl.app.app import bash_app
import textwrap


class QG:

    def __init__(self, config, env):
        self.config = config
        self.env = env

    def display(self):
        print(self.config)
        print(self.env)

    @bash_app(executors=['service'])
    def clone(env, install_path, tag="develop", stdout=None, stderr=None):
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
    def configure(env, install_path, tag="develop", stdout=None, stderr=None, clone=None):
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
    def make(env, install_path, tag="develop", stdout=None, stderr=None, configure=None):
        return env + textwrap.dedent(f'''
        echo Started at $(date)
        echo Executing on $(hostname)
        spack env list
        spack env deactivate
        cd {install_path}/jedi-bundle/{tag}/build
        make -j16 VERBOSE=1
        make install
        echo Completed at $(date)
        ''')
