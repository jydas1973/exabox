# Infrapatching Error Handling Framework — Improvements and Runbook Integration

- [Overview](#overview)
  - [Detailed Requirement](#detailed-requirement)
  - [Current Issues](#current-issues)
  - [Process Flow](#process-flow)
  - [Proposed Changes](#proposed-changes)
    - [Error Message Improvements](#error-message-improvements)
    - [Framework Structural Improvements](#framework-structural-improvements)
    - [Runbook Integration](#runbook-integration)
  - [Sample Implementation](#sample-implementation)
  - [Clarifications](#clarifications)
  - [JIRAS](#jiras)

---

## Overview

The infrapatching error handling framework in `infrapatching/core/infrapatcherror.py` defines all error codes, error messages, and error actions used across the infra patching subsystem. The framework is consumed by every handler (dom0, cell, domu, switch, cps, plugins) and drives operator-facing error output in ECRA.

Three areas of improvement have been identified through code review and runbook analysis:

1. **Structural issues** in the framework that cause silent failures and make future maintenance harder.
2. **Error message quality** — messages that are too terse and do not guide operators toward the right diagnostic action.
3. **Runbook integration** — the operations team maintains a detailed runbook of investigation steps per error code, but this knowledge is entirely disconnected from the code. Bridging this gap would significantly reduce mean time to resolution (MTTR).

---

## Detailed Requirement

### 1. Fix Structural Issues in `infrapatcherror.py`

The current file has several structural issues that silently affect behavior or make the framework brittle. These need to be fixed before any new error codes are added.

### 2. Improve Error Messages for Operator Effectiveness

Error messages must guide the operator toward the first diagnostic action. The current messages describe the failure but provide no triage direction. The operations runbook (`exacs_runbook_with_next_steps.pdf`) reveals a consistent pattern of causes and first steps per error code that should be encoded into the messages.

### 3. Integrate Runbook Next Steps into the Error Framework

The operations runbook contains per-error-code data (possible causes, first diagnostic command, CN template, reschedule policy) that is currently maintained entirely in Confluence as a manual document. This creates operational lag and risks of runbook diverging from code. A companion programmatic index should encode this data so it is:

- Accessible to logging and dispatcher code
- Automatically surfaced in ECRA error output
- Maintainable alongside the error code definitions

---

## Current Issues

### Issue 1: CPS Error Dictionaries Use Plain Strings — Silent Data Loss (High)

All CPS-related error dicts (`gCpsGenericError`, `gCpsPrecheckError`, `gCpsPatchError`, `gCpsRollbackError`, `gCpsSwitchoverError`, `gCpsPostcheckError`, `gCpsBackupkError`) use plain strings instead of `(message, error_action)` tuples.

```python
# Current — INCORRECT
gCpsGenericError = {
    "0x030F0004": "CPS operation Status failed.",   # plain string
    "0x030F0006": "CPS patch exception detected.",
}

# All other dicts — correct
gPatchDom0Error = {
    "0x03030008": ("Unable to establish Heartbeat on the cells.", "FAIL_DONTSHOW_PAGE_ONCALL"),  # tuple
}
```

`ebPatchFormatBuildErrorWithErrorAction` checks `isinstance(_error, tuple)`. For CPS errors it silently falls to the `else` branch — the `error_action` field is **never read** and always defaults to `FAIL_DONTSHOW_PAGE_ONCALL`. If a CPS error ever needs `FAIL_AND_SHOW`, the dict value is ignored with no warning.

Additionally, `gCpsBackupkError` contains a typo in the variable name (`Backup**k**Error`).

---

### Issue 2: Typo in Generic Error Message (Medium)

`"0x03010007"` contains a visible typo in a customer-facing message:

```python
"0x03010007": ("One ore more individual patch requests failed", "FAIL_DONTSHOW_PAGE_ONCALL"),
#                   ^^^ should be "or more"
```

---

### Issue 3: Error Constant Defined Without Dict Entry (Medium)

`NO_ACTION_REQUIRED = "0x0301003D"` is defined as a module-level constant but has no entry in `gPatchGenericError`. If `ebPatchFormatBuildErrorWithErrorAction` is called with this code, the lookup silently falls back to the generic `0x03010000` failure message — reporting a no-action scenario as a failure.

```python
# Constant defined at line 207
NO_ACTION_REQUIRED = "0x0301003D"

# But no entry in gPatchGenericError for "0x0301003D"
# Result: ebPatchFormatBuildErrorWithErrorAction("0x0301003D") returns
#         ("0x03010000", "Patch operation Status failed", ...)  ← wrong
```

---

### Issue 4: 15+ Separate Dicts With Manual Routing Function (Medium)

`mGetPatchkey()` implements a long if/elif chain to route from an error range string to the correct dict. Every new error category requires adding a new dict AND modifying this routing function — two places to change, one easy to miss.

```python
def mGetPatchkey(_error_code_range_key):
    if _error_code_range_key in [G_ERROR_RANGE_PATCH_GENERIC, G_SUCCESS_PATCH_GENERIC]:
        return gPatchGenericError
    if _error_code_range_key == G_ERROR_RANGE_PATCH_DOM0:
        return gPatchDom0Error
    if _error_code_range_key == G_ERROR_RANGE_PATCH_CELL:
        return gPatchCellError
    # ... 12 more branches ...
    # No default — returns None implicitly if range not matched
    # dict(None) raises TypeError in caller — unhandled
```

---

### Issue 5: Error Actions Are Magic Strings (Low)

Error actions (`"FAIL_DONTSHOW_PAGE_ONCALL"`, `"FAIL_AND_SHOW"`) are bare strings with no validation. A typo produces wrong operator behavior with no runtime warning.

---

### Issue 6: Two Near-Identical Format Functions (Low)

`ebPatchFormatBuildError` and `ebPatchFormatBuildErrorWithErrorAction` are ~90% identical. Future logic changes require updating both.

---

### Issue 7: Error Entries Are Positional Tuples (Low)

All callers unpack by position index, which is fragile and non-self-documenting:

```python
_error_description = _error[0]   # What is index 0? Must look it up
_error_action = _error[1]        # Positional — silent break if tuple changes
```

---

### Issue 8: No Validation Between Constants and Dict (Low)

Nothing prevents a constant from being defined without a corresponding dict entry (as seen in Issue 3), or a dict entry without a constant. There is no test-time check.

---

## Process Flow

### Current Error Handling Flow

```
Handler (e.g., Dom0Handler)
    └── mAddError(PATCH_OPERATION_FAILED, "detail message")
              │
              ▼
        GenericHandler.mAddError()
              │
              ▼
        ebPatchFormatBuildErrorWithErrorAction(error_code)
              │
              ├── Extracts error range from code string [2:6]
              ├── mGetPatchkey(range) → one of 15+ dicts
              ├── Looks up (message, action) tuple from dict
              └── Returns (code, message, suggestion, action) to ECRA
```

### Proposed Flow After Improvements

```
Handler (e.g., Dom0Handler)
    └── mAddError(PATCH_OPERATION_FAILED, "detail message")
              │
              ▼
        GenericHandler.mAddError()
              │
              ▼
        ebPatchFormatBuildErrorWithErrorAction(error_code)
              │
              ├── Single PATCH_ERRORS dict lookup (no routing)
              ├── Returns PatchError(message, action) namedtuple
              ├── Looks up gRunbookIndex for enrichment
              │       ├── possible_causes (top 2)
              │       ├── first_check command
              │       ├── cn_template
              │       └── reschedule_policy
              └── Returns (code, message, enriched_suggestion, action) to ECRA
                                              │
                                              ▼
                                  Ops sees: "CRS services down on VM.
                                   Possible causes: CRS could not be started;
                                   DomU file corruption. First check:
                                   tail -n 200 $CELLTRACE/alert.log | grep Heartbeat"
```

---

## Proposed Changes

### Error Message Improvements

The following messages are improved based on patterns from the operations runbook. The principle: every message should answer both **what failed** and **what to look at first**.

| Error Code | Current Message | Improved Message |
|------------|----------------|-----------------|
| `0x03010000` | "Patch operation Status failed" | "Patch operation failed. Check thread logs for details." |
| `0x03010007` | "One ore more individual patch requests failed" | "One or more individual patch requests failed. Check per-node thread logs." |
| `0x030C0000` | "ASM Deactivation outcome is not set to yes on cells. Please refer MOS Note 2829056.1 for more details." | "ASM Deactivation outcome is not set to yes on cells. Check griddisk status and ASM rebalance state on affected cells. Refer MOS Note 2829056.1." |
| `0x03030008` | "Unable to establish Heartbeat on the cells. Not all CRS/DB services are up on DomU." | "Unable to establish Heartbeat on cells. Verify CRS/DB services on DomU and check DcsPing status from OneView." |
| `0x03030027` | "CRS is disabled on DomU and further crs validations will be skipped." | "CRS is disabled on DomU — further CRS validations will be skipped. Verify no issues at dom0 level before rescheduling." |
| `0x03030024` | "Invalid CRS HOME on DomU." | "Invalid CRS HOME on DomU. Verify CRS software is correctly installed in the crs_home directory." |
| `0x0301003D` | *(missing — falls back to generic error)* | "No action required. Target is already at the expected version." |
| `0x03070008` | "Critical cell services not running." | "Critical cell services not running after patching. Check cell server hardware health and verify image was applied successfully." |

---

### Framework Structural Improvements

#### Change 1: Define Error Action Constants

Replace all bare string error actions with named constants defined once at the top of the file.

#### Change 2: Use `PatchError` Named Tuple for All Entries

Replace `(message, action)` positional tuples with a named tuple. This makes all consumer code self-documenting.

#### Change 3: Flatten to a Single `PATCH_ERRORS` Dict

Replace 15+ separate dicts and the `mGetPatchkey()` routing function with a single unified dict. Error codes are globally unique hex strings — a single flat lookup works for all of them.

#### Change 4: Add Module-Level Validation Assert

Add a runtime assertion (runs at import time during tests) that checks every module-level hex constant has a corresponding entry in `PATCH_ERRORS`.

#### Change 5: Consolidate Format Functions

`ebPatchFormatBuildError` should delegate to `ebPatchFormatBuildErrorWithErrorAction` and drop the last return value, eliminating duplicate logic.

---

### Runbook Integration

#### New File: `infrapatching/core/infrapatching_runbook.py`

A companion dict `gRunbookIndex` maps error codes to structured runbook metadata. This keeps `infrapatcherror.py` focused on error definitions while making runbook data programmatically accessible.

**Fields per entry:**

| Field | Type | Description |
|-------|------|-------------|
| `possible_causes` | `list[str]` | Top reasons this error occurs, from ops runbook |
| `first_check` | `str` | The first diagnostic command ops should run |
| `reschedule_policy` | `str` | One of: `reschedule_after_14_days`, `retry_mr`, `send_cn_reschedule_after_14_days` |
| `cn_template` | `str \| None` | Customer notification template reference (e.g., `"Exadata-3ac"`) |
| `sample_ticket` | `str \| None` | Reference DBAASOPS ticket for precedent |
| `customer_action_required` | `bool` | Whether customer needs to take action to resolve |

The dispatcher logs this data on failure, giving ops an immediate pointer to the runbook without Confluence access.

---

## Sample Implementation

### Step 1: Add `PatchError` Named Tuple and Error Action Constants

File: `infrapatching/core/infrapatcherror.py`

```python
from collections import namedtuple

# Error action constants — prevents typo bugs
EA_FAIL_DONTSHOW   = "FAIL_DONTSHOW_PAGE_ONCALL"
EA_FAIL_AND_SHOW   = "FAIL_AND_SHOW"
EA_RETRY_SAME      = "RETRY_WITH_SAME_TOKEN"
EA_RETRY_DIFFERENT = "RETRY_WITH_DIFFERENT_TOKEN"

# Typed error entry — replaces raw (message, action) tuples
PatchError = namedtuple('PatchError', ['message', 'action'])
```

---

### Step 2: Flatten to Single `PATCH_ERRORS` Dict

File: `infrapatching/core/infrapatcherror.py`

```python
PATCH_ERRORS = {

    # --- Generic / Dispatcher (0x0301xxxx) ---
    "0x00000000": PatchError("Patch operation successful. No further action required.", ""),
    "0x03010000": PatchError("Patch operation failed. Check thread logs for details.", EA_FAIL_DONTSHOW),
    "0x03010001": PatchError("Required patch files not found. Verify patch files are staged at the expected location.", EA_FAIL_DONTSHOW),
    "0x03010003": PatchError("System is busy. Please retry the operation after some time.", EA_FAIL_DONTSHOW),
    "0x03010005": PatchError("Patch request timed out. Check individual requests.", EA_FAIL_DONTSHOW),
    "0x03010007": PatchError("One or more individual patch requests failed. Check per-node thread logs.", EA_FAIL_DONTSHOW),
    "0x0301003D": PatchError("No action required. Target is already at the expected version.", EA_FAIL_DONTSHOW),
    # ... all remaining codes follow same pattern ...

    # --- Dom0 Patch (0x0303xxxx) ---
    "0x03030008": PatchError("Unable to establish Heartbeat on cells. Verify CRS/DB services on DomU and check DcsPing status.", EA_FAIL_DONTSHOW),
    "0x03030024": PatchError("Invalid CRS HOME on DomU. Verify CRS software is correctly installed in the crs_home directory.", EA_FAIL_DONTSHOW),
    "0x03030027": PatchError("CRS is disabled on DomU — further CRS validations will be skipped. Verify no issues at dom0 level.", EA_FAIL_AND_SHOW),

    # --- ASM (0x030Cxxxx) ---
    "0x030C0000": PatchError("ASM Deactivation outcome not set to yes on cells. Check griddisk status and ASM rebalance state. Refer MOS Note 2829056.1.", EA_FAIL_DONTSHOW),

    # --- CPS (0x030Fxxxx) --- now consistent tuples, not plain strings
    "0x030F0004": PatchError("CPS operation failed.", EA_FAIL_DONTSHOW),
    "0x030F0006": PatchError("CPS patch exception detected.", EA_FAIL_DONTSHOW),
}
```

---

### Step 3: Remove `mGetPatchkey()` and Update Lookup Function

File: `infrapatching/core/infrapatcherror.py`

```python
def ebPatchFormatBuildErrorWithErrorAction(aErrorCode, aSuggestionCode=None, aTargetTypes=None):
    """
    Returns a formatted (code, message, suggestion, error_action) tuple for the
    given error code. Enriches suggestion with runbook data if available.
    """
    _error_action = EA_FAIL_DONTSHOW  # safe default

    _entry = PATCH_ERRORS.get(aErrorCode)
    if not _entry:
        ebLogInfo(f"Error code {aErrorCode} not found in PATCH_ERRORS. Returning generic error.")
        _entry = PATCH_ERRORS.get("0x03010000")
        aErrorCode = "0x03010000"

    _error_description = _entry.message
    _error_action = _entry.action

    # For DomU targets, override action for specific generic codes
    if aTargetTypes and (PATCH_DOMU in aTargetTypes) and aErrorCode in gDomUGenericErrorAsFailAndShow:
        _error_action = EA_FAIL_AND_SHOW
        ebLogInfo(f"Overriding error action to FAIL_AND_SHOW for code {aErrorCode} on DomU target")

    # Enrich suggestion with runbook data if no caller-supplied suggestion
    if not aSuggestionCode:
        _runbook = gRunbookIndex.get(aErrorCode)
        if _runbook:
            _causes = "; ".join(_runbook["possible_causes"][:2])
            aSuggestionCode = f"Possible causes: {_causes}. First check: {_runbook['first_check']}"

    ebLogInfo(f"Error Action is {_error_action} for Error Code {aErrorCode}")
    ebLogInfo(f"Error description is {_error_description}")

    return (str(aErrorCode), str(_error_description), str(aSuggestionCode), _error_action)


def ebPatchFormatBuildError(aErrorCode, aSuggestionCode=None, aComment=None):
    """Delegates to ebPatchFormatBuildErrorWithErrorAction, drops error_action return value."""
    _code, _msg, _suggestion, _ = ebPatchFormatBuildErrorWithErrorAction(aErrorCode, aSuggestionCode)
    return (_code, _msg, _suggestion)
```

---

### Step 4: Add Module-Level Validation

File: `infrapatching/core/infrapatcherror.py` (at the bottom of the file)

```python
# Validate all hex error code constants have an entry in PATCH_ERRORS.
# This runs at import time and will fail tests immediately if a constant is defined
# without a corresponding dict entry (e.g., NO_ACTION_REQUIRED scenario).
import re as _re
_defined_hex_codes = {
    v for v in globals().values()
    if isinstance(v, str) and _re.match(r'^0x[0-9a-fA-F]{8}$', v)
}
_missing_from_dict = _defined_hex_codes - set(PATCH_ERRORS)
assert not _missing_from_dict, (
    f"Error codes defined as constants but missing from PATCH_ERRORS: {_missing_from_dict}. "
    f"Add an entry to PATCH_ERRORS for each."
)
```

---

### Step 5: Create `infrapatching_runbook.py`

File: `infrapatching/core/infrapatching_runbook.py`

```python
#
# $Header: ecs/exacloud/exabox/infrapatching/core/infrapatching_runbook.py /main/1 2026/03/09 00:00:00 jyotdas Exp $
#
# infrapatching_runbook.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#
#    NAME
#      infrapatching_runbook.py - Programmatic index of ops runbook entries per error code
#    DESCRIPTION
#      Maps infra patching error codes to structured runbook metadata including
#      possible causes, first diagnostic command, CN template, and reschedule policy.
#      This data mirrors the operations runbook maintained in Confluence and is used
#      to enrich error output surfaced in ECRA.
#
#    NOTES
#      When adding a new error code to infrapatcherror.py, add a corresponding
#      entry here if an ops runbook entry exists.
#
#    MODIFIED   (MM/DD/YY)
#    jyotdas     03/09/26 - Initial creation
#

# Reschedule policy constants
RESCHEDULE_AFTER_14_DAYS     = "reschedule_after_14_days"
SEND_CN_RESCHEDULE_14_DAYS   = "send_cn_reschedule_after_14_days"
RETRY_MR                     = "retry_mr"

gRunbookIndex = {

    # ASM Deactivation outcome not set to yes on cells
    # Runbook ref: DBAASOPS-329173
    "0x030C0000": {
        "possible_causes": [
            "Patching pre-check failed due to ASM disks offline from customer end",
            "Cell node did not complete successfully and ASM disks are offline",
            "ASM Deactivation outcome not set due to HDD or Flash disk fault",
            "ASM rebalance is running for a long time"
        ],
        "first_check": (
            "ecraEXATool.sh execmd -c $c -w cell -x "
            "'cellcli -e list griddisk attributes name,asmmodestatus,asmdeactivationoutcome'"
        ),
        "reschedule_policy": RESCHEDULE_AFTER_14_DAYS,
        "cn_template": "Exadata-3ac",
        "sample_ticket": "DBAASOPS-329173",
        "customer_action_required": False
    },

    # Unable to establish Heartbeat on cells — CRS/DB services not up on DomU
    # Runbook ref: DBAASOPS-395346
    "0x03030008": {
        "possible_causes": [
            "CRS could not be started on DomU",
            "DomU file system corruption",
            "CRS startup issue on DomU"
        ],
        "first_check": (
            "ecraEXATool.sh execmd -c $c -w cell -x "
            "'tail -n 200 $CELLTRACE/alert.log | grep Heartbeat -b1 -tail -10'"
        ),
        "reschedule_policy": RESCHEDULE_AFTER_14_DAYS,
        "cn_template": "Exadata-3h",
        "sample_ticket": "DBAASOPS-395346",
        "customer_action_required": False
    },

    # CRS services down on VM
    # Runbook ref: DBAASOPS-404449, DBAASOPS-382041
    "0x0305000F": {
        "possible_causes": [
            "CRS could not be started on DomU",
            "DomU file system or startup issue",
            "DcsPing service not working"
        ],
        "first_check": "ecraDBTool.sh showops -c $c",
        "reschedule_policy": RESCHEDULE_AFTER_14_DAYS,
        "cn_template": "Exadata-3h",
        "sample_ticket": "DBAASOPS-404449",
        "customer_action_required": False
    },

    # CRS is disabled on DomU
    # Runbook ref: DBAASOPS-369690
    "0x03030027": {
        "possible_causes": [
            "Customer disabled CRS auto-start on VM level"
        ],
        "first_check": "ecraDBTool.sh showops -c $c",
        "reschedule_policy": RESCHEDULE_AFTER_14_DAYS,
        "cn_template": "Exadata-3h",
        "sample_ticket": "DBAASOPS-369690",
        "customer_action_required": True   # Customer needs to re-enable CRS auto-start
    },

    # Critical cell services not running
    "0x03070008": {
        "possible_causes": [
            "Cell server did not come up after patching",
            "Hardware issue on cell node",
            "Software configuration issue",
            "Image not applied correctly"
        ],
        "first_check": "cellcli -e list cell detail",
        "reschedule_policy": RETRY_MR,
        "cn_template": None,
        "sample_ticket": None,
        "customer_action_required": False
    },

    # Invalid CRS HOME on DomU
    # Runbook ref: Exadata-3h
    "0x03030024": {
        "possible_causes": [
            "CRS software not correctly installed in the crs_home directory",
            "Missing essential CRS config files, libraries, or executables"
        ],
        "first_check": (
            "grep -i error "
            "/u01/app/oracle/admin/exacloud/log/threads/*/<wf_uuid>_cluctrl.patch_dom0.log"
        ),
        "reschedule_policy": RESCHEDULE_AFTER_14_DAYS,
        "cn_template": "Exadata-3h",
        "sample_ticket": None,
        "customer_action_required": False
    },

    # Execution of custom plugin script for Guest VM failed
    "0x030B0003": {
        "possible_causes": [
            "Custom plugin script execution failed on Guest VM"
        ],
        "first_check": "ecraDBTool.sh showops -c $c",
        "reschedule_policy": RETRY_MR,
        "cn_template": None,
        "sample_ticket": None,
        "customer_action_required": False
    },
}
```

---

### Step 6: Log Runbook Guidance in Dispatcher on Failure

File: `infrapatching/core/cludispatcher.py`

In `mAddDispatcherError` or the equivalent failure reporting path, add runbook logging:

```python
from exabox.infrapatching.core.infrapatching_runbook import gRunbookIndex

def mAddDispatcherError(self, aErrorCode, aErrorDetail):
    # ... existing error handling ...

    # Log runbook guidance for this error code to help ops triage faster
    _runbook = gRunbookIndex.get(aErrorCode)
    if _runbook:
        self.mPatchLogInfo(
            f"Runbook guidance for {aErrorCode}: "
            f"CN={_runbook.get('cn_template', 'N/A')}, "
            f"Reschedule={_runbook.get('reschedule_policy', 'N/A')}, "
            f"CustomerAction={_runbook.get('customer_action_required', False)}, "
            f"FirstCheck={_runbook.get('first_check', 'N/A')}"
        )
        if _runbook.get("sample_ticket"):
            self.mPatchLogInfo(f"Reference ticket: {_runbook['sample_ticket']}")
```

**Example output in ECRA thread log after this change:**

```
INFO - Runbook guidance for 0x03030008:
       CN=Exadata-3h, Reschedule=reschedule_after_14_days,
       CustomerAction=False,
       FirstCheck=ecraEXATool.sh execmd -c $c -w cell -x 'tail -n 200 $CELLTRACE/alert.log | grep Heartbeat -b1 -tail -10'
INFO - Reference ticket: DBAASOPS-395346
```

---

### Step 7: Unit Tests

File: `exatest/infrapatching/core/tests_infrapatcherror.py`

```python
#!/bin/python
#
# tests_infrapatcherror.py
#
# Copyright (c) 2026, Oracle and/or its affiliates.
#    NAME
#      tests_infrapatcherror.py - Unit tests for infrapatcherror.py improvements
#    MODIFIED   (MM/DD/YY)
#    jyotdas     03/09/26 - Initial creation
#
import unittest
from unittest.mock import patch
from exabox.exatest.common.ebTestClucontrol import ebTestClucontrol
from exabox.log.LogMgr import ebLogInfo
from exabox.infrapatching.core.infrapatcherror import (
    PATCH_ERRORS, PatchError, EA_FAIL_DONTSHOW, EA_FAIL_AND_SHOW,
    ebPatchFormatBuildErrorWithErrorAction, ebPatchFormatBuildError
)
from exabox.infrapatching.core.infrapatching_runbook import gRunbookIndex

class ebTestInfraPatchError(ebTestClucontrol):
    SUCCESS_CODE = "0x00000000"

    @classmethod
    def setUpClass(cls):
        ebLogInfo("Starting classSetUp ebTestInfraPatchError")
        super(ebTestInfraPatchError, cls).setUpClass(aGenerateDatabase=True)

    def test_mAllPatchErrorEntriesAreNamedTuples(self):
        """All entries in PATCH_ERRORS must be PatchError namedtuples."""
        ebLogInfo("Running test: all PATCH_ERRORS entries are PatchError namedtuples")
        for _code, _entry in PATCH_ERRORS.items():
            self.assertIsInstance(_entry, PatchError,
                f"Entry for {_code} is not a PatchError namedtuple")

    def test_mCpsErrorEntriesHaveCorrectType(self):
        """CPS error entries must be PatchError tuples, not plain strings."""
        ebLogInfo("Running test: CPS error entries are PatchError tuples")
        _cps_codes = ["0x030F0004", "0x030F0006", "0x03100002"]
        for _code in _cps_codes:
            if _code in PATCH_ERRORS:
                self.assertIsInstance(PATCH_ERRORS[_code], PatchError,
                    f"CPS error {_code} is not a PatchError namedtuple")

    def test_mNoActionRequiredCodeHasDictEntry(self):
        """NO_ACTION_REQUIRED constant must have a dict entry."""
        ebLogInfo("Running test: NO_ACTION_REQUIRED has dict entry")
        from exabox.infrapatching.core.infrapatcherror import NO_ACTION_REQUIRED
        self.assertIn(NO_ACTION_REQUIRED, PATCH_ERRORS,
            f"{NO_ACTION_REQUIRED} defined as constant but missing from PATCH_ERRORS")

    def test_mFormatBuildErrorWithAction_knownCode_returnsCorrectFields(self):
        """ebPatchFormatBuildErrorWithErrorAction returns 4-tuple for known code."""
        ebLogInfo("Running test: format function returns 4-tuple for known error code")
        _result = ebPatchFormatBuildErrorWithErrorAction("0x03010000")
        self.assertEqual(len(_result), 4)
        _code, _msg, _suggestion, _action = _result
        self.assertEqual(_code, "0x03010000")
        self.assertIsNotNone(_msg)
        self.assertEqual(_action, EA_FAIL_DONTSHOW)

    def test_mFormatBuildErrorWithAction_unknownCode_returnsGenericFallback(self):
        """Unknown error code falls back to 0x03010000 without raising exception."""
        ebLogInfo("Running test: unknown error code returns generic fallback")
        _result = ebPatchFormatBuildErrorWithErrorAction("0x99990000")
        _code, _msg, _, _action = _result
        self.assertEqual(_code, "0x03010000")
        self.assertEqual(_action, EA_FAIL_DONTSHOW)

    def test_mFormatBuildError_delegatesToFunctionWithAction(self):
        """ebPatchFormatBuildError returns 3-tuple (delegates to 4-tuple function)."""
        ebLogInfo("Running test: ebPatchFormatBuildError returns 3-tuple")
        _result = ebPatchFormatBuildError("0x03010000")
        self.assertEqual(len(_result), 3)

    def test_mRunbookIndexEntriesHaveRequiredFields(self):
        """Every gRunbookIndex entry must have all required fields."""
        ebLogInfo("Running test: gRunbookIndex entries have required fields")
        _required_fields = ["possible_causes", "first_check", "reschedule_policy",
                            "cn_template", "customer_action_required"]
        for _code, _entry in gRunbookIndex.items():
            for _field in _required_fields:
                self.assertIn(_field, _entry,
                    f"gRunbookIndex entry for {_code} missing field '{_field}'")

    def test_mRunbookIndexCodesExistInPatchErrors(self):
        """All error codes in gRunbookIndex must exist in PATCH_ERRORS."""
        ebLogInfo("Running test: gRunbookIndex codes exist in PATCH_ERRORS")
        for _code in gRunbookIndex:
            self.assertIn(_code, PATCH_ERRORS,
                f"gRunbookIndex has entry for {_code} but it is missing from PATCH_ERRORS")

    def test_mSuggestionEnrichedFromRunbook_whenNoCallerSuggestion(self):
        """Suggestion field is enriched from gRunbookIndex when caller passes no suggestion."""
        ebLogInfo("Running test: suggestion enriched from runbook index")
        # 0x03030008 has a runbook entry with possible_causes
        _code, _msg, _suggestion, _action = ebPatchFormatBuildErrorWithErrorAction("0x03030008")
        if "0x03030008" in gRunbookIndex:
            self.assertIsNotNone(_suggestion)
            self.assertIn("Possible causes", _suggestion)

if __name__ == '__main__':
    unittest.main()
```

---

## Summary of Changes

| Change | File(s) | Effort | Priority |
|--------|---------|--------|----------|
| Fix CPS dicts to use `PatchError` tuples | `infrapatcherror.py` | Low | High |
| Fix typo in `0x03010007` | `infrapatcherror.py` | Trivial | High |
| Add missing dict entry for `NO_ACTION_REQUIRED` | `infrapatcherror.py` | Trivial | High |
| Define `EA_*` error action constants | `infrapatcherror.py` | Trivial | Medium |
| Introduce `PatchError` namedtuple | `infrapatcherror.py` | Low | Medium |
| Flatten to single `PATCH_ERRORS` dict, remove `mGetPatchkey()` | `infrapatcherror.py` | Medium | Medium |
| Add module-level validation assert | `infrapatcherror.py` | Low | Medium |
| Consolidate `ebPatchFormatBuildError` to delegate | `infrapatcherror.py` | Low | Low |
| Improve error messages per runbook analysis (table above) | `infrapatcherror.py` | Low | Medium |
| Create `infrapatching_runbook.py` with `gRunbookIndex` | New file | Medium | High |
| Log runbook guidance in dispatcher on failure | `cludispatcher.py` | Low | High |
| Add unit tests | `exatest/infrapatching/core/tests_infrapatcherror.py` | Medium | High |

---

## Clarifications

- Should `gRunbookIndex` be maintained in Python or migrated to a JSON/YAML file to allow non-developer updates by the ops team?
- The `cn_template` field currently holds a reference string (e.g., `"Exadata-3ac"`). Should this link to a full template lookup system, or remain a reference string for now?
- For `reschedule_policy`, should the values be actionable commands (e.g., trigger auto-reschedule) or remain informational log strings?
- Should `customer_action_required` influence the error action (e.g., force `FAIL_AND_SHOW` if `True`)?
- How should the `gRunbookIndex` be kept in sync with the Confluence runbook as new errors are added? Should the runbook page be auto-generated from `gRunbookIndex`?
- Are there error codes in the runbook not yet covered in `gRunbookIndex` that should be added before this ships?

---

## JIRAS

| JIRA ID | Title | Description |
|---------|-------|-------------|
| TBD | Fix structural issues in `infrapatcherror.py` | CPS dict inconsistency, typo fix, missing dict entry, magic strings |
| TBD | Flatten error dict and remove `mGetPatchkey()` routing | Consolidate 15+ dicts into single `PATCH_ERRORS`, introduce `PatchError` namedtuple |
| TBD | Improve error messages for operator effectiveness | Update messages per runbook analysis to include first diagnostic hint |
| TBD | Create `infrapatching_runbook.py` with `gRunbookIndex` | Programmatic ops runbook index with possible causes, first check, CN template, reschedule policy |
| TBD | Enrich ECRA error output with runbook guidance | Log CN template, reschedule policy, and first check command on failure in dispatcher |
| TBD | Add unit tests for error handling framework | Tests for `infrapatcherror.py` and `infrapatching_runbook.py` in `exatest/` |
