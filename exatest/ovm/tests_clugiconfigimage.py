#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/ovm/tests_clugiconfigimage.py /main/14 2025/08/19 08:39:20 akkar Exp $
#
# test_clugiconfigimage.py
#
# Copyright (c) 2023, 2025, Oracle and/or its affiliates.
#
#    NAME
#      test_clugiconfigimage.py - Test cases for ebCluGiConfigImage methods
#
#    DESCRIPTION
#      Test cases to test the add delete update flows .
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    akkar       07/23/25 - Bug 38227428: Add more test cases
#    akkar       05/19/25 - Bug 37964965: Fix image name in inventory.json for
#                           multigi
#    akkar       09/10/24 - Bug 37043379: Revert image naming format
#    akkar       09/05/24 - Bug 37026513: Fix test case for adbd changes
#    akkar       08/21/23 - Creation
#
import copy
import shutil
import unittest
import warnings
import os
import pathlib
import tempfile
from unittest import mock
from unittest.mock import MagicMock, Mock, patch, mock_open

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.MockCommand import exaMockCommand
from exabox.core.Error import ExacloudRuntimeError
from exabox.log.LogMgr import ebLogInfo, ebLogError
from exabox.ovm.clugiconfigimage import ebCluGiRepoUpdate, ebTarBundleUpdate
from exabox.ovm.clucontrol import exaBoxCluCtrl
from exabox.core.Context import get_gcontext
import json

inventory_json_old_format = {
            "db-klones": [],
            "grid-klones": [
                {
                    "files": [],
                    "bpname": "OCT2024",
                    "service": [
                        "EXACS",
                        "ATP"
                    ],
                    "cdate": "241015",
                    "version": "12.1.0.2",
                    "xmeta": {
                        "supported_db": [
                            "121",
                            "112"
                        ],
                        "default": False,
                        "virtual": True,
                        "ol7_required": False,
                        "oeda_date": "180116",
                        "oeda_version": "2018.016",
                        "latest": False
                    }
                },
                {
                    "files": [],
                    "bpname": "OCT2024",
                    "service": [
                        "EXACS",
                        "ATP"
                    ],
                    "cdate": "241015",
                    "version": "12.2.0.1",
                    "xmeta": {
                        "supported_db": [
                            "122",
                            "121",
                            "112"
                        ],
                        "default": False,
                        "virtual": True,
                        "ol7_required": False,
                        "oeda_date": "180717",
                        "oeda_version": "2018.198",
                        "latest": False
                    }
                },
                {
                    "files": [],
                    "bpname": "OCT2024",
                    "service": [
                        "EXACS",
                        "ATP"
                    ],
                    "cdate": "241015",
                    "version": "18.1.0.0",
                    "xmeta": {
                        "supported_db": [
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "default": False,
                        "virtual": True,
                        "ol7_required": False,
                        "oeda_version": "2021.019",
                        "latest": False
                    }
                },
                {
                    "files": [
                        {
                            "path": "OCT2024/grid-klone-Linux-x86-64-19000241015.zip",
                            "type": "grid",
                            "sha256sum": "ad19d35e0dfca6bb6c7bd066493d7f0a60634bcb5c28e35a151fb9129c3caf93"
                        }
                    ],
                    "bpname": "OCT2024",
                    "service": [
                        "EXACS"
                    ],
                    "cdate": "241015",
                    "version": "19.0.0.0",
                    "xmeta": {
                        "default": True,
                        "ol7_required": True,
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "oeda_version": "2021.019",
                        "latest": False
                    }
                },
                {
                    "files": [
                        {
                            "path": "OCT2024/grid-klone-Linux-x86-64-23000241015.zip",
                            "type": "grid",
                            "sha256sum": "4f5e1623770974d4cda63c4b65cb7fbccdf212c639a30a897cb4a520737b413d"
                        }
                    ],
                    "bpname": "OCT2024",
                    "service": [
                        "EXACS"
                    ],
                    "cdate": "241015",
                    "version": "23.0.0.0",
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "oeda_version": "2021.019",
                        "latest": True
                    }
                },
                {
                    "files": [
                        {
                            "path": "ATP_192500/grid-klone-Linux-x86-64-19000241015.zip",
                            "type": "grid",
                            "sha256sum": "ad19d35e0dfca6bb6c7bd066493d7f0a60634bcb5c28e35a151fb9129c3caf93"
                        }
                    ],
                    "bpname": "OCT2024",
                    "service": [
                        "ATP"
                    ],
                    "cdate": "241015",
                    "version": "19.0.0.0",
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "oeda_version": "2021.019",
                        "latest": False
                    }
                },
                {
                    "files": [
                        {
                            "path": "ATP_2360/grid-klone-Linux-x86-64-23000241015.zip",
                            "type": "grid",
                            "sha256sum": "4f5e1623770974d4cda63c4b65cb7fbccdf212c639a30a897cb4a520737b413d"
                        }
                    ],
                    "bpname": "OCT2024",
                    "service": [
                        "ATP"
                    ],
                    "cdate": "241015",
                    "version": "23.0.0.0",
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "oeda_version": "2021.019",
                        "latest": True
                    }
                }
            ],
            "gendate": "2024-11-12 15:04:38.865784",
            "dbnid": []
        }


