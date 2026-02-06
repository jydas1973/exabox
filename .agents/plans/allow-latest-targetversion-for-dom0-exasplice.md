# Feature: Allow LATEST TargetVersion for DOM0 ExaSplice Patching

**Requirements Source**: Conversation context

The following plan should be complete, but it's important that you validate documentation and codebase patterns and task sanity before you start implementing.

Pay special attention to naming of existing utils, types, and models. Import from the right files etc.

## Feature Description

Enable the `targetVersion` parameter to accept the literal string `"LATEST"` for DOM0 infrastructure patching operations when `exasplice` is set to `"yes"`. Currently, the system resolves `"LATEST"` to an actual version by scanning the filesystem in `mGetLatestPatchVersion()`. This feature bypasses both validation and resolution, allowing `"LATEST"` to pass through as a literal string throughout the patching workflow.

**Key Behavior Changes:**
1. When `targetVersion="LATEST"` + `targetType="dom0"` + `exasplice="yes"`: Skip validation, skip resolution, pass `"LATEST"` as literal string
2. All other cases: Existing behavior (resolve LATEST to actual version via `mGetLatestPatchVersion()`)

**Note:** The scenario `targetVersion="LATEST"` + `targetType="dom0"` + `exasplice!="yes"` will not occur in practice as `targetVersion` will always have an actual version value when `exasplice` is not `"yes"`. No explicit error handling is needed for this case.

## User Story

As an infrastructure patching operator
I want to specify `"LATEST"` as the targetVersion for DOM0 exasplice patching
So that the patching system can pass this literal value downstream without validation or resolution

## Problem Statement

Currently, when `TargetVersion` is set to `"LATEST"`, the `cludispatcher.py` automatically resolves it to an actual version by calling `mGetLatestPatchVersion()`, which scans the filesystem. For DOM0 exasplice patching scenarios, we need the ability to pass `"LATEST"` as a literal string without any validation or resolution.

## Solution Statement

1. Add a new utility function `mIsLatestTargetVersionAllowed()` in `utility.py` to check the three conditions (targetVersion, targetType, exasplice)
2. Modify `cludispatcher.py` to bypass LATEST resolution when conditions are met
3. Skip version format validation in `mExaspliceVersionPatternMatch()` when version is `"LATEST"` and conditions are met
4. Ensure patch, precheck, and rollback operations handle the literal `"LATEST"` string correctly

## Feature Metadata

**Feature Type**: Enhancement
**Estimated Complexity**: Low-Medium
**Primary Systems Affected**:
- `infrapatching/core/cludispatcher.py`
- `infrapatching/utils/utility.py`
- `infrapatching/handlers/targetHandler/dom0handler.py`

**Dependencies**: None (uses existing infrastructure)

---

## CONTEXT REFERENCES

### Relevant Codebase Files - IMPORTANT: YOU MUST READ THESE FILES BEFORE IMPLEMENTING!

**Core LATEST Resolution Logic:**
- `infrapatching/core/cludispatcher.py` (lines 878-892) - Why: Contains the LATEST resolution logic that needs conditional bypass
- `infrapatching/core/cludispatcher.py` (lines 2249-2286) - Why: `mGetLatestPatchVersion()` method that resolves LATEST

**ExaSplice Detection:**
- `infrapatching/handlers/generichandler.py` (lines 2408-2420) - Why: `mIsExaSplice()` method pattern to follow
- `infrapatching/core/cludispatcher.py` (lines 2029-2032) - Why: How exasplice is extracted from AdditionalOptions

**Version Validation:**
- `infrapatching/utils/utility.py` (lines 1058-1068) - Why: `mQuarterlyVersionPatternMatch()` and `mExaspliceVersionPatternMatch()` patterns
- `infrapatching/handlers/targetHandler/dom0handler.py` (line 730) - Why: Where exasplice version pattern is validated

