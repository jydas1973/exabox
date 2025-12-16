#!/bin/python
#
# $Header: ecs/exacloud/exabox/ovm/clugiconfigimage.py /main/11 2025/08/19 08:39:20 akkar Exp $
#
# clugiconfigimage.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      clugiconfigimage.py - Implementation of GI image configuration
#
#    DESCRIPTION
#      Configuration and management of multiple GI images present in repository.
#
#
#    MODIFIED   (MM/DD/YY)
#    akkar       07/23/25 - Bug 38227428: Control ADBD image count
#    akkar       05/19/25 - Bug 37964965: Fix image name in inventory.json for
#                           multigi
#    akkar       01/30/25 - Bug 37530426: Update default latest in inventory
#    akkar       11/20/24 - Bug 37249048: Update default latest in inventory
#    akkar       09/10/24 - Bug 37043379: Revert image naming format
#    ivang       08/20/24 - bug-36953200: adbd improvements
#    akkar       08/20/23 - Creation
#
from datetime import datetime
from typing import Dict
import fcntl
import hashlib
import json
import os
import shutil
import tarfile
from ssl import SSLError
import socket
from exabox.core.Error import ExacloudRuntimeError
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.log.LogMgr import ebLogError, ebLogInfo, ebLogTrace
from exabox.exaoci.ExaOCIFactory import ExaOCIFactory


