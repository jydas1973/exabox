#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/vmcorecollection.py /main/1 2025/04/01 20:53:23 ririgoye Exp $
#
# vmcorecollection.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      vmcorecollection.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      This module will handle the collection of the .vmcore logs for a given
#      VM. These logs will in turn be uploaded to an OSS bucket which will be 
#      specifically created for this purpose.
#
#    NOTES
#      Currently the logs are only retrieved via 'virsh dump', there are some
#      alternative ways which have not been implemented yet as we will see how
#      the current way works.
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    03/12/25 - Enh 35314599 - EXACLOUD: CREATE AN API IN ECRA FOR
#                           MARS TEAM TO PUSH THE VMCORE TO MOS
#    ririgoye    03/12/25 - Creation
#

import functools
import json
import os
import os.path
import time
import uuid

from oci.object_storage.models import Bucket, CreateBucketDetails
from oci.object_storage.transfer.upload_manager import UploadManager
from subprocess import PIPE

from exabox.core.Context import get_gcontext
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogVerbose, ebLogDebug, ebLogJson, ebLogTrace
from exabox.utils.ExaRegion import get_instance_root_compartment
from exabox.utils.node import connect_to_host


DEFAULT_BUCKET_NAME = "vmcore-mos-logs-bucket"


def retry(aRetriesLimit, aSleep):
    """
    Meant to be used as decorator or wrapper.
    This allows to retry a func in case it raises exception, at most aRetriesLimit times.
    It will sleep aSleep seconds between each try

    :param aRetriesLimit: the retry num; retry sleep sec
    :return: decorator
    """

    def aDecorator(func):
        """aDecorator"""

        # Keep func info
        @functools.wraps(func)
        def aWrapper(*args, **kwargs):
            """wrapper"""

            for attempt in range(aRetriesLimit):
                try:
                    return func(*args, **kwargs)

                except Exception as err:   # pylint: disable=broad-except
                    ebLogTrace(f"Try {attempt} of {aRetriesLimit} failed for: '{func}'")
                    ebLogTrace(f"Error: \n{err}")
                    time.sleep(aSleep)
            ebLogError(f"Retry failed for '{func}'")
            raise Exception(f'Exceed max retry num: {aRetriesLimit} failed')

        return aWrapper

    return aDecorator