**Constants:**
- `infrapatching/utils/constants.py` (lines 210-214) - Why: Task type constants (TASK_PATCH, TASK_PREREQ_CHECK, TASK_ROLLBACK)
- `infrapatching/utils/constants.py` (lines 222-241) - Why: Target type constants (PATCH_DOM0)

**Test Patterns:**
- `exatest/infrapatching/core/tests_cludispatcher.py` - Why: Test patterns for cludispatcher
- `exatest/infrapatching/tests_generichandler.py` - Why: Test patterns for generichandler

### New Files to Create

- `exatest/infrapatching/utils/tests_utility_latest_version.py` - Unit tests for the new LATEST version utility function

### Relevant Documentation

No external documentation required. All patterns are derived from the existing codebase.

### Patterns to Follow

**Naming Conventions:**
- Functions: `mFunctionName()` prefix with `m`
- Constants: `UPPER_SNAKE_CASE`

**Logging Pattern (f-strings in infrapatching):**
```python
self.mPatchLogInfo(f"Condition met: targetVersion={_version}, targetType={_target}, exasplice={_exasplice}")
```

**Version Check Pattern (from utility.py):**
```python
def mExaspliceVersionPatternMatch(version):
    regex = r'^\d{6}(\.\d+)?$'
    pattern = re.compile(regex)
    return bool(pattern.fullmatch(version))
```

**ExaSplice Check Pattern (from generichandler.py):**
```python
def mIsExaSplice(self):
    if self.__additional_options and 'exasplice' in self.__additional_options[0] \
       and self.__additional_options[0]['exasplice']:
        if self.__additional_options[0]['exasplice'].lower() == 'yes':
            return True
    else:
        return False
```

---

## IMPLEMENTATION PLAN

### Phase 1: Foundation - Utility Function

Create a utility function to check if LATEST is allowed.

**Tasks:**
- Create `mIsLatestTargetVersionAllowed()` function in `utility.py`

### Phase 2: Core Implementation - Bypass LATEST Resolution

Modify the dispatcher to conditionally bypass LATEST resolution.

**Tasks:**
- Modify `mParsePatchJson()` in `cludispatcher.py` to check conditions before resolving LATEST

### Phase 3: Handler Integration

Ensure handlers properly handle LATEST as literal string.

**Tasks:**
- Update `dom0handler.py` to skip version pattern validation when LATEST is passed with valid conditions

### Phase 4: Testing & Validation

Create comprehensive unit tests.

**Tasks:**
- Create unit tests for the new utility function
- Create unit tests for cludispatcher LATEST handling

---

## STEP-BY-STEP TASKS

IMPORTANT: Execute every task in order, top to bottom. Each task is atomic and independently testable.

### Task 1: CREATE utility function `mIsLatestTargetVersionAllowed()` in `infrapatching/utils/utility.py`

- **IMPLEMENT**: Add new function after `mExaspliceVersionPatternMatch()` (after line 1068)
  ```python
  def mIsLatestTargetVersionAllowed(target_version, target_type, exasplice):
      """
      Check if LATEST targetVersion is allowed based on conditions.
      LATEST is allowed only for DOM0 with exasplice='yes'.

      Args:
          target_version: The target version string
          target_type: The target type (dom0, domu, cell, etc.)
          exasplice: The exasplice value from AdditionalOptions

      Returns:
          True if LATEST is allowed (dom0 + exasplice=yes)
          False otherwise
      """
      if target_version and target_version.upper() == 'LATEST':
          if target_type and target_type.lower() == PATCH_DOM0:
              if exasplice and exasplice.lower() == 'yes':
                  return True
      return False
  ```
- **PATTERN**: Follow `mExaspliceVersionPatternMatch()` pattern at lines 1064-1068
- **IMPORTS**: Add `from exabox.infrapatching.utils.constants import PATCH_DOM0` at top of file (if not already present)
- **GOTCHA**: Handle None values for all parameters with proper null checks
- **VALIDATE**: `python -c "from exabox.infrapatching.utils.utility import mIsLatestTargetVersionAllowed; print(mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'yes'))"`