class ebTestCluGiConfigImage(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluGiConfigImage, self).setUpClass(aGenerateDatabase = False)
        warnings.filterwarnings("ignore")
        self.image_repo = tempfile.mkdtemp(prefix='cleanmain_repo')
        self.latest_dir =  os.path.join(self.image_repo, 'multigibundle')
        os.makedirs(self.latest_dir)
        self.exacs_dir  = os.path.join(self.latest_dir, 'EXACS')
        os.makedirs(self.exacs_dir)
        self.adbd_dir = os.path.join(self.latest_dir, 'ADBD')
        os.makedirs(self.adbd_dir)
    
    @classmethod
    def tearDownClass(self) -> None:
        shutil.rmtree(self.image_repo)
    
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982")
    def test_incremental_bundle_flow_image_count4(self, mMockSha256):
        """Test image addition flow
        """
        _inventory_json = {
            "grid-klones": [
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192600250121.zip",
                            "type": "grid",
                            "sha256sum": "104cca2e83085c53fedbc5bb8bf10444d4f1e7a4c420d4e7be0414bc231bff0c"
                        }
                    ],
                    "xmeta": {
                        "default": True,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "19.26.0.0.250121",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192500241015.zip",
                            "type": "grid",
                            "sha256sum": "ad19d35e0dfca6bb6c7bd066493d7f0a60634bcb5c28e35a151fb9129c3caf93"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "19.25.0.0.241015",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192400240716.zip",
                            "type": "grid",
                            "sha256sum": "3344cf3e526e7d88a78e2cd14cb67df658c5b594166fcddaa325bd73c7a109e4"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "19.24.0.0.240716",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192300240416.zip",
                            "type": "grid",
                            "sha256sum": "762a80c4e41c6d724d45c8a0ee67ebf312590a26f9c2a15615bd568f39bb14bd"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "19.23.0.0.240416",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23700250121.zip",
                            "type": "grid",
                            "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "23.7.0.0.250121",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23600241015.zip",
                            "type": "grid",
                            "sha256sum": "4f5e1623770974d4cda63c4b65cb7fbccdf212c639a30a897cb4a520737b413d"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "23.6.0.0.241015",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23500240716.zip",
                            "type": "grid",
                            "sha256sum": "4730ee31613e80bb3655afee932c0742fcaa5848469b4bffde981496cd94f705"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "23.5.0.0.240716",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23400240118.zip",
                            "type": "grid",
                            "sha256sum": "dcc3c44f478fe48d2c4900214a1e7f56f6c17f0aaec70c6c46dd7ef0e324f3b8"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "23.4.0.0.240118",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-192600250121.zip",
                            "type": "grid",
                            "sha256sum": "585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "19.26.0.0.250121",
                    "service": ["ATP"]
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-23700250121.zip",
                            "type": "grid",
                            "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "23.7.0.0.250121",
                    "service": ["ATP"]
                }
            ],
            "gendate": "2025-05-13 14:38:14.141075"
        }
        _add_incremental_inventory_json = {
            "grid-klones": [
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192700250415.zip",
                            "type": "grid",
                            "sha256sum": "fedd84c6b29e0b08fef5bc6820b11e093a9dd0425d3535a089e07c39516d7068"
                        }
                    ],
                    "xmeta": {
                        "default": True,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "latest": True
                    },
                    "version": "19.27.0.0.250415",
                    "service": [
                        "EXACS"
                    ]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23800250415.zip",
                            "type": "grid",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "latest": True
                    },
                    "version": "23.8.0.0.250415",
                    "service": [
                        "EXACS"
                    ]
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-192700250415.zip",
                            "type": "grid",
                            "sha256sum": "dc528c1d6ddf036ce260bd165e8b76b7abb9557afc23c64a690d3f545485abf1"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "latest": True
                    },
                    "version": "19.27.0.0.250415",
                    "service": [
                        "ATP"
                    ]
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-23800250415.zip",
                            "type": "grid",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "latest": True
                    },
                    "version": "23.8.0.0.250415",
                    "service": [
                        "ATP"
                    ]
                }
            ],
            "gendate": "2025-06-25 10:21:18.746354"
        }
        gi_add_payload = {
            "system_type": "EXACS",
            "image_type": "RELEASE",
            "type": "ADD",
            "version" : None,
            "location":
                {
                    "type": "local_tar",
                    "source": "",
                    "sha256sum": "c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982",
                }
        }
        _result_inventory_json = {
            "gendate": "2025-07-23 06:38:27",
            "grid-klones": [
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-23800250415.zip",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c",
                            "type": "grid",
                        }
                    ],
                    "service": ["ATP"],
                    "version": "23.8.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-192700250415.zip",
                            "sha256sum": "dc528c1d6ddf036ce260bd165e8b76b7abb9557afc23c64a690d3f545485abf1",
                            "type": "grid",
                        }
                    ],
                    "service": ["ATP"],
                    "version": "19.27.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23800250415.zip",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.8.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192700250415.zip",
                            "sha256sum": "fedd84c6b29e0b08fef5bc6820b11e093a9dd0425d3535a089e07c39516d7068",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.27.0.0.250415",
                    "xmeta": {
                        "default": True,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192600250121.zip",
                            "sha256sum": "104cca2e83085c53fedbc5bb8bf10444d4f1e7a4c420d4e7be0414bc231bff0c",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.26.0.0.250121",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192500241015.zip",
                            "sha256sum": "ad19d35e0dfca6bb6c7bd066493d7f0a60634bcb5c28e35a151fb9129c3caf93",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.25.0.0.241015",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192400240716.zip",
                            "sha256sum": "3344cf3e526e7d88a78e2cd14cb67df658c5b594166fcddaa325bd73c7a109e4",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.24.0.0.240716",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23700250121.zip",
                            "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.7.0.0.250121",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23600241015.zip",
                            "sha256sum": "4f5e1623770974d4cda63c4b65cb7fbccdf212c639a30a897cb4a520737b413d",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.6.0.0.241015",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23500240716.zip",
                            "sha256sum": "4730ee31613e80bb3655afee932c0742fcaa5848469b4bffde981496cd94f705",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.5.0.0.240716",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
            ],
        }

        # add inventory.json file
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(_inventory_json, file)
            
        # create incremental bundle
        incremental_image_repo = tempfile.mkdtemp(prefix='incrementalbundle')
        exacs_dir  = os.path.join(incremental_image_repo, 'EXACS')
        os.makedirs(exacs_dir)
        adbd_dir = os.path.join(incremental_image_repo, 'ADBD')
        os.makedirs(adbd_dir)
        _add_incremental_inventory_json_path = os.path.join(incremental_image_repo, 'inventory.json')
        with open(_add_incremental_inventory_json_path, "w") as file:
            json.dump(_add_incremental_inventory_json, file)
        _image_file1 = os.path.join(exacs_dir, "grid-klone-Linux-x86-64-192700250415.zip")
        open(_image_file1, "w").close()
        _image_file2 = os.path.join(exacs_dir, "grid-klone-Linux-x86-64-23800250415.zip")
        open(_image_file2, "w").close()
        _image_file1_adbd = os.path.join(adbd_dir, "grid-klone-Linux-x86-64-192700250415.zip")
        open(_image_file1_adbd, "w").close()
        _image_file2_adbd = os.path.join(adbd_dir, "grid-klone-Linux-x86-64-23800250415.zip")
        open(_image_file2_adbd, "w").close()
        
        gi_add_payload['location']['source'] = incremental_image_repo
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self.latest_dir
        writableGConfigOptions["gi_multi_image_count"] = 4
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data['grid-klones'], _result_inventory_json['grid-klones'])
        # remove the added image from repo for next test case
        os.remove(f'{self.exacs_dir}/grid-klone-Linux-x86-64-192700250415.zip')
        os.remove(f'{self.exacs_dir}/grid-klone-Linux-x86-64-23800250415.zip')
        os.remove(f'{self.adbd_dir}/grid-klone-Linux-x86-64-192700250415.zip')
        os.remove(f'{self.adbd_dir}/grid-klone-Linux-x86-64-23800250415.zip')
    
    
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982")
    def test_incremental_bundle_flow_image_count1(self, mMockSha256):
        """Test image addition flow
        """
        _inventory_json = grid_data = {
            "grid-klones": [
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192600250121.zip",
                            "type": "grid",
                            "sha256sum": "104cca2e83085c53fedbc5bb8bf10444d4f1e7a4c420d4e7be0414bc231bff0c"
                        }
                    ],
                    "xmeta": {
                        "default": True,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "19.26.0.0.250121",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192500241015.zip",
                            "type": "grid",
                            "sha256sum": "ad19d35e0dfca6bb6c7bd066493d7f0a60634bcb5c28e35a151fb9129c3caf93"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "19.25.0.0.241015",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192400240716.zip",
                            "type": "grid",
                            "sha256sum": "3344cf3e526e7d88a78e2cd14cb67df658c5b594166fcddaa325bd73c7a109e4"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "19.24.0.0.240716",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192300240416.zip",
                            "type": "grid",
                            "sha256sum": "762a80c4e41c6d724d45c8a0ee67ebf312590a26f9c2a15615bd568f39bb14bd"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "19.23.0.0.240416",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23700250121.zip",
                            "type": "grid",
                            "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "23.7.0.0.250121",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23600241015.zip",
                            "type": "grid",
                            "sha256sum": "4f5e1623770974d4cda63c4b65cb7fbccdf212c639a30a897cb4a520737b413d"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "23.6.0.0.241015",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23500240716.zip",
                            "type": "grid",
                            "sha256sum": "4730ee31613e80bb3655afee932c0742fcaa5848469b4bffde981496cd94f705"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "23.5.0.0.240716",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23400240118.zip",
                            "type": "grid",
                            "sha256sum": "dcc3c44f478fe48d2c4900214a1e7f56f6c17f0aaec70c6c46dd7ef0e324f3b8"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "23.4.0.0.240118",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-192600250121.zip",
                            "type": "grid",
                            "sha256sum": "585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "19.26.0.0.250121",
                    "service": ["ATP"]
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-23700250121.zip",
                            "type": "grid",
                            "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "23.7.0.0.250121",
                    "service": ["ATP"]
                }
            ],
            "gendate": "2025-05-13 14:38:14.141075"
        }
        _add_incremental_inventory_json = {
            "grid-klones": [
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192700250415.zip",
                            "type": "grid",
                            "sha256sum": "fedd84c6b29e0b08fef5bc6820b11e093a9dd0425d3535a089e07c39516d7068"
                        }
                    ],
                    "xmeta": {
                        "default": True,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "latest": True
                    },
                    "version": "19.27.0.0.250415",
                    "service": [
                        "EXACS"
                    ]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23800250415.zip",
                            "type": "grid",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "latest": True
                    },
                    "version": "23.8.0.0.250415",
                    "service": [
                        "EXACS"
                    ]
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-192700250415.zip",
                            "type": "grid",
                            "sha256sum": "dc528c1d6ddf036ce260bd165e8b76b7abb9557afc23c64a690d3f545485abf1"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "latest": True
                    },
                    "version": "19.27.0.0.250415",
                    "service": [
                        "ATP"
                    ]
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-23800250415.zip",
                            "type": "grid",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": [
                            "190",
                            "181",
                            "122",
                            "121",
                            "112"
                        ],
                        "latest": True
                    },
                    "version": "23.8.0.0.250415",
                    "service": [
                        "ATP"
                    ]
                }
            ],
            "gendate": "2025-06-25 10:21:18.746354"
        }
        gi_add_payload = {
            "system_type": "EXACS",
            "image_type": "RELEASE",
            "type": "ADD",
            "version" : None,
            "location":
                {
                    "type": "local_tar",
                    "source": "",
                    "sha256sum": "c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982",
                }
        }
        _result_inventory_json = {
            "gendate": "2025-07-23 06:38:27",
            "grid-klones": [
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-23800250415.zip",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c",
                            "type": "grid",
                        }
                    ],
                    "service": ["ATP"],
                    "version": "23.8.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-192700250415.zip",
                            "sha256sum": "dc528c1d6ddf036ce260bd165e8b76b7abb9557afc23c64a690d3f545485abf1",
                            "type": "grid",
                        }
                    ],
                    "service": ["ATP"],
                    "version": "19.27.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23800250415.zip",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.8.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192700250415.zip",
                            "sha256sum": "fedd84c6b29e0b08fef5bc6820b11e093a9dd0425d3535a089e07c39516d7068",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.27.0.0.250415",
                    "xmeta": {
                        "default": True,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
            ],
        }

        # add inventory.json file
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(_inventory_json, file)
            
        # create incremental bundle
        incremental_image_repo = tempfile.mkdtemp(prefix='incrementalbundle')
        exacs_dir  = os.path.join(incremental_image_repo, 'EXACS')
        os.makedirs(exacs_dir)
        adbd_dir = os.path.join(incremental_image_repo, 'ADBD')
        os.makedirs(adbd_dir)
        _add_incremental_inventory_json_path = os.path.join(incremental_image_repo, 'inventory.json')
        with open(_add_incremental_inventory_json_path, "w") as file:
            json.dump(_add_incremental_inventory_json, file)
        _image_file1 = os.path.join(exacs_dir, "grid-klone-Linux-x86-64-192700250415.zip")
        open(_image_file1, "w").close()
        _image_file2 = os.path.join(exacs_dir, "grid-klone-Linux-x86-64-23800250415.zip")
        open(_image_file2, "w").close()
        _image_file1_adbd = os.path.join(adbd_dir, "grid-klone-Linux-x86-64-192700250415.zip")
        open(_image_file1_adbd, "w").close()
        _image_file2_adbd = os.path.join(adbd_dir, "grid-klone-Linux-x86-64-23800250415.zip")
        open(_image_file2_adbd, "w").close()
        
        gi_add_payload['location']['source'] = incremental_image_repo
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self.latest_dir
        writableGConfigOptions["gi_multi_image_count"] = 1
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data['grid-klones'], _result_inventory_json['grid-klones'])
        # remove the added image from repo for next test case
        os.remove(f'{self.exacs_dir}/grid-klone-Linux-x86-64-192700250415.zip')
        os.remove(f'{self.exacs_dir}/grid-klone-Linux-x86-64-23800250415.zip')
        os.remove(f'{self.adbd_dir}/grid-klone-Linux-x86-64-192700250415.zip')
        os.remove(f'{self.adbd_dir}/grid-klone-Linux-x86-64-23800250415.zip')
        
        
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982")
    @mock.patch("exabox.ovm.clugiconfigimage.mDownloadFromBucket")
    def test_add_image_OSS_tar(self, mDownloadFromBucket, mMockSha256):
        """Test image addition flow
        """
        _inventory_json = {
                        "gendate" : "2023-07-26 22:03:16.930889",
                        "grid-klones" : [        {
                        "files" : [
                            {
                                "path" : "EXACS/grid-klone-Linux-x86-64-191900230418.zip",
                                "sha256sum" : "c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982",
                                "type" : "grid"
                            }
                        ],
                        "service" : [
                            "EXACS"
                        ],
                        "version" : "19.19.0.0.230418",
                        "xmeta" : {
                            "default" : True,
                            "imgtype" : "RELEASE",
                            "latest" : True,
                            "ol7_required" : True,
                            "supported_db" : [
                                "190",
                                "181",
                                "122",
                                "121",
                                "112"
                            ]
                        }
                    }
                ]
            }
        _add_incremental_inventory_json = {
                        "gendate" : "2023-07-26 22:03:16.930889",
                        "grid-klones" : [        {
                        "files" : [
                            {
                                "path" : "EXACS/grid-klone-Linux-x86-64-192000230418.zip",
                                "sha256sum" : "c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982",
                                "type" : "grid"
                            }
                        ],
                        "service" : [
                            "EXACS"
                        ],
                        "version" : "19.20.0.0.230418",
                        "xmeta" : {
                            "default" : True,
                            "imgtype" : "RELEASE",
                            "latest" : True,
                            "ol7_required" : True,
                            "supported_db" : [
                                "190",
                                "181",
                                "122",
                                "121",
                                "112"
                            ]
                        }
                    }
                ]
            }
        gi_add_payload = {
            "system_type": "EXACS",
            "image_type": "RELEASE",
            "type": "ADD",
            "version" : "19.20.0.0.230418",
            "location":
            {
                "type": "objectstore_tar",
                "filename": "dbaas_patch/atp/giimages/1926/g34062/gi1926_g34062_250114_patch.zip",
                "namespace": "dbaasexadatacustomersea1",
                "bucket": "atppatch",
                "sha256sum": "c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982",
            }
        }
        # add inventory.json file
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(_inventory_json, file)
            
        # create incremental bundle
        incremental_image_repo = tempfile.mkdtemp(prefix='incrementalbundle')
        exacs_dir  = os.path.join(incremental_image_repo, 'EXACS')
        os.makedirs(exacs_dir)
        adbd_dir = os.path.join(incremental_image_repo, 'ADBD')
        os.makedirs(adbd_dir)
        _add_incremental_inventory_json_path = os.path.join(incremental_image_repo, 'inventory.json')
        with open(_add_incremental_inventory_json_path, "w") as file:
            json.dump(_add_incremental_inventory_json, file)
        _image_file1 = os.path.join(exacs_dir, "grid-klone-Linux-x86-64-192000230418.zip")
        open(_image_file1, "w").close()
        mDownloadFromBucket.return_value = incremental_image_repo
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self.latest_dir
        writableGConfigOptions["gi_multi_image_count"] = 4
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data['grid-klones'][0]['version'], gi_add_payload['version'])
        self.assertEqual(modified_data['grid-klones'][0]['files'][0]['path'], 'EXACS/grid-klone-Linux-x86-64-192000230418.zip')
        # remove the added image from repo for next test case
        _added_image = os.path.join(self.exacs_dir, "grid-klone-Linux-x86-64-192000230418.zip")
        os.remove(_added_image)
        
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982")
    def test_add_image_failure(self, mMockSha256):
        """Test image addition fail flow
        """
        _add_inventory_json = {
                        "gendate" : "2023-07-26 22:03:16.930889",
                        "grid-klones" : [        {
                        "files" : [
                            {
                                "path" : "EXACS/grid-klone-Linux-x86-64-191900230418.zip",
                                "sha256sum" : "c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982",
                                "type" : "grid"
                            }
                        ],
                        "service" : [
                            "EXACS"
                        ],
                        "version" : "19.19.0.0.230418",
                        "xmeta" : {
                            "default" : True,
                            "imgtype" : "RELEASE",
                            "latest" : True,
                            "ol7_required" : True,
                            "supported_db" : [
                                "190",
                                "181",
                                "122",
                                "121",
                                "112"
                            ]
                        }
                    }
                ]
            }
        _add_incremental_inventory_json = {
                        "gendate" : "2023-07-26 22:03:16.930889",
                        "grid-klones" : [        {
                        "files" : [
                            {
                                "path" : "EXACS/grid-klone-Linux-x86-64-192000230418.zip",
                                "sha256sum" : "c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982",
                                "type" : "grid"
                            }
                        ],
                        "service" : [
                            "EXACS"
                        ],
                        "version" : "19.20.0.0.230418",
                        "xmeta" : {
                            "default" : True,
                            "imgtype" : "RELEASE",
                            "latest" : True,
                            "ol7_required" : True,
                            "supported_db" : [
                                "190",
                                "181",
                                "122",
                                "121",
                                "112"
                            ]
                        }
                    }
                ]
            }
        gi_add_payload = {
            "system_type": "EXACS",
            "image_type": "RELEASE",
            "type": "ADD",
            "version" : "19.20.0.0.230418",
            "location":
            {
                "type": "local_tar",
                "source": "",
                "sha256sum": "c5aaffbcb7209eedd986e49eeb5c4f5d01448510c23cfb6e846ede6ea8572982",
            }
        }
        # add inventory.json file
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(_add_inventory_json, file)
            
        # create incremental bundle
        incremental_image_repo = tempfile.mkdtemp(prefix='incrementalbundle')
        exacs_dir  = os.path.join(incremental_image_repo, 'EXACS')
        os.makedirs(exacs_dir)
        adbd_dir = os.path.join(incremental_image_repo, 'ADBD')
        os.makedirs(adbd_dir)
        _add_incremental_inventory_json_path = os.path.join(incremental_image_repo, 'inventory.json')
        with open(_add_incremental_inventory_json_path, "w") as file:
            json.dump(_add_incremental_inventory_json, file)
        gi_add_payload['location']['source'] = incremental_image_repo
        cluCtrl_obj = exaBoxCluCtrl(get_gcontext())
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _gi_image_config_obj.current_repo_path = f'{self.latest_dir}'
        _gi_image_config_obj.inventory_json_path = _inventory_json_path
        with self.assertRaises(ExacloudRuntimeError) as context:
            _rc = _gi_image_config_obj.mExecute(gi_add_payload)
            self.assertEqual(_rc, 1)  
            
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340")
    def test_add_image_from_local_filesystem(self, mMockSha256):
        """Test add single image file from local file system
        """
        _add_inventory_json = {
                        "gendate": "2023-07-26 22:03:16.930889",
                        "grid-klones": [
                            {
                                "files": [
                                    {
                                        "path": "EXACS/grid-klone-Linux-x86-64-191900230418.zip",
                                        "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340",
                                        "type": "grid"
                                    }
                                ],
                                "service": ["EXACS"],
                                "version": "19.19.0.0.230418",
                                "xmeta": {
                                    "default": True,
                                    "imgtype": "RELEASE",
                                    "latest": True,
                                    "ol7_required": True,
                                    "supported_db": ["190", "181", "122", "121", "112"]
                                }
                            }
                        ]
                    }
                    
        gi_add_payload = {
            "system_type": "EXACS",
            "image_type": "RELEASE",
            "type": "ADD",
            "version": "19.22.0.0.240116",
            "xmeta": {
                "latest": True,
                "default": True
            },
            "location": {
                "type": "local_image",
                "filename": "grid-klone-Linux-x86-64-192200240116.zip",
                "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340",
                "source": ""
            }
        }

        # add inventory.json file
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(_add_inventory_json, file)
            
        _image_file1 = os.path.join(self.exacs_dir, "grid-klone-Linux-x86-64-191900230418.zip")
        open(_image_file1, "w").close()
        
        _image_file2 = os.path.join(self.image_repo, "grid-klone-Linux-x86-64-192200240116.zip")
        open(_image_file2, "w").close()
        gi_add_payload['location']['source'] = _image_file2
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self.latest_dir
        writableGConfigOptions["gi_multi_image_count"] = 4
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data['grid-klones'][0]['version'], gi_add_payload['version'])
        # inventory should have 2 entries
        self.assertEqual(len(modified_data), 2)
        # remove the added image from repo for next test case
        os.remove(_image_file1)
        _added_image = os.path.join(self.exacs_dir, "grid-klone-Linux-x86-64-192200240116.zip")
        os.remove(_added_image)
        
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2")
    @mock.patch("exabox.ovm.clugiconfigimage.mDownloadFromBucket")
    def test_add_image_from_OSS_adbd(self, mDownloadFromBucket, mMockSha256):
        """Test add single image file from OSS file system """
        _add_inventory_json = {
            "grid-klones": [
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-192700250415.zip",
                        "type": "grid",
                        "sha256sum": "fedd84c6b29e0b08fef5bc6820b11e093a9dd0425d3535a089e07c39516d7068"
                    }
                ],
                "xmeta": {
                    "default": True,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": True
                },
                "version": "19.27.0.0.250415",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-192600250121.zip",
                        "type": "grid",
                        "sha256sum": "104cca2e83085c53fedbc5bb8bf10444d4f1e7a4c420d4e7be0414bc231bff0c"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "19.26.0.0.250121",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-192500241015.zip",
                        "type": "grid",
                        "sha256sum": "ad19d35e0dfca6bb6c7bd066493d7f0a60634bcb5c28e35a151fb9129c3caf93"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "19.25.0.0.241015",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-192400240716.zip",
                        "type": "grid",
                        "sha256sum": "3344cf3e526e7d88a78e2cd14cb67df658c5b594166fcddaa325bd73c7a109e4"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "19.24.0.0.240716",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-23800250415.zip",
                        "type": "grid",
                        "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": True
                },
                "version": "23.8.0.0.250415",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-23700250121.zip",
                        "type": "grid",
                        "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "23.7.0.0.250121",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-23600241015.zip",
                        "type": "grid",
                        "sha256sum": "4f5e1623770974d4cda63c4b65cb7fbccdf212c639a30a897cb4a520737b413d"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "23.6.0.0.241015",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-23500240716.zip",
                        "type": "grid",
                        "sha256sum": "4730ee31613e80bb3655afee932c0742fcaa5848469b4bffde981496cd94f705"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "23.5.0.0.240716",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "ADBD/grid-klone-Linux-x86-64-192700250415.zip",
                        "type": "grid",
                        "sha256sum": "fedd84c6b29e0b08fef5bc6820b11e093a9dd0425d3535a089e07c39516d7068"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": True
                },
                "version": "19.27.0.0.250415",
                "service": [
                    "ATP"
                ]
            },
            {
                "files": [
                    {
                        "path": "ADBD/grid-klone-Linux-x86-64-23800250415.zip",
                        "type": "grid",
                        "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": True
                },
                "version": "23.8.0.0.250415",
                "service": [
                    "ATP"
                ]
            }
        ],
        "gendate": "2025-05-12 03:46:08.861541"
    }
                    
        gi_add_payload = {
                "system_type": "ADBD",
                "image_type": "RELEASE",
                "type": "ADD",
                "version": "19.28.0.0.250114",
                "location": {
                    "type": "objectstore_image",
                    "filename": "dbaas_patch/atp/giimages/1928/g34062/gi1926_g34062_250114_patch.zip",
                    "namespace": "dbaasexadatacustomersea1",
                    "bucket": "atppatch",
                    "sha256sum": "585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2"
                },
                "xmeta": {
                    "latest": True,
                    "default": False
                },
                "requestId": "f47253ff-81bd-4d42-941f-00a6b5942961",
                "ecra": {
                    "whitelist_cidr": [
                        "10.0.1.0/28",
                        "10.0.1.32/28",
                        "10.0.1.112/28"
                    ]
                }
            }
        
        _result_inventory_json = {
            "gendate": "2025-07-24 07:49:51",
            "grid-klones": [
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-192800250114.zip",
                            "sha256sum": "585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2",
                            "type": "grid",
                        }
                    ],
                    "service": ["ATP"],
                    "version": "19.28.0.0.250114",
                    "xmeta": {
                        "default": True,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192700250415.zip",
                            "sha256sum": "fedd84c6b29e0b08fef5bc6820b11e093a9dd0425d3535a089e07c39516d7068",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.27.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192600250121.zip",
                            "sha256sum": "104cca2e83085c53fedbc5bb8bf10444d4f1e7a4c420d4e7be0414bc231bff0c",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.26.0.0.250121",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192500241015.zip",
                            "sha256sum": "ad19d35e0dfca6bb6c7bd066493d7f0a60634bcb5c28e35a151fb9129c3caf93",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.25.0.0.241015",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192400240716.zip",
                            "sha256sum": "3344cf3e526e7d88a78e2cd14cb67df658c5b594166fcddaa325bd73c7a109e4",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.24.0.0.240716",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23800250415.zip",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.8.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23700250121.zip",
                            "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.7.0.0.250121",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23600241015.zip",
                            "sha256sum": "4f5e1623770974d4cda63c4b65cb7fbccdf212c639a30a897cb4a520737b413d",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.6.0.0.241015",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23500240716.zip",
                            "sha256sum": "4730ee31613e80bb3655afee932c0742fcaa5848469b4bffde981496cd94f705",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.5.0.0.240716",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-23800250415.zip",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c",
                            "type": "grid",
                        }
                    ],
                    "service": ["ATP"],
                    "version": "23.8.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
            ],
        }

        # add inventory.json file
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(_add_inventory_json, file)
            
        _image_file1 = os.path.join(self.exacs_dir, "grid-klone-Linux-x86-64-191900230418.zip")
        open(_image_file1, "w").close()
        
        _new_image = os.path.join(self.latest_dir, "gi1928_g34062_250114_patch.zip")
        open(_new_image, "w").close()
        mDownloadFromBucket.return_value = _new_image
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self.latest_dir
        writableGConfigOptions["gi_multi_image_count"] = 4
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        cluCtrl_obj.mSetIsATP(True) 
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data['grid-klones'][0]['files'][0]['path'], 'ADBD/grid-klone-Linux-x86-64-192800250114.zip')
        self.assertEqual(modified_data['grid-klones'][0]['version'], gi_add_payload['version'])
        self.assertEqual(modified_data['grid-klones'][0]['xmeta']["latest"], gi_add_payload['xmeta']["latest"])
        self.assertEqual(modified_data['grid-klones'][0]['xmeta']["default"], gi_add_payload['xmeta']["default"])
        cluCtrl_obj.mLoadRepoInventory()
        _default_version = cluCtrl_obj.mGetVersionGiMultiImages()
        self.assertEqual(_default_version, gi_add_payload['version'])
        # inventory should have 2 entries
        self.assertEqual(len(modified_data['grid-klones']), len(_add_inventory_json['grid-klones']))
        # remove the added image from repo for next test case
        os.remove(_image_file1)
        _added_image = os.path.join(self.adbd_dir, "grid-klone-Linux-x86-64-192800250114.zip")
        os.remove(_added_image)
        
        
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2")
    @mock.patch("exabox.ovm.clugiconfigimage.mDownloadFromBucket")
    def test_add_image_from_OSS_adbd_wrong_entry(self, mDownloadFromBucket, mMockSha256):
        """Test add single image file from OSS file system """
        _add_inventory_json = {
            "grid-klones": [
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-192700250415.zip",
                        "type": "grid",
                        "sha256sum": "fedd84c6b29e0b08fef5bc6820b11e093a9dd0425d3535a089e07c39516d7068"
                    }
                ],
                "xmeta": {
                    "default": True,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": True
                },
                "version": "19.27.0.0.250415",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-192600250121.zip",
                        "type": "grid",
                        "sha256sum": "104cca2e83085c53fedbc5bb8bf10444d4f1e7a4c420d4e7be0414bc231bff0c"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "19.26.0.0.250121",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-192500241015.zip",
                        "type": "grid",
                        "sha256sum": "ad19d35e0dfca6bb6c7bd066493d7f0a60634bcb5c28e35a151fb9129c3caf93"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "19.25.0.0.241015",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-192400240716.zip",
                        "type": "grid",
                        "sha256sum": "3344cf3e526e7d88a78e2cd14cb67df658c5b594166fcddaa325bd73c7a109e4"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "19.24.0.0.240716",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-23800250415.zip",
                        "type": "grid",
                        "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": True
                },
                "version": "23.8.0.0.250415",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-23700250121.zip",
                        "type": "grid",
                        "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "23.7.0.0.250121",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-23600241015.zip",
                        "type": "grid",
                        "sha256sum": "4f5e1623770974d4cda63c4b65cb7fbccdf212c639a30a897cb4a520737b413d"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "23.6.0.0.241015",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "EXACS/grid-klone-Linux-x86-64-23500240716.zip",
                        "type": "grid",
                        "sha256sum": "4730ee31613e80bb3655afee932c0742fcaa5848469b4bffde981496cd94f705"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": False
                },
                "version": "23.5.0.0.240716",
                "service": [
                    "EXACS"
                ]
            },
            {
                "files": [
                    {
                        "path": "ADBD/grid-klone-Linux-x86-64-192700250415.zip",
                        "type": "grid",
                        "sha256sum": "fedd84c6b29e0b08fef5bc6820b11e093a9dd0425d3535a089e07c39516d7068"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": True
                },
                "version": "19.27.0.0.250415",
                "service": [
                    "ATP"
                ]
            },
            {
                "files": [
                    {
                        "path": "ADBD/grid-klone-Linux-x86-64-23800250415.zip",
                        "type": "grid",
                        "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c"
                    }
                ],
                "xmeta": {
                    "default": False,
                    "ol7_required": True,
                    "imgtype": "RELEASE",
                    "supported_db": [
                        "190",
                        "181",
                        "122",
                        "121",
                        "112"
                    ],
                    "latest": True
                },
                "version": "23.8.0.0.250415",
                "service": [
                    "ATP"
                ]
            }
        ],
        "gendate": "2025-05-12 03:46:08.861541"
    }
                    
        gi_add_payload = {
                "system_type": "ADBD",
                "image_type": "RELEASE",
                "type": "ADD",
                "version": "19.28.0.0.250115",
                "location": {
                    "type": "objectstore_image",
                    "filename": "dbaas_patch/atp/giimages/1928/g34062/gi1928_g34062_250115_patch.zip",
                    "namespace": "dbaasexadatacustomersea1",
                    "bucket": "atppatch",
                    "sha256sum": "585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2"
                },
                "xmeta": {
                    "latest": False,
                    "default": False
                },
                "requestId": "f47253ff-81bd-4d42-941f-00a6b5942961",
                "ecra": {
                    "whitelist_cidr": [
                        "10.0.1.0/28",
                        "10.0.1.32/28",
                        "10.0.1.112/28"
                    ]
                }
            }
        
        _result_inventory_json = {
            "gendate": "2025-07-24 07:49:51",
            "grid-klones": [
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-192800250115.zip",
                            "sha256sum": "585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2",
                            "type": "grid",
                        }
                    ],
                    "service": ["ATP"],
                    "version": "19.28.0.0.250115",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192700250415.zip",
                            "sha256sum": "fedd84c6b29e0b08fef5bc6820b11e093a9dd0425d3535a089e07c39516d7068",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.27.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192600250121.zip",
                            "sha256sum": "104cca2e83085c53fedbc5bb8bf10444d4f1e7a4c420d4e7be0414bc231bff0c",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.26.0.0.250121",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192500241015.zip",
                            "sha256sum": "ad19d35e0dfca6bb6c7bd066493d7f0a60634bcb5c28e35a151fb9129c3caf93",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.25.0.0.241015",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192400240716.zip",
                            "sha256sum": "3344cf3e526e7d88a78e2cd14cb67df658c5b594166fcddaa325bd73c7a109e4",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "19.24.0.0.240716",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23800250415.zip",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.8.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23700250121.zip",
                            "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.7.0.0.250121",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23600241015.zip",
                            "sha256sum": "4f5e1623770974d4cda63c4b65cb7fbccdf212c639a30a897cb4a520737b413d",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.6.0.0.241015",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23500240716.zip",
                            "sha256sum": "4730ee31613e80bb3655afee932c0742fcaa5848469b4bffde981496cd94f705",
                            "type": "grid",
                        }
                    ],
                    "service": ["EXACS"],
                    "version": "23.5.0.0.240716",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": False,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-23800250415.zip",
                            "sha256sum": "4e4a85f1caabf30842dac955721c61705a14cb769b7d5b3a66a6f53c2e6e466c",
                            "type": "grid",
                        }
                    ],
                    "service": ["ATP"],
                    "version": "23.8.0.0.250415",
                    "xmeta": {
                        "default": False,
                        "imgtype": "RELEASE",
                        "latest": True,
                        "ol7_required": True,
                        "supported_db": ["190", "181", "122", "121", "112"],
                    },
                },
            ],
        }

        # add inventory.json file
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(_add_inventory_json, file)
            
        _image_file1 = os.path.join(self.exacs_dir, "grid-klone-Linux-x86-64-191900230418.zip")
        open(_image_file1, "w").close()
        
        _new_image = os.path.join(self.latest_dir, "gi1928_g34062_250114_patch.zip")
        open(_new_image, "w").close()
        mDownloadFromBucket.return_value = _new_image
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self.latest_dir
        writableGConfigOptions["gi_multi_image_count"] = 4
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        cluCtrl_obj.mSetIsATP(True) 
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data['grid-klones'][0]['files'][0]['path'], 'ADBD/grid-klone-Linux-x86-64-192800250115.zip')
        self.assertEqual(modified_data['grid-klones'][0]['version'], gi_add_payload['version'])
        self.assertEqual(modified_data['grid-klones'][0]['xmeta']["latest"], True)
        self.assertEqual(modified_data['grid-klones'][0]['xmeta']["default"], False)
        #cluCtrl_obj.mLoadRepoInventory()
        cluCtrl_obj.mImageSeparationInit(None)
        _default_version = cluCtrl_obj.mGetVersionGiMultiImages()
        self.assertEqual(_default_version, gi_add_payload['version'])
        # inventory should have 2 entries
        self.assertEqual(len(modified_data['grid-klones']), len(_add_inventory_json['grid-klones']))
        # remove the added image from repo for next test case
        os.remove(_image_file1)
        _added_image = os.path.join(self.adbd_dir, "grid-klone-Linux-x86-64-192800250115.zip")
        os.remove(_added_image)
        
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340")  
    def test_add_new_image_and_remove_old_from_inventory(self, mMockSha256):
        """Test adding a new image and removing the oldest image from the inventory.json  
        """  
        _add_inventory_json = {  
            "gendate": "2023-07-26 22:03:16.930889",  
            "grid-klones": [  
                {  
                    "files": [  
                        {"path": "EXACS/grid-klone-Linux-x86-64-191800230418.zip", "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340", "type": "grid"}  
                    ],  
                    "service": ["EXACS"],  
                    "version": "19.18.0.0.230418",  
                    "xmeta": {"default": True, "imgtype": "RELEASE", "latest": False, "ol7_required": True, "supported_db": ["190", "181", "122", "121", "112"]}  
                },  
                {  
                    "files": [  
                        {"path": "EXACS/grid-klone-Linux-x86-64-191900230418.zip", "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340", "type": "grid"}  
                    ],  
                    "service": ["EXACS"],  
                    "version": "19.19.0.0.230418",  
                    "xmeta": {"default": True, "imgtype": "RELEASE", "latest": False, "ol7_required": True, "supported_db": ["190", "181", "122", "121", "112"]}  
                },  
                {  
                    "files": [  
                        {"path": "EXACS/grid-klone-Linux-x86-64-192000230418.zip", "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340", "type": "grid"}  
                    ],  
                    "service": ["EXACS"],  
                    "version": "19.20.0.0.230418",  
                    "xmeta": {"default": True, "imgtype": "RELEASE", "latest": False, "ol7_required": True, "supported_db": ["190", "181", "122", "121", "112"]}  
                },  
                {  
                    "files": [  
                        {"path": "EXACS/grid-klone-Linux-x86-64-192100230418.zip", "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340", "type": "grid"}  
                    ],  
                    "service": ["EXACS"],  
                    "version": "19.21.0.0.230418",  
                    "xmeta": {"default": True, "imgtype": "RELEASE", "latest": True, "ol7_required": True, "supported_db": ["190", "181", "122", "121", "112"]}  
                }  
            ]  
        }  

        gi_add_payload = {  
            "system_type": "EXACS",  
            "image_type": "RELEASE",  
            "type": "ADD",  
            "version": "19.22.0.0.240116",
            "xmeta": {
                "latest": True,
                "default": True
            },
            "location": {  
                "type": "local_image",  
                "filename": "grid-klone-Linux-x86-64-192200240116.zip",  
                "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340",  
                "source": ""  
            }  
        }  

        # add inventory.json file  
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')  
        with open(_inventory_json_path, "w") as file:  
            json.dump(_add_inventory_json, file)  
            
        _image_file2 = os.path.join(self.image_repo, "grid-klone-Linux-x86-64-192200240116.zip")
        open(_image_file2, "w").close()
        gi_add_payload['location']['source'] = _image_file2
            
        gContext = self.mGetContext()  
        gConfigOptions = gContext.mGetConfigOptions()  
        writableGConfigOptions = copy.deepcopy(gConfigOptions)  
        writableGConfigOptions["repository_root"] = self.latest_dir  
        writableGConfigOptions["gi_multi_image_count"] = 4  
        gContext.mSetConfigOptions(writableGConfigOptions)  
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)  
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)  
        self.assertEqual(_rc, 0)  
        
        with open(_inventory_json_path, 'r') as json_file:  
            modified_data = json.load(json_file)  
        
        versions = [item['version'] for item in modified_data['grid-klones']]  
        self.assertIn("19.22.0.0.240116", versions)  
        self.assertNotIn("19.18.0.0.230418", versions)  
        self.assertEqual(len(versions), 4)
        _added_image = os.path.join(self.exacs_dir, "grid-klone-Linux-x86-64-192200240116.zip")
        os.remove(_added_image)

    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340")  
    def test_add_new_image_and_delete_old_image(self, mMockSha256):  
        """Test adding a new image and removing the oldest image in the repository  
        """  
        _add_inventory_json = {  
            "gendate": "2023-07-26 22:03:16.930889",  
            "grid-klones": [  
                {  
                    "files": [  
                        {"path": "EXACS/grid-klone-Linux-x86-64-191800230418.zip", "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340", "type": "grid"}  
                    ],  
                    "service": ["EXACS"],  
                    "version": "19.18.0.0.230418",  
                    "xmeta": {"default": True, "imgtype": "RELEASE", "latest": False, "ol7_required": True, "supported_db": ["190", "181", "122", "121", "112"]}  
                },  
                {  
                    "files": [  
                        {"path": "EXACS/grid-klone-Linux-x86-64-191900230418.zip", "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340", "type": "grid"}  
                    ],  
                    "service": ["EXACS"],  
                    "version": "19.19.0.0.230418",  
                    "xmeta": {"default": True, "imgtype": "RELEASE", "latest": False, "ol7_required": True, "supported_db": ["190", "181", "122", "121", "112"]}  
                },  
                {  
                    "files": [  
                        {"path": "EXACS/grid-klone-Linux-x86-64-192000230418.zip", "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340", "type": "grid"}  
                    ],  
                    "service": ["EXACS"],  
                    "version": "19.20.0.0.230418",  
                    "xmeta": {"default": True, "imgtype": "RELEASE", "latest": False, "ol7_required": True, "supported_db": ["190", "181", "122", "121", "112"]}  
                },  
                {  
                    "files": [  
                        {"path": "EXACS/grid-klone-Linux-x86-64-192100230418.zip", "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340", "type": "grid"}  
                    ],  
                    "service": ["EXACS"],  
                    "version": "19.21.0.0.230418",  
                    "xmeta": {"default": True, "imgtype": "RELEASE", "latest": True, "ol7_required": True, "supported_db": ["190", "181", "122", "121", "112"]}  
                }  
            ]  
        }  

        gi_add_payload = {  
            "system_type": "EXACS",  
            "image_type": "RELEASE",  
            "type": "ADD",  
            "version": "19.22.0.0.240116",
            "delete_old_image": "true",
            "xmeta": {
                "latest": True,
                "default": True
            },
            "location": {  
                "type": "local_image",  
                "filename": "grid-klone-Linux-x86-64-192200240116.zip",  
                "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340",  
                "source": ""  
            }  
        }  

        # add inventory.json file  
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')  
        with open(_inventory_json_path, "w") as file:  
            json.dump(_add_inventory_json, file)  
            
        _image_file1 = os.path.join(self.exacs_dir, "grid-klone-Linux-x86-64-191800230418.zip")
        open(_image_file1, "w").close()
            
        _image_file2 = os.path.join(self.image_repo, "grid-klone-Linux-x86-64-192200240116.zip")
        open(_image_file2, "w").close()
        gi_add_payload['location']['source'] = _image_file2
            
        gContext = self.mGetContext()  
        gConfigOptions = gContext.mGetConfigOptions()  
        writableGConfigOptions = copy.deepcopy(gConfigOptions)  
        writableGConfigOptions["repository_root"] = self.latest_dir  
        writableGConfigOptions["gi_multi_image_count"] = 4  
        gContext.mSetConfigOptions(writableGConfigOptions)  
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)  
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)  
        self.assertEqual(_rc, 0)  
        
        with open(_inventory_json_path, 'r') as json_file:  
            modified_data = json.load(json_file)  
        
        versions = [item['version'] for item in modified_data['grid-klones']]  
        self.assertIn("19.22.0.0.240116", versions)  
        self.assertNotIn("19.18.0.0.230418", versions)  
        self.assertEqual(len(versions), 4)
        self.assertEqual(os.path.exists(_image_file1), False)
        _added_image = os.path.join(self.exacs_dir, "grid-klone-Linux-x86-64-192200240116.zip")
        os.remove(_added_image)
        
    def test_add_image_invalid_sha256(self):
        """Test add single image file with invalid SHA-256 checksum
        """
        _add_inventory_json = {
                        "gendate": "2023-07-26 22:03:16.930889",
                        "grid-klones": [
                            {
                                "files": [
                                    {
                                        "path": "EXACS/grid-klone-Linux-x86-64-191900230418.zip",
                                        "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340",
                                        "type": "grid"
                                    }
                                ],
                                "service": ["EXACS"],
                                "version": "19.19.0.0.230418",
                                "xmeta": {
                                    "default": True,
                                    "imgtype": "RELEASE",
                                    "latest": True,
                                    "ol7_required": True,
                                    "supported_db": ["190", "181", "122", "121", "112"]
                                }
                            }
                        ]
                    }
                    
        gi_add_payload = {
            "system_type": "ADBD",
            "image_type": "RELEASE",
            "type": "ADD",
            "version": "19.22.0.0.240116",
            "xmeta": {
                "latest": True,
                "default": True
            },
            "location": {
                "type": "local_image",
                "filename": "grid-klone-Linux-x86-64-192200240116.zip",
                "sha256sum": "invalid_sha256sum",
                "source": ""
            }
        }

        # add inventory.json file
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(_add_inventory_json, file)
            
        _image_file2 = os.path.join(self.image_repo, "grid-klone-Linux-x86-64-192200240116.zip")
        open(_image_file2, "w").close()
        gi_add_payload['location']['source'] = _image_file2
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self.latest_dir
        writableGConfigOptions["gi_multi_image_count"] = 4
        gContext.mSetConfigOptions(writableGConfigOptions)
        
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        try: 
            _rc = _gi_image_config_obj.mExecute(gi_add_payload)  
        except ExacloudRuntimeError as e:
            pass
            #self.assertEqual('2066',str(e.mGetErrorCode()))
            #self.assertEqual('EXACLOUD : System version invalid for migration',str(e.mGetErrorMsg()))
            
    def test_mLoadRepoInventory_with_inventory(self):
        # add inventory.json file
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self.latest_dir
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        
        cluCtrl_obj.mLoadRepoInventory()
        
        
    def test_mManageDatabaseHomes(self):
        _inventory_json = {
            "grid-klones": [
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192600250121.zip",
                            "type": "grid",
                            "sha256sum": "104cca2e83085c53fedbc5bb8bf10444d4f1e7a4c420d4e7be0414bc231bff0c"
                        }
                    ],
                    "xmeta": {
                        "default": True,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "19.26.0.0.250121",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192500241015.zip",
                            "type": "grid",
                            "sha256sum": "ad19d35e0dfca6bb6c7bd066493d7f0a60634bcb5c28e35a151fb9129c3caf93"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "19.25.0.0.241015",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192400240716.zip",
                            "type": "grid",
                            "sha256sum": "3344cf3e526e7d88a78e2cd14cb67df658c5b594166fcddaa325bd73c7a109e4"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "19.24.0.0.240716",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-192300240416.zip",
                            "type": "grid",
                            "sha256sum": "762a80c4e41c6d724d45c8a0ee67ebf312590a26f9c2a15615bd568f39bb14bd"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "19.23.0.0.240416",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23700250121.zip",
                            "type": "grid",
                            "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "23.7.0.0.250121",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23600241015.zip",
                            "type": "grid",
                            "sha256sum": "4f5e1623770974d4cda63c4b65cb7fbccdf212c639a30a897cb4a520737b413d"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "23.6.0.0.241015",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23500240716.zip",
                            "type": "grid",
                            "sha256sum": "4730ee31613e80bb3655afee932c0742fcaa5848469b4bffde981496cd94f705"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "23.5.0.0.240716",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "EXACS/grid-klone-Linux-x86-64-23400240118.zip",
                            "type": "grid",
                            "sha256sum": "dcc3c44f478fe48d2c4900214a1e7f56f6c17f0aaec70c6c46dd7ef0e324f3b8"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": False
                    },
                    "version": "23.4.0.0.240118",
                    "service": ["EXACS"]
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-192600250121.zip",
                            "type": "grid",
                            "sha256sum": "585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "19.26.0.0.250121",
                    "service": ["ATP"]
                },
                {
                    "files": [
                        {
                            "path": "ADBD/grid-klone-Linux-x86-64-23700250121.zip",
                            "type": "grid",
                            "sha256sum": "2249b0619e86c08eec26b4bd6592497014e0866dfbf0c28b301773b72caf39b2"
                        }
                    ],
                    "xmeta": {
                        "default": False,
                        "ol7_required": True,
                        "imgtype": "RELEASE",
                        "supported_db": ["190", "181", "122", "121", "112"],
                        "latest": True
                    },
                    "version": "23.7.0.0.250121",
                    "service": ["ATP"]
                }
            ],
            "gendate": "2025-05-13 14:38:14.141075"
        }
        # add inventory.json file
        _inventory_json_path = os.path.join(self.latest_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(_inventory_json, file)
            
        _delete_node_payload = {
            "reshaped_node_subset": {
                "added_computes": [],
                "retained_computes": [
                    {
                        "compute_node_alias": "node-1",
                        "compute_node_hostname": "sin113089exdd001.oraclecloud.internal",
                    }
                ],
                "removed_computes": [
                    {
                        "compute_node_alias": "node-2",
                        "compute_node_hostname": "sin113089exdd002.oraclecloud.internal",
                        "compute_node_virtual_hostname": "tps9yarddb1b.planning.psa",
                    }
                ],
                "participating_computes": [
                    {
                        "compute_node_alias": "node-1",
                        "compute_node_hostname": "sin113089exdd001.oraclecloud.internal",
                    },
                    {
                        "compute_node_alias": "node-2",
                        "compute_node_hostname": "sin113089exdd002.oraclecloud.internal",
                    },
                ],
            }
        }

        
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self.latest_dir
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _options = copy.deepcopy(self.mGetClubox().mGetArgsOptions())
        _options.jsonconf = _delete_node_payload
        _cmds = {
            self.mGetRegexVm(): [
                [
                    exaMockCommand("/bin/cat /etc/oratab | /bin/grep '^+ASM.*' | /bin/cut -f 2 -d ':'", aStdout="/u01/app/19.0.0.0/grid"),
                    exaMockCommand("/u01/app/19.0.0.0/grid/bin/crsctl check crs", aStdout=None)
                ]
            ]
        }

        #Init new Args
        self.mPrepareMockCommands(_cmds)
        _ebox = self.mGetClubox()
        _ebox.mImageSeparationInit(False)
        _ebox.mSetCmd('elastic_info')
        _mGetOracleBaseDirectories_return_value_tuple = (
            '/u01/app/19.0.0.0/grid', 
            '19.21.0.0.0', 
            '/u01/app/grid'
        )
        with patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute'),\
            patch('exabox.ovm.cluelasticcompute.ebCluReshapeCompute.mGetSrcDomU', return_value="iad103716exddu1101.iad103716exd.adminiad1.oraclevcn.com"),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOracleBaseDirectories', return_value=_mGetOracleBaseDirectories_return_value_tuple),\
            patch('exabox.ovm.clucontrol.exaBoxCluCtrl.mGetOedaProperty', return_value = "33182392:GI_Bundle_Patch,33575975:OJVM,33142793:ACFS"):
            _ebox.mManageDatabaseHomes(_options)
            
        

