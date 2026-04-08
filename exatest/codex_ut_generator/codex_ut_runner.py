#!/bin/python
#
# $Header: ecs/exacloud/exabox/exatest/codex_ut_generator/codex_ut_runner.py /main/1 2025/12/15 11:26:49 aararora Exp $
#
# codex_ut_runner.py
#
# Copyright (c) 2025, Oracle and/or its affiliates.
#
#    NAME
#      codex_ut_runner.py - Minimal Codex UT runner: orchestrates Codex iterations and final coverage.
#
#    DESCRIPTION
# The runner is intentionally lightweight—the heavy lifting (planning, history,
# branch analysis) lives in CODEX_TEST_INSTRUCTIONS.md. This script only reads
# config, invokes Codex for a fixed number of iterations, and optionally executes
# the coverage command once Codex finishes.
#
#    NOTES
#      <other useful comments, qualifications, etc.>
#
#    MODIFIED   (MM/DD/YY)
#    aararora    12/12/25 - 38714897: UT generator framework - UT Runner script
#                           to generate unit tests in exacloud
#    aararora    12/12/25 - Creation
#

import argparse
import json
import os
import shlex
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

DEFAULT_TIMEOUT = 3600
DEFAULT_MAX_ITERATIONS = 5
LOG_PATH = Path.cwd() / "codex_ut_runner.log"

def log(message: str, also_print: bool = True) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] [{Path.cwd().name}:{os.getpid()}] {message}"
    if also_print:
        print(line)
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(line + "\n")

def load_config(path: Path) -> dict:
    """Load the JSON configuration describing targets and view name."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def resolve_path(raw: str, view_root: Path) -> Path:
    replaced = raw.replace("<VIEW_LOCATION>", str(view_root))
    candidate = Path(replaced)
    return candidate if candidate.is_absolute() else view_root / candidate

def resolve_targets(config: dict, base: Path) -> (Path, List[dict]):
    """Expand target paths relative to the resolved ADE view root."""
    view_root = base / config["view_name"]
    targets: List[dict] = []
    for entry in config.get("targets", []):
        tests_section = entry.get("tests", {})
        primary = tests_section.get("primary")
        if primary is None:
            raise ValueError(f"Missing primary test for target {entry['code']}")
        targets.append(
            {
                "code": resolve_path(entry["code"], view_root),
                "primary": resolve_path(primary, view_root),
                "additional": [resolve_path(item, view_root) for item in tests_section.get("additional", [])],
            }
        )
    return view_root, targets

def _in_view(view_name: Optional[str]) -> bool:
    """Check whether the current shell already resides in the desired view."""
    current = os.environ.get("ADE_VIEW_NAME")
    return bool(view_name and current and current == view_name)

def _wrap_with_view(argv: List[str], view_name: Optional[str], cwd: Optional[Path]) -> List[str]:
    if not view_name or _in_view(view_name):
        return argv
    command = " ".join(shlex.quote(str(arg)) for arg in argv)
    if cwd:
        command = f"cd {shlex.quote(str(cwd))} && {command}"
    wrapped = [
        "ade",
        "useview",
        view_name,
        "-exec",
        f"/bin/bash -lc {shlex.quote(command)}",
    ]
    return wrapped

def execute(
    argv: List[str],
    view_name: Optional[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
) -> subprocess.CompletedProcess:
    """Run a command, wrapping it with ade useview when needed."""
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
    wrapped = _wrap_with_view([str(arg) for arg in argv], view_name, cwd)
    result = subprocess.run(
        wrapped,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        check=False,
        env=proc_env,
    )
    return result

def spawn(
    argv: List[str],
    view_name: Optional[str],
    cwd: Optional[Path] = None,
    env: Optional[dict] = None,
    **kwargs,
) -> subprocess.Popen:
    """Spawn a long-running command (Codex) with optional view wrapping."""
    proc_env = os.environ.copy()
    if env:
        proc_env.update(env)
    wrapped = _wrap_with_view([str(arg) for arg in argv], view_name, cwd)
    return subprocess.Popen(
        wrapped,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        bufsize=1,
        env=proc_env,
        **kwargs,
    )

def build_prompt(
    view_root: Path,
    target: dict,
    instructions: str,
    iteration: int,
    max_iterations: int,
) -> str:
    """Assemble the Codex prompt using the rendered instructions and metadata."""
    additional = target["additional"] or []
    additional_text = "\n  - ".join(str(path) for path in additional) if additional else "(none)"
    return f"""
You are Codex operating inside the view {view_root}.
Target code: {target['code']}
Primary test: {target['primary']}
Additional tests:
  - {additional_text}
