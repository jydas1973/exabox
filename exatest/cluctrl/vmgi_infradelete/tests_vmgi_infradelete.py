#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/cluctrl/vmgi_infradelete/tests_vmgi_infradelete.py /main/9 2025/03/07 06:08:42 aararora Exp $
#
# tests_vmgi_infradelete.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_vmgi_infradelete.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    03/04/25 - Bug 37651686: Drop PMEMCACHE and PMEMLOG before
#                           running secure erase
#    aararora    11/27/24 - Bug 37067118: Use cellcli drop command for
#                           performing secure erase.
#    aararora    09/10/24 - Bug 37041670: Provide list of serial numbers for
#                           secure erase
#    aararora    08/05/24 - ER 36904128: Add API for secure erase
#    jfsaldan    08/22/23 - Bug 35719818 - PLEASE PROVIDE A WAY TO IDENTIFY
#                           FROM A XEN DOM0 IF THE GUESTVM HAS LUKS ENABLED OR
#                           NOT
#    jfsaldan    11/03/22 - Bug 33993510 - CELLDISKS RECREATED AFTER DBSYSTEM
#                           TERMINATION
#    jfsaldan    06/09/22 - Bug 34242884 - Add vlan reset unittest during
#                           delete infra endpoint call
#    naps        03/07/22 - remove virsh dependency.
#    jesandov    02/21/22 - Creation
#

import unittest

from exabox.core.MockCommand import MockCommand, exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from unittest.mock import patch
from unittest.mock import MagicMock


