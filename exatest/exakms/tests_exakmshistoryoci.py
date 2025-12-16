#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/exakms/tests_exakmshistoryoci.py /main/3 2024/10/07 18:01:10 ririgoye Exp $
#
# tests_exakmshistoryoci.py
#
# Copyright (c) 2022, 2024, Oracle and/or its affiliates.
#
#    NAME
#      tests_exakmshistoryoci.py - <one-line expansion of the name>
#
#    DESCRIPTION
#      <short description of component this file declares/defines>
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    ririgoye    09/26/24 - Bug 36390923 - REMOVE EXAKMS HISTORY VALIDATION
#                           ACROSS HOSTS
#    aypaul      06/08/22 - Creation
#
import unittest
import os, stat, socket
from unittest.mock import patch, MagicMock

from exabox.exakms.ExaKmsHistoryOCI import ExaKmsHistoryOCI
from exabox.exakms.ExaKmsOCI import ExaKmsOCI
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Context import get_gcontext
from exabox.exakms.ExaKmsSingleton import ExaKmsSingleton
from exabox.exakms.ExaKmsFileSystem import ExaKmsFileSystem

OLD_COLUMNS='Timestamp\tHost\tKey\tOperation\n' + '-' * 40 + '\n\n'
OLD_ROWS=f"""2021-09-28 22:27:17+0000\t{socket.getfqdn()}\t[ExaKmsEntryOCIRSA] [33349fbb09093a991d59fc60c2425b21a1947e039400940cf1fc0f431d41b8f6] root@iad103714exddu0502.iad103714exd.adminiad1.oraclevcn.com\tinsert\n\
2021-09-28 22:27:17+0000\t{socket.getfqdn()}\t[ExaKmsEntryOCIRSA] [501a41e4fef1fc9b9f1d579f5ac728da6c05b2ab7eac395ba9cedd3f178fa9a6] grid@iad103714exddu0602.iad103714exd.adminiad1.oraclevcn.com\tdelete\n\
2021-09-28 22:27:17+0000\t{socket.getfqdn()}\t[ExaKmsEntryOCIRSA] [501a41e4fef1fc9b9f1d579f5ac728da6c05b2ab7eac395ba9cedd3f178fa9a6] root@iad103714exddu0602.iad103714exd.adminiad1.oraclevcn.com\tinsert\n\
2021-09-28 22:27:17+0000\tmock792613.dev3sub6mock.databasemock.mock.oraclevcn.com\t[ExaKmsEntryOCIRSA] [915e6b83e4d0293617ba953a9c8e3bea4f1782a772619b208eea64580ab225b5] root@iad103714exddu0702.iad103714exd.adminiad1.oraclevcn.com\tdelete\n\
"""

COLUMNS='Timestamp\tHost\tKey\tOperation\tID\tLabel\n' + '-' * 50 + '\n\n'
ROWS=f"""2021-09-28 22:27:17+0000\t{socket.getfqdn()}\t[ExaKmsEntryOCIRSA] [33349fbb09093a991d59fc60c2425b21a1947e039400940cf1fc0f431d41b8f6] root@iad103714exddu0502.iad103714exd.adminiad1.oraclevcn.com\tinsert\tea78ab2c-e908-4e31-a87d-d9edb8e0f5e3\tECS_MAIN_LINUX.X64_240924.0900\n\
2021-09-28 22:27:17+0000\t{socket.getfqdn()}\t[ExaKmsEntryOCIRSA] [501a41e4fef1fc9b9f1d579f5ac728da6c05b2ab7eac395ba9cedd3f178fa9a6] grid@iad103714exddu0602.iad103714exd.adminiad1.oraclevcn.com\tdelete\t4f77e975-f03f-4665-9825-a1d5d7912664\tECS_MAIN_LINUX.X64_240923.0901\n\
2021-09-28 22:27:17+0000\t{socket.getfqdn()}\t[ExaKmsEntryOCIRSA] [501a41e4fef1fc9b9f1d579f5ac728da6c05b2ab7eac395ba9cedd3f178fa9a6] root@iad103714exddu0602.iad103714exd.adminiad1.oraclevcn.com\tinsert\t0f17d921-b029-43af-9074-9ea5b244f5ea\tECS_MAIN_LINUX.X64_240923.0901\n\
2021-09-28 22:27:17+0000\tmock792613.dev3sub6mock.databasemock.mock.oraclevcn.com\t[ExaKmsEntryOCIRSA] [915e6b83e4d0293617ba953a9c8e3bea4f1782a772619b208eea64580ab225b5] root@iad103714exddu0702.iad103714exd.adminiad1.oraclevcn.com\tdelete\t9d02ec24-6b4f-47fd-b9bf-1125a22bdfc8\tECS_MAIN_LINUX.X64_240813.0901\n\
"""

OLD_SAMPLE_OSS_CHANGES = f"{OLD_COLUMNS}{OLD_ROWS}".encode('utf-8')
SAMPLE_OSS_CHANGES = f"{COLUMNS}{ROWS}".encode('utf-8')

