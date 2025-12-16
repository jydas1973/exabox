# dbaastools AGENTS.md

## **Key Paths**
- Command definitions: `sa/src/main/resources/oracle/dblcm/sa/dbaastools/resource/dbaastools_commands_definition.json`
- CLI arg mapping: `sa/src/main/resources/oracle/dblcm/sa/dbaastools/resource/dbaastools_arg_to_dbaasoca_arg_mapper.json`
- Command processors: `sa/src/main/java/oracle/dblcm/sa/dbaastools/cmd/`
- Validators: `sa/src/main/java/oracle/dblcm/sa/dbaastools/validator/`
- Jobs (native): `sa/src/main/java/oracle/dblcm/sa/dbaastools/job/`
- Common-lib (DG, DB info): `common-lib/src/main/java/oracle/dbcloud/common/lib/`
- Dbaas SA error codes and messages: `sa/src/main/java/oracle/dblcm/sa/dbaastools/resource/`
- PILOT error codes and messages: `plugins/src/main/java/oracle/dbcloud/pilot/plugin/resource/`
- Common error codes and messages: `common-lib/src/main/java/oracle/dbcloud/common/lib/resource/`

## **Guidelines**
- Follow repository naming, structure, and dependencies.
- Prefer standard libraries; avoid adding new deps unless justified.
- Keep functions small, focused, and readable.
- Explain logic concisely when asked; avoid placeholder comments.
- Cover null checks and error handling consistently.

## **Code Review**
- Review staged and unstaged changes in the current working tree.
- Verify null checks, logging, and exception types/messages.
- Suggest targeted improvements without large refactors unless requested.
- Generate as output this template with corresponding information:
  - INTERNAL PROBLEM DESCRIPTION:
  - INTERNAL FIX DESCRIPTION:
  - TESTCASE: YES/NO
  - EXPLAIN HOW TO RUN THE TESTCASE:

## **Typical Flow**
- CLI → command definition → processor → validator(s) → job(s) → common-lib APIs.
- Composite executions run multiple steps; many DG ops end with a details generation job.
