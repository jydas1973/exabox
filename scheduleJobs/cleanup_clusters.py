#!/bin/python
#
# $Header: ecs/exacloud/exabox/scheduleJobs/cleanup_clusters.py /main/1 2024/02/19 06:45:03 aararora Exp $
#
# cleanup_clusters.py
#
# Copyright (c) 2023, Oracle and/or its affiliates.
#
#    NAME
#      cleanup_clusters.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      This file is to create a scheduler to delete cluster xml files generated
#      clusters/ folder.
#
#      As part of bug 35863722, the xmls files under clusters/PodRepo folder
#      will be periodically removed.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    12/19/23 - Bug 35863722: Scheduler to delete xml files under
#                           PodRepo directory periodically.
#    aararora    12/19/23 - Creation
#
import glob
import os
import time
from exabox.core.Context import get_gcontext
from exabox.core.Core import exaBoxCoreInit
from exabox.log.LogMgr import ebLogInit, ebLogInfo, ebLogError

class CleanUpClustersFolder():

    def __init__(self):
        exaBoxCoreInit({})
        self.__ctx = get_gcontext()
        self.__options = self.__ctx.mGetArgsOptions()
        ebLogInit(self.__ctx, self.__options)

        self.__exacloudPath = os.getcwd()
        self.__exacloudPath = self.__exacloudPath[0: self.__exacloudPath.rfind("exacloud")+8]

        # 336 hours is 14 days
        # 14 days is needed since the original cluster xml maybe required for debugging purpose
        self.__clusters_podrepo_cleanup_duration_hours = 336

        self.mParseConfig()

    def mParseConfig(self):

        _clusters_podrepo_cleanup_duration_hours = int(get_gcontext().mGetConfigOptions().get("clusters_podrepo_cleanup_duration_hours", "336"))
        if _clusters_podrepo_cleanup_duration_hours:
            self.__clusters_podrepo_cleanup_duration_hours = int(_clusters_podrepo_cleanup_duration_hours)

    def mExecuteJob(self):

        _exacloud_clusters_PodRepo_dir = os.path.join(self.__exacloudPath, "clusters/PodRepo")
        ebLogInfo(f"Executing CleanUpClustersFolder on directory: {_exacloud_clusters_PodRepo_dir}")
        _podrepo_xml_files = list(glob.glob(os.path.join(_exacloud_clusters_PodRepo_dir, "*.xml")))

        _current_time = time.time()
        _n_PodRepo_xmls_removed = 0
        _persist_duration_sec = self.__clusters_podrepo_cleanup_duration_hours * 3600
        for _podrepo_xml_file in _podrepo_xml_files:
            _last_modification_time = os.path.getmtime(_podrepo_xml_file)
            if (_current_time - _last_modification_time) > _persist_duration_sec:
                _n_PodRepo_xmls_removed = _n_PodRepo_xmls_removed + 1
                os.remove(_podrepo_xml_file)

        ebLogInfo(f"Removed {_n_PodRepo_xmls_removed} xml files from clusters/PodRepo folder.")

        _podrepo_xml_files.clear()


if __name__ == '__main__':
    try:
        clean = CleanUpClustersFolder()
        clean.mExecuteJob()
    except Exception as ex:
        ebLogError(f"Exception while removing xml files from clusters/PodRepo folder: {ex}")