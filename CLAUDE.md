# Exabox Code Generation Guide

## 1. Core Principles

- **No hardcoded values** — use constants from `infrapatching/utils/constants.py` or config
- **F-strings only** — all string interpolation MUST use f-strings (no `.format()` or `%`)
- **Method prefix `m`** — every class method must start with `m` (e.g., `mPreCheck`, `mPatch`)
- **Global function prefix `eb`** — standalone utility/log functions use `eb` prefix
- **Mock external calls in tests** — DB, HTTP, SSH, subprocess must always be mocked
- **Log before raising** — always log with context before raising any exception
- **Never log sensitive data** — no passwords, keys, tokens in logs

---

## 2. Tech Stack

- **Language**: Python 3 (some Python 2 legacy code — do not introduce new py2-only patterns)
- **Test framework**: `unittest` (NOT pytest)
- **Database**: MySQL via `core/DBStore3.py` (DBStore3 class)
- **HTTP server**: Custom `BaseServer/` infrastructure
- **OCI integration**: `exaoci/` module
- **KMS**: `exakms/` module
- **No external package manager file** — dependencies managed via system Python

---

## 3. Architecture

```
exabox/
├── agent/           # Worker, Dispatcher, Scheduler, Client, DBService
├── BaseServer/      # HTTP/HTTPS server, AsyncProcessing, BaseHandler
├── core/            # Context, Error, DBStore, Threads, Node
├── config/          # Configuration management
├── exakms/          # Key management system
├── exaoci/          # OCI connectors
├── exassh/          # SSH utilities
├── infrapatching/   # Infra patch orchestration (see below)
│   ├── core/        # cludispatcher.py, infrapatcherror.py
│   ├── handlers/
│   │   ├── targetHandler/   # dom0handler.py, cellhandler.py, ...
│   │   ├── taskHandler/     # task-specific handlers
│   │   ├── pluginHandler/   # plugin extensions
│   │   ├── mockTargetHandler/
│   │   └── mockTaskHandler/
│   ├── helpers/     # crshelper.py, etc.
│   └── utils/       # constants.py, utility.py
├── log/             # LogMgr.py — central logging
├── network/         # Network utilities
├── ovm/             # OVM/cluster utilities
├── utils/           # common.py, oci_region.py, etc.
└── exatest/         # Tests mirroring source structure
    ├── infrapatching/
    │   ├── core/
    │   └── handlers/
    └── common/      # ebTestClucontrol base class
```

**Infrapatching handler hierarchy:**
```
LogHandler
  └── GenericHandler
        ├── TargetHandler  ← dom0handler, cellhandler, domuhandler
        └── TaskHandler    ← task-specific handlers
```

---

## 4. File Headers

Every file MUST start with an RCS header and structured comment block:

```python
#
# $Header: ecs/exacloud/exabox/<path>/<file>.py /main/1 2025/01/01 00:00:00 author Exp $#
#
# <file>.py
#
# Copyright (c) 2020, 2025, Oracle and/or its affiliates.
#
#    NAME
#      <file>.py - Brief one-line description
#    DESCRIPTION
#      Detailed description of what this module does.
#
#    NOTES
#      <optional notes>
#
#    MODIFIED   (MM/DD/YY)
#    jyotdas    03/03/26 - Brief description of change
#
```

**Rules:**
- Use `INITIALS  MM/DD/YY - description` format in MODIFIED section (initials 3–7 chars)
- Copyright must cover actual year range (e.g., `2020, 2025`)
- Initials are typically the SCM username (e.g., `araghave`, `jyotdas`)

---

## 5. Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Class methods | `m` prefix | `mPreCheck`, `mPatch`, `mGetLogPath` |
| Global functions | `eb` prefix | `ebLogInfo`, `ebGetDefaultDB` |
| Private attributes | double underscore | `self.__config`, `self.__log` |
| Constants | UPPER_CASE | `PATCH_DOM0`, `TASK_PREREQ_CHECK` |
| Class names | Descriptive, no strict prefix | `Dom0Handler`, `CrsHelper`, `ebCluPatchDispatcher` |
| Test classes | `ebTest` prefix | `ebTestCluPatchDispatcher` |

**Class naming note**: `eb` prefix is common but not universal. Infrastructure-level classes (handlers, helpers) may omit it. Follow the existing pattern in the module.

---

## 6. Code Style

### String Interpolation — F-strings ONLY

```python
# CORRECT
self.mPatchLogInfo(f"Patching dom0: {_dom0} with version {_version}")
self.mPatchLogError(f"Return code from mSetEnvironment is {_ret}")
raise Exception(f"Unable to locate {DOM0_IPTABLES_SETUP_SCRIPT} on dom0 nodes")

# WRONG — do not use .format() or % in new code
ebLogInfo("Processing request: {0}".format(request_id))
ebLogError("Failed: %s" % error_msg)
```

### Import Organization

