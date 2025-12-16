#
# $Header: ecs/exacloud/exabox/ovm/sysimghandler.py /main/47 2025/12/01 22:37:00 avimonda Exp $
#
# sysimghandler.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      sysimghandler.py - System Image Handler
#
#    DESCRIPTION
#      Auxiliary functions to handle system VM Images in the cluters.
#
#    NOTES
#
#    MODIFIED   (MM/DD/YY)
#    avimonda    10/31/25 - Bug 38427813 - Enhance the robustness of image
#                           checksum validation.
#    jfsaldan    10/28/25 - Changes by AiDEr
#    jfsaldan    10/28/25 - Bug 38559314 - EXADBXS Y25W42 | CREATEVM FAILED | 2
#                           DOM0S HAVE DIFFERENT IMAGE VERSION | PARALLEL
#                           CREATE SERVICE 'B' WITH DIFFERENT FIRST.BOOT IMAGE
#                           SELECTED DELETED FIRST.BOOT IMAGE OF OPERATIONS 'A'
#    prsshukl    09/08/25 - Bug 38313259: Fix RTG image copy during node
#                           recovery
#    scoral      08/23/25 - Bug 38318254 - Improve resilience for u02 unmount
#    avimonda    07/23/25 - Bug 38151443 - EXACS: PROVISIONING FAILED WITH
#                           EXACLOUD ERROR CODE: 1793 EXACLOUD : SOMETHING
#                           WRONG HAPPENED WHILE IN FTL | ATP | U02 VOLUME NOT
#                           PROPERLY MOUNTED/CREATED
#    gparada     06/02/25 - 37963204 Fix for System Image in hybrid infra
#    bhpati      05/27/25 - Bug 37860899 - Fix mIsRtgImgPresent if NoneType
#                           object returned
#    pbellary    05/21/25 - Enh 37927692 - EXASCALE: EXACLOUD TO SUPPORT CREATION OF EDV FOR /U02 FOR THE VM IMAGE ON EDV (IMAGE VAULT)
#    gparada     04/24/25 - 37872666 Fix mGetSystemImageVersionMap regex for img
#    jfsaldan    04/03/25 - Enh 37647115 - EXACLOUD - REDUCE
#                           COMPRESSION/DECOMPRESSION TIME FOR SYSTEM IMAGE.
#                           REPLACE BZIP2 BY PBZIP2 OR SIMILAR
#    scoral      03/20/25 - Bug 37736043 - Make sure disk devices are attached
#                           with cache='none' & io='native' options if they are
#                           EDVs.
#    gparada     01/27/25 - Bug 37450961 Fallback to IMG file if RGT not present
#    gparada     12/04/24 - Bug 37333804 Fix mGetImageFromDom0ToLocal for exacc
#    gparada     10/16/24 - Bug 37159840 Fix regression (typo by mistake)
#    naps        10/04/24 - Bug 37134868 - Activate domu vg if not active.
#    prsshukl    08/06/24 - Bug 36910001 - Add Dom0 lock for System Image
#                           transfer
#    gparada     05/14/24 - 36603685 Handle *.rtg.img files for >=24.1
#                           RTG = Ready To Go
#    gparada     03/25/25 - 36409407 Avoid corrupt file, add retry in mCopyFile
#    jesandov    04/04/24 - 36482990: Add mBuildVDiskHost
#    remamid     03/02/24 - Remove metadata_csum feature from u02 if DomU is
#                           OL7 and Dom0 is OL8 bug 36360004
#    gparada     11/22/23 - Skip Custom Img code for ExaDB-XS/ExaCompute
#    aararora    10/16/23 - Bug 35893125: Copy System image from local to DOM0
#                           not having the image.
#    gparada     10/03/23 - 35866764 allow_domu_custom_version=False MAIN ExaCC
#    scoral      10/03/23 - Bug 35862910 - Refactor all DomU /u02 filesystem
#                           creation methods for KVM envs.
#    gparada     08/16/23 - 35664499 + Scoral Use hasDomUCustomOS for 
#                                    ExaCS & ExaCC
#    gparada     08/07/23 - 35669682 Flag DomU Custom Version Picking Algorithm
#    gparada     07/10/23 - 35529689 Refactor cluctl.mGetMinSystemImageVersion 
#                           and moved here as mGetDom0sImagesListSorted 
#    gparada     06/07/23 - 35402940 ECRA can define OS version to setup in VM
#    araghave    04/28/22 - Bug 34094559 - REVERTING THE CHANGES FOR ENH
#                           33729129
#    araghave    01/06/22 - Enh 33729129 - Provide both .zip and .bz2 file
#                           extension support on System image files.
#    jlombera    03/22/21 - Bug 32652512: use correct path to bunzip2(1)
#    jlombera    08/27/20 - Bug 31809001: system images in Dom0 must not have
#                           the '.kvm' part
#    dekuckre    07/23/20 - 31658105: Search non-KVM img post KVM img search.
#    jlombera    07/20/20 - Bug 31607257: add auxilary functions to handle KVM
#                           images
#    jlombera    07/20/20 - Creation
#

import datetime
import os
import re
import time
import uuid

from typing import Optional, Dict, List, Tuple, TYPE_CHECKING

from exabox.BaseServer.AsyncProcessing import ProcessManager, ProcessStructure
from exabox.core.Context import get_gcontext
from exabox.core.Error import ebError, ExacloudRuntimeError
from exabox.core.Node import exaBoxNode
from exabox.exadbxs.edv import EDVInfo, EDVState
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogWarn, ebLogDebug, ebLogTrace
from exabox.ovm.cludomufilesystems import attach_dom0_disk_image, create_new_lvm_disk_image, ebDiskImageInfo, fill_disk_with_lvm_partition, parse_size, shutdown_domu, start_domu
from exabox.ovm.clumisc import ebCluPreChecks, mGetDom0sImagesListSorted
from exabox.scheduleJobs.kms_module import ebKmsObjectStore
from exabox.utils.common import version_compare
from exabox.utils.node import (connect_to_host, node_cmd_abs_path_check,
    node_exec_cmd, node_exec_cmd_check, node_cmd_abs_path)

from exabox.exakms.ExaKmsEntry import ExaKmsEntry, ExaKmsHostType

# We need to import exaBoxCluCtrl for type annotations, but it will cause a
# cyclic-import at runtime.  Thus we import it only when type-checking.  We
# still need to define type exaBoxCluCtrl or pylint will complain, though, so
# we just make it an alias to 'object' when not type-checking.
if TYPE_CHECKING:
    from exabox.ovm.clucontrol import exaBoxCluCtrl
else:
    exaBoxCluCtrl = object  # pylint: disable=invalid-name

# Location where VM images are stored in the Dom0
__DOM0_VM_IMAGE_LOC = '/EXAVMIMAGES/'

# Relative location where the VM images repository
__REPO_VM_IMAGE_REL_LOC = 'images/'

def getDom0VMImageLocation():
    # type: () -> str
    """
    Get the location where VM Images are stored in Dom0.

    :return: The location where VM Images are stored
    :rtype: str
    """
    return __DOM0_VM_IMAGE_LOC

def __getVMImageShellPattern(aIsKvm=False, aIsRtg=False):
    # type: (bool) -> str
    """
    Get VM Image base name shell pattern.

    The pattern returned can be used in shell commands to match against
    (uncompressed) VM Image file.  For instance: 'ls <pattern>'.

    :param bool aIsKvm: Whether return pattern for a KVM image
    :param bool aIsRtg: Whether return pattern for a RTG image
    :return: The VM Image shell pattern
    :rtype: str
    """

    if aIsRtg:
        return 'System.first.boot.*.rtg.img'
    elif aIsKvm:
        return 'System.first.boot.*.kvm.img'
    else:
        return 'System.first.boot.*.img'

def formatVMImageBaseName(aVersion, aIsKvm=False, aIsRtg=False):
    # type: (str, bool) -> str
    """
    Format the basename non-/KVM VM image for the given version.

    :param str aVersion: Version of the image
    :param str aIsKvm: Whether a KVM image
    :param str aIsRtg: Whether a RTG image
    :return: The formated image basename
    :rtype: str
    """
    if aIsRtg:
        return 'System.first.boot.{}.rtg.img'.format(aVersion)
    elif aIsKvm:
        return 'System.first.boot.{}.kvm.img'.format(aVersion)    
    else:
        return 'System.first.boot.{}.img'.format(aVersion)

def mIsRtgImg(aVmImgVerNum:str) -> bool:
    """
    aVmImgVerNum: "24.1.0.0.0",
    """
    _config_opts = get_gcontext().mGetConfigOptions()
    _arg_options = get_gcontext().mGetArgsOptions()

    if get_gcontext().mCheckRegEntry("aOptions"):
        _arg_options = get_gcontext().mGetRegEntry("aOptions")

    def mIsRtgImageSupported(aVmImgVerNumX):
        if version_compare(aVmImgVerNumX, "24.1") >= 0:
            ebLogTrace("RTG is enable in Exadata 24.1+ version or greater")
            return True
        else:
            ebLogTrace("RTG is disable in Exadata 23.1 version or lower")
            return False

    # For production we will allow this feature to be enabled based on service
    # ExaCC
    if "ociexacc" in _config_opts.keys() \
        and _config_opts["ociexacc"] == "True" \
        and "rtg_enabled_exacc" in _config_opts.keys():
        _config_val = _config_opts["rtg_enabled_exacc"]
        if str(_config_val).lower() == "false":
            ebLogTrace("RTG is disable in ExaCC by exabox.conf parameter")
            return False
        else:
            ebLogTrace("RTG is enable in ExaCC by exabox.conf parameter")
            return mIsRtgImageSupported(aVmImgVerNum)

    # Exascale
    if _arg_options is not None and _arg_options.jsonconf is not None and \
           "storageType" in list(_arg_options.jsonconf.keys()) and \
           str(_arg_options.jsonconf['storageType'].upper()) == "EXASCALE":
        if "rtg_enabled_exadbxs" in _config_opts.keys():
            _config_val = _config_opts["rtg_enabled_exadbxs"]
            if str(_config_val).lower() == "false":
                ebLogTrace("RTG is disable in ExaDB-XS by exabox.conf parameter")
                return False
            else:
                ebLogTrace("RTG is enable in ExaDB-XS by exabox.conf parameter")
                return mIsRtgImageSupported(aVmImgVerNum)

    # ExaCS
    if "rtg_enabled_exacs" in _config_opts.keys():
        _config_val = _config_opts["rtg_enabled_exacs"]
        if str(_config_val).lower() == "false":
            ebLogTrace("RTG is disable in ExaCS by exabox.conf parameter")
            return False

    ebLogTrace("RTG is enable in ExaCS by exabox.conf parameter")
    return mIsRtgImageSupported(aVmImgVerNum)