### Task 2: UPDATE `mParsePatchJson()` in `infrapatching/core/cludispatcher.py`

- **IMPLEMENT**: Modify LATEST resolution logic at lines 878-892 to check conditions
  ```python
  # Get target version
  if 'TargetVersion' in _entry:
      # Bug-26830429 - Evaluate the available latest version
      if _entry['TargetVersion'].upper() == 'LATEST':
          # Check if LATEST is allowed as literal (dom0 + exasplice=yes)
          _exasplice_value = None
          if 'AdditionalOptions' in _entry and _entry['AdditionalOptions'] and 'exasplice' in _entry['AdditionalOptions'][0]:
              _exasplice_value = _entry['AdditionalOptions'][0]['exasplice']

          # Get target types from entry
          _target_types = _entry.get('TargetType', [])
          _is_dom0_only = len(_target_types) == 1 and _target_types[0].lower() == PATCH_DOM0

          if _is_dom0_only and _exasplice_value and _exasplice_value.lower() == 'yes':
              # Allow LATEST as literal string for dom0 + exasplice=yes
              self.mPatchLogInfo(f"Allowing LATEST as literal targetVersion for DOM0 exasplice patching")
              _version = _entry['TargetVersion']
          else:
              # All other cases: resolve LATEST to actual version (existing behavior)
              self.mPatchLogInfo("Finding the LATEST target version.")
              _version = self.mGetLatestPatchVersion()
      else:
          _version = _entry['TargetVersion']
          self.mPatchLogInfo(f"The TargetVersion selected: {_version} ")
  ```
- **PATTERN**: Follow existing conditional logic pattern at lines 878-892
- **IMPORTS**: Ensure `PATCH_DOM0` is imported from constants (should already be present)
- **GOTCHA**: Preserve existing behavior for non-dom0 targets and when exasplice is not 'yes'
- **VALIDATE**: Python syntax check; unit test with mock payload

### Task 3: UPDATE dom0handler.py to handle LATEST in version pattern matching

- **IMPLEMENT**: Modify version validation at line 730 to skip pattern check for LATEST when exasplice=yes
  ```python
  _target_version = self.mGetTargetVersion()
  if _target_version.upper() == 'LATEST' and self.mIsExaSplice():
      # LATEST allowed for dom0 exasplice - skip version pattern validation
      self.mPatchLogInfo(f"Processing LATEST targetVersion for DOM0 exasplice patching")
      # Continue with existing logic for exasplice nodes
      _list_of_dom0s_where_exasplice_can_be_applied = self.mGetListOfDom0sWhereExasplicePatchCanBeApplied()
  elif mExaspliceVersionPatternMatch(_target_version):
      # Existing exasplice version pattern logic
      ...
  ```
- **PATTERN**: Follow existing conditional pattern in dom0handler.py
- **IMPORTS**: None new required
- **GOTCHA**: Ensure LATEST check happens before pattern matching to avoid regex failure; only skip when exasplice is also yes
- **VALIDATE**: Unit test with mock dom0handler

### Task 4: CREATE unit tests in `exatest/infrapatching/utils/tests_utility_latest_version.py`

