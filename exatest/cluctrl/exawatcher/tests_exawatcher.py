import unittest

from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.ovm.exawatcher import exaBoxExaWatcher, cleanupExaWatcherLogs, deleteOldLogs
import os


class TestExawatcher(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super().setUpClass(aGenerateDatabase=True)
        super().setUpClass()

    def setUp(self):
        self.mGetClubox()._exaBoxCluCtrl__timeout_ecops = "2"
        self.mGetClubox()._exaBoxCluCtrl__kvm_enabled = True

    def test_exawatcher_fetch(self):

        _cmds = {
            self.mGetRegexVm(): [[
                    exaMockCommand("/opt/oracle.ExaWatcher/GetExaWatcherResults.sh --from.*"),
                    exaMockCommand("du -s.*", aStdout='1'),
                    exaMockCommand("ls .*/ExtractedResults", aStdout="file1"),
                    exaMockCommand("bin/rm -rf.*")
                ]],

            self.mGetRegexDom0(): [[
                    exaMockCommand("/opt/oracle.ExaWatcher/GetExaWatcherResults.sh --from.*"),
                    exaMockCommand("du -s.*", aStdout='1'),
                    exaMockCommand("ls .*/ExtractedResults", aStdout="file1"),
                    exaMockCommand("bin/rm -rf.*")
                ]],
            self.mGetRegexLocal(): [
                [
                    exaMockCommand("rm.*", aRc=0,  aPersist=True),
                    exaMockCommand("ping .*", aRc=0,  aPersist=True)
                ]
            ]


        }

        self.mPrepareMockCommands(_cmds)

        _options = self.mGetPayload()
        _options.jsonconf['targettypes'] = "dom0"
        cluctrl = self.mGetClubox()
        exawatcher = exaBoxExaWatcher(cluctrl)
        exawatcher.mListExaWatcherLogs(aOptions=None)
        exawatcher.mCollectExaWatcherLogs(aOptions=_options)
        _log_path = 'log/exawatcher/'
        _f_list = os.listdir(_log_path)
        self.assertTrue(len(_f_list))
        deleteOldLogs('log/exawatcher/', 0)
        cleanupExaWatcherLogs()

if __name__ == '__main__':
    unittest.main()

