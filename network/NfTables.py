"""$Header:

 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    NfTables class

FUNCTION:
    Implements the nftables command producer and nftables config parser.

NOTE:
    None

History:

        MODIFIED   (MM/DD/YY)
        jesandov   11/21/25 - 38677852: Remove comment message
        scoral     09/22/25 - Bug 38446950 - Implement mDeleteNFTRules as a
                              generalization of mDeleteDuplicateNFTRules.
        ririgoye   05/05/25 - Bug 37802755 - NFT DUPLICATE RULE DELETION FAILED
        joysjose   08/30/24 - Bug 36731935 : Make sure all NFTables are created
                              in the dom0s during Create Service and Add
                              Compute
        scoral     04/14/23 - Bug 35177571 - Fixed code command to add a chain.
                              Implemented also template replacement for chain
                              name.
        shavenug   01/15/23 - NfTables config Implementation
        shavenug   01/11/23 - create file
"""

import json
import copy
from exabox.log.LogMgr import ebLogInfo
from exabox.utils.node import node_exec_cmd_check, node_exec_cmd
from exabox.log.LogMgr import ebLogInfo, ebLogTrace, ebLogError
from exabox.core.Error import ExacloudRuntimeError



'''
rules = [{
        "type": "rule",
        "ruleset": "ip",
        "table": "filter",
        "chain" : "FORWARD",
        "details" : 
            [
                "iifname \"vmeth{vmeth_num}\" ip protocol tcp ct state established,related accept",
                "iifname \"vmeth{vmeth_num}\" ip protocol icmp ct state established,related accept",
                "oifname \"vmeth{vmeth_num}\" ip protocol tcp ct state established,related accept",
                "oifname \"vmeth{vmeth_num}\" ip protocol icmp ct state established,related accept",
                "oifname \"vmeth{vmeth_num}\" tcp dport 22 accept",
                "oifname \"vmeth{vmeth_num}\" icmp type echo-request accept",
            ]
    },
     {
        "type" : "chain",
        "ruleset": "ip",
        "chain" : "FORWARD",
        "table" : "filter",
        "details" :
            [
                "type filter hook forward priority filter\; policy accept\;"
            ] 

     }
    ]

nftConfig = """table ip filter {
    chain INPUT {
        type filter hook input priority filter; policy accept;
    }

    chain FORWARD {
        type filter hook forward priority filter; policy drop;
        iifname "vmeth0" ip protocol tcp ct state established,related accept
        oifname "vmeth0" tcp dport 22 accept
        oifname "vmeth0" icmp type echo-request accept
        iifname "vmeth0" ip daddr 12.12.12.12 tcp dport 1000 accept
        limit rate 2/minute log prefix "IPTables-FORWARD Dropped: "
        limit rate 2/minute log prefix "IPTables-FORWARD Dropped: "
        limit rate 2/minute log prefix "IPTables-FORWARD Dropped: "
    }

 }"""

nftConfig2 = """table ip filter { # handle 1
    chain INPUT { # handle 1
        type filter hook input priority filter; policy accept;
    }

    chain FORWARD { # handle 2
        type filter hook forward priority filter; policy drop;
        iifname "vmeth0" ip protocol tcp ct state established,related accept # handle 77
        oifname "vmeth0" tcp dport 22 accept # handle 78
        oifname "vmeth0" icmp type echo-request accept # handle 79
        iifname "vmeth0" ip daddr 12.12.12.12 tcp dport 1000 accept # handle 80
        limit rate 2/minute log prefix "IPTables-FORWARD Dropped: " # handle 86
        limit rate 2/minute log prefix "IPTables-FORWARD Dropped: " # handle 89
        limit rate 2/minute log prefix "IPTables-FORWARD Dropped: " # handle 90
        iifname "vmeth0" ip protocol tcp ct state established,related accept # handle 91
    }

    chain OUTPUT { # handle 3
        type filter hook output priority filter; policy accept;
        ip daddr 169.254.0.0/16 counter packets 437680 bytes 33221326 jump BareMetalInstanceServices # handle 9
        oifname "lo" accept # handle 81
    }

    chain BareMetalInstanceServices { # handle 8
        meta l4proto tcp ip daddr 169.254.0.2 skuid 0 tcp dport 3260  counter packets 0 bytes 0 accept # handle 10
        meta l4proto tcp ip daddr 169.254.2.0/24 skuid 0 tcp dport 3260  counter packets 0 bytes 0 accept # handle 11
        meta l4proto tcp ip daddr 169.254.4.0/24 skuid 0 tcp dport 3260  counter packets 0 bytes 0 accept # handle 12
        meta l4proto tcp ip daddr 169.254.5.0/24 skuid 0 tcp dport 3260  counter packets 0 bytes 0 accept # handle 13
        meta l4proto tcp ip daddr 169.254.0.2 tcp dport 80  counter packets 0 bytes 0 accept # handle 14
        meta l4proto udp ip daddr 169.254.169.254 udp dport 53  counter packets 79691 bytes 7311856 accept # handle 15
        meta l4proto tcp ip daddr 169.254.169.254 tcp dport 53  counter packets 0 bytes 0 accept # handle 16
        meta l4proto tcp ip daddr 169.254.0.3 skuid 0 tcp dport 80  counter packets 0 bytes 0 accept # handle 17
        meta l4proto tcp ip daddr 169.254.0.4 tcp dport 80  counter packets 0 bytes 0 accept # handle 18
        meta l4proto tcp ip daddr 169.254.169.254 tcp dport 80  counter packets 356164 bytes 25752946 accept # handle 19
        meta l4proto udp ip daddr 169.254.169.254 udp dport 67  counter packets 37 bytes 12136 accept # handle 20
        meta l4proto udp ip daddr 169.254.169.254 udp dport 69  counter packets 0 bytes 0 accept # handle 21
        meta l4proto udp ip daddr 169.254.169.254 udp dport 123  counter packets 1771 bytes 134596 accept # handle 22
        meta l4proto tcp ip daddr 169.254.0.0/16   counter packets 0 bytes 0 reject with tcp reset # handle 23
        meta l4proto udp ip daddr 169.254.0.0/16   counter packets 0 bytes 0 reject # handle 24
    }
} """
'''

