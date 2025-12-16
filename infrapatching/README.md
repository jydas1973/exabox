**Changed Needed in Exacloud files for Infra Patching Testing with the New Framework**  

```buildoutcfg

Infrapatching Directory structure

infrapatching (mw_home/user_projects/domains/exacloud/exabox/infrapatching)
├── core
│   ├── cludispatcher.py
│   ├── clupatchHealthCheck.py
│   ├── clupatchmetadata.py
│   ├── ibclusterpatch.py
│   ├── ibfabricpatch.py
│   ├── __init__.py
├── handlers
│   ├── genericHandler.py
│   ├── handlertypes.py
│   ├── __init__.py
│   ├── pluginHandler
│   │   ├── dbNuPluginHandler.py
│   │   ├── exacloudPluginHandler.py
│   │   ├── __init__.py
│   │   ├── oneOffPluginHandler.py
│   │   ├── pluginHandler.py
│   │   ├── pluginHandlerTypes.py
│   ├── targetHandler
│   │   ├── cellHandler.py
│   │   ├── dom0Handler.py
│   │   ├── domuHandler.py
│   │   ├── __init__.py
│   │   ├── switchHandler.py
│   │   ├── targetHandler.py
│   └── taskHandler
│       ├── backupImageHandler.py
│       ├── __init__.py
│       ├── patchHandler.py
│       ├── plugintasksHandler.py
│       ├── postcheckHandler.py
│       ├── prereqHandler.py
│       ├── rollbackHandler.py
│       ├── rollbackPrereqHandler.py
│       ├── taskHandler.py
├── __init__.py
├── test
│   ├── __init__.py
│   └── test_patch.py
└── utils
    ├── constants.py
    ├── __init__.py
    ├── Utility.py

7 directories, 72 files

```

