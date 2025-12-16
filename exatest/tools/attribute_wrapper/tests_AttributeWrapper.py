#
# $Header: ecs/exacloud/exabox/exatest/tests_AttributeWrapper.py /main/2 2020/07/31 18:27:43 scoral Exp $
#
# tests_AttributeWrapper.py
#
# Copyright (c) 2020, Oracle and/or its affiliates. 
#
#    NAME
#      tests_AttributeWrapper.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Test the AttributeWrapper class
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    vgerard     06/06/20 - Creation
#

import unittest
import six
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions, forceStrArgRet
from subprocess import Popen, PIPE, STDOUT, check_output
from base64 import b64encode, b64decode


class ebTestAttributeWrapper(unittest.TestCase):
    def test_SimpleWrap(self):

        # Try to use a with block with Popen objects to avoid Pylint warnings.
        with Popen(['echo', '-n', 'test'], shell=False, stdout=PIPE, stderr=PIPE) as _p:
            # Wrap the Popen objects whenever you want to use their communicate method.
            _out, _err = wrapStrBytesFunctions(_p).communicate()
            self.assertEqual((_out, _err), ('test', ''))

        with Popen(['echo', '-n', 'hello\nworld'], shell=False, stdout=PIPE, stderr=PIPE) as _p:
            # Wrap the std streams from the Popen objects whenever you want to use their
            # readline, readlines or read methods.
            _stdout, _stderr = (wrapStrBytesFunctions(stream) for stream in (_p.stdout, _p.stderr))
            _out, _err = (stream.readlines() for stream in (_stdout, _stderr))
            self.assertEqual((_out, _err), (['hello\n', 'world'], []))

        # Use forceStrArgRet with functions like b64encode/b64decode to automatically make their
        # arguments bytes objects and return values strings.
        _encoded = forceStrArgRet(b64encode)('hello')
        self.assertEqual(_encoded, 'aGVsbG8=')
        _decoded = forceStrArgRet(b64decode)(_encoded)
        self.assertEqual(_decoded, 'hello')

    
    def test_UnicodeWrap(self):
        with Popen(['echo', '-n', '-e', six.u('\u0263')], shell=False, stdout=PIPE, stderr=PIPE) as _p:
            _out, _err = wrapStrBytesFunctions(_p).communicate()
            self.assertEqual(_out, six.u('\u0263'))
     


if __name__ == '__main__':
    unittest.main()