- **IMPLEMENT**: Create new test file with comprehensive tests
  ```python
  #!/bin/python
  #
  # $Header: ecs/exacloud/exabox/exatest/infrapatching/utils/tests_utility_latest_version.py /main/1 2026/02/06 username Exp $
  #
  # tests_utility_latest_version.py
  #
  # Copyright (c) 2025, 2026, Oracle and/or its affiliates.
  #
  #    NAME
  #      tests_utility_latest_version.py - Unit tests for LATEST version validation
  #
  #    DESCRIPTION
  #      Unit tests for mIsLatestTargetVersionAllowed utility function
  #
  #    NOTES
  #      Tests the LATEST targetVersion handling for DOM0 exasplice patching
  #
  #    MODIFIED   (MM/DD/YY)
  #    <author>    02/06/26 - Creation
  #
  import unittest
  from exabox.infrapatching.utils.utility import mIsLatestTargetVersionAllowed

  class TestLatestVersionValidation(unittest.TestCase):

      def test_mIsLatestTargetVersionAllowed_valid_case(self):
          """Test LATEST allowed with dom0 + exasplice=yes"""
          result = mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'yes')
          self.assertTrue(result)

      def test_mIsLatestTargetVersionAllowed_case_insensitive_latest(self):
          """Test case insensitivity for LATEST"""
          self.assertTrue(mIsLatestTargetVersionAllowed('latest', 'dom0', 'yes'))
          self.assertTrue(mIsLatestTargetVersionAllowed('Latest', 'dom0', 'yes'))
          self.assertTrue(mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'yes'))

      def test_mIsLatestTargetVersionAllowed_case_insensitive_dom0(self):
          """Test case insensitivity for dom0"""
          self.assertTrue(mIsLatestTargetVersionAllowed('LATEST', 'DOM0', 'yes'))
          self.assertTrue(mIsLatestTargetVersionAllowed('LATEST', 'Dom0', 'yes'))

      def test_mIsLatestTargetVersionAllowed_case_insensitive_exasplice(self):
          """Test case insensitivity for exasplice"""
          self.assertTrue(mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'YES'))
          self.assertTrue(mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'Yes'))

      def test_mIsLatestTargetVersionAllowed_returns_false_for_exasplice_no(self):
          """Test returns False with dom0 + exasplice=no"""
          result = mIsLatestTargetVersionAllowed('LATEST', 'dom0', 'no')
          self.assertFalse(result)

      def test_mIsLatestTargetVersionAllowed_returns_false_for_exasplice_none(self):
          """Test returns False with dom0 + exasplice=None"""
          result = mIsLatestTargetVersionAllowed('LATEST', 'dom0', None)
          self.assertFalse(result)

      def test_mIsLatestTargetVersionAllowed_returns_false_for_domu(self):
          """Test returns False with domu target type"""
          result = mIsLatestTargetVersionAllowed('LATEST', 'domu', 'yes')
          self.assertFalse(result)

      def test_mIsLatestTargetVersionAllowed_returns_false_for_cell(self):
          """Test returns False with cell target type"""
          result = mIsLatestTargetVersionAllowed('LATEST', 'cell', 'yes')
          self.assertFalse(result)

      def test_mIsLatestTargetVersionAllowed_returns_false_for_switch(self):
          """Test returns False with switch target type"""
          result = mIsLatestTargetVersionAllowed('LATEST', 'switch', 'yes')
          self.assertFalse(result)

      def test_mIsLatestTargetVersionAllowed_returns_false_for_non_latest_version(self):
          """Test returns False for non-LATEST version string"""
          result = mIsLatestTargetVersionAllowed('25.1.0.0.0.250101', 'dom0', 'yes')
          self.assertFalse(result)

      def test_mIsLatestTargetVersionAllowed_returns_false_for_none_version(self):
          """Test returns False when version is None"""
          result = mIsLatestTargetVersionAllowed(None, 'dom0', 'yes')
          self.assertFalse(result)

      def test_mIsLatestTargetVersionAllowed_returns_false_for_none_target_type(self):
          """Test returns False when target_type is None"""
          result = mIsLatestTargetVersionAllowed('LATEST', None, 'yes')
          self.assertFalse(result)

      def test_mIsLatestTargetVersionAllowed_returns_false_for_empty_strings(self):
          """Test returns False for empty string parameters"""
          self.assertFalse(mIsLatestTargetVersionAllowed('', 'dom0', 'yes'))
          self.assertFalse(mIsLatestTargetVersionAllowed('LATEST', '', 'yes'))
          self.assertFalse(mIsLatestTargetVersionAllowed('LATEST', 'dom0', ''))

  if __name__ == '__main__':
      unittest.main()
  ```
