import os
import json
import unittest
import copy
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.core.Node import exaBoxNode
from exabox.core.MockCommand import exaMockCommand
from exabox.log.LogMgr import ebLogInfo
from exabox.agent.Client import ebJobResponse, ebExaClient
from exabox.core.DBStore import ebGetDefaultDB
import warnings
from ast import literal_eval
from exabox.core.Context import get_gcontext
import time

def populateTestOptions(thisOptions):
    thisOptions.jsondispatch = None
    thisOptions.sop = None
    thisOptions.agent = None
    thisOptions.exakms = None
    thisOptions.vmctrl = None
    thisOptions.bmcctrl = None
    thisOptions.clusterctrl = None
    thisOptions.schedgenctrl = None
    thisOptions.status = None
    thisOptions.monitor = None
    thisOptions.patchclu = None
    thisOptions.async = None
    thisOptions.steplist = None
    thisOptions.undo = None
    thisOptions.vmcmd = None
    thisOptions.jsonconf = None
    thisOptions.verbose = "True"
    thisOptions.vmid = "dummy VMID"
    thisOptions.scriptname = "dummyscript1"
    thisOptions.hostname = "hostname1"
    thisOptions.oeda_step = "sample_oeda_step"
    thisOptions.pkeyconf = None
    thisOptions.disablepkey = None
    thisOptions.jsonconf = None
    thisOptions.debug = None
    thisOptions.sshkey = None
    thisOptions.pnode_type = "sample pnode type"
    thisOptions.patch_file_cells = "patch file cells"
    thisOptions.patch_files_dom0s = "patch files dom0"
    thisOptions.patch_version_dom0s = "patch version dom0"
    thisOptions.dgcmd = None
    thisOptions.username = "username"
    thisOptions.enablegilatest = None
 

class testOptions(object): pass

class ebTestDispatcher(ebTestClucontrol):

    @classmethod
    def setUpClass(self):
        super(ebTestDispatcher, self).setUpClass(aGenerateDatabase=True, aUseAgent=True)
        warnings.filterwarnings("ignore")
        self.mGetUtil(self).mGetInstallerAgent().mStartAgent()
        get_gcontext().mSetConfigOption('kvm_override_disable_pinning',False)
        print('enter')

    @classmethod
    def tearDownClass(self):
        try:
            self.mGetUtil(self).mGetInstallerAgent().mStopAgent()
            print('done')
        except Exception as e:
            pass

    def test_mTest_dispatcher(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.clusterctrl")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.configpath = os.path.join(self.mGetUtil().mGetResourcesPath(),"sample.xml")

        thisClient = ebExaClient()
        thisOptions.clusterctrl = "sim_install"
        _db = ebGetDefaultDB()

        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        ebLogInfo("test_mTest_dispatcher: Checking Job is set to 'Pending' state!")
        #Assert job is set to pending state!
        self.assertEqual(thisClient.mGetJsonResponse()['status'], "Pending")
        _uuid = thisClient.mGetJsonResponse()['uuid']
        thisClient.mWaitForCompletion()
        _rc = _db.mGetUuidStatus(_uuid)
        _status = _rc[1].lstrip().rstrip()
        ebLogInfo("test_mTest_dispatcher: Checking Job is set to 'Done' state!")
        #Assert job is done !
        self.assertTrue(_status in ['Done'])
        

    def test_mTest_workermanager(self):
        ebLogInfo("")
        ebLogInfo("Running unit test on ebExaClient.mIssueRequest.clusterctrl")
        thisOptions = testOptions()
        populateTestOptions(thisOptions)
        thisOptions.configpath = os.path.join(self.mGetUtil().mGetResourcesPath(),"sample.xml")
        _uuid = '00000000-0000-0000-0000-000000000000'
        _db = ebGetDefaultDB()
        _idle_worker = _db.mGetNumberOfIdleWorkers()
        print(f'Idle workers: {_idle_worker}')
        _pool_count = get_gcontext().mGetConfigOptions()['idle_thread_pool_count_nonexacs']
        _worker_count = get_gcontext().mGetConfigOptions()['worker_count_nonexacs']
        print(f'Pool count: {_pool_count}')
        print(f'Worker count: {_worker_count}')

        self.assertTrue(int(_idle_worker) >= int(_pool_count))

        thisClient = ebExaClient()
        thisOptions.clusterctrl = "sim_install"
        thisClient.mIssueRequest(aCmd=None, aOptions=thisOptions)
        time.sleep(30)
        #By now, an idle worker would have got used up.
        #The workermanager process should kick in and create a new worker...
        #.. to ensure pool of threads is maintained.

        _idle_worker = _db.mGetNumberOfIdleWorkers()
        print(f'New Idle workers: {_idle_worker}')
        #Assert pool is still maintained!
        self.assertTrue(int(_idle_worker) >= int(_pool_count))


if __name__ == "__main__":
    pass
    # unittest.main()
