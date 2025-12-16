"""
 Copyright (c) 2020, 2025, Oracle and/or its affiliates.

NAME:
    clueiptablesroce.py - Exacloud RoCE Libvirt iptables configuration logic, specific to ExaBM OCI

FUNCTION:
    Setup Iptables using KVM libvirt.

NOTE:
    Ip tables configuration using virsh commands.
    The whole functionality provided by this class relies on the use of virsh dumpxml to grab kvm resource schemas.
    Network interfaces are referenced by using their aliases. Those aliases may vary according to the way the schemas are accessed.
    The name of the aliases when virsh dumpxml is used will not match what you would see through virsh edit commands.
    Based on the current kvm schemas used to bring up new vms the aliases (when accessed via virsh dumpxml) are: net0 and net1
    for admin and backup interfaces respectively

    The edition mechanism used to modify kvm resources works by dumping xml resources on Dom0s, schemas are then copied to DomU, where 
    they are processed and then copied back to Dom0. Once they are available on Dom0s, they are finally used to define/redefine kvm resources. 
    In order to avoid file names collisions, the linux mktemp command is used.

History:

    MODIFIED   (MM/DD/YY)
    mpedapro 11/20/25 - Enh::38602758 dcsagent nft rules are not required for
                        sriov enabled clusters
    scoral   01/14/25 - Bug 37102810: Support duplicate "bridge filter FORWARD"
                        jump rules deletion.
    joysjose 08/30/24 - Bug 36731935 : Make sure all NFTables are created in
                        the dom0s during Create Service and Add Compute
    scoral   06/07/24 - 36315105: Detect VLAN tag for each DomU.
    jesandov 10/16/23 - 35729701: Support of OL7 + OL8
    ririgoye 09/01/23 - Bug 35769896 - PROTECT YIELD KEYWORDS WITH TRY-EXCEPT
                        BLOCKS
    scoral   08/01/23 - 35654846: Make sure DomU is fully rebooted after
                        applying the network filters in OL7.
    scoral   06/05/23 - 35435421: Implemented mSetNfTablesExaBM to separate
                        dynamic NFTables setup from mSetupSecurityRulesExaBM.
    scoral   05/04/23 - Bug 35298579: Remove dynamic iptables rules from the
                        static rules file.
                        Move the temporary iptables rules setup to CreateVM.
    scoral   04/17/23 - Bug 35298579: Remove the libvirt network filters
                        dynamic rules from the static rules file.
    scoral   04/14/23 - Bug 35177571 - Use bridge family instead of ip
                        family for VM NFTables rules in OL8 envs.
    naps     01/13/23 - Bug 34957824 - change vm reboot logic while setting iptables.
    hnvenkat 12/12/22 - Enh 34886532: Allow all ingress/egress in ADBD
    scoral   10/26/22 - Enh 34529500: Refactored _mGetInterfacesAlias to
                        include the aliases to the interfaces if missing.
    scoral   10/20/22 - XbranchMerge scoral_bug-34701313 from st_ecs_22.3.1.0.0
    scoral   10/18/22 - Bug 34701313: Revert changes from Enh 33323287
    aararora 04/06/22 - Bug 34004534: Bandit issue fix.
    naps     03/06/22 - remove virsh dependency layer.
    ffrrodri 11/05/21 - Bug 33537143: Changed path for ADBD-template.tpl
    ffrrodri 10/22/21 - Enh 33435354: Remove rule to allow all egress in backup
                        net
    ffrrodri 09/29/21 - Enh 33323287: Added a function to drop iptable rule
                        postrouting masquerade for exacc envs.
    ffrrodri 10/07/21 - Bug 33229330: Added functionality to validate if
                        vnet100 and vnet101 are in the correct order or flipped
                        in bridges.
    ffrrodri 09/30/21 - Enh 33418458 - ADBD: ADD IPTABLES VALIDATION FOR X9M
    ffrrodri 07/15/21 - Enh 32992719: Add rule to modify all egress in Dom0
    scoral   11/13/20 - Implemented support for iptables configuration from
                        ECRA payload.
    jimillan 04/15/20 - Creation
"""

import json
import re
import time
import tempfile
import subprocess
from subprocess import PIPE
import xml.etree.cElementTree as etree
from typing import Mapping, Sequence, Dict
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn
from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.network.NfTables import NfTables
from exabox.ovm.clujumboframes import cluctrlGetDom0Bridges
from exabox.ovm.cludomufilesystems import shutdown_domu, start_domu, check_user_space_ready
from exabox.ovm.vmcontrol import exaBoxOVMCtrl, ebVgLifeCycle
from exabox.utils.node import connect_to_host, node_exec_cmd_check
from exabox.exakms.ExaKmsEntry import ExaKmsHostType
from exabox.ovm.cluacceleratednetwork import ebCluAcceleratedNetwork


EB_IPTABLES_ATP_IMPLICIT_RULES = {
    'atp': {
        'whitelist': {
            'client': {
                'protocol': {
                    'all': [
                        '@@out',
                        '@@in'
                    ]
                }
            },
            'backup': {
                'protocol': {
                    'all': [
                        '@@in',
                        '@@out'
                    ]
                }
            }
        }
    }
}

