from functools import wraps
from typing import Callable

from parsl.app.app import bash_app, join_app, python_app


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
        return python_app(function, executors=executor)(*args, **kwargs)

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
        return bash_app(function, executors=executor)(*args, **kwargs)

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
        return join_app(function)(*args, **kwargs)

    return function_wrapper
