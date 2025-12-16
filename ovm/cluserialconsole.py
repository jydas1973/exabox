#!/usr/bin/env python
#
# $Header: ecs/exacloud/exabox/ovm/cluserialconsole.py /main/16 2025/12/02 17:57:52 ririgoye Exp $
#
# cluserialconsole.py
#
# Copyright (c) 2021, 2025, Oracle and/or its affiliates.
#
#    NAME
#      serialConsole - Implementation layer for the Serial Console
#
#    DESCRIPTION
#      Provide basic/core API for serial console (History Console, ...)
#
#    NOTES
#      NONE
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    11/26/25 - Bug 38636333 - EXACLOUD PYTHON:ADD INSTANTCLIENT TO
#                           LD_LIBRARY_PATH
#    gsundara    11/14/25 - Bug 38611140 - EXADB-XS:VM MOVE CORRUPTS THE
#                           EXISTING SSH_CLIENT_KEY.PUB UNDER READ-QEMU LEADING
#                           TO FAILURES ON SERIAL CONSOLE
#    gojoseph    11/27/24 - Bug 37295953 Raise exception when container is not
#                           running while console_history operation
#    pbellary    11/16/23 - Bug 36002676 - EXACC:22.3.1.4.0:SERIAL CONSOLE: CLOUD SHELL CONNECTION FAILED: FAILED TO ESTABLISH SSH SESSION
#    pbellary    10/16/23 - Enh 35900619 - VM CONSOLE - EXACLOUD NEED TO SEND DIFFERENT ERROR CODE TO ECRA 
#                           IN CASE CPS/EXACLOUD FAILS TO UPLOAD HISTORY CONSOLE DUE CUSTOMER BLOCKING (OR BAD NETWORK) TO OBJECT STORAGE
#    pbellary    08/25/23 - Bug 35737837 - EXACS:23.4.1:X9M:MULTI-VM:ADBD PROVISIONING FAILING AT CREATE VM
#                           STEP:ERROR - 6153 - UNABLE TO REMOVE STALE DUMMY BRIDGE VMETH200
#    pbellary    06/20/23 - Bug 35517983 - SERIAL CONSOLE: HISTORY CONSOLE RESPONSE FAILING WITH ERROR: BYTES IS NOT JSON SERIALIZABLE 
#    jesandov    05/26/23 - 35426500: Change mGetEntryClass() by
#                           mBuildExaKmsEntry()
#    dsaes       05/03/23 - BUG 35354868 - VM CONSOLE - MAKE CHANGES AT
#                           EXA-HIPPO-SERIALMUX TO ALWAYS SUPPORT QEMU GOING
#                           DOWN IN CERTAIN OPERATIONS
#    joysjose    04/13/23 - Bug 35285505 - ADD COMPUTE FAILING WITH
#                           ATTRIBUTEERROR: 'EXAKMSOCI' OBJECT HAS NO ATTRIBUTE
#                           'MBUILDEXAKMSENTRY' fix
#    enrivera    04/12/23 - Bug 35280016 - VM SERIAL CONSOLE - EXACLOUD TO PROVIDE ENV VARIABLE TO DISTINGUISH BETWEEN XEN AND KVM ENVS IN DOM0 APPLICATION 
#    pbellary    12/08/22 - Creation
#
from exabox.core.Node import exaBoxNode
from exabox.core.Context import get_gcontext
from exabox.core.DBStore import ebGetDefaultDB
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from exabox.core.Error import ebError, ExacloudRuntimeError, gNetworkError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.exaoci.connectors.OCIConnector import OCIConnector
from exabox.exaoci.connectors.UserConnector import UserConnector
from exabox.exaoci.connectors.ResourceConnector import ResourceConnector
from exabox.ovm.cluencryption import RSAEncryption, SymmetricEncryption

import os, time, sys, io, json, traceback, oci
from tempfile import NamedTemporaryFile
from base64 import b64encode

