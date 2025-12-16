"""
 Copyright (c) 2014, 2019, Oracle and/or its affiliates. All rights reserved.

NAME:
    Network - Basic functionality for Node Network

FUNCTION:
    Provide basic/core API for managing Network Data

NOTE:
    None

History:
    ndesanto    10/02/2019 - Enh 30374491: EXACC PYTHON 3 MIGRATION BATCH 02
    mirivier    08/21/2014 - Create file
"""

from __future__ import print_function

ebNetDevNone   = 0
ebNetDevBridge = 1
ebNetDevBond   = 1 << 1
ebNetDevIB     = 1 << 2
ebNetDevEther  = 1 << 3
ebNetDevMaster = 1 << 4
ebNetDevSlave  = 1 << 5
ebNetDevUp     = 1 << 6
ebNetDevDown   = 1 << 7
ebNetDevLoopBack = 1 << 8
ebNetDevUndef  = -1

class exaBoxNetDev(object):

    def __init__(self):

        self.__type  = ebNetDevNone     # Loopback, Ethernet, Infiniband
        self.__mac   = ebNetDevNone     # Handle multiple MAC ?
        self.__bond  = ebNetDevNone     # bond device
        self.__bondrole = ebNetDevNone  # master or slave
        self.__status   = ebNetDevNone  # Up or Down
        self.__mtu      = ebNetDevUndef


class exaBoxLoopBackDev():

    def __init__(self):
        super(self)
        self.__type     = ebNetDevLoopBack

class exaBoxEtherDev(exaBoxNetDev):

    def __init__(self):
        super(self)
        self.__type     = ebNetDevEther

class exaBoxIBDev(exaBoxNetDev):

    def __init__(self):
        super(self)
        self.__type     = ebNetDevIB

ebNetworkInitialized  = 0
ebNetworkDiscover     = 1
ebNetworkUpdate       = 1 << 1

class exaBoxNetwork(object):

    def __init__(self, aNode):

        self.__node    = aNode
        self.__state   = None
        self.__host    = None      # Parent Host Node
        self.__devList = []        # Network device list

    # TODO: Two modes need to be supported Discover via ssh and via agent
    def mDiscover(self):

        self.__node.mConnect()
        fin, fout, ferr = self.__node.mExecuteCmd('ip -o link')
        for line in fout.readlines():
            print(line)

        self.__state = ebNetworkDiscover

    def mUpdate(self):
        pass


