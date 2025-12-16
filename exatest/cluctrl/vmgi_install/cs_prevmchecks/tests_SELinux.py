import json
import unittest
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo

"""
"se_linux" :  {
                "infraComponent" :
                    [
                        {
                            "mode": "disabled | enforcing | permissive",
                            "component": "dom0"
                            "targetcomponentName": "all" | [dom0_1, dom0_2,...],
                            "policy": <>
                        },
                        { 
                            "mode": "disabled | enforcing | permissive",
                            "component": "domU",
                            "targetComponentName": "all" | [domU_1, domU_2,...],
                            "policy": <>
                        },        
                        { 
                            "mode": "disabled | enforcing | permissive",
                            "component": "cell",
                            "targetComponentName": "all" | [cell_1, cell_2,...],
                            "policy": <>
                        }
                    ]
                }
"""
class testOptions(object): pass

class ebTestSELinux(ebTestClucontrol):
   
    @classmethod
    def setUpClass(self):
        super(ebTestSELinux, self).setUpClass(False, False)
    
    def createSELinuxPayload(self, updateToMode):
        seLinuxPayload = dict()
        infraComponentDom0 = dict()
        infraComponentDom0["mode"] = updateToMode
        infraComponentDom0["component"] = "dom0"
        infraComponentDom0["targetComponentName"] = "all"
        infraComponentDom0["policy"] = "dom0_policy"
        infraComponentDomU = dict()
        infraComponentDomU["mode"] = updateToMode
        infraComponentDomU["component"] = "domU"
        infraComponentDomU["targetComponentName"] = "all"
        infraComponentDomU["policy"] = "dom0_policy"
        infraComponentCell = dict()
        infraComponentCell["mode"] = updateToMode
        infraComponentCell["component"] = "cell"
        infraComponentCell["targetComponentName"] = "all"
        infraComponentCell["policy"] = "cell_policy"

        infraComponent = dict()
        infraComponent["infraComponent"] = [infraComponentDom0, infraComponentDomU, infraComponentCell]
        seLinuxPayload["se_linux"] = infraComponent
        return seLinuxPayload

    def template_SELinux(self, aSeLinuxPayload, aSeLinuxCurrentConfig):
        '''
        Test mSetSeLinux against Status of SELinux=aSeLinuxCurrentConfig and key se_linux aSeLinuxPayload
            aSeLinuxPayload -> string ["enabled" | "disabled"]
            aSeLinuxCurrentConfig -> string ["enabled" | "disabled"]
        '''     
        #Prepare env variables
        ebLogInfo("")
        ebLogInfo("SELinux current status is: {}".format(aSeLinuxCurrentConfig))
        fullOptions = testOptions()
        fullOptions.jsonconf = aSeLinuxPayload

        self.mGetClubox().mSetOptions(fullOptions)
        _selinux = self.mGetClubox().mGetSELinuxMode("dom0")
        ebLogInfo("Key se_linux key should be added to payload with value: {0}".format(_selinux))
        _status_dict = { "disabled": "disabled", "permissive": "permissive", "enforcing" : "enforcing" }
        _boolean_dict = {True: 1, False: 0}
        _expected_rc = True
        if _selinux == aSeLinuxCurrentConfig:
            _expected_rc = False

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("\/bin\/grep", aRc=0, aStdout="SELINUX={0}".format(aSeLinuxCurrentConfig)),
                    exaMockCommand("/bin/sed -i --follow-symlinks", aRc=0),
                    exaMockCommand("/bin/touch /.autorelabel", aRc=0)
                ]
            ]
        }

        # Init new Args
        self.mPrepareMockCommands(_cmds)
        
        # Execute Clucontrol functions
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _node = exaBoxNode(self.mGetContext())
            _node.mConnect(aHost = _dom0)
            _sereturned = self.mGetClubox().mSetSeLinux(_node, _selinux, "dom0") 
            ebLogInfo("My function returns: {0}".format(_sereturned))
            self.assertEqual(_boolean_dict[_sereturned], _expected_rc)
            _node.mDisconnect()

    def test_PermissiveDisabled(self):
        self.template_SELinux(self.createSELinuxPayload("permissive"), "disabled")

    def test_EnforcingDisabled(self):
        self.template_SELinux(self.createSELinuxPayload("enforcing"), "disabled")

    def test_DisabledDisabled(self):
        self.template_SELinux(self.createSELinuxPayload("disabled"), "disabled")

    def test_PermissivePermissive(self):
        self.template_SELinux(self.createSELinuxPayload("permissive"), "permissive")

    def test_EnforcingPermissive(self):
        self.template_SELinux(self.createSELinuxPayload("enforcing"), "permissive")

    def test_DisabledPermissive(self):
        self.template_SELinux(self.createSELinuxPayload("disabled"), "permissive")

    def test_PermissiveEnforcing(self):
        self.template_SELinux(self.createSELinuxPayload("permissive"), "enforcing")

    def test_EnforcingEnforcing(self):
        self.template_SELinux(self.createSELinuxPayload("enforcing"), "enforcing")

    def test_DisabledEnforcing(self):
        self.template_SELinux(self.createSELinuxPayload("disabled"), "enforcing")

    def test_autoRelabelFail(self):
        ebLogInfo("")
        ebLogInfo("Testing failure of autorelabel file creation.")
        fullOptions = testOptions()
        fullOptions.jsonconf = self.createSELinuxPayload("enforcing")

        self.mGetClubox().mSetOptions(fullOptions)
        _selinux = self.mGetClubox().mGetSELinuxMode("dom0")
        ebLogInfo("Key se_linux key should be added to payload with value: {0}".format(_selinux))
        aSeLinuxCurrentConfig = "disabled"

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("\/bin\/grep", aRc=0, aStdout="SELINUX={0}".format(aSeLinuxCurrentConfig)),
                    exaMockCommand("/bin/sed -i --follow-symlinks", aRc=0),
                    exaMockCommand("/bin/touch /.autorelabel", aRc=1)
                ]
            ]
        }

        self.mPrepareMockCommands(_cmds)
        for _dom0, _ in self.mGetClubox().mReturnDom0DomUPair():
            _node = exaBoxNode(self.mGetContext())
            _node.mConnect(aHost = _dom0)
            operationStatusDict = dict()
            _sereturned = self.mGetClubox().mSetSeLinux(_node, _selinux, "dom0", operationStatusDict) 
            ebLogInfo("mSetSeLinux function returns: {0}".format(_sereturned))
            self.assertEqual(_sereturned, False)
            self.assertEqual(operationStatusDict["modeUpdate"], "Failure")
            self.assertEqual(operationStatusDict["policyUpdate"], "Success")
            _node.mDisconnect()
            break

if __name__ == "__main__":
    unittest.main()

