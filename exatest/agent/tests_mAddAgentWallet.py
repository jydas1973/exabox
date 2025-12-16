#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/agent/tests_mAddAgentWallet.py /main/3 2021/06/01 12:19:51 jfsaldan Exp $
#
# tests_mAddAgentWallet.py
#
# Copyright (c) 2021, Oracle and/or its affiliates. 
#
#    NAME
#      tests_mAddAgentWallet.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    jfsaldan    05/27/21 - Bug 32921511 - ADB-CC:BB:CREATE STARTER DB FAILED
#                           -- OEDA ERROR WHILE APPLYING SECURITY FIXES
#    jfsaldan    02/10/21 - Creation
#
import unittest
import os
import base64
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.core.Error import ExacloudRuntimeError

class ebTestAgentWallet(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass()


    def template_test_dbcs_wallet(self, aWalletPath: str, aRcDict: dict):
        """
        This is the template used to test clucontrol.mAddAgentWallet function 
        when attempting to run the steps for DBCS/CP agent wallet creation
        """

         # Adittional resources
        _rc_mkdir_dir = aRcDict["mkdir_dir"]
        _rc_chmod_dir = aRcDict["chmod_dir"]
        _rc_chown_dir = aRcDict["chown_dir"]

        _wallet_name = "cwallet.sso"
        _dbcs_wallet = "DBCSAgentWallet.sso"
        _dbcs_target_dir = "/opt/oracle/dcs/auth"
        _dbcs_wallet_path = os.path.join(_dbcs_target_dir, _wallet_name)
        _cps_wallet = "CPSAgentWallet.sso.b64"
        _cps_target_dir = "/var/opt/oracle/dbaas_acfs/dbagent/dbagent_wallet"
        _cps_wallet_path = os.path.join(_cps_target_dir, _wallet_name)
        
        # Create args structure
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand(f"/usr/bin/mkdir -p {_dbcs_target_dir}", aRc=_rc_mkdir_dir),
                    exaMockCommand(f"/usr/bin/mkdir -p {_cps_target_dir}", aRc=_rc_mkdir_dir),
                    exaMockCommand(f"/usr/bin/chmod 700 {_dbcs_target_dir}", aRc=_rc_chmod_dir),
                    exaMockCommand(f"/usr/bin/chmod 700 {_cps_target_dir}", aRc=_rc_chmod_dir),
                    exaMockCommand(f"/usr/bin/chown opc:opc {_dbcs_target_dir}", aRc=_rc_chown_dir),
                    exaMockCommand(f"/usr/bin/chown oracle:oinstall {_cps_target_dir}", aRc=_rc_chown_dir),
                    exaMockCommand(f"/usr/bin/base64 -d {_dbcs_wallet_path}.b64 > {_dbcs_wallet_path}", aRc=0),
                    exaMockCommand(f"/usr/bin/base64 -d {_cps_wallet_path}.b64 > {_cps_target_dir}", aRc=0),
                    exaMockCommand(f"/usr/bin/shred {_dbcs_wallet_path}.b64 -vun 7", aRc=0),
                    exaMockCommand(f"/usr/bin/shred {_cps_wallet_path}.b64 -vun 7", aRc=0),
                    exaMockCommand(f"/usr/bin/shred {_dbcs_wallet_path}.b64 -vun 3", aRc=0),
                    exaMockCommand(f"/usr/bin/shred {_cps_wallet_path}.b64 -vun 3", aRc=0),
                    exaMockCommand(f"/usr/bin/chmod 700 {_dbcs_wallet_path}", aRc=0),
                    exaMockCommand(f"/usr/bin/chmod 700 {_cps_wallet_path}", aRc=0),
                    exaMockCommand(f"/usr/bin/chown opc:opc {_dbcs_wallet_path}", aRc=0),
                    exaMockCommand(f"/usr/bin/chown oracle:oinstall {_cps_wallet_path}", aRc=0),
                    exaMockCommand(f"/bin/scp .* {_dbcs_target_dir}"),
                    exaMockCommand(f"/bin/scp .* {_cps_wallet_path}")

                ]
            ]
        }

        # Init new Args
        self.mPrepareMockCommands(_cmds)

        #Prepare the enviroment variables
        
        # Execute the clucontrol function
        self.mGetClubox().mAddAgentWallet(aWalletPath)
        return 0

    def test_dbcs_wallet(self):
        # Create file to use as dummy wallet file 

        #_local_zip = self.createZip()
        cps_wallet, dbcs_wallet = self.createWallets()
        _wallets_path = os.path.dirname(cps_wallet)
        ebLogInfo(f"Created dummy wallets in: {_wallets_path}")
        ebLogInfo("Test- Below should work ok, vmerase not used")
        _aRcDict = {}
        _aRcDict["mkdir_dir"] = 0
        _aRcDict["chmod_dir"] = 0
        _aRcDict["chown_dir"] = 0
        _aRcDict["chmod_wallet"] = 0
        _aRcDict["chown_wallet"] = 0
        self.assertEqual(0, self.template_test_dbcs_wallet(_wallets_path, _aRcDict))
        os.unlink(cps_wallet)
        os.unlink(dbcs_wallet)

        cps_wallet, dbcs_wallet = self.createWallets()
        _wallets_path = os.path.dirname(cps_wallet)
        ebLogInfo(f"Created dummy file in: {_wallets_path}")
        ebLogInfo("Test- Below should work ok, vmerase set to invalid value")
        _aRcDict = {}
        _aRcDict["mkdir_dir"] = 0
        _aRcDict["chmod_dir"] = 0
        _aRcDict["chown_dir"] = 0
        _aRcDict["chmod_wallet"] = 0
        _aRcDict["chown_wallet"] = 0
        _shred_iterations = 3
        self.mGetContext().mSetConfigOption("vmerase_pass","vmerase")
        self.assertEqual(0, self.template_test_dbcs_wallet(_wallets_path, _aRcDict))
        os.unlink(cps_wallet)
        os.unlink(dbcs_wallet)

        
        cps_wallet, dbcs_wallet = self.createWallets()
        _wallets_path = os.path.dirname(cps_wallet)
        ebLogInfo(f"Created dummy file in: {_wallets_path}")
        ebLogInfo("Test- Below should work ok, vmerase set to 7pass")
        _aRcDict = {}
        _aRcDict["mkdir_dir"] = 0
        _aRcDict["chmod_dir"] = 0
        _aRcDict["chown_dir"] = 0
        _aRcDict["chmod_wallet"] = 0
        _aRcDict["chown_wallet"] = 0
        _shred_iterations = 3
        self.mGetContext().mSetConfigOption("vmerase_pass","7pass")
        self.assertEqual(0, self.template_test_dbcs_wallet(_wallets_path, _aRcDict))
        os.unlink(cps_wallet)
        os.unlink(dbcs_wallet)

        cps_wallet, dbcs_wallet = self.createWallets()
        _wallets_path = os.path.dirname(cps_wallet)
        ebLogInfo(f"Created dummy file in: {_wallets_path}")
        ebLogInfo("Test - Below should work ok, vmerase set to None")
        _aRcDict = {}
        _aRcDict["mkdir_dir"] = 0
        _aRcDict["chmod_dir"] = 0
        _aRcDict["chown_dir"] = 0
        _aRcDict["chmod_wallet"] = 0
        _aRcDict["chown_wallet"] = 0
        _shred_iterations = 3
        self.mGetContext().mSetConfigOption("vmerase_pass", None)
        self.assertEqual(0, self.template_test_dbcs_wallet(_wallets_path, _aRcDict))
        os.unlink(cps_wallet)
        os.unlink(dbcs_wallet)
        
        cps_wallet, dbcs_wallet = self.createWallets()
        _wallets_path = os.path.dirname(cps_wallet)
        ebLogInfo(f"Created dummy file in: {_wallets_path}")
        ebLogInfo("Test- Below should work ok, vmerase set to 3PASS")
        _aRcDict = {}
        _aRcDict["mkdir_dir"] = 0
        _aRcDict["chmod_dir"] = 0
        _aRcDict["chown_dir"] = 0
        _aRcDict["chmod_wallet"] = 0
        _aRcDict["chown_wallet"] = 0
        _shred_iterations = 3
        self.mGetContext().mSetConfigOption("vmerase_pass", "3PASS")
        self.assertEqual(0, self.template_test_dbcs_wallet(_wallets_path, _aRcDict))
        os.unlink(cps_wallet)
        os.unlink(dbcs_wallet)

        ebLogInfo("Test- This should not run the flow, but also dont fail")
        self.assertEqual(0, self.template_test_dbcs_wallet("~/", _aRcDict))
        
        '''
        ebLogInfo("Test- Below should raise an exception, zip bundle wallet doesnt exist")
        _empty_zip = "/scratch/jfsaldan/tmp/empty.zip"
        _local_zip = self.createZip(isEmpty=True)
        self.assertRaises(ExacloudRuntimeError, lambda : self.template_test_dbcs_wallet(_local_zip, _aRcDict))
        '''

        cps_wallet, dbcs_wallet = self.createWallets()
        _wallets_path = os.path.dirname(cps_wallet)
        ebLogInfo("Test- Below should raise an exception, mkdir fails")
        _aRcDict["mkdir_dir"] = 1
        _aRcDict["chmod_dir"] = 0
        _aRcDict["chown_dir"] = 0
        self.assertRaises(ExacloudRuntimeError, lambda : self.template_test_dbcs_wallet(_wallets_path, _aRcDict))
        os.unlink(cps_wallet)
        os.unlink(dbcs_wallet)

        cps_wallet, dbcs_wallet = self.createWallets()
        _wallets_path = os.path.dirname(cps_wallet)
        ebLogInfo("Test- Below should raise an exception, chmod on dir fails")
        _aRcDict["mkdir_dir"] = 0
        _aRcDict["chmod_dir"] = 1
        _aRcDict["chown_dir"] = 0
        self.assertRaises(ExacloudRuntimeError, lambda : self.template_test_dbcs_wallet(_wallets_path, _aRcDict))
        os.unlink(cps_wallet)
        os.unlink(dbcs_wallet)
        
        cps_wallet, dbcs_wallet = self.createWallets()
        _wallets_path = os.path.dirname(cps_wallet)
        ebLogInfo("Test- Below should raise an exception, chown on dir fails")
        _aRcDict["mkdir_dir"] = 0
        _aRcDict["chmod_dir"] = 0
        _aRcDict["chown_dir"] = 1
        self.assertRaises(ExacloudRuntimeError, lambda : self.template_test_dbcs_wallet(_wallets_path, _aRcDict))
        os.unlink(cps_wallet)
        os.unlink(dbcs_wallet)
        
     


    def createDummyWallet(self, aWalletName: str) -> str:
        '''
        Create a dummy wallet file for testing purposes only
        param aWalletName: String of wallet name to create
        returns wallet_path: Path of dummy file created
        ''' 
        _path = self.mGetUtil().mGetOutputDir()
        _wallet_path = os.path.join(_path, aWalletName)
        _some_text = "Arbitrary text for test"
        with open(_wallet_path, mode='w') as fd:
            fd.write(base64.b64encode(_some_text.encode("utf-8")).decode("utf-8"))
        return os.path.abspath(_wallet_path)

    def createWallets(self) -> str:
        '''
        Helper function to create dbas and cps wallets
        returns string representing abs path of two wallets created
        '''
        cps_dir = self.createDummyWallet("CPSAgentWallet.b64")
        dbcs_dir = self.createDummyWallet("DBCSAgentWallet.b64")
        #
        # Since cps_dir and dbcs_dir dirnames are the same we can safely return
        # any of them
        return os.path.abspath(cps_dir), os.path.abspath(dbcs_dir)
        



if __name__ == '__main__':
    unittest.main()
