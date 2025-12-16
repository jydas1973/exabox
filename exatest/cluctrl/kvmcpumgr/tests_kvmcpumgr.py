import unittest

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.kvmcpumgr import exaBoxKvmCpuMgr
import os
from unittest.mock import patch, Mock

class TestKVMCpuManager(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        self.maxDiff = None

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        get_gcontext().mSetConfigOption('kvm_var_size',None)
        get_gcontext().mSetConfigOption('kvm_u01_size',None)
        get_gcontext().mSetConfigOption('kvm_override_disable_pinning',False)
        self.mGetClubox().mRegisterVgComponents()

    def test_cpu_mgr(self):

        _vm_maker_list_vcpu = (
            "scaqab10client01vm08.us.oracle.com: Current: 16 Restart: 16\n"
            "               ----------\n"
            "Total VCPU required for reboot         : 16 (assumes restart situation)\n"
            "Host reserved PCPU                     : 4\n"
            "Available VCPU (now)                   : 184\n"
            "Available VCPU (delayed)               : 184\n"
            )
        _cmds = {
            self.mGetRegexVm(): [[
                    exaMockCommand("/opt/oracle.ExaWatcher/GetExaWatcherResults.sh --from.*"),
                    exaMockCommand("du -s.*", aStdout='1'),
                    exaMockCommand("ls .*/ExtractedResults", aStdout="file1"),
                    exaMockCommand("bin/rm -rf.*")
                ]],

            self.mGetRegexDom0(): [
                [   
                    exaMockCommand("/usr/sbin/vm_maker --list | /bin/grep running | /bin/grep scaqab10client01vm08.us.oracle.com", aStdout="scaqab10client01vm08.us.oracle.com(24)       : running"), #24 is the VMID
                ],
                [
                    exaMockCommand("/bin/test -e /opt/exacloud/vmconsole/history_console.py",aPersist=True),
                    exaMockCommand("/usr/bin/python3 /opt/exacloud/vmconsole/history_console.py --host scaqab10client01vm08.us.oracle.com --path /tmp/serial-exatest-scaqab10client01vm08.us.oracle.com.log.1",aPersist=True),
                    exaMockCommand("/bin/test -e /tmp/serial-exatest-scaqab10client01vm08.us.oracle.com.log.1",aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/serial-exatest-scaqab10client01vm08.us.oracle.com.log.1",aPersist=True),
                ],
                [
                    exaMockCommand(".*virsh nodeinfo.*", aStdout='100'),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu | /bin/grep 'Host reserved'.*", aStdout='4'),
                    #exaMockCommand("/usr/sbin/vm_maker --list | /bin/grep running | /bin/grep scaqab10client01vm08.us.oracle.com", aStdout="scaqab10client01vm08.us.oracle.com(24)       : running"),# 24 is the VMID
                    #exaMockCommand("/usr/sbin/vm_maker --list --vcpu$", aStdout=_vm_maker_list_vcpu, aPersist=True),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain.*", aStdout='16',aPersist=True), #16 is current VCPUS
                    exaMockCommand("/usr/sbin/vm_maker   --list   --vcpu   --domain.*", aStdout='16 16',aPersist=True),
                    exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/awk '{print $1}'", aStdout='scaqab10client01vm08.us.oracle.com'),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu", aStdout=_vm_maker_list_vcpu, aPersist=True),
                    exaMockCommand("/usr/bin/virsh vcpucount scaqab10client01vm08.us.oracle.com | /bin/grep maximum | /bin/grep config | /bin/awk '{print $3}'", aStdout='100'),
                    exaMockCommand("/usr/bin/virsh vcpucount.*", aStdout='100'),
                    exaMockCommand("/usr/sbin/vm_maker --set --vcpu .*"),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain scaqab10client01vm08.us.oracle.com | /bin/awk -F: '{print $4}'", aStdout='10'),
                    exaMockCommand("/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'", aStdout='scaqab10client01vm08.us.oracle.com')

                ],
                [
                    exaMockCommand("/usr/bin/virsh vcpucount .* | /bin/grep maximum | /bin/grep config | /bin/awk '{print $3}", aStdout='100'),
                    exaMockCommand("/usr/sbin/vm_maker --set --vcpu .*"),
                    exaMockCommand("/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'", aStdout='scaqab10client01vm08.us.oracle.com')
                ],
                [
                    exaMockCommand("/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'", aStdout='scaqab10client01vm08.us.oracle.com'),
                    exaMockCommand("/usr/bin/virsh dominfo scaqab10client01vm08.us.oracle.com | /bin/grep 'CPU(s)' | /bin/awk '{print $2}'", aStdout='10'),
                    exaMockCommand("/usr/bin/virsh vcpuinfo scaqab10client01vm08.us.oracle.com  --pretty | /bin/grep VCPU | /bin/awk '{print$2}'", aStdout='10'),
                    exaMockCommand("/usr/bin/virsh vcpupin --domain scaqab10client01vm08.us.oracle.com --vcpu 10 | /bin/tail -n+3 | /bin/awk '{print $2}'", aStdout='8-17'),
                    exaMockCommand("/usr/sbin/vm_maker --list | /bin/grep running | /bin/grep scaqab10client01vm08.us.oracle.com", aStdout="scaqab10client01vm08.us.oracle.com(24)       : running"),
                    exaMockCommand("/usr/bin/virsh vcpupin --domain scaqab10client01vm08.us.oracle.com --vcpu 10 4-13 --live --config"),
                    exaMockCommand("/usr/sbin/vm_maker --list | /bin/grep running | /bin/grep scaqab10client01vm08.us.oracle.com", aStdout="scaqab10client01vm08.us.oracle.com(24)       : running"),
                    exaMockCommand("/usr/bin/virsh vcpuinfo scaqab10client01vm08.us.oracle.com --pretty | /bin/grep Affinity | /bin/awk '{print$3}' | /bin/sort | /bin/uniq",aStdout='4-13'),
                ]
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True)
                ]
            ]


        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        _exacpueobj = exaBoxKvmCpuMgr(cluctrl)

        _options.vmcmd = 'resizecpus'
        _options.debug = '1'
        _options.vmid = 'scaqab10client01vm08.us.oracle.com'

        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEqual(_rc, 0)

    
    def test_cpu_cos(self):

        _vm_maker_list_vcpu = (
            "scaqab10client01vm08.us.oracle.com: Current: 16 Restart: 16\n"
            "               ----------\n"
            "Total VCPU required for reboot         : 16 (assumes restart situation)\n"
            "Host reserved PCPU                     : 4\n"
            "Available VCPU (now)                   : 184\n"
            "Available VCPU (delayed)               : 184\n"
            )
        _cmds = {
            self.mGetRegexVm(): [[
                    exaMockCommand("/opt/oracle.ExaWatcher/GetExaWatcherResults.sh --from.*"),
                    exaMockCommand("du -s.*", aStdout='1'),
                    exaMockCommand("ls .*/ExtractedResults", aStdout="file1"),
                    exaMockCommand("bin/rm -rf.*")
                ]],

            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/sbin/vm_maker --list | /bin/grep running | /bin/grep scaqab10client01vm08.us.oracle.com", aStdout="scaqab10client01vm08.us.oracle.com(24)       : running")
                ],
                [
                    exaMockCommand("/bin/test -e /opt/exacloud/vmconsole/history_console.py",aPersist=True),
                    exaMockCommand("/usr/bin/python3 /opt/exacloud/vmconsole/history_console.py --host scaqab10client01vm08.us.oracle.com --path /tmp/serial-exatest-scaqab10client01vm08.us.oracle.com.log.1",aPersist=True),
                    exaMockCommand("/bin/test -e /tmp/serial-exatest-scaqab10client01vm08.us.oracle.com.log.1",aPersist=True),
                    exaMockCommand("/bin/rm -f /tmp/serial-exatest-scaqab10client01vm08.us.oracle.com.log.1",aPersist=True),
                ],
                [
                    exaMockCommand(".*virsh nodeinfo.*", aStdout='100'),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu | /bin/grep 'Host reserved'.*", aStdout='4'),
                    #exaMockCommand("/usr/sbin/vm_maker --list --vcpu$", aStdout=_vm_maker_list_vcpu, aPersist=True),
                    #exaMockCommand("/usr/sbin/vm_maker --list | /bin/grep running | /bin/grep scaqab10client01vm08.us.oracle.com", aStdout="scaqab10client01vm08.us.oracle.com(24)       : running"),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain scaqab10client01vm08.us.oracle.com | /bin/awk -F: '{print $4}'", aStdout='10'),
                    exaMockCommand("/usr/sbin/vm_maker   --list   --vcpu   --domain.*", aStdout='Current: 16 Restart: 16',aPersist=True),
                    exaMockCommand("/usr/sbin/vm_maker --list-domains | /bin/awk '{print $1}'", aStdout='scaqab10client01vm08.us.oracle.com'),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu", aStdout=_vm_maker_list_vcpu, aPersist=True),
                    exaMockCommand("/usr/bin/virsh vcpucount scaqab10client01vm08.us.oracle.com | /bin/grep maximum | /bin/grep config | /bin/awk '{print $3}'", aStdout='100'),
                    exaMockCommand("/usr/bin/virsh vcpucount.*", aStdout='100'),
                    exaMockCommand("/usr/sbin/vm_maker --set --vcpu .*"),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain.*", aStdout='16',aPersist=True),
                    exaMockCommand("/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'", aStdout='scaqab10client01vm08.us.oracle.com')
                ],
                [
                    exaMockCommand("/usr/bin/virsh vcpucount .* | /bin/grep maximum | /bin/grep config | /bin/awk '{print $3}", aStdout='100'),
                    #exaMockCommand("/usr/sbin/vm_maker   --list   --vcpu   --domain.*", aStdout='16 16',aPersist=True),
                    exaMockCommand("/usr/sbin/vm_maker --set --vcpu .*",aPersist=True),
                    exaMockCommand("/usr/sbin/vm_maker   --list   --vcpu   --domain.*", aStdout='Current: 16 Restart: 16',aPersist=True),
                    exaMockCommand("/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'", aStdout='scaqab10client01vm08.us.oracle.com')
                    #exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain.*", aStdout='10'),
                    #exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain scaqab10client01vm08.us.oracle.com | /bin/awk -F: '{print $4}'", aStdout='10')
                ],
                [
                    exaMockCommand("/usr/bin/virsh list --all | /bin/tail -n+3 | /bin/awk '{print $2}'", aStdout='scaqab10client01vm08.us.oracle.com')
                ]
                ],


            self.mGetRegexLocal(): [
                [
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True)
                ]
            ]


        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 2
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        _exacpueobj = exaBoxKvmCpuMgr(cluctrl)
        _rc = _exacpueobj.mManageVMCpusCountKvm("resizecpus", "scaqab10client01vm08.us.oracle.com", aOptions=_options)
        self.assertEqual(_rc, 0)

    
    def test_cpu_info(self):

        _cmds = {
            self.mGetRegexDom0(): [[
                    exaMockCommand("/usr/sbin/vm_maker --list | /bin/grep running | /bin/grep scaqab10client01vm08.us.oracle.com", aStdout="scaqab10client01vm08.us.oracle.com(24)       : running"),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain.*", aStdout='10'),
                    exaMockCommand("/usr/bin/virsh vcpuinfo .*--pretty | /bin/grep Affinity.*", aStdout='12-16')
                ]],
            self.mGetRegexLocal(): [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True)
                ]]
        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        _exacpueobj = exaBoxKvmCpuMgr(cluctrl)
        return _exacpueobj.mClusterCPUInfoKvm(aOptions=_options)

    def test_cpu_patch(self):

        _cmds = {
            self.mGetRegexDom0(): [[
                    exaMockCommand("/usr/sbin/vm_maker --list | /bin/grep running.*", aStdout="1"),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain.*", aStdout='10'),
                    exaMockCommand("/usr/sbin/vm_maker --set --vcpu .*"),
                ]],
            self.mGetRegexLocal(): [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True)
                ]]
        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vm'] = {"cores": 8}
        cluctrl = self.mGetClubox()
        _exacpueobj = exaBoxKvmCpuMgr(cluctrl)
        return _exacpueobj.mPatchVMCfgVcpuCountKvm("scaqab10adm01.us.oracle.com", "scaqab10client01vm08.us.oracle.com", aOptions=_options)

    def test_cpu_burst(self):

        _cmds = {
            self.mGetRegexDom0(): [[
                    exaMockCommand(".*virsh nodeinfo.*", aStdout="CPU(s):100"),
                    exaMockCommand("/usr/sbin/vm_maker --list --vcpu | /bin/grep 'Host reserved'.*", aStdout='4'),
                    exaMockCommand("/usr/bin/virsh vcpucount scaqab10client01vm08.us.oracle.com | /bin/grep maximum | /bin/grep config | /bin/awk '{print $3}'", aStdout='100'),
                    exaMockCommand("/usr/sbin/vm_maker --list | /bin/grep running | /bin/grep scaqab10client01vm08.us.oracle.com", aStdout="scaqab10client01vm08.us.oracle.com(24)       : running"),
                    exaMockCommand("/usr/bin/virsh setvcpus .*"),
                ]],
            self.mGetRegexLocal(): [[
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True)
                ]]
        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vm'] = {"cores": 8}
        cluctrl = self.mGetClubox()
        _options.vmcmd = 'enablebursting'
        _options.debug = '1'
        _options.vmid = 'scaqab10client01vm08.us.oracle.com'

        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEqual(_rc, 0)

    
    @patch("exabox.utils.node.exaBoxNode.mDownloadRemoteFile")
    def test_fetchDiagLogs(self, mock_mDownloadRemoteFile):
        _cmds = {
            self.mGetRegexDom0(): [[
                    exaMockCommand(f"/opt/oracle.SupportTools/sundiag.sh", aStdout="Done. The report files are bzip2 compressed in /var/log/exadatatmp/sundiag_iad102036exdd001_2232XLR0HU_2023_10_16_14_13.tar.bz2"),
                    exaMockCommand("/usr/bin/rm -rf /var/log/exadatatmp/sundiag_iad102036exdd001_2232XLR0HU_2023_10_16_14_13.tar.bz2"),
                    exaMockCommand("/usr/bin/tar -czvf /tmp/varlog*"),
                    exaMockCommand("/usr/bin/rm -rf /tmp/varlog-*")
                ]]
        }

        self.mPrepareMockCommands(_cmds)

        cluctrl = self.mGetClubox()
        _exacpueobj = exaBoxKvmCpuMgr(cluctrl)
        _dom0s, _domUs, _cells, _ = cluctrl.mReturnAllClusterHosts()
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=_dom0s[0])
        _exacpueobj.fetchDiagLogs(_dom0s[0], _node)

    
    def test_mSetVCPUandValidate(self):
        _cmds = {
            self.mGetRegexDom0(): [            
                    [
                        exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain .*", aStdout="Current: 16 Restart: 16", aRc=0, aPersist=True),
                        exaMockCommand("timeout .* /usr/sbin/vm_maker --set --vcpu 16 --domain .* --force", aStdout="", aRc=0, aPersist=True),
                        exaMockCommand("/usr/sbin/vm_maker   --list   --vcpu   --domain .*", aStdout="Current: 16 Restart: 16", aRc=0, aPersist=True)
                    ]
            ]
        }
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _aDom = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        aNode = Mock()
        aNode.mExecuteCmd.side_effect = [
            (None, Mock(readlines=lambda: ['']), None),
            (None, Mock(readlines=lambda: ['Current: 16 Restart: 16']), None)
        ]
        aNode.mGetCmdExitStatus.side_effect = [0, 0]
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _exacpumgr = exaBoxKvmCpuMgr(_ebox)
        _result = {}
        _exacpumgr.mSetVCPUandValidate(_aDom, 16, _dom0, True, _result)
        self.assertTrue(_result[_aDom]['cpu_resize_success'])
        self.assertEqual(_result[_aDom]['currvcpus'], 16)
        self.assertEqual(_result[_aDom]['configvcpus'], 16)

    '''
    def test_mSetVCPUandValidate_failure(self):
        _cmds = {
            self.mGetRegexDom0(): [
                    [
                        exaMockCommand("/usr/sbin/vm_maker --list --vcpu --domain .*", aStdout="Current: 16 Restart: 16", aRc=0, aPersist=True)
                    ]
            ]
        }
        self.mPrepareMockCommands(_cmds)

        aNode = Mock()
        aNode.mExecuteCmd.return_value = (None, Mock(readlines=lambda: ['']), Mock(read=lambda: 'Error message'))
        aNode.mGetCmdExitStatus.return_value = 1
        _ebox = self.mGetClubox()
        _exacpumgr = exaBoxKvmCpuMgr(_ebox)
        _dom0 = self.mGetClubox().mReturnDom0DomUPair()[0][0]
        _aDom = self.mGetClubox().mReturnDom0DomUPair()[0][1]
        ret, currvcpus, configvcpus = _exacpumgr.mSetVCPUandValidate(_aDom, 16, _dom0, True, {})
        self.assertFalse(ret)
    ''' 

if __name__ == '__main__':
    unittest.main()

