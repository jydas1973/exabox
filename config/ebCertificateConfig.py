"""
 Copyright (c) 2014, 2021, Oracle and/or its affiliates. 

NAME:
    ebCertificateConfig - HTTPS and Certificate config reader utility

FUNCTION:
    HTTPS and Certificate config reader utility

NOTE:
    None

History:
    ndesanto    11/07/2019 - File Creation
"""

import json
import os

from typing import Any, Dict


class ebCertificateConfig(object):

    def __init__(self, cfg_app:str, cfg_file_path:str=''):
        if not os.path.exists(cfg_file_path):
            raise Exception("ERROR: {} configuration file not found."\
                .format(cfg_file_path))
        
        self.__dict_config: Dict[str, Any] = {}
        self.__app_config: Dict[str, Any] = {}
        with open(cfg_file_path) as _fd:
            self.__dict_config = json.load(_fd)
            self.__app_config = self.__dict_config[cfg_app]

    def __contains__(self, item:object) -> bool:
        for key in self.__app_config:
            if item == self.__app_config[key]:
                return True
        return False

    def __missing__(self, key:str) -> bool:
        return key in self.__app_config

    def __getitem__(self, key:str) -> object:
        if key not in self.__app_config:
            raise Exception("ERROR: {} key not found.".format(key))

        return self.__app_config[key]
    
    def __str__(self) -> str:
        return str(self.__app_config)
