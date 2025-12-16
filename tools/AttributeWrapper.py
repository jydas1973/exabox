"""

 $Header: 

 Copyright (c) 2018, 2020, Oracle and/or its affiliates. 

 NAME:
      AttributeWrapper.py - Provides an utility to easily override the
                            attribute getters of any object.
      
 DESCRIPTION:

      Contains a class that can be constructed using any object and any 
      function of the form (Any, str) -> Any (A general getter)

 NOTES:
      None

 History:

    MODIFIED   (MM/DD/YY)
        scoral      04/27/20 - Creation of the file
"""

# We disable this warning because curried functions (with the decorator) are
# not well recognized.
#pylint: disable=no-value-for-parameter

import six
from typing import TypeVar, Any, Callable, Tuple, Union, Mapping

A, B, E, R, S, T = (TypeVar(var) for var in ('A', 'B', 'E', 'R', 'S', 'T'))



# Generic functions and decorators


def identity(x: A) -> A:
    """
    Identity function.
    
    Useful mostly for testing purposes.

    identity(x) == x
    """
    return x


def prePostCompose(aPreProcessor: Callable[[S], A], aPostProcessor: Callable[[B], T]) -> Callable[[Callable[[A], B]], Callable[[S], T]]:
    """
    Generalization of a decorator.
        
    It's used to both preprocess the input of a function with some other
    given function, and postprocess it's result with yet another function.

    prePostCompose(pre, post)(f)(x) = post(f(pre(x)))
    """
    def composeWith(aFunction: Callable[[A], B]) -> Callable[[S], T]:
        def resultingFunction(*aArgs, **aKwArgs) -> T:
            return aPostProcessor(aFunction(aPreProcessor(*aArgs, **aKwArgs)))
        return resultingFunction
    return composeWith


def postCompose(aPostProcessor: Callable[[A], B]) -> Callable[[Callable[[E], A]], Callable[[E], B]]:
    """
    It's used to only postprocess the output of a function with another
    function, in other words, it's function post composition.
    
    postCompose(post)(f)(x) = post(f(x))
    """
    def postComposeWith(aFunction: Callable[[E], B]) -> Callable[[E], B]:
        def resultingFunction(*aArgs, **aKwArgs) -> B:
            return aPostProcessor(aFunction(*aArgs, **aKwArgs))
        return resultingFunction
    return postComposeWith


def preCompose(aPreProcessor: Callable[[A], B]) -> Callable[[Callable[[B], R]], Callable[[A], R]]:
    """
    Used to preprocess the input of a function with some other
    given function, in other words, it's function pre composition.
    
    preCompose(pre)(f)(x) = f(pre(x))
    """
    def preComposeWith(aFunction: Callable[[B], R]) -> Callable[[A], R]:
        def resultingFunction(*aArgs, **aKwArgs) -> R:
            return aFunction(aPreProcessor(*aArgs, **aKwArgs))
        return resultingFunction
    return preComposeWith


def curry(aFunction: Callable[[S, A], B]) -> Callable[[S], Callable[[A], B]]:
    """
    Converts a function of more then one argument into a function reciving the
    first argument and returning a function taking the rest of the arguments.

    curry(f)(x1)(x2, x3, ...) = f(x1, x2, x3, ...)
    """
    def fstArgReciever(aArg: S) -> Callable[[A], B]:
        def restArgsReciever(*aArgs, **aKwArgs) -> B:
            return aFunction(aArg, *aArgs, **aKwArgs)
        return restArgsReciever
    return fstArgReciever


@curry
def flipArgs(aFunction: Callable[[A, B], R], aSndArg: B, aFstArg: A, *aArgs, **aKwArgs) -> R:
    """
    Flips the first two arguments of a function.

    flipArgs(f)(x1, x2, x3, ...) = f(x2, x1, x3, ...)
    """
    return aFunction(aFstArg, aSndArg, *aArgs, **aKwArgs)

@curry
def applyNotNull(aFunction: Callable[[A], B], aArg: Union[None, A]) -> Union[None, B]:
    """
    Applies an argument to a function when the argument is not None.
    """
    if aArg is None:
        return None
    return aFunction(aArg)


class ebAttributeWrapper():
    """
    Overrides getattr with some specified alternative for a given object.
    
    FIXME: Magic methods won't work unless you call them as functions.
    For example: len(ebAttributeWrapper(getattr, 'hello')) will fail
    throwing an exception, but
    ebAttributeWrapper(getattr, 'hello').__len__() will work fine.
    
    A simple fix would be to override here all of the magic methods
    to use the original object's magic methods.
    """

    def __init__(self, aGetter: Callable[[A, str], Any], aObject: A):
        self.__object   = aObject
        self.__getter   = aGetter
    
    def __getattr__(self, aName: str) -> Any:
        if aName == 'unwrapped':
            return self.__object
        return self.__getter(self.__object, aName)


def wrapOverridingProp(aDict: Mapping[str, Any]) -> Callable[[A, str], Any]:
    """Creates a getter that overrides all of the specified properties in a dictionary."""
    def newGetter(self: A, aName: str) -> Any:
        if aName in aDict.keys():
            return aDict[aName]
        return getattr(self, aName)
    return newGetter


def wrapProcessingProp(aDict: Mapping[str, Callable[[Any], Any]]) -> Callable[[A, str], Any]:
    """Returns a getter that applies a function to all of the specified properties in a dictionary."""
    def newGetter(self: A, aName: str) -> Any:
        if aName in aDict.keys():
            return aDict[aName](getattr(self, aName))
        return getattr(self, aName)
    return newGetter



# Utilities

# Makes a function that acepts bytes objects compatible with strings as well
# and makes sure its return value is always a string.
forceStrArgRet = prePostCompose(six.ensure_binary, applyNotNull(six.ensure_text))


conflictingStrBytesFunctions = {
    'readlines':    postCompose(lambda lines: list(map(applyNotNull(six.ensure_text), lines))),
    'readline':     postCompose(six.ensure_text),
    'read':         postCompose(six.ensure_text),
    'write':        preCompose(six.ensure_binary),
    'writelines':   preCompose(lambda lines: map(six.ensure_binary, lines)),
    'communicate':  postCompose(lambda streamOut: tuple(map(applyNotNull(six.ensure_text), streamOut)))
}

def wrapStrBytesFunctions(aObj):
    return ebAttributeWrapper(wrapProcessingProp(conflictingStrBytesFunctions), aObj)

