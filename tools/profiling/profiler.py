#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/tools/profiling/profiler.py /main/3 2025/04/23 14:38:26 abflores Exp $
#
# profiler.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      profiler.py - Common profiling utilities with no business logic.
#
#    DESCRIPTION
#      Contains a decorator to measure the time execution of any function
#      call and utilities to consume the profiled data.
#
#      Example:
#
#       @measure_exec_time(lambda some_arg: some_arg, lambda ret: ret)
#       def some_func(some_arg: Optional[str]):
#           if some_arg is None:
#               raise TypeError
#           return f"Hi {some_arg}!"
#
#       try:
#           print(some_func('Larry'))
#           print(some_func(None))
#       except:
#           print("It's ok, go ahead.")
#
#       def print_info(
#           thread: Thread,
#           func: Callable[..., Any],
#           exec_start_time: float,
#           exec_data: Dict[str, Union[float, Exception, Any]]
#       ):
#           print()
#           print(f"Thread: {thread.name}")
#           print(f"Function: {func.__name__}")
#           print(f"Start time: {exec_start_time}")
#           print(f"Finish time: {exec_data['finished']}")
#
#           if 'exception' in exec_data:
#               print(f"Exception: {exec_data['exception']}")
#           if 'args' in exec_data:
#               print(f"Arguments: {exec_data['args']}")
#           if 'return' in exec_data:
#               print(f"Return value: {exec_data['return']}")
#
#       consume_profiling_data(print_info)
#
#
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    aararora    03/06/24 - Bug 36369329: Profiler having issues when
#                           dictionary data is changed
#    scoral      05/26/21 - Creation
#

from typing import Optional, TypeVar, Any, Union, Callable, Dict
from threading import Thread, current_thread
import time

from exabox.log.LogMgr import ebLogWarn


###############################################################################
#### Type variables and aliases
###############################################################################

TProfiledDataDict = Dict[
    Thread,
    Dict[
        Callable[..., Any],
        Dict[
            float, # Start time of the function
            Dict[
                str, # finished | args | return | exception
                Union[
                    Exception,  # exception
                    float,      # finished
                    Any         # args | return
                ]
            ]
        ]
    ]
]


TProfiledData = Callable[
    [
        Thread,
        Callable[..., Any],
        float,
        Dict[str, Union[float, Exception, Any]]
    ],
    Any
]



###############################################################################
### Global variables
###############################################################################

profiling_data: TProfiledDataDict = {}



###############################################################################
### Common methods
###############################################################################

def measure_exec_time(
    args_stealer: Callable[..., Any]=None,
    ret_stealer: Callable[[Any], Any]=None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """
    Creates a decorator that measures the execution time of every call of the
    decorated function and stores the results into the global variable
    'profiling_data' which is also found at this module.

    If any function call ends unexpectedly due to some exception, a copy of
    the raised exception is also stored in the execution data dictionary.

    We can also provide another function with an equivalent arguments
    signature than the decorated one which will be called with the same
    arguments after the execution measure time is done, its return value
    will be stored in the execution data dictionary and can be used to cause a
    side effect with the arguments of every measured call or to store a copy
    of some or all of the arguments of every measured call.

    We can also provide another function which will be called with the return
    value of the measured call and which return value will be sotored in the
    execution data dictionary.

    To get full usage examples, check the module header.

    :param args_stealer: A function that will be called after the decorated
        one with the same arguments and which return value will be stored.
    :param ret_stealer: A function that will be called after the decorated one
        with the its return value and which return value will be stored.
    :returns: Decorator to measure the time execution of every function call.
    """

    def measure_wrapper(func: Callable[..., Any]) -> Callable[..., Any]:
        def measured_func(*args, **kwargs) -> Any:
            global profiling_data

            thread: Thread = current_thread()
            if thread not in profiling_data:
                profiling_data[thread] = {}
            if func not in profiling_data[thread]:
                profiling_data[thread][func] = {}

            ret: Optional[Any] = None
            t0: float = time.time()
            profiling_data[thread][func][t0] = {}

            try:
                ret = func(*args, **kwargs)
                return ret
            except Exception as ex:
                profiling_data[thread][func][t0]['exception'] = ex
                raise ex
            finally:
                tf: float = time.time()
                profiling_data[thread][func][t0]['finished'] = tf
                if args_stealer:
                    profiling_data[thread][func][t0]['args'] = \
                        args_stealer(*args, **kwargs)
                if ret_stealer:
                    profiling_data[thread][func][t0]['return'] = \
                        ret_stealer(ret)

        return measured_func
    return measure_wrapper



def consume_profiling_data(consumer: TProfiledData):
    """
    Iterates over the whole set of entries of measured function calls made by
    this module.

    To get full usage examples, check the module header.

    :param consumer: A function that will consume each entry of the dictionary.
    """
    global profiling_data

    try:
        for thread, thread_data in list(profiling_data.items()):
            for func, func_data in list(thread_data.items()):
                for exec_start_time, exec_data in list(func_data.items()):
                    consumer(thread, func, exec_start_time, exec_data)
    except Exception as ex:
        # If the profiling fails, we can still continue with the functionality
        ebLogWarn(f"Profiling failed due to an exception: {ex}. Continuing.")



def flush_profiled_data():
    """
    Deletes all saved entries of the measured function calls dictionary of
    this module.
    """
    global profiling_data
    profiling_data = {}