Iteration {iteration} of {max_iterations}.

=== PLAYBOOK ===
{instructions.strip()}
=== END PLAYBOOK ===

Execute autonomously and stop when coverage goals in the playbook are satisfied.
"""

def run_codex(
    view_root: Path,
    view_name: Optional[str],
    target: dict,
    instructions: str,
    iteration: int,
    max_iterations: int,
    timeout: int,
) -> subprocess.CompletedProcess:
    """Invoke Codex CLI for a single iteration and stream logs into the runner."""
    cmd = [
        "codex",
        "exec",
        "--skip-git-repo-check",
        "--sandbox",
        "danger-full-access",
        "--cd",
        str(view_root),
    ]
    log(f"[runner] Invoking Codex (iteration {iteration}/{max_iterations})...")
    proc = spawn(cmd, view_name, cwd=view_root)
    stdout_lines: List[str] = []
    stderr_lines: List[str] = []

    def _reader(pipe, store: List[str], also_print: bool) -> None:
        try:
            for line in pipe:
                clean = line.rstrip("\n")
                store.append(clean)
                log(clean, also_print=also_print)
        finally:
            pipe.close()

    threads = [
        threading.Thread(target=_reader, args=(proc.stdout, stdout_lines, True), daemon=True),
        threading.Thread(target=_reader, args=(proc.stderr, stderr_lines, False), daemon=True),
    ]
    for thread in threads:
        thread.start()

    try:
        prompt = build_prompt(view_root, target, instructions, iteration, max_iterations)
        if proc.stdin:
            proc.stdin.write(prompt)
            proc.stdin.close()
    except Exception as exc:
        log(f"[runner] Failed to send prompt to Codex: {exc}")

    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        log("[runner] Codex invocation timed out; terminating process")
        proc.kill()
        proc.wait()
    finally:
        for thread in threads:
            thread.join(timeout=1)

    return subprocess.CompletedProcess(
        args=cmd,
        returncode=proc.returncode,
        stdout="\n".join(stdout_lines),
        stderr="\n".join(stderr_lines),
    )

def run_coverage(view_root: Path, tests: Iterable[Path], view_name: Optional[str]) -> None:
    """Execute the exatest coverage command once Codex iterations are done."""
    tests = list(dict.fromkeys(tests))
    if not tests:
        return
    python_bin = view_root / "ecs/exacloud/bin/python"
    exatest = view_root / "ecs/exacloud/exabox/exatest/exatest.py"
    cmd = [str(python_bin), str(exatest), "-r", "-f", *(str(t) for t in tests), "--coverage"]
    log(f"[runner] Running coverage command: {' '.join(cmd)}")
    result = execute(cmd, view_name, cwd=view_root)
    if result.stdout:
        log(result.stdout.rstrip())
    if result.stderr:
        log(result.stderr.rstrip(), also_print=False)

def main(argv: List[str]) -> int:
    """Entry point coordinating iterations and optional coverage execution."""
    parser = argparse.ArgumentParser(description="Codex multi-target UT runner")
    parser.add_argument("--config", required=True)
    parser.add_argument("--user", default=os.environ.get("USER", ""))
    parser.add_argument("--base")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--instructions",
        default=str(Path(__file__).resolve().with_name("CODEX_TEST_INSTRUCTIONS.md")),
    )
    parser.add_argument("--codex-timeout", type=int, default=DEFAULT_TIMEOUT)
    parser.add_argument("--max-iterations", type=int, default=DEFAULT_MAX_ITERATIONS)
    args = parser.parse_args(argv)

    LOG_PATH.write_text("")
    instructions_text = Path(args.instructions).read_text(encoding="utf-8")
    config = load_config(Path(args.config))
    view_name = config.get("view_name")
    base_dir = Path(args.base) if args.base else Path("/scratch") / args.user / "view_storage"
    view_root, targets = resolve_targets(config, base_dir)

    log(f"[runner] View root: {view_root}")
    for target in targets:
        log("\n--- Target ---")
        log(f"Code: {target['code']}")
        log(f"Primary test: {target['primary']}")
        if target["additional"]:
            for extra in target["additional"]:
                log(f"Additional test: {extra}")

        tests = [target["primary"]] + target["additional"]

        for iteration in range(1, args.max_iterations + 1):
            result = run_codex(
                view_root,
                view_name,
                target,
                instructions_text,
                iteration,
                args.max_iterations,
                timeout=args.codex_timeout,
            )
            if result.returncode not in (0, None):
                log(f"[runner] Codex returned exit code {result.returncode}; stopping iterations")
                break

        if args.execute:
            run_coverage(view_root, tests, view_name)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))