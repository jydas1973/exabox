# Codex UT Orchestration

This directory provides a lightweight toolkit for generating unit tests across multiple Python modules in a single run. Use it when you want Codex to improve coverage for several code files within the same ADE view.

## 1. Configuration File (`config-template.json`)

Create your own config by copying the template:

```bash
cp config-template.json config-myview.json
```

Populate the JSON with one entry per code file inside the `targets` list:

```json
{
  "view_name": "<ADE_VIEW_NAME>",
  "targets": [
    {
      "code": "<REL_OR_ABS_PATH_TO_CODE>",
      "tests": {
        "primary": "<REL_OR_ABS_PATH_TO_PRIMARY_TEST>",
        "additional": [
          "<OPTIONAL_SUPPORTING_TEST_1>",
          "<OPTIONAL_SUPPORTING_TEST_2>"
        ]
      }
    }
  ]
}
```

### Field Notes
- **`code`** and **`tests.primary`** may be absolute paths or relative to `/scratch/<user>/view_storage/<ADE_VIEW_NAME>`.
- Add as many `targets` as needed; Codex will process them sequentially.
- Use `tests.additional` to list existing suites that already touch the code so coverage reruns include every relevant file.

## 2. Helper Script (`codex_ut_runner.py`)

Run the helper to verify path expansion, orchestrate Codex iterations, and (optionally) trigger coverage once Codex completes.

```bash
python3 codex_ut_runner.py --config config-myview.json --user <unix_user> --max-iterations 3 --execute
```

Flags:
- `--config`: required path to your JSON file.
- `--user`: overrides `$USER` when resolving `/scratch/<user>/view_storage`.
- `--base`: optional override for the view-storage root.
- `--max-iterations`: number of Codex passes per target (default 5).
- `--codex-timeout`: per-iteration timeout in seconds (default 3600).
- `--execute`: when present, runs the coverage command once per target after Codex finishes (`<VIEW_LOCATION>/ecs/exacloud/bin/python <VIEW_LOCATION>/ecs/exacloud/exabox/exatest/exatest.py -r -f <tests> --coverage`).

The runner logs Codex output, but the detailed branch and line-gap bookkeeping is delegated to the playbook (`CODEX_TEST_INSTRUCTIONS.md`), where Codex writes/refreshes `codex_ut_state.json` and `coverage_context.txt` each iteration.

## 3. Codex Workflow Expectations

When you provide Codex with the config (and after entering the view via `ade useview <ADE_VIEW_NAME> -exec bash`):
1. Codex parses every target, enumerates public methods, and inspects existing coverage artifacts.
2. For each target:
   - Verifies the test file is checked out (runs `ade co` if needed) and edits it **in place**.
   - Generates tests only for uncovered logic (`coverage_strategy: fill_gaps`) while keeping production code unmodified. All emitted unit tests must stay Python 3.6 compatible.
3. Codex never issues destructive commands and captures iteration logs plus final coverage numbers for each module.

## 4. Review & Delivery

After Codex finishes:
- Inspect modified test files (one per target) and the refreshed coverage reports under `ecs/exacloud/exabox/exatest/test_results/`.
- Use ADE commands (`ade status`, `ade diff`, `ade ci`) to review and deliver your changes.
- Update `config-myview.json` as new modules are added to ensure future runs remain comprehensive.

For the precise unit-test authoring procedure that Codex should follow during enhancement (enumeration, mocking, coverage loops, and reporting), see `CODEX_TEST_INSTRUCTIONS.md` in this directory.