class ebTestCluGiConfigImageOldRepo(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestCluGiConfigImageOldRepo, self).setUpClass(aGenerateDatabase = False)
        warnings.filterwarnings("ignore")
        self.image_repo = tempfile.mkdtemp(prefix='cleanmain_repo')
        self._repo_dir =  os.path.join(self.image_repo, 'OCT2024_241015')
        os.makedirs(self._repo_dir)
        self._grid_klones_dir  = os.path.join(self._repo_dir, 'grid-klones')
        os.makedirs(self._grid_klones_dir)
        self._grid_klones_exacs  = os.path.join(self._grid_klones_dir, 'OCT2024')
        os.makedirs(self._grid_klones_exacs)
        self._grid_klones_adbd  = os.path.join(self._grid_klones_dir, 'ATP_192500')
        os.makedirs(self._grid_klones_adbd)
    
    @classmethod
    def tearDownClass(self) -> None:
        shutil.rmtree(self._repo_dir)
        
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340")
    def test_single_add_image_from_local_filesystem_oct2024_19c(self, mMockSha256):
        """Test add single image file from local file system
        """
        gi_add_payload = {
            "system_type": "EXACS",
            "image_type": "RELEASE",
            "type": "ADD",
            "version": "19.26.0.0.241016",
            "delete_old_image": "True",
            "location": {
                "type": "local_image",
                "filename": "grid-klone-Linux-x86-64-19000241016.zip",
                "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340",
                "source": ""
            }
        }
        # add inventory.json file
        _inventory_json_path = os.path.join(self._repo_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(inventory_json_old_format, file)
            
        _image_file1 = os.path.join(self._grid_klones_exacs, "grid-klone-Linux-x86-64-19000241015.zip")
        open(_image_file1, "w").close()
        
        _image_file2 = os.path.join(self._grid_klones_exacs, "grid-klone-Linux-x86-64-23000241015.zip")
        open(_image_file2, "w").close()
        
        _new_image = os.path.join(self._repo_dir, "grid-klone-Linux-x86-64-19260241016.zip")
        open(_new_image, "w").close()
        gi_add_payload['location']['source'] = _new_image
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self._repo_dir
        writableGConfigOptions["gi_multi_image_count"] = 1
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data['grid-klones'][0]['version'], '19.0.0.0')
        self.assertEqual(modified_data['grid-klones'][0]['files'][0]['path'], 'OCT2024/grid-klone-Linux-x86-64-19000241016.zip')
        self.assertEqual(modified_data['grid-klones'][0]['files'][0]['sha256sum'], '55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340')
        self.assertEqual(modified_data['grid-klones'][0]['service'], [gi_add_payload['system_type']])
        # inventory should have 2 entries
        self.assertEqual(len(modified_data['grid-klones']), len(inventory_json_old_format['grid-klones']))
        self.assertFalse(os.path.exists(_image_file1))
        # remove the added image from repo for next test case
        # os.remove(_image_file1)
        # _added_image = os.path.join(self._grid_klones_exacs, "grid-klone-Linux-x86-64-19000240116.zip")
        # os.remove(_added_image)
        
        
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de341")
    def test_single_add_image_from_local_filesystem_oct2024_23c(self, mMockSha256):
        """Test add single image file from local file system
        """
        gi_add_payload = {
            "system_type": "EXACS",
            "image_type": "RELEASE",
            "type": "ADD",
            "version": "23.26.0.0.241016",
            "location": {
                "type": "local_image",
                "filename": "grid-klone-Linux-x86-64-23260241016.zip",
                "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de341",
                "source": ""
            }
        }
        # add inventory.json file
        _inventory_json_path = os.path.join(self._repo_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(inventory_json_old_format, file)
            
        _image_file1 = os.path.join(self._grid_klones_exacs, "grid-klone-Linux-x86-64-19000241015.zip")
        open(_image_file1, "w").close()
        
        _image_file2 = os.path.join(self._grid_klones_exacs, "grid-klone-Linux-x86-64-23000241015.zip")
        open(_image_file2, "w").close()
        
        _new_image = os.path.join(self._repo_dir, "grid-klone-Linux-x86-64-23260241016.zip")
        open(_new_image, "w").close()
        gi_add_payload['location']['source'] = _new_image
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self._repo_dir
        writableGConfigOptions["gi_multi_image_count"] = 1
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data['grid-klones'][0]['version'], '23.0.0.0')
        self.assertEqual(modified_data['grid-klones'][0]['files'][0]['path'], 'OCT2024/grid-klone-Linux-x86-64-23000241016.zip')
        self.assertEqual(modified_data['grid-klones'][0]['files'][0]['sha256sum'], '55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de341')
        self.assertEqual(len(modified_data['grid-klones']), len(inventory_json_old_format['grid-klones']))
        self.assertTrue(os.path.exists(_image_file1))
        # remove the added image from repo for next test case
        # os.remove(_image_file1)
        # _added_image = os.path.join(self._grid_klones_exacs, "grid-klone-Linux-x86-64-19000240116.zip")
        # os.remove(_added_image)
        
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340")
    def test_single_add_image_from_local_filesystem_atp(self, mMockSha256):
        """Test add single image file from local file system
        """
        gi_add_payload = {
            "system_type": "ADBD",
            "image_type": "RELEASE",
            "type": "ADD",
            "version": "19.0.0.0.241016",
            "location": {
                "type": "local_image",
                "filename": "grid-klone-Linux-x86-64-19000241016.zip",
                "sha256sum": "55c6a6bcee5751b503dfb494009b05d6acf5240c9e57b0664f0b1313dc4de340",
                "source": ""
            }
        }
        # add inventory.json file
        _inventory_json_path = os.path.join(self._repo_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(inventory_json_old_format, file)
            
        _image_file1 = os.path.join(self._grid_klones_adbd, "grid-klone-Linux-x86-64-19000241015.zip")
        open(_image_file1, "w").close()
        
        _image_file2 = os.path.join(self._grid_klones_adbd, "grid-klone-Linux-x86-64-23000241015.zip")
        open(_image_file2, "w").close()
        
        _new_image = os.path.join(self._repo_dir, "grid-klone-Linux-x86-64-19000241016.zip")
        open(_new_image, "w").close()
        gi_add_payload['location']['source'] = _new_image
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self._repo_dir
        writableGConfigOptions["gi_multi_image_count"] = 1
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data['grid-klones'][0]['version'], '19.0.0.0')
        self.assertEqual(modified_data['grid-klones'][0]['files'][0]['path'], 'ATP_192500/grid-klone-Linux-x86-64-19000241016.zip')
        self.assertEqual(len(modified_data['grid-klones']), len(inventory_json_old_format['grid-klones']))
        # remove the added image from repo for next test case
        os.remove(_image_file1)
        _added_image = os.path.join(self._grid_klones_adbd, "grid-klone-Linux-x86-64-19000241016.zip")
        os.remove(_added_image)
        
        
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2")
    @mock.patch("exabox.ovm.clugiconfigimage.mDownloadFromBucket")
    def test_single_add_image_from_OSS_atp(self, mDownloadFromBucket, mMockSha256):
        """Test add single image file from local file system
        """
        
        gi_add_payload = {
            "system_type": "ADBD",
            "image_type": "RELEASE",
            "type": "ADD",
            "version": "19.26.0.00.250116",
            "location": {
                "type": "objectstore_image",
                "filename": "dbaas_patch/atp/giimages/1926/g34062/gi1926_g34062_250114_patch.zip",
                "namespace": "dbaasexadatacustomersea1",
                "bucket": "atppatch",
                "sha256sum": "585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2"
            },
            "xmeta": {
                "latest": True,
                "default": True
            },
            "requestId": "f47253ff-81bd-4d42-941f-00a6b5942961",
            "ecra": {
                "whitelist_cidr": [
                    "10.0.1.0/28",
                    "10.0.1.32/28",
                    "10.0.1.112/28"
                ]
            }
        }
        # add inventory.json file
        _inventory_json_path = os.path.join(self._repo_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(inventory_json_old_format, file)
            
        _image_file1 = os.path.join(self._grid_klones_adbd, "grid-klone-Linux-x86-64-19000241016.zip")
        open(_image_file1, "w").close()
        
        _image_file2 = os.path.join(self._grid_klones_adbd, "grid-klone-Linux-x86-64-23000241016.zip")
        open(_image_file2, "w").close()
        
        _new_image = os.path.join(self._repo_dir, "gi1926_g34062_250114_patch.zip")
        open(_new_image, "w").close()
        mDownloadFromBucket.return_value = _new_image
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self._repo_dir
        writableGConfigOptions["gi_multi_image_count"] = 1
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data['grid-klones'][0]['files'][0]['path'], 'ATP_192500/grid-klone-Linux-x86-64-19000250116.zip')
        self.assertEqual(modified_data['grid-klones'][0]['files'][0]['sha256sum'], '585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2')
        self.assertEqual(modified_data['grid-klones'][0]['cdate'] , '250116')
        
        dir_path = pathlib.Path(self._grid_klones_adbd)
        file_name = 'grid-klone-Linux-x86-64-19000250116.zip'
        full_file_path = dir_path / file_name
        assert full_file_path.exists(), f"The file {full_file_path} does not exist."
        # inventory should have 2 entries
        self.assertEqual(len(modified_data), 4)
        # remove the added image from repo for next test case
        os.remove(_image_file1)
        
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2")
    @mock.patch("exabox.ovm.clugiconfigimage.mDownloadFromBucket")
    def test_single_add_duplicate_image_from_OSS_atp(self, mDownloadFromBucket, mMockSha256):
        """Test add single image file from local file system
        """
        
        gi_add_payload = {
            "system_type": "ADBD",
            "image_type": "RELEASE",
            "type": "ADD",
            "version": "19.26.0.00.241016",
            "location": {
                "type": "objectstore_image",
                "filename": "dbaas_patch/atp/giimages/1926/g34062/gi1926_g34062_250114_patch.zip",
                "namespace": "dbaasexadatacustomersea1",
                "bucket": "atppatch",
                "sha256sum": "585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2"
            },
            "xmeta": {
                "latest": True,
                "default": True
            },
            "requestId": "f47253ff-81bd-4d42-941f-00a6b5942961",
            "ecra": {
                "whitelist_cidr": [
                    "10.0.1.0/28",
                    "10.0.1.32/28",
                    "10.0.1.112/28"
                ]
            }
        }
        # add inventory.json file
        _inventory_json_path = os.path.join(self._repo_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(inventory_json_old_format, file)
            
        _image_file1 = os.path.join(self._grid_klones_adbd, "grid-klone-Linux-x86-64-19000241016.zip")
        open(_image_file1, "w").close()
        
        _image_file2 = os.path.join(self._grid_klones_adbd, "grid-klone-Linux-x86-64-23000241016.zip")
        open(_image_file2, "w").close()
        
        _new_image = os.path.join(self._repo_dir, "gi1926_g34062_250114_patch.zip")
        open(_new_image, "w").close()
        mDownloadFromBucket.return_value = _new_image
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self._repo_dir
        writableGConfigOptions["gi_multi_image_count"] = 1
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        _rc = _gi_image_config_obj.mExecute(gi_add_payload)
        self.assertEqual(_rc, 0)
        with open(_inventory_json_path, 'r') as json_file:
            modified_data = json.load(json_file)
        self.assertEqual(modified_data, inventory_json_old_format)
        dir_path = pathlib.Path(self._repo_dir)
        file_name = 'gi1926_g34062_250114_patch.zip'
        full_file_path = dir_path / file_name
        assert not full_file_path.exists(), f"The file {full_file_path} does not exist."
        # remove the added image from repo for next test case
        os.remove(_image_file1)    
    
    @mock.patch("exabox.ovm.clugiconfigimage.mComputeSha256sum", return_value="585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f2")
    @mock.patch("exabox.ovm.clugiconfigimage.mDownloadFromBucket")
    def test_single_add_image_from_OSS_atp_wrong_checksum(self, mDownloadFromBucket, mMockSha256):
        """Test add single image file from local file system
        """
        
        gi_add_payload = {
            "system_type": "ADBD",
            "image_type": "RELEASE",
            "type": "ADD",
            "version": "19.26.0.00.250115",
            "location": {
                "type": "objectstore_image",
                "filename": "dbaas_patch/atp/giimages/1926/g34062/gi1926_g34062_250114_patch.zip",
                "namespace": "dbaasexadatacustomersea1",
                "bucket": "atppatch",
                "sha256sum": "585439677673e12d50509dd0d2e356fb9c67b9d0839dcbaa044edca061d065f1"
            },
            "xmeta": {
                "latest": True,
                "default": True
            },
            "requestId": "f47253ff-81bd-4d42-941f-00a6b5942961",
            "ecra": {
                "whitelist_cidr": [
                    "10.0.1.0/28",
                    "10.0.1.32/28",
                    "10.0.1.112/28"
                ]
            }
        }
        # add inventory.json file
        _inventory_json_path = os.path.join(self._repo_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(inventory_json_old_format, file)
            
        _image_file1 = os.path.join(self._grid_klones_adbd, "grid-klone-Linux-x86-64-19000241015.zip")
        open(_image_file1, "w").close()
        
        _image_file2 = os.path.join(self._grid_klones_adbd, "grid-klone-Linux-x86-64-23000241015.zip")
        open(_image_file2, "w").close()
        
        _new_image = os.path.join(self._repo_dir, "gi1926_g34062_250114_patch.zip")
        open(_new_image, "w").close()
        gi_add_payload['location']['source'] = _new_image
        mDownloadFromBucket.return_value = _new_image
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self._repo_dir
        writableGConfigOptions["gi_multi_image_count"] = 1
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        _gi_image_config_obj = ebCluGiRepoUpdate._from_payload(cluCtrl_obj, gi_add_payload)
        with self.assertRaises(ExacloudRuntimeError) as context:
            _rc = _gi_image_config_obj.mExecute(gi_add_payload)
            self.assertEqual(_rc, 1)
            
    def test_mLoadRepoInventory_with_inventory(self):
        # add inventory.json file
        _inventory_json_path = os.path.join(self._repo_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(inventory_json_old_format, file)
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self._repo_dir
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        
        cluCtrl_obj.mLoadRepoInventory()
        
    def test_mLoadRepoInventory_without_inventory(self):
        # add inventory.json file
        _inventory_json_path = os.path.join(self._repo_dir, 'inventory.json')
        os.remove(_inventory_json_path)       
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self._repo_dir
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        
        cluCtrl_obj.mLoadRepoInventory()

    
    def test_mGetGiImageList_singleGI(self):
        _inventory_json_path = os.path.join(self._repo_dir, 'inventory.json')
        with open(_inventory_json_path, "w") as file:
            json.dump(inventory_json_old_format, file)
            
        gContext = self.mGetContext()
        gConfigOptions = gContext.mGetConfigOptions()
        writableGConfigOptions = copy.deepcopy(gConfigOptions)
        writableGConfigOptions["repository_root"] = self._repo_dir
        gContext.mSetConfigOptions(writableGConfigOptions)
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        expected_result = { 
            'giimagelist': {
                'EXACS': ['12.1.0.2', '12.2.0.1', '18.1.0.0', '19.0.0.0', '23.0.0.0'], 
                'ATP': ['19.0.0.0', '23.0.0.0']
                }
            }
        cluCtrl_obj.mLoadRepoInventory()
        giimagelist = cluCtrl_obj.mGetGiImageList()
        self.assertEqual(giimagelist, expected_result)  
                  
class ebTestmGetGiImageList(ebTestClucontrol):  
    def setUp(self):  
        self.mock_repo_inventory = {  
    'grid-klones': [  
        {  
            'files': [  
                {  
                    'path': 'EXACS/grid-klone-Linux-x86-64-192400240716.zip',  
                    'type': 'grid',  
                    'sha256sum': '3344cf3e526e7d88a78e2cd14cb67df658c5b594166fcddaa325bd73c7a109e4'  
                }  
            ],  
            'xmeta': {  
                'default': True,  
                'ol7_required': True,  
                'imgtype': 'RELEASE',  
                'supported_db': ['190', '181', '122', '121', '112'],  
                'latest': False  
            },  
            'version': '19.24.0.0.240716',  
            'service': ['EXACS']  
        },  
        {  
            'files': [  
                {  
                    'path': 'EXACS/grid-klone-Linux-x86-64-192300240416.zip',  
                    'type': 'grid',  
                    'sha256sum': '762a80c4e41c6d724d45c8a0ee67ebf312590a26f9c2a15615bd568f39bb14bd'  
                }  
            ],  
            'xmeta': {  
                'default': False,  
                'ol7_required': True,  
                'imgtype': 'RELEASE',  
                'supported_db': ['190', '181', '122', '121', '112'],  
                'latest': False  
            },  
            'version': '19.23.0.0.240416',  
            'service': ['EXACS']  
        },  
        {  
            'files': [  
                {  
                    'path': 'EXACS/grid-klone-Linux-x86-64-192200240116.zip',  
                    'type': 'grid',  
                    'sha256sum': '7f0b60b72b318efc886fd38ff9acfa2fb0067e195c4a91b87c3dcb01451a30e8'  
                }  
            ],  
            'xmeta': {  
                'default': False,  
                'ol7_required': True,  
                'imgtype': 'RELEASE',  
                'supported_db': ['190', '181', '122', '121', '112'],  
                'latest': False  
            },  
            'version': '19.22.0.0.240116',  
            'service': ['EXACS']  
        },  
        {  
            'files': [  
                {  
                    'path': 'EXACS/grid-klone-Linux-x86-64-192100231017.zip',  
                    'type': 'grid',  
                    'sha256sum': 'a8a36ab56c59cce963158cb907efa3ab48ea1428b94da3cebdab8659f5256f46'  
                }  
            ],  
            'xmeta': {  
                'default': False,  
                'ol7_required': True,  
                'imgtype': 'RELEASE',  
                'supported_db': ['190', '181', '122', '121', '112'],  
                'latest': False  
            },  
            'version': '19.21.0.0.231017',  
            'service': ['EXACS']  
        },  
        {  
            'files': [  
                {  
                    'path': 'EXACS/grid-klone-Linux-x86-64-23400240118.zip',  
                    'type': 'grid',  
                    'sha256sum': 'dcc3c44f478fe48d2c4900214a1e7f56f6c17f0aaec70c6c46dd7ef0e324f3b8'  
                }  
            ],  
            'xmeta': {  
                'default': False,  
                'ol7_required': True,  
                'imgtype': 'RELEASE',  
                'supported_db': ['190', '181', '122', '121', '112'],  
                'latest': False  
            },  
            'version': '23.4.0.0.240118',  
            'service': ['EXACS']  
        },  
        {  
            'files': [  
                {  
                    'path': 'EXACS/grid-klone-Linux-x86-64-23500240716.zip',  
                    'type': 'grid',  
                    'sha256sum': '4730ee31613e80bb3655afee932c0742fcaa5848469b4bffde981496cd94f705'  
                }  
            ],  
            'xmeta': {  
                'default': False,  
                'ol7_required': True,  
                'imgtype': 'RELEASE',  
                'supported_db': ['190', '181', '122', '121', '112'],  
                'latest': True  
            },  
            'version': '23.5.0.0.240716',  
            'service': ['EXACS']  
        },  
        {  
            'files': [  
                {  
                    'path': 'ADBD/grid-klone-Linux-x86-64-192400240716.zip',  
                    'type': 'grid',  
                    'sha256sum': '3344cf3e526e7d88a78e2cd14cb67df658c5b594166fcddaa325bd73c7a109e4'  
                }  
            ],  
            'xmeta': {  
                'default': False,  
                'ol7_required': True,  
                'imgtype': 'RELEASE',  
                'supported_db': ['190', '181', '122', '121', '112'],  
                'latest': False  
            },  
            'version': '19.24.0.0.240716',  
            'service': ['ATP']  
        },  
        {  
            'files': [  
                {  
                    'path': 'ADBD/grid-klone-Linux-x86-64-23500240716.zip',  
                    'type': 'grid',  
                    'sha256sum': '4730ee31613e80bb3655afee932c0742fcaa5848469b4bffde981496cd94f705'  
                }  
            ],  
            'xmeta': {  
                'default': False,  
                'ol7_required': True,  
                'imgtype': 'RELEASE',  
                'supported_db': ['190', '181', '122', '121', '112'],  
                'latest': True  
            },  
            'version': '23.5.0.0.240716',  
            'service': ['ATP']  
        }  
    ],  
    'gendate': '2024-09-23 03:28:42.126408'  
} 
    def test_mGetGiImageList(self):
        gContext = self.mGetContext()
        cluCtrl_obj = exaBoxCluCtrl(aCtx=gContext)
        cluCtrl_obj.mGetRepoInventory = MagicMock(return_value=self.mock_repo_inventory)
        expected_result = {  
            "giimagelist": {  
                "EXACS": ["19.24.0.0.240716", "19.23.0.0.240416", "23.4.0.0.240118", "23.5.0.0.240716"],  
                "ATP": ["19.24.0.0.240716", "23.5.0.0.240716"],  
            }  
        }  
        giimagelist = cluCtrl_obj.mGetGiImageList()
        self.assertEqual(giimagelist, expected_result)
            
        
if __name__ == '__main__':
    unittest.main()