```python
# 1. Standard library
import os, sys
import json
import traceback
import datetime
from time import sleep

# 2. Third-party
from exabox.BaseServer.AsyncProcessing import ProcessManager

# 3. Local — organized by module
from exabox.core.Context import get_gcontext
from exabox.core.Node import exaBoxNode
from exabox.infrapatching.handlers.targetHandler.targethandler import TargetHandler
from exabox.infrapatching.utils.utility import mGetFirstDirInZip, mFormatOut
from exabox.infrapatching.utils.constants import *   # wildcard ok for constants
from exabox.infrapatching.core.infrapatcherror import *
```

### Getter/Setter Pattern

```python
class Dom0Handler(TargetHandler):
    def __init__(self):
        self.__patch_base_dir = None

    def mGetDom0PatchBaseDir(self):
        return self.__patch_base_dir

    def mSetDom0PatchBaseDir(self, aDir):
        self.__patch_base_dir = aDir
```

---

## 7. Logging

**In handler classes** — use the `mPatchLog*` wrapper methods inherited from `LogHandler`:

```python
self.mPatchLogInfo(f"Starting {TASK_PREREQ_CHECK} on {PATCH_DOM0}: {_dom0}")
self.mPatchLogError(f"Exception in mPreCheck: {str(e)}")
self.mPatchLogWarn(f"Unexpected state for dom0: {_dom0}")
self.mPatchLogDebug(f"Dom0 list from xm list: {_domU_listed_by_xm_list}")
```

**Outside handler classes** — use global log functions directly:

```python
from exabox.log.LogMgr import ebLogInfo, ebLogError, ebLogDebug, ebLogWarn

ebLogInfo(f"Processing request: {request_id}")
ebLogError(f"Failed to process job: {str(e)}")
```

**Available functions:** `ebLogInfo`, `ebLogError`, `ebLogDebug`, `ebLogWarn`, `ebLogTrace`

**What to log:**
- Operation start/end with target names and task type
- Return codes from subprocess/SSH calls
- Exception details with `str(e)` before any re-raise
- Important state transitions

---

## 8. Error Handling

### Infrapatching Error Codes

Use hex constants from `infrapatching/core/infrapatcherror.py`:

```python
from exabox.infrapatching.core.infrapatcherror import *

# Check return codes
if _ret != PATCH_SUCCESS_EXIT_CODE:  # "0x00000000"
    self.mAddError(PATCH_OPERATION_FAILED, f"Patch failed with rc={_ret}")

# Build error report
_code, _msg, _desc, _error_action = ebPatchFormatBuildErrorWithErrorAction(
    aError, _suggestion_msg, aTargetTypes=self.__target_type
)
```

**Common error codes:**
- `PATCH_SUCCESS_EXIT_CODE = "0x00000000"`
- `PATCH_OPERATION_FAILED = "0x03010000"`
- `MISSING_PATCH_FILES = "0x03010001"`
- `INCORRECT_INPUT_JSON = "0x03010004"`
- `PATCH_REQUEST_TIMEOUT = "0x03010005"`

### Exception Pattern

```python
try:
    _ret = self.mRunPatching(_dom0)
    if _ret != PATCH_SUCCESS_EXIT_CODE:
        self.mPatchLogError(f"Patching failed on {_dom0}, rc={_ret}")
        self.mAddError(PATCH_OPERATION_FAILED, f"Failure on {_dom0}")
except Exception as e:
    self.mPatchLogError(f"Exception in mPatch: {str(e)}")
    self.mAddError(PATCH_OPERATION_FAILED, str(e))
```

### Core Agent Error Codes

For non-infrapatching code, use `core/Error.py`:

```python
from exabox.core.Error import ebError, ebErrorCodes
try:
    # operation
except Exception as e:
    ebLogError(f"Operation failed: {str(e)}")
    raise ebError(ebErrorCodes.GENERAL_ERROR, str(e))
```

---

## 9. Testing

### File Structure

```
exatest/infrapatching/core/tests_cludispatcher.py   ← mirrors infrapatching/core/cludispatcher.py
exatest/infrapatching/handlers/tests_dom0handler.py  ← mirrors dom0handler.py
```

### Test Template

```python
#!/bin/python
#
# tests_<module>.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#    NAME
#      tests_<module>.py - Unit tests for <module>.py
#    MODIFIED   (MM/DD/YY)
#    author     MM/DD/YY - Initial version

import unittest
from unittest.mock import patch, MagicMock

from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.<module>.<class> import <ClassName>
from exabox.log.LogMgr import ebLogInfo

class ebTest<ClassName>(ebTestClucontrol):
    SUCCESS_ERROR_CODE = "0x00000000"

    @classmethod
    def setUpClass(cls):
        ebLogInfo("Starting classSetUp <ClassName>")
        super(ebTest<ClassName>, cls).setUpClass(aGenerateDatabase=True)

    @patch('exabox.<module>.<class>.<ClassName>.<mSomeExternalCall>', return_value="0x00000000")
    def test_mOperation_success(self, mock_call):
        ebLogInfo("Running test: mOperation success case")
        # arrange
        _instance = <ClassName>(aJob=self._job)
        # act
        _result = _instance.mOperation()
        # assert
        self.assertEqual(_result, self.SUCCESS_ERROR_CODE)

    def test_mOperation_missingInput_returnsError(self):
        ebLogInfo("Running test: mOperation missing input")
        # ...

if __name__ == '__main__':
    unittest.main()
```