class ebCluGiRepoUpdate:
    
    def __init__(self,aExaBoxCluCtrlObj):
        self.img_src_path = None
        self.img_dest_path = None
        self.__current_repo_path = get_gcontext().mGetConfigOptions()['repository_root']
        self.new_inventory_data = {}
        self._eboxobj = aExaBoxCluCtrlObj
        self.is_inventory_json_updated = False
        self.inventory_json_backup_file = None
        self.gi_response_data = {}
        self.replication_server_list = []
        self.replication_image_list = []
        self._inventory_json_path = os.path.join(self.getRepoPath(), "inventory.json")
        self._inventory_json_data = mReadInventoryJson(self._inventory_json_path)
        self._inventoryjson_backup_file_name = None
        self.new_repo_path = None
        self.image_remove_list = []
        self._max_images_exacs = 4 # default
        if self._eboxobj.mCheckConfigOption('gi_multi_image_count'):
            # if not default 4 will be used
            self._max_images_exacs = int(self._eboxobj.mCheckConfigOption('gi_multi_image_count'))
        self._max_images_adbd = 1 # default
        
    def getRepoPath(self):
        return self.__current_repo_path  
    
    @classmethod
    def _from_payload(self, _ebox, json_payload):
        ebLogInfo('*** payload received from ECRA: ' + json.dumps(json_payload, indent=4))
        is_old_repo = os.path.isdir(os.path.join(get_gcontext().mGetConfigOptions()['repository_root'], 'grid-klones'))
        if json_payload["location"]["type"] in ['local_tar', 'objectstore_tar']:
            __object = ebTarBundleUpdate(_ebox, json_payload)
        elif json_payload["location"]["type"] in ['objectstore_image', 'local_image']:
            if is_old_repo:
                __object = SingleImageUpdateOldFormat(_ebox, json_payload)
            else:
                __object = ebSingleImageUpdate(_ebox, json_payload)
        else:
            raise ValueError('Invalid payload type')
        return __object

    def mParsePayload(self, payload):
        ebLogInfo(f'Parsing payload ...')
        self.image_type = payload["image_type"] #RELEASE/CUSTOM
        self.operation_type = payload.get("type") #ADD/DELETE/UPLOAD
        if payload.get("ecra"):
            self.replication_server_list = payload["ecra"].get("servers")
        self.location_type = payload["location"]["type"] # FS/OSS
        self.delete_old_image = payload.get("delete_old_image")
            
    def mParseNewInventoryJson(self, image_info):
        """Parse the incremental inventory JSON data for a given image."""
        ebLogInfo('Parsing new image info from new inventory.json...')
        try:
            self.service_type = image_info["service"][0]
            self.image_version = image_info["version"] #19.19.0.0.230418
            self.major_version = self.image_version.split(".")[0]
            _filename = image_info["files"][0]['path'] # EXACS/grid-klone-Linux-x86-64-191900230418.zip
            self.sha256sum = image_info["files"][0]["sha256sum"]
            if self.operation_type == "ADD":
                self.image_default_status = True if image_info["xmeta"].get("default") else False
                self.image_latest_status = True if image_info["xmeta"].get("latest") else False
            self.img_src_path = os.path.join(self.new_repo_path, _filename)
            self.img_dest_path = os.path.join(self.getRepoPath(), _filename)
        except Exception as e:
            _err_msg = f"Error while parsing Incremental Inventory.json error: {e}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg)
        
    def mWriteToInventoryJson(self):
        """Updates the inventory.json file 

        Args:
            aUpdatedInventoryData (_dict_): inventory json data

        Raises:
            ExacloudRuntimeError: BlockingIOError
            ExacloudRuntimeError: JSONDecodeError
            ExacloudRuntimeError: OSError
            ExacloudRuntimeError: Other Exceptions
        """
        temp_file = self._inventory_json_path + '.tmp'
        with open(temp_file, "w") as _fd_write:
            ebLogInfo("***INFO**** Patching inventory.json")
            try:
                ebLogTrace(f'Acquiring Exclusive lock on {self._inventory_json_path}') 
                fcntl.flock(_fd_write, fcntl.LOCK_EX | fcntl.LOCK_NB)
                _inventory_data = self._inventory_json_data
                _inventory_data["gendate"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                _fd_write.write(json.dumps(_inventory_data, indent=4, sort_keys=True, separators=(',',' : ')))
                _fd_write.flush()  # Flush internal buffer to OS buffer
                os.fsync(_fd_write.fileno())  # Ensure OS buffers are written to disk
            except BlockingIOError:
                _err_msg = f"Concurrent image configuration operations not allowed! Please try after some time"
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)
            except json.JSONDecodeError as e:
                _err_msg = f"Error decoding JSON from {self._inventory_json_path}: {e}"
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)
            except OSError as e:
                _err_msg = f"File operation error on {self._inventory_json_path}: {e}"
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)
            except Exception as e:
                _err_msg = f"An unexpected error occurred: {e}"
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)
            finally:
                # Release the lock after the operation is done
                fcntl.flock(_fd_write, fcntl.LOCK_UN)
                ebLogTrace(f" Exclusive Lock on {self._inventory_json_path} released")
            
        # Take backup of current inventory.json
        if self.mBackupInventoryJson(self._inventory_json_path):
            # os.rename() function is atomic on POSIX-compliant systems
            ebLogInfo(f'Backup of {self._inventory_json_path} file taken, renaming temp file to inventory.json')
            os.rename(temp_file , self._inventory_json_path)
            self._is_inventoryjson_updated = True
            
    def mFetchRemoteJson(self, aNode, aRemoteNodeJsonPath):
        _remote_node_file = aNode.mReadFile(aRemoteNodeJsonPath)
        _remote_node_inventory = json.loads(_remote_node_file)
        return _remote_node_inventory
            
    def mCompareInventoryJson(self,aNode, aRemoteNodeJsonPath):
        try:
            primary_node_inventory_json = mReadInventoryJson(self._inventory_json_path)
            secondary_node_inventory_json = self.mFetchRemoteJson(aNode,aRemoteNodeJsonPath)
            
            if primary_node_inventory_json == secondary_node_inventory_json:
                ebLogInfo("Primary and secondary nodes inventory jsons are the same, no action required.")
                return True
            else:
                ebLogInfo("Primary and secondary nodes inventory jsons are different!")
                return False
        except Exception as e:
            print(f"Error: {e}")
            
    def mVerifyImageCheckSum(self):
        new_image_sha256sum = mComputeSha256sum(self.img_src_path)
        if new_image_sha256sum != self.sha256sum:
            _err_msg = f'Downloaded image sha256sum {new_image_sha256sum} does not match with payload : {self.sha256sum}'
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg)
            
    def mCheckImageExists(self):
        if os.path.exists(self.img_dest_path):
            # same image name with different hashsum cannot exist
            _existing_file_sha256sum = mComputeSha256sum(self.img_dest_path)
            if _existing_file_sha256sum != self.sha256sum:
                _err_msg = f"Same Image with differernt sha256sum exists {self.img_dest_path}"
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)
            # if exact same image then delete downloaded iamge and skip flow
            mRemoveImage(self.img_src_path)
            return True
        return False
            
    def mReplicateImageRepoOnSecondaryEcra(self):
        if not self.replication_server_list:
            ebLogInfo(f'No secondary node list provided, skipping replication. ')
            return True
        ebLogInfo(f' Checking secondary nodes for image replication ...')
        _node = exaBoxNode(get_gcontext())
        _node.mSetUser('oracle')
        for server_ip in self.replication_server_list:
            try:
                if socket.gethostname() in server_ip:
                    continue
                _node.mConnect(aHost=server_ip, aTimeout=900, aKeyOnly=False)
                _cmd_str = f'/bin/ls {self.getRepoPath()}'
                _i, _o, _e = _node.mExecuteCmd(_cmd_str)
                _out = _o.readlines()
                if not _out:
                    return False
                if _out:
                    _new_repo_format =  False
                    for folder in _out:
                        if folder.strip() == 'EXACS':
                            _new_repo_format = True
                    if not _new_repo_format:
                        ebLogError(f'Single GI repo format present in repo :{server_ip}, cannot upgrade !')
                        return False
                # compare the inventory.jsons
                secondary_node_inventory_json_path = os.path.join(self.getRepoPath(), "inventory.json")
                if self.mCompareInventoryJson(_node, secondary_node_inventory_json_path):
                    return True
                # copy the image to repo location
                ebLogInfo(f"Copying updated inventory.json to secondary node: {server_ip}")
                _node.mCopyFile(self._inventory_json_path, secondary_node_inventory_json_path)
                # copy the image 
                for image_path in self.replication_image_list:
                    ebLogInfo(f"Copying GI image {image_path} to secondary node: {server_ip}:{image_path}")
                    _node.mCopyFile(image_path, image_path)
            except Exception as e:
                _err_msg =  f"GI image replication on secondary server failed : {e}"
                ebLogError(_err_msg)
                raise ExacloudRuntimeError(aErrorMsg=_err_msg)
            finally:
                _node.mDisconnect()
    
    def mGetOlderVersionFiles(self):
        # Initialize the smallest version to None
        ebLogInfo(f"Computing the Oldest Versions from Inventory.json ... ")
        _ebox = self._eboxobj
        ebLogTrace(f'Image count control parameter from exabox.conf : EXACS-{self._max_images_exacs}')
        _max_images = self._max_images_exacs if self.service_type == "EXACS" else self._max_images_adbd
        ebLogInfo(f'Repo will contain maximum {_max_images} image/images as set in config.')
        
        # Iterate over the dictionaries to find the smallest version
        versions_paths = []
        for _dict in self._inventory_json_data["grid-klones"]:
            version_str = _dict.get('version')
            major_ver = version_str.split(".")[0]
            service_type = _dict.get('service')[0]
            if self.major_version == major_ver and self.service_type == service_type:
                version = _dict['version']
                file_path = _dict['files'][0]['path']
                versions_paths.append((version, file_path))
        
        # Parse the full version string and return a tuple for sorting
        def parse_version_str(version_str):
            parts = version_str.split('.')
            major_version = int(parts[0])
            minor_version = int(parts[1])
            date_part = parts[4]
            date = datetime.strptime(date_part, "%y%m%d")
            return (major_version, minor_version, date)
        
        # Sorting the versions by major version, minor version, and date
        versions_paths_sorted = sorted(versions_paths, key=lambda v: parse_version_str(v[0]))
        
        # Extracting the file paths of the 'n' oldest versions
        _n_images = len(versions_paths_sorted)
        # remove images if we exceed the capacity only
        # this avoid deleting all images
        if _n_images <= _max_images:
            return []

        _files_to_remove = _n_images - _max_images
        redundant_file_paths = [path for version, path in versions_paths_sorted[:_files_to_remove]]
        ebLogInfo(f"{redundant_file_paths} files will be removed from {versions_paths_sorted} in {self.service_type}")
        
        return redundant_file_paths
    
    def mAddEntryToInventory(self, incr_image_data):
        """Add new image related details to inventory.json"""
        self._inventory_json_data["grid-klones"].insert(0,incr_image_data)
        ebLogInfo('Incremental inventory data added: ' + json.dumps(incr_image_data, indent=4))

    def mRemoveEntryFromInventory(self, aFileName):
        """Remove old image related entry from inventory.json.

        Args:
            aFileName (str): Old filename which is to be removed.
        """
        _filename_in_inventory = aFileName
        try:
            # Check the inventory,json for presence of file
            for num, image in enumerate(self._inventory_json_data['grid-klones']):
                if not image["files"]:
                    continue
                if _filename_in_inventory == image["files"][0]['path']:
                    ebLogInfo(f"File {_filename_in_inventory} to be deleted found in inventory.json")
                    del self._inventory_json_data['grid-klones'][num]
                    break
        except Exception as e:
            _err_msg = f"Failed to remove entry for {aFileName} in inventory.json due to error : {e}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg)
        
    def mRemoveFileFromRepo(self, aFileAbsPath):
        """Remove image file from repository

        Args:
            aFileAbsPath (str): Absolute path of file to be removed.
        """
        try:
            if not os.path.exists(aFileAbsPath):
                ebLogError(f"File at path {aFileAbsPath} not present !")
                return
            os.remove(aFileAbsPath)
            ebLogInfo(f"Image {aFileAbsPath} removed successfully.")
        except FileNotFoundError:
            ebLogError(f"Image {aFileAbsPath} not found.")
        except PermissionError:
            ebLogError(f"Permission denied for removing image {aFileAbsPath}.")
        
    def mBackupInventoryJson(self, aInventoryjsonPath):
        """Backup of inventory.json file
        Returns:
            str: backup file name
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            file_name, file_extension = os.path.splitext(aInventoryjsonPath)
            backup_file_name = f"{file_name}_{self.operation_type}_{timestamp}{file_extension}"
            os.rename(aInventoryjsonPath, backup_file_name)
            ebLogInfo(f"Renamed inventory.json to: {backup_file_name}")
            self._inventoryjson_backup_file_name = backup_file_name
            return True
        except Exception as e:
            ebLogError(f' Renaming inventory.json for backup failed due to : {e}')
    
    def mRevertInventoryJson(self):
        """Replace the patched inventory.json by orginal.
        """
        if not os.path.exists(self.inventory_json_backup_file):
            ebLogError(f" Inventory.json backup does not exist ! Unable to revert")
            return
        os.rename(self._inventoryjson_backup_file_name, self._inventory_json_path)
        ebLogInfo("Successfully reverted inventory.json")
        
    def mSetDefaultFalseInInventory(self):
        """Set default flag false across inventory 
        as new image has default and inventory 
        can have only one default 
        """
        try:
            for image in self._inventory_json_data['grid-klones']:
                if image['xmeta']['default']:
                    ebLogInfo(f"Removing current default tag from {image['files'][0]['path']}")
                    image['xmeta']['default'] = False
        except Exception as e:
            _err_msg = f"Failed to update inventory.json due to error : {e}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg)
                
    def mSetLatestFalseInInventory(self):
        """ Update latest field in inventory.json 
        in case of addition of release images

        Args:
            aInventoryJson (_dict_): inventory.json data

        Raises:
            ExacloudRuntimeError: To handle any format errors during iteration

        Returns:
            _dict_: updated inventory.json data
        """
        try:
            for image in self._inventory_json_data['grid-klones']:
                # each service and major version has a latest image
                if image["service"][0] == self.service_type and image["version"].split(".")[0] == self.major_version:
                    if image['xmeta']['latest']:
                        ebLogInfo(f"Removing current latest tag from {image['files'][0]['path']}")
                        image['xmeta']['latest'] = False
        except Exception as e:
            _err_msg = f"Failed to update inventory.json due to error : {e}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg)
            
    def mExecute(self, json_payload):
        try:
            _rc = self.update_repository(json_payload)
            return _rc
        except Exception as e:
            _err_msg =  f"GI image operation failed due to error : {e}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorCode=1, aErrorMsg=_err_msg)

    def update_repository(self, json_payload):
        raise NotImplementedError

    def mGetGIResponseData(self):
        return self.gi_response_data

    def mSetGIResponseData(self, aGiResoponseData):
        ebLogTrace(f"mSetGIResponseData set data to: {aGiResoponseData}")
        self.gi_response_data = aGiResoponseData

class ebTarBundleUpdate(ebCluGiRepoUpdate):
    def __init__(self, ebox, payload):
        super().__init__(ebox)
        super().mParsePayload(payload)
        self.bundle_path = None
         
    def mAddGiImageToRepo(self, image_data):
        """Method to Add new GI image to repository
        """
        try:
            ebLogInfo(f'Image Addition to repo in progress ...')
            os.makedirs(os.path.dirname(self.img_dest_path), exist_ok=True)

            ebLogInfo(f'Moving Image from {self.img_src_path} to {self.img_dest_path}')
            shutil.move(self.img_src_path, self.img_dest_path)
            dest_copied = True
            # if new added image is latest , remove latest tag from current latest image
            if self.image_default_status:
                self.mSetDefaultFalseInInventory()
            if self.image_latest_status:
                self.mSetLatestFalseInInventory()
            # add new image information
            self.mAddEntryToInventory(image_data)
            # keep list of images to be copied on secondary server
            self.replication_image_list.append(self.img_dest_path)
        except Exception as e:
            _err_msg =  f"ADD operation failed due to error : {e}"
            ebLogError(_err_msg)
            raise 
        
    def update_repository(self, payload):  
        """  
        Update the local repository with the new inventory data from the tar file.  
        """  
        ebLogInfo('Tar file from file system provided')  
        
        try:
            if payload["location"]["type"] == "local_tar":
                self.bundle_path = payload["location"]["source"]
            else:
                self.bundle_path = mDownloadFromBucket(payload["location"], self.getRepoPath())
            self.new_repo_path = mUntarBundle(self.bundle_path)
            
            # Untar and get inventory data 
            _new_inventory_path = os.path.join(self.new_repo_path, 'inventory.json')  
        
            with open(_new_inventory_path, "r") as _fd_read:  
                invstr = _fd_read.read()  
                self.new_inventory_data = json.loads(invstr)  
            
            # Iterate over the new inventory data and update repository  
            for image in self.new_inventory_data['grid-klones']:  
                ebLogInfo(f'*** Iteration begins for {image["service"]}:{image["version"]} ***')  
                self.mParseNewInventoryJson(image)
                
                if self.mCheckImageExists():
                    continue
                
                if self.operation_type == 'ADD':  
                    self.mAddGiImageToRepo(image)
            
                # Maintain the count of files as per configuration  
                if self.operation_type == 'ADD' and self.image_type == 'RELEASE':  
                    _files_to_remove = self.mGetOlderVersionFiles()  
                    
                    for _filename in _files_to_remove:  
                        self.mRemoveEntryFromInventory(_filename)  
                        
                        if self.delete_old_image:  
                            _abs_path = os.path.join(self.getRepoPath(), _filename)
                            if os.path.exists(_abs_path):
                                self.mRemoveFileFromRepo(_abs_path)
                            
                ebLogInfo(f'*** Iteration ends for {image["service"]}:{image["version"]} *** \n')  
            
            self.mWriteToInventoryJson()  
            # Replicate on the secondary ecra nodes  
            self.mReplicateImageRepoOnSecondaryEcra()  
            delete_extracted_folder(self.new_repo_path)  
            _response = {"ADDED": self._inventory_json_data}  
            self.mSetGIResponseData(_response)  
            return 0  
        
        except Exception as e:
            if os.path.exists(self.new_repo_path):
                delete_extracted_folder(self.new_repo_path)
            _err_msg = f"GI image operation failed due to error: {e}"  
            ebLogError(_err_msg)  
            raise ExacloudRuntimeError(aErrorCode=1, aErrorMsg=_err_msg)
            

class ebSingleImageUpdate(ebCluGiRepoUpdate):
    def __init__(self,ebox, payload):
        super().__init__(ebox)
        super().mParsePayload(payload)
        self.new_image_name = None
        self.sha256sum = payload["location"]["sha256sum"]
        self.location_details = payload["location"]
        self.version = payload["version"]
        self.major_version = self.version.split(".")[0]
        self.system_type = payload["system_type"]
        self.is_oss = payload["location"]["type"]
        self.service_type = 'ATP' if self.system_type == 'ADBD' else 'EXACS'
        self.file_name_in_payload = payload['location']['filename']
        self.image_default_status = payload.get('xmeta', {}).get('latest', True)
        self.image_latest_status = payload.get('xmeta', {}).get('default', True)
        
    def mPrepareMockInventoryData(self, payload):
        """Create inventory data like structure for direct image downloads
        This is so that minimal changes are done in existing flow
        """
        _image_file_name = self.file_name_in_payload.split('/')[-1]
        _image_file_basename, _image_file_ext = os.path.splitext(_image_file_name)

        # don't trust original filename as it can conflict. use version as true ID
        # so the mAddGiImageToRepo won't fail
        # <original basename>__191900230418.<ext>
        # this filename pattern is required for oeda to work
        # grid-klone-Linux-x86-64-191900230418.zip
        self.new_image_name = f"grid-klone-Linux-x86-64-{self.version.replace('.', '')}{_image_file_ext}"
        if self.service_type == 'EXACS':
            _default_status = self.image_default_status
            _latest_status = self.image_latest_status 
        else:
            # ADBD only have single entries , hence we hardcode the status 
            _default_status = False 
            _latest_status = True
        
        self.new_inventory_data = {
                "files": [
                    {
                        "path": f'{payload["system_type"]}/{self.new_image_name}',
                        "type": "grid",
                        "sha256sum": f'{payload["location"]["sha256sum"]}'
                    }
                ],
                "xmeta": {
                    "default": _default_status,
                    "ol7_required": True,
                    "imgtype": f'{payload["image_type"]}',
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": _latest_status
                },
                "version": f'{self.version}',
                "service": [f'{self.service_type}']
            }
        
    def mAddGiImageToRepo(self):
        """Method to Add new GI image to repository
        """
        dest_copied = False
        try:
            ebLogInfo(f'Image Addition to repo in progress ...')
            
            if os.path.exists(self.img_dest_path):
                # if image of same name exists , rename it
                _image_backup = f'{self.img_dest_path}_backup_{datetime.now().strftime("%Y%m%d%H%M%S")}'
                shutil.move(self.img_dest_path, _image_backup)
                ebLogInfo(f"Image with same name present , renamed to {_image_backup}!")
                self.image_remove_list.append(_image_backup)
                
            os.makedirs(os.path.dirname(self.img_dest_path), exist_ok=True)

            ebLogInfo(f'Moving Image from {self.img_src_path} to {self.img_dest_path}')
            shutil.move(self.img_src_path, self.img_dest_path)
            dest_copied = True
            # if new added image is latest , remove latest tag from current latest image
            if self.image_default_status:
                self.mSetDefaultFalseInInventory()
            if self.image_latest_status:
                self.mSetLatestFalseInInventory()
            # add new image information
            self.mAddEntryToInventory(self.new_inventory_data)
            # keep list of images to be copied on secondary server
            self.replication_image_list.append(self.img_dest_path)
        except Exception as e:
            if dest_copied and os.path.exists(self.img_dest_path):
                os.remove(self.img_dest_path)
            _err_msg =  f"ADD operation failed due to error : {e}"
            ebLogError(_err_msg)
            raise ExacloudRuntimeError(aErrorMsg=_err_msg)
        
    def update_repository(self, aPayload):  
        """  
        Update the local repository with a single image based on the provided payload.  
        """  
        try:
            if aPayload['location']['type'] == 'local_image':
                self.img_src_path = aPayload['location']['source']
            else:
                self.img_src_path = mDownloadFromBucket(self.location_details, self.getRepoPath())
            self.mVerifyImageCheckSum()
            self.mPrepareMockInventoryData(aPayload)
            self.img_dest_path = f'{self.getRepoPath()}/{self.system_type}/{self.new_image_name}'
            
            if self.mCheckImageExists():
                _response = {"ADDED": self._inventory_json_data}
                self.mSetGIResponseData(_response)
                return 0
            
            if self.operation_type == 'ADD':
                self.mAddGiImageToRepo()
                
            # Maintain the count of files as per configuration  
            if self.operation_type == 'ADD' and self.image_type == 'RELEASE':  
                _files_to_remove = self.mGetOlderVersionFiles()  
                
                for _filename in _files_to_remove:  
                    self.mRemoveEntryFromInventory(_filename)  
                    
                    if self.delete_old_image:  
                        _abs_path = os.path.join(self.getRepoPath(), _filename)  
                        self.mRemoveFileFromRepo(_abs_path)  

            self.mWriteToInventoryJson()  
            # Replicate on the secondary ECRA nodes  
            self.mReplicateImageRepoOnSecondaryEcra()  
            _response = {"ADDED": self._inventory_json_data}  
            self.mSetGIResponseData(_response)  
            return 0  
        
        except Exception as e:
            mRemoveImage(self.img_src_path)
            _err_msg = f"GI image operation failed due to error: {e}"  
            ebLogError(_err_msg)  
            raise ExacloudRuntimeError(aErrorCode=1, aErrorMsg=_err_msg)
               
class SingleImageUpdateOldFormat(ebSingleImageUpdate):
    def __init__(self,ebox, payload):
        super().__init__(ebox, payload)
        super().mParsePayload(payload)
        self._redundant_img_path = None
        self.dest_dir = None
              
    def mGetImageDataOldFormat(self):
        _payload_major_version_ = self.version.split(".")[0]
        for num, _dict in enumerate(self._inventory_json_data['grid-klones']):
            version_str = _dict.get('version')
            major_ver = version_str.split(".")[0]
            service_type = _dict.get('service')[0]
            if _payload_major_version_ == major_ver and self.service_type == service_type:
                # Delete the data to avoid redundency
                self._redundant_img_path = _dict["files"][0]["path"]
                del self._inventory_json_data['grid-klones'][num]
                return _dict
            
    def mUpdateInventoryDataOldFormat(self, aOldInventoryData):
        """Create old format inventory data like structure for direct image downloads
        This is so that minimal changes are done in existing flow
        """
        # Generate image name
        _version_major = self.version.split(".")[0]
        _version_rudate = self.version.split(".")[-1]
        self.new_image_name = f"grid-klone-Linux-x86-64-{_version_major}000{_version_rudate}.zip"
        
        self.dest_dir = aOldInventoryData["files"][0]["path"].split("/")[0]
        self.new_inventory_data = aOldInventoryData
        self.new_inventory_data["service"] = [self.service_type]
        self.new_inventory_data["cdate"] = _version_rudate
        self.new_inventory_data["files"][0]["path"] = f"{self.dest_dir}/{self.new_image_name}"
        self.new_inventory_data["files"][0]["sha256sum"] = self.sha256sum
        
    def mAddGiImageToRepo(self):
        """Method to Add new GI image to repository
        """
        try:
            ebLogInfo(f'Image Addition to repo in progress ...')    
            os.makedirs(os.path.dirname(self.img_dest_path), exist_ok=True)

            ebLogInfo(f'Moving Image from {self.img_src_path} to {self.img_dest_path}')
            shutil.move(self.img_src_path, self.img_dest_path)
            # add new image information
            self.mAddEntryToInventory(self.new_inventory_data)
            # keep list of images to be copied on secondary server
            self.replication_image_list.append(self.img_dest_path)
        except Exception as e:
            _err_msg =  f"ADD operation failed due to error : {e}"
            ebLogError(_err_msg)
            raise
        
    def update_repository(self, aPayload):  
        """  
        Update the local repository with a single image based on the provided payload.  
        """  
        try:  
            self.mParsePayload(aPayload)
            if aPayload['location']['type'] == 'local_image':
                self.img_src_path = aPayload['location']['source']
            else:
                self.img_src_path = mDownloadFromBucket(self.location_details, self.getRepoPath())
            self.mVerifyImageCheckSum()
            
            # Get the inventory data to be replaced
            _old_inventory_data =  self.mGetImageDataOldFormat()
            # Update the dictionary with payload details
            self.mUpdateInventoryDataOldFormat(_old_inventory_data)
            self.img_dest_path = f'{self.getRepoPath()}/grid-klones/{self.dest_dir}/{self.new_image_name}'
            # Check if same image exists 
            if self.mCheckImageExists():
                _response = {"ADDED": self._inventory_json_data}
                self.mSetGIResponseData(_response)
                return 0
            
            if self.operation_type == 'ADD':
                self.mAddGiImageToRepo()
                
            if self.operation_type == 'ADD' and self.image_type == 'RELEASE':
                if self.delete_old_image and self._redundant_img_path:
                    _abs_path = os.path.join(self.getRepoPath(), 'grid-klones', self._redundant_img_path)
                    self.mRemoveFileFromRepo(_abs_path)

            self.mWriteToInventoryJson()  
            # Replicate on the secondary ECRA nodes  
            self.mReplicateImageRepoOnSecondaryEcra()
            _response = {"ADDED": self._inventory_json_data}
            self.mSetGIResponseData(_response)
            return 0
        
        except Exception as e:
            mRemoveImage(self.img_src_path)
            _err_msg = f"GI image operation failed due to error: {e}"  
            ebLogError(_err_msg)  
            raise ExacloudRuntimeError(aErrorCode=1, aErrorMsg=_err_msg)
        
#------------------
# HELPER METHODS
#------------------

def mDownloadFromBucket(download_info, image_dir):
    """Download new image file from provided bucket address
    """
    namespace = download_info['namespace'] #"idd1ng7x2ake"
    #_namespace = _objectStorage.get_namespace().data
    bucket =  download_info['bucket'] #"atp-patches"
    object_name = download_info['filename'] #"test/gi_images/ADBD_dynximages-19.22.0.0.240108.tar"
    file_name = object_name.split('/')[-1]
    destination_path = os.path.join(image_dir, file_name)
    _factory = ExaOCIFactory()
    # Create an OCI Object Storage client
    _objectStorage = _factory.get_object_storage_client()
    try:
        _resp = _objectStorage.get_object(namespace, bucket, object_name)
        # Download the file
        with open(destination_path, "wb") as f:
            for chunk in _resp.data.raw.stream(1024 * 1024, decode_content=False):
                f.write(chunk)

        return destination_path
    except Exception as e:
        if os.path.exists(destination_path):
            os.remove(destination_path)
        _msg = f"Response unexpected: {e}"
        ebLogError(_msg)
        raise ExacloudRuntimeError(aErrorMsg=_msg) from e
       
def mComputeSha256sum(aImagepath):
    """Compute sha256sum of file present in repository.

    Returns:
        str: computed hash value
    """

    ebLogInfo(f"Computing SHA256 checksum of file: {aImagepath}")
    new_sha256_sum = -1
    sha256_hash = hashlib.sha256()
    with open(aImagepath,"rb") as f:
        for byte_block in iter(lambda: f.read(65536),b''):
            sha256_hash.update(byte_block)
        new_sha256_sum = sha256_hash.hexdigest()
    ebLogInfo(f"SHA256 checksum computed: {new_sha256_sum}")
    return new_sha256_sum

def mReadInventoryJson(aInventoryJsonPath):
    
    # Read the existing inventory
    ebLogInfo(f'Reading inventory.json from {aInventoryJsonPath}')
    with open(aInventoryJsonPath, "r") as _fd_read:
        invstr = _fd_read.read()
        _inventory_data = json.loads(invstr)
        return _inventory_data

def mUntarBundle(aBundlePath):
    # Check if the tar file exists
    _bundle_path = aBundlePath
    # Extract the directory path and the base name (without extension)
    dir_path, base_name = os.path.split(_bundle_path)
    new_dir_name = os.path.splitext(base_name)[0]  # Remove the extension 
    split_dir_name = base_name.split('.') 
    
    if split_dir_name[-1] != 'tar':
        ebLogTrace("Not a tar file, skip untar process")
        return _bundle_path
     
    # if tar provided check if it exists
    if not os.path.exists(_bundle_path):
        ebLogError(f"Image bundle : {_bundle_path} does not exist!")
        return None
    
    try:
        # create directory for untarring bundle
        new_dir_path = os.path.join(dir_path, new_dir_name)
        os.makedirs(new_dir_path)
        ebLogInfo(f"Extracting GI bundle at :{new_dir_path} ...")
        with tarfile.open(_bundle_path, "r:*") as tar_ref:
            tar_ref.extractall(path=new_dir_path)
            ebLogInfo(f"Successfully extracted. Folder created: {new_dir_path}")
            return new_dir_path
    except Exception as e:
        return f"An error occurred: {e}"

def mRemoveImage(aPath):
    if os.path.exists(aPath):
        os.remove(aPath)
        
def delete_extracted_folder(folder_path):
    # Check if the folder exists
    if not os.path.exists(folder_path):
        ebLogTrace(f"Folder does not exist: {folder_path}")
        return
    
    # Delete the folder
    try:
        shutil.rmtree(folder_path)
        ebLogTrace(f"Successfully deleted folder: {folder_path}")
    except Exception as e:
        ebLogError(f"An error occurred while deleting the folder: {e}")