class serialConsole(object):

    def __init__(self, aCluCtrlObj, aOptions):

        self.__cluctrl = aCluCtrlObj
        self.__options = aOptions
        self.__objectStorage = None

    def mGetConnectorType(self) -> str:
        return self.__cluctrl.mCheckConfigOption('exacc_auth_principals')

    def mUpdateRequestData(self, aDataD):
        _data_d = aDataD
        _reqobj = self.__cluctrl.mGetRequestObj()
        if _reqobj is not None:
            _reqobj.mSetData(json.dumps(_data_d))
            _db = ebGetDefaultDB()
            _db.mUpdateRequest(_reqobj)

    def mObjectStoreInit(self) -> None:
        """ Initializes the object storage client
        """
        _ebox = self.__cluctrl
        _ociexacc  = _ebox.mIsOciEXACC()
        if _ociexacc:
            _connector_type = self.mGetConnectorType()
            if _connector_type == "UserPrincipals":
                _factory = ExaOCIFactory(UserConnector())
            elif _connector_type == "ResourcePrincipals":
                _factory = ExaOCIFactory(ResourceConnector())
        else:
            _factory = ExaOCIFactory()

        # Create an OCI Object Storage client
        self.__objectStorage = _factory.get_object_storage_client()

    def mUploadFile(self, aNamespace, aBucket, aObjectName, aDirectory, aFileName):
        """ Upload a file to object store
        """
        _namespace = aNamespace
        _bucket = aBucket
        _object_name = aObjectName
        _dir = aDirectory
        _file = aFileName

        try:
            if not self.__objectStorage:
                #Initialize the object store
                self.mObjectStoreInit()

            _response = self.__objectStorage.put_object(namespace_name=_namespace, bucket_name=_bucket, object_name=_object_name,
                                                        put_object_body=io.open(os.path.join(_dir, _file), 'rb'))
            ebLogInfo(_response.headers)
        except oci.exceptions.RequestException as err:
            """
                HTTP Status Code: 
                           408: request_timeout, timeout
                           504: gateway_timeout
            """
            _detail_error = f"oci.exceptions.RequestException: Failed to upload {_object_name} to object storage {sys.exc_info()[1:2]}{err}"
            ebLogError(_detail_error)
            if err and hasattr(err, "response") and err.response and hasattr(err.response, "status_code") and err.response.status_code in [ 408, 504 ]:
                self.__cluctrl.mUpdateErrorObject(gNetworkError['ERROR_UPLOAD_FAILED'], _detail_error)
            raise ExacloudRuntimeError(0x0818, 0xA, _detail_error)
        except oci.exceptions.ServiceError as err:
            """
                HTTP Status Code: 
                           408: request_timeout, timeout
                           504: gateway_timeout
            """
            _detail_error = f"oci.exceptions.ServiceError: Failed to upload {_object_name} to object storage {sys.exc_info()[1:2]}{err}"
            ebLogError(_detail_error)
            if err and hasattr(err, "status") and err.status in [ 408, 504 ]:
                self.__cluctrl.mUpdateErrorObject(gNetworkError['ERROR_UPLOAD_FAILED'], _detail_error)
            raise ExacloudRuntimeError(0x0818, 0xA, _detail_error)
        except Exception as err:
            _detail_error = f"Exception: Failed to upload {_object_name} to object storage {sys.exc_info()[1:2]}{err}"
            ebLogError(_detail_error)
            raise ExacloudRuntimeError(0x0818, 0xA, _detail_error)

        return _response

    def mGetObject(self, aNamespace, aBucket, aObjectName):
        """ Fetch an object from object store
        """
        _namespace = aNamespace
        _bucket = aBucket
        _object_name = aObjectName
        try:
            if not self.__objectStorage:
                #Initialize the object store
                self.mObjectStoreInit()

            return self.__objectStorage.get_object(_namespace, _bucket, _object_name)
        except Exception as e:
            return str(e)

    def mEncryptFile(self, aFileName, aPubKey):
        """ Encrypt File using client public key
        """
        _file = aFileName
        _public_key = aPubKey
        _encrypted_file = None

        with open(_file, "rb") as _fp:
            _data = _fp.read()

        #Exacloud generates a symmetric key which will be used to encrypt history console data & upload to the object store
        #Exacloud encryptes the symmetric key using the public key provided by ECRA & sends back this encrypted key to CP via ECRA.
        _rsa_obj = RSAEncryption()
        _rsa_obj.mLoadPublicKey(_public_key)

        _symmetric_obj = SymmetricEncryption()
        _symmetric_key = _symmetric_obj.mGetKey()
        _encrypted_symmetric_key = _rsa_obj.mEncryptKey(_symmetric_key)

        _encrypted_data = _symmetric_obj.mEncrypt(_data)

        _encrypted_file = _file + ".enc"
        with open(_encrypted_file, "wb") as _fp:
            _fp.write(_encrypted_data.encode("utf-8"))

        return _encrypted_file, _encrypted_symmetric_key

    def mListObject(self, aNamespace, aBucket, aObjectPrefix=None):
        """ List objects from the object store
        """
        _namespace = aNamespace
        _bucket = aBucket
        _obj_name_prefix = aObjectPrefix
        try:
            if not self.__objectStorage:
                #Initialize the object store
                self.mObjectStoreInit()

            if _obj_name_prefix:
                _objects = json.loads(str(self.__objectStorage.list_objects(_namespace, _bucket, prefix=_obj_name_prefix).data))['objects']
            else:
                _objects = json.loads(str(self.__objectStorage.list_objects(_namespace, _bucket).data))['objects']

            return _objects

        except Exception as e:
            _err_msg = "Failed to list objects!\n{0}".format(e)
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg)

    def mCreateQemuDirs(self, aDom0, aDomU):
        """ Create read-qemu & write-qemu dirs in /EXAVMIMAGES/GuestImages folder
        """
        _dom0 = aDom0
        _domU = aDomU

        _read_qemu = f"/EXAVMIMAGES/GuestImages/{_domU}/console/read-qemu/"
        _write_qemu = f"/EXAVMIMAGES/GuestImages/{_domU}/console/write-qemu/"

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost = _dom0)

        if _node.mFileExists(_read_qemu) is False:
            _cmd_str = f"/bin/mkdir -p {_read_qemu}"
            _node.mExecuteCmdLog(_cmd_str)
            _rc = _node.mGetCmdExitStatus()
            if _rc != 0:
                ebLogWarn(f'*** read qemu path {_read_qemu} creation failed ***')
                _node.mDisconnect()
                return
            ebLogInfo(f"*** read qemu path {_read_qemu} created successfully..")

        if _node.mFileExists(_read_qemu) is False:
            _cmd_str = f"/bin/mkdir -p {_write_qemu}"
            _node.mExecuteCmdLog(_cmd_str)
            _rc = _node.mGetCmdExitStatus()
            if _rc != 0:
                ebLogWarn(f'*** write qemu path {_write_qemu} creation failed ***')
                _node.mDisconnect()
                return
            ebLogInfo(f"*** write qemu path {_write_qemu} created successfully..")

        _node.mDisconnect()

    def mCopyFile(self, aDom0, aLocalFile, aRemoteFile):
        """ Copy File to remote node
        """
        _dom0 = aDom0
        try:
            _remote_dir = os.path.dirname(aRemoteFile)
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            if _node.mFileExists(_remote_dir):
                _node.mCopyFile(aLocalFile, aRemoteFile)
                _node.mExecuteCmdLog(f"/usr/bin/chmod 600 {aRemoteFile}")
            else:
                ebLogError(f"*** Failed to copy {aLocalFile} to dom0:{_dom0}  {_remote_dir} directory not exists")
        except Exception as e:
            ebLogError(f"*** Failed to copy {aLocalFile} to dom0:{_dom0} at location:{aRemoteFile}, ERROR: {e}")
        finally:
            _node.mDisconnect()
    
    def mCopyFakeKey(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU

        _client_key = f"/EXAVMIMAGES/GuestImages/{_domU}/console/read-qemu/ssh_client_key.pub"
        _read_qemu = f"/EXAVMIMAGES/GuestImages/{_domU}/console/read-qemu/"
        _remotefile = _read_qemu + "ssh_client_key.pub"

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            #Remove the client public key
            if _node.mFileExists(_remotefile):
                _cmd_str = f"/bin/rm -rf {_client_key}"
                _node.mExecuteCmdLog(_cmd_str)
        finally:
            _node.mDisconnect()

        #Generate Temporary key
        _exakms = get_gcontext().mGetExaKms()
        _dummyEntry = _exakms.mBuildExaKmsEntry("dummy", 'root',_exakms.mGetEntryClass().mGeneratePrivateKey())
        _fake_key = _dummyEntry.mGetPublicKey("TEMPORAL_KEY")

        #Copy the fake public key
        with NamedTemporaryFile(delete=False) as _tmp_file:
            _tmp_file.write(_fake_key.encode('utf8'))
            _tmp_file.close()
            self.mCopyFile(_dom0, _tmp_file.name, _remotefile)
            os.unlink(_tmp_file.name)

    def mCheckDockerImages(self, aDom0, aOLVersion):
        _dom0 = aDom0
        _cmd_str = ""
        _OLVersion = aOLVersion
        _exists = False

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)

            if _OLVersion == "OL7":
                _cmd_str = "timeout 30s docker images | egrep 'exa-hippo-serialmux|exa-hippo-sshd'"
            elif _OLVersion == "OL8":
                _cmd_str = "timeout 30s podman images | egrep 'exa-hippo-serialmux|exa-hippo-sshd'"

            if _cmd_str:
                _node.mExecuteCmdLog(_cmd_str)
                _rc = _node.mGetCmdExitStatus()
                if _rc != 0:
                    ebLogWarn(f'*** {_cmd_str} failed.. ***')
                    _exists = False
                else:
                    ebLogInfo(f"Docker images 'exa-hippo-serialmux|exa-hippo-sshd' are existing on dom0:{_dom0}")
                    _exists = True
        finally:
            _node.mDisconnect()
        return _exists

    def mCheckContainerStatus(self, aDom0, aDomU, aOLVersion):
        _dom0 = aDom0
        _domU = aDomU
        _OLVersion = aOLVersion
        _cmd_str = ""
        _running = False

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            _hostname = _domU.split('.')[0]

            if _OLVersion == "OL7":
                _cmd_str = f"timeout 30s docker ps | egrep '{_hostname}-serialmux|{_hostname}-sshd'"
            elif _OLVersion == "OL8":
                _cmd_str = f"timeout 30s podman ps | egrep '{_hostname}-serialmux|{_hostname}-sshd'"

            if _cmd_str:
                _node.mExecuteCmdLog(_cmd_str)
                _rc = _node.mGetCmdExitStatus()
                if _rc != 0:
                    ebLogWarn(f'*** {_cmd_str} failed.. ***')
                    _running = False
                else:
                    ebLogInfo(f"Docker containers '{_hostname}-serialmux|{_hostname}-sshd' are running on dom0:{_dom0}")
                    _running = True
        finally:
            _node.mDisconnect()
        return _running

    def mCopyContainerTemplate(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _ebox = self.__cluctrl
        _remotefile = "/opt/exacloud/vmconsole/container_template.json"
        _path = f"/log/serialConsole/{_domU}/"
        _dir = _ebox.mGetBasePath() + _path
        if not os.path.exists(_dir):
            os.makedirs(_dir)

        try:
            _local_path = _dir + "/" + "container_template.json"
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            if _node.mFileExists(_remotefile):
                _node.mCopy2Local(_remotefile, _local_path)
            else:
                _local_path = None
        except:
            ebLogWarn('*** Can not access/read container_template.json file')
            _local_path = None
        finally:
            _node.mDisconnect()
        return _local_path

    def mPrepareContainerCommands(self, aDom0, aDomU, aOLVersion):
        _dom0 = aDom0
        _domU = aDomU
        _OLVersion = aOLVersion
        _ebox = self.__cluctrl

        _path = f"/log/serialConsole/{_domU}/"
        _dir = _ebox.mGetBasePath() + _path
        if not os.path.exists(_dir):
            os.makedirs(_dir)

        with open(_dir + "container_template.json") as fd:
            _d = json.load(fd)

        def _prepare_commands(aDomU, aOLVersion, aCmdType):
            _domU = aDomU
            _OLVersion = aOLVersion
            _cmd_type = aCmdType
            run_options = ["timeout 30s"]
            _hostname = _domU.split('.')[0]
            if _OLVersion == "OL7" and _cmd_type == "sshd":
                run_options.extend(["docker", "run"])
                _options = _d["docker_run_options_sshd"]
            elif _OLVersion == "OL7" and _cmd_type == "serialmux":
                run_options.extend(["docker", "run"])
                _options = _d["docker_run_options_serialmux"]
            elif _OLVersion == "OL8" and _cmd_type == "sshd":
                run_options.extend(["podman", "run"])
                _options = _d["podman_run_options_sshd"]
            elif _OLVersion == "OL8" and _cmd_type == "serialmux":
                run_options.extend(["podman", "run"])
                _options = _d["podman_run_options_serialmux"]

            if _options.get("detached"):
                run_options.append("-d")
            if _options.get("tty"):
                run_options.append("-t")
                run_options.extend([
                    "--security-opt={}".format(_options["security_options"]),
                    "--memory={}".format(_options["memory"]),
                    "--cpus={}".format(_options["cpus"]),
                    "--pids-limit={}".format(_options["pids_limit"]),
                    "--restart={}".format(_options["restart"]),])
            if _options.get("network"):
                run_options.extend(["--network={}".format(_options["network"])])
            for log_opt in _options.get("log_options", {}).items():
                run_options.extend(["--log-opt", "{}={}".format(*log_opt)])
            for _volume in _options.get("volumes", []):
                run_options.extend([
                    "-v",
                    "{}:{}{}".format(_volume["src"], _volume["dst"], ":ro" if _volume.get("read_only") else "").replace("{_domU}", _domU)])
            run_options.extend([
                "--name", _options["name"].replace("{_hostname}", _hostname),
                "--hostname", _options["hostname"].replace("{_hostname}", _hostname),
                _options["image"]])
            return run_options

        _cmd_list = []
        _run_options_sshd = _prepare_commands(_domU, _OLVersion, "sshd")
        if _run_options_sshd:
            _cmd_str = ' '.join(_sshd_options for _sshd_options in _run_options_sshd)
            _cmd_list.append(_cmd_str)

        _run_options_serialmux = _prepare_commands(_domU, _OLVersion, "serialmux")
        if _run_options_serialmux:
            _cmd_str = ' '.join(_serialmux_options for _serialmux_options in _run_options_serialmux)
            _cmd_list.append(_cmd_str)

        return _cmd_list

    def mRunContainer(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _cmd_str = ""
        _cmd_list = []

        _ebox = self.__cluctrl
        _OLVersion = _ebox.mGetOLVersion(_dom0)
        _client_key_exists = False
        _read_qemu = f"/EXAVMIMAGES/GuestImages/{_domU}/console/read-qemu/"
        _remotefile = _read_qemu + "ssh_client_key.pub"
        _exists = self.mCheckDockerImages(_dom0, _OLVersion)
        if not _exists:
            ebLogInfo(f"Docker images 'exa-hippo-serialmux|exa-hippo-sshd' are not existing on dom0:{_dom0}")
            return

        self.mCreateQemuDirs(_dom0, _domU)
        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            #Check if client public key exists
            if _node.mFileExists(_remotefile):
                ebLogInfo(f"*** {_remotefile} is present, no need to copy fake key. ***")
                _client_key_exists = True
        finally:
            _node.mDisconnect()

        if not _client_key_exists:
            self.mCopyFakeKey(_dom0, _domU)

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            _hostname = _domU.split('.')[0]
            _local_path = self.mCopyContainerTemplate(_dom0, _domU)
            if _OLVersion == "OL7":
                if _local_path:
                     _cmd_list = self.mPrepareContainerCommands(_dom0, _domU, _OLVersion)
                else:
                    #start container exa-hippo-serialmux
                    _cmd_list = [f"timeout 30s docker run -d -t --security-opt=no-new-privileges --memory=256m --cpus=0.1 --pids-limit=64 --restart always --log-opt max-size=10m --log-opt max-file=5 -v /EXAVMIMAGES/GuestImages/{_domU}/console/write-qemu:/write-qemu --name {_hostname}-serialmux --hostname {_hostname}-serialmux exa-hippo-serialmux:latest"]

                    #start container exa-hippo-sshd
                    _cmd_list += [f"timeout 30s docker run -d -t --security-opt=no-new-privileges --memory=256m --cpus=0.1 --pids-limit=64 --restart always --log-opt max-size=10m --log-opt max-file=5 -v /EXAVMIMAGES/GuestImages/{_domU}/console/write-qemu:/write-qemu -v /EXAVMIMAGES/GuestImages/{_domU}/console/read-qemu:/read-qemu:ro --name {_hostname}-sshd --hostname {_hostname}-sshd exa-hippo-sshd:latest"]
            elif _OLVersion == "OL8":
                if _local_path:
                    _cmd_list = self.mPrepareContainerCommands(_dom0, _domU, _OLVersion)
                else:
                    #start container exa-hippo-serialmux
                    _cmd_str = [f"timeout 30s podman run -d -t --security-opt=no-new-privileges --memory=256m --cpus=0.1 --pids-limit=64 --restart always --log-opt max-size=10m --log-opt max-file=5 -v /EXAVMIMAGES/GuestImages/{_domU}/console/write-qemu:/write-qemu --network=none --name {_hostname}-serialmux --hostname {_hostname}-serialmux exa-hippo-serialmux:latest"]

                    #start container exa-hippo-sshd
                    _cmd_str += [f"timeout 30s podman run -d -t --security-opt=no-new-privileges --memory=256m --cpus=0.1 --pids-limit=64 --restart always --log-opt max-size=10m --log-opt max-file=5 -v /EXAVMIMAGES/GuestImages/{_domU}/console/write-qemu:/write-qemu -v /EXAVMIMAGES/GuestImages/{_domU}/console/read-qemu:/read-qemu:ro --network=none --name {_hostname}-sshd --hostname {_hostname}-sshd exa-hippo-sshd:latest"]
            for _cmd_str in _cmd_list:
                _node.mExecuteCmdLog(_cmd_str)
                _rc = _node.mGetCmdExitStatus()
                if _rc != 0:
                    ebLogWarn(f'*** {_cmd_str} failed.. ***')
        finally:
            _node.mDisconnect()

    def mRestartContainer(self, aDom0, aDomU, aMode="restart"):
        _dom0 = aDom0
        _domU = aDomU
        _mode = aMode
        _cmd_str = ""

        _ebox = self.__cluctrl
        _OLVersion = _ebox.mGetOLVersion(_dom0)
        _exists = self.mCheckDockerImages(_dom0, _OLVersion)
        if not _exists:
            ebLogInfo(f"Docker images 'exa-hippo-serialmux|exa-hippo-sshd' are not existing on dom0:{_dom0}")
            return

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            _hostname = _domU.split('.')[0]

            if _OLVersion == "OL7":
                if _mode == "restart":
                    _cmd_str = f"timeout 30s docker {_mode} {_hostname}-sshd"
                else:
                    _cmd_str = f"timeout 30s docker {_mode} {_hostname}-serialmux {_hostname}-sshd"
            elif _OLVersion == "OL8":
                if _mode == "restart":
                    _cmd_str = f"timeout 30s podman {_mode} {_hostname}-sshd"
                else:
                    _cmd_str = f"timeout 30s podman {_mode} {_hostname}-serialmux {_hostname}-sshd"
            if _cmd_str:
                _node.mExecuteCmdLog(_cmd_str)
                _rc = _node.mGetCmdExitStatus()
                if _rc != 0:
                    ebLogWarn(f'*** {_cmd_str} failed.. ***')

        finally:
            _node.mDisconnect()

    def mStopContainer(self, aDom0, aDomU, aForce=False):
        _dom0 = aDom0
        _domU = aDomU
        _cmd_str = ""

        _ebox = self.__cluctrl
        _OLVersion = _ebox.mGetOLVersion(_dom0)
        _running_status = self.mCheckContainerStatus(_dom0, _domU, _OLVersion)
        if not _running_status:
            return

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            _hostname = _domU.split('.')[0]

            if _OLVersion == "OL7":
                if aForce:
                    _cmd_str = f"timeout 30s docker stop {_hostname}-serialmux {_hostname}-sshd"
                else:
                    _cmd_str = f"timeout 30s docker stop {_hostname}-sshd"
            elif _OLVersion == "OL8":
                if aForce:
                    _cmd_str = f"timeout 30s podman stop {_hostname}-serialmux {_hostname}-sshd"
                else:
                    _cmd_str = f"timeout 30s podman stop {_hostname}-sshd"
            if _cmd_str:
                _node.mExecuteCmdLog(_cmd_str)
                _rc = _node.mGetCmdExitStatus()
                if _rc != 0:
                    ebLogWarn(f'*** {_cmd_str} failed.. ***')

        finally:
            _node.mDisconnect()

    def mRemoveContainer(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU
        _cmd_str = ""

        _ebox = self.__cluctrl
        _OLVersion = _ebox.mGetOLVersion(_dom0)
        _exists = self.mCheckDockerImages(_dom0, _OLVersion)
        if not _exists:
            ebLogInfo(f"Docker images 'exa-hippo-serialmux|exa-hippo-sshd' are not existing on dom0:{_dom0}")
            return

        try:
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            _hostname = _domU.split('.')[0]

            if _OLVersion == "OL7":
                _cmd_str = f"timeout 30s docker rm {_hostname}-serialmux {_hostname}-sshd"
            elif _OLVersion == "OL8":
                _cmd_str = f"timeout 30s podman rm {_hostname}-serialmux {_hostname}-sshd"
            if _cmd_str:
                _node.mExecuteCmdLog(_cmd_str)
                _rc = _node.mGetCmdExitStatus()
                if _rc != 0:
                    ebLogWarn(f'*** {_cmd_str} failed.. ***')

        finally:
            _node.mDisconnect()

    def mRemoveConsoleDirs(self, aDom0, aDomU):
        _dom0 = aDom0
        _domU = aDomU

        try:
            _remote_dir = f"/EXAVMIMAGES/GuestImages/{_domU}/console"
            _node = exaBoxNode(get_gcontext())
            _node.mConnect(aHost = _dom0)
            if _node.mFileExists(_remote_dir):
                ebLogInfo(f"Serial Console Directory exists for VM:{_domU} Deleting the Directory..")
                _cmd_str = f"/bin/rm -rf {_remote_dir}"
                _node.mExecuteCmdLog(_cmd_str)
                _rc = _node.mGetCmdExitStatus()
                if _rc != 0:
                    ebLogError(f'*** {_cmd_str} failed.. ***')
        finally:
            _node.mDisconnect()

    def mCreateSSH(self, aDom0, aDomU):
        """Create SSH connection via OCI for VM via VNC and/or serial console.

        Exacloud injects the pub key provided by Customer on a given domU for creating 
        ssh connection via OCI for VM via VNC and/or serial console.

        :param aDom0: dom0 host name.
        :param aDomU: domU host name.
        :returns: Nothing.
        :raises ExacloudRuntimeError: on error
        """
        _dom0 = aDom0
        _domU = aDomU
        _ebox = self.__cluctrl

        _jconf = self.__options.jsonconf
        if _jconf is not None:
            _jconf_keys = list(_jconf.keys())
        
        _client_pub_key = None
        try:
            if _jconf_keys is not None:
                if 'sshkey' in _jconf_keys:
                    _client_pub_key = _jconf['sshkey']
        except Exception as e:
            _error_str = f'Error in fetching payload attributes: "{e}"'
            ebLogError(f'{_error_str}: Traceback "{traceback.format_exc()}"')
            raise

        _localfile = "/tmp/ssh_client_key.pub"
        with open(_localfile, "w") as _fp:
            _fp.write(_client_pub_key)

        _file_name = _localfile.split("/")[2]
        _read_qemu = f"/EXAVMIMAGES/GuestImages/{_domU}/console/read-qemu/"
        _remotefile = _read_qemu + _file_name

        self.mCreateQemuDirs(_dom0, _domU)
        _OLVersion = _ebox.mGetOLVersion(_dom0)
        _running_status = self.mCheckContainerStatus(_dom0, _domU, _OLVersion)
        if not _running_status:
            self.mRunContainer(_dom0, _domU)
        self.mCopyFile(_dom0, _localfile, _remotefile)
        self.mRestartContainer(_dom0, _domU)

        if os.path.exists(_localfile):
            os.remove(_localfile)

    def mCaptureConsoleHistory(self, aDom0, aDomU):
        """Capture Console History for a given VM.

        Exacloud fetches the console history for a given VM.
        Encrypts the console history public key provided by customer public key.
        Encrypted data is uploaded to the object store using Resource/User principals
        in EXACC & Instance principals in EXACS.

        :param aDom0: dom0 host name.
        :param aDomU: domU host name.
        :returns: Nothing.
        :raises ExacloudRuntimeError: on error
        """
        _dom0 = aDom0
        _domU = aDomU
        _remote_path = ""
        _file_name = ""
        _ebox = self.__cluctrl

        _OLVersion = _ebox.mGetOLVersion(_dom0)
        _running_status = self.mCheckContainerStatus(_dom0, _domU, _OLVersion)
        if not _running_status:
            _hostname = _domU.split('.')[0]
            _detail_error = f"Docker containers '{_hostname}-serialmux|{_hostname}-sshd' are not running on dom0:{_dom0}"   
            raise ExacloudRuntimeError(aErrorMsg=_detail_error)

        _path = f"/log/serialConsole/{_domU}/"
        _dir = _ebox.mGetBasePath() + _path
        if not os.path.exists(_dir):
            os.makedirs(_dir)

        _jconf = self.__options.jsonconf
        if _jconf is not None:
            _jconf_keys = list(_jconf.keys())
        _object_name = None
        _client_pub_key = None
        _namespace = None
        _bucket = None
        try:
            if _jconf_keys is not None:
                if 'namespace' in _jconf_keys:
                    _namespace = _jconf['namespace']
                if 'bucket_name' in _jconf_keys:
                    _bucket = _jconf['bucket_name']
                if 'object_name' in _jconf_keys:
                    _object_name = _jconf['object_name']
                if 'sshkey' in _jconf_keys:
                    _client_pub_key = _jconf['sshkey']
        except Exception as e:
            _error_str = f'Error in fetching payload attributes: "{e}"'
            ebLogError(f'{_error_str}: Traceback "{traceback.format_exc()}"')
            raise

        _localfile = _dir + _object_name
        _remote_path = f"/EXAVMIMAGES/GuestImages/{_domU}/console/" + _object_name

        _node = exaBoxNode(get_gcontext())
        _node.mConnect(aHost = _dom0)
        _cmd_str = f"/usr/bin/python3 /opt/exacloud/vmconsole/history_console.py --host {_domU}  --path {_remote_path}"
        _node.mExecuteCmd(_cmd_str)
        if _node.mFileExists(_remote_path):
            _node.mCopy2Local(_remote_path, _localfile)
            _node.mExecuteCmd(f"/bin/rm -rf {_remote_path}")
        _node.mDisconnect()

        #Encrypt the History Console File using client public key
        _encrypted_file, _encrypted_symmetric_key = self.mEncryptFile(_localfile, _client_pub_key)

        #Initialize the object store
        self.mObjectStoreInit()

        #Upload the encrypted file to the object store
        _response = self.mUploadFile(_namespace, _bucket, _object_name, _dir, _encrypted_file)

        if os.path.exists(_localfile):
            os.remove(_localfile)
        if os.path.exists(_encrypted_file):
            os.remove(_encrypted_file)

        _data_d  = {}
        _data_d['checksum'] = _response.headers["opc-content-md5"]
        _data_d['key'] = b64encode(_encrypted_symmetric_key).decode('utf-8')
        ebLogTrace(f"HistoryConsole Response Object: {json.dumps(_data_d)}")
        self.mUpdateRequestData(_data_d)

    def mRemoveSSH(self, aDom0, aDomU):
        """Remove SSH Connection previously created for accessing the serial console.

        Exacloud removes the pub key provided by Customer for a given DomU.
        At dom0 stop & remove the docker container for a given DomU.

        :param aDom0: dom0 host name.
        :param aDomU: domU host name.
        :returns: Nothing.
        :raises ExacloudRuntimeError: on error
        """
        _dom0 = aDom0
        _domU = aDomU

        aOptions = self.__cluctrl.mGetArgsOptions()
        _vmcmd = aOptions.vmcmd
        _cmd = self.__cluctrl.mGetCmd()

        if self.__cluctrl.mGetCmd() in ["vmgi_delete", "gi_delete", "createservice", "deleteservice", "vmgi_reshape"]:
            self.mStopContainer(_dom0, _domU, aForce=True)
            self.mRemoveContainer(_dom0, _domU)
            self.mRemoveConsoleDirs(_dom0, _domU)
        elif self.__cluctrl.mGetCmd() in ["vm_cmd"] and _vmcmd in ["delete_console_ssh"]:
            #Delete the existing client key & copy fake key        
            self.mCopyFakeKey(_dom0, _domU)

            #restarts the exa-hippo-sshd container
            self.mRestartContainer(_dom0, _domU)