class TestVMGIInfraDelete(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aUseOeda=True)

    # Bug 34242884 - Since we are moving the restore of the vlanID to 868 to
    # the infra delete endpoint, we need to patch oedacli in here to "mock"
    # the deploy of the action
    @patch("exabox.ovm.clucontrol.ebOedacli")
    def test_001_handler_vmgi_infradelete(self, aMagicOedacli):

        #Create args structure
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand("rm /etc/libvirt/qemu/.*"),
                    exaMockCommand("usr/sbin/vm_maker --list-domains | /usr/bin/grep -i 'shut off' | /usr/bin/awk '{print $1}'", aStdout="vm1(-)"),
                    exaMockCommand("test -e /EXAVMIMAGES/GuestImages/vm1", aRc=1),
                    exaMockCommand("virsh undefine.*vm1")
                ],
                [
                    exaMockCommand("rm /opt/exacloud/clusters/shared_env_enabled")
                ],
                [
                    exaMockCommand("test.*rm", aRc=0),
                    exaMockCommand("/bin/rm -rf /opt/exacloud/fs_encryption", aRc=0)
                ]
            ],
            self.mGetRegexCell(): [
                [
                    exaMockCommand("cellcli -e drop celldisk all"),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout="ORACLE SERVER X8-2L"),
                    exaMockCommand("/bin/test -e /bin/python"),
                    exaMockCommand("python /opt/oracle.cellos/lib/python/secureeraser --erase --all --hdd_erasure_method crypto --is_eligible", aRc=0, aPersist=True),
                ],
                [
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e drop celldisk all"),
                    exaMockCommand("/bin/test -e /bin/python"),
                    exaMockCommand("python /opt/oracle.cellos/lib/python/secureeraser --erase --all --hdd_erasure_method crypto --is_eligible", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e alter flashcache ALL FLUSH", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHCACHE ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHLOG ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMCACHE", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMLOG", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL FLASHDISK ERASE=7PASS", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL HARDDISK ERASE=3PASS", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e create celldisk all", aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e alter flashcache ALL FLUSH", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHCACHE ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHLOG ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMCACHE", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMLOG", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="19.0.0.0.0.220517.1", aPersist=True),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL FLASHDISK ERASE=7PASS", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e drop celldisk all"),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL HARDDISK ERASE=3PASS", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e create celldisk all", aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="19.0.0.0.0.220517.1", aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e drop celldisk all", aRc=0, aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)

        # Add mock stdout to aMagicOedacli to simulate the return status
        # of the deploy action
        aMagicOedacli.return_value.mRun.return_value = "Mock deploy"

        # Discover KVM
        self.mGetClubox().mSetEnableKVM(True)

        cluctrl = self.mGetClubox()

        # This test is running infra delete with secure cell erase for exadata version < 19.1.0
        cluctrl.mHandlerVMGIInfraDelete()

    def test_002_mHandlerSecureCellErase(self):
        """
        Test mHandlerSecureCellErase method
        """
        cluctrl = self.mGetClubox()

        #Create args structure
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/bin/test -e /bin/python", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout="ORACLE SERVER X8-2L"),
                    exaMockCommand("python /opt/oracle.cellos/lib/python/secureeraser --erase --all --hdd_erasure_method crypto --is_eligible", aRc=0),
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="24.1.0", aRc=0),
                    exaMockCommand("/bin/test -e /bin/python", aRc=0),
                    exaMockCommand("python /opt/oracle.cellos/lib/python/secureeraser --erase --all --hdd_erasure_method crypto --is_eligible", aRc=0),
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e alter flashcache ALL FLUSH", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHCACHE ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHLOG ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMCACHE", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMLOG", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL FLASHDISK", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL HARDDISK", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e LIST CELLDISK *", aRc=0, aStdout="UM7XE\nSEYLE\n", aPersist=True),
                    exaMockCommand("/bin/python /opt/oracle.cellos/lib/python/secureeraser --list --hdd *", aRc=0, aStdout="21130UM7XE\n21130SEYLE\n", aPersist=True),
                    exaMockCommand("/bin/test -e /root/secure_cell_erase_certs/*", aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/mkdir -p /root/secure_cell_erase_certs/*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/python /opt/oracle.cellos/lib/python/secureeraser --erase --erasure_method_optional "\
                        "--devices_to_erase UM7XE,SEYLE,21130UM7XE,21130SEYLE --flash_erasure_method=crypto --hdd_erasure_method=crypto --output=/root/secure_cell_erase_certs/*",
                        aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/usr/bin/ls /root/secure_cell_erase_certs/*", aRc=0, aStdout="secureeraser.2004XLA0KF.20240802_125741.certificate.html", aPersist=True),
                    exaMockCommand("cellcli -e create celldisk all", aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e alter flashcache ALL FLUSH", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHCACHE ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHLOG ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMCACHE", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMLOG", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="24.1.0.0.0.240517.1", aPersist=True),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL FLASHDISK", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL HARDDISK", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /bin/python", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e LIST CELLDISK *", aRc=0, aStdout="UM7XE\nSEYLE\n", aPersist=True),
                    exaMockCommand("/bin/python /opt/oracle.cellos/lib/python/secureeraser --list --hdd *", aRc=0, aStdout="21130UM7XE\n21130SEYLE\n", aPersist=True),
                    exaMockCommand("/bin/test -e /root/secure_cell_erase_certs/*", aRc=1, aStdout="", aPersist=True),
                    exaMockCommand("/bin/mkdir -p /root/secure_cell_erase_certs/*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/python /opt/oracle.cellos/lib/python/secureeraser --erase --erasure_method_optional "\
                        "--devices_to_erase UM7XE,SEYLE,21130UM7XE,21130SEYLE --flash_erasure_method=crypto --hdd_erasure_method=crypto --output=/root/secure_cell_erase_certs/*",
                        aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/usr/bin/ls /root/secure_cell_erase_certs/*", aRc=0, aStdout="secureeraser.2004XLA0KF.20240802_125741.certificate.html", aPersist=True),
                    exaMockCommand("cellcli -e create celldisk all", aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="24.1.0.0.0.240517.1", aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e drop celldisk all", aRc=0, aPersist=True)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        # This test is running secure cell erase for exadata version >= 19.1.0
        _options = cluctrl.mGetArgsOptions()
        _options.skip_serase = False
        cluctrl.mHandlerSecureCellErase(_options)

    def test_003_mHandlerSecureCellEraseWithCellCli(self):
        """
        Test mHandlerSecureCellErase method
        """
        super().setUpClass(aUseOeda=True)
        cluctrl = self.mGetClubox()

        #Create args structure
        _cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand("/bin/test -e /bin/python", aRc=0),
                    exaMockCommand("/opt/oracle.cellos/exadata.img.hw --get model", aStdout="ORACLE SERVER X8-2L"),
                    exaMockCommand("python /opt/oracle.cellos/lib/python/secureeraser --erase --all --hdd_erasure_method crypto --is_eligible", aRc=0),
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aStdout="25.1.0", aRc=0),
                    exaMockCommand("/bin/test -e /bin/python", aRc=0),
                    exaMockCommand("python /opt/oracle.cellos/lib/python/secureeraser --erase --all --hdd_erasure_method crypto --is_eligible", aRc=0),
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e alter flashcache ALL FLUSH", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHCACHE ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHLOG ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMCACHE", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMLOG", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/test -e /var/log/cellos", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL ERASE=7pass", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/usr/bin/ls /root/secure_cell_erase_certs/*", aRc=0, aStdout="secureeraser.2004XLA0KF.20240802_125741.certificate.html", aPersist=True),
                    exaMockCommand("cellcli -e create celldisk all", aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e alter flashcache ALL FLUSH", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHCACHE ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHLOG ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMCACHE", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMLOG", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/date *", aRc=0, aStdout="1732713219", aPersist=True),
                    exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="25.1.0.0.0.240517.1", aPersist=True),
                    exaMockCommand("/bin/test -e /var/log/cellos", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL ERASE=7pass", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/ls -Art /var/log/cellos/secureeraser*", aRc=0, aStdout="/var/log/cellos/secureeraser.2004XLA0KF.20240802_125741.certificate.html", aPersist=True),
                    exaMockCommand("/bin/stat -c *", aRc=0, aStdout="1732713224", aPersist=True),
                    exaMockCommand("cellcli -e create celldisk all", aRc=0, aStdout="", aPersist=True),
                ],
                [
                    exaMockCommand("/usr/local/bin/imageinfo -version", aRc=0, aStdout="25.1.0.0.0.240517.1", aPersist=True),
                    exaMockCommand("cellcli -e LIST GRIDDISK ATTRIBUTES NAME*", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/opt/oracle/cell/cellsrv/bin/cellcli -e drop celldisk all", aRc=0, aPersist=True),
                    exaMockCommand("cellcli -e alter flashcache ALL FLUSH", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHCACHE ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP FLASHLOG ALL", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMCACHE", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP PMEMLOG", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/date *", aRc=0, aStdout="1732713219", aPersist=True),
                    exaMockCommand("/bin/test -e /var/log/cellos", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("cellcli -e DROP CELLDISK ALL ERASE=7pass", aRc=0, aStdout="", aPersist=True),
                    exaMockCommand("/bin/ls -Art /var/log/cellos/secureeraser*", aRc=0, aStdout="/var/log/cellos/secureeraser.2004XLA0KF.20240802_125741.certificate.html", aPersist=True),
                    exaMockCommand("/bin/stat -c *", aRc=0, aStdout="1732713224", aPersist=True),
                    exaMockCommand("cellcli -e create celldisk all", aRc=0, aStdout="", aPersist=True),
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        # This test is running secure cell erase for exadata version >= 19.1.0
        _options = cluctrl.mGetArgsOptions()
        _options.skip_serase = False
        cluctrl.mHandlerSecureCellErase(_options)

if __name__ == '__main__':
    unittest.main(warnings='ignore')

# end of file
