"""
 Copyright (c) 2014, 2020, Oracle and/or its affiliates. 

NAME:
    MockNode - Basic functionality

FUNCTION:
    Provide basic/core API for create Mock Commands

NOTE:
    None

History:
    jesandov   08/13/2019 - Creation of file
"""

from typing import Callable, Tuple

MockCommandCallback = Callable[[str, str], Tuple[int, str, str]]
"""Mock command callback

Callback to be used in mock commands.  It must accept two parameters, the first
one being the command that is being mocked, and the second one the stdin being
passed to the command; both of type str.  It must return a tuple (rc, stdout,
stderr), where
    rc     (int): command's return code
    stdout (str): command's stdout
    stderr (str): command's stderr
"""

class MockCommand():
    def __init__(
            self,
            aCmdRegex: str,
            aCallback: MockCommandCallback,
            aPersist: bool = False) -> None:
        """Create mock command

        :param aCmdRegex: String regex to match commands against.
        :param aCallback: Callback to be called when mocking command execution.
                          See documentation of MockCommandCallback for details.
        :param aPersist: Whether this mock command should be reused in more
                         than one execution.
        """
        self.__cmd_regex = aCmdRegex
        self.__cmd_callback = aCallback
        self.__persist = aPersist

    def mGetCmdRegex(self) -> str:
        return self.__cmd_regex

    def mIsPersist(self) -> bool:
        return self.__persist

    def mExecuteMockCmd(self, aCmd: str, aStdin: str) -> Tuple[int, str, str]:
        return self.__cmd_callback(aCmd, aStdin)

    def __repr__(self) -> str:
        return f'Regex:{self.__cmd_regex}, Callback:{self.__cmd_callback}, Persist:{self.__persist}'

class exaMockCommand(MockCommand):
    def __init__(
            self,
            aCmdRegex: str,
            aRc: int = 0,
            aStdout: str = "",
            aStderr: str = "",
            aPersist: bool = False) -> None:
        """Create MockCommand that returns fixed values

        Creates a MockCommand with a callback that always returns fixed values.

        :param aCmdRegex: command regex to match the MockCommand against
        :param aRc: return code to be returned by the MockCommand callback
        :param aStdout: stdout to be returned by the MockCommand callback
        :param astderr: stderr to be returned by the MockCommand callback
        """
        callback = lambda cmd, stdin: (aRc, aStdout, aStderr)
        super().__init__(aCmdRegex, callback, aPersist)
        self.__rc = aRc
        self.__stdout = aStdout
        self.__stderr = aStderr

    def mGetRc(self) -> int:
        return self.__rc

    def mGetStdout(self) -> str:
        return self.__stdout

    def mGetStderr(self) -> str:
        return self.__stderr

    def __repr__(self) -> str:
        return f'{super().__repr__()} aRc:{self.__rc}, aStdout:{self.__stdout}, aStderr:{self.__stderr}'
