import unittest
from unittest import mock
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Error import ExacloudRuntimeError, ebError
import os
import re

cmdOutput1="""xen
00000000-0000-0000-0000-000000000000
"""
cmdOutput2="""xen"""

class TestKeys(ebTestClucontrol):

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        self.mGetClubox()._exaBoxCluCtrl__tools_key_public = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        self.mGetClubox().mRegisterVgComponents()

    
    def test_keys_addkey_missing_key_param(self):
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        self.mGetClubox()._exaBoxCluCtrl__tools_key_public = None

        _vmcmd = 'addkey'
        _vmid  = '_all_'
        _options.jsonconf['vms'] = ['_all_']
        _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        self.assertNotEqual(_rc, 0)
        self.mGetClubox()._exaBoxCluCtrl__tools_key_public = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

    def test_keys_addkey_invalid_key_param(self):
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _vmcmd = 'addkey'
        _vmid  = '_all_'
        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'wrongkeyformat'
        try:
            _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        except Exception as e:
            _rc = "SSH Key not provided or incorrect" in str(e)
            self.assertEqual(_rc, 1)

    def test_keys_addkey_key_dir_missing(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -f /home/opc/.ssh/authorized_keys", aRc=1),
                    exaMockCommand("test -d /home/opc/.ssh", aRc=1),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _vmcmd = 'addkey'
        _vmid  = '_all_'
        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        try:
            _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        except Exception as e:
            _rc = "Exception on mManageVMSSHKeys, too many failures" in str(e)
            self.assertEqual(_rc, 1)
    

    def test_keys_addkey_key_exists_already(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -f /home/opc/.ssh/authorized_keys", aRc=1),
                    exaMockCommand("test -d /home/opc/.ssh", aRc=0),
                    exaMockCommand("touch /home/opc/.ssh/authorized_keys ; chmod 600 /home/opc/.ssh/authorized_keys ; chown opc:.*"),
                    exaMockCommand("grep -F.*/authorized_keys 2> /dev/null.*", aRc=0),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _vmcmd = 'addkey'
        _vmid  = '_all_'
        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        self.assertEqual(_rc, 0)

    def test_keys_addkey_success(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -f /home/opc/.ssh/authorized_keys", aRc=1),
                    exaMockCommand("test -d /home/opc/.ssh", aRc=0),
                    exaMockCommand("touch /home/opc/.ssh/authorized_keys ; chmod 600 /home/opc/.ssh/authorized_keys ; chown opc:.*"),
                    exaMockCommand("grep -F.*/authorized_keys 2> /dev/null.*", aRc=1),
                    exaMockCommand("sh -c 'echo.* >> /home/opc/.ssh/authorized_keys 2> /dev/null'")
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _vmcmd = 'addkey'
        _vmid  = '_all_'
        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        self.assertEqual(_rc, 0)

    def test_keys_deletekey_keydir_not_found(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -f /home/opc/.ssh/authorized_keys", aRc=1),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _vmcmd = 'deletekey'
        _vmid  = '_all_'
        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        try:
            _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        except Exception as e:
            _rc = "Exception on mManageVMSSHKeys, too many failures" in str(e)
            self.assertEqual(_rc, 1)

    def test_keys_deletekey_key_not_present(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -f /home/opc/.ssh/authorized_keys", aRc=0),
                    exaMockCommand("grep -F.*/authorized_keys 2> /dev/null.*", aRc=1),

                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _vmcmd = 'deletekey'
        _vmid  = '_all_'
        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        self.assertEqual(_rc, 0)

    def test_keys_deletekey_success(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -f /home/opc/.ssh/authorized_keys", aRc=0),
                    exaMockCommand("grep -F.*/authorized_keys 2> /dev/null.*", aRc=0),
                    exaMockCommand("sed.*-i /home/opc/.ssh/authorized_keys 2> /dev/null"),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _vmcmd = 'deletekey'
        _vmid  = '_all_'
        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        self.assertEqual(_rc, 0)
    

    def test_keys_listkey_success(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /home/opc/.ssh/authorized_keys", aRc=0),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        _options.vmid = '_all_'
        _options.vmcmd = 'listkey'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEqual(_rc, 0)
    
    def test_keys_listkey_sshkey_already_in_memory(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /home/opc/.ssh/authorized_keys", aRc=0),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        cluctrl = self.mGetClubox()
        _vmcmd = 'listKey'
        _vmid  = '_all_'

        _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=None, aKey=None, aMode=False)
        self.assertEqual(_rc, 0)
        
        
    def test_keys_listkey_not_64base(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /home/opc/.ssh/authorized_keys", aRc=0),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        cluctrl = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf['vm'] = {"sshkey": "#c3NoLXJzYSBBQUFBQjNOemFDMXljMkVBQUFBREFRQUJBQUFCQVFEVmVZVkJjNzlKVHdNdlNSbm9MOFIzS25pZEdTNGwwN2ZuOTBtMSt0ZjFabzJtNWtPMFFNNDR6SmhQYnlIR1JhUXVoT25oUm42SUdaR1RGOTNlbVRjM2QvMzlVelpBa1I2MWc2SjFIaEhZTG5yV1VIYk5FTmJZWUtDZ2VZcjZhSTFpRmhCT0RMemR4SldBc2MxdmxScXFLVzYzWDMwRDc2SnBqTU95ZHN3WjdJR1pwVEpvTHVFdUJqRHozMXpobjJvU1FxdFRQeXM0Sk9IOVU5UnJ2REIwZTQrVVpJSE51RlhaUWEvL3hiNnZvN1RRN04vYTdSZ2djZUZUNk03SHpTUGl0STgyZU1WeWN1Q2VqNUtZRkx0NkZybmx3bHM3ZEZBZnJobjRNZEFuMXl2RkN3aGd6TUpoUXdRUURKc20zbG9KT1pmQW9pajBROFdYSWVGdTJTUHogZXhha21z"}
        _vmid = '_all_'
        _vmcmd = 'listkey'
        cluctrl.mSetOptions(_options)
        with self.assertRaises(ExacloudRuntimeError):
            cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
            
    def test_keys_listkey_64base(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /home/opc/.ssh/authorized_keys", aRc=0),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        cluctrl = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf['vm'] = {"sshkey": "c3NoLXJzYSBBQUFBQjNOemFDMXljMkVBQUFBREFRQUJBQUFCQVFEVmVZVkJjNzlKVHdNdlNSbm9MOFIzS25pZEdTNGwwN2ZuOTBtMSt0ZjFabzJtNWtPMFFNNDR6SmhQYnlIR1JhUXVoT25oUm42SUdaR1RGOTNlbVRjM2QvMzlVelpBa1I2MWc2SjFIaEhZTG5yV1VIYk5FTmJZWUtDZ2VZcjZhSTFpRmhCT0RMemR4SldBc2MxdmxScXFLVzYzWDMwRDc2SnBqTU95ZHN3WjdJR1pwVEpvTHVFdUJqRHozMXpobjJvU1FxdFRQeXM0Sk9IOVU5UnJ2REIwZTQrVVpJSE51RlhaUWEvL3hiNnZvN1RRN04vYTdSZ2djZUZUNk03SHpTUGl0STgyZU1WeWN1Q2VqNUtZRkx0NkZybmx3bHM3ZEZBZnJobjRNZEFuMXl2RkN3aGd6TUpoUXdRUURKc20zbG9KT1pmQW9pajBROFdYSWVGdTJTUHogZXhha21z"}
        _vmid = '_all_'
        _vmcmd = 'listkey'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        self.assertEqual(_rc, 0)
        
    def test_cleanup_keys(self):
        cluctrl = self.mGetClubox()
        _options = None
        _rc = cluctrl.mCleanupKeys(_options)
        self.assertEqual(_rc, None)
    
    def test_get_user_key_not_64base(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /home/opc/.ssh/authorized_keys", aRc=0),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        cluctrl = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf['vm'] = {"sshkey": "#c3NoLXJzYSBBQUFBQjNOemFDMXljMkVBQUFBREFRQUJBQUFCQVFEVmVZVkJjNzlKVHdNdlNSbm9MOFIzS25pZEdTNGwwN2ZuOTBtMSt0ZjFabzJtNWtPMFFNNDR6SmhQYnlIR1JhUXVoT25oUm42SUdaR1RGOTNlbVRjM2QvMzlVelpBa1I2MWc2SjFIaEhZTG5yV1VIYk5FTmJZWUtDZ2VZcjZhSTFpRmhCT0RMemR4SldBc2MxdmxScXFLVzYzWDMwRDc2SnBqTU95ZHN3WjdJR1pwVEpvTHVFdUJqRHozMXpobjJvU1FxdFRQeXM0Sk9IOVU5UnJ2REIwZTQrVVpJSE51RlhaUWEvL3hiNnZvN1RRN04vYTdSZ2djZUZUNk03SHpTUGl0STgyZU1WeWN1Q2VqNUtZRkx0NkZybmx3bHM3ZEZBZnJobjRNZEFuMXl2RkN3aGd6TUpoUXdRUURKc20zbG9KT1pmQW9pajBROFdYSWVGdTJTUHogZXhha21z"}
        cluctrl.mSetOptions(_options)
        with self.assertRaises(ExacloudRuntimeError):
            cluctrl.mGetUserkey(aOptions=_options)
        
        
    

    def test_keys_listkey_success_without_vmid(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /home/opc/.ssh/authorized_keys", aRc=0),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        #_options.vmid = '_all_'
        _options.vmcmd = 'listkey'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEqual(_rc, 0)

    def test_keys_listkey_fail_without_vmcd(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("cat /home/opc/.ssh/authorized_keys", aRc=0),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertNotEqual(_rc, 0)
    
    
    def test_keys_resetkey_uid_not_accesible(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("grep opc //etc/passwd | tr ':' ' ' | awk '{ print $3" "$4 }'", aStdout="no no"),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _vmcmd = 'resetkey'
        _vmid  = '_all_'
        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        try:
            _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        except Exception as e:
            _rc = "Exception on mManageVMSSHKeys, too many failures" in str(e)
            self.assertEqual(_rc, 1)

    def test_keys_resetkey_success(self):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("grep opc //etc/passwd | tr ':' ' ' | awk '{ print $3" "$4 }'", aStdout="100 200"),
                    exaMockCommand("mkdir -p /home/opc/.ssh ; cp -r /home/opc/.ssh /home/opc/.ssh.orig ; rm /home/opc/.ssh/authorized_keys ; chmod 600 /home/opc/.ssh/authorized_keys"),
                    exaMockCommand("sh -c '.*>> /home/opc/.ssh/authorized_keys 2> /dev/null ; chown -R 100:20 /home/opc/.ssh ; chmod 600 /home/opc/.ssh/authorized_keys'"),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _vmcmd = 'resetkey'
        _vmid  = '_all_'
        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        try:
            _rc = cluctrl.mManageVMSSHKeys(_vmcmd, _vmid, aOptions=_options, aMode=False)
        except Exception as e:
            _rc = "Exception on mManageVMSSHKeys, too many failures" in str(e)
            self.assertEqual(_rc, 1)
   

    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mRestartVM")
    @mock.patch("exabox.ovm.vmcontrol.ebVgLifeCycle.mDispatchEvent", return_value=0)
    def test_keysi_resetkey_mode_true(self, mock_restartvm, mock_dispathevent):
        xm_list_out_empty = [
            "Name                                        ID   Mem VCPUs      State   Time(s)",
            "Domain-0                                     0  8785     4     r----- 4737270.8"
        ]
        xm_list_out = list(xm_list_out_empty)
        for _, _domu in self.mGetClubox().mReturnDom0DomUPair():
            xm_list_out.append(_domu + " 1 92163    10     -b---- 427769.7")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout='\n'.join(_domu for _, _domu in self.mGetClubox().mReturnDom0DomUPair()), aRc=0, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("/bin/test -e /etc/xen/auto/", aRc=0, aPersist=True),
                    exaMockCommand("/bin/unlink /etc/xen/auto/", aRc=0, aPersist=True),
                    exaMockCommand("xm shutdown", aRc=0, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out_empty), aRc=0),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out_empty), aRc=0),


                ],
                [
                    exaMockCommand("xm list", aRc=0, aPersist=True),
                    exaMockCommand("/sbin/e2fsck -fy /EXAVMIMAGES/GuestImages/", aStdout=" ", aRc=0, aPersist=True),
                    exaMockCommand("mkdir -p /opt/exacloud/bin", aRc=0, aPersist=True),
                    exaMockCommand("/bin/scp scripts/images/vmimg.sh.*"),
                    exaMockCommand("chmod.*/opt/exacloud/bin/vmimg.sh.*"),
                    exaMockCommand("/opt/exacloud/bin/vmimg.sh mount.*"),
                    exaMockCommand("grep opc.*/etc/passwd | tr ':' ' ' | awk '{ print $3" "$4 }'", aStdout="100 200"),
                    exaMockCommand("mkdir -p .*/home/opc/.ssh ; cp -r .*/home/opc/.ssh .*/home/opc/.ssh.orig ; rm .*/home/opc/.ssh/authorized_keys ; chmod 600 .*/home/opc/.ssh/authorized_keys"),
                    exaMockCommand("sh -c '.*>> .*/home/opc/.ssh/authorized_keys 2> /dev/null ; chown -R 100:20 .*/home/opc/.ssh ; chmod 600 .*/home/opc/.ssh/authorized_keys'"),
                    exaMockCommand("/opt/exacloud/bin/vmimg.sh umount.*"),

                ],

                ],

            self.mGetRegexVm(): [
                [
                    exaMockCommand("test -f /home/opc/.ssh/authorized_keys", aRc=1),
                    exaMockCommand("test -d /home/opc/.ssh", aRc=0),
                    exaMockCommand("touch /home/opc/.ssh/authorized_keys ; chmod 600 /home/opc/.ssh/authorized_keys ; chown opc:.*"),
                    exaMockCommand("grep -F.*/authorized_keys 2> /dev/null.*", aRc=1),
                    exaMockCommand("sh -c 'echo.* >> /home/opc/.ssh/authorized_keys 2> /dev/null'")
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)
        mock_restartvm.side_effect = None
        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _options.jsonconf['vms'] = ['_all_']
        _options.jsonconf['sshkey'] = 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC7teF4ZnixfJic/jQgL9IWBYXHW+9m7FgpN15z2JntjZm7uU5DEPJ0CTI/jlRST2lpxizqr9oNLpqDmxnCoDTGLsCiYTYGS5SsD+A8fHYOXVQM91JM16lOwXo2SZ3eRrdg9/l3/x2o9jzjT7rD95VO2Th+bPn1r7i3FtwqjdLozChcuJhyOV/jfBJ2lKPC7r98nZh/mM0BS0mQ7M5r4GFC9EmkjqeRP9hTYksNzE3OI00xAer4tUSPYV893dM3LVDYrhHFtV/8quE7Ydq3JqdPeCM+BpCmkeqZpbDfx81EgwS109uWTM7nc15dPSr9RjO4mf4GSiQooylN0NCS7ntR naps@den00udi'

        _options.vmcmd = 'resetkey'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEqual(_rc, 0)
    
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mValidateKeys", return_value=1)
    def test_create_oeda_ssh_keys_no_rotate(self,mock_validatekeys):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e .ssh/authorized_keys || mkdir -p .ssh && touch .ssh/authorized_keys && chmod 700 .ssh && chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("sh -c.*EXACLOUD KEY.*-scwq.*"),
                    exaMockCommand("/bin/test -e .ssh/authorized_keys", aRc=1),
                    exaMockCommand("/bin/mkdir -p .ssh", aRc=1),
                    exaMockCommand("/bin/touch .ssh/authorized_keys"),
                    exaMockCommand("/bin/chmod 700 .ssh"),
                    exaMockCommand("/bin/chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("/bin/grep.*.ssh/authorized_keys.*", aRc=1),
                    exaMockCommand("/bin/echo.* >> .ssh/authorized_keys"),
                    exaMockCommand("grep.*EXACLOUD KEY.*.ssh/authorized_keys.*"),
                ]
                ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("test -e .ssh/authorized_keys || mkdir -p .ssh && touch .ssh/authorized_keys && chmod 700 .ssh && chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("sh -c.*EXACLOUD KEY.*-scwq.*"),
                    exaMockCommand("/bin/test -e .ssh/authorized_keys", aRc=1),
                    exaMockCommand("/bin/mkdir -p .ssh", aRc=1),
                    exaMockCommand("/bin/touch .ssh/authorized_keys"),
                    exaMockCommand("/bin/chmod 700 .ssh"),
                    exaMockCommand("/bin/chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("/bin/grep.*.ssh/authorized_keys.*", aRc=1),
                    exaMockCommand("/bin/echo.* >> .ssh/authorized_keys"),
                    exaMockCommand("grep.*EXACLOUD KEY.*.ssh/authorized_keys.*"),
                ]
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand('/bin/ping -c 1 *', aRc=0, aPersist=True)
                ]
            ]
            
        }   
        self.mPrepareMockCommands(_cmds)
        mock_validatekeys.side_effect = None
        cluctrl = self.mGetClubox()
        cluctrl.mCreateOEDASSHKeys()
        
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost", return_value=True)
    def test_update_all_cluster_hosts_keys_with_key_rotation_nodes(self, mock_pinghost):
        # Set up KEY_ROTATION_NODES
        _options = self.mGetPayload()
        _options.jsonconf = {'KEY_ROTATION_NODES': ['scaqab10adm01.us.oracle.com']}
        cluctrl = self.mGetClubox()
        cluctrl.mSetOptions(_options)
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e .ssh/authorized_keys || mkdir -p .ssh && touch .ssh/authorized_keys && chmod 700 .ssh && chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("sh -c.*EXACLOUD KEY.*-scwq.*"),
                    exaMockCommand("/bin/test -e .ssh/authorized_keys", aRc=1),
                    exaMockCommand("/bin/mkdir -p .ssh", aRc=1),
                    exaMockCommand("/bin/touch .ssh/authorized_keys"),
                    exaMockCommand("/bin/chmod 700 .ssh"),
                    exaMockCommand("/bin/chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("/bin/grep.*.ssh/authorized_keys.*", aRc=1),
                    exaMockCommand("/bin/echo.* >> .ssh/authorized_keys"),
                    exaMockCommand("grep.*EXACLOUD KEY.*.ssh/authorized_keys.*"),
                ]
            ],
            self.mGetRegexCell(): [],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand('/bin/ping -c 1 *', aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        cluctrl.mUpdateAllClusterHostsKeys(aCreateNew=True)
        
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost", return_value=True)
    def test_update_all_cluster_hosts_keys_with_ingestion_hw_failure(self, mock_pinghost):
        # Set up INGESTION_HW_FAILURE
        _options = self.mGetPayload()
        _options.jsonconf = {'INGESTION_HW_FAILURE': ['scaqab10adm01.us.oracle.com']}
        cluctrl = self.mGetClubox()
        cluctrl.mSetOptions(_options)
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e .ssh/authorized_keys || mkdir -p .ssh && touch .ssh/authorized_keys && chmod 700 .ssh && chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("sh -c.*EXACLOUD KEY.*-scwq.*"),
                    exaMockCommand("/bin/test -e .ssh/authorized_keys", aRc=1),
                    exaMockCommand("/bin/mkdir -p .ssh", aRc=1),
                    exaMockCommand("/bin/touch .ssh/authorized_keys"),
                    exaMockCommand("/bin/chmod 700 .ssh"),
                    exaMockCommand("/bin/chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("/bin/grep.*.ssh/authorized_keys.*", aRc=1),
                    exaMockCommand("/bin/echo.* >> .ssh/authorized_keys"),
                    exaMockCommand("grep.*EXACLOUD KEY.*.ssh/authorized_keys.*"),
                ]
            ],
            self.mGetRegexCell(): [],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand('/bin/ping -c 1 *', aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mPingHost", return_value=True)
    def test_update_all_cluster_hosts_keys_with_both_configurations(self, mock_pinghost):
        # Set up both KEY_ROTATION_NODES and INGESTION_HW_FAILURE
        _options = self.mGetPayload()
        _options.jsonconf = {'KEY_ROTATION_NODES': ['scaqab10adm01.us.oracle.com', 'scaqab10adm02.us.oracle.com', 'scaqab10adm01nat08.us.oracle.com'], 'INGESTION_HW_FAILURE': ['scaqab10adm01nat08.us.oracle.com']}
        cluctrl = self.mGetClubox()
        cluctrl.mSetOptions(_options)
        
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e .ssh/authorized_keys || mkdir -p .ssh && touch .ssh/authorized_keys && chmod 700 .ssh && chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("sh -c.*EXACLOUD KEY.*-scwq.*"),
                    exaMockCommand("/bin/test -e .ssh/authorized_keys", aRc=1),
                    exaMockCommand("/bin/mkdir -p .ssh", aRc=1),
                    exaMockCommand("/bin/touch .ssh/authorized_keys"),
                    exaMockCommand("/bin/chmod 700 .ssh"),
                    exaMockCommand("/bin/chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("/bin/grep.*.ssh/authorized_keys.*", aRc=1),
                    exaMockCommand("/bin/echo.* >> .ssh/authorized_keys"),
                    exaMockCommand("grep.*EXACLOUD KEY.*.ssh/authorized_keys.*"),
                ]
            ],
            self.mGetRegexCell(): [],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand('/bin/ping -c 1 *', aRc=0, aPersist=True)
                ]
            ]
        }
        self.mPrepareMockCommands(_cmds)
        cluctrl = self.mGetClubox()
        cluctrl.mUpdateAllClusterHostsKeys(aCreateNew=True)
         
    @mock.patch("exabox.ovm.clucontrol.exaBoxCluCtrl.mValidateKeys", return_value=0)
    def test_rotate_keys(self, mock_validatekeys):
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("test -e .ssh/authorized_keys || mkdir -p .ssh && touch .ssh/authorized_keys && chmod 700 .ssh && chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("sh -c.*EXACLOUD KEY.*-scwq.*"),
                    exaMockCommand("/bin/test -e .ssh/authorized_keys", aRc=1),
                    exaMockCommand("/bin/mkdir -p .ssh", aRc=1),
                    exaMockCommand("/bin/touch .ssh/authorized_keys"),
                    exaMockCommand("/bin/chmod 700 .ssh"),
                    exaMockCommand("/bin/chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("/bin/grep.*.ssh/authorized_keys.*", aRc=1),
                    exaMockCommand("/bin/echo.* >> .ssh/authorized_keys"),
                    exaMockCommand("grep.*EXACLOUD KEY.*.ssh/authorized_keys.*"),
                ]
                ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("test -e .ssh/authorized_keys || mkdir -p .ssh && touch .ssh/authorized_keys && chmod 700 .ssh && chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("sh -c.*EXACLOUD KEY.*-scwq.*"),
                    exaMockCommand("/bin/test -e .ssh/authorized_keys", aRc=1),
                    exaMockCommand("/bin/mkdir -p .ssh", aRc=1),
                    exaMockCommand("/bin/touch .ssh/authorized_keys"),
                    exaMockCommand("/bin/chmod 700 .ssh"),
                    exaMockCommand("/bin/chmod 600 .ssh/authorized_keys"),
                    exaMockCommand("/bin/grep.*.ssh/authorized_keys.*", aRc=1),
                    exaMockCommand("/bin/echo.* >> .ssh/authorized_keys"),
                    exaMockCommand("grep.*EXACLOUD KEY.*.ssh/authorized_keys.*"),
                ]
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand('/bin/ping -c 1 *', aRc=0, aPersist=True)
                ]
            ],

        }
        self.mPrepareMockCommands(_cmds)
        mock_validatekeys.side_effect = None

        cluctrl = self.mGetClubox()
        _rc = cluctrl.mHandlerRotateKeys()
        self.assertEqual(_rc, 0)


    def test_keys_sshkey_wrong_vmid(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("mkdir -p ~/.ssh ; ls ~/.ssh", aRc=0),
                    exaMockCommand("echo .*ssh/authorized_keys")
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'abc.com'
        _options.vmcmd = 'sshkey'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertNotEqual(_rc, 0)

    def test_keys_sshkey(self):
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("mkdir -p ~/.ssh ; ls ~/.ssh", aRc=0),
                    exaMockCommand("echo .*ssh/authorized_keys")
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = '_all_'
        _options.vmcmd = 'sshkey'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertEqual(_rc, 0)


    def test_keys_ping_fail(self):

        xm_list_out_empty = [
            "Name                                        ID   Mem VCPUs      State   Time(s)",
            "Domain-0                                     0  8785     4     r----- 4737270.8"
        ]

        xm_list_out = list(xm_list_out_empty)
        for _, _domu in self.mGetClubox().mReturnDom0DomUPair():
            xm_list_out.append(_domu + " 1 92163    10     -b---- 427769.7")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("/bin/test -e /bin/virsh", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout='\n'.join(_domu for _, _domu in self.mGetClubox().mReturnDom0DomUPair()), aRc=0, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("/bin/test -e /etc/xen/auto/", aRc=0, aPersist=True),
                    exaMockCommand("/bin/unlink /etc/xen/auto/", aRc=0, aPersist=True),
                ]
                ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand(re.escape('/bin/ping -c 1 *'), aRc=1, aPersist=True)
                ]
                ],

        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()

        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = 'unknownvm.oracle.com'
        _options.vmcmd = 'ping'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()
        self.assertNotEqual(_rc, 0)

    def test_mValidatesshkey_goodkey(self):
        cluctrl = self.mGetClubox()
        _options = self.mGetPayload()
        _options.jsonconf['vm'] = {"sshkey": "c3NoLXJzYSBBQUFBQjNOemFDMXljMkVBQUFBREFRQUJBQUFCQVFEVmVZVkJjNzlKVHdNdlNSbm9MOFIzS25pZEdTNGwwN2ZuOTBtMSt0ZjFabzJtNWtPMFFNNDR6SmhQYnlIR1JhUXVoT25oUm42SUdaR1RGOTNlbVRjM2QvMzlVelpBa1I2MWc2SjFIaEhZTG5yV1VIYk5FTmJZWUtDZ2VZcjZhSTFpRmhCT0RMemR4SldBc2MxdmxScXFLVzYzWDMwRDc2SnBqTU95ZHN3WjdJR1pwVEpvTHVFdUJqRHozMXpobjJvU1FxdFRQeXM0Sk9IOVU5UnJ2REIwZTQrVVpJSE51RlhaUWEvL3hiNnZvN1RRN04vYTdSZ2djZUZUNk03SHpTUGl0STgyZU1WeWN1Q2VqNUtZRkx0NkZybmx3bHM3ZEZBZnJobjRNZEFuMXl2RkN3aGd6TUpoUXdRUURKc20zbG9KT1pmQW9pajBROFdYSWVGdTJTUHogZXhha21z"}
        _sshkey = cluctrl.mGetUserkey(_options)
        cluctrl.mValidatesshkey(_sshkey)

    def test_mValidatesshkey_badkey(self):
        cluctrl = self.mGetClubox()
        _options = self.mGetPayload()

        #Lets try with a base64 string
        _options.jsonconf['vm'] = {"sshkey": "Z2Vla3Nmb3JnZWVrcw=="}
        try:
            _sshkey = cluctrl.mGetUserkey(_options)
            cluctrl.mValidatesshkey(_sshkey)
        except Exception as e:
            _rc = "SSH Key not provided or incorrect" in str(e)
            self.assertEqual(_rc, 1)

    def test_keys_ping(self):

        xm_list_out_empty = [
            "Name                                        ID   Mem VCPUs      State   Time(s)",
            "Domain-0                                     0  8785     4     r----- 4737270.8"
        ]

        xm_list_out = list(xm_list_out_empty)
        for _, _domu in self.mGetClubox().mReturnDom0DomUPair():
            xm_list_out.append(_domu + " 1 92163    10     -b---- 427769.7")

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("imageinfo | grep 'Node type:'", aStdout="DOM0 DOM0 DOM0"),
                    exaMockCommand("/bin/test -e /bin/virsh", aRc=0, aPersist=True),
                    exaMockCommand("/bin/virsh domstate", aRc=0, aPersist=True),
                    
                ],
                [

                    exaMockCommand("imageinfo | grep 'Node type:'", aRc=0, aPersist=True),
                    exaMockCommand("cat /sys/hypervisor/type /sys/hypervisor/uuid", aRc=0, aStdout=cmdOutput1,aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout='\n'.join(_domu for _, _domu in self.mGetClubox().mReturnDom0DomUPair()), aRc=0, aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("/bin/test -e /etc/xen/auto/", aRc=0, aPersist=True),
                    exaMockCommand("/bin/unlink /etc/xen/auto/", aRc=0, aPersist=True),
                    exaMockCommand("cat /sys/hypervisor/type", aRc=0, aStdout=cmdOutput2,aPersist=True),

                ],
                [
                    exaMockCommand("cat /sys/hypervisor/type", aRc=0, aStdout=cmdOutput2,aPersist=True),
                    exaMockCommand("xm list", aStdout='\n'.join(xm_list_out), aRc=0),
                    exaMockCommand("ls /EXAVMIMAGES/GuestImages/", aStdout='\n'.join(_domu for _, _domu in self.mGetClubox().mReturnDom0DomUPair()), aRc=0, aPersist=True),


                ]
                ],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand('/bin/ping -c 1 *', aRc=0, aPersist=True)
                ]
                ],

        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        cluctrl = self.mGetClubox()
        _options.jsonconf['vms'] = ['_all_']

        _options.vmid = '_all_'
        _options.vmcmd = 'ping'
        _options.debug = '1'
        cluctrl.mSetOptions(_options)
        _rc = cluctrl.mHandlerVmCmd()

if __name__ == '__main__':
    unittest.main()

