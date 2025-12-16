"""
 Copyright (c) 2019, 2025, Oracle and/or its affiliates.

NAME:
    ImageManagementEndpoint - Basic functionality

FUNCTION:
    Wrapper for image management commands execution

NOTE:
    None

History:
    cagaray     03/04/2025 - 37787638: make post operations async
    cagaray     03/03/2025 - Bug#34807833: redownload operation and optional payload for list
    rbehl       02/12/2019 - Bug#30243322: remoteec restart imagemgmt
    oerincon    25/06/2019 - File Creation
"""

from exabox.managment.src.AsyncTrackEndpoint import AsyncTrackEndpoint
import os
import tempfile
import subprocess
import base64
import json
from socket import getfqdn

class ImageManagementEndpoint(AsyncTrackEndpoint):

    def __init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData):

        # Initialization of the base class
        AsyncTrackEndpoint.__init__(self, aHttpUrlArgs, aHttpBody, aHttpResponse, aSharedData)

        self.__install_dir = self.mGetConfig().mGetConfigValue('install_dir')

    def mPost(self):

        if self.__install_dir is None or not os.path.isdir(self.__install_dir):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'install_dir key is missing or pointing to an invalid directory. ' \
                                           'Please review exacloud/exabox/managment/config/basic.conf'
            return

        # Production path
        __download_sh_path = os.path.join(self.__install_dir, 'imagemgmt', 'bin', 'download.sh')
        __manual_operation_path = os.path.join(self.__install_dir, 'imagemgmt', 'bin', 'manual_operation.sh')
        # Development path
        # __download_sh_path = os.path.join(self.__install_dir, 'imagemgmt', 'shipdownload', 'bin', 'download.sh')
        if not os.path.isfile(__download_sh_path):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = '{0} is an invalid filepath. Please review ' \
                                           'exacloud/exabox/managment/config/basic.conf'.format(__download_sh_path)
            return

        if not os.path.isfile(__manual_operation_path):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = '{0} is an invalid filepath. Please review ' \
                                           'exacloud/exabox/managment/config/basic.conf'.format(__manual_operation_path)
            return

        # Check whether this validation is really needed
        __op = self.mGetBody()['op']
        if __op is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'op is a required parameter.'
            return

        # JSON payload will come as a base64 encoded string.
        if not 'payload' in self.mGetBody() or self.mGetBody()['payload'] is None:
            __payload = b'{}'
        else:
            try:
                __payload = base64.b64decode(self.mGetBody()['payload'])
            except Exception as e:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Error decoding payload: {0}'.format(e)
                return

        # Log decoded payload
        self.mGetLog().mInfo('Image management received payload:\n {0}'.format(__payload.decode('utf8')))

        if __op == "list":
            with tempfile.NamedTemporaryFile() as __payload_file:
                __payload_file.write(__payload)
                __payload_file.flush()
                __cmd_to_exec = [__download_sh_path, __op, __payload_file.name]
                __rc, __stdout, __stderr = self.mBashExecution(__cmd_to_exec, subprocess.PIPE) 

            # Failure
            if __rc != 0:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Error executing image management download.sh {0} {1}'.format(__stdout, __stderr)
                return

            # Success
            # Preprocess the output to remove well-known tags so return value is just JSON
            __result = __stdout
            
            __start_tag = '----START-JSON-DATA----'
            __start_tag_index = __result.find(__start_tag)
            if __start_tag_index >= 0:
                __result = __result[__start_tag_index + len(__start_tag):]

            __end_tag = '----END-JSON-DATA----'
            __end_tag_index = __result.find(__end_tag)
            if __end_tag_index >= 0:
                __result = __result[:__end_tag_index]

            # Convert to JSON on a best-effort basis
            try:
                __result = json.loads(__result)
            except ValueError as e:
                # This is not JSON, return value as-is
                pass
            self.mGetResponse()['text'] = __result

        elif __op == "download_status":
            try:
                __payload_json = json.loads(__payload)
            except ValueError as e:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Payload sent is not a proper json {0}'.format(e)
                return

            try: 
                __bptype = __payload_json['bptype'].replace("-bundlepatch","")
                __bpname = __payload_json['bpname']
                __bpdate = __payload_json['bpdate']
            except KeyError as e:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Missing key from details json {0}'.format(e)
                return

            __dwld_prop_path = f"{self.__install_dir}/imagemgmt/config/download.properties"
            try:
                __dwld_prop = self._mLoadProperties(__dwld_prop_path)
            except FileNotFoundError as e:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'download.properties file does not exist in path {0} : {1}'.format(__dwld_prop_path, e)
                return
            except Exception as e: 
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'error when loading download.properties file {0} : {1}'.format(__dwld_prop_path, e)
                return 
            
            try:
                __dwld_location = __dwld_prop['image.location']
            except Exception as e:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'download.properties file does not include image.location property {0}'.format(e)
                return

            __base_uri = f"{__bpname}_{__bpdate}"
            __status_dir = f"{__dwld_location}{__bptype}/{__base_uri}/"
            __status_path = os.path.join(__status_dir, 'status.json')
            
            try:
                with open(__status_path, 'r') as f:
                    __status_json = f.read()
            except FileNotFoundError:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Status json {0} does not exist, If a download is in progress please wait, ' \
                                                'otherwise verify bpname and bpdate sent are correct.'.format(__status_path)
                return

            # Convert to JSON on a best-effort basis
            try:
                __status_json = json.loads(__status_json)
            except ValueError as e:
                # This is not JSON, return value as-is
                pass

            self.mGetResponse()['text'] = __status_json

        elif __op in ["download", "redownload", "delete"]:
            __ocps_setup_json = self.mGetConfig().mGetConfigValue("ecra_token")
            if __ocps_setup_json == "":
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Error obtaining ocpsSetup.json file '
            self.mGetLog().mInfo(f"manual_operation.sh will be called with ocpsSetup.json:{__ocps_setup_json}")
            with tempfile.NamedTemporaryFile(delete=False) as __payload_file:
                __payload_file.write(__payload)
                __payload_file.flush()
                __cmd_to_exec = [__manual_operation_path, __op, __ocps_setup_json, __payload_file.name]
                self.mGetResponse()['text'] = self.mCreateBashProcess([__cmd_to_exec], aName="execute [{0}]".format(__cmd_to_exec), aOnFinish=self._mRemoveDetailsFile, aOnFinishArgs=[__payload_file.name])
                return
        else: 
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Operation {0} is not permited'.format(__op)


    def mPut(self):

        if self.__install_dir is None or not os.path.isdir(self.__install_dir):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'install_dir key is missing or pointing to an invalid directory. ' \
                                           'Please review exacloud/exabox/managment/config/basic.conf'
            return

        __op = self.mGetBody()['op']

        if __op == "walletupdate":
            self._mUpdateWallet()
        else:        
            __cmd_to_exec = ['sudo', 'systemctl', __op, 'imagemgmt']
            __rc, __stdout, __stderr = self.mBashExecution(__cmd_to_exec, subprocess.PIPE)

            # Failure
            if __rc != 0:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Error executing image management {0} {1}'.format(__stdout, __stderr)
                return
            # Success
            self.mGetResponse()['text'] = __stdout

    def _mRemoveDetailsFile(self, filepath):
        """
          On finish callback for download, delete, redownload operations.
        """
        if os.path.isfile(filepath):
            os.remove(filepath)

    def _mLoadProperties(self, filepath, sep='=', comment_char='#'):
        """
        Read the file passed as parameter as a properties file.
        """
        props = {}
        with open(filepath, "rt") as f:
            for line in f:
                l = line.strip()
                if l and not l.startswith(comment_char):
                    key_value = l.split(sep)
                    key = key_value[0].strip()
                    value = sep.join(key_value[1:]).strip().strip('"')
                    props[key] = value
        return props

    def _mUpdateWallet(self):

        # Production path
        __wallet_path = os.path.join(self.__install_dir, 'imagemgmt', 'config')
        if not os.path.isdir(__wallet_path):
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = '{0} is an invalid config path for ImgMgmt. Please review ' \
                                        'exacloud/exabox/managment/config/basic.conf'.format(__wallet_path)
            return 

        #Check If payload(wallet file) is passed (or) not. If not return with error.
        if not 'payload' in self.mGetBody() or self.mGetBody()['payload'] is None:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Please pass wallet file to update.'
            return

        # Check for the actual file existence. If file is there take backup before replacing.
        __wallet_file = os.path.join(__wallet_path, "cwallet.sso")
        backupFile = False
        if os.path.isfile(__wallet_file):
            __bkupwalletfile = "{}{}".format(__wallet_file, ".BKUP")
            __backupcmd = ["sudo", "cp", "-p", __wallet_file, __bkupwalletfile]
            self.mGetLog().mInfo('command to take wallet backup ::  {0}'.format(__backupcmd))
            __rc, __stdout, __stderr = self.mBashExecution(__backupcmd, subprocess.PIPE)
            backupFile = True
            if __rc != 0:
                self.mGetResponse()['status'] = 500
                self.mGetResponse()['error'] = 'Error executing image management {0} {1}'.format(__stdout, __stderr)
                return

        #Decode the payload
        try:
            __payload = base64.b64decode(self.mGetBody()['payload'])
        except Exception as e:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error decoding payload: {0}'.format(e)
            return

        #Replace the wallet now.
        try:
            with tempfile.NamedTemporaryFile() as __payload_file:
                __payload_file.write(__payload)
                __payload_file.flush()
                __updatecmd = ["sudo", "cp", "-p", __payload_file.name, __wallet_file]
                self.mGetLog().mInfo("locally created payload file name :: {0}".format(__payload_file.name))
                self.mGetLog().mInfo("wallet file to be replaced :: {0}".format(__wallet_file))
                __rc, __stdout, __stderr = self.mBashExecution(__updatecmd, subprocess.PIPE)
                if __rc != 0:
                    self.mGetResponse()['status'] = 500
                    self.mGetResponse()['error'] = 'Error updating the download wallet {0} {1}'.format(__stdout, __stderr)
                    return
                chngperms = ["sudo", "chmod", "555", __wallet_file]
                __rc, __stdout, __stderr = self.mBashExecution(chngperms, subprocess.PIPE)
                if __rc != 0:
                    self.mGetResponse()['status'] = 500
                    self.mGetResponse()['error'] = 'Error updating the download wallet {0} {1}'.format(__stdout, __stderr)
                    return

                self.mGetLog().mInfo("updating the wallet in the current host is successful")

        except Exception as e:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error updating the download wallet in primary host {0} '.format(e)
            return

        #Now sync this wallet to the standby host.
        try:
            _remoteCpsHost = self.mGetConfig().mGetExacloudConfigValue("remote_cps_host")
            if _remoteCpsHost:
                filesToSync = [__wallet_file]
                if backupFile == True:
                    __wallet_bkup = __wallet_file + ".BKUP"
                    filesToSync.append(__wallet_bkup)
                for wallet in filesToSync:
                    __stby_walletpath = _remoteCpsHost + ":" + wallet
                    __sync_walletcmd = ["/bin/rsync", "-a", __wallet_file, __stby_walletpath]
                    __rc, __stdout, __stderr = self.mBashExecution(__sync_walletcmd, subprocess.PIPE)
                    if __rc != 0:
                        self.mGetResponse()['status'] = 500
                        self.mGetResponse()['error'] = 'Error in syncing the updated wallet to the standby cps host {} ::' \
                                                    '{0} {1}'.format(_remoteCpsHost, __stdout, __stderr)
                        return
        except Exception as e:
            self.mGetResponse()['status'] = 500
            self.mGetResponse()['error'] = 'Error in syncing the updated download wallet from primary to standy cps {0}'.format(e)
            return
        #If we reach heare which means success.
        self.mGetResponse()['text'] = "Updation of wallet is successful."