class ebOSSBucketManager:
    """
    Wrapper of some OCI clients to easily handle the creation of the bucket
    that will store the VM core logs.
    """

    def __init__(self):
        self.__ociFactory = ExaOCIFactory()
        self.__identityClient = self.__ociFactory.get_identity_client()
        self.__objectStorageClient = self.__ociFactory.get_object_storage_client()
        self.__transferManager = UploadManager(self.__objectStorageClient)
        self.__tenancyOcid = self.mFetchTenancyOCID()
        self.__ossNamespace = self.mFetchOSSNamespace()
        self.__bucketName = DEFAULT_BUCKET_NAME

    def mGetBucketName(self) -> str:
        return self.__bucketName

    def mSetBucketName(self, aName: str) -> None:
        self.__bucketName = aName

    def mGetTenancyOCID(self) -> str:
        return self.__tenancyOcid

    def mGetOSSNamespace(self) -> str:
        return self.__ossNamespace

    def mFetchTenancyOCID(self) -> str:
        # Call IMDSv2 to retrieve the tenancy OCID
        try:
            self.__tenancyOcid = get_instance_root_compartment()
            ebLogInfo("Detected root compartment from Exacloud IMDSv2: "
                f"{self.__tenancyOcid}")
            return self.__tenancyOcid
        # If call to IMDS fails, raise error
        except Exception as e:
            _err = ("Exacloud could not call the IMDS endpoint to get the "
                "Instance Tenancy OCID, Please verify the Instance is healthy"
                f"and you can curl the IMDS endpoint, e.g. try: "
                "'curl http://169.254.169.254/opc/v2/instance/', error: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

    @retry(aRetriesLimit=5, aSleep=5)
    def mFetchOSSNamespace(self) -> str:
        ebLogInfo("Exacloud is about to try to get the OSS Namespace")
        # Trigger call
        try:
            _response = self.__objectStorageClient.get_namespace()
        except Exception as e:
            _err = (f"Exacloud failed to get the OSS namespace  "
                f"with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Error: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log Request Id
        ebLogTrace(f"Request ID is: '{_response.request_id}'")
        ebLogInfo(f"Detected OSS Namespace: '{_response.data}'")
        return _response.data

    @retry(aRetriesLimit=5, aSleep=5)
    def mBucketExists(self) -> Bucket:
        try:
            # Trigger call and fail on error
            _response = self.__objectStorageClient.get_bucket(
                   namespace_name = self.mGetOSSNamespace(),
                   bucket_name = self.mGetBucketName()
            )
            # Log Request Id
            ebLogTrace(f"Request ID is: '{_response.request_id}'")
            # Return bucket if found
            if _response.status == 404:
                ebLogWarn(f"Did not find bucket with name: {self.mGetBucketName()}")
                return False
            _bucket = _response.data
            ebLogInfo(f"Found bucket: {_bucket}")
            return _bucket
        except Exception as e:
            ebLogWarn(f"Could not find any bucket with name: '{self.mGetBucketName()}'")
            ebLogTrace(f"Error: '{e}'")
            return None

    @retry(aRetriesLimit=5, aSleep=5)
    def mCreateBucket(self) -> Bucket:
        # Create bucket details
        _bucketCreationDetails = CreateBucketDetails(
            name = self.mGetBucketName(),
            compartment_id = self.mGetTenancyOCID(),
            metadata={'Comment': 'Created by Exacloud'}
        )

        # Nothing is sensitive here, we can log it
        ebLogInfo(f"Exacloud is about to create a bucket with details:\n"
            f"{_bucketCreationDetails}'")

        # Trigger call and fail on error
        try:
            _response = self.__objectStorageClient.create_bucket(
                   namespace_name = self.mGetOSSNamespace(),
                   create_bucket_details = _bucketCreationDetails)
        except Exception as e:
            _err = (f"Exacloud couldn't create the Bucket with name: "
                f"'{self.mGetBucketName()}' with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Erorr: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        # Log request ID
        ebLogTrace(f"Request ID is: '{_response.request_id}'")

        ebLogInfo(f"Exacloud created with success a bucket with name: "
                f"'{self.mGetBucketName()}'")
        return _response.data

    @retry(aRetriesLimit=3, aSleep=5)
    def mUploadToBucket(self, aFilePath: str, aObjectName: str) -> None:
        # Log that exacloud will create a new object
        ebLogInfo(f"Exacloud is about to upload a new object from: {aFilePath}")
        # Get file size for content_length (required for multipart upload)
        _fileSize = os.path.getsize(aFilePath)
        try:
            # Open the file in binary mode to stream data
            with open(aFilePath, 'rb') as _stream:
                _response = self.__transferManager.upload_stream(
                    namespace_name=self.mGetOSSNamespace(),
                    bucket_name=self.mGetBucketName(),
                    object_name=aObjectName,
                    stream_ref=_stream,
                    content_length=_fileSize
                )
                # Log request ID
                ebLogTrace(f"Request ID is: '{_response.request_id}'")
        except Exception as e:
            _err = (f"Exacloud couldn't upload the object {aObjectName} in"
                f"'{self.mGetBucketName()}' with the ECRA Super User. "
                f"Please review the IAM setup for the host where Exacloud is running. "
                f"Error: '{e}'")
            ebLogError(_err)
            raise ExacloudRuntimeError(0x095, 0xA, _err) from e

        ebLogInfo(f"Exacloud created object {aObjectName} with success in {self.mGetBucketName()}.")

class ebVMCoreCollector:
    """
    The aim here is to be able to collect the VM Core logs and process multiple
    iterations of the operation. Making it a class so it's easier to encapsulate
    and limit the amount of lines added to the clucontrol handler.
    """
    def __init__(self, aCluCtrl, aOptions: dict):
        self.__uuid = uuid.uuid1()
        self.__ebox = aCluCtrl
        self.__options = aOptions
        self.__vm = self.__options.get("vm_name")
        self.__targetOssPath = {"bucket": "", "object_name": ""}
        self.__tmpDir = f"/tmp/{self.__uuid}_vmcorelogs"

    def mGetUUID(self) -> str:
        return str(self.__uuid)

    def mGetEbox(self):
        return self.__ebox
    
    def mGetVMName(self) -> str:
        return self.__vm

    def mGetTargetOssPath(self) -> str:
        return json.dumps(self.__targetOssPath)

    def mSetTargetOssPath(self, aBucketName: str, aObjectName: str) -> None:
        self.__targetOssPath["bucket"] = aBucketName
        self.__targetOssPath["object_name"] = aObjectName

    def mGetTmpDir(self) -> str:
        return self.__tmpDir

    def mCreateLocalDir(self, aPath: str) -> None:
        _ebox = self.mGetEbox()
        _cmd = f"/usr/bin/mkdir -p {aPath}"
        _ebox.mExecuteCmdLog(_cmd)
        ebLogInfo(f"Created local VM Core log directory {aPath}")

    def mDeleteLocalDir(self, aPath: str) -> None:
        _ebox = self.mGetEbox()
        _cmd = f"/usr/bin/rm -rf {aPath}"
        _ebox.mExecuteCmdLog(_cmd)
        ebLogInfo(f"Deleted local VM Core log directory {aPath}")

    def mCollectVMCoreVirsh(self, aNode: exaBoxNode, aTargetRemoteDir: str) -> int:
        # Create remote temporary path
        _tmpDir = self.mGetTmpDir()
        _vm = self.mGetVMName()
        _targetFileName = f"{_vm}.vmcore"
        _targetRemotePath = os.path.join(aTargetRemoteDir, _targetFileName)
        _targetLocalPath = f"{_tmpDir}/{_targetFileName}"
        # Build VM core generation command
        _cmd = "/usr/bin/virsh dump --live --memory-only --bypass-cache"
        _cmd += f" --format=kdump-zlib --domain {_vm}"
        _cmd += f" --file {_targetRemotePath}"
        # Generate VM core and copy to local directory
        ebLogInfo(f"Generating VM core logs for host: {_vm}")
        _retries, _maxRetries = 0, 3
        _status = 0
        while _retries < _maxRetries:
            _, _o, _e = aNode.mExecuteCmd(_cmd)
            _status = aNode.mGetCmdExitStatus()
            if _status != 0:
                ebLogError(f"Error during VM Core dump: {_e.read()} | Stdout: {_o.read()}")
                if (_retries + 1) < _maxRetries:
                    ebLogInfo("Retrying VM Core dump...")
                    _retries += 1
                    continue
                ebLogError("Maximum retries exceeded. VM core dump failed.")
                return _status
            # Here we can assume the above is successful
            ebLogInfo("VM core dump successful.")
            break
        ebLogInfo(f"Copying log from remote path {_targetRemotePath} to local {_targetLocalPath}")
        aNode.mCopy2Local(_targetRemotePath, aLocalPath=_targetLocalPath)
        # Delete remote VM core log after copying to local directory
        _cmd = f"/usr/bin/rm -rf {_tmpDir}"
        aNode.mExecuteCmdLog(_cmd)
        return 0

    def mCollectVMCoreQMP(self, aNode: exaBoxNode, aTargetLocalDir: str) -> int:
        ebLogError("'mCollectVMCoreQMP' not implemented yet.")
        return 0

    def mCollectCrashFiles(self, aNode: exaBoxNode, aTargetLocalDir: str):
        ebLogError("'mCollectCrashFiles' not implemented yet.")
        return 0

    def mCollectVMCoreLogs(self, aHostname: str) -> int:
        # Create temporary local directory
        _ebox = self.mGetEbox()
        _tmpDir = self.mGetTmpDir()
        # Connect to host and start collection
        _rc = 0
        with connect_to_host(aHostname, _ebox.mGetCtx()) as _node:
            # Create remote temporary path
            _node.mExecuteCmdLog(f"/usr/bin/mkdir -p {_tmpDir}")
            # VM Core dump using virsh
            _rc = self.mCollectVMCoreVirsh(_node, _tmpDir)
            # TODO: Check if there are more necessary logs
        return _rc

    def mCompressFile(self, aTargetDir: str) -> tuple:
        # Create .tar.xz file path
        ebLogInfo(f"Creating specified dir for compressed file storage")
        _ebox = self.mGetEbox()
        _tempDir = self.mGetTmpDir()
        _tarPath = f"{aTargetDir}/vmcorelogs.tar.xz"
        self.mCreateLocalDir(aTargetDir)
        # Tar and compress using xz
        ebLogInfo(f"Compressing VM core files as {_tarPath}. This may take a while...")
        _cmd = f"/usr/bin/tar -c --use-compress-program=\"xz -3\" -f {_tarPath} {_tempDir}"
        _rc, _i, _o, _e = _ebox.mExecuteLocal(_cmd, aStdIn=PIPE, aStdOut=PIPE, aStdErr=PIPE)
        if _rc != 0:
            ebLogError(f"Error while compressing file to {_tarPath}: {_e.read()}")
            return _rc, None
        ebLogInfo(f"Compressed file to {_tarPath}")
        # Once compressed, we can delete the temporary directory
        self.mDeleteLocalDir(_tempDir)
        return 0, _tarPath

    def mUploadToOss(self, aFilePath: str) -> int:
        # Initialize bucket manager
        _bucketHandler = ebOSSBucketManager()
        _bucket = _bucketHandler.mBucketExists()
        if not _bucket:
            _bucket = _bucketHandler.mCreateBucket()
        _bucketHandler.mUploadToBucket(aFilePath, self.mGetVMName())
        self.mSetTargetOssPath(_bucket.name, self.mGetVMName())
        return 0

    def mHandleLogCollection(self) -> int:
        # Create local temp directory where logs will be copied to remotely
        _ebox = self.mGetEbox()
        _tempDir = self.mGetTmpDir()
        self.mCreateLocalDir(_tempDir)
        # Perform the collection per host
        _dpairs = _ebox.mReturnDom0DomUPair()
        _rc = 0
        _found = False
        for _dom0, _domU in _dpairs:
            # Skip if domU doesn't match with VM name
            if not _domU == self.mGetVMName():
                continue
            # This part will be executed only if domU matches with VM name
            _found = True
            ebLogInfo(f"Collecting VM core logs from dom0: {_dom0}")
            _rc = self.mCollectVMCoreLogs(_dom0)
            ebLogInfo(f"VM core collection from {_dom0} returned exit code ({_rc}).")
            break
        # Return exit code 1 if domU isn't found
        if not _found:
            ebLogError(f"Could not find a matching domU for VM name: {self.mGetVMName()}")
            _rc = 1
        # Check return code before proceeding
        if _rc != 0:
            ebLogError("Error while trying to collect the logs.")
            return _rc
        # Once all vm core logs have been copied, we need to compress them
        ebLogInfo("Successfully collected the VM core file.")
        _tarDir = get_gcontext().mGetConfigOptions().get("vmcore_tmp_storage_dir", "/tmp/compressedvmcorelogs")
        _tarDir = os.path.join(_tarDir, self.mGetUUID())
        _rc, _tarPath = self.mCompressFile(_tarDir)
        if _rc != 0:
            ebLogError("Error while compressing VM core logs.")
            return _rc
        # Upload compressed file to OSS
        _rc = self.mUploadToOss(_tarPath)
        self.mDeleteLocalDir(_tarDir)
        if _rc != 0:
            ebLogError("Error while trying to upload the logs to OSS.")
            return _rc
        return 0
