#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/exatest/tools/xml_generation/tests_lacp_xml_generation.py /main/15 2025/11/15 11:40:55 joysjose Exp $
#
# tests_lacp_xml_generation.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_lacp_xml_generation.py - test LACP XML generation
#
#    DESCRIPTION
#      Test LACP is properly configured in generated OEDA XML
#
#    NOTES
#      - If you change this file, please make sure lines are no longer than 80
#        characters (including newline) and it passes pylint, mypy and flake8
#        with all the default checks enabled.
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    08/21/25 - Bug 38299487 - ECS_MAIN -> ETF -> NSLOOKUP COMMAND
#                           IS SENDING RETURN STATUS 1 , CAUSING
#                           TESTS_LACP_XML_GENERATION_PY.DIF AND
#                           TESTS_XML_GENERATION_PY.DIF TO FAIL
#    jesandov    10/16/23 - 35729701: Support of OL7 + OL8
#    gparada     05/26/23 - 34556452 Upd cmd for call to mValidateVersionForMVV
#    jesandov    03/31/23 - 35141247 - Add SSH Connection Pool
#    rkhemcha    08/11/22 - 34450609 - Change unittests to read LACP info from
#                           root level rather than node level
#    naps        06/20/22 - check for es.properties file.
#    jlombera    09/29/21 - Bug 33412675: add entry to mock command "nslookup
#    jlombera    07/20/21 - Bug 33116666: test LACP XML generation
#    jlombera    07/20/21 - Creation
#
"""
Tests for XML generation with LACP configuration.
"""

import copy
import json
import os
import re
import shlex
import subprocess
import unittest
import warnings

warnings.filterwarnings("ignore")

from typing import Any, Mapping, Sequence

from exabox.core.MockCommand import MockCommand, exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.tools.AttributeWrapper import wrapStrBytesFunctions
from exabox.tools.ebXmlGen.ebFacadeXmlGen import ebFacadeXmlGen
from exabox.log.LogMgr import ebLogInfo, ebLogError

# { <domU>: { "client": <True|False>, "backup": <True|False> }, ...}
DomUsLacpAttrs = Mapping[str, Mapping[str, bool]]


def oedacli_get_net_lacp_attr(
        oedacli_path: str,
        xml: str,
        domus: Sequence[str]) -> DomUsLacpAttrs:
    """Get LACP attributes of client/backup networks of the given DomUs

    ... from the given XML.
    """

    def __domu_lacp_attr(domu: str, net_type: str) -> bool:
        oedacli_cmd = \
            f"list networks where hostname={domu} networktype={net_type}"
        cmd_args = (oedacli_path, "-q", "-j", "-c", xml, "-e", oedacli_cmd)
        proc = subprocess.run(cmd_args, stdout=subprocess.PIPE, check=True)

        # get attribute "lacp", assume "false" if not set
        lacp = json.loads(proc.stdout)[0].get("lacp", "false")

        return lacp.lower() == "true"

    return {
        domu: {"client": __domu_lacp_attr(domu, "client"),
               "backup": __domu_lacp_attr(domu, "backup")}
        for domu in domus
    }


def get_lacp_patched_payload(
        payload: Mapping[str, Any],
        lacp_conf: DomUsLacpAttrs) -> Mapping[str, Any]:
    """Return payload patched with LACP config."""
    # Work on a copy of the payload.  We assume it's a create-service-like
    # payload.
    payload = copy.deepcopy(payload)
    payload.get("customer_network").update(lacp_conf)

    return payload


def set_lacp_payloads(domus, client_flag=False, backup_flag=False):

    input_payload = {
        "network_types": {
                "client": {
                    "bonding_mode": "active-backup"
                },
                "backup": {
                    "bonding_mode": "active-backup"
                }
            }
    }

    if client_flag:
        input_payload["network_types"]["client"]["bonding_mode"] = "lacp"
    if backup_flag:
        input_payload["network_types"]["backup"]["bonding_mode"] = "lacp"

    expected_results = {
            domu: {"client": client_flag, "backup": backup_flag}
            for domu in domus
        }


    return input_payload, expected_results

