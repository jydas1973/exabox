#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/remoteec/tests_exacloud_endpoint.py /main/1 2023/12/01 00:48:35 hgaldame Exp $
#
# tests_exacloud_endpoint.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      tests_exacloud_endpoint.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    hgaldame    11/29/23 - 36055367 - oci/exacc: unrecognized arguments error
#                           executing exacloud commands through remote manager
#    hgaldame    11/29/23 - Creation
#
import unittest
import uuid
import os

from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol

from exabox.managment.src.ExacloudCmdEndpoint import ExacloudCmdEndpoint
from unittest.mock import patch, Mock

class ebTestExacloudCmdEndpoint(ebTestClucontrol):


    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateRemoteEC=True)
        os.makedirs("log/threads", exist_ok=True)

    def test_000_exacloud_split_cmd(self):

        # Init Args for endpoint call
        _shared = self.mGetUtil().mGetRemoteEC().mGetShared()

        _body = {
            "args": "--help --debug --verbose"
        }

        _response = {}
        _endpoint = ExacloudCmdEndpoint(None, _body, _response, _shared)
        with patch.object(_endpoint, "mCreateBashProcess") as _spy_method:
            exacloud_bin_path = os.path.join(self.mGetUtil().mGetExacloudPath(),"bin","exacloud")
            _endpoint.mPost()
            _spy_method.assert_called_once_with([[exacloud_bin_path,"--help","--debug","--verbose"]],aName="execute [--help --debug --verbose]")



if __name__ == '__main__':
    unittest.main(warnings='ignore')


