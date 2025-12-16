#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/cluhealthpostprov.py /main/9 2022/02/09 11:59:18 illamas Exp $
#
# cluhealthpostprov.py
#
# Copyright (c) 2021, 2022, Oracle and/or its affiliates.
#
#    NAME
#      cluhealthpostprov.py - 
#
#    DESCRIPTION
#      Provide functionality of endpoint to perform Post-Provisioning Health Checks
#
#    NOTES
#      Since this checks will be performed during create service, this should never trigger
#      exceptions, as this would have impact on current provisioning and cause failure.
#      ECRA has a property to determine if abort should happend based on check results
#
#    MODIFIED   (MM/DD/YY)
#    illamas     02/04/22 - Enh 33820899 Adding data/reco checks
#    illamas     10/12/21 - Enh 33444585 - Enhancement for postChecks
#    illamas     07/14/21 - Bug 33116643 - The mandatory field is wrong when
#                           the result is stored in DB
#    illamas     07/01/21 - Enh 33055022 - Adding more validations for
#                           postcheck framework
#    marislop    06/23/21 - ENH 32925891 Accept clusterless and dom0 list
#    jfsaldan    01/20/21 - Creation
#

from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from enum import Enum
import re

# Useful alias to use on dictionary building
CURR_VAL = "currentValue"
RESULT = "result"
ERR_MSG = "err_msg"

# Useful alias for results 
PASS = "pass"
FAIL = "fail"
ERROR = "error"

# Useful alias to use on dictionary parsing
TYPE = "type"
NAME = "name"
METRIC = "metric"
EXPECTED = "expected"
MANDATORY = "mandatory"
CURRENT = "currentValue"
ARGUMENT = "argument"
EXPECTED_RETURN_CODE = "expected_return_code"
CURRENT_RETURN_CODE  = "current_return_code"

# Types of validations
FILESYSTEM = "filesystem"
COMMAND    = "command"

def executeHealthPostProv(aClubox: object, aOptions: dict)-> dict:
    """
    This is the driver function that will call other functions to perform
    specific checks.
    The final response json is build here with the results
    from other checks-functions
    param aClubox(exaBoxCluCtrl): an exaBoxCluCtrl object
    param aOptions: an aOptions dict containing desired checks to run
    returns _return_dict: dictionary with results
    """
    try:
        _jconf = aOptions.jsonconf
    except:
        ebLogError("jsonconf is requiered for this operation. Aborting")
        return ebError(0x0808)    #TODO return empty dict?
    else:
        if not _jconf:
            ebLogError("jsonconf cannot be none. Aborting")
            return ebError(0x0808)
    _ebox = aClubox
    _return_dict = {}

    # Getting hostNames list from json
    # hostNames list is used to get serial_number and admin_ether
    # In this case, json only have dom0,cells and hostNames objects.
    _hostnames = _jconf.get("hostnames", [])

    _dom0 = []
    _domU = []
    pairs = aClubox.mReturnDom0DomUPair(aIsClusterLessXML=aClubox.mIsClusterLessXML())
    for pair in pairs:
        _dom0.append(pair[0])
        _domU.append(pair[1])

    _cells = []
    dicst_cells = aClubox.mReturnCellNodes(aIsClusterLessXML=aClubox.mIsClusterLessXML())
    for cell in dicst_cells.keys():
        _cells.append(cell)
    #
    # DomU checks
    #
    _checks_domU = _jconf.get("domU", None)
    if _checks_domU:
        try:
            _return_dict["domU_checks"] = checkDriver(_domU, _checks_domU,"domU")
        except:
            _return_dict["domU_checks"] = errComputeDriver("domU")

    #
    # Dom0 checks
    #
    _checks_dom0 = _jconf.get("dom0", None)
    if _checks_dom0:
        _dom0 = _dom0 if len(set(_dom0) & set(_hostnames))==0 else _hostnames
        try:
            _return_dict["dom0_checks"] = checkDriver(_dom0, _checks_dom0,"dom0")
        except:
            _return_dict["dom0_checks"] = errComputeDriver("dom0")

    #
    # Cell checks
    #
    _checks_cell = _jconf.get("cell", None)
    if _checks_cell:
        _cells = _cells if len(set(_cells) & set(_hostnames))==0 else _hostnames
        try:
            _return_dict["cell_checks"] = checkDriver(_cells, _checks_cell,"cell")
        except:
            _return_dict["cell_checks"] = errComputeDriver("cell")

    return _return_dict

def errComputeDriver(aComputeType: str) -> dict:
    """
    Helper function to return an error response
    param aComputeType: 
    returns 
    """
    _key = f"err_msg"
    _err_msg = f"Something unexpected happened while running '{aComputeType}' checks"
    return {"err_msg": _err_msg}

