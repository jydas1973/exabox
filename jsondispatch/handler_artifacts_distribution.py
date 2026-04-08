#!/bin/python
#
# $Header: ecs/exacloud/exabox/jsondispatch/handler_artifacts_distribution.py scoral_bug-34650120/2 2026/03/01 08:29:50 scoral Exp $
#
# handler_artifacts_distribution.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      handler_artifacts_distribution.py - Artifacts distribution to Exadata nodes.
#
#    DESCRIPTION
#      Entrypoint for the artifacts distribution endpoint.
#      This endpoint will upload and install any artifact into any Exadata note.
#      Further details included in the spec:
#      https://confluence.oraclecorp.com/confluence/display/EDCS/Exacloud+Artifacts+Distribution+and+Installation+Endpoint
#
#    NOTES
#      None.
#
#    MODIFIED   (MM/DD/YY)
#    scoral      02/06/26 - Creation
#

import os
from datetime import datetime
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogTrace
from exabox.ovm.clumisc import ebMiscFx
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check,
                               node_exec_cmd, node_exec_cmd_check,
                               node_read_text_file, node_write_text_file)
from exabox.jsondispatch.jsonhandler import JDHandler

class ArtifactsDistribution(JDHandler):
    def __init__(self, aOptions, aRequestObj=None, aDb=None):
        super().__init__(aOptions, aRequestObj, aDb)
        self.mSetSchemaFile(os.path.abspath("exabox/jsondispatch/schemas/artifacts_distribution.json"))

    def mExecute(self) -> tuple:
        # Parse payload
        _payload = self.mGetOptions().jsonconf
        _mime = _payload['file']['mime']
        _sha256sum = _payload['file']['sha256checksum']
        _path = _payload['file']['local_path']
        # Auxiliary variables
        _now = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        _filename =  os.path.basename(_path)
        _remote_dir = f"/EXAVMIMAGES/Exacloud/ArtifactsDistribution_{_now}"
        _remote_path = f"{_remote_dir}/{_filename}"
        _result = { "dom0": [] }

        # Check if MIME type is supported
        if _mime.lower() != "application/gzip":
            _msg = f'MIME type "{_mime}" is not supported'
            raise ExacloudRuntimeError(0x0825, 0xA, _msg)

        # Check if the file has the correct SHA256 checksum
        _cmd = f"/bin/sha256sum {_path}"
        _rc, _, _out, _ = ebMiscFx.mExecuteLocal(_cmd)
        if _rc:
            _msg = f"Error while calculating the SHA256 checksum of {_path}"
            raise ExacloudRuntimeError(0x0825, 0xA, _msg)
        _actual_sha256sum = _out.split()[0]
        if _sha256sum != _actual_sha256sum:
            _msg = (f'SHA256 checksum of {_path} is "{_actual_sha256sum}" '
                    f'but payload is "{_sha256sum}"')
            raise ExacloudRuntimeError(0x0825, 0xA, _msg)

        # Upload the file to each host
        for _dom0 in _payload['dom0']:
            with connect_to_host(_dom0['hostname'], get_gcontext()) as _node:
                _status = "success"
                _error_code = "0x00000000"
                _error_details = ""
                try:
                    # Create temp dir
                    _cmd = f'/bin/mkdir -p {_remote_dir}'
                    node_exec_cmd_check(_node, _cmd)

                    # Upload the artifact
                    _node.mCopyFile(_path, _remote_path)

                    # Extract the file inside the node
                    _cmd = f"/bin/tar -xf {_remote_path} -C {_remote_dir}"
                    node_exec_cmd_check(_node, _cmd)

                    # Execute the script and check everything was fine
                    _cmd = f'/bin/sh {_remote_dir}/install.sh'
                    _rc, _out, _err = node_exec_cmd(_node, _cmd)

                    # Dump the script stdout & stderr to a log file into the Dom0
                    _log = ("==================\n"
                            "===== STDOUT =====\n"
                            "==================\n") + _out + "\n\n" + \
                           ("==================\n"
                            "===== STDERR =====\n"
                            "==================\n") + _err
                    _log_path = f"{_remote_dir}.log"
                    node_write_text_file(_node, _log_path, _log)

                    # Check if script execution failed
                    if _rc:
                        _msg = ("install.sh execution failed!!!, "
                                f"please check logs under {_log_path} "
                                f"in {_dom0['hostname']}")
                        raise ExacloudRuntimeError(0x0825, 0xA, _msg)

                except Exception as ex:
                    _status = "fail"
                    _error_code = "0x02030007"
                    _error_details = str(ex)

                finally:
                    # Cleanup the temporary directory
                    _cmd = f"/bin/rm -rf {_remote_dir}"
                    node_exec_cmd(_node, _cmd)

                    # Build the result payload
                    _result['dom0'].append({
                        "hostname": _dom0['hostname'],
                        "status": _status,
                        "error_code": _error_code,
                        "error_details": _error_details
                    })

        return (0, _result)
