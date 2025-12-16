import unittest

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.kvmcpumgr import exaBoxKvmCpuMgr
import os
import copy


cmdOutput1="""xen
00000000-0000-0000-0000-000000000000
"""

_total_cpu="""Name                                        ID   Mem VCPUs      State   Time(s)
Domain-0                                     0  9135     4     r----- 379576.0
slcs16adm03vm04-v303.us.oracle.com           1 30723    16     -b---- 514410.6
"""

_total_cpu_insuff="""VCPUs
400
1116
"""

_total_cpu_with_dom0="""VCPUs
4
16
"""

_total_cpus="""VCPUs
16
"""

_total_cpus_less="""VCPUs
100
"""

_vm_cfg_prev_list = """/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev1
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev2
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev3
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev4
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev5
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev6
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev7
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev8
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev9
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev10
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11
/EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"""

class TestCPUXen(ebTestClucontrol):

    def setUp(self):
        super(TestCPUXen, self).setUpClass(aGenerateDatabase=True)
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__timeout_vmcpu_resize = 2

     
    def test_cpu_info(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [   
                    exaMockCommand("xm vcpu-list | grep -v Domain-0| grep -v ^Name | awk '{print $1,$2,$7}' |sort |uniq", aStdout='slcs16adm03vm04-v303.us.oracle.com 1 4-19', aPersist=True),
                ],
            ]
        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        cluctrl.mHandlerClusterCPUInfo()

    def test_cpu_bursting(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                    exaMockCommand("xm li | grep Domain-0 | awk '{ print $4 }'", aStdout='4', aPersist=True),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*", aStdout="maxvcpus = 68", aPersist=True),
                    exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                    exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                    exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
                    exaMockCommand("/bin/scp .*", aPersist=True)

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],

            ]
        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        _rc = cluctrl.mManageVMCpusBursting("enablebursting", "scaqab10client01vm08.us.oracle.com", _options)
        self.assertEqual(_rc, 0)


    def test_cpu_cpucount_insufficient1(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="16"),
                    exaMockCommand("xm li slcs16adm03vm04-v303.us.oracle.com -l | grep '\(vcpu' | tr -d '\)' | awk '{ print $2 }'", aStdout="68"),
                    exaMockCommand("xm li | awk '{ print $4 }'", aStdout=_total_cpu_insuff),

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
                [
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.* | grep maxvcpus", aStdout="maxvcpus = 68")
                ]
            ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        _rc = cluctrl.mManageVMCpusCount("resizecpus", "scaqab10client01vm08.us.oracle.com", _options)
        self.assertNotEqual(_rc, 0)

    
    def test_cpu_cpucount_set_fail(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="16"),
                    exaMockCommand("xm li slcs16adm03vm04-v303.us.oracle.com -l | grep '\(vcpu' | tr -d '\)' | awk '{ print $2 }'", aStdout="68"),
                    exaMockCommand("xm li | awk '{ print $4 }'", aStdout=_total_cpu_with_dom0),
                    exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                    exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                    exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="16"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="16"),

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
                [
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.* | grep maxvcpus", aStdout="maxvcpus = 200"),
                    exaMockCommand("domu_maker vcpu-set scaqab10client01vm08.us.oracle.com.*")
                ],
                [
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=""),
                    exaMockCommand("xm li | grep Domain-0 | awk '{ print $4 }'",  aStdout="16", aPersist=True),
                    exaMockCommand("grep '\^cpus' /EXAVMIMAGES/GuestImages/.*", aRc=1),
                ],
            ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }

        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        get_gcontext().mSetConfigOption('timeout_vmcpu_resize', '2')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        cluctrl.__timeout_vmcpu_resize = 2

        _rc = cluctrl.mManageVMCpusCount("resizecpus", "scaqab10client01vm08.us.oracle.com", _options)
        self.assertNotEqual(_rc, 0)



    def test_cpu_cpucount_set_success(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="16"),
                    exaMockCommand("xm li slcs16adm03vm04-v303.us.oracle.com -l | grep '\(vcpu' | tr -d '\)' | awk '{ print $2 }'", aStdout="68"),
                    exaMockCommand("xm li | awk '{ print $4 }'", aStdout=_total_cpu_with_dom0),
                    exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                    exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                    exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="16 "),

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
                [
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.* | grep maxvcpus", aStdout="maxvcpus = 200"),
                    exaMockCommand("domu_maker vcpu-set scaqab10client01vm08.us.oracle.com.*")
                ],
                [
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout=""),
                    exaMockCommand("xm li | grep Domain-0 | awk '{ print $4 }'",  aStdout="16", aPersist=True),
                    exaMockCommand("grep '\^cpus' /EXAVMIMAGES/GuestImages/.*", aRc=1),
                ],
            ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }

        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        get_gcontext().mSetConfigOption('timeout_vmcpu_resize', '2')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        cluctrl.__timeout_vmcpu_resize = 2

        _rc = cluctrl.mManageVMCpusCount("resizecpus", "scaqab10client01vm08.us.oracle.com", _options)
        self.assertEqual(_rc, 0)

    

    def test_cpu_cpucount_nojson(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        cluctrl = self.mGetClubox()
        _rc = cluctrl.mManageVMCpusCount("resizecpus", "scaqab10client01vm08.us.oracle.com")
        self.assertNotEqual(_rc, 0)

    def test_cpu_cpucount_missinghostname(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hst": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hst": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        _rc = cluctrl.mManageVMCpusCount("resizecpus", "scaqab10client01vm08.us.oracle.com", _options)
        self.assertNotEqual(_rc, 0)

    def test_cpu_cpucount_missingvms(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        cluctrl = self.mGetClubox()
        _rc = cluctrl.mManageVMCpusCount("resizecpus", "scaqab10client01vm08.us.oracle.com", _options)
        self.assertNotEqual(_rc, 0)

    def test_cpu_cpucount_dom0_not_pingable(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
            ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping .*", aRc=1,  aPersist=True),
                ],
            ]
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        try:
            cluctrl.mManageVMCpusCount("resizecpus", "scaqab10client01vm08.us.oracle.com", _options)
        except Exception as e:
                _rc = "CPU resize failed as none of the Dom0s are pingable" in str(e)
                self.assertEqual(_rc, 1)

     
    def test_cpu_cpucount_cos(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="16", aPersist=False),
                    exaMockCommand("xm li slcs16adm03vm04-v303.us.oracle.com -l | grep '\(vcpu' | tr -d '\)' | awk '{ print $2 }'", aStdout="68"),
                    exaMockCommand("xm li | grep -v Domain-0 | awk '{ print $4 }'", aStdout=_total_cpus),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/.* awk -F.*", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("grep \^vcpus /EXAVMIMAGES/GuestImages.*", aStdout=" 16"),
                    exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                    exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                    exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand("domu_maker vcpu-set scaqab10client01vm08.us.oracle.com.*"),

                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="164", aPersist=False),

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
                [
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.* | grep maxvcpus", aStdout="maxvcpus = 200"),
                    exaMockCommand("domu_maker vcpu-set scaqab10client01vm08.us.oracle.com.*")
                ],
                [
                    exaMockCommand("grep '\^cpus' /EXAVMIMAGES/GuestImages/.*", aRc=1),
                ],
            ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }

        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 2
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        cluctrl._dom0U_list = copy.deepcopy(cluctrl.mReturnDom0DomUPair(aIsClusterLessXML=cluctrl.mIsClusterLessXML()))
        _rc = cluctrl.mManageVMCpusCount("resizecpus", "scaqab10client01vm08.us.oracle.com", _options)
        self.assertEqual(_rc, 0)
    

    def test_cpu_cpucount_cos_maxcpu_is_lower(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="16", aPersist=False),
                    exaMockCommand("xm li slcs16adm03vm04-v303.us.oracle.com -l | grep '\(vcpu' | tr -d '\)' | awk '{ print $2 }'", aStdout="68"),
                    exaMockCommand("xm li | grep -v Domain-0 | awk '{ print $4 }'", aStdout=_total_cpus),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/.* awk -F.*", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("grep \^vcpus /EXAVMIMAGES/GuestImages.*", aStdout=" 16"),
                    exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                    exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                    exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand("domu_maker vcpu-set scaqab10client01vm08.us.oracle.com.*"),

                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="164", aPersist=False),

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
                [
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.* | grep maxvcpus", aStdout="maxvcpus = 8 "),
                    exaMockCommand("domu_maker vcpu-set scaqab10client01vm08.us.oracle.com.*")
                ],
                [
                    exaMockCommand("grep '\^cpus' /EXAVMIMAGES/GuestImages/.*", aRc=1),
                ],
            ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }

        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 2
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        cluctrl._dom0U_list = copy.deepcopy(cluctrl.mReturnDom0DomUPair(aIsClusterLessXML=cluctrl.mIsClusterLessXML()))
        _rc = cluctrl.mManageVMCpusCount("resizecpus", "scaqab10client01vm08.us.oracle.com", _options)
        self.assertNotEqual(_rc, 0)

    def test_cpu_cpucount_cos_over_subscribed(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com | grep scaqab10client01vm08.us.oracle.com | awk '{ print $4 }'", aStdout="16", aPersist=False),
                    exaMockCommand("xm li slcs16adm03vm04-v303.us.oracle.com -l | grep '\(vcpu' | tr -d '\)' | awk '{ print $2 }'", aStdout="68"),
                    exaMockCommand("xm li | grep -v Domain-0 | awk '{ print $4 }'", aStdout=_total_cpus_less),
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
                [
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.* | grep maxvcpus", aStdout="maxvcpus = 200"),
                    exaMockCommand("domu_maker vcpu-set scaqab10client01vm08.us.oracle.com.*")
                ],
                [
                    exaMockCommand("grep '\^cpus' /EXAVMIMAGES/GuestImages/.*", aRc=1),
                ],
            ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }

        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 2
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        cluctrl._dom0U_list = copy.deepcopy(cluctrl.mReturnDom0DomUPair(aIsClusterLessXML=cluctrl.mIsClusterLessXML()))
        _rc = cluctrl.mManageVMCpusCount("resizecpus", "scaqab10client01vm08.us.oracle.com", _options)
        self.assertNotEqual(_rc, 0)



    def test_cpu_mModifyService(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/.*", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm li | grep Domain-0 | awk '{ print $4 }'", aStdout="4"),
                    exaMockCommand("grep \^vcpus /EXAVMIMAGES/GuestImages.*", aStdout=" 16"),
                    exaMockCommand("grep \^cpus /EXAVMIMAGES/GuestImages/.* |  awk -F '=' '{print $2}'", aStdout=" '4-19'"),
                    exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                    exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                    exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm vcpu-pin.*"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm vcpu-list.*", aStdout="4-19"),
                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
            ],
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        cluctrl._dom0U_list = copy.deepcopy(cluctrl.mReturnDom0DomUPair(aIsClusterLessXML=cluctrl.mIsClusterLessXML()))
        _rc = cluctrl.mModifyService(aOptions=_options, aDomU="scaqab10client01vm08.us.oracle.com", aForcePinning=True)
        self.assertEqual(_rc, 0)

    

    def test_cpu_mModifyService_pinning_failure(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/.*", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm li | grep Domain-0 | awk '{ print $4 }'", aStdout="4"),
                    exaMockCommand("grep \^vcpus /EXAVMIMAGES/GuestImages.*", aStdout=" 16"),
                    exaMockCommand("grep \^cpus /EXAVMIMAGES/GuestImages/.* |  awk -F '=' '{print $2}'", aStdout=" '4-17'"),
                    exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                    exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                    exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm vcpu-pin.*"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm vcpu-list.*", aStdout="4-14"),
                    exaMockCommand("xm vcpu-list.*", aStdout="4-14"),

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
            ],
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        get_gcontext().mSetConfigOption('timeout_vcpu_pin', '5')

        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 1
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        cluctrl = self.mGetClubox()
        cluctrl._dom0U_list = copy.deepcopy(cluctrl.mReturnDom0DomUPair(aIsClusterLessXML=cluctrl.mIsClusterLessXML()))
        try:
            _rc = cluctrl.mModifyService(aOptions=_options, aDomU="scaqab10client01vm08.us.oracle.com", aForcePinning=True)
        except Exception as e:
                _rc = "The pinning range is incorrect" in str(e)
                self.assertEqual(_rc, 1)
    

    def test_cpu_mModifyService_cos_pinning_failure(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/.*", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm li | grep Domain-0 | awk '{ print $4 }'", aStdout="4"),
                    exaMockCommand("grep \^vcpus /EXAVMIMAGES/GuestImages.*", aStdout=" 16"),
                    exaMockCommand("grep \^cpus /EXAVMIMAGES/GuestImages/.* |  awk -F '=' '{print $2}'", aStdout=" '4-19'"),
                    exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                    exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                    exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm vcpu-pin.*"),
                    exaMockCommand("xm vcpu-list.*", aStdout="4-19"),
                    exaMockCommand("xm vcpu-list.*", aStdout="4-19"),

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
            ],
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 2
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        get_gcontext().mSetConfigOption('timeout_vcpu_pin', '5')
        cluctrl = self.mGetClubox()
        cluctrl._dom0U_list = copy.deepcopy(cluctrl.mReturnDom0DomUPair(aIsClusterLessXML=cluctrl.mIsClusterLessXML()))
        try:
            cluctrl.mModifyService(aOptions=_options, aDomU="scaqab10client01vm08.us.oracle.com", aForcePinning=True)
        except Exception as e:
                _rc = "The pinning range is not same across clusters or incorrect range" in str(e)
                self.assertEqual(_rc, 1)

    
    def test_cpu_mModifyService_cos_pinning_success(self):

        _vmcfg = self.mGetResourcesTextFile("cmd_vmcfg.txt")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/.*", aStdout="scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm li | grep Domain-0 | awk '{ print $4 }'", aStdout="4"),
                    exaMockCommand("grep \^vcpus /EXAVMIMAGES/GuestImages.*", aStdout=" 16"),
                    exaMockCommand("grep \^cpus /EXAVMIMAGES/GuestImages/.* |  awk -F '=' '{print $2}'", aStdout=" '4-19'"),
                    exaMockCommand("cp /EXAVMIMAGES/GuestImages/.*/vm.cfg /EXAVMIMAGES/GuestImages/.*/vm.cfg.*"),
                    exaMockCommand("/bin/test -e .*", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/find /EXAVMIMAGES/GuestImages/.*/ -name 'vm.cfg.prev*' | /bin/xargs /bin/ls -t",aStdout=_vm_cfg_prev_list),
                    exaMockCommand("/bin/test -e /bin/rm", aRc=0,  aPersist=True),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev11"),
                    exaMockCommand("/bin/rm -f /EXAVMIMAGES/GuestImages/slcqab02adm03vm01.us.oracle.com/vm.cfg.prev12"),
                    exaMockCommand("/bin/scp .*"),
                    exaMockCommand("xm li scaqab10client01vm08.us.oracle.com"),
                    exaMockCommand("xm vcpu-pin.*"),
                    exaMockCommand("xm vcpu-list.*", aStdout="4-43"),

                ],
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout="scaqab10client01vm08.us.oracle.com              1513 65539     8     r-----  25154.2", aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout="scaqab10client01vm08.us.oracle.com scaqab10client02vm08.us.oracle.com"),
                    exaMockCommand("cat /EXAVMIMAGES/GuestImages/.*/vm.cfg", aStdout=_vmcfg),
                    exaMockCommand("xm info | grep nr_cpus", aStdout="nr_cpus                : 72"),
                ],
            ],
        }
        self.mPrepareMockCommands(_cmds)

        get_gcontext().mSetConfigOption('force_pinning_on_resize', 'False')
        _options = self.mGetPayload()
        _options.jsonconf['subfactor'] = 2
        _options.jsonconf['poolsize'] = 40
        _options.jsonconf['vms'] = [{"hostname": "scaqab10client01vm08.us.oracle.com", "cores": "8"}, {"hostname": "scaqab10client02vm08.us.oracle.com", "cores": "8"}]
        get_gcontext().mSetConfigOption('timeout_vcpu_pin', '5')
        cluctrl = self.mGetClubox()
        cluctrl._dom0U_list = copy.deepcopy(cluctrl.mReturnDom0DomUPair(aIsClusterLessXML=cluctrl.mIsClusterLessXML()))
        _rc = cluctrl.mModifyService(aOptions=_options, aDomU="scaqab10client01vm08.us.oracle.com", aForcePinning=True)
        self.assertEqual(_rc, 0)
    
    
if __name__ == '__main__':
    unittest.main()

