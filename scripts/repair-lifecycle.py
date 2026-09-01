#!/usr/bin/env python3
"""Fail-closed validation for machine-readable NDR repair records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ALLOWED_PREFIXES = (".github/", "bootstrap/", "scripts/", "template/")
PROHIBITED_DOMAINS = (
    "architecture", "product", "auth", "security_boundary", "public_api",
    "schema", "data", "deploy", "dependency_upgrade",
)


def load_record(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        return json.loads(text)
    marker = "```json\n"
    start = text.find(marker)
    end = text.find("\n```", start + len(marker))
    if start < 0 or end < 0:
        raise ValueError("Markdown record requires a fenced JSON machine record")
    return json.loads(text[start + len(marker):end])


def canonical_paths(paths: object, label: str) -> tuple[list[str], list[str]]:
    """Reject non-canonical path spellings instead of normalizing them silently."""
    if not isinstance(paths, list) or not paths:
        return [], [f"{label} must be a non-empty path list"]
    errors: list[str] = []
    canonical: list[str] = []
    for path in paths:
        if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or "\x00" in path:
            errors.append(f"{label} contains an invalid path")
            continue
        components = path.split("/")
        if any(component in {"", ".", ".."} for component in components):
            errors.append(f"{label} contains a non-canonical path")
            continue
        canonical.append(path)
    if len(canonical) != len(set(canonical)):
        errors.append(f"{label} paths must be unique")
    return canonical, errors


def validate(record: dict, actual_paths: list[str] | None = None) -> list[str]:
    errors: list[str] = []
    if record.get("mode") != "NDR": errors.append("mode must be NDR")
    if record.get("risk") not in {"low", "medium"}: errors.append("risk must be low or medium")
    if record.get("deterministic") is not True: errors.append("deterministic must be true")
    if record.get("reversible") is not True: errors.append("reversible must be true")
    if record.get("architecture_decision_required") is not False: errors.append("architecture_decision_required must be false")
    prohibited = record.get("prohibited_domains")
    if not isinstance(prohibited, dict) or any(prohibited.get(domain) is not False for domain in PROHIBITED_DOMAINS):
        errors.append("every prohibited domain must be explicitly false")
    if record.get("implementation_passes") != 1: errors.append("exactly one implementation pass required")
    if record.get("correction_rounds") not in {0, 1}: errors.append("NDR permits at most one correction")
    allowlist, allowlist_errors = canonical_paths(record.get("allowlist"), "allowlist")
    errors.extend(allowlist_errors)
    if not allowlist or any(not path.startswith(ALLOWED_PREFIXES) for path in allowlist):
        errors.append("allowlist must be a non-empty CI/bootstrap/runtime-validation path list")
    actual, actual_errors = canonical_paths(actual_paths, "actual changed paths")
    errors.extend(actual_errors)
    if not actual_errors and sorted(allowlist) != sorted(actual):
        errors.append("allowlist must exactly match actual changed paths")
    stabilization = record.get("integration_stabilization", {})
    if not isinstance(stabilization, dict) or not isinstance(stabilization.get("items", []), list) or len(stabilization.get("items", [])) > 3 or stabilization.get("correction_rounds", 0) > 2:
        errors.append("Integration Stabilization permits at most three items and two corrections")
    for field in ("problem", "root_cause", "verification_commands", "stop_condition"):
        if not record.get(field): errors.append(f"{field} required")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    parser.add_argument("--changed-path", action="append", default=[])
    args = parser.parse_args()
    try:
        errors = validate(load_record(args.record), args.changed_path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"BLOCKED: invalid repair record: {exc}")
        return 1
    if errors:
        print("BLOCKED: " + "; ".join(errors))
        return 1
    print("READY: NDR repair record is within its mechanical limits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
