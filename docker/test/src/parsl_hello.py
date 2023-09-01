#!/bin/env python3

import parsl
import os
from parsl.app.app import python_app, bash_app
from parsl.configs.local_threads import config

# Print the version of Parsl we are using
print(f"Running Parsl version: {parsl.__version__}")

# Configure Parsl with default config
parsl.load(config)

# Define a "hello world" Python Parsl App
@python_app
def python_hello (stdout=None, stderr=None):
    return 'Hello World! from Python App'

# Define a "hello world" Bash Parsl App
@bash_app
def bash_hello(stdout=None, stderr=None):
    return 'echo "Hello World! from Bash App"'

# Run the Python "hello world", wait for the result, and write it to output file
with open('parsl_python_hello.out', 'w') as f:
    f.write(f"{python_hello().result()}\n")

# Run the Bash "hello world", wait for the result, and write it to output file
bash_hello(stdout=('parsl_bash_hello.out', 'w'),
           stderr=('parsl_bash_hello.err', 'w')).result()

# Cleanup
parsl.clear()
