"""
 Copyright (c) 2014, 2020, Oracle and/or its affiliates. All rights reserved.

NAME:
    OVM - Data guard functionality

FUNCTION:
    Module to provide data guard related functions

NOTE:
    None

History:
    dtalla      05/11/2018 - Fix for Bug 27983437, Disabling EB tables.
    aschital    08/26/2016 - added lifecycle operations, restructred output handling, names etc.
    aschital    07/15/2016 - Changed to support slightly modified json input
    aschital    06/20/2016 - Changed scanip json structure, other minor changes per testing
    aschital    06/14/2016 - Restructure for json output
    aschital    05/30/2016 - Create file

Changelog:

"""

from exabox.core.Node import exaBoxNode
from exabox.core.Error import ebError
from exabox.core.Context import get_gcontext
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogDebug, ebLogJson
from exabox.core.DBStore import ebGetDefaultDB
import os, sys, os.path, time
import json
import re
from multiprocessing import Process, Manager
from datetime import datetime

RESULTKEY="result"
ERRKEY="error"
OUTKEY="output"

DGASYNC="/var/opt/oracle/dg/dgasync"
LC_OPERS = ["switchover", "failover", "reinstate", "state"]
LC_SWITCHOVER=DGASYNC + " -dbname %s switchover "
LC_FAILOVER=DGASYNC + " -dbname %s failover -force "
LC_REINSTATE=DGASYNC + " -dbname %s reinstate "
LC_STATE=DGASYNC + " -dbname %s dataguard_status -details"
LC_GETRESULT=DGASYNC + " -dbname %s get_status %s"

