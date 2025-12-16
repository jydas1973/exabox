import unittest

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
import os
import re

class TestFips(ebTestClucontrol):

    '''
    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        super().setUpClass()
    '''

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__ociexacc = False
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True
        get_gcontext().mSetConfigOption('kvm_var_size',None)
        self.mGetClubox().mRegisterVgComponents()

    def test_fips_conf_disable(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="1"),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "disabled"}}}}
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=_options, aHost=_dom0)
        self.assertEqual(_rc, -1)
   
    def test_fips_conf_disable2(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="1"),
                ]
                ],
        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "disabled"}}}}
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=None, aHost=_dom0)
        self.assertEqual(_rc, -1)

    def test_fips_exabox_conf(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="1"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=1),
                    exaMockCommand("/bin/sed -i 's/\^Ciphers.*/Ciphers aes128-ctr,aes192-ctr,aes256-ctr/'.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout="new-sha"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs --both --enable --macs hmac-sha2-256,hmac-sha2-512"),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=0),
                    exaMockCommand("/bin/sed -i 's/curve25519-sha256@libssh.org.*"),
                    exaMockCommand("/bin/sed -i 's/curve25519-sha256.*"),
                    exaMockCommand("/sbin/service sshd restart"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=1),
                    exaMockCommand("/bin/sed -i 's/\^Ciphers.*/Ciphers aes128-ctr,aes192-ctr,aes256-ctr/'.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout="new-sha"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs --both --enable --macs hmac-sha2-256,hmac-sha2-512"),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=0),
                    exaMockCommand("/bin/sed -i 's/curve25519-sha256@libssh.org.*"),
                    exaMockCommand("/bin/sed -i 's/curve25519-sha256.*"),
                    exaMockCommand("/sbin/service sshd restart")

                ],
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "disabled"}}}}
        cluctrl = self.mGetClubox()
        get_gcontext().mSetConfigOption("enforce_fips_compliance", "True")
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=None, aHost=_dom0)
        self.assertEqual(_rc, 0)
 
    def test_fips_ssh_conf_only(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="1"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=1),
                    exaMockCommand("/bin/sed -i 's/\^Ciphers.*/Ciphers aes128-ctr,aes192-ctr,aes256-ctr/'.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout="new-sha"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs --both --enable --macs hmac-sha2-256,hmac-sha2-512"),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=0),
                    exaMockCommand("/bin/sed -i 's/curve25519-sha256@libssh.org.*"),
                    exaMockCommand("/bin/sed -i 's/curve25519-sha256.*"),
                    exaMockCommand("/sbin/service sshd restart"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=1),
                    exaMockCommand("/bin/sed -i 's/\^Ciphers.*/Ciphers aes128-ctr,aes192-ctr,aes256-ctr/'.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout="new-sha"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs --both --enable --macs hmac-sha2-256,hmac-sha2-512"),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=0),
                    exaMockCommand("/bin/sed -i 's/curve25519-sha256@libssh.org.*"),
                    exaMockCommand("/bin/sed -i 's/curve25519-sha256.*"),
                    exaMockCommand("/sbin/service sshd restart")

                ],
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "enabled"}}}}       
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=_options, aHost=_dom0)
        self.assertEqual(_rc, 0)

    def test_fips_active_el7(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="22.1.0.0.0.220703"),
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="0"),
                    exaMockCommand("/bin/rpm -q dracut-fips", aRc=1),
                    exaMockCommand("/bin/rpm -q dracut", aStdout="dracut-el7-v1", aRc=1),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/rpm -i /tmp/hmaccalc-0.9.13-4.el7.x86_64.rpm"),
                    exaMockCommand("/bin/rpm -i /tmp/dracut-fips-el7.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --status", aStdout="FIPS mode is configured and active"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),
                ],
            ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ls  misc/fips/.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "enabled"}}}}
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=_options, aHost=_dom0)
        self.assertEqual(_rc, 0)

    def test_fips_active(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/usr/local/bin/imageinfo -ver", aStdout="22.1.0.0.0.220703"),
                ],
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="0"),
                    exaMockCommand("/bin/rpm -q dracut-fips", aRc=1),
                    exaMockCommand("/bin/rpm -q dracut", aStdout="dracut-el6-v1", aRc=1),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/rpm -i /tmp/hmaccalc-0.9.12-2.el6.x86_64.rpm"),
                    exaMockCommand("/bin/rpm -i /tmp/dracut-fips-el6.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --status", aStdout="FIPS mode is configured and active"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),

                ],
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ls  misc/fips/.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "enabled"}}}}
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=_options, aHost=_dom0)
        self.assertEqual(_rc, 0)

    def test_fips_disabled(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="0"),
                    exaMockCommand("/bin/rpm -q dracut-fips", aRc=1),
                    exaMockCommand("/bin/rpm -q dracut", aStdout="dracut-el6-v1", aRc=1),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/rpm -i /tmp/hmaccalc-0.9.12-2.el6.x86_64.rpm"),
                    exaMockCommand("/bin/rpm -i /tmp/dracut-fips-el6.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --status", aStdout="FIPS mode is disabled"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --enable"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),

                ],
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ls  misc/fips/.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }
        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "enabled"}}}}
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=_options, aHost=_dom0)
        self.assertEqual(_rc, 0)

    def test_fips_inactive(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="0"),
                    exaMockCommand("/bin/rpm -q dracut-fips", aRc=1),
                    exaMockCommand("/bin/rpm -q dracut", aStdout="dracut-el6-v1", aRc=1),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/rpm -i /tmp/hmaccalc-0.9.12-2.el6.x86_64.rpm"),
                    exaMockCommand("/bin/rpm -i /tmp/dracut-fips-el6.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --status", aStdout="FIPS mode is configured but not activated"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --enable"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),

                ],
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ls  misc/fips/.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }
        self.mPrepareMockCommands(_cmds)


        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "enabled"}}}}
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=_options, aHost=_dom0)
        self.assertEqual(_rc, 0)

    
    def test_fips_enable_manually(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="0"),
                    exaMockCommand("/bin/rpm -q dracut-fips", aRc=1),
                    exaMockCommand("/bin/test -e .*dracut"),
                    exaMockCommand("/bin/rpm -q dracut", aStdout="dracut-el6-v1", aRc=1),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/rpm -i /tmp/hmaccalc-0.9.12-2.el6.x86_64.rpm"),
                    exaMockCommand("/bin/rpm -i /tmp/dracut-fips-el6.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --status"),
                    exaMockCommand("/bin/mount | /bin/grep /boot/efi", aRc=0),
                    exaMockCommand("/bin/findmnt --output=UUID --noheadings --target=/boot/efi", aStdout="efi-1234"),
                    exaMockCommand("/bin/findmnt --output=UUID --noheadings --target=/boot", aStdout="boot-1234"),
                    exaMockCommand("/bin/grep 'fips=1' /etc/default/grub", aRc=1),
                    exaMockCommand("/bin/grep 'fips=0' /etc/default/grub", aRc=0),
                    exaMockCommand("/bin/sed -i 's/fips=0/fips=1 boot=UUID=.*"),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg"),
                    exaMockCommand("/bin/test -e /boot/efi/EFI/redhat/grub.cfg", aRc=0),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/efi/EFI/redhat/grub.cfg"),
                    exaMockCommand("/bin/test -e /boot/efi/EFI/XEN/xen.cfg", aRc=0),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/efi/EFI/XEN/xen.cfg"),
                    exaMockCommand("/sbin/dracut -f"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --enable"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),

                ],
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ls  misc/fips/.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }
        self.mPrepareMockCommands(_cmds)


        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "enabled"}}}}
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=_options, aHost=_dom0)
        self.assertEqual(_rc, 0)

    def test_fips_enable_manually2(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="0"),
                    exaMockCommand("/bin/rpm -q dracut-fips", aRc=1),
                    exaMockCommand("/bin/rpm -q dracut", aStdout="dracut-el6-v1", aRc=1),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/rpm -i /tmp/hmaccalc-0.9.12-2.el6.x86_64.rpm"),
                    exaMockCommand("/bin/rpm -i /tmp/dracut-fips-el6.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --status"),
                    exaMockCommand("/bin/mount | /bin/grep /boot/efi", aRc=0),
                    exaMockCommand("/bin/findmnt --output=UUID --noheadings --target=/boot/efi", aStdout="efi-1234"),
                    exaMockCommand("/bin/findmnt --output=UUID --noheadings --target=/boot", aStdout="boot-1234"),
                    exaMockCommand("/bin/grep 'fips=1' /etc/default/grub", aRc=1),
                    exaMockCommand("/bin/grep 'fips=0' /etc/default/grub", aRc=1),

                    exaMockCommand("/bin/sed -i '/\^GRUB_CMDLINE.*"),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg"),
                    exaMockCommand("/bin/test -e /boot/efi/EFI/redhat/grub.cfg", aRc=0),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/efi/EFI/redhat/grub.cfg"),
                    exaMockCommand("/bin/test -e /boot/efi/EFI/XEN/xen.cfg", aRc=0),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/efi/EFI/XEN/xen.cfg"),
                    exaMockCommand("/bin/test -e .*dracut"),
                    exaMockCommand("/sbin/dracut -f"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --enable"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),

                ],
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ls  misc/fips/.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }
        self.mPrepareMockCommands(_cmds)


        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "enabled"}}}}
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=_options, aHost=_dom0)
        self.assertEqual(_rc, 0)

    def test_fips_enable_manually3(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="0"),
                    exaMockCommand("/bin/rpm -q dracut-fips", aRc=1),
                    exaMockCommand("/bin/rpm -q dracut", aStdout="dracut-el6-v1", aRc=1),
                    exaMockCommand("/bin/test -e .*dracut"),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/rpm -i /tmp/hmaccalc-0.9.12-2.el6.x86_64.rpm"),
                    exaMockCommand("/bin/rpm -i /tmp/dracut-fips-el6.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --status"),
                    exaMockCommand("/bin/mount | /bin/grep /boot/efi", aRc=1),


                    exaMockCommand("/bin/findmnt --output=UUID --noheadings --target=/boot", aStdout="boot-1234"),
                    exaMockCommand("/bin/grep 'fips=1' /etc/default/grub", aRc=1),
                    exaMockCommand("/bin/grep 'fips=0' /etc/default/grub", aRc=1),

                    exaMockCommand("/bin/sed -i '/\^GRUB_CMDLINE.*"),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg"),
                    exaMockCommand("/bin/test -e /boot/efi/EFI/redhat/grub.cfg", aRc=0),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/efi/EFI/redhat/grub.cfg"),
                    exaMockCommand("/bin/test -e /boot/efi/EFI/XEN/xen.cfg", aRc=0),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/efi/EFI/XEN/xen.cfg"),
                    exaMockCommand("/sbin/dracut -f"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --enable"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),

                ],
                ],

            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ls  misc/fips/.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }
        self.mPrepareMockCommands(_cmds)


        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "enabled"}}}}
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=_options, aHost=_dom0)
        self.assertEqual(_rc, 0)

    def test_fips_enable_manually4(self):

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("/bin/cat /proc/sys/crypto/fips_enabled", aStdout="0"),
                    exaMockCommand("/bin/rpm -q dracut-fips", aRc=1),
                    exaMockCommand("/bin/rpm -q dracut", aStdout="dracut-el6-v1", aRc=1),
                    exaMockCommand("/bin/test -e .*dracut"),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/scp misc/fips/.*"),
                    exaMockCommand("/bin/rpm -i /tmp/hmaccalc-0.9.12-2.el6.x86_64.rpm"),
                    exaMockCommand("/bin/rpm -i /tmp/dracut-fips-el6.*"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --status"),
                    exaMockCommand("/bin/mount | /bin/grep /boot/efi", aRc=1),


                    exaMockCommand("/bin/findmnt --output=UUID --noheadings --target=/boot", aStdout="boot-1234"),
                    exaMockCommand("/bin/grep 'fips=1' /etc/default/grub", aRc=1),
                    exaMockCommand("/bin/grep 'fips=0' /etc/default/grub", aRc=0),

                    exaMockCommand("/bin/sed -i 's/fips=0/fips=1 boot=UUID=.*"),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/grub2/grub.cfg"),
                    exaMockCommand("/bin/test -e /boot/efi/EFI/redhat/grub.cfg", aRc=0),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/efi/EFI/redhat/grub.cfg"),
                    exaMockCommand("/bin/test -e /boot/efi/EFI/XEN/xen.cfg", aRc=0),
                    exaMockCommand("/usr/sbin/grub2-mkconfig -o /boot/efi/EFI/XEN/xen.cfg"),
                    exaMockCommand("/sbin/dracut -f"),
                    exaMockCommand("/opt/oracle.cellos/host_access_control fips-mode --enable"),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),
                    exaMockCommand("/bin/grep '\^Ciphers aes128-ctr,aes192-ctr,aes256-ctr'.*", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/host_access_control ssh-macs -s.*", aStdout=""),
                    exaMockCommand("/bin/grep '\^KexAlgorithms.*curve25519-sha256'.*", aRc=1),

                ],
                ],


            self.mGetRegexLocal(): [
                [
                    exaMockCommand("/bin/ls  misc/fips/.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True),
                ],
            ]

        }
        self.mPrepareMockCommands(_cmds)


        _options = self.mGetPayload()
        _options.jsonconf = {'dbaas_api': {'params': {'common': {'fips_compliance': "enabled"}}}}
        cluctrl = self.mGetClubox()
        for _dom0, _ in cluctrl.mReturnDom0DomUPair():
            _rc, _str = cluctrl.mMakeFipsCompliant(aOptions=_options, aHost=_dom0)
        self.assertEqual(_rc, 0)


if __name__ == '__main__':
    unittest.main()