### Test Coverage Requirements

For every new method, write:
1. **Success path** — valid inputs, expected return value
2. **Edge case** — empty dict, None values, boundary conditions
3. **Error case** — invalid input, exception from dependency

### Running Tests

```bash
cd exatest
python exatest.py -run -all                      # all tests
python exatest.py -run tests_dom0handler         # specific file
python exatest.py -run -all infrapatching        # component tests
python exatest.py -run -all --coverage           # with coverage
./exatest.sh -run -all                           # shell runner
```

---

## 10. Infrapatching-Specific Patterns

### Handler Implementation

```python
from exabox.infrapatching.handlers.targetHandler.targethandler import TargetHandler
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *

class Dom0Handler(TargetHandler):
    def mPreCheck(self):
        self.mPatchLogInfo(f"\n---------------> Starting {TASK_PREREQ_CHECK} on {PATCH_DOM0}s <---------------\n")
        _ret = PATCH_SUCCESS_EXIT_CODE
        try:
            # precheck logic
            pass
        except Exception as e:
            self.mPatchLogError(f"Exception in mPreCheck: {str(e)}")
            self.mAddError(PATCH_OPERATION_FAILED, str(e))
            _ret = PATCH_OPERATION_FAILED
        self.mPatchLogInfo(f"Final return code from {self.mGetTask()}: {_ret}")
        return _ret

    def mPatch(self):
        # patch logic

    def mRollBack(self):
        # rollback logic

    def mPostCheck(self):
        # postcheck logic
```

### Constants & Wildcard Import

```python
# Always import constants with wildcard
from exabox.infrapatching.utils.constants import *
from exabox.infrapatching.core.infrapatcherror import *

# Use them directly (not as module.CONSTANT)
if _operation == TASK_PREREQ_CHECK:
    ...
if _target == PATCH_DOM0:
    ...
```

### Factory Pattern

```python
_handler = getTaskHandlerInstance(operation, params_dict)
_ret = _handler.mPreCheck()
```

---

## 11. Common Patterns

### Configuration Access

```python
from exabox.core.Context import get_gcontext
context = get_gcontext()
config_value = context.mGetConfig().mGetConfigValue("key")
```

### Database Operations

```python
from exabox.core.DBStore import ebGetDefaultDB
db = ebGetDefaultDB()
result = db.mExecuteQuery(query, params)
```

### Context Manager for Locking

```python
from exabox.core.DBStore import ExaLock
with ExaLock(lock_name):
    # protected critical section
```

---

## 12. Development Commands

```bash
# Run all tests
cd exatest && python exatest.py -run -all

# Run specific test
cd exatest && python exatest.py -run tests_dom0handler

# Run with coverage
cd exatest && python exatest.py -run -all --coverage

# Check coverage report
open exatest/htmlcov/index.html
```

---

## 13. AI Coding Assistant Instructions

- **Read before editing** — always read target file(s) before making changes
- **Follow f-string rule strictly** — never use `.format()` or `%` for string interpolation in new code
- **Use `m` prefix** for all new class methods; use `eb` prefix for new global functions
- **Add file header** — every new file needs the RCS-style header with MODIFIED log
- **Mirror test structure** — test file path must mirror source file path under `exatest/`
- **Inherit correctly** — infrapatching handlers must inherit from the correct base (`TargetHandler`, `TaskHandler`, `GenericHandler`)
- **Constants from constants.py** — never hardcode operation names, target types, or error codes; import from `constants.py` and `infrapatcherror.py`
- **Mock all external calls** — no real DB/SSH/HTTP in unit tests; use `unittest.mock.patch`
- **Use `mPatchLog*` in handlers** — do NOT call `ebLogInfo` directly inside handler classes; use `self.mPatchLogInfo` instead
- **Run tests before committing** — `cd exatest && python exatest.py -run -all` must pass with no regressions

---

## 14. Pre-Commit Checklist

- [ ] File header with RCS `$Header` and MODIFIED log entry added
- [ ] All string interpolation uses f-strings
- [ ] Method names prefixed with `m`, global functions with `eb`
- [ ] No hardcoded constants — all in `constants.py` or `infrapatcherror.py`
- [ ] Error codes from `infrapatcherror.py` (infrapatching) or `core/Error.py` (agent/core)
- [ ] Unit tests created in `exatest/` with matching path
- [ ] Tests cover: success path, edge cases, error cases
- [ ] All external dependencies mocked in tests
- [ ] `cd exatest && python exatest.py -run -all` passes
- [ ] No sensitive data (passwords, keys, tokens) in logs or code
