"""
 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    ExaClient - Allows to call a Exacloud endpoint

FUNCTION:
    Provide basic functionality to call an Exacloud endpoint

NOTE:
    None

History:
    ndesanto    02/22/2021 - Create file.

"""

import argparse
import os
import json
import socket
import sys

from argparse import ArgumentParser, Namespace
from exabox.agent.AuthenticationStorage import ebGetHTTPAuthStorage, ebConfigAuthStorage
from exabox.network.HTTPSHelper import build_opener, is_https_enabled

def call(aConfigPath: str, aHost: str, aPort: int, aEndpoint: str) -> None:
    try:
        _protocol: str = "http"
        if is_https_enabled():
            _protocol = "https"

        _url: str = "{}://{}:{}/{}".format(_protocol, aHost, aPort, aEndpoint)
        print("url = {}".format(_url))

        _opts: dict = {}
        with open(aConfigPath, "r") as _fd:
            _opts = json.load(_fd)
        _ebCAS = ebConfigAuthStorage(_opts)
        _authkey = ebGetHTTPAuthStorage(aCustomStorage=_ebCAS, aExacloudOpts=_opts).mGetAdminCredentialForRequest()

        _headers = {}
        _headers["authorization"] = "Basic {}".format(_authkey)

        _response = build_opener(aHost, aPort, _url, aHeaders=_headers)

        if _response:
            print("status = {}\ndata = {}".format(_response.status, _response.data))
        else:
            print("Error - {}".format(_response.msg))

    except Exception as e:
        print("ERROR - e = {}".format(e))
        raise


def help() -> None:
    print("""
Usage:
    bin/python exabox/network/ExaClient -i|--host host -p|--port port [-E endpoint] [-c|--config path]

DESCRIPTION
    Helper script to call a Exacloud enpoint, certificates and/or passwords are loaded internally.

    This script assumes Exacloud is running and working properlly.

OPTIONS
    -h, --help
      Prints this help message.

    -c, --config
      exabox.conf file location if not using default one (config/exabox.conf).
""")


def main() -> bool:
    _basepath: str = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../.."))
    _default_config: str = os.path.abspath(
        os.path.join(_basepath, "config", "exabox.conf"))

    _parser: ArgumentParser = ArgumentParser(description="Exacloud self signed certificates creation tool",
                            epilog="Exa ECS Team")

    _parser.add_argument("-i","--host", help="Specify the host where Exacloud is running.", dest="host")
    _parser.add_argument("-p","--port", help="Specify the location of the Exacloud configuration to use.", type=int, dest="port")
    _parser.add_argument("-e","--endpoint", help="Specify the location of the Exacloud configuration to use.", default="", dest="endpoint")
    _parser.add_argument("-c","--config", help="Specify the location of the Exacloud configuration to use.", default=_default_config, dest="config")

    args: Namespace = _parser.parse_args()

    if "help" in args:
        help()
    elif args.host and args.port:
        call(args.config, args.host, args.port, args.endpoint)
    else:
        print("Invalid option.\n")
        help()
        return False

    return True


if __name__ == "__main__":
    if main():
        sys.exit(0)
    sys.exit(1)

# end of file