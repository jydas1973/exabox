"""
 Copyright (c) 2014, 2023, Oracle and/or its affiliates. 

NAME:
    HyperVisor - Basic utilities functionality (abstract layer for KVM/Xen/OedaCli)

FUNCTION:
    Basic utilities functionality (abstract layer for KVM/Xen/OedaCli)
    xxx/MR: Additional details covering the content/functionality is required.

NOTE:
    None

History:
    pbellary     02/06/2020 - ENH 30804242 DEVELOP ABSTRACT LAYER FOR HANDLING XEN AND KVM CODE PATHS
    pbellary     02/06/2020 - ENH 30804272 DEVELOP VM OPERATIONS SUPPORT FOR KVM USING VIRSH
    siyarlag     01/22/2020 - support vm operations on x8m
    mirivier     10/05/2019 - Initial file revamping
"""

from exabox.ovm.xenvmmgr import ebXenVmMgr
from exabox.ovm.kvmvmmgr import ebKvmVmMgr
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogVerbose, ebLogJson
import abc

HVIT_UNDEFINED = 0
HVIT_XEN = 1
HVIT_KVM = 2
HVIT_HYBRID = 3
HVIT_GUEST = 4
HVIT_COMPUTE = 5

gHVINodeCache = {}

def getTargetHVIType(aTarget):

    _hviType = HVIT_UNDEFINED
    _node = exaBoxNode(get_gcontext())
    _node.mConnect(aTarget)
    _cmdstr = "imageinfo | grep 'Node type:'"
    _i, _o, _ = _node.mExecuteCmd(_cmdstr)
    if _o:
        _out = _o.readlines()
        if not _out:
            _cmdstr = "cat /sys/hypervisor/type"
            _, _o, _ = _node.mExecuteCmd(_cmdstr)
            if _o:
                _out = _o.readlines()
                if not _out:
                    _node.mDisconnect()
                    ebLogError('*** Error can not retrieve HV Instance Type from host: %s' % (aTarget))
                    return HVIT_UNDEFINED
                else:
                    _hviType = _out[0].strip().upper()
            _node.mDisconnect()
            if _hviType == 'XEN':
                return HVIT_XEN
            return HVIT_UNDEFINED
        try:
            _hviType = _out[0].split()[2]
            if _hviType == 'KVMHOST':
                return HVIT_KVM
            if _hviType == 'DOM0':
                return HVIT_XEN
            if _hviType == 'GUEST':
                return HVIT_GUEST
            if _hviType == 'COMPUTE':
                _cmdstr = "cat /sys/hypervisor/type"
                _, _o, _ = _node.mExecuteCmd(_cmdstr)
                if _o:
                    _out = _o.readlines()
                    if not _out:
                        _node.mDisconnect()
                        ebLogError('*** Error can not retrieve HV Instance Type from host: %s' % (aTarget))
                        return HVIT_COMPUTE
                    else:
                        _hviType = _out[0].strip().upper()
                    _node.mDisconnect()
                    if _hviType == 'XEN':
                        return HVIT_XEN
                else:
                    _node.mDisconnect()
                return HVIT_COMPUTE
        except:
            pass
        _node.mDisconnect()

    ebLogInfo('*** getTargetHVIType() for : %s found as : %s' % (aTarget,str(_hviType)))            

    return _hviType

def getHVInstance(aTarget, aOptions=None):
    
    _hvAttributes={'hostname':aTarget}

    global gHVINodeCache
    if aTarget in gHVINodeCache.keys():
        return gHVINodeCache['aTarget']

    _hviType = getTargetHVIType(aTarget)
    _hvMgr   = None
    if _hviType == HVIT_XEN: 	
        _hvMgr = ebXenVmMgr(_hvAttributes)

    if _hviType == HVIT_KVM: 	
        _hvMgr = ebKvmVmMgr(_hvAttributes)
     
    if _hvMgr == None :
        if _hviType == HVIT_COMPUTE :
            raise ExacloudRuntimeError(0x919, 0xA,
                                   'Invalid Node type %s' %(str(_hviType)),
                                   aStackTrace=False)
        else :
            raise ExacloudRuntimeError(0x920, 0xA,
                                   'Unexpected Response %s' %(str(_hviType)),
                                   aStackTrace=False)


    gHVINodeCache['aTarget'] = _hvMgr

    ebLogDebug('*** getHVInstance for host: %s returned: %s' % (aTarget,str(_hviType)))

    return _hvMgr

# TODO: xxx/MR: Check target node HV Type using remote check via kvm/libvirt driver
def isKVM(aHostname):
	raise NotImplementedError

class ebVgBase(metaclass=abc.ABCMeta):

    def __init__(self, *initial_data, **kwargs):
        super(ebVgBase, self).__init__()

    @abc.abstractmethod
    def mDispatchEvent(self, aCmd, aOptions=None, aVMId=None):
        """ Dispatch Event"""

class SingletonBase(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(SingletonBase, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class ebVgCompRegistry(metaclass=SingletonBase):

    __component = {}

    def mRegisterComponent(self, aCompType, aVirtGuestObj):
        _type = aCompType
        self.__component[_type] = aVirtGuestObj

    def mGetComponent(self, aCompType):
        _type = aCompType
        _handle = None
        if self.__component and _type in self.__component.keys():
            _handle = self.__component[_type]
        return _handle
