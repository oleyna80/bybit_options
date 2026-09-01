#!/usr/bin/env python3
"""Validate one generated project's resolved bootstrap installation profile."""
from __future__ import annotations

import json
from pathlib import Path, PurePosixPath, PureWindowsPath
import sys
from typing import Any

PROFILE_PATH = Path(".agent/bootstrap-profile.json")
DEFAULT_WORK_BLOCK_PATH = Path(".agent/active-work-block.default.json")
SCHEMA_VERSION = 1
DEFAULT_WORK_BLOCK_SCHEMA_VERSION = 3
EXPECTED_AUTHORITY_MODE = "github_capability"
EXPECTED_DEFAULT_GOVERNANCE_PROFILE = "Controlled"
EXPECTED_DEFAULT_DEFINE_QUALITY = {
    "required": False,
    "status": "PENDING",
    "requirements_review": "",
    "traceability": "",
    "consistency_analysis": "",
}
EXPECTED_EXTERNAL_HARD_STOPS = [
    "protected_default_branch_mutation",
    "destructive",
    "live_infra",
    "live_data",
    "credentials",
    "client_communications",
    "irreversible_publish",
]
EXPECTED_COORDINATION_WRITE_SET = [
    ".agent/active-work-block.json",
    ".agent/critic-gate.md",
    ".agent/verification-gate.md",
    ".codex/write-gate.md",
    "docs/plans/**",
    "docs/specs/**",
    "docs/tasklist/**",
    "docs/reports/**",
    "docs/architecture/drafts/**",
    "memory_bank/**",
]
EXPECTED_DEFAULT_EVALUATION = {
    "required": False,
    "status": "PENDING",
    "verdict": "PENDING",
    "plan": "",
    "report": "",
    "rubric_revision": "",
    "benchmark_revision": "",
    "isolation": "unknown",
    "skip_reason": "",
}


class ValidationError(RuntimeError):
    pass


def load_state(root: Path) -> dict[str, Any]:
    path = root / PROFILE_PATH
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid {PROFILE_PATH}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{PROFILE_PATH} must contain a JSON object")
    return value


def relative_paths(state: dict[str, Any], field: str) -> list[str]:
    value = state.get(field)
    if not isinstance(value, list):
        raise ValidationError(f"{field} must be an array")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"{field}[{index}] must be a non-empty string")
        path = Path(item)
        if path.is_absolute() or ".." in path.parts:
            raise ValidationError(f"{field}[{index}] is not a safe relative path: {item!r}")
        result.append(item)
    if len(set(result)) != len(result):
        raise ValidationError(f"{field} contains duplicate paths")
    return result


def string_list(state: dict[str, Any], field: str) -> list[str]:
    value = state.get(field)
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValidationError(f"{field} must be an array of non-empty strings")
    if len(set(value)) != len(value):
        raise ValidationError(f"{field} contains duplicates")
    return list(value)


def path_kinds(state: dict[str, Any], required: list[str]) -> dict[str, str]:
    value = state.get("required_path_kinds")
    if value is None:
        return {path: "file" for path in required}
    if not isinstance(value, dict):
        raise ValidationError("required_path_kinds must be an object")
    result: dict[str, str] = {}
    for path in required:
        kind = value.get(path)
        if kind not in {"file", "directory"}:
            raise ValidationError(
                f"required_path_kinds[{path!r}] must be file or directory"
            )
        result[path] = kind
    unexpected = sorted(set(value).difference(required))
    if unexpected:
        raise ValidationError(
            "required_path_kinds contains unknown paths: " + ", ".join(unexpected)
        )
    return result


def require_kind(root: Path, relative: str, kind: str) -> bool:
    path = root / relative
    if kind == "file":
        return path.is_file()
    if kind == "directory":
        return path.is_dir()
    raise AssertionError(f"unexpected required path kind: {kind}")


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValidationError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{label} must contain a JSON object")
    return value


def validate_coordination_write_set(state: dict[str, Any]) -> None:
    value = state.get("coordination_write_set")
    if not isinstance(value, list):
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} coordination_write_set must be an array"
        )

    for index, item in enumerate(value):
        if not isinstance(item, str) or not item or item != item.strip():
            raise ValidationError(
                f"{DEFAULT_WORK_BLOCK_PATH} coordination_write_set[{index}] "
                "must be a non-empty canonical string"
            )
        normalized = item.replace("\\", "/")
        posix_path = PurePosixPath(normalized)
        windows_path = PureWindowsPath(item)
        if posix_path.is_absolute() or windows_path.is_absolute():
            raise ValidationError(
                f"{DEFAULT_WORK_BLOCK_PATH} coordination_write_set[{index}] "
                f"must be relative: {item!r}"
            )
        if item in {".", "./"}:
            raise ValidationError(
                f"{DEFAULT_WORK_BLOCK_PATH} coordination_write_set[{index}] "
                "must not authorize the repository root"
            )
        if ".." in posix_path.parts:
            raise ValidationError(
                f"{DEFAULT_WORK_BLOCK_PATH} coordination_write_set[{index}] "
                f"must not traverse outside the project: {item!r}"
            )
        if any(marker in item for marker in ("*", "?", "[")) and (
            item not in EXPECTED_COORDINATION_WRITE_SET
        ):
            raise ValidationError(
                f"{DEFAULT_WORK_BLOCK_PATH} coordination_write_set[{index}] "
                f"contains an unauthorized wildcard pattern: {item!r}"
            )

    if value != EXPECTED_COORDINATION_WRITE_SET:
        detail = (
            "must preserve canonical path order"
            if len(value) == len(EXPECTED_COORDINATION_WRITE_SET)
            and set(value) == set(EXPECTED_COORDINATION_WRITE_SET)
            else "must exactly match the canonical blocked-default paths"
        )
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} coordination_write_set {detail}"
        )