- **PATTERN**: Follow test patterns from `tests_generichandler.py` and `tests_cludispatcher.py`
- **IMPORTS**: Standard unittest imports
- **GOTCHA**: Ensure tests cover all edge cases including None and empty string values
- **VALIDATE**: `cd exatest && python -m unittest infrapatching.utils.tests_utility_latest_version`

### Task 5: ADD unit tests for cludispatcher LATEST handling in `exatest/infrapatching/core/tests_cludispatcher.py`

- **IMPLEMENT**: Add test methods to existing test file
  ```python
  @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mLockPatchCmd', return_value=True)
  @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mUpdateStatusFromList')
  @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mGetLatestPatchVersion', return_value='25.1.0.0.0.250101')
  def test_mParsePatchJson_LATEST_dom0_exasplice_yes_bypasses_resolution(self, mock_get_latest, mock_update, mock_lock):
      """Test LATEST is NOT resolved for dom0 with exasplice=yes"""
      ebLogInfo("")
      ebLogInfo("Running unit test: LATEST targetVersion with dom0 + exasplice=yes should bypass resolution")
      _job = ebJobRequest("version", {})
      _patch_dispatcher = ebCluPatchDispatcher(aJob=_job)
      # Set up payload with LATEST + dom0 + exasplice=yes
      # Assert mGetLatestPatchVersion is NOT called
      # Assert version remains as 'LATEST' literal
      mock_get_latest.assert_not_called()
      ebLogInfo("Unit test executed successfully")

  @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mLockPatchCmd', return_value=True)
  @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mUpdateStatusFromList')
  @patch('exabox.infrapatching.core.cludispatcher.ebCluPatchDispatcher.mGetLatestPatchVersion', return_value='25.1.0.0.0.250101')
  def test_mParsePatchJson_LATEST_non_dom0_resolves_version(self, mock_get_latest, mock_update, mock_lock):
      """Test LATEST is resolved for non-dom0 targets (existing behavior)"""
      ebLogInfo("")
      ebLogInfo("Running unit test: LATEST targetVersion with cell should resolve to actual version")
      _job = ebJobRequest("version", {})
      _patch_dispatcher = ebCluPatchDispatcher(aJob=_job)
      # Set up payload with LATEST + cell + exasplice=yes
      # Assert mGetLatestPatchVersion IS called
      mock_get_latest.assert_called_once()
      ebLogInfo("Unit test executed successfully")
  ```
- **PATTERN**: Follow existing test patterns in the file (lines 66-80)
- **IMPORTS**: None new required
- **GOTCHA**: Use proper mocking to isolate the test; verify mGetLatestPatchVersion call behavior
- **VALIDATE**: `cd exatest && python exatest.py -run tests_cludispatcher`

---

## TESTING STRATEGY

### Unit Tests

Based on the project's `unittest` framework:

1. **Utility Function Tests** (`tests_utility_latest_version.py`)
   - Test `mIsLatestTargetVersionAllowed()` returns True for valid case (dom0 + exasplice=yes)
   - Test `mIsLatestTargetVersionAllowed()` returns False for invalid cases
   - Test case insensitivity (LATEST, latest, Latest; DOM0, dom0; YES, yes)
   - Test None and empty string handling for all parameters

2. **Dispatcher Tests** (`tests_cludispatcher.py`)
   - Test LATEST bypasses resolution for dom0 + exasplice=yes (mGetLatestPatchVersion NOT called)
   - Test LATEST resolves normally for non-dom0 targets (mGetLatestPatchVersion IS called)

3. **Handler Tests** (`tests_dom0handler.py`)
   - Test LATEST skips version pattern validation when exasplice=yes
   - Test existing behavior preserved for non-LATEST versions

### Integration Tests

- Test full patching workflow with LATEST + dom0 + exasplice=yes payload
- Verify LATEST passes through all three operations: precheck, patch, rollback

