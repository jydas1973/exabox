"""
 Copyright (c) 2014, 2025, Oracle and/or its affiliates.

NAME:
    ExasshScript - Basic functionality

FUNCTION:
    Provide a command line tool to manipulate the access to the deploy hosts

NOTE:
    The return code of the script are the same as as ssh command execution

History:
    MODIFIED   (MM/DD/YY)
    jesandov    01/06/25 - Add PKCS8 and TraditionalOpenSSL Format export
    ririgoye    09/30/24 - Bug 36390923 - REMOVE EXAKMS HISTORY VALIDATION
                           ACROSS HOSTS
    jesandov    09/02/24 - 36883563: Add Paramiko Debug Mode
    jesandov    04/18/24 - 36529410: silent mode on banner
    ririgoye    08/02/23 - Enh 35637033 - EXASSH TO ALLOW TO EXECUTE SCRIPTS
                           WITHOUT COPYING SCRIPTS TO TARGET
    aypaul      06/01/22 - Enh#34207528 ExaKms entry history tracking and
                           generation.
    jesandov    05/31/22 - Add ExaKms KeyValue Info
    aypaul      05/04/22 - Enh#34127058 exakms entry tracking endpoint.
    jesandov    01/26/22 - Add two new options for invalid keys
    naps        01/20/22 - Bug 33216821 - Fix stdout and stderr.
    alsepulv    12/17/21 - Bug 33676363: Ensure root is default user
    alsepulv    04/14/21 - Enh 32769003: Deduce hostname and domain from FQDN
    jesandov    09/26/18 - File Creation
"""

from __future__ import print_function

import shlex
import sys
import time
import json
import argparse

from exabox.core.Context import get_gcontext
from exabox.exassh.ExasshManager import ExasshManager

