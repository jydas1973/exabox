# Codex Unit Test Generation Playbook

Use this playbook with the files in this directory to run Codex inside the ADE view. You can work in either of two modes:

- **Config-driven (default):** Run the `codex_ut_runner.py` helper to read a multi-target config and enumerate test files to enhance.
- **Manual prompt:** Accept explicit file targets from the user and execute the same playbook steps without invoking the runner.

Codex should follow the guidance below—choose the workflow that matches how targets are provided and update the tests in place accordingly.

## 1. Environment Setup
1. Enter the view shell before running anything: `ade useview <ADE_VIEW_NAME> -exec bash`.
2. All paths must resolve under `/scratch/<user>/view_storage/<ADE_VIEW_NAME>`; never use `.ade_path` symlinks.
3. Remote execution prompts, SSH keys, and Expect scripts are **not** required—everything runs locally inside the view.

## 2. Configuration-Driven Targets (Runner Workflow)
1. The JSON configuration (`config-template.json` copy) lists every code/test pair under `targets`.
2. For each target:
   - Expand `code`, `tests.primary`, and `tests.additional` using `/scratch/<username>/view_storage/<VIEW_NAME>` if present.
   - Check whether the primary test file exists:
     - If yes, ensure it is checked out (`ade co <test file> -c "<Relevant comments>"`) and plan to append tests at the end.
     - If no, create `<primary>.py` (`ade mkelem <test file> -c "<Relevant comments>"` command can be used) and add tests.
3. Reference tests: use any two files in `ecs/exacloud/exabox/exatest` (e.g., `tests_cludiskgroups.py`, `tests_clustorage.py`) to match structure and mocking style.

4. Ignore below errors and warnings (during unit test execution):

   find: ‘/ade/<ADE_VIEW_NAME>/ecs/exacloud/bin/../packages/instantclient*’: No such file or directory
   /ade/<ADE_VIEW_NAME>/ecs/exacloud/opt/py3_venv/lib/python3.11/site-packages/paramiko/pkey.py:101: CryptographyDeprecationWarning: TripleDES has been moved to cryptography.hazmat.decrepit.ciphers.algorithms.TripleDES and will be removed from cryptography.hazmat.primitives.ciphers.algorithms in 48.0.0.
   “cipher”: algorithms.TripleDES,
   /ade/<ADE_VIEW_NAME>/ecs/exacloud/opt/py3_venv/lib/python3.11/site-packages/paramiko/transport.py:259: CryptographyDeprecationWarning: TripleDES has been moved to cryptography.hazmat.decrepit.ciphers.algorithms.TripleDES and will be removed from cryptography.hazmat.primitives.ciphers.algorithms in 48.0.0.
   “class”: algorithms.TripleDES,

5. Always do smoke test using the way mentioned in "## 6. Execution Loop (Local Only)" instruction.

## 2A. Manual Prompt Workflow
Use this path when the user supplies targets directly (e.g., inside a prompt) instead of via the runner.

1. Confirm each target includes both the code-under-test path and the desired primary test file. If any path is missing, ask the user to clarify before proceeding.
2. Normalize all provided paths to absolute locations inside `/scratch/<user>/view_storage/<ADE_VIEW_NAME>` and avoid `.ade_path` symlinks.
3. For each target:
   - Checkout the existing test file with `ade co <test file>` when it exists.
     - Always supply a descriptive comment: `ade co -c "Codex UT enhancement" <test file>` (no silent checkouts).
   - If the primary file does not exist, create `<primary>.py`, append tests there, and remind the user to check in after review.
4. Reuse the same reference test files (`tests_cludiskgroups.py`, `tests_clustorage.py`) to keep structure and mocking consistent.
5. Optionally mirror the runner config by jotting down a lightweight checklist (code file, primary tests, additional tests) so later reporting matches Section 6.
6. Never delete or rename existing code or test files.
7. Never modify the target code file.

## 3. Persistent Coverage History
The runner now captures per-target coverage snapshots for reuse across sessions.