The design and the spec document for this code change is [here](https://confluence.oraclecorp.com/confluence/display/EIP/Code+Modularity+for+Infra+Patching)

 - The ebCluPatchDispatcher class has been moved to a new package exabox.infrapatching.utils.cludispatcher. All references to this class needs to be changed in other files . The list of files affected by this are
	 - exabox/agent/Worker.py
		 - Replace ***'from exabox.ovm.clupatching import ebCluPatchDispatcher'*** with ***'from exabox.infrapatching.core.cludispatcher import ebCluPatchDispatcher' ***
	 - exabox/agent/Agent.py
		 - Remove the unwanted import *** 'from exabox.ovm.clupatching import ebCluPatchDispatcher'***
	 - exabox/bin/exabox.py
		 - Replace ***'from exabox.ovm.clupatching import ebCluPatchDispatcher'*** with *** 'from exabox.infrapatching.core.cludispatcher import ebCluPatchDispatcher' ***

The following changes are to be made in the exabox/ovm/clucontrol.py file

 - The class ebCluPatchControl (which is the current exabox/ovm/clucontrol.py) will cease to exist and will be replaced by different classes from new framework
 - Replace ebCluPatchHealthCheck import to ***'from exabox.infrapatching.core.clupatchhealthcheck import ebCluPatchHealthCheck'***
 - Add the import  ***from exabox.infrapatching.handlers.handlertypes import getInfraPatchingTaskHandlerInstance***
 - The file exabox/ovm/clucontrol.py has lot of constants which refers to  ebCluPatchControl like
	 - ebCluPatchControl.KEY_NAME_CellPatchFile
	 - ebCluPatchControl.KEY_NAME_SwitchPatchFile
	 - other constants (like ebCluPatchControl.KEY_NAME_DBPatchFile etc)
	 - All the above had been moved to a constants file under exabox/infrapatching/utils/constants.py . So the reference to these constant variables needs to be changed in clucontrol
		 - CluControl file needs to have this import added
			 - ***from exabox.infrapatching.utils.constants import KEY_NAME_CellPatchFile, KEY_NAME_SwitchPatchFile, KEY_NAME_DBPatchFile, \  
    KEY_NAME_Dom0_YumRepository, KEY_NAME_Domu_YumRepository, KEY_NAME_PatchFile, PATCH_CELL, PATCH_IBSWITCH, \  
    PAYLOAD_NON_RELEASE, PATCH_ALL, PATCH_DOM0 ,PATCH_DOMU***
		All the constants defined above needs to have the ebCluPatchControl prefix removed from them
		
 - The file exabox/ovm/clucontrol.py also needs to be changed to incorporate the call to the new framework
	 - The following lines of code needs to be commented
	    ```
            # Create clupatching instance
            _patch_mgr = ebCluPatchControl(self,
                            aLocalLog=_log_path,
                            aTargetType=_target_type,
                            aTask = aCmd,
                            aOperationStyle = _op_style,
                            aPayloadType = _payload,
                            aTargetEnv = _target_env,
                            aCellIBSwitchesPatchZipFile = _patch_file_cells,
                            aDom0DomuPatchZipFiles = _patch_files_dom0s_or_domus,
                            aTargetVersion = _target_version,
                            aClusterID = _cluster_id,
                            aBackupMode = _backup_mode,
                            aEnablePlugins = _enable_plugins,
                            aPluginTypes = _plugin_types,
                            aFedramp = _fedramp,
                            aRetry = _retry_flag,
                            aRequestId = _request_id,
                            aRackName = _rack_name,
                            aAdditionalOptions = _additional_options)
            # Run patch or rollback
            _patch_mgr_return_val = _patch_mgr.mRunPatchMgr()
            return _patch_mgr_return_val

	    ```
	 - The below lines of code needs to be incorporated in the same place
		 ```
            # Create clupatching instance
            _patch_args_dict = { 
                "CluControl": self,  
                "LocalLogFile": _log_path,  
                "TargetType": _target_type, 
                "Operation": aCmd,  
                "OperationStyle": _op_style,
                "PayloadType": _payload,   
                "TargetEnv": _target_env, 
                "EnablePlugins": _enable_plugins,  
                "PluginTypes": _plugin_types,  
                "CellIBSwitchesPatchZipFile": _patch_file_cells,  
                "Dom0DomuPatchZipFile": _patch_files_dom0s_or_domus,  
                "TargetVersion": _target_version,  
                "ClusterID":_cluster_id,
                "BackupMode": _backup_mode,
                "Fedramp": _fedramp,  
                "Retry": _retry_flag,  
                "RequestId": _request_id,
                "RackName" : _rack_name,
                "AdditionalOptions": _additional_options  
            } 
            _patch_mgr_return_val = 0
            _taskHandlerInstance = getInfraPatchingTaskHandlerInstance(_patch_args_dict)
            _patch_mgr_return_val = _taskHandlerInstance.mExecuteTask()

            return _patch_mgr_return_val

		 ```
		
  

  
---  
  
**Test Related commands**  

 - Plugin Related commands
	 ```
	 patch dom0 slcs08adm07adm08 op=patch EnablePlugins=yes PluginTypes=dom0+dom0domu"
	 patch dom0 slcs08adm07adm08 op=patch EnablePlugins=yes PluginTypes=dom0"
	 patch domu slcs08adm07adm08 op=patch EnablePlugins=yes PluginTypes=domu 
	 patch dom0 slcs08adm07adm08 op = patch EnablePlugins = yes PluginTypes = dbnu-plugin  
	 In case we need to run both plugin, we can specify options as below. 
	 patch dom0 slcs08adm07adm08 op=patch EnablePlugins=yes PluginTypes=Dom0+dbnu-plugin
	 ```
 - Dom0 Testing Commands
   ```
   patch dom0 slcs27adm0304clu6 op=patch
   patch dom0 slcs27adm0304clu6 op=rollback
   patch dom0 slcs27adm0304clu6 op=patch_prereq_check
   patch dom0 slcs27 op=patch isSingleNodeUpgrade=yes SingleUpgradeNodeName=slcs27adm02.us.oracle.com
   patch dom0 slcs27adm0304clu6 op=rollback isSingleNodeUpgrade=yes   SingleUpgradeNodeName=slcs27adm03.us.oracle.com
   
   ```
 - Domu Testing commands
    ```
    patch domu slcs27 op=patch_prereq_check
    patch domu slcs27 op=patch
    patch domu slcs27 op=rollback
   patch domu slcs27 op=patch isSingleNodeUpgrade=yes SingleUpgradeNodeName=slcs27adm01.us.oracle.com
   patch domu slcs27 op=rollback isSingleNodeUpgrade=yes   SingleUpgradeNodeName=slcs27adm01.us.oracle.com
    patch domu slcs27  op=patch EnablePlugins=yes PluginTypes=domu
    patch domu slcs27  op=rollback EnablePlugins=yes PluginTypes=domu
    ```