class dummyContent():
    content = "mock_content"

class dummyData():
    data = dummyContent()

class ebTestExaKmsHistoryOCI(ebTestClucontrol):

    @classmethod
    def setUpClass(self):

        super().setUpClass(aGenerateDatabase=True)
        _exakms_oci = None
        with patch('urllib.request.urlopen'),\
             patch('exabox.exakms.ExaKmsOCI.ExaKmsOCI.mObjectStoreInit'):
             get_gcontext().mSetConfigOption('exakms_bucket_primary', 'mock_oss_primary_bucket')
             get_gcontext().mSetConfigOption('kms_key_id', 'mock_id')
             get_gcontext().mSetConfigOption('kms_dp_endpoint', 'mock_endpoint')
             _exakms_oci = ExaKmsOCI()
        self.__exakmshistory_oci = ExaKmsHistoryOCI(_exakms_oci)

        self.authorizedKeysFile = os.path.expanduser('~/.ssh/authorized_keys')
        self.currentPermissions = os.stat(self.authorizedKeysFile).st_mode
        if self.currentPermissions & stat.S_IWUSR != 1:
            os.chmod(self.authorizedKeysFile, stat.S_IRUSR | stat.S_IWUSR)

        self.mGetClubox(self).mGetCtx().mSetConfigOption('exakms_type', 'ExaKmsFileSystem')
        self.exakmsSingleton = ExaKmsSingleton()

        self.exakms = ExaKmsFileSystem()
        self.user = os.environ["USER"]
        self.home = os.environ["HOME"]
        self.host = os.environ["HOSTNAME"]

    @patch('exabox.exakms.ExaKmsOCI.ExaKmsOCI.mGetOSS')
    @patch('exabox.exakms.ExaKmsOCI.ExaKmsOCI.mPutOSS')
    def test_mPutExaKmsHistory(self, mock_getoss, mock_putoss):
        _mock_exakms_entry = _entry = self.exakms.mBuildExaKmsEntry(self.host, self.user, self.exakms.mGetEntryClass().mGeneratePrivateKey())
        self.__exakmshistory_oci._ExaKmsHistoryOCI__backupBucket = "mock_oss_secondary_bucket"
        self.__exakmshistory_oci.mPutExaKmsHistory(_mock_exakms_entry, "insert")

    @patch('exabox.exakms.ExaKmsOCI.ExaKmsOCI.mGetOSS')
    def test_mGetExaKmsHistory(self, mock_getoss):
        _mock_response = dummyData()
        _mock_response.data.content = SAMPLE_OSS_CHANGES
        mock_getoss.return_value = _mock_response

        self.assertEqual(len(self.__exakmshistory_oci.mGetExaKmsHistory(aUser = None, aHostName = None, aNumEntries = 20)), 4)
        self.assertEqual(len(self.__exakmshistory_oci.mGetExaKmsHistory(aUser = None, aHostName = "iad103714exddu0602", aNumEntries = 20)), 2)
        self.assertEqual(self.__exakmshistory_oci.mGetExaKmsHistory(aUser = "grid", aHostName = None, aNumEntries = 20)[0]["user_hostname"], "grid@iad103714exddu0602.iad103714exd.adminiad1.oraclevcn.com")
        self.assertEqual(self.__exakmshistory_oci.mGetExaKmsHistory(aUser = "root", aHostName = "iad103714exddu0602", aNumEntries = 20)[0]["user_hostname"], "root@iad103714exddu0602.iad103714exd.adminiad1.oraclevcn.com")

    @patch('exabox.exakms.ExaKmsOCI.ExaKmsOCI.mGetOSS')
    def test_mGetOlderExaKmsHistory(self, mock_getoss):
        _mock_response = dummyData()
        _mock_response.data.content = OLD_SAMPLE_OSS_CHANGES
        mock_getoss.return_value = _mock_response

        self.assertEqual(len(self.__exakmshistory_oci.mGetExaKmsHistory(aUser = None, aHostName = None, aNumEntries = 20)), 4)
        self.assertEqual(len(self.__exakmshistory_oci.mGetExaKmsHistory(aUser = None, aHostName = "iad103714exddu0602", aNumEntries = 20)), 2)
        self.assertEqual(self.__exakmshistory_oci.mGetExaKmsHistory(aUser = "grid", aHostName = None, aNumEntries = 20)[0]["user_hostname"], "grid@iad103714exddu0602.iad103714exd.adminiad1.oraclevcn.com")
        self.assertEqual(self.__exakmshistory_oci.mGetExaKmsHistory(aUser = "root", aHostName = "iad103714exddu0602", aNumEntries = 20)[0]["user_hostname"], "root@iad103714exddu0602.iad103714exd.adminiad1.oraclevcn.com")


if __name__ == '__main__':
    unittest.main(warnings='ignore')