def checkDriver(aListHost: list, aDictOfChecks: dict, aTargetMachine: str)-> dict:
    """
    This function determines which checks are requiered for the given host
    param aListHost: a list
    param aDictOfChecks: dictionary containing the list of all checks
    param aTargetMachine: target machine for the check (dom0,domU,cell)
    returns _results_dict: dictionary containing check results
    """
    _results_dict = {}
    #
    # Make sure payload contains valid checks to be done
    # properties and commands are valid ones.
    # Otherwise don't open node connection
    #
    for host in aListHost:
        _results_filesystem = []
        _results_command    = []
        _node = exaBoxNode(get_gcontext())
        _node.mSetMaxRetries(2)
        try:
            if not _node.mIsConnectable(aHost=host):
                ebLogTrace(f"Node {host} is not connectable")
                continue
            _node.mConnect(aHost=host)
            aNode = _node
            _results_dict[host] = {}
            _grid_home_placeholder = "$GRID_HOME"
            _grid_home_path        = ""
            if(aTargetMachine == "domU"):
                _grid_home_path = _getGridHome(aNode)  
            for key,values in aDictOfChecks.items():
                _validation_type = values.get(TYPE)
                if _validation_type == FILESYSTEM:
                    ebLogInfo("Filesystem validations")
                    _results_filesystem.append({})
                    index = len(_results_filesystem)-1
                    _fs_mnt_point = key
                    _fs_size = values[EXPECTED]
                    _fs_block_size = values[METRIC]
                    _expected = f"{_fs_size}{_fs_block_size}"
                    _results_filesystem[index][NAME] = _fs_mnt_point
                    _results_filesystem[index][EXPECTED] = _fs_size
                    _results_filesystem[index][METRIC] = _fs_block_size
                    _results_filesystem[index][MANDATORY] = values.get(MANDATORY)
                    _fs_mnt_point = _fs_mnt_point.replace(_grid_home_placeholder,_grid_home_path)
                    ebLogInfo(f"Path {_fs_mnt_point} Expected {_fs_size} {_fs_block_size}")
                    #
                    # Check that we received a valid mount point,
                    # skip check if not a valid Mnt Point
                    #
                    if not _isFsMntPoint(aNode, _fs_mnt_point):
                        _results_filesystem[index][RESULT] = ERROR
                        _results_filesystem[index][ERR_MSG] = (
                            f"Invalid mount point: {_fs_mnt_point}"
                        )
                        ebLogInfo(f"Invalid mount point: {_fs_mnt_point}")
                        continue
                    try:
                        _cmd = f"/usr/bin/df {_fs_mnt_point} -PB{_fs_block_size}"
                        _, _o, _e = aNode.mExecuteCmd(_cmd)
                        _rc = aNode.mGetCmdExitStatus()
                        _out = _o.readlines()
                    except:
                        _messages = "\n".join(_e.readlines())
                        _results_filesystem[index][RESULT] = ERROR
                        _results_filesystem[index][ERR_MSG] = (
                            f"Unable to perform check with cmd {_cmd}: {_messages}"
                        )
                        ebLogInfo(f"Unable to perform check with cmd {_cmd}: {_messages}")

                    else:
                        #
                        # Below determines Pass/Fail based on expectedValue & metric
                        # Number '2' is because 'df' returns headers and results, e.g.
                        # Filesystem     1K-blocks      Used Available Use% Mounted on
                        # /dev/vdb       206292968 125967036  69823788  65% /scratch
                        #
                        if 2 == len(_out) and not _rc:

                            fixed_size ={"G":"5","T":".005"}
                            _expected_value = float(_fs_size)
                            _validation = False
                            
                            _current_size = _out[1].split()[1]
                            _results_filesystem[index][CURR_VAL] = _current_size
                            _current_size_number = int(_current_size[0:len(_current_size)-1])

                            if(fixed_size.get(_fs_block_size)):
                                _expected_size_right = _expected_value + float(fixed_size.get(_fs_block_size))
                                _expected_size_left  = _expected_value - float(fixed_size.get(_fs_block_size))
                                _greater_or_equal = _current_size_number >= _expected_size_left
                                _less_or_equal    = _current_size_number <= _expected_size_right
                                _validation = _greater_or_equal and _less_or_equal
                            else:
                                _validation = (_expected_value == _current_size_number)

                            if _validation:
                                _results_filesystem[index][RESULT] = PASS
                            else:
                                _results_filesystem[index][RESULT] = FAIL
                            ebLogInfo(f"Result: {_results_filesystem[index][RESULT]}")
                        else:
                            _messages = "\n".join(_e.readlines())
                            _results_filesystem[index][RESULT] = ERROR
                            _results_filesystem[index][ERR_MSG] = (
                                f"Something unexpected occurred: {_messages}, "
                                f"command: '{_cmd}' exited with error: '{_rc}'"
                            )
                            ebLogInfo(f"Something unexpected occurred: {_messages}")
                else:

                    ebLogInfo("Command validation")
                    _results_command.append({})
                    index = len(_results_command)-1
                    _cmd_path =  values[COMMAND]
                    _cmd_path = _cmd_path.replace(_grid_home_placeholder,_grid_home_path)
                    _cmd_arguments = values[ARGUMENT]
                    _cmd_expectd_output = values[EXPECTED]
                    _cmd_expected_return_code = values[EXPECTED_RETURN_CODE]
                    _results_command[index][NAME]     = key
                    _results_command[index][COMMAND]  = _cmd_path
                    _results_command[index][ARGUMENT] = _cmd_arguments
                    _results_command[index][EXPECTED] = _cmd_expectd_output
                    _results_command[index][MANDATORY]= values.get(MANDATORY)
                    _results_command[index][EXPECTED_RETURN_CODE] = _cmd_expected_return_code
                    ebLogInfo(f"Command {_cmd_path} arguments {_cmd_arguments} expected {_cmd_expectd_output}")
                    try:
                        _cmd = f"{_cmd_path} {_cmd_arguments}"
                        _, _o, _e = aNode.mExecuteCmd(_cmd)
                        _rc = aNode.mGetCmdExitStatus()
                        _results_command[index][CURRENT_RETURN_CODE] = str(_rc)
                        _out = _o.readlines()
                    except:
                        _messages = "\n".join(_e.readlines())
                        _results_command[index][RESULT] = ERROR
                        _results_command[index][ERR_MSG] = (
                            f"Unable to perform check with cmd {_cmd}: {_messages}"
                        )
                        ebLogInfo(f"Unable to perform check with cmd {_cmd}: {_messages}")
                    else:
                        #
                        # Below determines Pass/Fail based on expectedValue & metric
                        # Number '2' is because 'df' returns headers and results, e.g.
                        # Filesystem     1K-blocks      Used Available Use% Mounted on
                        # /dev/vdb       206292968 125967036  69823788  65% /scratch
                        #
                        try:
                            _current_output = str(_out).replace(r"\r\n", r"\n")
                            _results_command[index][CURR_VAL] = str(_current_output)
                            if re.search(".*"+_cmd_expectd_output+"\\\\n\\s*",str(_current_output)) and str(_rc) == _cmd_expected_return_code:
                                _results_command[index][RESULT] = PASS
                            else:
                                _results_command[index][RESULT] = FAIL
                            ebLogInfo(f"Result: {_results_command[index][RESULT]}")
                        except:
                            _messages = "\n".join(_e.readlines())
                            _results_command[index][RESULT] = ERROR
                            _results_command[index][ERR_MSG] = (
                                f"Something unexpected occurred: {_messages}, "
                                f"command: '{_cmd}' exited with error: '{_rc}'"
                            )
                            ebLogInfo(f"Something unexpected occurred: {_messages}")
            _results_dict[host] = {FILESYSTEM:_results_filesystem,COMMAND:_results_command}
        except:
            _err_msg = ("Unexpected error while doing checks")
            _results_dict[ERR_MSG] = _err_msg
            ebLogInfo("Unexpected error while doing checks")
        finally:
            _node.mDisconnect()
    return _results_dict

def _isFsMntPoint(aNode: exaBoxNode, aMntPoint: str) -> bool:
    """
    Check if aMntPoint is a valid mount point
    param aNode: an already connected node to a desired host
    param aMntPoint: a String
    
    returns :True if aMntPoint is a mount point of a filesystem,
                False otherwise
    """
    _cmd = f"/usr/bin/findmnt {aMntPoint}"
    aNode.mExecuteCmd(_cmd)
    return not aNode.mGetCmdExitStatus()

def _getGridHome(aNode: exaBoxNode) -> str:
    """
    Return the $GRID_HOME location
    param aNode: an already connected node to a desired host

    returns: Absolute path of $GRID_HOME
    """
    _error_str = '*** GRID.INI entry not found for grid'
    _cmd = "cat /etc/oratab | grep +ASM | cut -d ':' -f 2"
    _, _o, _e = aNode.mExecuteCmd(_cmd)
    _out = _o.readlines()
    if not _out or len(_out) == 0: 
        ebLogError(_error_str)
        raise ExacloudRuntimeError(0x0792, 0x0A, _error_str)
    _grid_home = _out[0].replace("\n","")
    ebLogInfo(f"$GRID_HOME: {_grid_home}")
    return _grid_home