1. Review `codex_ut_state.json` in this directory to see the most recent line coverage percentages and missing line numbers recorded for each target (baseline plus per-iteration checkpoints).
2. Include a short summary of the relevant history (coverage percentage + missing lines) so Codex can avoid retreading covered areas in `codex_ut_state.json`.
3. When using the runner, history should be injected automatically into Codex prompts as the “Historical coverage context” section from `codex_ut_state.json`.
4. If history becomes stale (e.g., the code under test changes substantially), remove the affected entry from `codex_ut_state.json` or delete the file before starting a new session.
5. Refer to `codex_ut_state.sample.json` in this directory for a commented example of the expected JSON layout, including how `history`, `last_coverage_pct`, and path keys should look.
6. The runner auto-creates an empty `codex_ut_state.json` the first time it runs if the file is missing, so manual setup is optional.
7. If a pre-existing state file lacks metadata (for example, a hand-crafted sample), the runner replaces it with an empty structure on first execution to ensure Codex starts with a clean slate.
8. After each iteration, record any remaining uncovered line numbers and branch arc identifiers in `last_missing_lines` and `last_missing_branches` and `history`. The runner interprets empty arrays as “nothing to do,” so keeping these fields up to date ensures the next pass can focus on the outstanding gaps.
9. Review the relevant coverage files under "ecs/exacloud/exabox/exatest/test_results/" to check covered lines and branches. The authoritative line/branch coverage figures must be read from `coverage_txt.suc` (per-target summary rows). Capture key values and notes in `coverage_context.txt` for use in subsequent iterations.
10. Treat `codex_ut_state.json` and `coverage_context.txt` as per-iteration scratchpads:
    - At the start of an iteration, export a cache directory for each target code file (`CACHE_ROOT=$(pwd)/codex_cache_<shortNameTargetCodeFile>`) and `mkdir -p "$CACHE_ROOT"`; change into that folder before reading the scratch files so all temporary artifacts live in the cache for a target code file.
    - Read their contents, present a summary to the user, then delete the files to avoid stale data.
    - After generating new results, recreate both files inside `$CACHE_ROOT`, log the new contents, and leave them there for the next iteration.
11. Create any additional temporary artifacts (generation prompts, coverage annotations, branch checklists, etc.) inside `$CACHE_ROOT`. Never write scratch files directly under `$ADE_VIEW_ROOT` or the module directories.

## 4. Coverage Planning
1. Parse the target code file with AST and emit a checklist of every public class, its public methods (including inherited overrides), `@property` accessors, and `get_/set_` helpers.
2. For each method on the checklist, enumerate the full branch matrix (success, failure, retries/timeouts, option flags, None/edge cases) before generating tests.
3. Build a plan covering node-command mock requirements (Dom0, DomU, Cell, VM, Switch, Local) and identify which references in `ecs/exacloud/exabox/exatest` illustrate the required mocking style.
4. Consult the latest history entry for the target (either from `codex_ut_state.json` or from the runner’s prompt) to understand which methods/paths remain untested before drafting new test cases.
5. Branch expectations: even if a method already has unit-test coverage, confirm every branch (success, failure, retries, exception paths) has tests. Treat branch coverage as mandatory for **every** method on the checklist. If an existing test leaves a branch unexecuted, append new unit tests to exercise it and document any remaining gap when it truly cannot be closed.

## 5. Test Authoring Rules
1. Follow `ebTestClucontrol` patterns; mock all external systems (DBaaS, cellcli, subprocess, filesystem, time) before instantiation.
2. Match method signatures in mocks; return realistic objects and assert calls.
3. Cover branch variants: success, failure, retries, option flags, partial failures, validation, polling/timeouts, and logging fallbacks.
4. For properties/getters/setters: test default, set/get roundtrip, and invalid input.
5. Annotate new tests with `# Auto-generated test for <method>`; keep imports at the top, no method-local imports.
6. Maintain Python 3.6 compatibility—no walrus operator, f-string debug specifiers, dataclasses without backports, etc.
7. When the code under test issues commands to Dom0, DomU, Cell, VM, Switch, or Local nodes, mirror the regex-based mocking demonstrated in `ecs/exacloud/exabox/exatest/common/ebTestClucontrol.py` and the reference tests (`tests_cludiskgroups.py`, `tests_clustorage.py`, `tests_cluelasticcells.py`). Ensure each command path (success, partial failure, retries) is covered with realistic mock outputs and assertions on fan-out behavior.