class NfTables:

    def convertJsonConfigToCmd(self, nftjsonConfig, operation="ADD", handle=None):

        command = ""

        if nftjsonConfig['type'] == "rule" :

            if operation == "ADD":
                command = f"add rule {nftjsonConfig['ruleset']} {nftjsonConfig['table']} {nftjsonConfig['chain']} {nftjsonConfig['details']}"

            elif operation == "DELETE":

                if handle:
                    command = f"delete rule {nftjsonConfig['ruleset']} {nftjsonConfig['table']} {nftjsonConfig['chain']} handle {handle}"
                elif 'handle' in nftjsonConfig:
                    command = f"delete rule {nftjsonConfig['ruleset']} {nftjsonConfig['table']} {nftjsonConfig['chain']} handle {nftjsonConfig['handle']}"

        elif nftjsonConfig['type'] == "chain":

            if operation == "ADD":
                command = f"add chain {nftjsonConfig['ruleset']} {nftjsonConfig['table']} {nftjsonConfig['chain']} " + "'{" + nftjsonConfig['details'] + "}'"

            elif operation == "FLUSH":
                command = f"flush chain {nftjsonConfig['ruleset']} {nftjsonConfig['table']} {nftjsonConfig['chain']}"

            elif operation == "DELETE":
                command = f"delete chain {nftjsonConfig['ruleset']} {nftjsonConfig['table']} {nftjsonConfig['chain']}"

        return command


    def convertConfigToCommand(self, nftConfig):
        resultCommands = []
        jsonConfig = self.convertConfigToJson(nftConfig)
        ebLogInfo(json.dumps(jsonConfig, indent = 4))
        for cfg in jsonConfig:
            resultCommands += self.convertJsonConfigToCmd(cfg)
        ebLogInfo(json.dumps(jsonConfig, indent = 4))
        return resultCommands

    def convertConfigToJson(self, nftConfig):
        NFT_SECTION_STARTER_TOKEN ='{'
        NFT_SECTION_END_TOKEN='}'
        NFT_CHAIN_DECLARE_START_TOKEN = "type"
        resultJson = []
        rules = []
        chaincomment = []

        if isinstance(nftConfig, list):
            cfgLines = nftConfig
        else:
            cfgLines = nftConfig.split("\n")
        current_section = None
        for line in cfgLines:
            rawline = line.strip()
            if not rawline:
                continue
            if "#" in rawline:
                linecommentsplit = rawline.split("#")
                line = linecommentsplit[0].strip()
                comment = linecommentsplit[1].strip().split()
            else:
                line = rawline
                comment = []
            linetokens = line.split()
            if linetokens[-1] == NFT_SECTION_STARTER_TOKEN:
                if linetokens[0] == 'table':
                    # table line format is  'table {ruleset} {tableName} {'
                    table = linetokens[2]
                    ruleset = linetokens[1]
                    current_section = "table"
                if linetokens[0] == 'chain':
                    #chain likne format is 'chain {chainName} {'
                    chain = linetokens[1]
                    current_section = "chain"
                    chaincomment = comment
            elif linetokens[-1] == NFT_SECTION_END_TOKEN:
                if current_section == "chain":
                    '''
                    if rules:
                        ruleJson = { "type": "rule",
                              "ruleset": ruleset,
                              "chain": chain,
                              "table": table,
                              "handles": handles,
                              "details" : rules }
                        resultJson.append(ruleJson)
                    rules = []
                    handles = []
                    '''
                    chain = None
                    current_section = "table"
                    chaincomment = None
                elif current_section == "table":
                    ruleset = None
                    table = None
                    current_section = None
            else:
                if linetokens[0] == NFT_CHAIN_DECLARE_START_TOKEN:
                    chainjson =  {"type" :"chain",
                                  "ruleset": ruleset,
                                  "table": table,
                                  "chain" : chain,
                                  "details": line
                                  }
                    if chaincomment:
                        chainjson['handle'] = chaincomment[-1]
                    resultJson.append(chainjson)
                else:
                    ruleJson = { "type": "rule",
                              "ruleset": ruleset,
                              "chain": chain,
                              "table": table,
                              "details" : line }
                    resultJson.append(ruleJson)
                    if comment:
                        ruleJson['handle'] = comment[-1]

        return resultJson

    def mReplaceValuesJsonRules(self, aIpRules, aRuleKey, aReplaceDict={}):

        _rules_list = []

        for ip_rule in aIpRules[aRuleKey]:

            _replaced = copy.deepcopy(ip_rule)
            _replaced["details"] = _replaced["details"].format(**aReplaceDict)
            _replaced["chain"] = _replaced["chain"].format(**aReplaceDict)
            _rules_list.append(_replaced)

        return _rules_list

    def mRuleExistsPosition(self, aRule, aRuleSet):

        def clean(aStr):

            _tokens = ["\\", "/", " ", "\"", "'"]

            _c = str(aStr)
            for _token in _tokens:
                _c = _c.replace(_token, "")

            return _c

        _exclude_keys = ["handle"]
        _positions = []

        for _index, _rule in enumerate(aRuleSet):

            _found = True
            for _key in _rule.keys():

                if _key in _exclude_keys:
                    continue

                if _key not in aRule:
                    _found = False
                    break

                if clean(_rule[_key]) != clean(aRule[_key]):
                    _found = False
                    break

            if _found:
                _positions.append(_index)

        return _positions

    def mRuleExists(self, aRule, aRuleSet):
        _positions = self.mRuleExistsPosition(aRule, aRuleSet)
        if _positions:
            return aRuleSet[_positions[0]]
        else:
            return None
        
    def mGetDefaultChainCommands(self, aFamily, aTable):
        '''
        This function implementation is adopted from the script 
        exacloud/exadataPrePostPlugins/dbnu_plugins/ol7_iptables_to_ol8_nftables.py
        It aims at creating the default chains required before rule addition to the table created. 
        This function returns the default chain commands.
        '''
        _table = aTable
        _family = aFamily
        _cmds = []
        if _table.endswith('filter'):
            _cmds.append(f"add chain {_family} filter INPUT '{{ type filter hook input priority filter; policy accept; }}'")
            _cmds.append(f"add chain {_family} filter FORWARD '{{ type filter hook forward priority filter; policy accept; }}'")
            _cmds.append(f"add chain {_family} filter OUTPUT '{{ type filter hook output priority filter; policy accept; }}'")
        elif _table.endswith('nat'):
            _cmds.append(f"add chain {_family} nat PREROUTING '{{ type nat hook prerouting priority dstnat; policy accept; }}'")
            _cmds.append(f"add chain {_family} nat INPUT '{{ type nat hook input priority 100; policy accept; }}'")
            _cmds.append(f"add chain {_family} nat POSTROUTING '{{ type nat hook postrouting priority srcnat; policy accept; }}'")
            _cmds.append(f"add chain {_family} nat OUTPUT '{{ type nat hook output priority -100; policy accept; }}'")
        elif _table.endswith('mangle'):
            _cmds.append(f"add chain {_family} mangle PREROUTING '{{ type filter hook prerouting priority mangle; policy accept; }}'")
            _cmds.append(f"add chain {_family} mangle INPUT '{{ type filter hook input priority mangle; policy accept; }}'")
            _cmds.append(f"add chain {_family} mangle FORWARD '{{ type filter hook forward priority mangle; policy accept; }}'")
            _cmds.append(f"add chain {_family} mangle OUTPUT '{{ type route hook output priority mangle; policy accept; }}'")
            _cmds.append(f"add chain {_family} mangle POSTROUTING '{{ type filter hook postrouting priority mangle; policy accept; }}'")
        return _cmds

    def mEnsureNFTableExist(self, aNode, aFamily, aTable, aDefaultChain=True):
        '''
        This function aims at the creation of tables in NFTables along with default chains, if found missing on a host.
        It can be invoked before the addition of rules to the nftables to make sure that the table and the chain is present 
        before rules are added to it. Commiting of the rules is not included in this function as it is assumed that it would be
        taken care while adding rules.
        '''
        _family = aFamily
        _table = aTable
        _node = aNode
        try:
            _nft_cmd = "/usr/sbin/nft"
            _cmd_str = f"{_nft_cmd} list tables | grep '{_family} {_table}'"
            _ret, _out, _err = node_exec_cmd(_node, _cmd_str)
            if _ret!=0:
                ebLogTrace(f"Table {_family} {_table} does not exist. Adding the table..")
                _cmd_str = f"{_nft_cmd} add table {_family} {_table}"
                _ret, _out, _err = node_exec_cmd(_node, _cmd_str)
                if _ret == 0:
                    ebLogTrace(f"Addition of table {_family} {_table} is successful")
                    if aDefaultChain:
                        ebLogTrace(f"Proceeding with addition of default chains for the table")
                        _default_chain_cmds = self.mGetDefaultChainCommands(_family, _table)
                        for _cmd in _default_chain_cmds:
                            _node.mExecuteCmd('/usr/sbin/nft ' + _cmd)
                    else:
                        ebLogTrace(f"Default Chain Addition for Table Added is disabled.")
                else:
                    _err = f"Addition of table {_family} {_table} failed.."
                    raise Exception(_err)
                    
            elif _ret==0:
                ebLogTrace(f"NFTable {_family} {_table} exists..")
        except Exception as e:
            _err = f"mEnsureNFTableExist failed with Exception {str(e)}"
            raise ExacloudRuntimeError(0x0838, 0xA, _err)

    def mDeleteNFTRules(self, aNode, aRuleSet=None, aOnlyDuplicates=False):
        ebLogInfo("Removing NFTables rules...")

        # List current ruleset
        _nft_cmd = "/usr/sbin/nft"
        _cmd_str = f"{_nft_cmd} -as list ruleset"
        _, _o, _e = aNode.mExecuteCmd(_cmd_str)
        _out = _o.readlines()
        _curr_rules_json = self.convertConfigToJson(_out)

        # If not specific set of rules, remove all rules.
        if aRuleSet is None:
            aRuleSet = _curr_rules_json
        
        # How many rules to keep
        _k = 1 if aOnlyDuplicates else 0

        # Create list of indices where the duplicated rules will be stored
        _delete_indexes = []

        for _rule_to_find in aRuleSet:

            if "ToDelete" in _rule_to_find:
                continue

            # mRuleExistsPosition will always include the first occurence of the rule,
            # therefore we must ignore it in case there is more than one, as we would
            # be deleting the original rule with this logic otherwise.
            _positions = self.mRuleExistsPosition(_rule_to_find, _curr_rules_json)

            if _positions and len(_positions) > _k:
                ebLogInfo(f"Detected duplicated rule: {_rule_to_find}")
                ebLogTrace(f"Rule found at indexes: {_positions}")
                # Add indexes to delete (except the original instance)
                _delete_indexes.extend(_positions[_k:])
                for _p in _positions[_k:]:
                    _curr_rules_json[_p]["ToDelete"] = True

        # Ensure the correct deletion of the rule by specifying both the rule and the handle
        for _index in _delete_indexes:
            _rule = _curr_rules_json[_index]
            _handle = _rule["handle"]
            _cmd = self.convertJsonConfigToCmd(_rule, operation="DELETE", handle=_handle)
            node_exec_cmd(aNode, f"{_nft_cmd} {_cmd}",
                    log_error=True, log_stdout_on_error=True)

    def mDeleteDuplicateNFTRules(self, aNode):
        ebLogInfo("Removing duplicated NFTables rules")
        self.mDeleteNFTRules(aNode, aOnlyDuplicates=True)

# end of file