def __getVMImageInfo(aFile):
    # type: (str) -> Optional[ImageDict]
    """
    Get VM Image info from a file name.

    If the given file name is a valid VM Image, returns a dictionary
    with the following fields:
      'filePath': the same file name received as parameter
      'fileBaseName': os.path.basename() of the file name
      'imgBaseName': basename of the uncompressed image
      'imgArchiveBaseName': basename of the compressed image
      'imgVersion': version of the VM image
      'isKvmImg': whether it is KVM VM image
      'isRtgImg': whether it is RTG VM image (introduced after 24.1)
      'isArchive': whether 'filePath' is a compressed VM image

    If the file name is not a valid VM image, None is returned.

    NOTE: this function does not check whether the file name actually
          exists, it just gets the information based on the file name.

    :param str aFile: The file name
    :return: A dictionary with the information or None
    :rtype: dict
    """

    baseName = os.path.basename(aFile)
    regex = r'^(System\.first\.boot\.((?:\d+\.)*\d+)(\.kvm)?(\.rtg)?\.img)(\.bz2)?$'
    match = re.search(regex, baseName)

    if match is not None:
        imgBaseName = match.group(1)
        version = match.group(2)
        isKvm = (match.group(3) is not None) 
        isRtg = (match.group(4) is not None)
        isArchive = (match.group(5) is not None)
       
        if isArchive:
            archiveName = baseName
        else:
            archiveName = baseName + '.bz2'

        return {'filePath': aFile,
                'fileBaseName': baseName,
                'imgBaseName': imgBaseName,
                'imgArchiveBaseName': archiveName,
                'imgVersion': version,
                'isKvmImg': isKvm,
                'isRtgImg': isRtg,
                'isArchive': isArchive}
    else:
        return None  # not a proper VM Image name

def __getVMImagesInRepo(aImageBaseLocation=None):
    # type: (Optional[str]) -> List[ImageDict]
    """
    Get information of existing VM images in the repository.

    Returns the information (as returned by __getVMImageInfo()) of all
    the VM images in the repository.  If aImageBaseLocation is not None,
    it will be used as base (prefix) for the repository.

    :param str aImageBaseLocation: An optional base directory
    :return: The information of all the VM images in the repository
    :rtype: List[dic]
    """

    if aImageBaseLocation is None:
        aImageBaseLocation = os.path.abspath('.')

    repoDir = os.path.join(aImageBaseLocation, __REPO_VM_IMAGE_REL_LOC)
    ebLogInfo(f'__getVMImagesInRepo will search in {repoDir}')

    images = []
    if os.path.isdir(repoDir):        
        for f in os.listdir(repoDir):
            filePath = os.path.join(repoDir, f)

            if os.path.isfile(filePath):
                imgInfo = __getVMImageInfo(filePath)

                if imgInfo is not None:
                    images.append(imgInfo)

    ebLogTrace('Found Images {} in Repodir {}'
                .format(images, repoDir))
    return images

def getVMImageArchiveInRepo(aVersion, aIsKvm, aIsRtg, aImageBaseLocation=None):
    # type: (str, bool, Optional[str]) -> Optional[ImageDict]
    """
    Get information of a VM image of a specific version in the repository.

    Searches for a compressed VM image of a specific version and type
    (KVM or not) in the repository.  If found, returns its information
    (as returned by __getVMImageInfo()); returns None otherwise.

    :param str aVersion: Version of the image to look for
    :param bool aIsKvm: Whether look for KVM images
    :param bool aIsRtg: Whether look for RTG images
    :param str aImageBaseLocation:
        Optional base location for the repository
    :return: The information about the image; None if not found
    :rtype: dict
    """

    imgInfos = __getVMImagesInRepo(aImageBaseLocation)

    # return image that:
    #  a) is an archive; and
    #  b) the version matches aVersion; and
    #  c) is a non-/kvm image according to aIsKvm
    
    # When RTG is validated, by default it is considered KVM
    # but the RTG image file only has RTG prefix (in other words, 
    # kvm.rtg.img does NOT exist). Hence, forcing isKvmImg to be false.
    if aIsRtg:
        aIsKvm = False

    for img in imgInfos:
        ebLogTrace(f'Validating {img} in Local Image Repo')
        if (img['isArchive'] == True
              and img['imgVersion'] == aVersion
              and img['isKvmImg'] == aIsKvm
              and img['isRtgImg'] == aIsRtg 
              ):
            ebLogInfo(f'Image Match: {img} in Local Image Repo')
            return img
    else:
        ebLogInfo('No Image Match in Local Image Repo for '
            f'aVersion:{aVersion} aIsKvm:{aIsKvm} aIsRtg: {aIsRtg}')
        return None

def getNewestVMImageArchiveInRepoNodeRecovery(aImageBaseLocation=None):
    # type: (Optional[str]) -> Optional[ImageDict]
    """
    Get information of the newest VM image in the repository.

    Returns information (as returned by __getVMImageInfo()) of the
    newest VM image of the given type (RTG or KVM or not) in the repository.
    Returns None, if no image is found.

    :param str aImageBaseLocation:
        An optional base location for the repository
    :return: The information about the image; None if not found
    :rtype: dict
    """

    def __getVMImgVersionIntComponents(aImg):
        # type: (ImageDict) -> Tuple[int, ...]
        """Get the version of the VM image as a list of ints"""
        return tuple(map(int, aImg['imgVersion'].split('.')))

    imgInfos = __getVMImagesInRepo(aImageBaseLocation)

    newestImg = None
    for img in imgInfos:
        if newestImg is None:
            newestImg = img
        else:
            newestImg = max(newestImg, img,
                            key=__getVMImgVersionIntComponents)

    return newestImg

def getNewestVMImageArchiveInRepo(aIsKvm, aImageBaseLocation=None):
    # type: (bool, Optional[str]) -> Optional[ImageDict]
    """
    Get information of the newest VM image in the repository.

    Returns information (as returned by __getVMImageInfo()) of the
    newest VM image of the given type (KVM or not) in the repository.
    Returns None, if no image is found.

    :param bool aIsKvm: Whether to look for a KVM image
    :param str aImageBaseLocation:
        An optional base location for the repository
    :return: The information about the image; None if not found
    :rtype: dict
    """

    def __getVMImgVersionIntComponents(aImg):
        # type: (ImageDict) -> Tuple[int, ...]
        """Get the version of the VM image as a list of ints"""
        return tuple(map(int, aImg['imgVersion'].split('.')))

    imgInfos = __getVMImagesInRepo(aImageBaseLocation)

    newestImg = None
    for img in imgInfos:
        if img['isKvmImg'] == aIsKvm:
            if newestImg is None:
                newestImg = img
            else:
                newestImg = max(newestImg, img,
                                key=__getVMImgVersionIntComponents)

    return newestImg

