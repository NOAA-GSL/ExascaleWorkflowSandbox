#!/bin/env bash

spack env activate flux
pip install parsl
pip install 'dill @ git+https://github.com/uqfoundation/dill'

exit 0