class ExasshScript:

    def __init__(self):

        self.__start   = time.time()
        self.__manager = None
        self.__args = None
        self.__parser = None

    def mArgsParse(self):

        _parser = argparse.ArgumentParser(description='Access to the host using KMS keys"')
        _parser.add_argument('target', nargs='?', help='The number or host to access')

        _g1 = _parser.add_argument_group('Status Operations')
        _g1.add_argument('-s', '--status', dest='status', action='store_true', help='Show specific information about the target host')
        _g1.add_argument('-oi', '--only-invalid', dest="only_invalid", action='store_true', help="On status, print invalid keys")
        _g1.add_argument('-di', '--delete-invalid', dest="delete_invalid", action='store_true', help="On status, delete invalid keys")
        _g1.add_argument('-ht', '--history', dest='history', action='store_true', help='Specify this option to fetch historical data of all exakms entries.')

        _g2 = _parser.add_argument_group('File Operations')
        _g2.add_argument(
            '-dw', '--download', dest='download', nargs=2,
            metavar=('<Remote File Absolute path>', '<Local File absolute path>')
         )
        _g2.add_argument(
            '-up', '--upload', dest='upload', nargs=2, 
            metavar=('<Local File Absolute Path>', '<Remote File Absolute Path>')
        )
        _g2.add_argument('-e', '--execute', dest='execute', nargs=argparse.REMAINDER, help='Execute the Script on the target host')
        _g2.add_argument(
            '-re', '--remote-execute', dest='remotelyexecute', nargs=argparse.REMAINDER, 
            help='Executes a file remotely without copying them directly to target.',
            metavar=('<Local path of the file to execute>', '<Arguments of the file to be run>')
        )

        _g3 = _parser.add_argument_group('Select operations')
        _g3.add_argument('-o', '--output', dest='output', help='output: ["default", "json", "delimiter"]')
        _g3.add_argument('-u', '--user', dest='user',  help='Try to connect using the <user>')
        _g3.add_argument('-w', '--wait-ssh', dest='wait', help='Microseconds to wait to ssh to response')
        _g3.add_argument('-sl', '--silent', dest='silent', action="store_true", help='Hide execution time')
        _g3.add_argument('-d', '--debug', dest='debug', action="store_true", help='Paramiko Debug Mode')
        _g3.add_argument('-nc', '--no-console', dest='no_console', action="store_true", help='No Console')
        _g3.add_argument('-fl', '--filelog', dest='filelog', action="store_true", help='Create exassh.log')
        _g3.add_argument('-x', '--xml', dest='xml', help='Exacloud XML')
        _g3.add_argument('-mi', '--mina', dest='mina', action="store_true", help='Test SSH Connection using OEDA MINA')
        _g3.add_argument('-m', '--mode', dest='mode', choices=["default", "soft", "hard"], default="default", \
            help='modes: {"default": "only list keys", "soft": "calculate ping", "hard": "calculate ssh}'
        )
        _g3.add_argument('-ek', '--exakms', choices=["ExaKmsFileSystem", "ExaKmsOCI", "ExaKmsKeysDB"], \
           dest='exakms', help='ExaKms Implementation, default behavior is auto'
        )

        _g4 = _parser.add_argument_group('Deprecated options')
        _g4.add_argument('-k', '--kms', dest='kms', help='KMS Object name')
        _g4.add_argument('-r', '--recursive', dest='recursive', action='store_true', help='Recursive File Operations')
        _g4.add_argument('-ne', '--numentries', dest='numentries', type=int, default=20, help='Number of entries to show in historical analysis.')

        self.__parser = _parser

    def mCreateManager(self, aArgsList=None):

        if aArgsList:
            self.__args = self.__parser.parse_args(aArgsList)
        else:
            self.__args = self.__parser.parse_args()

        _console = not self.__args.no_console

        self.__manager = ExasshManager(
            aConsoleLog=_console,
            aFileLog=self.__args.filelog,
            aSilent=self.__args.silent,
            aDebug=self.__args.debug

        )

    def mGetExassManager(self):
        return self.__manager

    def mExecute(self):

        if self.__args.kms or self.__args.recursive:
            self.__manager.mGetLog().info("")
            self.__manager.mGetLog().info("###########################################")
            self.__manager.mGetLog().info("# OPTIONS '--kms' and '-r' ARE DEPRECATED #")
            self.__manager.mGetLog().info("#    WILL BE REMOVED IN FUTURE VERSIONS   #")
            self.__manager.mGetLog().info("###########################################")
            self.__manager.mGetLog().info("")

        if self.__args.exakms:
            get_gcontext().mSetConfigOption("exakms_type", self.__args.exakms)

        _options = {}
        if self.__args.xml:
            self.__manager.mSetXmlPath(self.__args.xml)

        self.__manager.mSetMode(self.__args.mode)

        if self.__args.wait is not None:
            self.__manager.mSetSshMicroseconds(self.__args.wait)

        if self.__args.output is not None:
            self.__manager.mSetOutput(self.__args.output)

        # Init parameters
        _cparams = {}
        _user = ''

        # Fetch connection params
        if self.__args.target is not None:
            _cparams['FQDN'] = self.__args.target
            _cparams['strict'] = True
            _user = 'root'

        # Fetch User
        if self.__args.user is not None:
            _user = self.__args.user
            if not _user:
                _user = "root"

        if _user:
            _cparams['user'] = _user

        # Fetch keys
        self.__manager.mSetConnParams(_cparams)

        _exakms = self.__manager.mGetExaKmsSingleton().mGetExaKms()

        if not self.__args.silent:
            self.__manager.mGetLog().info(f"ExaKms: {type(_exakms).__name__}")

        if self.__args.history:

            _pull_entries = self.__args.numentries
            if _cparams.get('FQDN', None) is None:
                self.__manager.mGetLog().info(f"Displaying last {_pull_entries} records from exakms entries.")
            else:
                self.__manager.mGetLog().info(f"Displaying last {_pull_entries} records from exakms entries for host {_cparams.get('FQDN')}.")

            if self.__args.user is not None:
                _curr_history_list = _exakms.mGetExaKmsHistoryInstance().mGetExaKmsHistory(_cparams.get('user','root'), _cparams.get('FQDN', None), _pull_entries)
            else:
                _curr_history_list = _exakms.mGetExaKmsHistoryInstance().mGetExaKmsHistory(None, _cparams.get('FQDN', None), _pull_entries)

            #Item: {"time": "", "operation": "", "user_hostname": ""}
            if len(_curr_history_list) == 0:
                self.__manager.mGetLog().info(f"No historical records found for user {_cparams.get('user','root')} and {_cparams.get('FQDN', 'All')}")
            for _entry in _curr_history_list:
                self.__manager.mGetLog().info(f"Key for {_entry['user_hostname']} got {_entry['operation']} at {_entry['time']} from {_entry['src_host']}")
            return 0

        # Print
        if self.__args.target is None:

            if not self.__args.status:
                self.__manager.mPrintAll()
                return 0

        if self.__manager.mGetMode() == "default":
            self.__manager.mSetMode("soft")

        if self.__args.status:

            _onlyInvalid = self.__args.only_invalid
            _delete = self.__args.delete_invalid

            _entries = self.__manager.mSearchExaKms()

            for _entry in _entries:

                _status = self.__manager.mGetHostStatus(
                    _entry,
                    aValidateEntry=True
                )

                _printStatus = True
                if _onlyInvalid or _delete:

                    _printStatus = False
                    if "invalid" in _status and _status["invalid"]:

                        if _delete:
                            self.__manager.mGetLog().info(f"Deleting ExaKmsEntry: {_entry.mToJsonMinimal()}")
                            _exakms.mDeleteExaKmsEntry(_entry)

                        else:
                            _printStatus = True

                if _printStatus:
                    self.__manager.mGetLog().info(json.dumps(_status, sort_keys=True, indent=4))

            return 0

        # Validate OPCTL_ENABLE
        if get_gcontext().mCheckConfigOption("enable_block_opctl", "True"):

            _entries = self.__manager.mSearchExaKms()
            for _entry in _entries:

                _kv = _entry.mGetKeyValueInfo()
                if "OPCTL_ENABLE" in _kv and str(_kv["OPCTL_ENABLE"]).upper() == "TRUE":

                    self.__manager.mGetLog().error("="*50)
                    self.__manager.mGetLog().error("ExaKms Entry is marked as OPCTL_ENABLE")
                    self.__manager.mGetLog().error(str(_entry))
                    self.__manager.mGetLog().error("")
                    self.__manager.mGetLog().error("The usage of exassh script under OPCTL_ENABLE hosts is denied")
                    self.__manager.mGetLog().error("="*50)
                    return 126

        # Do connection

        if self.__args.mina:

            if self.__args.execute:
                return self.__manager.mConnectMina(" ".join(self.__args.execute))
            else:
                return self.__manager.mConnectMina()

        try:
            self.__manager.mConnect()
        except Exception as e:
            self.__manager.mGetLog().info(e)
            return 1

        if self.__args.upload:
            _up = self.__args.upload
            return self.__manager.mUpload(_up[0], _up[1])

        elif self.__args.download:
            _dw = self.__args.download
            return self.__manager.mDownload(_dw[0], _dw[1])
        
        elif self.__args.remotelyexecute:
            _re = self.__args.remotelyexecute
            self.__manager.mGetLog().info(f"About to run file {_re[0]} with args: {_re[1:]}")
            return self.__manager.mRemotelyExecute(_re[0], _re[1:])

        elif self.__args.execute is not None:

            _rc, _out, _err =  self.__manager.mExecuteSshCommand(" ".join(self.__args.execute))

            _out = _out.strip()
            _err = _err.strip()

            if _out:
                self.__manager.mGetLog().info(_out)

            if _err:
                self.__manager.mGetLog().error(_err)

            return _rc

        else:
            return self.__manager.mStartCli()

        return 0

    def mExit(self, aRc):

        self.__manager.mDisconnect()

        if not self.__args.silent:
            self.__manager.mGetLog().info(f"\n*** Exassh Execution time: {time.time() - self.__start} \n")

        sys.exit(aRc)

if __name__ == '__main__':

    _obj = ExasshScript()
    _obj.mArgsParse()
    _obj.mCreateManager()

    _rc = 1
    _rc = _obj.mExecute()

    _obj.mExit(_rc)

# end of file