def copyVMImageVersionToDom0IfMissing(
        aDom0:str, 
        aVersion:str, 
        aIsKvm:bool,
        aImageBaseLocation:Optional[str]=None, 
        aForceRtg:bool=False,
        aImageInfo:Optional[Tuple[str,...]]=None,
        aLocalFileHash:Optional[Dict[str, str]]=None):
    # type: (str, str, bool, Optional[str]) -> Tuple[bool, Optional[ImageDict], bool]
    """
    Copy VM image from the repository to a remote Dom0 if not already there.

    Looks for a non-/KVM VM image of the specified version in the
    specified Dom0.  If not found, searches for the image in the local
    repository and, if found, copies it to the Dom0.

    A triple (remoteImgFound, localImgInfo, imgCopied) is returned,
    where:
      remoteImgFound: Whether the image was found in the Dom0.
      localImgInfo: Information of the image in the local repository
                    (as returned by __getVMImageInfo()).  Will be None
                    if remoteImgFound==True or no image found in the
                    local repository.
      imgCopied: Whether the image in the local repository was copied to
                 the Dom0.  Will be False if remoteImgFound==True or
                 localImgInfo==None.

    A return value of (True, <no_None_value>, False) means there was an
    error while copying the image from the local repository to the Dom0.

    NOTE: If a KVM image is requested but not found, we will fallback to
          a non-KVM image.  A warning will be logged in this case.

    NOTE2: KVM images in the Dom0 will always be stripped of the '.kvm'
           part in the file name.  Either if originally found there or
           copied from the local repository.

    :param str aDom0: The Dom0 to copy the image to
    :param str aVersion: The version of the image to copy
    :param bool aIsKvm: Whether to look for a KVM image
    :param str aImageBaseLocation:
        An optional base location for the repository
    :param aForceRtg: Force RTG image sync when supported but not on all Dom0s.
    :param aImageInfo: The information about the image
    :param aLocalFileHash: Dict mapping local file -> checksum 
    :return:
        Whether the image was found in the Dom0/repository and copied to
        the first.
    :rtype: (bool, dict, bool)
    """
    
    # RTG logic does not apply on XEN 
    if not aIsKvm: 
        aIsRtg = False
        aForceRtg = False        
    else:
        aIsRtg = mIsRtgImg(aVersion)

    ebLogInfo('*** Copying VM image to remote Dom0: host={}'
        ' ver={} kvm={} rtg={} aForceRtg={}'
        .format(aDom0, aVersion, aIsKvm, aIsRtg, aForceRtg))

    remoteImgFound = False
    imgInfo = None
    imgCopied = False

    try:
        remoteImgLoc = getDom0VMImageLocation()
        imgBaseName = formatVMImageBaseName(aVersion, aIsKvm, aIsRtg) 
        remoteImgFile = os.path.join(remoteImgLoc, imgBaseName)
        ebLogInfo('**** Looking for image file (1st attempt): {}'
                  .format(remoteImgFile))

        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=aDom0)
        remoteImgFound = node.mFileExists(remoteImgFile)
        
        # If we know in advance that RTG will be used (because some Dom0 has it)
        # then aForceRtg is True, and hence we must be sure this img is used.
        # No need to check further and we need to get from local, so we skip 
        if not aForceRtg:

            if not remoteImgFound: #  NON_RTG
                ebLogInfo('**** Remote VM image {} not found in Dom0 {}'
                            .format(remoteImgFile, aDom0))
                imgBaseName = formatVMImageBaseName(aVersion, aIsKvm, False) 
                remoteImgFile = os.path.join(remoteImgLoc, imgBaseName)
                ebLogInfo('**** Looking for image file (2nd attempt): {}'
                        .format(remoteImgFile))
                remoteImgFound = node.mFileExists(remoteImgFile)

            if not remoteImgFound and aIsKvm: # NON_KVM Force look for NON_RTG img
                ebLogInfo('**** Remote VM image {} not found in Dom0 {}'
                            .format(remoteImgFile, aDom0))
                imgBaseName = formatVMImageBaseName(aVersion, False, False) 
                remoteImgFile = os.path.join(remoteImgLoc, imgBaseName) 
                ebLogInfo('**** Looking for image file (3rd attempt): {}'
                        .format(remoteImgFile))
                remoteImgFound = node.mFileExists(remoteImgFile)

        if remoteImgFound:
            ebLogInfo('**** Found remote VM image {} in Dom0 {}'
                        .format(remoteImgFile, aDom0))
            ebLogInfo('**** Skipping copy')
        else:
            ebLogInfo('**** Remote VM image {} not found in Dom0 {}'
                        .format(remoteImgFile, aDom0))

            if aImageInfo is None:
                imgInfo = mGetVMImageArchiveInfoInLocalRepo(aVersion, aImageBaseLocation)
            else:
                imgInfo = aImageInfo

            if imgInfo is None:
                ebLogError('**** No suitable VM image with version {} found in'
                             ' local repository... Aborting'.format(aVersion))
            else:
                localArchive = imgInfo['filePath']
                remoteArchive = os.path.join(remoteImgLoc,
                                             imgInfo['imgArchiveBaseName'])
                remoteImgFile = os.path.join(remoteImgLoc,
                                             imgInfo['imgBaseName'])

                ebLogInfo('**** Found VM image archive {} in local repository'
                            .format(localArchive))

                # System.fist.boot is 2-3 Gb size, so do checksum to verify and
                # if needed, retry until 3 times until file is correct.
                node.mCopyFile(localArchive, remoteArchive, 3)

                _checksum_rtn = node.mCompareFiles(localArchive, remoteArchive, aLocalFileHash)
                if not _checksum_rtn:
                    _msg = f'Checksum verification failed for {remoteArchive} on Dom0 {aDom0}.'
                    ebLogError(_msg)
                    raise ExacloudRuntimeError(0x0779, 0xA, _msg)

                # Check if pbunzip exists (it should but we'll have this
                # small nice check)
                bin_unzip = node_cmd_abs_path(node, 'pbunzip2', sbin=True)
                if not bin_unzip:
                    bin_unzip = node_cmd_abs_path_check(node, 'bunzip2')

                # decompress image
                cmd = f'{bin_unzip} {remoteArchive}'

                _, _, stderr = node.mExecuteCmd(cmd)
                rc = node.mGetCmdExitStatus()

                if rc == 0:
                    ebLogInfo('**** Successfully transfered VM image {} to '
                                'remote Dom0 {}'.format(imgBaseName, aDom0))
                    imgCopied = True
                    _remote_file = os.path.join('/EXAVMIMAGES', imgBaseName)
                    if node.mFileExists(_remote_file):
                        ebLogInfo(f"Touching image file to change its timestamp")
                        _bin_touch = node_cmd_abs_path_check(node, "touch", sbin=True)
                        _cmd = f"{_bin_touch} {_remote_file}"
                        node_exec_cmd_check(node, _cmd)
                    else:
                        ebLogError(f'**** File {_remote_file} not '
                            f'touched as not found in {aDom0}')
                else:
                    ebLogError('**** An error occurred while decompressing VM '
                                 'image {} in remote Dom0 {}'
                                 .format(remoteArchive, aDom0))
                    ebLogError('***** rc: {}, stderr:\n{}'.format(rc, stderr.read()))

        # We must be sure that file name of the image in the Dom0 does not have
        # the '.kvm' part and strip it if it does.
        if remoteImgFound or imgCopied:
            remoteImgInfo = __getVMImageInfo(remoteImgFile)
            if not imgInfo:
                imgInfo = remoteImgInfo
            if remoteImgInfo is not None:
                if remoteImgInfo['isKvmImg'] == True:
                    nonKvmBaseImgName = formatVMImageBaseName(aVersion,
                                                              aIsKvm=False)
                    newRemoteImgFile = os.path.join(remoteImgLoc,
                                                    nonKvmBaseImgName)

                    cmd = f'/bin/mv {remoteImgFile} {newRemoteImgFile}'
                    _, _, stderr = node.mExecuteCmd(cmd)
                    rc = node.mGetCmdExitStatus()

                    if rc == 0:
                        ebLogInfo(f'**** Renamed system image {remoteImgFile} '
                                    f'to {newRemoteImgFile} in Dom0 {aDom0}')
                    else:
                        ebLogError('**** An error occurred while renaming '
                                     f'system image {remoteImgFile} to '
                                     f'{newRemoteImgFile} in Dom0 {aDom0}\n'
                                     f'  rc: {rc}, stderr: {stderr.read()}')
                        remoteImgFound = False
                        imgCopied = False

            else:
                raise ValueError(f'{remoteImgFile} is not a valid image name')
    finally:
        node.mDisconnect()

    if not imgInfo:
        imgInfo = getVMImageArchiveInRepo(aVersion, aIsKvm, aIsRtg, aImageBaseLocation)

    return (remoteImgFound, imgInfo, imgCopied)

def getDom0VMImagesInfo(aDom0, aComputeMd5Sum=False, aComputeSha256Sum=False):
    # type: (str, bool, bool) -> Optional[List[ImageDict]]
    """
    Get information of the VM images in a Dom0.

    Return the information (as returned by __getVMImageInfo()) of all
    the VM images in the given Dom0.  Optionally can compute the
    md5sum/sha256sum of the images, in which case a 'md5sum'/'sha256'
    field will be added to the information dictionary with the value
    of the hash respectively; this value will be None if there was an
    error computing the hash.

    On error, None is returned.  If no images are found in Dom0, an
    empty list is returned.

    :param str aDom0: Dom0 to the information from
    :param bool aComputeMd5Sem: Wether compute the md5sum of the images
    :param bool aComputeSha256Sem:
        Wether compute the sha256sum of the images
    :return: A list with the information of the images
    :rtype: List[dict]
    """

    def __getDom0VMImageHash(_aDom0, _aNode, _aImgFile, _aHashType):
        # type: (str, exaBoxNode, str, str) -> Optional[str]
        hash_cmd = _aHashType + ' ' + _aImgFile
        imgHash = None
        _, out, err = _aNode.mExecuteCmd(hash_cmd)

        if _aNode.mGetCmdExitStatus() == 0:
            imgHash = out.readline().split(' ')[0]
        else:
            ebLogError('*** Failed to compute {} of VM image {} in '
                         'Dom0 {}'.format(_aHashType, _aImgFile, _aDom0))
            ebLogError('**** stderr:\n{}'.format(err.read()))

        return imgHash

    imgInfos = None
    try:
        node = exaBoxNode(get_gcontext())
        node.mConnect(aHost=aDom0)

        imgNamePattern = __getVMImageShellPattern()
        ls_cmd = 'ls {}'.format(os.path.join(getDom0VMImageLocation(),
                                             imgNamePattern))

        _, out, err = node.mExecuteCmd(ls_cmd)

        if node.mGetCmdExitStatus() == 0:
            # compute image info of valid image files
            imgInfos = []
            for img in out.read().splitlines():
                info = __getVMImageInfo(img)

                if info is not None:
                    if aComputeMd5Sum:
                        info['md5sum'] = __getDom0VMImageHash(aDom0, node, img,
                                                              'md5sum')

                    if aComputeSha256Sum:
                        info['sha256sum'] = \
                          __getDom0VMImageHash(aDom0, node, img, 'sha256sum')

                    imgInfos.append(info)

        else:
            ebLogError('*** Unable to get list of VM images in Dom0 {}'
                         .format(aDom0))
            ebLogError('**** stderr:\n{}'.format(err.read()))
    finally:
        node.mDisconnect()

    return imgInfos