### Edge Cases

- `targetVersion = "LATEST"` (uppercase)
- `targetVersion = "latest"` (lowercase)
- `targetVersion = "Latest"` (mixed case)
- `exasplice = "YES"` / `"Yes"` (case variations)
- `exasplice = None` or missing from AdditionalOptions
- Multiple target types including dom0 (e.g., `["dom0", "cell"]`) - should use existing behavior

---

## VALIDATION COMMANDS

Execute every command to ensure zero regressions and 100% feature correctness.

### Level 1: Syntax & Style

```bash
# Python syntax check
python -m py_compile infrapatching/core/cludispatcher.py
python -m py_compile infrapatching/utils/utility.py
python -m py_compile infrapatching/handlers/targetHandler/dom0handler.py

# Pylint check (as per project standards)
pylint infrapatching/core/cludispatcher.py
pylint infrapatching/utils/utility.py
```

### Level 2: Unit Tests

```bash
# Run all infrapatching tests
cd exatest && python exatest.py -run -all infrapatching

# Run specific test files
cd exatest && python exatest.py -run tests_cludispatcher
cd exatest && python -m unittest infrapatching.utils.tests_utility_latest_version
```

### Level 3: Integration Tests

```bash
# Run full test suite
cd exatest && python exatest.py -run -all
```

### Level 4: Manual Validation

1. Create a test payload JSON with:
   - `TargetVersion: "LATEST"`
   - `TargetType: ["dom0"]`
   - `AdditionalOptions: [{"exasplice": "yes", ...}]`

2. Verify the version is NOT resolved (stays as "LATEST" literal)

3. Verify logs show: "Allowing LATEST as literal targetVersion for DOM0 exasplice patching"

---

## ACCEPTANCE CRITERIA

Feature-Specific Criteria:
- [ ] When `targetVersion="LATEST"` + `targetType="dom0"` + `exasplice="yes"`, the version is passed as literal "LATEST" without resolution
- [ ] When `targetVersion="LATEST"` + `targetType!="dom0"`, existing behavior (resolution) is preserved
- [ ] When `targetVersion="LATEST"` + `exasplice!="yes"`, existing behavior (resolution) is preserved
- [ ] The feature works for patch, precheck, and rollback operations
- [ ] Case insensitivity is handled for LATEST, dom0, and exasplice values

Technical Quality Criteria:
- [ ] All validation commands pass with zero errors
- [ ] Unit test coverage for new functions is complete
- [ ] Code follows project conventions (m prefix, f-strings in infrapatching, Oracle header)
- [ ] No regressions in existing functionality

---

## COMPLETION CHECKLIST

- [ ] All tasks completed in order
- [ ] Each task validation passed immediately
- [ ] All validation commands executed successfully
- [ ] Full test suite passes (unit + integration)
- [ ] No linting or type checking errors
- [ ] Manual testing confirms feature works
- [ ] Acceptance criteria all met
- [ ] Code reviewed for quality and maintainability

---

## NOTES

### Design Decisions

1. **Utility Function Location**: Placed in `utility.py` alongside existing version pattern functions for consistency

2. **Simplified Logic**: No explicit error handling for LATEST + dom0 + exasplice!=yes because this scenario won't occur in practice. The existing resolution behavior handles this case.

3. **Case Insensitivity**: All comparisons use `.upper()` or `.lower()` for consistency with existing codebase patterns

### Trade-offs

1. **Inline vs Utility Function**: Chose utility function approach for reusability and testability, even though the check could be inline in cludispatcher

### Risks

1. **Downstream Impact**: Components that consume targetVersion may need to handle "LATEST" as a special string - verify no downstream code expects a version format

2. **Multi-target Payloads**: If a payload contains `["dom0", "cell"]`, the current implementation will use existing behavior (resolve LATEST) since it's not "dom0 only"

### Future Considerations

1. If LATEST support needs to extend to other target types (domu, cell), the utility function is designed to be easily extensible