def validate_default_assurance(state: dict[str, Any]) -> None:
    assurance = state.get("assurance")
    if not isinstance(assurance, dict):
        raise ValidationError(f"{DEFAULT_WORK_BLOCK_PATH} assurance must be an object")
    if set(assurance) != {"review", "verification", "evaluation", "drift"}:
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} assurance must contain review, verification, evaluation, and drift"
        )
    if assurance.get("evaluation") != EXPECTED_DEFAULT_EVALUATION:
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} assurance.evaluation must be the optional PENDING default"
        )
    if state.get("closeout_mode") != "pending":
        raise ValidationError(f"{DEFAULT_WORK_BLOCK_PATH} closeout_mode must be pending")


def validate_blocked_default(root: Path) -> None:
    state = load_json_object(
        root / DEFAULT_WORK_BLOCK_PATH, str(DEFAULT_WORK_BLOCK_PATH)
    )
    if state.get("schema_version") != DEFAULT_WORK_BLOCK_SCHEMA_VERSION:
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} requires schema_version={DEFAULT_WORK_BLOCK_SCHEMA_VERSION}"
        )
    if state.get("authority_mode") != EXPECTED_AUTHORITY_MODE:
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} authority_mode must be {EXPECTED_AUTHORITY_MODE}"
        )
    if state.get("governance_profile") != EXPECTED_DEFAULT_GOVERNANCE_PROFILE:
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} governance_profile must be the canonical Controlled default"
        )
    if state.get("define_quality") != EXPECTED_DEFAULT_DEFINE_QUALITY:
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} define_quality must be the canonical Controlled PENDING default"
        )
    if "authorization" in state or "hard_stop_approvals" in state:
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} must not require legacy signed authorization state"
        )
    write_gate = state.get("write_gate")
    if not isinstance(write_gate, dict):
        raise ValidationError(f"{DEFAULT_WORK_BLOCK_PATH} missing write_gate object")
    if write_gate != {"status": "BLOCKED", "opened_at": None}:
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} write_gate must be the canonical BLOCKED schema v3 state"
        )
    integrations = state.get("integrations")
    if integrations != {"approved": [], "admission_records": []}:
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} integrations must be approval-free"
        )
    if state.get("write_set") != []:
        raise ValidationError(f"{DEFAULT_WORK_BLOCK_PATH} write_set must be empty")
    if state.get("external_hard_stops") != EXPECTED_EXTERNAL_HARD_STOPS:
        raise ValidationError(
            f"{DEFAULT_WORK_BLOCK_PATH} external_hard_stops must match the canonical capability boundary"
        )
    validate_coordination_write_set(state)
    validate_default_assurance(state)


def validate(root: Path) -> dict[str, Any]:
    state = load_state(root)
    if state.get("schema_version") != SCHEMA_VERSION:
        raise ValidationError(
            f"bootstrap profile requires schema_version={SCHEMA_VERSION}"
        )
    for field in ("requested_profile", "resolved_profile", "description"):
        if not isinstance(state.get(field), str) or not state[field].strip():
            raise ValidationError(f"{field} must be a non-empty string")

    required = relative_paths(state, "required_paths")
    forbidden = relative_paths(state, "forbidden_paths")
    overlaps = sorted(set(required).intersection(forbidden))
    if overlaps:
        raise ValidationError(
            f"paths cannot be both required and forbidden: {', '.join(overlaps)}"
        )

    components = string_list(state, "components")
    runtimes = string_list(state, "runtimes")
    integrations = string_list(state, "integrations")
    skills = string_list(state, "skills")
    mirrors = relative_paths(state, "skill_mirrors")

    if "generic" not in runtimes:
        raise ValidationError("every installation profile must retain generic runtime guidance")
    if not isinstance(state.get("authority_note"), str) or "does not grant" not in state["authority_note"]:
        raise ValidationError("authority_note must state that installation does not grant authority")

    kinds = path_kinds(state, required)
    missing = [path for path in required if not require_kind(root, path, kinds[path])]
    unexpected = [path for path in forbidden if (root / path).exists()]
    if missing:
        raise ValidationError("missing required paths: " + ", ".join(missing))
    if unexpected:
        raise ValidationError("unexpected unselected paths: " + ", ".join(unexpected))

    for skill in skills:
        if not (root / ".agent/skills" / skill / "SKILL.md").is_file():
            raise ValidationError(f"missing portable skill: {skill}")
        for mirror in mirrors:
            if not (root / mirror / skill / "SKILL.md").is_file():
                raise ValidationError(f"missing skill mirror {mirror}/{skill}")

    validate_blocked_default(root)

    return {
        "profile": state["resolved_profile"],
        "requested_profile": state["requested_profile"],
        "components": components,
        "runtimes": runtimes,
        "integrations": integrations,
        "skills": skills,
    }


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    try:
        summary = validate(root)
    except ValidationError as exc:
        print(f"FAIL: installation profile validation: {exc}", file=sys.stderr)
        return 1
    print(
        "Installation profile: OK "
        f"({summary['requested_profile']} -> {summary['profile']}; "
        f"runtimes={','.join(summary['runtimes'])}; "
        f"components={len(summary['components'])}; skills={len(summary['skills'])})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
