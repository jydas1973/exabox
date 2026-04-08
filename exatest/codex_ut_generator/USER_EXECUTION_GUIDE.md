# Quick Start: Multi-Target Codex UT Flow

1. **Clone the template config**  
   ```bash
   cp config-template.json config-ut.json
   ```
   - For each code file you want covered, add an entry under `targets`.
   - Fill in `code`, `tests.primary`, and any supporting suites in `tests.additional`.
   - Leave `coverage_strategy: "fill_gaps"`, `ade_checkout: true`, and `allow_rm: false` unless you have explicit reasons to change them.

2. **Run the helper**
   ```bash
   python3 codex_ut_runner.py --config config-ut.json --user <unix_user> --max-iterations 3 --execute
   ```
   The script wraps commands in `ade useview` when needed, so you can invoke it from outside the view. After the final Codex pass, it will run the coverage command for each target.

3. **Hand off to Codex**
   Provide Codex with the config path. For each target it will:
   - Enumerate public methods, read `codex_ut_state.json`/`coverage_context.txt`, and plan coverage gaps.
   - Check out the primary test file (using `ade co -c "Codex UT enhancement"`) if necessary, then append tests in place.
   - Keep production code untouched, enforce Python 3.6 compatibility, and avoid destructive commands.
   - Refresh `codex_ut_state.json` and `coverage_context.txt` after each iteration so the next pass starts clean.

   Codex itself runs coverage at the beginning (iteration 1) to capture baseline context, and again after it finalizes tests for the iteration.

4. **Review and deliver**  
   Inspect the modified test files plus updated coverage HTML/TXT. Use ADE commands (`ade status`, `ade diff`, `ade ci`, etc.) to review and submit the combined changes.