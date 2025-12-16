#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/tools/ssh/tests_clusshkey.py /main/1 2021/12/15 20:59:58 ndesanto Exp $
#
# tests_clusshkey.py
#
# Copyright (c) 2021, Oracle and/or its affiliates.
#
#    NAME
#      tests_clusshkey.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ndesanto    12/14/21 - Increase coverage for ndesanto files.
#    ndesanto    12/14/21 - Creation
#

import os
import unittest
import exabox.ovm.clusshkey as clusshkey

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol


class ebTest_clubackup(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        self._authorized_keys_path = "exabox/exatest/tools/ssh/resources/authorized_keys"
        self._key_path = "exabox/exatest/tools/ssh/resources/id_rsa.pub"
        self._authorized_keys = None
        with open(self._authorized_keys_path, "r") as fd:
            self._authorized_keys = fd.read()
        self._key = None
        with open(self._key_path, "r") as fd:
            self._key = fd.read()

    def test_log_backup(self):
        _protocol, _key, _user, _comment = clusshkey.get_sshkey_and_parts(
            self._key)
        self.assertIsNotNone(_protocol)
        self.assertIsNotNone(_key)
        self.assertIsNotNone(_user)
        self.assertEqual("ssh-rsa", _protocol)
        self.assertEqual("ndesanto@slc14uwt", _user)

        self.assertEqual(_key, clusshkey.get_only_sshkey(self._key))
        self.assertEqual(_user, clusshkey.get_sshkey_user(self._key))

        _raw = clusshkey.to_raw_str(self._key)
        self.assertNotEqual(self._key, _raw)

if __name__ == '__main__':
    unittest.main(warnings='ignore')