## 6. Execution Loop (Local Only)
1. After generating or appending tests, smoke-test the primary suite without coverage to ensure the new cases pass (always use the view’s Python at `<VIEW_LOCATION>/ecs/exacloud/bin/python`; never call binaries from `/ecs/exacloud/opt/py3_venv/` or other virtual environments):
   ```bash
   /scratch/<username>/view_storage/<VIEW_NAME>/ecs/exacloud/bin/python /scratch/<username>/view_storage/<VIEW_NAME>/ecs/exacloud/exabox/exatest/exatest.py -r -f <primary_test_path>
   ```
   _Example_: `/scratch/aararora/view_storage/aararora_UTClineCludiskgroups/ecs/exacloud/bin/python /scratch/aararora/view_storage/aararora_UTClineCludiskgroups/ecs/exacloud/exabox/exatest/exatest.py -r -f /scratch/aararora/view_storage/aararora_UTClineCludiskgroups/ecs/exacloud/exabox/exatest/ovm/tests_cludiskgroups.py`

If the smoke test fail for pre-existing tests - always resolve the previous failing tests and rerun smoke test to check if the tests are executing fine.

For any hang, run the test under a 120 seconds timeout (timeout 120s <cmd>); if it exits 124, read the latest logs in exacloud.log under latest /ade/<VIEW_NAME>/ecs/exacloud/log/exatest/<uuid> folder and log the last test header or repeated log pattern that indicates the hang, then proceed with fixes and retry the smoke test (DO NOT ASK - Fix the hang issue).

2. Once the iteration’s test plan is complete (all branches exercised), run the full coverage command with the primary + additional suites using the same view Python path (this can take upto 10 minutes):
   ```bash
   /scratch/<username>/view_storage/<VIEW_NAME>/ecs/exacloud/bin/python /scratch/<username>/view_storage/<VIEW_NAME>/ecs/exacloud/exabox/exatest/exatest.py -r -f <primary_and_additional_tests> --coverage
   ```
   _Example_: `/scratch/aararora/view_storage/aararora_UTClineCludiskgroups/ecs/exacloud/bin/python /scratch/aararora/view_storage/aararora_UTClineCludiskgroups/ecs/exacloud/exabox/exatest/exatest.py -r -f /scratch/aararora/view_storage/aararora_UTClineCludiskgroups/ecs/exacloud/exabox/exatest/ovm/tests_cludiskgroups.py --coverage`
3. Parse failures and coverage reports to identify missed lines/branches, then regenerate only what is needed.
   - Use the state file or the runner’s historical context to focus on the still-missing line numbers and avoid duplicating coverage work already captured in earlier iterations.
   - Coverage thresholds apply to the **target code file**, not the accompanying test modules. Always base decisions on coverage data keyed to the code path.
   - Meet both line and branch thresholds (default ≥80% each unless overridden). Treat outstanding branch arcs as first-class gaps to close.
4. Repeat until:
   - Line coverage ≥ `goal.min_line_coverage` (default 0.8).
   - All mandatory methods have positive + negative coverage.
   - No unhandled errors remain.

## 7. Reporting & Output
1. Enhanced files must preserve existing tests and append new ones at the end; new files should be ready to replace originals after review.
2. Document any methods that remain uncovered with explicit reasons tied to code facts (line numbers, dynamic dispatch, etc.).
3. Provide final summary: methods covered, methods pending (if any), coverage statistics, and test command used. Reference entries from `codex_ut_state.json` when describing the evolution of coverage so the user can compare against prior runs.
   - Call out the final line coverage for the code-under-test, quoting the exact figure from `coverage_txt.suc`, and distinguish it from any test module coverage reported by tooling.
   - Describe branch coverage qualitatively (for example, “all branches exercised” or “branches still missing: ...”) based on your branch checklist and `coverage_context.txt`. Do not quote branch percentages unless `coverage_txt.suc` explicitly provides them.
   - Enumerate remaining branch gaps (if any) per method, with line numbers, so follow-up iterations can focus on them.
4. Leave files checked out in ADE so the user can review, diff, and submit with `ade status/diff/ci`.