def hasDomUCustomOS(aExaBoxCluCtrlObj: exaBoxCluCtrl) -> Optional[str]:
    """
    Parses payload and checks if image_version is requested by ECRA

    This confluence contains more info about the Payload sent by ECRA
    https://confluence.oraclecorp.com/confluence/display/
        DCLS/EXACS-105073_ExaCS%3A+Support+Exadata+23.1_FDS

    ECRA Payloads
    https://confluence.oraclecorp.com/confluence/display/
        EDCS/API+Payloads+from+ECRA+to+ExaCloud

    Below is an example of how the payload may define image_version:

    # CREATE SERVICE
    "operation": "create-service",
    "rack": {
        "backup_disk": false,
        "cores": 10,
        "create_sparse": "false",
        "ecra_db_rack_name": "exacompute-iad1-d2-x8-x4-x4-x4-x12-clu01",
        "gb_memory": "400",
        "gb_storage": 1024,
        "id": "ff748d37-2cde-48f7-bc61-a7bd41d85bea",
        "model": "X8M-2",
        "os_version": "ol7",
        "image_version": "22.2.1.032223",
        "name": "VmCluster72",
        "size": "ELASTIC-RACK",
        "tb_storage_": "1"
    }

    # ADD COMPUTE
    ...
    "rackname": "iad103714exd-d0-05-06-cl-07-09-clu01",
    "reshaped_node_subset": {
        "added_computes": [...]
    },
    "image_version": "22.2.1.032223",
    ...

    :param aExaBoxCluCtrlObj: CluControl Obj

    Dom0s
        21.X    22.X    23.X
    XEN OL6     OL7     OL7
    KVM OL7     OL7     OL8
    
    DomUs
        21.X    22.X    23.X
    XEN OL7     OL7     OL8
    KVM OL7     OL7     OL8

    :returns Opt String: String with the Custom Img Version found
    """
    _eBox:exaBoxCluCtrl = aExaBoxCluCtrlObj
    aOptions = _eBox.mGetArgsOptions()
    _exadata_model = _eBox.mGetExadataDom0Model()
    defaultDomUImgVer = None

    # Check1. Payload.
    # If payload from ECRA has a domU Exadata version
	# - provision the vm cluster with that version for the domUs
    if not defaultDomUImgVer and aOptions.jsonconf:
        rack = aOptions.jsonconf.get("rack", {})            
        image_version = rack.get("image_version", 
                                 aOptions.jsonconf.get("image_version"))
        if image_version:
            defaultDomUImgVer = image_version
            ebLogInfo(f"Custom DomU Image {defaultDomUImgVer} detected from 'image_version' from payload")
            return defaultDomUImgVer

    # Check2. ExaCC scenario.
    # If exabox.conf property exadata_custom_domu_version is defined
    if _eBox.mIsOciEXACC():
        defaultDomUImgVer = _eBox.mCheckConfigOption('exadata_custom_domu_version')
        if defaultDomUImgVer:
            ebLogInfo(f"Custom DomU Image {defaultDomUImgVer} detected from 'exadata_custom_domu_version' from exabox.conf")
            return defaultDomUImgVer
        
    # Check3a. X10.
    # If payload from ECRA does NOT have a domU Exadata version, then
    # - if dom0s are x10m, then domU version is same as dom0 version
    if _eBox.mCompareExadataModel(_exadata_model, 'X10') >= 0:
        ebLogInfo("Custom Version is None because of X10. " +
                  "If dom0s are x10m, then domU version is same as dom0 version.")
        return None

    # Check3b. ExaDB-XS
    # If payload from ECRA does NOT have a domU Exadata version, then
    # - if service type is ExaDB-XS, then domU version is same as dom0 version
    if _eBox.mIsExaScale():
        ebLogInfo("Custom Version is None because of ExaDB-XS. " +
                "If service type is ExaDB-XS, then domU version is same as dom0 version.")
        return None

    # Check4. Main flag (switch) for Handling Custom Image.    
    _featureFlag = 'allow_domu_custom_version'
    if not _eBox.mCheckConfigOption(_featureFlag, 'True'):
        ebLogInfo(f"Custom Version is None because of {_featureFlag} flag")
        return None

    # Check5. Read ExaCS property.
    # - if dom0s are < X10M, then (execution is here after "Check3")
    #   - if exabox.conf param has hardcoded domU version, provision domUs with that version
    _exaboxConfVersion = 'default_domu_img_version'
    defaultDomUImgVer = _eBox.mCheckConfigOption(_exaboxConfVersion)
    if defaultDomUImgVer:
        ebLogInfo(f"Custom DomU Image {defaultDomUImgVer} detected from '{_exaboxConfVersion}' from exabox.conf")
        return defaultDomUImgVer

    
    # Check6. Exadata < 23.1.0
    # - if dom0s are < X10M, then (execution is here after Check3)
    #   - if no exabox.conf param for domU version (after Check5)
    #     - if dom0s are < 23.1.0, then domU version is same as dom0 version (hence OL7)    

    # Check7. Exadata >= 23.1.0
    # - if dom0s are < X10M, then (execution is here after Check3)
    #   - if no exabox.conf param for domU version (after Check5)
    #     - if dom0s are >= 23.1.0, then hardcode domU version to be 22.1.10 (hence OL7)
    # In other words:
    # If not custom version specified, use the same DomU version as the Dom0 version depending on the Dom0 version.

    dom0sImagesVersion = mGetDom0sImagesListSorted(_eBox)
    
    # Check7. 
    if all( version_compare(img, "23") > 0 for img in dom0sImagesVersion):        
        # From https://confluence.oraclecorp.com/confluence/display/EIP/Exadata+Cloud+Service+Software+Versions#ExadataCloudServiceSoftwareVersions-21.1.12
        _exaboxConfLastResource = "default_domu_img_version_last_res"
        _domUVersion = _eBox.mCheckConfigOption(_exaboxConfLastResource)
        if not _domUVersion:
            ebLogError(f"{_exaboxConfLastResource} is required.")
            raise ValueError(f'{_exaboxConfLastResource} is required.')
        ebLogInfo(f"Custom DomU version {_domUVersion} from '{_exaboxConfLastResource}' from exabox.conf")
        return _domUVersion

    # Check6.
    ebLogInfo(f"No custom DomU version configuration detected, using same version as Dom0.")
    return None

def mGetSystemImageVersionMap(aEboxObj: exaBoxCluCtrl) -> Dict[str, list]:
    """
    Retrieves a list of files with format 
      'System.first.boot.[0-9\.]*(\.rtg)?.img$'
    And strips(clean spaces) for such list     
    This function returns an dict with dom0 as key and list of str 
    {
        "dom0_01" : ['/EXAVMIMAGES/System.first.boot.22.1.10.0.0.230527.img', 
                     '/EXAVMIMAGES/System.first.boot.23.1.2.0.0.230523.img'],
        "dom0_02" : ['/EXAVMIMAGES/System.first.boot.22.1.1.0.0.YYMMDD.img', 
                     '/EXAVMIMAGES/System.first.boot.23.1.2.0.0.YYMMDD.img']
    }
    """
    _ebox = aEboxObj
    _versionMap = {}
    for _dom0, _ in _ebox.mReturnDom0DomUPair():
        _versionMap[_dom0] = ""
        with connect_to_host(_dom0, get_gcontext()) as _node:
            _cmd = "/bin/ls /EXAVMIMAGES " \
                   "| /bin/grep -E 'System.first.boot.[0-9\.]*(\.rtg)?.img$'"
            _, _o, _ = _node.mExecuteCmd(_cmd)
            _lines = _o.readlines()
            if _lines:
                _versionMap[_dom0] = list(map(lambda x: x.strip(), _lines))

    ebLogTrace(f'Dom0s with images under /EXAVMIMAGES: {_versionMap}')
    return _versionMap

# _mExecute from clucontrol.py inside mCheckSystemImage
def mCleanOldImgsAndEnsureGivenImgInDom0(
        aEboxObj: exaBoxCluCtrl, 
        aDom0:str, 
        aImgVersion:str,          
        _rc_status:Dict[str,int],
        aForceRtg:bool=False,
        aImageInfo:Tuple[str,...]=None,
        aImageBaseLocation:str=None,
        aLocalFileHash:Dict[str,str]=None) -> None:
    """
    Return codes will be {"dom0_01":0} on success, or {"dom0_01":0x0730} on err

    For the given aDom0, location EXAVMIMAGES will be checked/validated, so
    1) old system boot images will be deleted from this folder, and
    2) this process will ensure that given IMG aImgVersion file exists in there
    """
    ebLogInfo('Starting mCleanOldImgsAndEnsureGivenImgInDom0 '\
        f'in Dom0: {aDom0} with aImgVersion: {aImgVersion}')
    _ebox:exaBoxCluCtrl = aEboxObj

    # RTG logic does not apply on XEN 
    if not _ebox.mIsKVM():
        aForceRtg = False

    _dom0 = aDom0
    _rc_status[_dom0] = 0

    _imgrev = aImgVersion
    if not _imgrev:
        return

    _pchecks = ebCluPreChecks(_ebox)
    _pchecks.cleanup_old_system_boot_files(
        _dom0, { _imgrev, _ebox.mGetImageVersion(aDom0) })

    # 'exadata' argument is passed here to indicate exadata related
    # patches are to be fecthed from this location.
    _repo_download_location = aImageBaseLocation
    ebLogInfo('Starting mCleanOldImgsAndEnsureGivenImgInDom0 '\
        f'in Dom0: {aDom0} with aImgVersion: {aImgVersion}, _repo_download_location = {_repo_download_location}')

    if _repo_download_location is None:
        if _ebox.mGetOciExacc():
            _repo_download_location = \
                _ebox.mCheckConfigOption('ociexacc_exadata_patch_download_loc')
            ebLogTrace(f"Using ExaCC repository location: {_repo_download_location}")
        else:
            ebLogTrace('*** ociexacc parameter set to "False" in '
                            'exabox.conf.  Retaining the patch path to '
                            'default exacloud location.')

    if _repo_download_location is None:
        _msg = "Repository download location is None or empty. Cannot proceed without a valid location."
        ebLogError(_msg)
        raise ExacloudRuntimeError(0x10, 0xA, _msg)

    _succ = False
    try:
        # If Img was FOUND, for RTG we need to review which image was found.
        _remoteImgFound, _, _imgCopied = \
            copyVMImageVersionToDom0IfMissing(
                _dom0, _imgrev, _ebox.mIsKVM(), _repo_download_location, aForceRtg, aImageInfo, aLocalFileHash)

        _succ = _remoteImgFound or _imgCopied
        ebLogInfo(f'Dom0: {_dom0}, _remoteImgFound: {_remoteImgFound}, _imgCopied: {_imgCopied}')
    except Exception as copyError:
        ebLogError("Error {0}".format(copyError))
    finally:
        if not _succ:
            _rc_status[_dom0] = 0x0730