class ebCluDataguardManager(object):

    def __init__(self, aCluCtrlObj):
        self.__cluctrl = aCluCtrlObj
        self.__reqobj  = aCluCtrlObj.mGetRequestObj()
        self.__options = None

    # Entry point for all DG functioality
    def mClusterDataguard(self, aOptions=None):
        rc = -1
        out, err = {}, {}
        self.__options = aOptions
        try:
            self._validate_args(aOptions)
            rc, out, err = self._execute_dgcmd(aOptions)
            result = "pass" if (rc == 0) else "fail"
        except Exception as e:
            result = "fail"
            err["generic"] = 'Exception during dataguard command execution: '+ str(e)
            ebLogError('*** ' + str(err))
        self._updateResponse(aOptions, rc, out, err)
        return (rc if (rc==0) else ebError(0x0650))

    def _updateResponse(self, aOptions, rc, out, err):
        json_response = dict()
        result = "pass" if (rc == 0) else "fail"
        json_response[RESULTKEY] = result
        json_response[ERRKEY] = err
        json_response[OUTKEY] = out
        if aOptions.jsonmode:
            ebLogJson(json.dumps(json_response, indent=4, separators=(',', ': ')))
        if (self.__reqobj is not None):
            db = ebGetDefaultDB()
            self.__reqobj.mSetData(json.dumps(json_response, indent=4))
            db.mUpdateRequest(self.__reqobj)

    def _validate_args (self, aOptions):
        if (aOptions is None):
            raise ValueError ("aOptions must be supplied")
        if (aOptions.jsonconf is None):
            raise ValueError ("jsonconf must be supplied")
        if (aOptions.dgcmd is None):
            raise ValueError ("dgcmd must be supplied")

    # Loop over all DomUs and execute the dataguard command
    def _execute_dgcmd(self, aOptions):
        all_results = dict()
        plist = []
        for dom0, domu in self.__cluctrl.mReturnDom0DomUPair():
            all_results[domu] = Manager().dict()
            all_results[domu][OUTKEY] = ""
            all_results[domu][ERRKEY] = ""
            p = Process(target=self._execute_cmd, args=(domu, aOptions.dgcmd, aOptions.jsonconf, all_results[domu]))
            plist.append(p)
            p.start()
            # If DG lifecycle operation or is_connectivity_required, it's sufficient to execute only on one domu 
            if (aOptions.dgcmd in LC_OPERS) or aOptions.dgcmd == "is_connectivity_required" :
                break
        self._wait_for_completion(plist)
        return self._create_results_json(all_results)

    def _wait_for_completion(self, plist):
        still_running = True
        while still_running:
            still_running = False
            for p in plist:
                if p.is_alive():
                    still_running = True
                    time.sleep(5)

    def _create_results_json (self, all_results):
        rc = 0
        out, err = {}, {}
        for domu in list(all_results.keys()):
            if (all_results[domu][OUTKEY] != ""):
                out[domu] = all_results[domu][OUTKEY]
            if (all_results[domu][ERRKEY] != ""):
                rc = -1
                err[domu] = all_results[domu][ERRKEY]
        return rc, out, err

    def _execute_cmd(self, domu, dgcmd, jsonconf, results):
        try:
            if (dgcmd == "configure"):
                operations = [self._configure_addpublickey, self._configure_storepvtkey, 
                              self._configure_addscanips, self._configure_addips, self._configure_addiptoebt]
                for op in operations:
                    op(domu, jsonconf, results)
            elif (dgcmd == "delconn"):
                operations = [self._delpvtkey, 
                              self._delscanips, self._delips]
                for op in operations:
                    op(domu, jsonconf, results)
            elif (dgcmd == "verifyconn"):
                self._verifyconn(domu, jsonconf, results)
            elif (dgcmd in LC_OPERS):
                self._invoke_lc_oper(domu, jsonconf, results, dgcmd)
            elif (dgcmd == "is_connectivity_required"):
                self._is_connectivity_required(domu, jsonconf, results)
            else:
                err = 'Unsupported Dataguard operation: ' + dgcmd
                ebLogError('*** ' + err)
                separator = "," if results[ERRKEY] != "" else ""
                results[ERRKEY] += separator + err
        except Exception as e:
            ebLogError('*** ' + str(e))
            separator = "," if results[ERRKEY] != "" else ""
            results[ERRKEY] += separator + str(e)

    def _sshdir_path(self, user):
        return '/root/.ssh/' if (user == 'root') else '/home/'+user+'/.ssh/'

    # Recursive validation of the input json.
    def _validate_json(self, domu, jconf, required_params):
        # If list, loop over each object in the list
        if isinstance (jconf, list):
	    #check for empty list
            if not jconf:
                raise ValueError ('*** Empty list provided in JSON structure %s and required params %s' %
                             (jconf, required_params))
 
            for conf in jconf:
                self._validate_json(domu, conf, required_params)
            return
        # IF not list, must be a dict type
        if (not isinstance (jconf, dict)):
            raise ValueError ('*** Inconsistency in JSON structure %s and required params %s' % 
                              (jconf, required_params))

        # Required params is a list of params which must be present in the input json
        # Each of the param may be a list by itself during recursion
        # e.g. To validate below JSON
        # { 
        #   "user": "...",
        #   "ssh_key": {
        #      "private":"..."
        #   }
        #   "remote_cluster": {
        #       "vms": [{"ip":"...",fdn":"..."},
        #               {"ip":"...","fdn":"..."}]
        #   }
        # }
        # use: required_params = ['user', ['ssh_key', 'private'], ['remote_cluster', ['vms', 'ip', 'fdn']]]
        for param in required_params:
            if isinstance (param, list):
                # If it's a list, first field is the top level subobject. 
                # Use it as a starting point and recurse through it
                if not param[0] in list(jconf.keys()):
                    raise ValueError ('*** Required parameter %s, not found in input JSON' % param[0])
                sub_jconf = jconf[param[0]]
                param.pop(0)
                self._validate_json(domu, sub_jconf, param)
            else: 
                # Just a regular field, verify it is present
                if not param in list(jconf.keys()):
                    raise ValueError ('*** Required parameter %s, not found in input JSON' % param)
                else:
                    if not jconf[param]:
                        raise ValueError ('*** Empty value provided for param %s in JSON' % param)

    # Method to add public key in authorized_keys. The remote cluster needs to be
    # setup with the corresponding private key with which it can connect to this cluster.
    def _configure_addpublickey(self, domu, jsonconf, results):
        required_params = ['users', ['ssh_key', 'public']]
        self._validate_json(domu, jsonconf, required_params)
        _users = jsonconf['users'].split(",")
        for user in _users:
            if(not self._user_exists(domu,user)):
                separator = "," if results[OUTKEY] != "" else ""
                out = 'Warning user ' + user + ' does not existing. skipping for this user'
                results[OUTKEY] += separator + out
            else:
                path_sshdir = self._sshdir_path(user)
                pub_key = jsonconf['ssh_key']['public'].rstrip()

                ebLogInfo ('*** Checking whether public key exists for DOM-U %s' % (domu))
                cmd  = 'grep -q -F "' + pub_key + '" ' 
                cmd += path_sshdir + '/authorized_keys 2> /dev/null'
                rc, o, e = self._execute_on_domu (cmd, domu)
                if rc == 0:
                    separator = "," if results[OUTKEY] != "" else ""
                    out = 'Public key already exists for %s in %s, skipping' % (domu, path_sshdir)
                    results[OUTKEY] += separator + out
                    return

                ebLogInfo ('*** Adding public key for user %s on  DOM-U %s to authorized keys under %s' % (user, domu, path_sshdir))
                cmd = 'echo "' + pub_key + '" >> ' 
                cmd += path_sshdir + '/authorized_keys 2> /dev/null'
                rc, o, e = self._execute_on_domu ("sh -c \'" + cmd + "\'", domu)
                if rc != 0:
                    separator = "," if results[ERRKEY] != "" else ""
                    results[ERRKEY] += separator + e
                    return

                separator = "," if results[OUTKEY] != "" else ""
                out = 'Successfully added public key for user %s on  DOM-U %s to authorized keys under %s' % (user, domu, path_sshdir)
                ebLogInfo('*** ' + out)
                results[OUTKEY] += separator + out

    # Method to store private key in the .ssh directory. The remote cluster needs to be
    # setup with the corresponding public key in its authorized_keys file.
    def _configure_storepvtkey(self, domu, jsonconf, results):
        required_params = ['users', ['ssh_key', 'private'], ['remote_cluster', ['vms', 'ip', 'fdn']]]
        self._validate_json(domu, jsonconf, required_params)
        _users = jsonconf['users'].split(",")
        for user in _users:
            if(not self._user_exists(domu,user)):
                separator = "," if results[OUTKEY] != "" else ""
                out = 'Warning user ' + user + ' does not existing. skipping for this user'
                results[OUTKEY] += separator + out
            else:
                path_sshdir = self._sshdir_path(user)
                vms = jsonconf['remote_cluster']['vms']
                pvt_key = jsonconf['ssh_key']['private'].rstrip()

                all_vms = set()
                for vmip in vms:
                    all_vms.add(vmip["fdn"])

                # This will replace any previous files. This is fine so long as the public key
                # associated with this pvt key is added to the remote cluster
                ebLogInfo ('*** Storing pvt keys for user %s on %s under %s for %d no. of vms' % (user, domu, path_sshdir, len(all_vms)))
                cmd = ""
                for vm in all_vms:
                    filename = path_sshdir +  '/id_rsa.' + vm
                    cmd += 'touch ' + filename +'; '
                    cmd += 'chmod 600 ' + filename + '; '
                    cmd += 'chown ' + user + ' ' + filename + '; '
                    cmd += 'echo "' + pvt_key + '" > ' + filename + ' 2> /dev/null' + '; '
                rc, o, e = self._execute_on_domu ("sh -c \'" + cmd + "\'", domu)
                if rc != 0:
                    separator = "," if results[ERRKEY] != "" else ""
                    results[ERRKEY] += separator + e
                    return

                out = 'Successully stored pvt keys for user %s on %s under %s for %d no. of vms' % (user, domu, path_sshdir, len(all_vms))
                ebLogInfo('*** ' + out)
                separator = "," if results[OUTKEY] != "" else ""
                results[OUTKEY] += separator + out

    # Method to add scanips of the remote cluster in /etc/hosts file
    def _configure_addscanips(self, domu, jsonconf, results):
        required_params = [['remote_cluster',['scannames','ip','name']]]
        self._validate_json(domu, jsonconf, required_params)

        remote_scanips = jsonconf['remote_cluster']['scannames']
        ebLogInfo ('*** Adding %d scan ips to /etc/hosts of %s' % (len(remote_scanips), domu))
        for scanip in remote_scanips:
            ip = scanip["ip"]
            scanname = scanip["name"]
            short = scanname.split('.')[0]
            entry = ip + ' ' + scanname + ' ' + short
            cmd = 'grep -q -F "' + entry + '" /etc/hosts 2> /dev/null'
            rc, o, e = self._execute_on_domu (cmd, domu)
            if rc == 0:
                out = 'Scan IP %s already exists on %s, skipping' % (ip, domu)
                ebLogInfo('*** ' + out)
                separator = "," if results[OUTKEY] != "" else ""
                results[OUTKEY] += separator + out
                continue
            cmd = 'echo "' + entry + '" >> /etc/hosts 2> /dev/null'
            rc, o, e = self._execute_on_domu ("sh -c \'" + cmd + "\'", domu)
            if rc != 0:
                separator = "," if results[ERRKEY] != "" else ""
                results[ERRKEY] += separator + e
                return
            out = 'Successfully added %d scan ips to /etc/hosts on %s' % (len(remote_scanips), domu)
            ebLogInfo('*** ' + out)
            separator = "," if results[OUTKEY] != "" else ""
            results[OUTKEY] += separator + out

    # Method to add ips of the remote domus in /etc/hosts file
    def _configure_addips(self, domu, jsonconf, results):
        required_params = [['remote_cluster', ['vms', 'ip', 'fdn']]]
        self._validate_json(domu, jsonconf, required_params)

        vms = jsonconf['remote_cluster']['vms']
        ebLogInfo ('*** Adding %d ips to /etc/hosts on %s' % (len(vms), domu))
        for vmip in vms:
            ip = vmip["ip"]
            fdn = vmip["fdn"]
            short = fdn.split('.')[0]
            entry = ip + ' ' + fdn + ' ' + short
            cmd = 'grep -q -F "' + entry + '" /etc/hosts 2> /dev/null'
            rc, o, e = self._execute_on_domu (cmd, domu)
            if rc == 0:
                out = 'IP %s already exists on %s, skipping' % (ip, domu)
                ebLogInfo('*** ' + out)
                separator = "," if results[OUTKEY] != "" else ""
                results[OUTKEY] += separator + out
                continue
            cmd = 'echo "' + entry + '" >> /etc/hosts 2> /dev/null'
            rc, o, e = self._execute_on_domu ("sh -c \'" + cmd + "\'", domu)
            if rc != 0:
                separator = "," if results[ERRKEY] != "" else ""
                results[ERRKEY] += separator + e
                return
            out = 'Successfully added %d ips to /etc/hosts on %s' % (len(vms), domu)
            ebLogInfo('*** ' + out)
            separator = "," if results[OUTKEY] != "" else ""
            results[OUTKEY] += separator + out
    
    #
    def _delscanips(self, domu, jsonconf, results):
        required_params = [['remote_cluster', ['scannames','ip','name']]]
        self._validate_json(domu, jsonconf, required_params)
        scannames = jsonconf['remote_cluster']['scannames']
        ebLogInfo ('*** removing %d scanip from /etc/hosts on %s' % (len(scannames), domu))
        hostfile = "/etc/hosts"
        tempfile = "/etc/hosts.bak." + datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        cmd = "cp" + " " + hostfile + " " +  tempfile
        rc, o, e = self._execute_on_domu (cmd, domu)
        for scan in scannames:
            ip = scan["ip"]
            fdn = scan["name"]
            short = fdn.split('.')[0]
            entry = ip + ' ' + fdn + ' ' + short
            cmd = 'grep -q -F "' + entry + '"' + " " + hostfile + " " + ' 2> /dev/null'
            rc, o, e = self._execute_on_domu (cmd, domu)
            if rc == 0:
                out = 'entry %s  exists on %s, deleting' % (entry, domu)
                ebLogInfo('*** ' + out)
                cmd = "sed -i '/" + entry + "/d'" + " " + hostfile 
                rc, o, e = self._execute_on_domu (cmd, domu)
                if rc != 0:
                    self._execute_on_domu("mv -f " + tempfile + " " + hostfile, domu)
                    separator = "," if results[ERRKEY] != "" else ""
                    results[ERRKEY] += separator + e
                    return
                out = 'Successfully deleted entry from %s on %s' % (hostfile, domu)
                separator = "," if results[OUTKEY] != "" else ""
                results[OUTKEY] += separator + out
        self._execute_on_domu("rm -f " + tempfile, domu);


    #
    def _delips(self, domu, jsonconf, results):
        required_params = [['remote_cluster', ['vms', 'ip', 'fdn']]]
        self._validate_json(domu, jsonconf, required_params)
        vms = jsonconf['remote_cluster']['vms']
        ebLogInfo ('*** removing %d ip from /etc/hosts on %s' % (len(vms), domu))
        hostfile = "/etc/hosts"
        tempfile = "/etc/hosts.bak." + datetime.now().strftime('%Y-%m-%d-%H:%M:%S')
        cmd = "cp" + " " + hostfile + " " +  tempfile
        rc, o, e = self._execute_on_domu (cmd, domu)
        for vm in vms:
            ip = vm["ip"]
            fdn = vm["fdn"]
            short = fdn.split('.')[0]
            entry = ip + ' ' + fdn + ' ' + short
            cmd = 'grep -q -F "' + entry + '"' + " " + hostfile + " " + ' 2> /dev/null'
            rc, o, e = self._execute_on_domu (cmd, domu)
            if rc == 0:
                out = 'entry %s  exists on %s, deleting' % (entry, domu)
                ebLogInfo('*** ' + out)
                cmd = "sed -i '/" + entry + "/d'" + " " + hostfile 
                rc, o, e = self._execute_on_domu (cmd, domu)
                if rc != 0:
                    self._execute_on_domu("mv -f " + tempfile + " " + hostfile, domu)
                    separator = "," if results[ERRKEY] != "" else ""
                    results[ERRKEY] += separator + e
                    return
                out = 'Successfully deleted entry from %s on %s' % (hostfile, domu)
                separator = "," if results[OUTKEY] != "" else ""
                results[OUTKEY] += separator + out
        self._execute_on_domu("rm -f " + tempfile, domu);

    # Method to delete private key in the .ssh directory. The remote cluster needs to be
    # 
    def _delpvtkey(self, domu, jsonconf, results):
        required_params = ['users',  ['remote_cluster', ['vms', 'ip', 'fdn']]]
        self._validate_json(domu, jsonconf, required_params)
        _users = jsonconf['users'].split(",")
        for user in _users:
            if(not self._user_exists(domu,user)):
                separator = "," if results[OUTKEY] != "" else ""
                out = 'Warning user ' + user + ' does not existing. skipping for this user'
                results[OUTKEY] += separator + out
            else:
                path_sshdir = self._sshdir_path(user)
                vms = jsonconf['remote_cluster']['vms']

                all_vms = set()
                for vm in vms:
                    all_vms.add(vm["fdn"])

                # This will replace any previous files. This is fine so long as the public key
                # associated with this pvt key is added to the remote cluster
                ebLogInfo ('*** deleting pvt keys for user %s on %s under %s for %d no. of vms' % (user, domu, path_sshdir, len(all_vms)))
                cmd = ""
                for vm in all_vms:
                    filename = path_sshdir +  '/id_rsa.' + vm
                    cmd = 'ls ' + filename
                    rc, o, e = self._execute_on_domu (cmd, domu)
                    if rc == 0:
                        cmd = 'rm -f ' + filename
                        rc, o, e = self._execute_on_domu (cmd, domu)
                        if rc != 0 :
                            separator = "," if results[ERRKEY] != "" else ""
                            results[ERRKEY] += separator + "Could not delete private key " + filename

                out = 'Deleted pvt keys for user %s on %s under %s for %d no. of vms' % (user, domu, path_sshdir, len(all_vms))
                ebLogInfo('*** ' + out)
                separator = "," if results[OUTKEY] != "" else ""
                results[OUTKEY] += separator + out

    #Method to add ips to ebtables
    def _configure_addiptoebt(self, domu, jsonconf, results):
        # Disabling eb tables - 
        self.__cluctrl.mEnableEbtablesOnDom0(aMode=False)
        # Leaving previous code for reference
            #required_params = [['remote_cluster', ['vms', 'ip', 'fdn'],['scannames','ip','name']]]
        #self._validate_json(domu, jsonconf, required_params)
        #remote_vms = jsonconf['remote_cluster']['vms']
        #remote_scans = jsonconf['remote_cluster']['scannames']
        #ips = ''
        #for scan in remote_scans:
        #    ips += "," + scan["ip"] 
        #for vm in remote_vms:
        #    ips += "," + vm["ip"] 
            #if 'observer' in jsonconf['remote_cluster'].keys():
            #    remote_observer = jsonconf['remote_cluster']['observer']
        #    for vm in remote_observer:
        #        ips += "," + vm["ip"] 
        #ips = ips.lstrip(",")
        #ebLogInfo('***Adding ips ' + ips + 'to ebtables')
        #tempoptions = self.__options
        #tempoptions.ip = ips
        #self.__cluctrl.mAddEbtablesRuleOnDom0(tempoptions)
        #separator = "," if results[OUTKEY] != "" else ""
        #results[OUTKEY] += separator + 'Successfully added ips to ebtables'

    # Method to check connectivity to the remote DG cluster
    def _verifyconn(self, domu, jsonconf, results):
        required_params = ['users', ['remote_cluster', ['vms', 'ip', 'fdn'],['scannames','ip','name']]]
        self._validate_json(domu, jsonconf, required_params)
        _users = jsonconf['users'].split(",")
        timeoutcounter = 0
        maxcounter = 1  #no of times ssh connectivity is tested
        if 'timeout_counter' in jsonconf:
            maxcounter = int(jsonconf['timeout_counter'])
            ebLogInfo('*** ' + 'setting maxcounter based on json, maxcounter:' + str(maxcounter));
        
        errorflag = True
        #Check if domu is up
        domu_node = exaBoxNode(get_gcontext())
        try:
            domu_node.mConnect(domu)
        except:
            err = 'Dom-U %s not connectable or not running' % (domu)
            ebLogError('*** ' + err)
            maxcounter = 0

        while (errorflag and (timeoutcounter < maxcounter)):
            errorflag = False
            ebLogInfo('*** ' + "retry count : " + str(timeoutcounter));
            for user in _users:
                if(not self._user_exists(domu,user)):
                    separator = "," if results[OUTKEY] != "" else ""
                    out = 'Warning user ' + user + ' does not existing. skipping for this user'
                    results[OUTKEY] += separator + out
                else:
                    vms = jsonconf['remote_cluster']['vms']
                    path_sshdir = self._sshdir_path(user)
                    ebLogInfo('*** Testing SSH connectivity to %d VMs for user %s from %s' % (len(vms), user, domu))
                    for vmip in vms:
                        fdn = vmip["fdn"]
                        filename = path_sshdir + '/id_rsa.' + fdn
                        cmd  = 'ssh -T -o StrictHostKeyChecking=no -oBatchMode=yes -o ConnectTimeout=20 -i '
                        cmd += filename + ' ' + user + '@' + fdn + ' "echo 2>&1"'
                        ebLogInfo('*** Using cmd %s to check remote connectivity' % cmd)
                        rc, o, e = self._execute_on_domu ("sh -c \'" + cmd + "\'", domu)
                        if rc != 0:
                            errorflag = True
                            #log the errors for 1st and last retries so that logs are not swamped
                            if timeoutcounter == 0 or timeoutcounter == maxcounter-1:
                                separator = "," if results[ERRKEY] != "" else ""
                                results[ERRKEY] += 'Error: SSH connectivity to %d VMs for user %s from %s is not working' % (len(vms), user, domu)
                        else:
                             out = 'SSH connectivity to %d VMs for user %s from %s is working' % (len(vms), user, domu)
                             ebLogInfo('*** ' + out)
                   
	    #current implementation requires 1521 port connectivity for scannames only. In future if vips need to be used, vips port must be checked for 1521 port connectivity
            scans = jsonconf['remote_cluster']['scannames']
            ports = [1521]
            ebLogInfo('*** Testing port connectivity to %d scan ips from %s' % (len(scans), domu))
            for scanips in scans:
                for port in ports:
                    scanip = scanips['ip']
                    cmd = '</dev/tcp/' + scanip + '/' + str(port) + ' && true || false'
                    cmd_html = '&lt/dev/tcp/' + scanip + '/' + str(port) + ' && true || false'
                    ebLogInfo('*** Using cmd %s to check connectivity for port %s' %(cmd_html, port))
                    rc, o, e = self._execute_on_domu (cmd, domu)
                    if rc != 0:
                        out = 'WARNING: port connectivity for port %s to %s ip  from %s is not setup (yet)' % (port, scanip, domu)
                        ebLogInfo('*** ' + out)
                    else:
                        out = 'port connectivity for port %s to %s ip  from %s is working' % (port, scanip, domu)
                        ebLogInfo('*** ' + out)

            if(errorflag) :
                time.sleep(60)
                timeoutcounter = timeoutcounter + 1

        if(errorflag):
            separator = "," if results[ERRKEY] != "" else ""
            results[ERRKEY] += "Error: Couldnt Verify Connectivity. Please check logs"
        else:
            separator = "," if results[OUTKEY] != "" else ""
            results[OUTKEY] += separator + "Success: Successfully verified connectivity"
            #flush errors
            results[ERRKEY] = ""

    # Method to invoke dataguard lifecycle operations
    def _invoke_lc_oper(self, domu, jsonconf, results, lcoper):
        required_params = ['user', 'dbname']
        self._validate_json(domu, jsonconf, required_params)

        user = jsonconf['user']
        dbname = jsonconf['dbname']
        cmd = "su - " + user + " -c "
        if (lcoper == "switchover"):
            cmd += '\'' + LC_SWITCHOVER % (dbname) + '\''
        elif (lcoper == "failover"):
            cmd += '\'' + LC_FAILOVER % (dbname) + '\''
        elif (lcoper == "reinstate"):
            cmd += '\'' + LC_REINSTATE % (dbname) + '\''
        elif (lcoper == "state"):
            cmd += '\'' + LC_STATE % (dbname) + '\''
        else:
            raise ValueError("Unrecognized Dadataguard lifecycle operation " + lcoper)

        ebLogInfo('*** Using cmd %s to start dataguard lifecycle operation %s ' % (cmd, lcoper))
        rc, o, e = self._execute_on_domu (cmd, domu)
        if rc != 0:
            separator = "," if results[ERRKEY] != "" else ""
            results[ERRKEY] += separator + e
            return

        # Get Job ID from the output
        id = self._lc_oper_id (domu, results, o)

        # Wait for the Job to complete
        self._lc_oper_wait (domu, results, user, id,dbname)



	
	    
       
    # Example output returned by dgasync command
    # - Keys which will be parsed is "id"
    # - Output may contain non-JSON data, use tags to fetch JSON content
    #     <json begin>{"id":"8"}<json end>
    def _lc_oper_id (self, domu, results, out):
        # Exception, if any, will be caught by the caller.
        json_str = re.search('<json begin>(.*)<json end>', out).group(1)
        json_obj = json.loads(json_str)
        if (not "id" in list(json_obj.keys())):
            raise ValueError ("id field not found in the json returned by dgasync: " + out)
        return json_obj["id"]
    
    # Method to get result of a previously invoked dataguard lifecycle operation
    # There is no timeout in this method. It will exit in following cases:
    # - dgasync command invocation fails 
    # - dgasync command doesn't return correct JSON
    # - dgasync command returns SUCCESS or FAILURE
    # Example output returned by dgasync command
    # - Keys which will be parsed are "status", "msg", "errmsg"
    # - Output may contain non-JSON data too, e.g. ("Initializing registry..."), use tags to fetch JSON content
    #     Initializing registry in backwards compatiblity mode...[done]
    #     <json begin>{"msg":"","status":"FAILED","ts":"1472527783","err":"-1","errmsg":"All Standby Database \
    #     instances are down or not reachable","action":"switchover","module":"async_dg"}<json end>
    def _lc_oper_wait(self, domu, results, user, id, dbname):
        cmd = "su - " + user + " -c "
        cmd += '\'' + LC_GETRESULT % (dbname, id) + '\''
        while True:
            ebLogInfo('*** Using cmd %s to get result of the dataguard lifecycle operation' % cmd)
            rc, o, e = self._execute_on_domu (cmd, domu)
            if rc != 0:
                separator = "," if results[ERRKEY] != "" else ""
                results[ERRKEY] += separator + e
                return
            # Look for status field in the output JSON.
            # Exception, if any, will be caught by the caller.
            json_str = re.search('<json begin>(.*)<json end>', o).group(1)
            json_obj = json.loads(json_str)
            if (not "status" in list(json_obj.keys())):
                raise ValueError ("status field not found in the json returned by dgasync: " + json_str)
            status = json_obj["status"]
            ebLogInfo('*** dgasync operation %s has status: %s' % (id, status))
            if ("FAILED" in status):
                err = "<json begin>" + json_str + "<json end>"
                separator = "," if results[ERRKEY] != "" else ""
                results[ERRKEY] += separator + err
                return
            elif ("SUCCESS" in status):
                out = "<json begin>" + json_str + "<json end>"
                separator = "," if results[OUTKEY] != "" else ""
                results[OUTKEY] += separator + out
                return
            # Status is not success or failure, assume operation to be in progress.
            # Sleep for a minute before next attempt.
            time.sleep(60)

    #Method to check if connectivity between two clusters are required
    def _is_connectivity_required(self, domu, jsonconf, results):
        required_params = [['remote_cluster', 'id']]
        self._validate_json(domu, jsonconf, required_params)
        id = jsonconf['remote_cluster']['id']
        cmd = "/var/opt/oracle/ocde/rops is_connection_required " + id
        ebLogInfo('*** executing cmd: %s' %(cmd))
        rc, o, e = self._execute_on_domu (cmd, domu)
        if rc != 0:
            separator = "," if results[ERRKEY] != "" else ""
            results[ERRKEY] += separator + e + "Could not determine if connection is required"
            return
        if "<yes>" in o:
            results[OUTKEY] = "<connection is required>";
            return
        elif "<no>" in o:
            results[OUTKEY] = "<connection is not required>";
            return 
        else:
            separator = "," if results[ERRKEY] != "" else ""
            results[ERRKEY] += separator + e + "Could not determine if connection is required"
            return

    def _execute_on_domu(self, cmd, domu):
        domu_node = exaBoxNode(get_gcontext())
        try:
            domu_node.mConnect(domu)
        except:
            err = 'Dom-U %s not connectable or not running' % (domu)
            ebLogError('*** ' + err)
            return -1, "", err
        i, o, e = domu_node.mExecuteCmd(cmd)
        outlines = o.readlines()
        errlines = e.readlines()
        out = ""
        if (outlines is not None and len(outlines) != 0):
            out = out.join(outlines)
        err = ""
        if (errlines is not None and len(errlines) != 0):
            err = err.join(errlines)

        rc = domu_node.mGetCmdExitStatus()
        if (rc != 0 and err != ""):
            ebLogError('*** ' + err)

        return rc, out, err
    
    #method to check if user exists
    def _user_exists(self, domu, user):
        cmd = "id -u " + user
        rc, o, e = self._execute_on_domu (cmd, domu)
        return not rc
    
	    
# End of file
