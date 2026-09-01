#!/usr/bin/env python3
"""Validate Define-stage requirement/acceptance/task traceability.

This validator is intentionally format-light. It validates stable IDs and
cross-artifact references without deciding product correctness.

Specification syntax:
  - REQ-001: Requirement text
  - AC-001 [req=REQ-001,REQ-002]: Measurable acceptance criterion

Task syntax:
  - [ ] TASK-001 [type=requirement] [req=REQ-001] [ac=AC-001] [paths=src/a.py] Implement ...
  - [ ] TASK-002 [type=enabling] [req=-] [ac=-] [paths=pyproject.toml] Add tooling ...
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

REQ_RE = re.compile(r"^\s*-\s+(REQ-[A-Za-z0-9._-]+)\s*:\s*(.+?)\s*$")
AC_RE = re.compile(
    r"^\s*-\s+(AC-[A-Za-z0-9._-]+)\s+\[req=([^\]]+)\]\s*:\s*(.+?)\s*$"
)
TASK_RE = re.compile(
    r"^\s*-\s+\[[ xX]\]\s+(TASK-[A-Za-z0-9._-]+)\s+"
    r"\[type=(requirement|enabling|assurance|documentation)\]\s+"
    r"\[req=([^\]]+)\]\s+\[ac=([^\]]+)\]\s+\[paths=([^\]]+)\]\s+(.+?)\s*$"
)


@dataclass(frozen=True)
class Acceptance:
    refs: tuple[str, ...]
    text: str


@dataclass(frozen=True)
class Task:
    task_type: str
    reqs: tuple[str, ...]
    acs: tuple[str, ...]
    paths: tuple[str, ...]
    text: str


def split_refs(raw: str) -> tuple[str, ...]:
    raw = raw.strip()
    if raw == "-":
        return ()
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def parse_spec(path: Path) -> tuple[dict[str, str], dict[str, Acceptance], list[str]]:
    requirements: dict[str, str] = {}
    acceptance: dict[str, Acceptance] = {}
    errors: list[str] = []

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        req_match = REQ_RE.match(line)
        if req_match:
            req_id, text = req_match.groups()
            if req_id in requirements:
                errors.append(f"{path}:{line_no}: duplicate requirement {req_id}")
            else:
                requirements[req_id] = text
            continue

        ac_match = AC_RE.match(line)
        if ac_match:
            ac_id, raw_refs, text = ac_match.groups()
            refs = split_refs(raw_refs)
            if ac_id in acceptance:
                errors.append(f"{path}:{line_no}: duplicate acceptance criterion {ac_id}")
            elif not refs:
                errors.append(
                    f"{path}:{line_no}: {ac_id} must reference at least one requirement"
                )
            else:
                acceptance[ac_id] = Acceptance(refs, text)

    if not requirements:
        errors.append(f"{path}: no REQ-* requirements found")
    if not acceptance:
        errors.append(f"{path}: no AC-* acceptance criteria found")
    return requirements, acceptance, errors


def parse_tasks(path: Path) -> tuple[dict[str, Task], list[str]]:
    tasks: dict[str, Task] = {}
    errors: list[str] = []

    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if "TASK-" not in line:
            continue
        match = TASK_RE.match(line)
        if not match:
            errors.append(
                f"{path}:{line_no}: TASK line does not match required traceability format"
            )
            continue

        task_id, task_type, raw_reqs, raw_acs, raw_paths, text = match.groups()
        reqs = split_refs(raw_reqs)
        acs = split_refs(raw_acs)
        paths = split_refs(raw_paths)

        if task_id in tasks:
            errors.append(f"{path}:{line_no}: duplicate task {task_id}")
            continue
        if not paths:
            errors.append(f"{path}:{line_no}: {task_id} requires explicit paths/write-set")
        if task_type == "requirement" and (not reqs or not acs):
            errors.append(
                f"{path}:{line_no}: requirement task {task_id} must reference REQ and AC IDs"
            )

        tasks[task_id] = Task(task_type, reqs, acs, paths, text)

    if not tasks:
        errors.append(f"{path}: no TASK-* tasks found")
    return tasks, errors


def validate(spec_path: Path, tasks_path: Path) -> dict[str, object]:
    requirements, acceptance, errors = parse_spec(spec_path)
    tasks, task_errors = parse_tasks(tasks_path)
    errors.extend(task_errors)

    for ac_id, ac in acceptance.items():
        for req_id in ac.refs:
            if req_id not in requirements:
                errors.append(f"{ac_id} references unknown requirement {req_id}")

    req_to_ac: dict[str, set[str]] = {req_id: set() for req_id in requirements}
    for ac_id, ac in acceptance.items():
        for req_id in ac.refs:
            if req_id in req_to_ac:
                req_to_ac[req_id].add(ac_id)
    for req_id, ac_ids in req_to_ac.items():
        if not ac_ids:
            errors.append(f"{req_id} has no acceptance criterion")

    req_to_tasks: dict[str, set[str]] = {req_id: set() for req_id in requirements}
    ac_to_tasks: dict[str, set[str]] = {ac_id: set() for ac_id in acceptance}

    for task_id, task in tasks.items():
        # References are validated for every task type that carries them.
        for req_id in task.reqs:
            if req_id not in requirements:
                errors.append(f"{task_id} references unknown requirement {req_id}")

        for ac_id in task.acs:
            if ac_id not in acceptance:
                errors.append(f"{task_id} references unknown acceptance criterion {ac_id}")

        # Only requirement tasks represent implementation coverage. Enabling,
        # assurance, and documentation tasks may carry useful references but
        # cannot satisfy REQ/AC implementation coverage.
        if task.task_type == "requirement":
            for req_id in task.reqs:
                if req_id in requirements:
                    req_to_tasks[req_id].add(task_id)
            for ac_id in task.acs:
                if ac_id in acceptance:
                    ac_to_tasks[ac_id].add(task_id)

            for ac_id in task.acs:
                if ac_id in acceptance:
                    covered_reqs = set(acceptance[ac_id].refs)
                    if task.reqs and covered_reqs.isdisjoint(task.reqs):
                        errors.append(
                            f"{task_id} references {ac_id}, but that criterion covers "
                            f"{','.join(sorted(covered_reqs))}, not the task requirements"
                        )

    for req_id, task_ids in req_to_tasks.items():
        if not task_ids:
            errors.append(f"{req_id} has no implementation task")
    for ac_id, task_ids in ac_to_tasks.items():
        if not task_ids:
            errors.append(f"{ac_id} has no traced implementation task")

    return {
        "verdict": "READY" if not errors else "BLOCKED",
        "spec": str(spec_path),
        "tasks": str(tasks_path),
        "requirements": len(requirements),
        "acceptance_criteria": len(acceptance),
        "tasks_count": len(tasks),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", required=True, type=Path)
    parser.add_argument("--tasks", required=True, type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    for path in (args.spec, args.tasks):
        if not path.is_file():
            result = {
                "verdict": "UNVERIFIED",
                "errors": [f"missing required file: {path}"],
            }
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print("UNVERIFIED")
                for error in result["errors"]:
                    print(f"- {error}")
            return 2

    result = validate(args.spec, args.tasks)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["verdict"])
        print(
            f"requirements={result['requirements']} "
            f"acceptance={result['acceptance_criteria']} tasks={result['tasks_count']}"
        )
        for error in result["errors"]:
            print(f"- {error}")
    return 0 if result["verdict"] == "READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
