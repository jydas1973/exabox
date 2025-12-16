Function:
---------
This script houses unit tests for the infra patching framework, invoked through ECRA.


Markers Supported:
------------------
* dom0  
* domu  
* cell  
* switch 
* roceswitch
* dom0_patch_prereq_check  
* domu_patch_prereq_check 
* cell_patch_prereq_check  
* switch_patch_prereq_check 
* roceswitch_patch_prereq_check
* dom0_patch  
* domu_patch 
* cell_patch  
* switch_patch  
* roceswitch_patch
* cell_rollback_prereq_check  
* switch_rollback_prereq_check 
* roceswitch_rollback_prereq_check
* dom0_rollback  
* domu_rollback 
* cell_rollback  
* switch_rollback 
* roceswitch_rollback
* dom0_backup_image  
* domu_backup_image 
* dom0_postcheck  
* domu_postcheck  
* cell_postcheck  
* switch_postcheck 
* roceswitch_postcheck


Pre-Requisite for running tests
------------------------------------
Correct values for cluster,ECRA url, ecra username and ecra password for the the user, need to be updated in the payload.json file present in config folder.
pytest (>=6.2.4), pytest-dependency (>=0.5.1) and pytest-ordering (>=0.6) modules are required. These can be installed in dev environment in a view by executing
bin/py3_venv.sh -dev_addons

These modules can be installed and used with out depending on ECS source code like below
example for pytest instllation.
pip3 install pytest --user 
export PATH=$HOME/.local/bin:$PATH


Running Tests:
--------------
The tests can be invoked in the following ways:
1. Unique test(s) for a particular target.
   * python3 -m pytest -vv -ra -s -m dom0_patch
   Above command will run only the patch operation on dom0's
   
2. All tests for a particular target.
   * python3 -m pytest -vv -ra -s -m dom0
   Above command will run all the operations on dom0's.
   
3. All tests for all multiple targets.
   * python3 -m pytest -vv -ra -s -m "dom0, domu"
   This command will run all the unit tests for dom0's and domU's

4. Combination of different tests from different targets
   * python3 -m pytest -vv -ra -s -m "dom0_patch_prereq_check, domu_postcheck"


Test results are of the below format

success scenario:

bash-4.2$ python3 -m pytest -vv -ra -s -m 'cell_patch_prereq_check'
==================================================================== test session starts ====================================================================
platform linux -- Python 3.6.8, pytest-6.2.4, py-1.10.0, pluggy-0.13.1 --
/bin/python3
cachedir: .pytest_cache
rootdir:
/net/slc16ofa/scratch/sdevasek/view_storage/sdevasek_testautomate/ecs/exacloud/exabox/exatest/infrapatch/test,
configfile: pytest.ini
plugins: ordering-0.6, dependency-0.5.1
collected 25 items / 24 deselected / 1 selected

test_infrapatching_cell.py::Test_cell_class::test_cell_patch_prereq_check


2021-09-15 20:55:33-0700  - PatchTestHandler -INFO- Payload updation in progress.
======================================================= 1 passed, 24 deselected in 365.64s (0:06:05) ========================================================  


failure scenario:

bash-4.2$ python3 -m pytest -vv -ra -s -m 'cell_patch_prereq_check or cell_patch or cell_rollback'
==================================================================== test session starts ====================================================================
platform linux -- Python 3.6.8, pytest-6.2.4, py-1.10.0, pluggy-0.13.1 --
/bin/python3
cachedir: .pytest_cache
rootdir:
/net/slc16ofa/scratch/sdevasek/view_storage/sdevasek_testautomate/ecs/exacloud/exabox/exatest/infrapatch/test,
configfile: pytest.ini
plugins: ordering-0.6, dependency-0.5.1
collected 25 items / 22 deselected / 3 selected

test_infrapatching_cell.py::Test_cell_class::test_cell_patch_prereq_check FAILED
test_infrapatching_cell.py::Test_cell_class::test_cell_patch SKIPPED
(test_cell_patch depends on patch_prereq_check)
test_infrapatching_cell.py::Test_cell_class::test_cell_rollback SKIPPED
(test_cell_rollback depends on patch)

========================================================================= FAILURES ==========================================================================
_______________________________________________________
Test_cell_class.test_cell_patch_prereq_check
________________________________________________________

self = <test_infrapatching_cell.Test_cell_class
testMethod=test_cell_patch_prereq_check>

    @pytest.mark.run(order=201)
    @pytest.mark.dependency(name="patch_prereq_check", scope="class")
    @pytest.mark.cell_patch_prereq_check
    def test_cell_patch_prereq_check(self):
        result =  mExecuteInfraPatchCommand(TASK_PREREQ_CHECK, PATCH_CELL)
>       self.assertTrue(result, "Test Failed.")
E       AssertionError: False is not true : Test Failed.

test_infrapatching_cell.py:38: AssertionError
================================================================== short test summary info ==================================================================
SKIPPED [1]
../../../../../../../../../../../../home/sdevasek/.local/lib/python3.6/site-packages/pytest_dependency.py:103:
test_cell_patch depends on patch_prereq_check
SKIPPED [1]
../../../../../../../../../../../../home/sdevasek/.local/lib/python3.6/site-packages/pytest_dependency.py:103:
test_cell_rollback depends on patch
FAILED test_infrapatching_cell.py::Test_cell_class::test_cell_patch_prereq_check
- AssertionError: False is not true : Test Failed.
======================================================== 1 failed, 2 skipped, 22 deselected in 0.41s ========================================================


Note :
------
 Test execution order depends on the run order annotation used on the test. If the test has dependency on other test, it gets skipped in the execution
 if the dependent test fails.
