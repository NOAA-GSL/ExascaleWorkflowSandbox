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
def python_hello ():
    return 'Hello World! from Python App'


# Define a "hello world" Bash Parsl App
@bash_app
def bash_hello(stdout='echo-hello.stdout', stderr='echo-hello.stderr'):
    return 'echo "Hello World! from Bash App"'

# Run the Python "hello world", wait for the result, and print it
print(python_hello().result())

# Run the Bash "hello world", wait for the result, and print it
bash_hello().result()
with open('echo-hello.stdout', 'r') as f:
     print(f.read())

