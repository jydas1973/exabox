#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_opctlmgr.py /main/2 2024/03/14 10:39:16 nisrikan Exp $
#
# tests_opctlmgr.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_opctlmgr.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    nisrikan    02/16/22 - Creation
#
import os
import json
import copy
import pwd
import logging
import logging.handlers
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.ovm.opctlMgr import ebOpctlMgr

class ebTestOpctlMgr(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        
    @classmethod
    def tearDownClass(self):
        log_basefolder = os.getcwd()
        log_folder = os.path.join(os.path.join(log_basefolder, "exadatainfrastructure"))
        os.system("rm -rf {0}".format(log_folder))
                        
    def prepare_context(self, ocps_filename, exacc_env):
        # set ocps json path
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["ocps_jsonpath"] = ocps_filename
        gContext.mSetConfigOptions(writableGConfigOptions)
        
        # set env to exacc
        if exacc_env is True:
            self.mGetClubox()._exaBoxCluCtrl__ociexacc = True
        else:
            self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
                    
    def prepare_log_mock_commands(self):
        #Prepare cmds
        cmds = {
            self.mGetRegexLocal():[
                [
                    exaMockCommand("/usr/bin/sudo /usr/bin/mkdir -p -m 744 /opt/oci/exacc/opctl/exadatainfrastructure/log",
                        aRc=0),
                    exaMockCommand("/usr/bin/sudo /usr/bin/chown -R ecra /opt/oci/exacc/opctl",
                        aRc=0)
                ],
            ]
        }
        self.mPrepareMockCommands(cmds)
        
        log_basefolder = os.getcwd()
        log_folder = os.path.join(os.path.join(log_basefolder, "exadatainfrastructure"), "log")
        os.system("mkdir -p {0}".format(log_folder))
        
        user = pwd.getpwuid(os.getuid())[0]
        os.system("chown -R {0} {1}".format(user, log_basefolder))
                        
    def test_invalid_env(self):
        """
        non exacc env
        """
        ebox = self.mGetClubox()
        options = self.mGetContext().mGetArgsOptions()
        options.jsonconf = self.mGetPayload()
        ocps = "some_ocps_json_filename"
        self.prepare_context(ocps_filename=ocps, exacc_env=False)
        
        # fails because of non-exacc env
        ebox = self.mGetClubox()
        opctl_mgr = ebOpctlMgr(ebox, "", "", None)
        self.assertEqual(opctl_mgr.mExecuteCmd(options), -1)
                
    def test_execute_cmd(self):
        """
        invalid scenarios include
            - no clustername
            - no patch xml config
            - not having resource id
        """
        ocps = "some_ocps_json_filename"
        self.prepare_context(ocps_filename=ocps, exacc_env=True)
        options = self.mGetContext().mGetArgsOptions()
        options.jsonconf = self.mGetPayload()

        # fails because of invalid clustername
        ebox = self.mGetClubox()
        opctl_mgr = ebOpctlMgr(ebox, None, "", None)
        self.assertEqual(opctl_mgr.mExecuteCmd(options), -1)
        
        # fails because of invalid patch config
        key = "some_file_name"
        opctl_mgr = ebOpctlMgr(ebox, key, None, None)
        self.assertEqual(opctl_mgr.mExecuteCmd(options), -1)
        
        # fails because of invalid resource id
        patch_config = "some_file_name"
        opctl_mgr = ebOpctlMgr(ebox, key, patch_config, None)
        self.assertEqual(opctl_mgr.mExecuteCmd(options), -1)        
        
        
    def test_install_in_cps(self):
        """
        invalid scenarios include
            - trying to install an incorrect rpm
                - rpmVersion in incorrect
                - rpm is not present in /u01/downloads/opctl
                - rpm is present but install failure
        """
        ocps = "some_ocps_json_filename"
        self.prepare_context(ocps_filename=ocps, exacc_env=True)
        ebox = self.mGetClubox()  
        
        key = "some_cluster_name"
        patch_config = "some_patch_config_file"
        opctl_mgr = ebOpctlMgr(ebox, key, patch_config, None)
        
        options = self.mGetContext().mGetArgsOptions()
        options.jsonconf = self.mGetPayload()
        options.jsonconf["usercmd"] = "assign"
        options.jsonconf["operation"] = "install"
        options.jsonconf["assignInfo"] = dict()
        options.jsonconf["resourceType"] = "exadatainfrastructure"
        options["unittest"] = True
                
        # "rpmVersion" is not present in input json        
        self.prepare_log_mock_commands()              
        self.assertEqual(opctl_mgr.mExecuteCmd(options), -1)
        
        # rpm is not present in folder
        rpm_name = "junk"
        options.jsonconf["assignInfo"]["rpmVersion"] = rpm_name
        rpm_find_cmd_failure = {
            self.mGetRegexLocal():[
                [
                    exaMockCommand("/usr/bin/find /u01/downloads/opctl/ -name " + rpm_name + ".rpm",
                        aRc=-1)
                ]
            ]
        }
        self.mPrepareMockCommands(rpm_find_cmd_failure)
        self.assertEqual(opctl_mgr.mExecuteCmd(options), -1)
        
        # rpm install failure
        mock_rpm_path = "/u01/downloads/opctl/" + rpm_name + ".rpm"
        rpm_install_cmd_failure = {
            self.mGetRegexLocal():[
                [
                    exaMockCommand("/usr/bin/find /u01/downloads/opctl/ -name " + rpm_name + ".rpm",
                        aRc=0, aStdout=mock_rpm_path),
                    exaMockCommand("/usr/bin/sudo /bin/rpm -U --force " + mock_rpm_path, aRc=-1)
                ]
            ]
        }
        self.mPrepareMockCommands(rpm_install_cmd_failure)
        self.assertEqual(opctl_mgr.mExecuteCmd(options), -1)
        
        # valid install in cps but not in other nodes
        remote_cps = " "
        rpm_install_in_nodes_failure = {
            self.mGetRegexLocal():[
                [
                    exaMockCommand("/usr/bin/find /u01/downloads/opctl/ -name " + rpm_name + ".rpm",
                        aRc=0, aStdout=mock_rpm_path),
                    exaMockCommand("/usr/bin/sudo /bin/rpm -U --force " + mock_rpm_path, aRc=0),
                    exaMockCommand("/bin/rpm -qa opctl-backend-core*", aRc=0, aStdout=rpm_name),
                    exaMockCommand("""/usr/bin/sudo -u ecra sh /usr/local/opctl/shell/opctlExacloud.sh install '{0}' {1} {2} {3} {4} """.format( 
                                    json.dumps(options.jsonconf),key,remote_cps,ocps,patch_config), aRc=-1)
                ]
            ]
        }
        # currently is failing due exception in mocking
        self.mPrepareMockCommands(rpm_install_in_nodes_failure)  
        self.assertEqual(opctl_mgr.mExecuteCmd(options), -1)
               
if __name__ == "__main__":
    unittest.main()