def mGetImageFromDom0ToLocal(
        aCluctrl: exaBoxCluCtrl,
        aVmImgVerNum:str, 
        aMinDom0:str,
        aForceRtg:bool=False) -> None:
    """
    If Local already contains such aImgName, it does nothing and returns
    If Local does NOT contain such aImgName, then it's copied from Dom0 to Local
    aVmImgVerNum:str with format as 22.1.10.0.0.230527
    aMinDom0:str containing a fqdm which should contain the img
    forceRtg:bool to identify if RTG is enforced
    """
    ebLogInfo(f'mGetImageFromDom0ToLocal aVmImgVerNum:{aVmImgVerNum}, aMinDom0: {aMinDom0}, forceRtg:{aForceRtg}')

    # Although formatVMImageBaseName receives second arg as flag for XEN or KVM,
    # in Dom0 we force formatVMImageBaseName to not use KVM prefix, since all
    # images WITHIN Dom0 have the same name regardless of the hypervisor.

    # RTG logic does not apply on XEN 
    _isRtgImg = False
    if aCluctrl.mIsKVM():        
        _isRtgImg = mIsRtgImg(aVmImgVerNum)
    else:
        aForceRtg = False

    _imgNameFmt = formatVMImageBaseName(aVmImgVerNum, False, _isRtgImg) 
    _imgNameBz2 = f"{_imgNameFmt}.bz2"
    _minDom0 = aMinDom0    

    # Find compressed file in images folder
    _config_opts = get_gcontext().mGetConfigOptions()    

    # ExaCC
    _repo_location = __REPO_VM_IMAGE_REL_LOC
    if "ociexacc" in _config_opts.keys() \
        and _config_opts["ociexacc"] == "True":
        _exacc_loc = _config_opts['ociexacc_exadata_patch_download_loc']
        _repo_location = os.path.join(_exacc_loc, __REPO_VM_IMAGE_REL_LOC)
        if not os.path.exists(f"{_repo_location}"):
            ebLogInfo(f'ExaCC: {_repo_location} does not exist, will create it')
            os.makedirs(_repo_location) # in exacc folder is own by ecra user

    if os.path.exists(f"{_repo_location}{_imgNameBz2}"):
        ebLogInfo(f'Found Image {_repo_location}{_imgNameBz2} - Nothing to compress.')

    if not os.path.exists(f"{_repo_location}{_imgNameBz2}") and _minDom0:        
        _node = exaBoxNode(get_gcontext())
        try:
            _node.mConnect(aHost=_minDom0)

            # Create compressed file in case of missing
            if not _node.mFileExists(f"/EXAVMIMAGES/{_imgNameBz2}"):
                ebLogInfo(f"Image will be 1: bz2'ed from {_minDom0} and 2: copied to local")
                if _node.mFileExists(f"/EXAVMIMAGES/{_imgNameFmt}"):

                    # If we have pbzip2 we use that
                    bin_zip = node_cmd_abs_path(_node, 'pbzip2', sbin=True)
                    if not bin_zip:
                        bin_zip = node_cmd_abs_path_check(_node, 'bzip2')

                    ebLogTrace(f"1: {bin_zip} from: /EXAVMIMAGES/{_imgNameFmt}")
                    node_exec_cmd_check(_node, f"{bin_zip} -k /EXAVMIMAGES/{_imgNameFmt}")
                else:
                    ebLogWarn(f"File /EXAVMIMAGES/{_imgNameFmt} not exists in dom0 {_minDom0}")

            # Copy compressed file from dom0 to images folder
            if _node.mFileExists(f"/EXAVMIMAGES/{_imgNameBz2}"):
                ebLogInfo(f"2: Copy from: /EXAVMIMAGES/{_imgNameBz2} to {_repo_location}/{_imgNameBz2}")
                _node.mCopy2Local(f"/EXAVMIMAGES/{_imgNameBz2}", f"{_repo_location}/{_imgNameBz2}")
            else:
                ebLogWarn(f"File /EXAVMIMAGES/{_imgNameBz2} not exists in dom0 {_minDom0}")
    
        finally:
            _node.mDisconnect()

def mGetImageFromOSSToLocal(
    aCluctrl: exaBoxCluCtrl,
    aVmImgVerNum:str,
    aIsKVM:bool):    
    """
    If Local already contains such aImgName, it does nothing and returns
    If Local does NOT contain such aImgName, then it's copied from OSS to Local
    """    

    # RTG logic does not apply on XEN 
    _isRtgImg = False
    if aCluctrl.mIsKVM():
        _isRtgImg = mIsRtgImg(aVmImgVerNum)

    _imgNameFmt = formatVMImageBaseName(aVmImgVerNum, aIsKVM, _isRtgImg) 
    _imgNameBz2 = f"{_imgNameFmt}.bz2"

    if not os.path.exists(f"images/{_imgNameBz2}"):
        # Download from bucket 
        _ok = ebKmsObjectStore(get_gcontext(),"ExadataSystemFirstBootRepo")
        startTime = datetime.datetime.now()
        _rc, _resp = _ok.mGetObject(_imgNameBz2)
        if _rc:
            ebLogError(f"Download error from OSS: {_imgNameBz2}")    
            raise ExacloudRuntimeError(0x10, 0xA, _resp) 
        with open(f"images/{_imgNameBz2}", 'wb') as f:
            for chunk in _resp.data.raw.stream(1024 * 1024, decode_content=False):
                f.write(chunk)
        ebLogInfo('Download time : ' + str(datetime.datetime.now() - startTime))

def mGetVMImageArchiveInfoInLocalRepo(
        aVersion: str,
        aImageBaseLocation: Optional[str] = None) -> Optional[Tuple[int,...]]:
    """
    Retrieve information of a VM image from the local repository with fallback logic.
    Automatically determines the type of image to search for (RTG, KVM, or neither).

    Args:
        aVersion (str): Version of the image to look for.
        aImageBaseLocation (Optional[str]): Optional base location for the repository.

    Returns:
        Optional[Dict]: Information about the image if found; None if no suitable image is found.
    """
    ebLogInfo('**** Looking for image file in Local Repo')

    # Step 1: Determine if the image version supports RTG (Ready To Go) based on the provided version
    _isRtg = mIsRtgImg(aVersion)
    _isKVM = False

    # Step 2: First attempt - Search for an RTG image in the local repository if RTG is applicable
    imgInfo = getVMImageArchiveInRepo(aVersion, True, _isRtg, aImageBaseLocation)

    # Step 3: If no RTG image is found and RTG is applicable, fallback to searching for a non-RTG KVM image
    if imgInfo is None and _isRtg:
        ebLogWarn('**** NO RTG IMAGE FOUND; FALLBACK TO NON-RTG IMAGE')
        imgInfo = getVMImageArchiveInRepo(aVersion, True, False, aImageBaseLocation)
        _isKVM = True

    # Step 4: If no KVM image is found and the previous search wasn't for KVM, fallback to searching for a non-KVM, non-RTG image (Xen)
    if imgInfo is None and not _isKVM:
        ebLogWarn('**** NO KVM IMAGE FOUND; FALLBACK TO NON-KVM NON-RTG IMAGE')
        imgInfo = getVMImageArchiveInRepo(aVersion, False, False, aImageBaseLocation)

    return imgInfo

def mGetLocalFileHash(aLocalFile:str) -> Optional[Dict[str, str]]:
    """
    Calculate the SHA256 checksum of a local VM image file using sha256sum command.

    Calculate the SHA256 checksum of a local VM image file for verification purposes
    using the sha256sum command, which is faster for CPU-intensive hashing. Uses
    mGetLocalFileCksum to obtain the checksum. Returns None if the checksum is not
    found or if there is an error during checksum calculation.

    Args:
        aLocalFile:str : A local VM image file

    Returns:
        Optional[str]: SHA256 checksum of the file if successful; None otherwise.
    """
    ebLogInfo(f"Calculating checksum for VM image {aLocalFile}")

    _local_file = aLocalFile
    _local_hash = None
    _hash_dict = {}

    _node = exaBoxNode(get_gcontext(), aLocal=True)
    try:
        _local_hash = _node.mGetLocalFileCksum(aLocalFile)
        if _local_hash is None:
            return None
        _hash_dict[_local_file] = _local_hash
        ebLogInfo(f'*** Calculated cksum for local file {_local_file}: {_local_hash}')

    except Exception as e:
        ebLogError(f"Error calculating checksum for {_local_file}: {str(e)}")
        return None

    return _hash_dict

def mVerifyImagesMultiProc(
        aEboxObj: exaBoxCluCtrl, 
        aVmImgVerNum:str,
        aForceRtg:bool=False) -> Dict[str,int]:
    """
    Executes mCleanOldImgsAndEnsureGivenImgInDom0 with ProcessStructure (start,join)
    Returns a Dict 
    {
        "dom0_01":0,       # on success
        "dom0_02":0x0730,  # on error
    }
    """
    ebLogInfo(f"Start mVerifyImagesMultiProc with img: {aVmImgVerNum}, aForceRtg: {aForceRtg}")
    _vmImageVersionNum = aVmImgVerNum
    _ebox:exaBoxCluCtrl = aEboxObj
    _repo_download_location = ''
    _imgInfo = ()
    _local_file_hash = {}

    # Determine the repository download location based on configuration
    if _ebox.mGetOciExacc():
        _repo_download_location = _ebox.mCheckConfigOption('ociexacc_exadata_patch_download_loc')
        ebLogTrace(f"Using ExaCC repository location: {_repo_download_location}")
    else:
        ebLogTrace('*** ociexacc parameter set to "False" in '
                        'exabox.conf.  Retaining the patch path to '
                        'default exacloud location.')

    if _repo_download_location is None:
        _msg = "Repository download location is None or empty. Cannot proceed without a valid location."
        ebLogError(_msg)
        raise ExacloudRuntimeError(0x10, 0xA, _msg)

    _imgInfo = mGetVMImageArchiveInfoInLocalRepo(_vmImageVersionNum, _repo_download_location)

    if _imgInfo is None:
        ebLogError(f'**** No suitable VM image with version {_vmImageVersionNum} found in local repository...')
    else:
        _local_file = _imgInfo['filePath']

        # At this point images/ folder should have the bz2 image file format for the System img.
        _local_file_hash = mGetLocalFileHash(_local_file)
        if _local_file_hash is None:
            _msg = f'Failed to calculate checksum for the local file'
            ebLogError(_msg)

    # Trigger Process
    _plist = ProcessManager()
    _rc_status = _plist.mGetManager().dict()

    # Set an environment variable to indicate multiprocessing context
    os.environ['IS_MULTIPROCESS'] = '1'

    # Parallelize execution on dom0s
    _dpairs = _ebox.mReturnDom0DomUPair()
    for _dom0, _ in _dpairs:
        _p = ProcessStructure(mCleanOldImgsAndEnsureGivenImgInDom0, \
                [_ebox, _dom0, _vmImageVersionNum, _rc_status, aForceRtg, _imgInfo, _repo_download_location, _local_file_hash], _dom0)
        _p.mSetMaxExecutionTime(30*60) # 30 minutes
        _p.mSetJoinTimeout(5)
        _p.mSetLogTimeoutFx(ebLogWarn)
        _plist.mStartAppend(_p)

    _plist.mJoinProcess()

    # Remove the environment variable for non-multiprocessing execution
    del os.environ['IS_MULTIPROCESS']

    return { _dom0: _rc_status[_dom0] for _dom0, _ in _dpairs }

