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

    @wraps(function)
    def function_wrapper(
        *args,
        executor="all",
        **kwargs,
    ):
        return python_app(_create_filtered_wrapper(function), executors=executor)(
            *args, **kwargs
        )

    return function_wrapper


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

    @wraps(function)
    def function_wrapper(
        *args,
        executor="all",
        **kwargs,
    ):
        return bash_app(_create_filtered_wrapper(function), executors=executor)(
            *args, **kwargs
        )

    return function_wrapper


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

    @wraps(function)
    def function_wrapper(
        *args,
        **kwargs,
    ):
        return join_app(_create_filtered_wrapper(function))(*args, **kwargs)

    return function_wrapper