class ebIpTablesRoCE(object):

    @staticmethod
    def mExistsNetFilter(aDom0: str, aNetFilterName: str) -> bool:
        """
        Checks if a network filter named: aNetFilterName exists in a given Dom0

        Parameters:
        aDom0(str): A Dom0 FQDN
        aNetFilterName(str): A libvirt filter name

        Returns:
        bool:Whether or not the filter exists

        """
        ebLogInfo("*** Checking if kvm network filter:{0} exists ***".format(aNetFilterName))
        
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)

        ebLogInfo("*** Checking if filter already exist ***")

        _cmd = "virsh nwfilter-list | awk '{{ print $2 }}' | grep -c {0} || true".format(aNetFilterName)
        _fin, _out, _err = _node.mExecuteCmd(_cmd)
        _rc = _node.mGetCmdExitStatus()
        if _rc != 0:
            _messages = "\n".join(_out.readlines())+"\n".join(_err.readlines())
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0114, 0xA, "Error while checking if network filter:{0} exists.\n{1}".format(aNetFilterName,_messages))

        _out = _out.readlines()[0].strip()
        _node.mDisconnect()

        return int(_out) > 0

    @staticmethod
    def mCreateNetFilter(aDom0: str, aNetFilterName: str):
        """
        Creates a network filter named: aNetFilterName in a given Dom0

        Parameters:
        aDom0(str): A Dom0 FQDN
        aNetFilterName(str): A libvirt filter name

        Returns:
        None:No specific value is returned

        """

        ebLogInfo("*** Creating kvm network filter:{0} ***".format(aNetFilterName))

        if ebIpTablesRoCE.mExistsNetFilter(aDom0,aNetFilterName):
            raise ExacloudRuntimeError(0x0114, 0xA, "Error while checking if network filter:{0} exists".format(aNetFilterName))
        
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)

        ebLogInfo("*** Creating network filter template on dom0:{0} ***".format(aDom0))
        ebLogInfo("*** Creating a temporary file to hold the network filter template ***")

        _cmd = "mktemp --suffix=.xml"
        _fin, _out, _err = _node.mExecuteCmd(_cmd)
        _rc = _node.mGetCmdExitStatus()
        if _rc != 0:
            _messages = "\n".join(_out.readlines())+"\n".join(_err.readlines())
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0114, 0xA, "Error while creating temporary file in node:{0}\n{1}".format(aDom0,_messages))
        _temp_file = _out.readlines()[0].strip()

        ebLogInfo("*** Writing template to file:{0} ***".format(_temp_file))
        
        _cmd = "echo '<filter name=\"{0}\"/>' > {1}".format(aNetFilterName,_temp_file)
        _fin, _out, _err = _node.mExecuteCmd(_cmd)
        _rc = _node.mGetCmdExitStatus()
        if _rc != 0:
            _messages = "\n".join(_out.readlines())+"\n".join(_err.readlines())
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0114, 0xA, "Error while writing to temporary file:{0} in node:{1}\n{2}".format(_temp_file,aDom0,_messages))

        ebLogInfo("*** Defining network filter with virsh ***")
        _cmd = "virsh nwfilter-define {0}".format(_temp_file)
        _fin, _out, _err = _node.mExecuteCmd(_cmd)
        _rc = _node.mGetCmdExitStatus()
        if _rc != 0:
            _messages = "\n".join(_out.readlines())+"\n".join(_err.readlines())
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0114, 0xA, "Error while defining network filter:\n{0}".format(_messages))
   
        _node.mDisconnect()

    @staticmethod
    def mRemoveNetFilter(aDom0: str, aNetFilterName: str):
        """
        Removes an existing network filter from a given Dom0

        Parameters:
        aDom0(str): A Dom0 FQDN
        aNetFilterName(str): A libvirt filter name

        Returns:
        None:No specific value is returned

        """

        ebLogInfo("*** Removing network filter:{0} ***".format(aNetFilterName))
       
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)

        _cmd = "virsh nwfilter-undefine {0}".format(aNetFilterName)
        _fin, _out, _err = _node.mExecuteCmd(_cmd)
        _rc = _node.mGetCmdExitStatus()
        if _rc != 0:
            _messages = "\n".join(_out.readlines())+"\n".join(_err.readlines())
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0114, 0xA, "Error while undefining network filter:{0} on dom0:{1}\n{2}".format(aNetFilterName,aDom0,_messages))

        _node.mDisconnect()

    @staticmethod
    def mAddNetFilterToVMSchema(aVmSchemaFile: str, aInterfaceAlias: str, aNetFilterName: str):
        """
        Adds a reference to an existing network filter in an existing VM network bridge schema file
        located in the machine where excloud is running

        Parameters:
        aVmSchemaFile(str): A local file system path to a kvm vm schema file.
        aInterfaceAlias(str): A network interface alias name as defined by kvm libvirtd.
                              Alias names vary according to how the schema is accessed. If the schema is accessed via
                              virsh edit the name will not match what you would get when using virsh dumpxml.
                              The whole functionality provided by this class relies on the virsh dumpxml functionality where
                              net0 and net1 aliases are used for admin and backup networks respectively.
                              This of course depends on the underlying xml kvm schema used to bring up the vms.
        aNetFilterName(str): A libvirt filter name

        Returns:
        None:No specific value is returned

        """

        ebLogInfo("*** Adding network filter:{0} to virtual machine kvm schema:{1} interface:{2} ***".format(aNetFilterName,aVmSchemaFile,aInterfaceAlias))

        if not aVmSchemaFile:
            raise ExacloudRuntimeError(0x0114, 0xA, "Unable to get VM schema file:{0} ***".format(aVmSchemaFile))

        ebLogInfo("*** Kvm resource schema stored at:{0}".format(aVmSchemaFile))

        try:
            _xml_file = etree.parse(aVmSchemaFile)
        except etree.ParseError: 
            raise ExacloudRuntimeError(0x0114, 0xA,"Error while parsing local copy of virtual machine schema file:{0} ***".format(aVmSchemaFile))

        ebLogInfo("*** Getting list of devices from kvm resource xml schema file:{0} ***".format(aVmSchemaFile))
        _xml_root = _xml_file.getroot()
        _devices = _xml_root.find("devices")
        _found_interface = False

        if len(_devices) > 0:
            _interfaces = _devices.findall("interface")
            if len(_interfaces) > 0:
                for _interface in _interfaces:
                    if _interface.attrib["type"] == "bridge":
                        _net_filters = _interface.findall("filterref")
                        
                        _interface_alias = _interface.find("alias")

                        if _interface_alias == None:
                            continue

                        if _interface_alias.attrib["name"] == aInterfaceAlias:
                            _found_interface = True

                            if _net_filters:
                                ebLogError("*** Only one network filter per interfaces is allowed by kvm/qemu ***")
                                raise ExacloudRuntimeError(0x0114, 0xA,"Error while defining network filter for {0}".format(aInterfaceAlias))


                            ebLogInfo("*** Adding filter:{0} to virtual machine schema ***".format(aNetFilterName))
                            
                            _network_filter = etree.SubElement(_interface,"filterref")
                            _network_filter.attrib["filter"] = aNetFilterName
                            _xml_file.write(aVmSchemaFile)
                if not _found_interface:
                    raise ExacloudRuntimeError(0x0114, 0xA,"Interface alias:{0} not found in virtual machine schema".format(aInterfaceAlias))
            else:
                raise ExacloudRuntimeError(0x0114, 0xA,"No interfaces defintion found in virtual  machine schema")
        else:
            raise ExacloudRuntimeError(0x0114, 0xA,"No devices found in virtual machine schema")

    @staticmethod
    def mRemoveNetFilterFromVMSchema(aVmSchemaFile: str, aInterfaceAlias: str):
        """
        Removes a reference to an existing network filter in an existing VM network bridge schema file
        located in the machine where excloud is running

        Parameters:
        aVmSchemaFile(str): A local file system path to a kvm vm schema file.
        aInterfaceAlias(str): A network interface alias name as defined by kvm libvirtd.
                              Alias names vary according to how the schema is accessed. If the schema is accessed via
                              virsh edit the name will not match what you would get when using virsh dumpxml.
                              The whole functionality provided by this class relies on the virsh dumpxml functionality where
                              net0 and net1 aliases are used for admin and backup networks respectively.
                              This of course depends on the underlying xml kvm schema used to bring up the vms.
        Returns:
        None:No specific value is returned

        """

        ebLogInfo("*** Removing network filters from virtual machine kvm schema:{0} interface:{1} ***".format(aVmSchemaFile,aInterfaceAlias))

        if not aVmSchemaFile:
            raise ExacloudRuntimeError(0x0114, 0xA, "Unable to get VM schema file:{0} ***".format(aVmSchemaFile))

        ebLogInfo("*** Kvm resource schema stored at:{0}".format(aVmSchemaFile))

        try:
            _xml_file = etree.parse(aVmSchemaFile)
        except etree.ParseError: 
            raise ExacloudRuntimeError(0x0114, 0xA,"Error while parsing local copy of virtual machine schema file:{0} ***".format(aVmSchemaFile))

        ebLogInfo("*** Getting list of devices from kvm resource xml schema file:{0} ***".format(aVmSchemaFile))
        _xml_root = _xml_file.getroot()
        _devices = _xml_root.find("devices")
        _found_interface = False

        if len(_devices) > 0:
            _interfaces = _devices.findall("interface")
            if len(_interfaces) > 0:
                for _interface in _interfaces:
                    if _interface.attrib["type"] == "bridge":
                        _net_filters = _interface.findall("filterref")
                        
                        _interface_alias = _interface.find("alias")

                        if _interface_alias == None:
                            continue

                        if _interface_alias.attrib["name"] == aInterfaceAlias:
                            _found_interface = True

                            if not _net_filters:
                                ebLogError("*** No network filter found in virtual machine schema ***")
                                ebLogError("*** It could be possible that the filter exists at the virsh level on Dom0, but it is no longer part of the DomU schema, in which \
case a manual removal of the filter must be performed on Dom0 ***")
                                return

                            for _filter in _net_filters:
                                ebLogInfo("*** Removing netfilter:{0} from virtual machine schema ***".format(_filter.attrib["filter"]))
                                _interface.remove(_filter)

                            _xml_file.write(aVmSchemaFile)
                if not _found_interface:
                    raise ExacloudRuntimeError(0x0114, 0xA,"Interface alias:{0} not found in virtual machine schema".format(aInterfaceAlias))
            else:
                raise ExacloudRuntimeError(0x0114, 0xA,"No interfaces defintion found in virtual  machine schema")
        else:
            raise ExacloudRuntimeError(0x0114, 0xA,"No devices found in virtual machine schema")
    
    @staticmethod
    def mInsertRemoveRulesFromNetFilterSchema(aNetFilterSchemaFile: str, aInsert: bool, *aRulesDict: Sequence[dict]):
        """
        Inserts or removes a sequence of network rules (iptables like rule)
        from an existing network filter schema file located in the machine
        where excloud is running.

        Parameters:
        aNetFilterSchemaFile(str): A local file system path to a kvm network filter schema file.
        aInsert(bool): Specifies if the rules are either going to be inserted or removed.
        aRulesDict(Sequence): A sequence of dictionaries containing all the elemantes required to setup a new network rule:
            Format: 
            Main(dict): {"protocol":"str","rule":dict,"attr":dict}
            Rule(dict): {"str":"str","str":"str",...}
            Attr(dict): {"str":"str","str":"str:,...}

            Rule and attr dictionaries can dynamically received any supported kvm values as described here: 
            https://libvirt.org/formatnwfilter.html#nwfconceptschains
            This allow a dynamic configuration that can add as many rule attributes, as well as as any inner attributes inside a rule:
            e.g.
            _rule = {"action":"accept","direction":"in"}
            _port = "7060"
            _protocol = "tcp"
            _attr = {"srcipaddr":"169.254.169.254","srcipmask":"32","dstportstart":_port}
            _net_rules = {"protocol":_protocol,"rule":_rule,"attr":_attr}

        Returns:
        None:No specific value is returned
        """

        try:
            _xml_file = etree.parse(aNetFilterSchemaFile)
        except etree.ParseError: 
            raise ExacloudRuntimeError(0x0114, 0xA,"Error while parsing local copy of virtual machine schema file:{0} ***".format(aNetFilterSchemaFile))

        _xml_root = _xml_file.getroot()
        _rules = _xml_root.findall("rule")
        _changed = False
        
        for aRuleDict in aRulesDict:
            _rule_dict = aRuleDict["rule"]
            _attr_dict = aRuleDict["attr"]
            _protocol = aRuleDict["protocol"]

            for _rule in _rules:
                if _rule_dict["action"] == _rule.get("action") and _rule_dict["direction"] == _rule.get("direction"):
                    _protocol_element = _rule.find(_protocol)
                    if _protocol_element != None and _protocol_element.attrib == _attr_dict:
                        if aInsert:
                            #ebLogInfo("*** Skipping rule:{0} as it already exists in network filter ***".format(aRuleDict))
                            pass
                        else:
                            #ebLogInfo("*** Removing ip table rule:{0} ***".format(aRuleDict))
                            _changed = True
                            _xml_root.remove(_rule)
                        break
            else:
                if aInsert:
                    #ebLogInfo("*** Setting rule:{0} ***".format(aRuleDict))
                    _changed = True
                    _rule_element = etree.SubElement(_xml_root, "rule")
                    for rule_k, rule_v in _rule_dict.items():
                        _rule_element.set(rule_k, rule_v)

                    _protocol_element = etree.SubElement(_rule_element, _protocol)
                    for attr_k,attr_v in _attr_dict.items():
                        _protocol_element.set(attr_k,attr_v)
                else:
                    #ebLogInfo("*** Rule:{0} not found in filter ***".format(aRuleDict))
                    pass
        
        if _changed:
            _xml_file.write(aNetFilterSchemaFile)

    @staticmethod
    def mAddRulesToNetFilterSchema(aNetFilterSchemaFile: str, *aRulesDict: Sequence[dict]):
        """
        Inserts a sequence of network rules (iptables like rule)
        from an existing network filter schema file located in the machine
        where excloud is running.

        Parameters:
        aNetFilterSchemaFile(str): A local file system path to a kvm network filter schema file.
        aRulesDict(Sequence): A sequence of dictionaries containing all the elemantes required to setup a new network rule:
            The format is mentioned at the mInsertRemoveRulesFromNetFilterSchema documentation.

        Returns:
        None:No specific value is returned
        """
        ebIpTablesRoCE.mInsertRemoveRulesFromNetFilterSchema(aNetFilterSchemaFile, True, *aRulesDict)

    @staticmethod
    def mRemoveRulesFromNetFilterSchema(aNetFilterSchemaFile: str, *aRulesDict: Sequence[dict]):
        """
        Removes a sequence of network rules (iptables like rule)
        from an existing network filter schema file located in the machine
        where excloud is running.

        Parameters:
        aNetFilterSchemaFile(str): A local file system path to a kvm network filter schema file.
        aRulesDict(Sequence): A sequence of dictionaries containing all the elemantes required to setup a new network rule:
            The format is mentioned at the mInsertRemoveRulesFromNetFilterSchema documentation.

        Returns:
        None:No specific value is returned
        """
        ebIpTablesRoCE.mInsertRemoveRulesFromNetFilterSchema(aNetFilterSchemaFile, False, *aRulesDict)

    @staticmethod
    def mRebootVMViaVirsh(aExaBoxCluCtrlObj: str, aDomU: str, aDom0: str):
        """
        Reboots a DomU via vm_maker from its Dom0.

        Parameters:
        aExaBoxCluCtrlObj(exaBoxCluCtrl): A exaBoxCluCtrl instance
        aDomU(str): A DomU FQDN
        aDom0(str): A Dom0 FQDN

        Returns:
        None: No specific value is returned

        """

        ebox = aExaBoxCluCtrlObj
        _dom0 = aDom0
        _domU = aDomU
        with connect_to_host(_dom0, get_gcontext()) as _node:
        
            _vmhandle = ebVgLifeCycle()
            _vmhandle.mSetOVMCtrl(aCtx=get_gcontext(), aNode=_node)
            _cmd = 'shutdown'
            _rc = _vmhandle.mDispatchEvent(_cmd, None, aVMId=_domU, aCluCtrlObj=ebox)
            if _rc not in [0, 0x0411, 0x0454]:
                ebLogError('*** FATAL mRebootVMViaVirsh:: vmid: %s - Could not be shut down' % (_domU))
                raise ExacloudRuntimeError(0x0403, 0xA, 'VM was not able to shutdown')

            _rc = ebox.mRestartVM(_domU, aVMHandle=_vmhandle)
            if _rc != 0:
                ebLogError('*** FATAL mRebootVMViaVirsh:: vmid: %s - Could not be started' % (_domU))
                raise ExacloudRuntimeError(0x0411, 0xA, 'VM was not able to start')

    @staticmethod
    def mValidateIptables(aDom0: str):
        """
        Validates iptables rules setted in ADBD environments using misc/resources/network/iptables/ADBD-template.tpl file

        Parameters:
        aDom0(str): A Dom0 FQDN

        Returns:
        _result(boolean): Return true if completes successfully validation

        """

        # Open file with iptables ADBD template to validate
        fname = 'misc/resources/network/iptables/ADBD-template.tpl'
        try:
            with open(fname, 'r') as f:
                _iprules = f.readlines()
        except Exception as e:
            _msg = f"Failed to load file {fname}: {e}"
            ebLogError(_msg)
            raise ExacloudRuntimeError(0x0750, 0xA, _msg) from e

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aDom0)

            _cmd = "/sbin/iptables -S"
            _i, _o, _e = _node.mExecuteCmd(_cmd)
            _out = _o.readlines()
            _current_rules = [_curr.strip() for _curr in _out]
            for _iprule in _iprules:
                if _iprule.strip() not in _current_rules:
                    _msg = f"IPrules validation fails, rule {_iprule} not found in {aDom0}"
                    ebLogError(_msg)
                    raise ExacloudRuntimeError(0x0750, 0xA, _msg)
            ebLogInfo(f"*** IPrules validation succeed for {aDom0} ***")
        finally:
            _node.mDisconnect()

        return True

    @staticmethod
    def mGetKVMSchemaFromDom0(aDom0: str, aSchemaName: str, aSchemaType: str="") -> Dict[str, str]:
        """
        Grabs a KVM resource schema from a given Dom0.

        Parameters:
        aDom0(str): A Dom0 FQDN
        aSchemaName(str): A kvm resource schema name
        aSchemaType(str): A kvm schema type
                          The type might be required for non vm resources

        Returns:
        dict: Dictionary containing two file paths: a remote path where the file is stored on Dom0 and a local path
              which represents the local file path where the file will be available

        """
        ebLogInfo("*** Getting kvm schema:{0} from dom0:{1}".format(aSchemaName,aDom0))
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)

        ebLogInfo("*** Creating temporary file to store kvm schema:{0} ***".format(aSchemaName))

        _cmd = "mktemp --suffix=.xml"
        _fin, _out, _err = _node.mExecuteCmd(_cmd)
        _rc = _node.mGetCmdExitStatus()
        if _rc != 0:
            _messages = "\n".join(_out.readlines())+"\n".join(_err.readlines())
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0114, 0xA, "Error while creating temporary file in node:{0}\n{1}".format(aDom0,_messages))
        _temp_file = _out.readlines()[0].strip()

        ebLogInfo("*** Dumping kvm schema:{0} to file:{1} ***".format(aSchemaName,_temp_file))

        if aSchemaType:
            aSchemaType+="-"

        _cmd = "virsh {0}dumpxml {1} > {2}".format(aSchemaType,aSchemaName,_temp_file)
        _fin, _out, _err = _node.mExecuteCmd(_cmd)
        _rc = _node.mGetCmdExitStatus()
        if _rc != 0:
            _out_lines = _out.readlines()
            _messages = "\n".join(_out_lines)+"\n".join(_err.readlines())
            _node.mDisconnect()
            # If the resource is not found virsh returns and empty list []
            if len(_out_lines) == 0:
                ebLogError("*** Resource:{0} not found in kvm ***".format(aSchemaName))

            raise ExacloudRuntimeError(0x0114, 0xA, "Error while dumping kvm schema:{0} to file via virsh on node:{1}\n{2}".format(aSchemaName,aDom0,_messages))

        ebLogInfo("*** Creating temporary file:{0} locally to store kvm schema ***".format(_temp_file))

        try:
            _temp_file_local_obj = tempfile.NamedTemporaryFile(suffix='.xml', delete=False)
            _temp_file_local = _temp_file_local_obj.name
        except Exception as ex:
            _messages = str(ex)
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0114, 0xA, "Error while creating local temporary file from node:{0} to store kvm schema\n{1}".format(aDom0,_messages))
        
        ebLogInfo("*** Copying kvm xml schema to local file:{0} ***".format(_temp_file_local)) 

        try:
            _node.mCopy2Local(_temp_file,_temp_file_local)
        except Exception:
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0114, 0xA, "Error fetching file:{0} from node:{1} to local file:{2} ***".format(_temp_file,aDom0,_temp_file_local))

        _node.mDisconnect()

        return {"remote":_temp_file,"local":_temp_file_local}

    @staticmethod
    def mDefineKVMResourceInDom0(aDom0: str, aLocalSchemaFile: str, aRemoteSchemaFile: str, aSchemaType: str=""):
        """
        Defines a KVM resource on a Dom0 using a kvm schema file available in the Dom0.

        The define mechanism relies on the process of grabing kvm schemas to the exacloud machine, process them locally
        and copy the edited files to the Dom0. Once the files are copied back to the Dom0, kvm resources are defined/redefined 
        using that specific file. Specific files for this operations are created by using the mktemp linux command. 

        Parameters:
        aDom0(str): A Dom0 FQDN
        aLocalSchemaFile(str): A local file system path to a kvm schema file
        aRemoteSchemaFile(str): A Dom0 file system path where the local schema will be copied to.

        Returns:
        None: No specific value is returned

        """
       
        ebLogInfo("*** Applying schema changes on dom0:{0}, local schema file:{1} ***".format(aDom0,aLocalSchemaFile))
        
        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost=aDom0)

        ebLogInfo("*** Copying local schema file:{0} to dom0:{1},file:{2}".format(aLocalSchemaFile,aDom0,aRemoteSchemaFile))

        _node.mCopyFile(aLocalSchemaFile,aRemoteSchemaFile)

        _rc = _node.mGetCmdExitStatus()
  
        if _rc != 0:
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0114, 0xA, "Error while copying file:{0} to dom0:{1}".format(aLocalSchemaFile,aDom0)) 


        ebLogInfo("*** Defining kvm resource via virsh ***")
        
        if aSchemaType:
            aSchemaType+="-"

        _cmd = "virsh {0}define {1}".format(aSchemaType,aRemoteSchemaFile)
        _fin, _out, _err = _node.mExecuteCmd(_cmd)
        _rc = _node.mGetCmdExitStatus()

        if _rc != 0:
            _messages = "\n".join(_out.readlines())+"\n".join(_err.readlines())
            _node.mDisconnect()
            raise ExacloudRuntimeError(0x0114, 0xA, "Error while defining resources via virsh command:\n{0}".format(_messages)) 

        ebLogInfo("*** Successfully defined resources:{0} ***".format(_out.readlines()[0].strip()))

        _node.mDisconnect()


    @staticmethod
    def mGetNFTRuleHandle(aNode, aRuleArgs):

        _, _o, _ = aNode.mExecuteCmd("/usr/sbin/nft -a list ruleset")
        _ruleWithHandler = None
        _lines = _o.readlines()

        for _line in _lines:

            _ruleFound = True

            for _args in aRuleArgs:
                if _args not in _line:
                    _ruleFound = False

            if _ruleFound:
                _ruleWithHandler = _line
                break

        if _ruleWithHandler:

            _handlerId = re.search("# handle (.*)", _ruleWithHandler).group(1)
            return _handlerId

        return None

    @staticmethod
    def mCommitIPTables(aNode):

        _cmd = "/bin/cp /etc/sysconfig/iptables /etc/sysconfig/iptables.`date +%y.%j.%H.%m.%s`"
        aNode.mExecuteCmdLog(_cmd)

        _cmd = "/sbin/iptables-save > /etc/sysconfig/iptables"
        aNode.mExecuteCmdLog(_cmd)

        # Remove the libvirt network filters dynamic rules from the static rules file
        _cmd = "/bin/sed -i '/vnet/d' /etc/sysconfig/iptables"
        aNode.mExecuteCmdLog(_cmd)

    @staticmethod
    def mCommitNFTables(aNode):

        _cmd = "/bin/cp /etc/nftables/exadata.nft /etc/nftables/exadata.`date +%y.%j.%H.%m.%s`"
        aNode.mExecuteCmdLog(_cmd)

        _cmd = "/usr/sbin/nft list ruleset > /etc/nftables/exadata.nft"
        aNode.mExecuteCmdLog(_cmd)


    @staticmethod
    def mPrevmSetupNFTables(aExaBoxCluCtrlObj,append=True):

        ebox = aExaBoxCluCtrlObj

        for _dom0,_domu in ebox.mReturnDom0DomUPair():
            _vlan_tag_list = []
            _rules_cmd = []

            for _network in ebox.mGetMachines().mGetMachineConfig(_domu).mGetMacNetworks():
                _network_config = ebox.mGetNetworks().mGetNetworkConfig(_network)
                if _network_config.mGetNetType() in [ 'client','backup']:
                    _vlan_tag_list.append(_network_config.mGetNetVlanId())

            _node = exaBoxNode(get_gcontext())
            try:
                _node.mConnect(aHost=_dom0)
                _rules_cmds = []

                for _vlan_tag in _vlan_tag_list:

                    _bridge_suffix = ""
                    if _vlan_tag != "UNDEFINED":
                        _bridge_suffix = '.' + _vlan_tag

                    _ruleArgs = ['oifname', f'"vmbondeth0{_bridge_suffix}"', 'counter', 'accept']
                    _handle = ebIpTablesRoCE.mGetNFTRuleHandle(_node, _ruleArgs)

                    if append: # add rule

                        if not _handle:
                            _rule = "nft add rule ip filter FORWARD"
                            _rule += " " + " ".join(_ruleArgs)
                            _rules_cmds.append(_rule)
                        else:
                            ebLogWarn(f"Rule '{_ruleArgs}' already with handle: {_handle}")

                    else: # delete rule

                        if _handle:
                            _rule = "nft delete rule ip filter FORWARD"
                            _rule += f" handle {_handle}"
                            _rules_cmds.append(_rule)
                        else:
                            ebLogWarn(f"Rule '{_ruleArgs}' not exists")

                for _cmd in _rules_cmds:

                    _, _out, _err = _node.mExecuteCmd(_cmd)
                    _rc = _node.mGetCmdExitStatus()

                    if _rc != 0:
                        _messages = "\n".join(_out.readlines())+"\n".join(_err.readlines())
                        _node.mDisconnect()
                        raise ExacloudRuntimeError(0x0114, 0xA, "Error while applying nftables rule:{0} in node:{1}\n{2}".format(_cmd, _dom0,_messages))

                ebIpTablesRoCE.mCommitNFTables(_node)

            finally:
                _node.mDisconnect()


    @staticmethod
    def mPrevmSetupIptables(aExaBoxCluCtrlObj,append=True, aDom0s=[]):
        """
        Sets or removes ip tables required for KVM create/delete service request
        This has to do with kernel modules:br_netfilter xt_phydev that when loaded can cause
        create service requests to hung.

        Parameters:
        aExaBoxCluCtrlObj(exaBoxCluCtrl): A exaBoxCluCtrl instance
        append (bool): Defines if the rules should be appended or deleted. Default:True
        
        Returns:
        None: No specific value is returned
        """

        def _exist_rule(aDom0,aRule):
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=aDom0)

            _rule = aRule
            _rule = _rule.replace("-D","-A")
            _rule = _rule.replace("iptables ","")
            _rule = _rule.replace("-","\\-")
            _cmd = "iptables -S | grep -c '{0}'".format(_rule)

            ebLogInfo("***** Running command:{}".format(_cmd))
            _fin, _out, _err = _node.mExecuteCmd(_cmd)

            _rc = _node.mGetCmdExitStatus()

            if _rc > 1:
                raise ExacloudRuntimeError(0x0114, 0xA, "Error while checking if iptable rule:{0} exists in Dom0:{1}".format(_rule,aDom0))

            _out = _out.readlines()[0].strip()

            _count = 0

            try:
                _count = int(_out)
                if _count == 0:
                    # 1 is return in count, because whne a rule must be added and it does not exist
                    # The loop below should iterate once time to add the desired rule
                    return {"exist":False,"count":1}

            except ValueError:
                 _node.mDisconnect()
                 raise ExacloudRuntimeError(0x0114, 0xA, "Error while checking if iptable rule:{0} exists in Dom0:{1}".format(_rule,aDom0))
            _node.mDisconnect()

            return {"exist":True,"count":_count}

        ebox = aExaBoxCluCtrlObj

        for _dom0, _domu in ebox.mReturnDom0DomUPair():
            if aDom0s and _dom0 not in aDom0s:
                continue

            _vlan_tag_list = []
            _iptables_cmd = []

            for _network in ebox.mGetMachines().mGetMachineConfig(_domu).mGetMacNetworks():
                _network_config = ebox.mGetNetworks().mGetNetworkConfig(_network)
                if _network_config.mGetNetType() in [ 'client','backup']:
                    _vlan_tag_list.append(_network_config.mGetNetVlanId())

            for _vlan_tag in _vlan_tag_list:
                _bridge_suffix = ""
                _action = "-A"

                if append == False:
                    _action = "-D"

                if _vlan_tag != "UNDEFINED":
                        _bridge_suffix = '.' + _vlan_tag

                _iptables_cmd.append('iptables {} FORWARD -o vmbondeth0{} -j ACCEPT'.format(_action,_bridge_suffix))

            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost=_dom0)


            for _cmd in _iptables_cmd:
                ebLogInfo("*** Checking if iptables rule:{0} exists in dom0:{1} ***".format(_cmd,_dom0))

                _exist_rule_dict = _exist_rule(_dom0,_cmd)
                _exist = _exist_rule_dict["exist"]
                _count = _exist_rule_dict["count"]

                _setup_rules = True

                if append and _exist:
                    ebLogInfo("*** iptables rule:{0} already exists in dom0. Skipping setup ***".format(_cmd))
                    _setup_rules = False

                if append == False and _exist == False:
                    ebLogInfo("*** iptables rule:{0} to delete does not exist. Skipping setup ***".format(_cmd))
                    _setup_rules = False

                ebLogDebug("*** Applying iptable rules. Rule:{}. Append rule:{}. Rule found:{}".format(_cmd,append,_exist))

                if _setup_rules:
                    #This is a loop to take into account the possibility of finding left over iptables rules form a past failed create service
                    for _i in range(_count):
                        ebLogInfo("*** Applying iptables rule:{0} in dom0:{1} ***".format(_cmd,_dom0))
                        _fin, _out, _err = _node.mExecuteCmd(_cmd)
                        _rc = _node.mGetCmdExitStatus()

                        if _rc != 0:
                            _messages = "\n".join(_out.readlines())+"\n".join(_err.readlines())
                            _node.mDisconnect()
                            raise ExacloudRuntimeError(0x0114, 0xA, "Error while applying iptables rule:{0} in node:{1}\n{2}".format(_cmd,_dom0,_messages))

            ebIpTablesRoCE.mCommitIPTables(_node)
            _node.mDisconnect()

    @staticmethod
    def mReadIpTablesDictATPPayload(aJsonConf: dict, aInterfaceType: str) -> Sequence[dict]:
        """
        Parses the iptables from the ECRA Payload to a list of
        dictionaries representing the rules consumables by
        mAddRuleToNetFilterSchema.

        Parameters:
        aJsonConf(dict): A dictionary representing the ECRA Payload which
                         may contain the iptables rules at
                         ['atp']['whitelist']['client|backup']['protocol']
        aInterfaceType(str): Either 'client' or 'backup'

        Returns:
        generator: A generator of dictionaries representing the rules
                   consumables by mAddRuleToNetFilterSchema.
        """
        try:
            for protocol, rules in aJsonConf['atp']['whitelist'][aInterfaceType]['protocol'].items():
                for rule in rules:
                    ipaddr, port, direction = rule.split('@')
                    if '/' in ipaddr: # The subnet mask is included in the ip
                        ipaddr, ipmask = ipaddr.split('/')
                    else:
                        ipmask = '32'
                    _net_rule = {
                        'protocol': protocol,
                        'rule': {'action': 'accept', 'direction': direction, 'priority': '500'},
                        'attr': {}
                    }
                    if ipaddr:
                        if ipaddr[0] == 's':
                            _net_rule['attr']['srcipaddr'] = ipaddr[1:]
                            _net_rule['attr']['srcipmask'] = ipmask
                        else: # ipaddr[0] == 'd'
                            _net_rule['attr']['dstipaddr'] = ipaddr[1:]
                            _net_rule['attr']['dstipmask'] = ipmask
                    if port:
                        _net_rule['attr']['dstportstart'] = port
                    try:
                        yield _net_rule
                    except StopIteration:
                        return
                    
        except (KeyError, TypeError):
            #ebLogWarn("*** iptables rules for client interfaces not found in payload. ***")
            pass
    
    @staticmethod
    def mAlterATPIptables(aDom0: str, aDomU: str, aJsonConf: dict, aInsert: bool):
        """
        Add or removes iptables rules from a given payload to a certain Dom0.
        using virsh nwfilter-define.
        NOTE: The network filter must have been already defined at this point.
              So you should use this function only after mSetIpTablesExaBM.

        Parameters:
        aDom0(str): A Dom0 FQDN
        aDomU(str): A DomU FQDN
        aJsonConf(dict): A dictionary representing the ECRA Payload which
                         may contain the iptables rules at
                         ['atp']['whitelist']['client|backup']['protocol']
        aInsert(bool): Indicates weather to insert or remove the rules from
                       the payload to 
        """
        for _interface_alias, _interface_type in [('net0', 'client'), ('net1', 'backup')]:
            _environment = "exabm"
            _net_filter_name = "-".join([aDomU, _interface_alias, _environment])
            _nwfilter_xml_schemas_dict = ebIpTablesRoCE.mGetKVMSchemaFromDom0(aDom0, _net_filter_name, aSchemaType="nwfilter")
            
            _rules = ebIpTablesRoCE.mReadIpTablesDictATPPayload(aJsonConf, _interface_type)
            ebIpTablesRoCE.mInsertRemoveRulesFromNetFilterSchema(_nwfilter_xml_schemas_dict['local'], aInsert, *_rules)
            ebIpTablesRoCE.mDefineKVMResourceInDom0(aDom0, _nwfilter_xml_schemas_dict["local"], _nwfilter_xml_schemas_dict["remote"], aSchemaType="nwfilter")
    
    @staticmethod
    def mRemoveSSHIpTablesRules(aExaBoxCluCtrlObj):
        _rules_payload = { 'atp': { 'whitelist': { 'client': { 'protocol': { 'tcp': ['@22@in', '@22@out'] } } } } }
        for _dom0, _domu in aExaBoxCluCtrlObj.mReturnDom0DomUPair():
            ebIpTablesRoCE.mAlterATPIptables(_dom0, _domu, _rules_payload, False)

    @staticmethod
    def _mGetInterfacesAlias(
            aVmSchemaFile: str,
            aBridgeTypeMap: Mapping[str, str]) -> Mapping[str, str]:
        """
        It returns a map of the correct newtork aliases that correspond to the
        client and backup networks given a libvirt VM XML schema local file.
        If the aliases are not already in the XML, we will add a default net0
        alias for the client network and a net1 alias for the backup network
        and will overwrite the given file.

        For example:
        ebIpTablesRoCE._mGetInterfacesAlias(
            _schema_local_path,
            {
                "vmbondeth0.1": "client",
                "vmbondeth0.2": "backup"
            }
        ) == { "client": "net0", "backup": "net1" }

        Parameters:
        aVmSchemaFile(str): A libvirt VM XML schema local file path.
        aBridgeTypeMap(dict): A dictionary of the expected bridge names for
                              both client and backup networks.

        Returns:
        aInterfaceAliases(dict): A map of the networks aliases present in the
                                 given network filter.
        """
        _interfaces_alias_dict = {
            'client': 'net0',
            'backup': 'net1'
        }

        ebLogInfo("*** Retrieving network aliases from VM schema "
                  f"'{aVmSchemaFile}'. Bridges map: {aBridgeTypeMap} ***")

        try:
            _xml_file = etree.parse(aVmSchemaFile)
        except etree.ParseError:
            _msj = ("Error while parsing local copy of virtual machine schema "
                    f"file: {aVmSchemaFile}")
            raise ExacloudRuntimeError(0x0114, 0xA, _msj)

        _xml_root = _xml_file.getroot()
        _devices = _xml_root.find("devices")
        if not _devices:
            _msj = "No devices found in virtual machine schema"
            raise ExacloudRuntimeError(0x0114, 0xA, _msj)

        _interfaces = _devices.findall("interface")
        for _interface in _interfaces:
            if _interface.attrib["type"] != "bridge":
                continue

            _interface_source = _interface.find("source")
            if _interface_source is None:
                continue

            _interface_bridge = _interface_source.attrib["bridge"]
            if _interface_bridge not in aBridgeTypeMap:
                continue

            _interface_type = aBridgeTypeMap[_interface_bridge]
            _interface_alias = _interface.find("alias")
            if _interface_alias is None:
                _alias = _interfaces_alias_dict[_interface_type]
                ebLogWarn(f"*** Bridge {_interface_bridge} does not have an "
                          f"alias, we will add {_alias} ***")
                _interface_alias = etree.SubElement(_interface, "alias")
                _interface_alias.attrib["name"] = _alias
            else:
                _alias = _interface_alias.attrib["name"]
                ebLogInfo(f"*** Alias {_alias} found in bridge "
                          f"{_interface_bridge}")
                _interfaces_alias_dict[_interface_type] = _alias

        _xml_file.write(aVmSchemaFile)
        return _interfaces_alias_dict


    @staticmethod
    def mRemoveSecurityRulesExaBM(aExaBoxCluCtrlObj, aDom0s=[]):

        _nftDom0s = aExaBoxCluCtrlObj.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL8"])
        _iptDom0s = aExaBoxCluCtrlObj.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL7", "OL6"])

        _nftFilter = []
        _iptFilter = []

        # Filter dom0s in base of the list
        if aDom0s:
            for _dom0 in aDom0s:
                if _dom0 in _nftDom0s:
                    _nftFilter.append(_dom0)
                if _dom0 in _iptDom0s:
                    _iptFilter.append(_dom0)

        else:
            _nftFilter = _nftDom0s
            _iptFilter = _iptDom0s

        # Remove iptables
        if _iptFilter:
            if aExaBoxCluCtrlObj.mCheckConfigOption("iptables_backend", "legacy"):
                ebIpTablesRoCE.mRemoveIpTablesExaBM(aExaBoxCluCtrlObj, onDomUSchema=False, aDom0s=_iptFilter)

        # Remove nftables
        if not _nftFilter:
            return

        for _dom0, _domU in aExaBoxCluCtrlObj.mReturnDom0DomUPair():
            if _dom0 not in _nftFilter:
                continue

            _hostname = _domU
            _ctx = get_gcontext()

            if _ctx.mCheckRegEntry('_natHN_' + _domU):
                _hostname = _ctx.mGetRegEntry('_natHN_' + _domU)

            _hostname = _hostname.split(".")[0]
            _bridge = f"vm_{_hostname}"

            _node = exaBoxNode(get_gcontext())

            try:
                _node.mConnect(aHost=_dom0)

                if aExaBoxCluCtrlObj.mIsHostOL8(_dom0):

                    _ruleArgs = ["jump", _bridge]
                    _handle = ebIpTablesRoCE.mGetNFTRuleHandle(_node, _ruleArgs)
                    _foundHandle = True if _handle else False

                    # We keep checking for duplicate rules and remove each handle
                    while _handle:

                        _cmd = f"/usr/sbin/nft delete rule bridge filter FORWARD handle {_handle}"
                        node_exec_cmd_check(_node, _cmd)

                        _handle = ebIpTablesRoCE.mGetNFTRuleHandle(_node, _ruleArgs)

                    # Flush chain if handle was found, otherwise it doesn't have to be done
                    if _foundHandle:

                        _cmd = f"/usr/sbin/nft flush chain bridge filter {_bridge}"
                        node_exec_cmd_check(_node, _cmd)

                        _cmd = f"/usr/sbin/nft delete chain bridge filter {_bridge}"
                        node_exec_cmd_check(_node, _cmd)

                    # By this point we can confirm that no chain is found.
                    if not _handle:
                        ebLogWarn(f"Chain not found: {_bridge}")

                else:

                    _cmd = f"/sbin/iptables -D FORWARD -j {_bridge}"
                    node_exec_cmd_check(_node, _cmd)

                    _cmd = f"/sbin/iptables --flush {_bridge}"
                    node_exec_cmd_check(_node, _cmd)

                    _cmd = f"/sbin/iptables -X {_bridge}"
                    node_exec_cmd_check(_node, _cmd)

                if aExaBoxCluCtrlObj.mIsHostOL8(_dom0):
                    ebIpTablesRoCE.mCommitNFTables(_node)
                else:
                    ebIpTablesRoCE.mCommitIPTables(_node)

            finally:
                _node.mDisconnect()


    @staticmethod
    def mSetupSecurityRulesExaBM(aExaBoxCluCtrlObj, aJsonConf: str, aDom0s=None):

        _nftDom0s = aExaBoxCluCtrlObj.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL8"])
        _iptDom0s = aExaBoxCluCtrlObj.mGetHostsByTypeAndOLVersion(ExaKmsHostType.DOM0, ["OL7", "OL6"])

        _nftFilter = []
        _iptFilter = []

        # Filter dom0s in base of the list
        if aDom0s:
            for _dom0 in aDom0s:
                if _dom0 in _nftDom0s:
                    _nftFilter.append(_dom0)
                if _dom0 in _iptDom0s:
                    _iptFilter.append(_dom0)

        else:
            _nftFilter = _nftDom0s
            _iptFilter = _iptDom0s

        # Apply the security rules
        if _nftFilter:
            ebIpTablesRoCE.mSetNfTablesExaBM(aExaBoxCluCtrlObj, aDom0s=_nftFilter)

        if _iptFilter:
            ebIpTablesRoCE.mSetIpTablesExaBM(aExaBoxCluCtrlObj, aJsonConf, aDom0s=_iptFilter)


    @staticmethod
    def mSetNfTablesExaBM(aExaBoxCluCtrlObj, aDom0s=[]):

        _rules_json = {}

        if aExaBoxCluCtrlObj.isBaseDB() or aExaBoxCluCtrlObj.isExacomputeVM():
            with open("properties/basedb_postvm_nft.json") as _f:
                _rules_json = json.load(_f)
        else:
            if ebCluAcceleratedNetwork.isClusterEnabledWithAcceleratedNetwork(aExaBoxCluCtrlObj):
                ebLogInfo(f"{aExaBoxCluCtrlObj.mGetClusterName()} is enabled with accelerated network. Skipping dcsagent nft rules addition")
                return
            with open("properties/exacs_postvm_nft.json") as _f:
                _rules_json = json.load(_f)

        _nft = NfTables()
        _domus_nat_hostnames = dict(aExaBoxCluCtrlObj.mReturnDom0DomUNATPair())
        for _dom0, _domU in aExaBoxCluCtrlObj.mReturnDom0DomUPair():
            if aDom0s and _dom0 not in aDom0s:
                continue
            _client_vnet = ""
            _client_bond = ""
            _backup_vnet = ""
            _backup_bond = ""

            for _network in aExaBoxCluCtrlObj.mGetMachines().mGetMachineConfig(_domU).mGetMacNetworks():
                _network_config = aExaBoxCluCtrlObj.mGetNetworks().mGetNetworkConfig(_network)

                if _network_config.mGetNetType() in ['client', 'backup']:

                    _bridge_suffix = ""
                    _vlan_tag = _network_config.mGetNetVlanId()

                    if _vlan_tag != "UNDEFINED":
                        _bridge_suffix = '.' + _vlan_tag

                    if _network_config.mGetNetType() ==  'backup':
                        _backup_vnet = "vnet*"
                        _backup_bond = f"bondeth0{_bridge_suffix}"
                    else:
                        _client_vnet = "vnet*"
                        _client_bond = f"bondeth0{_bridge_suffix}"

            _replace_values = {
                "domu_nat_hostname": _domus_nat_hostnames[_dom0],
                "client_vnet": _client_vnet,
                "client_bond": _client_bond,
                "backup_vnet": _backup_vnet,
                "backup_bond": _backup_bond
            }

            _rules = _nft.mReplaceValuesJsonRules(
                _rules_json,
                'bridge_filter_vm_rules',
                _replace_values
            )

            # Execute the commands
            with connect_to_host(_dom0, get_gcontext()) as _node:
                # Get rules current state
                _nft.mEnsureNFTableExist(_node, "bridge", "filter")
                _nft_cmd = "/usr/sbin/nft"
                _cmd_str = f"{_nft_cmd} -as list table bridge filter"
                _, _o, _ = node_exec_cmd_check(_node, _cmd_str)
                _out = _o.splitlines()
                _curr_filter_rules_json = _nft.convertConfigToJson(_out)

                # Apply the rules
                for _rule in _rules:
                    _exist_rule = _nft.mRuleExists(
                        _rule,
                        _curr_filter_rules_json
                    )
                    if not _exist_rule:
                        _cmd = _nft.convertJsonConfigToCmd(_rule)
                        node_exec_cmd_check(_node, f"{_nft_cmd} {_cmd}")
                    else:
                        ebLogWarn(f"Rule already exists: {_rule}")

                # Persist the rules
                if aExaBoxCluCtrlObj.mIsHostOL8(_dom0):
                    ebIpTablesRoCE.mCommitNFTables(_node)
                else:
                    ebIpTablesRoCE.mCommitIPTables(_node)


    @staticmethod
    def mSetIpTablesExaBM(aExaBoxCluCtrlObj, aJsonConf: str, aDom0s=[]):
        """
        Configures iptables according to the exabm requirements.

        This process was created to be executed as part of Step2 process.
        Any execution ran via sim install where vms already exists with a reference to netfilter
        might result in errors.

        Parameters:
        aExaBoxCluCtrlObj(exaBoxCluCtrl): A exaBoxCluCtrl instance
        aJsonConf(dict): A dictionary representing the ECRA Payload which
                         may contain the iptables rules at
                         ['atp']['whitelist']['client|backup']['protocol']

        Returns:
        None: No specific value is returned

        """

        ebox = aExaBoxCluCtrlObj
        
        _net_rules = []
        _rule = {"action":"accept","direction":"in","priority":"500"}
        _port = "7060"
        _protocol = "tcp"
        _attr = {"srcipaddr":"169.254.169.254","srcipmask":"32","dstportstart":_port}

        _net_rules.append({"protocol":_protocol,"rule":_rule,"attr":_attr})

        _port = "7070"
        _attr = {"srcipaddr":"169.254.169.254","srcipmask":"32","dstportstart":_port}

        _net_rules.append({"protocol":_protocol,"rule":_rule,"attr":_attr})

        _port = "7060"
        _rule = {"action":"drop","direction":"in","priority":"500"}
        _attr = {"dstportstart":_port}

        _net_rules.append({"protocol":_protocol,"rule":_rule,"attr":_attr})

        _port = "7070"
        _attr = {"dstportstart":_port}
        _net_rules.append({"protocol":_protocol,"rule":_rule,"attr":_attr})


        _rule = {"action":"accept","direction":"inout","priority":"800"}
        _protocol = "all"
        _attr = {}
        _net_rules.append({"protocol":_protocol,"rule":_rule,"attr":_attr})

        _client_net_rules = _net_rules
        _backup_net_rules = _net_rules[2:]

        def _add_rules(aInterfaceAlias,aXMLSchemaLocalPath,aDom0,aDomU,aListOfNetRules):

            _environment = "exabm"
            _net_filter_name = "-".join([aDomU,aInterfaceAlias,_environment])

            #If a filter with the expected name exists. It will be removed to avoid having issues due to left over iptables rules
            #This makes the process more idempotent
            #This was also modified as part of bug:	31380644
            if ebIpTablesRoCE.mExistsNetFilter(aDom0,_net_filter_name):
                ebLogInfo("*** Network filter:{0} found in:{1}. Removing it ***".format(_net_filter_name,aDom0))
                ebIpTablesRoCE.mRemoveNetFilter(aDom0,_net_filter_name)

            ebLogInfo("*** Creating Network Filter:{0} in host:{1} ***".format(_net_filter_name,aDom0))
            ebIpTablesRoCE.mCreateNetFilter(aDom0,_net_filter_name)

            ebIpTablesRoCE.mAddNetFilterToVMSchema(aXMLSchemaLocalPath,aInterfaceAlias,_net_filter_name)

            ebLogInfo("*** Getting network filter:{0} schema ***".format(_net_filter_name))
            _nwfilter_xml_schemas_dict = ebIpTablesRoCE.mGetKVMSchemaFromDom0(aDom0,_net_filter_name,aSchemaType="nwfilter")

            ebIpTablesRoCE.mAddRulesToNetFilterSchema(_nwfilter_xml_schemas_dict["local"], *aListOfNetRules)

            ebLogInfo("*** Defining kvm resource on dom0:{0}".format(aDom0))
            ebIpTablesRoCE.mDefineKVMResourceInDom0(aDom0,_nwfilter_xml_schemas_dict["local"],_nwfilter_xml_schemas_dict["remote"],aSchemaType="nwfilter")

        def _configure_host(aDom0,aDomU):
            
            _domu_xml_schemas_dict = ebIpTablesRoCE.mGetKVMSchemaFromDom0(aDom0,aDomU)

            ebLogInfo(f"*** Obtaining interface aliases for {aDomU} in {aDom0} ***")    
            _client_bridge, _backup_bridge = cluctrlGetDom0Bridges(ebox, aDomU)
            _bridges_types_map = { _client_bridge: "client", _backup_bridge: "backup" }
            _interfaces_alias = ebIpTablesRoCE._mGetInterfacesAlias(_domu_xml_schemas_dict["local"], _bridges_types_map)

            _add_rules(_interfaces_alias['client'],_domu_xml_schemas_dict["local"],aDom0,aDomU,_client_net_rules)
            _add_rules(_interfaces_alias['backup'],_domu_xml_schemas_dict["local"],aDom0,aDomU,_backup_net_rules)

            ebLogInfo("*** Applying network filter changes to domU schema ***")
            ebIpTablesRoCE.mDefineKVMResourceInDom0(aDom0,_domu_xml_schemas_dict["local"],_domu_xml_schemas_dict["remote"])

            ebLogInfo("*** Rebooting machine via virsh reboot to apply schema changes ***")
            with connect_to_host(aDom0, get_gcontext()) as node:
                shutdown_domu(node, aDomU)
                start_domu(node, aDomU, wait_condition=check_user_space_ready)

            if ebox.isATP():
                ebLogInfo(f"*** Starting iptables validation on {aDom0} ***")
                ebIpTablesRoCE.mValidateIptables(aDom0)

        #Parallely Configure iptables 
        _remote_lock = ebox.mGetRemoteLock()

        with _remote_lock():
            _plist = ProcessManager()
            for _dom0, _domu in ebox.mReturnDom0DomUPair():
                if aDom0s and _dom0 not in aDom0s:
                    continue
                _p = ProcessStructure(_configure_host, [_dom0,_domu])
                _p.mSetMaxExecutionTime(60*60)
                _p.mSetJoinTimeout(5)
                _p.mSetLogTimeoutFx(ebLogWarn)
                _plist.mStartAppend(_p)

            _plist.mJoinProcess()

        for  _process in _plist.mGetProcessList():
            if _process.exitcode != 0:
                raise ExacloudRuntimeError(0x0821, 0xA, "Iptables configuration subprocess exited with code:{0} \n{1}".format(_process.exitcode,_process.mStr()), aStackTrace=True)

        if _plist.mGetStatus() == "killed":
            raise ExacloudRuntimeError(0x0821, 0xA, "Timeout while configuring iptables in domUs. Aborting process", aStackTrace=True)

        #Removing temporary iptables rules to allow step2 completion
        ebIpTablesRoCE.mPrevmSetupIptables(ebox,append=False, aDom0s=aDom0s)

    @staticmethod
    def mRemoveIpTablesExaBM(aExaBoxCluCtrlObj,onDomUSchema: bool=True, aDom0s=[]):
        """
        Remove iptables according to the exabm requirements.

        Parameters:
        aExaBoxCluCtrlObj(exaBoxCluCtrl): A exaBoxCluCtrl instance
        onDomUSchema(bool): Defines wether or not the networkfilters should be removed 
                            from the domUs schemas
        exaBoxCluCtrl

        Returns:
        None: No specific value is returned

        """
        ebox = aExaBoxCluCtrlObj

        def _configure_host(_dom0, _domu):
            _net_filter_names = []
            _environment = "exabm"
            _interface_alias = "net0"
            _net_filter_name = "-".join([_domu,_interface_alias,_environment])
            _net_filter_names.append(_net_filter_name)
            
            if onDomUSchema:
                _domu_xml_schemas_dict = ebIpTablesRoCE.mGetKVMSchemaFromDom0(_dom0,_domu)

            if onDomUSchema and ebIpTablesRoCE.mExistsNetFilter(_dom0,_net_filter_name):
                ebLogInfo("*** Network filter:{0} exists on Dom0. ***".format(_net_filter_name))
                ebIpTablesRoCE.mRemoveNetFilterFromVMSchema(_domu_xml_schemas_dict["local"],_interface_alias)
            else:
                ebLogInfo("*** Network filter:{0} does not exists, or the request was made to not modify domU schema. Skipping filter removal ***".format(_net_filter_name))

            _interface_alias = "net1"
            _net_filter_name = "-".join([_domu,_interface_alias,_environment])
            _net_filter_names.append(_net_filter_name)


            if onDomUSchema and ebIpTablesRoCE.mExistsNetFilter(_dom0,_net_filter_name):
                ebLogInfo("*** Network filter:{0} exists on Dom0. ***".format(_net_filter_name))
                ebIpTablesRoCE.mRemoveNetFilterFromVMSchema(_domu_xml_schemas_dict["local"],_interface_alias)
            else:
                ebLogInfo("*** Network filter:{0} does not exists, or the request was made to not modify domU schema. Skipping filter removal ***".format(_net_filter_name))


            if onDomUSchema:
                ebLogInfo("*** Defining schema changes with virsh on dom0_dom:{0} ***".format(_dom0))
                ebIpTablesRoCE.mDefineKVMResourceInDom0(_dom0,_domu_xml_schemas_dict["local"],_domu_xml_schemas_dict["remote"])

                ebLogInfo("*** Rebooting machine via virsh reboot to apply schema changes ***")
                with connect_to_host(_dom0, get_gcontext()) as node:
                    shutdown_domu(node, _domu)
                    start_domu(node, _domu, wait_condition=check_user_space_ready)

            for _net_filter_name in _net_filter_names:
                if ebIpTablesRoCE.mExistsNetFilter(_dom0,_net_filter_name):
                    try:
                        ebIpTablesRoCE.mRemoveNetFilter(_dom0,_net_filter_name)
                    except ExacloudRuntimeError:
                        ebLogError("*** Unable to undefine existing network filter:{0}. Process will continue ***".format(_net_filter_name))

        #Parallely Configure iptables 
        _plist = ProcessManager()
        for _dom0, _domu in aExaBoxCluCtrlObj.mReturnDom0DomUPair():
            if aDom0s and _dom0 not in aDom0s:
                continue
            _p = ProcessStructure(_configure_host, [_dom0,_domu])
            _p.mSetMaxExecutionTime(-1)
            _p.mSetJoinTimeout(10)
            _p.mSetLogTimeoutFx(ebLogWarn)
            _plist.mStartAppend(_p)

        _plist.mJoinProcess()

        for  _process in _plist.mGetProcessList():
            if _process.exitcode != 0:
                raise ExacloudRuntimeError(0x0821, 0xA, "Iptables configuration subprocess exited with code:{0} \n{1}".format(_process.exitcode,_process.mStr()), aStackTrace=True)

        if _plist.mGetStatus() == "killed":
            raise ExacloudRuntimeError(0x0821, 0xA, "Timeout while configuring iptables in domUs. Aborting process", aStackTrace=True)

        #Removing temporary iptables rules
        ebIpTablesRoCE.mPrevmSetupIptables(ebox,append=False, aDom0s=aDom0s)
