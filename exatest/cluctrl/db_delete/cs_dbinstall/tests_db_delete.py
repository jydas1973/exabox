#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/db_delete/cs_dbinstall/tests_db_delete.py /main/3 2021/03/26 10:22:29 jesandov Exp $
#
# tests_db_delete.py
#
# Copyright (c) 2020, 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_db_delete.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      Unittesting class to cs_dbinstall.py containers files
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    jesandov    07/23/20 - Creation


import unittest
 
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
 
class ebTestDbDelete(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestDbDelete, self).setUpClass()
 
    def test_mRemoveSshKeys(self):
 
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /etc/passwd | grep .*", aStdout="/root"),
                    exaMockCommand("sed --follow-symlinks -i '/OEDA_PUB/d' /root/.*"),
                    exaMockCommand("sed --follow-symlinks -i '/EXACLOUD_KEY/d' /root/.*"),
                    exaMockCommand("cat /etc/passwd | grep .*", aStdout="/home/opc"),
                    exaMockCommand("sed --follow-symlinks -i '/OEDA_PUB/d' /home/opc/.*"),
                    exaMockCommand("sed --follow-symlinks -i '/EXACLOUD_KEY/d' /home/opc/.*")
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True)
                ]
            ]
        }
 
        #Init new Args
        self.mPrepareMockCommands(_cmds)

        #Execute the clucontrol function
        self.mGetClubox().mRemoveSshKeys()

 
if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end file