# Silence pylint about CamelCase names
# pylint: disable=invalid-name
class TestLacpXmlGen(ebTestClucontrol):
    """Test"""
    @classmethod
    def setUpClass(cls):
        # this method signature differs than one in ebTestClucontrol
        # pylint: disable=arguments-differ
        super().setUpClass(aGenerateDatabase=True, aUseOeda=True, aEnableUTFlag=False)

    def mSetupBoilerplate(self):
        """Setup test.

        NOTE: none of what is done in this method is relevant for LACP unit
              testing, but is required or exaBoxCluCtrl.mDispatchCluster()
              fails.  This was copied almost verbatim from
              tests_xml_generation.py.
        """
        oedapath = self.mGetUtil().mGetOedaDir()

        def mRealExecute(aCmd, aStdIn):
            # aStdIn is not used
            # pylint: disable=unused-argument

            if aCmd.startswith("/bin/scp"):
                aCmd = aCmd.replace("/bin/scp", "/bin/cp")

            args = shlex.split(aCmd)

            proc = subprocess.Popen(
                args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, cwd=oedapath)

            stdout, stderr = wrapStrBytesFunctions(proc).communicate()

            return proc.returncode, stdout, stderr

        cmds = {
            self.mGetRegexCell(): [
                [
                    exaMockCommand(
                        "imageinfo -version", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand(
                        "cellcli -e list.*FLASH.*", aStdout="7.15366"),
                    exaMockCommand(
                        "cellcli -e list.*FLASH.*", aStdout="7.15366"),
                    exaMockCommand(
                        "cellcli -e list.*DELTA.*", aStdout="7.15366"),
                    exaMockCommand(
                        "cellcli -e list.*CATALOG.*", aStdout="7.15366"),
                    exaMockCommand(
                        "/opt/oracle.cellos/exadata.img.hw --get model",
                        aStdout="ORACLE SERVER X6-2L")
                ],
                [
                    exaMockCommand(
                        "cellcli -e list.*FLASH.*", aStdout="7.15366"),
                    exaMockCommand(
                        "cellcli -e list.*FLASH.*", aStdout="7.15366"),
                    exaMockCommand(
                        "/opt/oracle.cellos/exadata.img.hw --get model",
                        aStdout="ORACLE SERVER X6-2L")
                ],
                [
                    exaMockCommand(
                        "/opt/oracle.cellos/exadata.img.hw --get model",
                        aStdout="ORACLE SERVER X6-2L")
                ],
                [
                    exaMockCommand(
                        "/opt/oracle.cellos/exadata.img.hw --get model",
                        aStdout="ORACLE SERVER X6-2L")
                ]
            ],
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(".*shared_env.*", aRc=1)
                ],
                [
                    exaMockCommand(
                        "imageinfo -version", aStdout="20.2.0.0.0.200803")
                ],
                [
                    exaMockCommand(".*shared_env.*", aRc=1),
                    exaMockCommand(
                        "cat.*virbr.*", aStdout="52:54:00:87:07:09"),
                    exaMockCommand(
                        "imageinfo -version", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand(
                        "/opt/oracle.cellos/exadata.img.hw --get model",
                        aStdout="ORACLE SERVER X6-2L")
                ],
                [
                    exaMockCommand(
                        "imageinfo -version", aStdout="20.2.0.0.0.200803"),
                    exaMockCommand(
                        "/opt/oracle.cellos/exadata.img.hw --get model",
                        aStdout="ORACLE SERVER X6-2L")
                ],
                [
                    exaMockCommand(
                        "/opt/oracle.cellos/exadata.img.hw --get model",
                        aStdout="ORACLE SERVER X6-2L")
                ]
            ],
            self.mGetRegexVm(): [
                [
                    exaMockCommand("ls /u01/app", aRc=1),
                    exaMockCommand(re.escape("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':' "), aRc=0, aStdout="/u01/app/18.1.0.0/grid" ,aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/oraversion -baseVersion"), aRc=0, aStdout="18.0.0.0.0" ,aPersist=True),
                    exaMockCommand(re.escape("export ORACLE_HOME=/u01/app/18.1.0.0/grid; $ORACLE_HOME/bin/orabase"), aRc=0, aStdout="/u01/app/18.1.0.0/grid" ,aPersist=True),
                ]
            ],
            self.mGetRegexLocal(): [
                [
                    # Create Keys folder
                    MockCommand(".*mkdir.*ibswitch.*", mRealExecute),
                    MockCommand(".*mkdir.*clusters.*", mRealExecute),
                    MockCommand(".*chmod.*600.*", mRealExecute),

                    # NAT lookup
                    MockCommand(".*nslookup.*", mRealExecute),

                    # Create OEDA workdir
                    MockCommand(".*mkdir.*requests.*", mRealExecute),
                    MockCommand(".*chmod.*stage.sh.*", mRealExecute),
                    MockCommand(".*sed.*", mRealExecute, aPersist=True),
                    MockCommand(".*stage.sh.*", mRealExecute),

                    # Copy XML
                    MockCommand(".*mkdir.*exacloud.conf.*", mRealExecute),
                    MockCommand(".*scp.*", mRealExecute),

                    # KVM Execution
                    MockCommand(".*mkdir.*log*", mRealExecute),
                    MockCommand(".*cp.*xml*", mRealExecute, aPersist=True),

                    # Execute install.sh
                    exaMockCommand("/bin/test -e .*es.properties", aRc=0,  aPersist=True),
                    MockCommand(".*install.sh.*", mRealExecute),
                    exaMockCommand(
                        ".*grep Version.*", aStdout="Version : 201207", aPersist=True),

                    # Execute info call
                    exaMockCommand("/bin/test -e .*es.properties", aRc=0,  aPersist=True),
                    MockCommand(".*install.sh.*", mRealExecute),
                    MockCommand(".*install.sh.*", mRealExecute),

                    # Clean up of environment
                    MockCommand(".*rm -f.*", mRealExecute),

                    # Any other command
                    MockCommand(".*", mRealExecute, aPersist=True),
                ]
            ]
        }

        # Init new Args
        self.mPrepareMockCommands(cmds)
        self.mGetContext().mSetConfigOption("repository_root", self.mGetPath())

    def mRunTest(
            self,
            test_id: str,
            json_payload: Mapping[str, Any],
            expected_lacp_attrs: DomUsLacpAttrs) -> None:
        """Run test.

        Patch XML using given JSON payload and test that LACP attributes is the
        patched XML are the same as expected_lacp_attrs.
        """
        savedir = self.mGetUtil().mGetOutputDir()
        payload = self.mGetResourcesJsonFile("payload.json")

        self.mSetupBoilerplate()

        # Execute xml_generator framework
        facade = ebFacadeXmlGen(test_id, payload, savedir)
        xmlpath = os.path.abspath(facade.mGenerateXml())

        cluctrl = self.mGetClubox()
        cluctrl.mSetSharedEnv(None)
        cluctrl.mSetConfigPath(xmlpath)
        cluctrl.mGetArgsOptions().jsonconf = json_payload
        try:
            # generate XML
            cluctrl.mDispatchCluster("info", cluctrl.mGetArgsOptions())

            domus = [domu for _, domu in cluctrl.mReturnDom0DomUPair()]

            # get LACP attributes
            oedacli_bin = os.path.join(cluctrl.mGetOedaPath(), 'oedacli')
            xml_lacp_attrs = oedacli_get_net_lacp_attr(
                oedacli_bin, cluctrl.mGetPatchConfig(), domus)

            msg = (f"test_id: {test_id}\n"
                f"expected_attrs: {expected_lacp_attrs}\n"
                f"xml_attrs:      {xml_lacp_attrs}")

            self.assertEqual(expected_lacp_attrs, xml_lacp_attrs, msg)
        except Exception as e:
            ebLogError(f"Exception: {str(e)}")


    def test_global(self):
        """Test global LACP config"""
        cluctrl = self.mGetClubox()
        cluctrl.mSetSharedEnv(None)
        ctx = self.mGetContext()
        payload = self.mGetResourcesJsonFile("cs_payload.json")
        domus = tuple(domu for _, domu in cluctrl.mReturnDom0DomUPair())

        no_lacp = {
            domu: {"client": False, "backup": False}
            for domu in domus
        }

        # no LACP should be configured by default
        try:
            cluctrl.mSetOciExacc(False)
            self.mRunTest("global_no_lacp_1", payload, expected_lacp_attrs=no_lacp)
        except Exception as e:
            ebLogError("Could not update Cell Disk Size", str(e))

        # no LACP should be configured by default, even for ExaCC
        cluctrl.mSetOciExacc(True)
        self.mRunTest("global_no_lacp_2", payload, expected_lacp_attrs=no_lacp)

        # no LACP should be configured, if global parameters are not "True"
        ctx.mSetConfigOption("customer_net_client_lacp", "False")
        ctx.mSetConfigOption("customer_net_backup_lacp", "False")
        self.mRunTest("global_no_lacp_3", payload, expected_lacp_attrs=no_lacp)

        # no LACP should be configured, if global parameters are "True" but not
        # ExaCC
        cluctrl.mSetOciExacc(False)
        ctx.mSetConfigOption("customer_net_client_lacp", "True")
        ctx.mSetConfigOption("customer_net_backup_lacp", "True")
        self.mRunTest("global_no_lacp_4", payload, expected_lacp_attrs=no_lacp)

        all_lacp = {
            domu: {"client": True, "backup": True}
            for domu in domus
        }

        cluctrl.mSetOciExacc(True)
        ctx.mSetConfigOption("customer_net_client_lacp", "True")
        ctx.mSetConfigOption("customer_net_backup_lacp", "True")
        self.mRunTest("global_all", payload, expected_lacp_attrs=all_lacp)

        client_lacp = {
            domu: {"client": True, "backup": False}
            for domu in domus
        }

        ctx.mSetConfigOption("customer_net_client_lacp", "True")
        ctx.mSetConfigOption("customer_net_backup_lacp", "False")
        self.mRunTest(
            "global_client", payload, expected_lacp_attrs=client_lacp)

        backup_lacp = {
            domu: {"client": False, "backup": True}
            for domu in domus
        }

        ctx.mSetConfigOption("customer_net_client_lacp", "False")
        ctx.mSetConfigOption("customer_net_backup_lacp", "True")
        self.mRunTest(
            "global_backup", payload, expected_lacp_attrs=backup_lacp)


    def test_payload(self):
        """Test payload-based LACP config."""
        # ensure LACP is not enabled globally
        ctx = self.mGetContext()
        ctx.mSetConfigOption("customer_net_client_lacp", "False")
        ctx.mSetConfigOption("customer_net_backup_lacp", "False")

        cluctrl = self.mGetClubox()
        cluctrl.mSetSharedEnv(None)
        orig_payload = self.mGetResourcesJsonFile("cs_payload.json")
        domus = tuple(domu for _, domu in cluctrl.mReturnDom0DomUPair())

        no_lacp_payload,  no_lacp_result = set_lacp_payloads(domus,
                                                             client_flag=False,
                                                             backup_flag=False)

        all_lacp_payload, all_lacp_result = set_lacp_payloads(domus,
                                                              client_flag=True,
                                                              backup_flag=True)

        # No LACP should be configured if no ExaCC, even if LACP is configured
        # in payload.
        cluctrl.mSetOciExacc(False)
        payload = get_lacp_patched_payload(orig_payload, lacp_conf=all_lacp_payload)
        self.mRunTest("payload_no_exacc", payload, expected_lacp_attrs=no_lacp_result)

        cluctrl.mSetOciExacc(True)

        # LACP in all networks
        payload = get_lacp_patched_payload(orig_payload, lacp_conf=all_lacp_payload)
        self.mRunTest("payload_all", payload, expected_lacp_attrs=all_lacp_result)

        # LACP only in client network
        client_lacp_payload,  client_lacp_result = set_lacp_payloads(domus,
                                                                     client_flag=True,
                                                                     backup_flag=False)

        payload = get_lacp_patched_payload(orig_payload, lacp_conf=client_lacp_payload)
        self.mRunTest(
            "payload_client", payload, expected_lacp_attrs=client_lacp_result)

        # LACP only in backup network
        backup_lacp_payload, backup_lacp_result = set_lacp_payloads(domus,
                                                                    client_flag=False,
                                                                    backup_flag=True)

        payload = get_lacp_patched_payload(orig_payload, lacp_conf=backup_lacp_payload)
        self.mRunTest(
            "payload_backup", payload, expected_lacp_attrs=backup_lacp_result)


    def test_mixed(self):
        """Test mixed global/payload-based LACP config."""
        ctx = self.mGetContext()

        cluctrl = self.mGetClubox()
        cluctrl.mSetSharedEnv(None)
        cluctrl.mSetOciExacc(True)
        orig_payload = self.mGetResourcesJsonFile("cs_payload.json")
        domus = tuple(domu for _, domu in cluctrl.mReturnDom0DomUPair())

        no_lacp_payload, no_lacp_result = set_lacp_payloads(domus,
                                                            client_flag=False,
                                                            backup_flag=False)

        all_lacp_payload, all_lacp_result = set_lacp_payloads(domus,
                                                              client_flag=True,
                                                              backup_flag=True)

        #
        # Payload config have priority over global config
        #

        ctx.mSetConfigOption("customer_net_client_lacp", "False")
        ctx.mSetConfigOption("customer_net_backup_lacp", "False")
        payload = get_lacp_patched_payload(orig_payload, lacp_conf=all_lacp_payload)

        self.mRunTest(
            "mixed_payload_first_on", payload, expected_lacp_attrs=all_lacp_result)

        ctx.mSetConfigOption("customer_net_client_lacp", "True")
        ctx.mSetConfigOption("customer_net_backup_lacp", "True")
        payload = get_lacp_patched_payload(orig_payload, lacp_conf=no_lacp_payload)

        self.mRunTest(
            "mixed_payload_first_off", payload, expected_lacp_attrs=no_lacp_result)

        backup_missing = {
            "network_types": {
                "client": {
                    "bonding_mode": "lacp"
                }
            }
        }

        # If LACP config is missing in payload, global config is honored
        ctx.mSetConfigOption("customer_net_client_lacp", "True")
        ctx.mSetConfigOption("customer_net_backup_lacp", "True")
        payload = get_lacp_patched_payload(
            orig_payload, lacp_conf=backup_missing)
        self.mRunTest(
            "mixed_payload_backup_missing",
            payload, expected_lacp_attrs=all_lacp_result)


if __name__ == '__main__':
    unittest.main()
