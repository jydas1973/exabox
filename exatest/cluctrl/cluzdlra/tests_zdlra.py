import unittest
from unittest import mock
from unittest.mock import patch, MagicMock, PropertyMock, mock_open
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.exawatcher import exaBoxExaWatcher, cleanupExaWatcherLogs, deleteOldLogs
from exabox.core.Error import ExacloudRuntimeError
import os
import shutil

class TestZdlra(ebTestClucontrol):

    def setUp(self):
        #Ensure every test begin with standard conf
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__timeout_ecops = 1
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True

    def test_mPatchXmlZdlra(self):
        cluctrl = self.mGetClubox()

        zdlra_xml = \
            'exabox/exatest/cluctrl/cluzdlra/resources/rack_nonzdlra.xml'
        shutil.copy2('exabox/exatest/cluctrl/cluzdlra/resources/rack_nonzdlra_sample.xml', zdlra_xml)
        os.chmod(zdlra_xml, 0o744)
        # load zdlra XML

        jsonconf = cluctrl.mGetArgsOptions().jsonconf

        cluctrl.mSetConfigPath(zdlra_xml)
        cluctrl.mSetPatchConfig(zdlra_xml)
        cluctrl.mParseXMLConfig(jsonconf)

        _cmds = {
            self.mGetRegexDom0():
                [[
                    exaMockCommand("/bin/test -e.*", aRc=0,  aPersist=True),
                ]],
            self.mGetRegexLocal():
                [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True)
                ]],
            self.mGetRegexCell(): [[
                    exaMockCommand("i/opt/oracle/cell/cellsrv/bin/cellcli -e list griddisk | /bin/grep 'CATALOG'", aRc=1),
                ]],

        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()

        zdlra_flag = cluctrl.mGetZDLRA().mCheckZdlraInEnv()
        self.assertEqual(zdlra_flag, False)

        cluctrl.mGetZDLRA().mPatchXmlZdlra()
        cluctrl.mSetConfigPath(zdlra_xml)
        cluctrl.mSetPatchConfig(zdlra_xml)
        cluctrl.mParseXMLConfig(jsonconf)

        zdlra_flag = cluctrl.mGetZDLRA().mCheckZdlraInEnv()
        self.assertEqual(zdlra_flag, True)

    def test_mPatchClusterZdlraDisks(self):

        _cmds = {
            self.mGetRegexCell(): [[
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout="X7-2", aRc=0),
                ]],
            self.mGetRegexLocal():
                [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                ]],
            self.mGetRegexDom0():
                [[
                    exaMockCommand("/bin/test -e.*", aRc=0,  aPersist=True),
                ]]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        self.mGetClubox()._exaBoxCluCtrl____enable_quorum = False
        cluctrl.mGetZDLRA().mPatchClusterZdlraDisks(self.mGetClubox()._exaBoxCluCtrl__storage, aOptions=None)

        _cluster = cluctrl.mGetClusters().mGetCluster()
        _cludgroups = _cluster.mGetCluDiskGroups()
        for _dgid in _cludgroups:
            if _dgid.find('datadg') != -1:
                _data_dg_id = _dgid

        _catalogConfig = self.mGetClubox()._exaBoxCluCtrl__storage.mGetDiskGroupConfig(_data_dg_id)
        qdisk = _catalogConfig.mGetQuorumDisk()
        self.assertEqual(qdisk.text, 'true')
        dsize = _catalogConfig.mGetAcfsVolumeSize()
        self.assertEqual(dsize, '122')
        asmss = self.mGetClubox().mGetClusters().mGetCluster().mGetCluAsmScopedSecurity()
        self.assertEqual(asmss, 'true')

        self.mGetClubox().mSetEnableAsmss('False')
        cluctrl.mGetZDLRA().mPatchClusterZdlraDisks(self.mGetClubox()._exaBoxCluCtrl__storage, aOptions=None)
        asmss = self.mGetClubox().mGetClusters().mGetCluster().mGetCluAsmScopedSecurity()
        self.assertEqual(asmss, 'false')




	    
    def test_mCreateWallet(self):
        _cmds = {
            self.mGetRegexLocal():
                [[  
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                ]],
            self.mGetRegexVm():
                [[
                    exaMockCommand("/u01/app/12.2.0.1/grid/bin/mkstore -wrl.*"),
                    exaMockCommand("chown .*"),
                    exaMockCommand("/bin/test -e.*", aRc=1)
                ]]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        cluctrl.mGetZDLRA().mCreateWallet()

    def test_mDelWalletEntry(self):
        _cmds = {
            self.mGetRegexLocal():
                [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                ]],
            self.mGetRegexVm():
                [[
                    exaMockCommand("/u01/app/12.2.0.1/grid/bin/mkstore -wrl.*-deleteEntry.*"),
                    exaMockCommand("/u01/app/12.2.0.1/grid/bin/mkstore -wrl.* -viewEntry.*", aStdout="passwd=pwd"),
                    exaMockCommand("/bin/test -e.*", aRc=1)
                ]]
        }
        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        cluctrl.mGetZDLRA().mDelWalletEntry("wkey")
        key = cluctrl.mGetZDLRA().mGetWalletViewEntry("wkey")
        self.assertEqual(key, None)

    def test_mAddWalletEntry(self):
        _cmds = {
            self.mGetRegexLocal():
                [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                ]],
            self.mGetRegexVm():
                [[
                    exaMockCommand("/u01/app/12.2.0.1/grid/bin/mkstore -wrl.* -createEntry.*"),
                    exaMockCommand("/u01/app/12.2.0.1/grid/bin/mkstore -wrl.*-deleteEntry.*"),
                    exaMockCommand("/u01/app/12.2.0.1/grid/bin/mkstore -wrl.* -viewEntry.*", aStdout="passwd=pwd"),
                    exaMockCommand("/bin/test -e.*", aRc=1)
                ]]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        key = cluctrl.mGetZDLRA().mAddWalletEntry("wkey", "pwd")
        self.assertEqual(key, "wkey")
        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        cluctrl.mGetZDLRA().mDelWalletEntry("wkey")
        key = cluctrl.mGetZDLRA().mGetWalletViewEntry("wkey")
        self.assertEqual(key, None)


    def test_mAddWalletEntry2(self):
        _cmds = {
            self.mGetRegexLocal():
                [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                ]],
            self.mGetRegexVm():
                [[
                    exaMockCommand("/u01/app/12.2.0.1/grid/bin/mkstore -wrl.* -createEntry.*"),
                    exaMockCommand("/bin/test -e.*", aRc=1)
                ]]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        key = cluctrl.mGetZDLRA().mAddWalletEntry("wkey", "pwd")
        self.assertEqual(key, "wkey")


    def test_mGetWalletViewEntry(self):
        _cmds = {
            self.mGetRegexLocal():
                [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                ]],
            self.mGetRegexVm():
                [[
                    exaMockCommand("/u01/app/12.2.0.1/grid/bin/mkstore -wrl.* -viewEntry.*", aStdout="passwd=pwd"),
                    exaMockCommand("/bin/test -e.*", aRc=1)
                ]]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        key = cluctrl.mGetZDLRA().mGetWalletViewEntry("wkey")
        self.assertEqual(key, "pwd")

    def test_apages(self):
        _cmds = {
            self.mGetRegexDom0():
                [[
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("xm li .*-l | grep.*maxmem'.*", aStdout="10"),
                ]],
            self.mGetRegexVm():
                [[
                    exaMockCommand(".*Hugepagesize.*", aStdout="10"),
                    exaMockCommand("/bin/test -e.*", aRc=1),

                    # Get current value as 100
                    exaMockCommand(".*/usr/sbin/sysctl -n vm.nr_hugepages.*", aStdout="100", aRc=0),
                    exaMockCommand("cat /etc/sysctl.conf", aStdout="vm.nr_hugepages = 100"),

                    # Modify value to 0
                    exaMockCommand("cp /etc/sysctl.conf"),
                    exaMockCommand("/bin/sed -i.*nr_hugepages.*sysctl", aRc=0),
                    exaMockCommand("/usr/sbin/sysctl -p", aRc=0),

                    # Get the new value as 0
                    exaMockCommand(".*/usr/sbin/sysctl -n vm.nr_hugepages.*", aStdout="0", aRc=0),
                    exaMockCommand("cat /etc/sysctl.conf", aStdout="vm.nr_hugepages = 0"),
                ]]

        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        key = cluctrl.mGetZDLRA().mUpdateHugePages()

    def test_mdeleteDG_list(self):

        _cmds = {
            self.mGetRegexCell(): [[
                    exaMockCommand("cellcli -e list griddisk | grep 'CATALOG\|DELTA'", aStdout="DG1"),
                ]],
            self.mGetRegexLocal(): 
                [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                ]]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        cluctrl.mGetZDLRA().mDeleteGD(aListOnly=True, aCell=None)

    def test_mdeleteDG(self):

        _cmds = {
            self.mGetRegexCell(): [[
                    exaMockCommand("cellcli -e list griddisk | grep 'CATALOG\|DELTA'", aStdout="DG1"),
                    exaMockCommand("cellcli -e DROP GRIDDISK ALL PREFIX='CATALOG' FORCE"),
                    exaMockCommand("cellcli -e DROP GRIDDISK ALL PREFIX='DELTA' FORCE")
                ]],
            self.mGetRegexLocal(): 
                [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                ]]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        cluctrl.mGetZDLRA().mDeleteGD(aListOnly=False, aCell=None)

    @patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mRebootNodesIfNoVMExists')
    def test_menableHT(self, mockRebootNodesIfNoVMExists):

        _cmds = {
            self.mGetRegexDom0(): [[
                    #TODO : for amd to be done.
                    exaMockCommand("/usr/bin/lscpu | grep 'Model name' | grep -i 'Intel'", aRc=0, aPersist=True),
                    exaMockCommand("/usr/sbin/ubiosconfig export all -x /tmp/bios.*xml --expert_mode -y"),
                    exaMockCommand("/bin/grep -oP.*<Hyper-threading>.*", aStdout="Disabled", aRc=0),
                    exaMockCommand("/bin/sed.*<Hyper-threading>Disabled.*"),
                    exaMockCommand("/bin/sed.*<Hyper-threading>Enabled.*"),
                    exaMockCommand("/bin/grep.*<Hyper-Threading_ALL>.*"),
                    exaMockCommand("/bin/sed.*<Hyper-Threading_ALL>Disabled.*"),
                    exaMockCommand("/bin/sed.*<Hyper-Threading_ALL>Enabled.*"),
                    exaMockCommand("/usr/sbin/ubiosconfig import all -x /tmp/bios.*xml --expert_mode -y"),
                    exaMockCommand("/bin/rm -f /tmp/bios-.*xml")
                    #exaMockCommand("reboot")
                ],
                [
                    exaMockCommand("/usr/sbin/ubiosconfig export all -x /tmp/bios.*xml --expert_mode -y"),
                    exaMockCommand("/bin/grep.*", aStdout="Disabled", aRc=0),
                    #exaMockCommand("reboot")
                ]],
            self.mGetRegexLocal():
                [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True)
                ]]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        cluctrl.mGetZDLRA().mEnableDisableHT("Enabled", aOptions=None)
    
    def test_mGetGridHome(self):
        _cmds = {
            self.mGetRegexLocal():
                [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                ]],
            self.mGetRegexVm():
                [[
                    exaMockCommand("/bin/su - grid -c '/bin/cat /etc/oratab.* cut -f 2.*'", aStdout="/tmp/path", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/su - grid -c '/bin/cat /etc/oratab.* cut -f 1.*'", aStdout="sid1", aRc=0,  aPersist=True)
                ]]
        }

        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        cluctrl.mGetZDLRA().mGetGridHome("scaqab10client01vm08.us.oracle.com")

    def test_mCheckZdlraInEnv_CPUScaleupNonZdlra(self):
        cluctrl = self.mGetClubox()
        cluctrl.mSetCmd('vm_cmd')
        cluctrl.mGetArgsOptions().vmcmd = 'resizecpus'
        zdlra_flag = cluctrl.mGetZDLRA().mCheckZdlraInEnv()
        self.assertEqual(zdlra_flag, False)

    def test_mCheckZdlraInEnv_ExceptionRaised(self):
        cluctrl = self.mGetClubox()
        cluctrl.mSetCmd('vm_cmd')
        cluctrl.mGetArgsOptions().vmcmd = 'removecpus'
        with patch('exabox.ovm.cluzdlra.exaBoxNode.mIsConnectable', return_value=False):
            with self.assertRaises(ExacloudRuntimeError) as ex:
                zdlra_flag = cluctrl.mGetZDLRA().mCheckZdlraInEnv()

if __name__ == '__main__':
    unittest.main()