def mSearchImgInDom0s(aEboxObj: exaBoxCluCtrl, aImgName:str) -> List[str]:
    """
    Returns list of Dom0's where aImgName is found.
    If aImgName is found, it will 'touch' the file in each Dom0
    where its present
    aImgName: str. i.e. System.first.boot.24.1.0.0.0.240429.img 
    """
    ebLogInfo(f'Search Img: {aImgName} in Dom0s')
    _ebox:exaBoxCluCtrl = aEboxObj
    _imgName = aImgName
    _versionMap = mGetSystemImageVersionMap(_ebox)
    _Dom0sWithImg = []

    for _dom0, _imgs in _versionMap.items():
        for _img in _imgs:
            if _img.endswith(_imgName):
                _Dom0sWithImg.append(_dom0)

                # Ref 38559314: For every image file we detect
                # we'll use, lets touch it so Exacloud
                # will not delete it as part of a parallel
                # operation -> Exacloud uses the file timestamp
                # to decide if its old enough to be deleted
                _remote_file = os.path.join('/EXAVMIMAGES', _img)
                with connect_to_host(_dom0, get_gcontext()) as _node:
                    ebLogInfo(f"Touching image file to change its timestamp")
                    _bin_touch = node_cmd_abs_path_check(_node, "touch", sbin=True)
                    _cmd = f"{_bin_touch} {_remote_file}"
                    node_exec_cmd_check(_node, _cmd)

    ebLogInfo(f'Img: {aImgName} found in Dom0s {_Dom0sWithImg}')
    return _Dom0sWithImg 



def mBuildAndAttachU02DiskKVM(
        aCluctrl: exaBoxCluCtrl,
        aDom0: str,
        aDomU: str,
        aHostNode: exaBoxNode,
        aU02Name: str,
        aGIHome: str,
        aEDVStates: Dict[str, Dict[str, List[EDVInfo]]]={},
        aDevicePath=None) -> int:

    aOptions = aCluctrl.mGetArgsOptions()
    _utils = aCluctrl.mGetExascaleUtils()
    _xs_edv_image_support = _utils.mIsEDVImageSupported(aOptions)

    if aCluctrl.mIsExaScale() and aCluctrl.mCheckConfigOption("exascale_edv_enable", "True"):
        _u02_edv, *_ = [ edv for edv in aEDVStates[aDom0][aDomU] if edv.vol_type.lower() == 'u02' ]
        _new_ref_link = _u02_edv.device_path
    elif _xs_edv_image_support:
        _new_ref_link = aDevicePath
    else:
        _new_ref_link = f"/EXAVMIMAGES/GuestImages/{aDomU}/{aU02Name}.img"

    # See if u02 is already associated with domU
    if aCluctrl.mIsExaScale() and aCluctrl.mCheckConfigOption("exascale_edv_enable", "True"):
        if _u02_edv.state in (EDVState.NOT_MOUNTED, EDVState.BAD_VOLUME):
            ebLogError("*** Bad u02 EDV volume cannot be used in DomU: {0}".format(aDomU))
            return -1
        _u02_attached = _u02_edv.state == EDVState.ATTACHED_GUEST
    elif _xs_edv_image_support:
        aHostNode.mExecuteCmdLog(f"/opt/exadata_ovm/vm_maker --list --disk-image --domain {aDomU} | grep '{_new_ref_link}'")  
        _u02_attached = (aHostNode.mGetCmdExitStatus() == 0)
    else:
        aHostNode.mExecuteCmdLog(f"/opt/exadata_ovm/vm_maker --list --disk-image --domain {aDomU} | grep '{aU02Name}.img'")
        _u02_attached = (aHostNode.mGetCmdExitStatus() == 0)
    if _u02_attached:
        ebLogInfo('*** /u02 already attached on domu {}'.format(aDomU))

        # Detach the volume first if already attached
        with connect_to_host(aDomU, get_gcontext(), username="root") as _guest_node:
            node_exec_cmd(_guest_node, "/bin/umount /u02")
            node_exec_cmd(_guest_node, f"/sbin/vgchange -an VGExaDbDisk.{aU02Name}.img")
            node_exec_cmd(_guest_node, f"/bin/sed -i '/{aU02Name}/d' /etc/fstab")

        node_exec_cmd(aHostNode, f"/bin/virsh detach-disk {aDomU} {_new_ref_link} --live --config")

    # Make operation idempotent
    mBuildVDisk(aCluctrl, aHostNode, _new_ref_link)

    status = mAttachVDiskToKVMGuest(aCluctrl, aDom0, aDomU, _new_ref_link, "/u02", False, aGIHome)
    if status != 0:
        ebLogError("*** Unable to attach U02 Extra vDisk to domu: {0}".format(aDomU))
        return status

    return 0



def mBuildVDisk(aCluctrl: exaBoxCluCtrl, aNode: exaBoxNode, aImagePath: str):

    aOptions = aCluctrl.mGetArgsOptions()
    _utils = aCluctrl.mGetExascaleUtils()
    _xs_edv_image_support = _utils.mIsEDVImageSupported(aOptions)
    def _build_vdisk(_node, aImagePath):

        _base_vdisk_path = aImagePath
        ebLogInfo('*** Building vDisk: %s' % (_base_vdisk_path))
        #
        # Remove vDisk if it already exists
        #
        if not (aCluctrl.mIsExaScale() and aCluctrl.mCheckConfigOption("exascale_edv_enable", "True") \
                or _xs_edv_image_support) and _node.mFileExists(_base_vdisk_path):
            ebLogWarn('*** vDisk image %s already exist on remote node' % (_base_vdisk_path))
            _node.mExecuteCmd('rm -f '+_base_vdisk_path)
        #
        # Fetch vDisk size
        #
        _disk_u02_size = aCluctrl.mGetu02Size()

        ebLogInfo('*** Add vDisk u02 size %s' % (_disk_u02_size))
        _device_path = None

        if not aCluctrl.mIsKVM():
            aCluctrl.mCreateImage(_node, _base_vdisk_path, _disk_u02_size)
        else:
            _device_path = mCreateImageLVM(aCluctrl, _node, _base_vdisk_path, _disk_u02_size, aKeep=True)

        #
        # Push Additional bits (ocde, klone, rpm,..) into new vDisk image
        #
        _base_remote_dyndep_dir = aImagePath
        _uuid = str(uuid.uuid1())

        _node.mExecuteCmdLog('mkdir -p /mnt/' + _uuid)

        if aCluctrl.mIsKVM():
            _node.mExecuteCmdLog('mount -o loop ' + _device_path + ' /mnt/' + _uuid)
        else:
            _node.mExecuteCmdLog('mount -o loop ' + _base_vdisk_path + ' /mnt/' + _uuid)

        _node.mExecuteCmdLog('mkdir -p /mnt/' + _uuid + '/opt/dbaas_images')
        _node.mExecuteCmdLog('mkdir -p /mnt/' + _uuid + '/opt/dbaas_images/dbnid')
        _node.mExecuteCmdLog('mkdir -p /mnt/' + _uuid + '/opt/dbaas_images/managed')
        _node.mExecuteCmdLog('mkdir -p /mnt/' + _uuid + '/opt/bdcs')
        _node.mExecuteCmdLog('chmod a+x /mnt/' + _uuid + '/opt')

        _packages_list = aCluctrl.mDynDepNonImageList(['db_templates', 'bdcs', 'rpm', 'ocde_bits'])

        if (aCluctrl.isATP() == True):
            ebLogInfo('*** mBuildVDisk For ATP enabled service ***')
        else:
            ebLogInfo('*** mBuildVDisk For ATP disabled service ***')

        for _oss in _packages_list:

            _dom0file = _oss['dom0']

            if 'bdcs' in list(_oss.keys()) and _oss['bdcs'] == 'True':
                _dest_dir = '/opt/bdcs/'

            elif 'managed' in list(_oss.keys()) and _oss['managed'] == 'True':
                _dest_dir = '/opt/dbaas_images/managed/'

            else:
                _dest_dir = '/opt/dbaas_images/'

            ebLogInfo('*** Copying %s to %s' % (_dom0file, _dest_dir))

            _, _o, _e = _node.mExecuteCmd('cp ' + _dom0file + ' ' + '/mnt/' + _uuid + _dest_dir)

            _rc = _node.mGetCmdExitStatus()
            if _rc:
                _node.mExecuteCmdLog('umount /mnt/' + _uuid)
                if aCluctrl.mIsKVM():
                    mUnmountImageLVM(aCluctrl, _node, _base_vdisk_path)
                _node.mExecuteCmdLog('rmdir /tmp/' + _uuid)
                _error_str = '*** vDisk image creation fail (cpimg): ' + str(_o.readlines()) + ' ' + str(_e.readlines())
                ebLogError(_error_str)
                raise ExacloudRuntimeError(0x0204, 0x0A, _error_str)

        _node.mExecuteCmdLog('umount /mnt/' + _uuid)
        _node.mExecuteCmdLog('rmdir /mnt/' + _uuid)

        if aCluctrl.mIsKVM():
            mUnmountImageLVM(aCluctrl, _node, _base_vdisk_path)

    # Execute _build_vdisk
    if aNode is None:
        for _dom0, _ in aCluctrl.mReturnDom0DomUPair():
            with connect_to_host(_dom0, get_gcontext()) as _node:
                _build_vdisk(_node, aImagePath)
    else:
        _build_vdisk(aNode, aImagePath)


