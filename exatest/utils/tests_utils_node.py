#
# tests_utils_node.py
#
# Copyright (c) 2022, 2025, Oracle and/or its affiliates.
#
#    NAME
#      tests_utils_node.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aypaul      07/25/25 - Bug#38202055 Add unit test case for kill_proc_tree.
#    jfsaldan    10/30/24 - Bug 37207274 -
#                           EXACS:24.4.1:241021.0914:MULTI-VM:PARALLEL VM
#                           CLUSTER PROVISIONING FAILING AT PREVM SETUP
#                           STEP:EXACLOUD : COULD NOT UPDATE CELL DISK SIZE
#    ririgoye    08/22/23 - Bug 35631856 - Added ignore parameter testing
#    jlombera    02/22/22 - Bug 33882570: test _update_key_val_str()
#    jlombera    02/22/22 - Creation
#
"""Unit tests for exabox.utils.node"""

import unittest, psutil
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.utils.node import _update_key_val_str, node_list_process, connect_to_host, kill_proc_tree
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogInfo
from unittest.mock import patch, MagicMock

class MockProcess():

    pid = psutil.Process().pid

    def children(self, recursive):
        return [MockProcess()]

    def send_signal(self, sig):
        pass

    def status(self):
        return psutil.STATUS_ZOMBIE

class UtilsNodeTest(ebTestClucontrol):
    """exabox.utils.node unit tests"""

    def test_update_key_val_str(self):
        """Test _update_key_val_str()"""

        orig_str = """
# SOME COMMENT
    key1=   val1
key2 = val2
# ANOTHER COMMENT

key3=
key4=val4
key5
"""

        key_vals = {
            "key2": "NEW_VAL2",  # change value of "key2"
            "key4": None,        # remove "key4"
            "newkey": "NEW_VAL"  # add new key "newkey"
        }

        # Some considerations:
        #   * keys/lines not touched are left in the original state and
        #     original position.
        #
        #   * keys whose value is modified, are removed from their original
        #     position and added at the end with the new value.
        #
        #   * new keys are added at the end.
        #
        #   * a newline is added at the end.
        expected_str = """
# SOME COMMENT
    key1=   val1
# ANOTHER COMMENT

key3=
key5
key2=NEW_VAL2
newkey=NEW_VAL
"""

        new_str = _update_key_val_str(orig_str, key_vals)
        self.assertEqual(expected_str, new_str)

    def test_update_key_val_str_ignore(self):
        """
        This test asserts that as long as the ignore parameter is active, every
        key value pair that already exists in the file won't be updated. Only
        pairs that don't already exist will be added.

        For this particular case, a .bashrc file is being emulated.
        """
        sample_filename = ".samplebashrc"
        original_content = self.mGetResourcesTextFile(sample_filename)

        key_vals = {"COMMON_VAR": "THIS_VALUE_SHOULDNT_DISPLAY"}
        new_content = _update_key_val_str(original_content, key_vals, "=", ignore=True)

        self.assertEqual(original_content, new_content)

    def test_node_list_process_empty(self):
        """
        Test node_list_process
        """

        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"test.*pgrep", aRc=0),
                    exaMockCommand(f"test.*grep", aRc=0),
                    exaMockCommand(f"pgrep -af 'elasticConfig'", aRc=1),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                self.assertEqual(
                        [], node_list_process(_node, "elasticConfig"))

    def test_node_list_process_non_empty(self):
        """
        Test node_list_process
        """

        _list_out_proc = "1997 /opt/ovm/elasticConfig.sh\n"
        _cmds = {
            self.mGetRegexDom0(): [
                [
                    exaMockCommand(f"test.*pgrep", aRc=0),
                    exaMockCommand(f"test.*grep", aRc=0),
                    exaMockCommand(f"pgrep -af 'elasticConfig'", aRc=0,
                        aStdout=_list_out_proc),
                ],
            ],
        }

        self.mPrepareMockCommands(_cmds)

        _ebox = self.mGetClubox()
        for _dom0, _domU in _ebox.mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                self.assertEqual(
                    [_list_out_proc.strip()], node_list_process(_node, "elasticConfig"))

    def test_kill_proc_tree(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on utils.kill_proc_tree")

        coptions = get_gcontext().mGetConfigOptions()
        configs = {'kill_proc_tree':None,'terminate_workers_having_defunct_child':None,'agent_delegation_enabled':None}
        for config in configs.keys():
            if config in list(coptions.keys()):
                configs[config] = coptions.get(config)

        get_gcontext().mSetConfigOption('kill_proc_tree',"False")
        self.assertEqual(kill_proc_tree(None), [])
        get_gcontext().mSetConfigOption('kill_proc_tree',"True")

        get_gcontext().mSetConfigOption('terminate_workers_having_defunct_child',"True")
        with patch('psutil.Process', return_value=MockProcess()),\
             patch('psutil.pid_exists', return_value=True):
             self.assertEqual(kill_proc_tree(987)[0], psutil.Process().pid)

        get_gcontext().mSetConfigOption('terminate_workers_having_defunct_child',"False")
        get_gcontext().mSetConfigOption('agent_delegation_enabled',"False")
        with patch('psutil.Process', return_value=MockProcess()),\
             patch('psutil.pid_exists', return_value=True):
             self.assertEqual(len(kill_proc_tree(987)), 0)

        with patch('psutil.Process', return_value=MockProcess()),\
             patch('psutil.pid_exists', side_effect=[psutil.NoSuchProcess(1234, name="None", msg="Process doesn't exist."), psutil.AccessDenied(5678, name="SuperProcess", msg="Access to process denied"), Exception("A Generic exception")]):
             self.assertEqual(len(kill_proc_tree(987)), 0)
             self.assertEqual(len(kill_proc_tree(987)), 0)
             self.assertEqual(len(kill_proc_tree(987)), 0)

        for config in configs.keys():
            if configs.get(config) is not None:
                get_gcontext().mSetConfigOption(config, configs.get(config))

        ebLogInfo("Unit test on utils.kill_proc_tree completed successfully.")

if __name__ == '__main__':
    unittest.main()
