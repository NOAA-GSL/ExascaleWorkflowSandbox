# SPDX-License-Identifier: Apache-2.0

"""Task decorators for Chiltepin workflows.

This module provides decorators for defining workflow tasks that can be executed
on configured resources. Tasks are the fundamental units of work in Chiltepin workflows.

Available Decorators
--------------------
- :func:`python_task`: Execute Python functions as workflow tasks
- :func:`bash_task`: Execute shell commands as workflow tasks
- :func:`join_task`: Coordinate multiple tasks without blocking workflow execution

For comprehensive usage examples and best practices, see the :doc:`tasks` documentation.

Examples
--------
Define a simple Python task::

    from chiltepin.tasks import python_task

    @python_task
    def add_numbers(a, b):
        return a + b

    # Execute on a specific resource
    result = add_numbers(5, 3, executor="compute").result()

Define a bash task::

    from chiltepin.tasks import bash_task

    @bash_task
    def list_files(directory):
        return f"ls -la {directory}"

    # Returns exit code (0 = success)
    exit_code = list_files("/tmp", executor="compute").result()
"""

from functools import wraps
from inspect import Parameter, signature
from typing import Callable

from parsl.app.app import bash_app, join_app, python_app


def _create_filtered_wrapper(function: Callable) -> Callable:
    """Create a wrapper that filters kwargs to only pass what the function accepts.

    This helper function creates an intermediate wrapper for Parsl app decorators.
    The wrapper accepts any arguments that Parsl injects (stdout, stderr, etc.)
    but only forwards the ones that the user's function signature expects.

    Parameters
    ----------
    function: Callable
        The user's function to wrap

    Returns
    -------
    Callable
        A wrapper function that filters kwargs based on the function's signature
    """
    sig = signature(function)
    func_params = sig.parameters

    # Check if the function accepts **kwargs (VAR_KEYWORD)
    has_var_keyword = any(
        param.kind == Parameter.VAR_KEYWORD for param in func_params.values()
    )

    @wraps(function)
    def wrapper(*args, **kwargs):
        # If function has **kwargs, pass all kwargs through
        # Otherwise, filter to only include parameters the function explicitly accepts
        if has_var_keyword:
            return function(*args, **kwargs)
        else:
            filtered_kwargs = {k: v for k, v in kwargs.items() if k in func_params}
            return function(*args, **filtered_kwargs)

    return wrapper


class MethodWrapper:
    """Wrapper that preserves method behavior for decorated functions.

    This descriptor ensures that when a decorated function is accessed as a
    method, it properly creates a bound method with the instance.
    """

    def __init__(self, func, wrapper_func):
        self.func = func
        self.wrapper_func = wrapper_func
        # Copy over metadata
        wraps(func)(self)

    def __get__(self, obj, objtype=None):
        """Support instance methods."""
        if obj is None:
            # Accessed on class, return self
            return self
        # Return a bound version of the wrapper
        from functools import partial

        return partial(self.wrapper_func, obj)

    def __call__(self, *args, **kwargs):
        """Support standalone function calls."""
        return self.wrapper_func(*args, **kwargs)


def python_task(function: Callable) -> Callable:
    """Decorator function for making Chiltepin python tasks.

    The decorator transforms the function into a Parsl python_app but adds an executor
    argument such that the executor for the function can be chosen dynamically at runtime.

    Parameters
    ----------

    function: Callable
        The function to be decorated to yield a Python workflow task. This function can be a
        stand-alone function or a class method. If it is a class method, it can make use of
        `self` to access object state.


    Returns
    -------

    Callable

    """

    def function_wrapper(
        *args,
        executor="all",
        **kwargs,
    ):
        return python_app(_create_filtered_wrapper(function), executors=executor)(
            *args, **kwargs
        )

    return MethodWrapper(function, function_wrapper)


def bash_task(function: Callable) -> Callable:
    """Decorator function for making Chiltepin bash tasks.

    The decorator transforms the function into a Parsl bash_app but adds an executor
    argument such that the executor for the function can be chosen dynamically at runtime.

    Parameters
    ----------

    function: Callable
        The function to be decorated to yield a Bash workflow task. This function can be a
        stand-alone function or a class method. If it is a class method, it can make use of
        `self` to access object state. The function must return a string that contains a
        series of bash commands to be executed.


    Returns
    -------

    Callable

    """

    def function_wrapper(
        *args,
        executor="all",
        **kwargs,
    ):
        return bash_app(_create_filtered_wrapper(function), executors=executor)(
            *args, **kwargs
        )

    return MethodWrapper(function, function_wrapper)


def join_task(function: Callable) -> Callable:
    """Decorator function for making Chiltepin join tasks.

    The decorator transforms the function into a Parsl join_app. A parsl @join_app decorator
    accomplishes the same thing.  This decorator is added to provide API consistency so that
    users can use @join_task rather than @join_app along with @python_task and @bash_task.

    Parameters
    ----------

    function: Callable
        The function to be decorated to yield a join workflow task. This function can be a
        stand-alone function or a class method. If it is a class method, it can make use of
        `self` to access object state. The function is expected to call multiple python or
        bash tasks and return a Future that encapsulates the result of those tasks.


    Returns
    -------

    Callable

    """

    def function_wrapper(
        *args,
        **kwargs,
    ):
        return join_app(_create_filtered_wrapper(function))(*args, **kwargs)

    return MethodWrapper(function, function_wrapper)