def mCreateImageLVM(aCluctrl, aNode, aPath, aSize, aType='ext4', aKeep=False):

    def _error_banner():
        _error_txt = "*** FATAL ERROR ***"
        ebLogError(_error_txt)

    def _bail_on_error(_error_str,_out=None):
        _error_banner()
        if _out:
            _error_str = _error_str + ' ' + str(_out.readlines())
        ebLogError(_error_str)
        raise ExacloudRuntimeError(0x0204, 0x0A, _error_str)

    def _process_cmd(_node, _cmd, _error_str, aWarn=False, _retries=5, _interval_retry_sec=2):
        # Retry at least 5 times each command before failing
        _error = ''
        for _ in range(_retries):
            if aCluctrl.mIsDebug():
                ebLogDebug('>>> CMD: {}'.format(_cmd))
            _, _o, _e = _node.mExecuteCmd(_cmd)
            _rc = _node.mGetCmdExitStatus()
            if _rc and _error_str is not None:
                _error = _error_str + str(_o.readlines()) + ' ' + str(_e.readlines())
                ebLogWarn(_error)
                if not aWarn:
                    time.sleep(_interval_retry_sec)
                    continue
            return _o.readlines()
        _bail_on_error(_error)

    def _cleanup_vdisk(_node,_vgname, _pvid,_device):
        _cmd = 'lvremove -f VGExaDbDisk.{0}.img/LVDBDisk'.format(_vgname)
        _out = _process_cmd(_node,_cmd, None)
        _cmd = 'vgchange -an VGExaDbDisk.{0}.img'.format(_vgname)
        _out = _process_cmd(_node,_cmd, None)
        _cmd = 'vgremove VGExaDbDisk.{0}.img --force'.format(_vgname)
        _out = _process_cmd(_node,_cmd, None)
        _cmd = 'pvremove /dev/mapper/{0} --force --force <<< y'.format(_pvid)
        _out = _process_cmd(_node,_cmd, None)
        _cmd = 'kpartx -d -v {0}'.format(_device)
        _out = _process_cmd(aNode, _cmd, '*** vDisk Cleanup fail (kpartx delete)',aWarn=True)
        _cmd = 'losetup -d {0}'.format(_device)
        _out = _process_cmd(aNode, _cmd, '*** vDisk Cleanup fail (losetup delete)',aWarn=True)
        _cmd = ' /usr/sbin/udevadm settle ;  pvscan --cache'
        _out = _process_cmd(aNode, _cmd, '*** vDisk Cleanup fail (update pvs cache)')

    def _pre_check_cleanup(_node,_pname):
        _sname = _pname.split('/')[-1].split('.')[0]
        _cmd = 'pvs | grep {0}'.format(_sname)
        _out = _process_cmd(_node,_cmd, None)
        for _entry in _out:
            if _sname in _entry:
                ebLogWarn('*** Previous PV ({0})found trying to clean up'.format(_out))
            else:
                continue
            _pvid = _entry.split()[0].split('/')[-1]
            _device = '/dev/'+_pvid[:-2]
            _cleanup_vdisk(_node,_sname,_pvid,_device)
            break

    aOptions = aCluctrl.mGetArgsOptions()
    _utils = aCluctrl.mGetExascaleUtils()
    _xs_edv_image_support = _utils.mIsEDVImageSupported(aOptions)
    _short_name = aCluctrl.mCheckConfigOption('u02_name') if aCluctrl.mCheckConfigOption('u02_name') else 'u02_extra'

    if aCluctrl.mIsExaScale() and aCluctrl.mCheckConfigOption("exascale_edv_enable", "True") or _xs_edv_image_support:

        #
        # Wipe the EDV volume first
        #
        _device = aPath
        fill_disk_with_lvm_partition(aNode, _device, 'msdos')

        #
        # Mount the image
        #
        _cmd = 'kpartx -a -v {0}'.format(_device)
        _out = _process_cmd(aNode, _cmd, '*** vDisk image creation fail (kpartx mount)')
        _device_id = _out[0].split()[2]

        #
        # HACK: Create a dummy ext4 filesystem to wipe the previous existing partition.
        # Don't try to use dd to write 0s in the first sectors of the EDV, it just won't work.
        #
        _cmd = f"/sbin/vgchange -an VGExaDbDisk.{_short_name}.img"
        _out = _process_cmd(aNode, _cmd, '*** vDisk image wipe previous LV fail (vgchange)', aWarn=True)

        _cmd = f"/sbin/mkfs.ext4 -F /dev/mapper/{_device_id}"
        _out = _process_cmd(aNode, _cmd, '*** vDisk image wipe previous LV fail (mkfs.ext4)')


    else:

        #
        # PreChecks and cleanup if required
        #
        _pre_check_cleanup(aNode,aPath)

        _cmd = 'losetup -a'
        _out = _process_cmd(aNode, _cmd, '*** vDisk image creation fail (already mounted)')
        for _entry in _out:
            if aPath in _entry:
                ebLogWarn('*** Found image already mounted: {0} - {1}'.format(aPath, _entry))
                #
                # Image is not expected to be mounted on the loop device - assume bad left over and try to get red of it
                #
                _device = _entry.split(':')[0]
                _cmd = 'kpartx -v -d {0} ; losetup -d {0}'.format(_device)
                _out = _process_cmd(aNode, _cmd, '*** vDisk delete previous image (already mounted)')
                _cmd = 'losetup -a'
                _out = _process_cmd(aNode, _cmd, '*** vDisk image creation fail (already mounted (S2))')
                for _entry in _out:
                    if aPath in _entry:
                        _bail_on_error('*** vDisk imge creation fail (already mounted)')

        #
        # Create the new disk image and its partition
        #
        _disk_info = ebDiskImageInfo(aPath, parse_size(aSize), 'raw', 'msdos')
        create_new_lvm_disk_image(aNode, _disk_info)

        #
        # Mount the image
        #
        _cmd = 'kpartx -a -v {0}'.format(aPath)
        _out = _process_cmd(aNode, _cmd, '*** vDisk image creation fail (kpartx mount')
        _device_id = _out[0].split()[2]
        if _device_id[:4] != 'loop':
            _bail_on_error('*** vDisk image invalid loop device id: {0}'.format(_device_id), _out)

        _cmd = 'losetup -a'
        _out = _process_cmd(aNode, _cmd, '*** vDisk image creation fail (losetup): ')
        _device = None
        for _entry in _out:
            if aPath in _entry:
                _device = _entry.split(':')[0]
                break
        if _device is None:
            _bail_on_error('*** vDisk image creation fail (losetup): ', _out)

    #
    # Create PV/VG/LV on the new disk image
    #
    _cmd = 'lvm pvcreate --force  /dev/mapper/{0}'.format(_device_id)
    _out = _process_cmd(aNode, _cmd, '*** vDisk image creation fail (pvcreate)')

    _cmd = 'lvm vgcreate VGExaDbDisk.{0}.img /dev/mapper/{1}'.format(_short_name,_device_id)
    _out = _process_cmd(aNode, _cmd, '*** vDisk image creation fail (vgcreate)')

    _lv_size = f"-L {int(aSize[:-1]) - 2}{aSize[-1]}"
    _cmd = 'lvm lvcreate {1} -n LVDBDisk VGExaDbDisk.{0}.img'.format(_short_name, _lv_size)
    _out = _process_cmd(aNode, _cmd, '*** vDisk image creation fail (lvcreate)')

    _cmd = 'lvm lvchange -a y /dev/VGExaDbDisk.{0}.img/LVDBDisk'.format(_short_name)
    _out = _process_cmd(aNode, _cmd, '*** vDisk image creation fail (lvchange Yes)')
    #
    # Format and Label vDisk (xxx/MR: Switch to xfs eventually)
    #
    if aCluctrl.mCheckConfigOption('kvm_enable_u02_fstype_xfs', 'True'):
        ebLogInfo('*** Making u02 as xfs partition !')
        _cmd = 'mkfs.xfs -f /dev/VGExaDbDisk.{0}.img/LVDBDisk 2>&1 > /dev/null'.format(_short_name)
        _out = _process_cmd(aNode, _cmd, '*** vDisk Formatting error')
        _cmd = 'xfs_admin -L {0} /dev/VGExaDbDisk.{1}.img/LVDBDisk'.format('U02_IMAGE',_short_name)
        _out = _process_cmd(aNode, _cmd, '*** vDisk Labelling error')
    else:
        ebLogInfo('*** Making u02 as ext4 partition !')
        _cmd = 'mkfs.ext4 -F /dev/VGExaDbDisk.{0}.img/LVDBDisk' .format(_short_name)
        #Check if domu is ol7 and dom0 is ol8,if yes then modify fs feature
        _domu_version = aCluctrl.mGetMajorityHostVersion(ExaKmsHostType.DOMU) #added for 36360004 
        _dom0_version = aCluctrl.mGetOracleLinuxVersion(aNode.mGetHostname()) #added for 36360004 
        if _domu_version.lower() == 'ol7' and _dom0_version.lower() == 'ol8':
           ebLogInfo('*** Removing metadata_csum filesystem feature for ol7 domU with ol8 dom0!')
           _rm_fs_feature = '-O ^metadata_csum'
           _cmd = 'mkfs.ext4 -F /dev/VGExaDbDisk.{0}.img/LVDBDisk {1}'.format(_short_name, _rm_fs_feature)
        _out = _process_cmd(aNode, _cmd, '*** vDisk Formatting error')
        _cmd = 'e2label /dev/VGExaDbDisk.{0}.img/LVDBDisk {1}'.format(_short_name,'U02_IMAGE')
        _out = _process_cmd(aNode, _cmd, '*** vDisk Labelling error')

    #
    # Detach/delete loopback device and release disk image
    #
    if aKeep is False:
        _cmd = 'lvm lvchange -a n /dev/VGExaDbDisk.{0}.img/LVDBDisk'.format(_short_name)
        _out = _process_cmd(aNode, _cmd, '*** vDisk image creation fail (lvchange No)')
        _cmd = ' /usr/sbin/udevadm settle ;  pvscan --cache'
        _out = _process_cmd(aNode, _cmd, '*** vDisk Cleanup fail (update pvs cache)')
        _cleanup_vdisk(aNode,_short_name,_device_id,_device)

    return  '/dev/VGExaDbDisk.{0}.img/LVDBDisk'.format(_short_name)



def mUnmountImageLVM(aCluctrl, aNode, aPath):

    def _error_banner():
        _error_txt = "*** FATAL ERROR ***"
        ebLogError(_error_txt)

    def _bail_on_error(_error_str, _out=None):
        _error_banner()
        if _out:
            _error_str = _error_str + ' ' + str(_out.readlines())
        ebLogError(_error_str)
        raise ExacloudRuntimeError(0x0204, 0x0A, _error_str)

    def _process_cmd(_node, _cmd, _error_str,aWarn=False):
        if aCluctrl.mIsDebug():
            ebLogDebug('>>> CMD: {}'.format(_cmd))
        _, _o, _e = _node.mExecuteCmd(_cmd)
        _rc = _node.mGetCmdExitStatus()
        if _rc and _error_str is not None:
            _error_str = _error_str + str(_o.readlines()) + ' ' + str(_e.readlines())
            if aWarn:
                ebLogWarn(_error_str)
            else:
                _bail_on_error(_error_str)
        return _o.readlines()

    def _cleanup_vdisk(_node,_vgname,_device):
        _cmd = 'lvm lvchange -a n /dev/VGExaDbDisk.{0}.img/LVDBDisk'.format(_vgname)
        _ret, _out, _err = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True)
        if _ret == 5:
            _cmd = 'lvm lvchange -a n -f /dev/VGExaDbDisk.{0}.img/LVDBDisk'.format(_vgname)
            _ret, _out, _err = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True)
        _cmd = 'vgchange -an VGExaDbDisk.{0}.img'.format(_vgname)
        _ret, _out, _err = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True)
        if _ret == 5:
            _cmd = 'vgchange -an -f VGExaDbDisk.{0}.img'.format(_vgname)
            _ret, _out, _err = node_exec_cmd(_node, _cmd, log_warning=True, log_stdout_on_error=True)
        _cmd = 'kpartx -d -v {0}; losetup -d {0}'.format(_device)
        _out = _process_cmd(aNode, _cmd, '*** vDisk Cleanup fail (kpartx/losetup delete)',aWarn=True)
        _cmd = ' /usr/sbin/udevadm settle ;  pvscan --cache'
        _out = _process_cmd(aNode, _cmd, '*** vDisk Cleanup fail (update pvs cache)')

    def _pre_check_cleanup(_node,_pname):
        _sname = aCluctrl.mCheckConfigOption('u02_name') if aCluctrl.mCheckConfigOption('u02_name') else 'u02_extra'
        _cmd = 'pvs | grep {0}'.format(_sname)
        _out = _process_cmd(_node,_cmd, None)
        for _entry in _out:
            if _sname in _entry:
                ebLogWarn(f'*** mUnmountImageLVM(): Previous PV {_out} found trying to release vDisk')
            else:
                continue
            _cleanup_vdisk(_node,_sname,_pname)
            break
    #
    # PreChecks and cleanup if required
    #
    _pre_check_cleanup(aNode,aPath)



def mAttachVDiskToKVMGuest(aCluctrl, aHostOsName, aGuestName, aVDiskPath, aMountPoint, aAlreadyInVirsh=False, aGIHome=None):

    _vgname = aCluctrl.mCheckConfigOption('u02_name') if aCluctrl.mCheckConfigOption('u02_name') else 'u02_extra'
    if not aAlreadyInVirsh:
        #
        # PreCheck partition not already mounted in VM
        #
        _guest_node = exaBoxNode(get_gcontext())
        _guest_node.mSetUser('root')
        _guest_node.mConnect(aHost=aGuestName)

        _cmd = 'lvs | grep "VGExaDbDisk.{0}.img"'.format(_vgname)
        _guest_node.mExecuteCmdLog(_cmd)
        if _guest_node.mGetCmdExitStatus() == 0:
            _error_str = '*** Error vDisk ({1}) already mounted in VM -- Review/Fix target domu: {0} and retry'.format(aGuestName, _vgname)
            raise ExacloudRuntimeError(0x0204, 0x0A, _error_str)
        #
        # Connect to the KVM Host OS
        #
        _host_node = exaBoxNode(get_gcontext())
        _host_node.mConnect(aHost=aHostOsName)
        attach_dom0_disk_image(
            _host_node,
            aGuestName,
            aVDiskPath,
            'none' if aVDiskPath.startswith('/dev/exc/') else 'writethrough',
            'native' if aVDiskPath.startswith('/dev/exc/') else None,
        )
        _cmd = '/usr/sbin/udevadm settle'
        _host_node.mExecuteCmd(_cmd)

        _host_node.mDisconnect()
        #
        # Wait for LVM to show up in VM
        #
        _count = 6
        _time_slice = 10 #Bug 31660672
        while _count:
            _cmd = 'ls /dev/VGExaDbDisk.{0}.img/LVDBDisk'.format(_vgname)
            _guest_node.mExecuteCmdLog(_cmd)
            if _guest_node.mGetCmdExitStatus() == 0:
                ebLogInfo('*** vDisk mounted in VM and available')
                break
            else:
                ebLogInfo('*** vDisk still not available - retry -')
                if _count == 2:
                    #During final attempt.. lets see if VG is still not activated. workaround for Bug 37134868.
                    ebLogInfo(f'*** Checking if vg {_vgname} is not active')
                    _cmd = f"/usr/sbin/lvdisplay /dev/VGExaDbDisk.{_vgname}.img/LVDBDisk | grep 'LV Status' | grep -i 'NOT available'"
                    _guest_node.mExecuteCmdLog(_cmd)
                    if _guest_node.mGetCmdExitStatus() == 0:
                        ebLogInfo('***VG was not active. Activating vg now !')
                        _cmd = f"/usr/sbin/lvchange -a y /dev/VGExaDbDisk.{_vgname}.img/LVDBDisk"
                        _guest_node.mExecuteCmdLog(_cmd)
                        if _guest_node.mGetCmdExitStatus() == 0:
                            ebLogInfo('*** Successfully activated vg !')

            _count = _count - 1
            time.sleep(_time_slice)
            _time_slice += _time_slice
        if not _count:
            _error_str = '*** Error vDisk ({1}) can not be  mounted in VM -- Review/Fix target domu: {0} and retry'.format(aGuestName, _vgname)
            raise ExacloudRuntimeError(0x0204, 0x0A, _error_str)
    else:
        _guest_node = exaBoxNode(get_gcontext())
        _guest_node.mConnect(aHost=aGuestName)
    #
    # Update fstab in VM to make partition mount in VM persistent
    #
    _cmd = "mkdir -p {1} ; "
    _cmd += "mount /dev/VGExaDbDisk.{0}.img/LVDBDisk /u02  ; "
    _u02_img = "/dev/VGExaDbDisk.{0}.img/LVDBDisk".format(_vgname)
    _guest_node.mExecuteCmdLog(f"/bin/grep '{_u02_img}' /etc/fstab")
    # Do not add entry again in fstab if already there
    if _guest_node.mGetCmdExitStatus() != 0:
        if aCluctrl.mCheckConfigOption('kvm_enable_u02_fstype_xfs', 'True'):
            _cmd += 'echo "/dev/VGExaDbDisk.{0}.img/LVDBDisk  /u02       xfs     defaults 1 1" >> /etc/fstab'
        else:
            _cmd += 'echo "/dev/VGExaDbDisk.{0}.img/LVDBDisk  /u02       ext4     defaults 1 1" >> /etc/fstab'

    _cmd = _cmd.format(_vgname, aMountPoint)
    _guest_node.mExecuteCmdLog(_cmd)
    if aCluctrl.mIsDebug():
        _guest_node.mExecuteCmdLog('mount | grep {0}'.format(_vgname))

    _gridhome = aGIHome
    if _gridhome:
        _dir = _gridhome.split('/', 2)[1]
        if _dir == "u02":
            _cmd = f"cp -a /etc/fstab /etc/fstab.gridHome.bak; cat /etc/fstab | grep -v {_gridhome} > /etc/fstab.orig; cp /etc/fstab.orig /etc/fstab"
            _guest_node.mExecuteCmdLog(_cmd)

    _guest_node.mDisconnect()

    return 0

def mCopySystemImgLocalToDOM0(
        aCluctrl: exaBoxCluCtrl, 
        aVmImgVerNum:str, 
        aDom0sWithImg:List[str],
        aForceRtg:bool=False) -> None:
    """
    Copy image with given image version from local to DOM0
    aVmImgVerNum: str with format "24.1.0.0.0.240517"
    aDom0sWithImg: List(str) with format ['fqdn_01', 'fqdn_02'...]
    """
    ebLogInfo (f'mCopySystemImgLocalToDOM0 will check if img {aVmImgVerNum} currently present {aDom0sWithImg} is missing in other Dom0s')

    # RTG logic does not apply on XEN 
    if not aCluctrl.mIsKVM():
        aForceRtg = False

    _unique_dom0s, _, _, _ = aCluctrl.mReturnAllClusterHosts()
    if not aDom0sWithImg:
        ebLogInfo(f"DOM0s do not have the System img file for version {aVmImgVerNum}."\
                    " Will try to copy System img bz2 file if present in images/ directory to the DOM0s.")
    elif len(list(set(aDom0sWithImg))) == len(_unique_dom0s):
        ebLogInfo(f"All DOM0s have the System img file for version {aVmImgVerNum}. Not copying System img file.")
        return
    elif len(list(set(aDom0sWithImg))) > 0:
        ebLogInfo(f"Some DOM0s don't have the System img file present. Copying the img from DOM0 with "\
            "System img file present to local.")
        mGetImageFromDom0ToLocal(aCluctrl, aVmImgVerNum, aDom0sWithImg[0],aForceRtg)

    # At this point images/ folder should have the bz2 image file format for the System img
    # Trigger multiprocess to copy System img from local to DOM0 if it does not exist on DOM0
    _rc_status = mVerifyImagesMultiProc(aCluctrl, aVmImgVerNum,aForceRtg)
    # validate the return codes
    _rc_all = 0

    # Check for errors in the return status of the multiprocess
    for _dom0 in _unique_dom0s:
        if _rc_status[_dom0]:
            _rc_all = ebError(_rc_status[_dom0])
            ebLogError(f"*** Could not copy System Image to Dom0 '{_dom0}' " \
                        f"return status = '{_rc_status[_dom0]}' ***")
    if _rc_all:
        raise ExacloudRuntimeError(0x0730, 0xA, "No suitable System first boot Image found. Aborting.")

def mIsRtgImgPresent(
    aCluctrl: exaBoxCluCtrl, 
    aVmImgVerNum:str) -> Tuple[bool, bool]:
    """
    aVmImgVerNum format: "24.1.0.0.0",
    This function will search if there is AT LEAST one filename MATCHING this 
    aVmImgVerNum (version number), it will search in Dom0s and local repo
    and return the whole Image Filename if it's found somewhere.
    It will return the available image considering the following priority
    * if *.RTG.IMG is available
    * if *.IMG is available
    """
    ebLogInfo(f"Validate if RTG Image {aVmImgVerNum} exists in Dom0s or Local.")
    rtgImgExistInDom0s = False
    rtgImgExistInLocal = False
    
    dom0sWithImgFiles = mGetSystemImageVersionMap(aCluctrl) 
    
    for _, files in dom0sWithImgFiles.items():
        for f in files:
            fileInfo = __getVMImageInfo(f)
            if fileInfo is not None:        
                if fileInfo['imgVersion'] == aVmImgVerNum:
                    if fileInfo['isRtgImg']:
                        rtgImgExistInDom0s = True
                        break

    localWithImgFile = getVMImageArchiveInRepo(
        aVmImgVerNum,aCluctrl.mIsKVM(),True) # None if not found
    if localWithImgFile:
        rtgImgExistInLocal = True
    
    ebLogInfo(f"RTG in Dom0s {rtgImgExistInDom0s}, Local {rtgImgExistInLocal}")
    return rtgImgExistInDom0s, rtgImgExistInLocal


