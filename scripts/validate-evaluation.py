#!/usr/bin/env python3
"""Validate portable evaluation plans, reports, and Work Block closeout state."""
from __future__ import annotations

import argparse
import json
from pathlib import Path, PurePosixPath
import sys
from typing import Any

SCHEMA_VERSION = 1
ACTIVE_WORK_BLOCK_SCHEMA_VERSION = 3
ACTIVE_AUTHORITY_MODE = "github_capability"
RESULT_STATES = {"pass", "fail", "blocked", "not_run", "not_applicable"}
EVALUATION_VERDICTS = {"READY", "BLOCKED", "UNVERIFIED"}
ASSURANCE_STATUSES = {"PENDING", "READY", "SKIPPED", "DEGRADED", "BLOCKED"}
EVALUATOR_TYPES = {"deterministic", "human", "rule_based", "lm_judge"}
FORBIDDEN_REASONING_KEYS = {
    "chain_of_thought",
    "chain-of-thought",
    "hidden_reasoning",
    "private_reasoning",
    "scratchpad",
    "internal_deliberation",
}


class EvaluationError(RuntimeError):
    pass


def load_json_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"invalid {label}: {exc}") from exc
    if not isinstance(value, dict):
        raise EvaluationError(f"{label} must contain a JSON object")
    return value


def nonempty_string(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise EvaluationError(f"{label} must be a non-empty string")
    return value.strip()


def string_list(
    value: object,
    label: str,
    *,
    allow_empty: bool = True,
    unique: bool = True,
) -> list[str]:
    if not isinstance(value, list) or any(
        not isinstance(item, str) or not item.strip() for item in value
    ):
        raise EvaluationError(f"{label} must be an array of non-empty strings")
    result = [item.strip() for item in value]
    if not allow_empty and not result:
        raise EvaluationError(f"{label} must not be empty")
    if unique and len(set(result)) != len(result):
        raise EvaluationError(f"{label} contains duplicates")
    return result


def bool_value(value: object, label: str) -> bool:
    if not isinstance(value, bool):
        raise EvaluationError(f"{label} must be boolean")
    return value


def number_value(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise EvaluationError(f"{label} must be numeric")
    return float(value)


def reject_hidden_reasoning(value: object, path: str = "root") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace(" ", "_")
            if normalized in FORBIDDEN_REASONING_KEYS:
                raise EvaluationError(
                    f"{path}.{key} requests hidden reasoning; only observable events are allowed"
                )
            reject_hidden_reasoning(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            reject_hidden_reasoning(child, f"{path}[{index}]")


def criterion_list(items: object, label: str) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        raise EvaluationError(f"{label} must be an array")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise EvaluationError(f"{label}[{index}] must be an object")
        criterion_id = nonempty_string(
            item.get("criterion_id"), f"{label}[{index}].criterion_id"
        )
        if criterion_id in seen:
            raise EvaluationError(f"duplicate criterion_id in {label}: {criterion_id}")
        seen.add(criterion_id)
        result.append(item)
    return result


def validate_plan(
    plan: dict[str, Any], *, require_approved: bool = False
) -> dict[str, Any]:
    reject_hidden_reasoning(plan)
    if plan.get("schema_version") != SCHEMA_VERSION:
        raise EvaluationError(
            f"evaluation plan requires schema_version={SCHEMA_VERSION}"
        )
    if plan.get("artifact_type") != "evaluation_plan":
        raise EvaluationError("artifact_type must be evaluation_plan")

    evaluation_id = nonempty_string(plan.get("evaluation_id"), "evaluation_id")
    work_block_id = nonempty_string(plan.get("work_block_id"), "work_block_id")
    revision = nonempty_string(plan.get("revision"), "revision")
    status = nonempty_string(plan.get("status"), "status")
    if status not in {"draft", "review", "approved", "superseded", "blocked"}:
        raise EvaluationError(f"unsupported evaluation plan status: {status}")
    if require_approved and status != "approved":
        raise EvaluationError("closeout evaluation plan must be approved")

    subject = plan.get("subject")
    if not isinstance(subject, dict):
        raise EvaluationError("subject must be an object")
    objective = nonempty_string(subject.get("objective"), "subject.objective")
    specification_revision = nonempty_string(
        subject.get("specification_revision"), "subject.specification_revision"
    )
    frozen_revision = nonempty_string(
        subject.get("frozen_revision"), "subject.frozen_revision"
    )
    if require_approved and frozen_revision.startswith("pending"):
        raise EvaluationError("approved evaluation plan requires a frozen subject revision")

    deterministic = criterion_list(
        plan.get("deterministic_checks"), "deterministic_checks"
    )
    output = criterion_list(plan.get("output_criteria"), "output_criteria")
    trajectory = criterion_list(
        plan.get("trajectory_requirements"), "trajectory_requirements"
    )
    if not deterministic and not output and not trajectory:
        raise EvaluationError("evaluation plan must define at least one criterion")

    all_ids: set[str] = set()
    for label, items in (
        ("deterministic_checks", deterministic),
        ("output_criteria", output),
        ("trajectory_requirements", trajectory),
    ):
        for index, item in enumerate(items):
            criterion_id = nonempty_string(
                item.get("criterion_id"), f"{label}[{index}].criterion_id"
            )
            if criterion_id in all_ids:
                raise EvaluationError(
                    f"criterion_id must be globally unique: {criterion_id}"
                )
            all_ids.add(criterion_id)
            nonempty_string(item.get("description"), f"{label}[{index}].description")
            bool_value(item.get("blocking"), f"{label}[{index}].blocking")

    for index, item in enumerate(deterministic):
        nonempty_string(item.get("command"), f"deterministic_checks[{index}].command")
        nonempty_string(
            item.get("evidence"), f"deterministic_checks[{index}].evidence"
        )

    total_weight = 0.0
    for index, item in enumerate(output):
        evaluator_type = nonempty_string(
            item.get("evaluator_type"), f"output_criteria[{index}].evaluator_type"
        )
        if evaluator_type not in EVALUATOR_TYPES:
            raise EvaluationError(
                f"output_criteria[{index}].evaluator_type is unsupported: {evaluator_type}"
            )
        number_value(item.get("threshold"), f"output_criteria[{index}].threshold")
        weight = number_value(
            item.get("weight"), f"output_criteria[{index}].weight"
        )
        if weight < 0:
            raise EvaluationError(
                f"output_criteria[{index}].weight must be non-negative"
            )
        total_weight += weight
        nonempty_string(item.get("evidence"), f"output_criteria[{index}].evidence")
    if output and total_weight <= 0:
        raise EvaluationError("output criteria require a positive total weight")

    for index, item in enumerate(trajectory):
        nonempty_string(
            item.get("event_source"),
            f"trajectory_requirements[{index}].event_source",
        )
        required_events = string_list(
            item.get("required_events"),
            f"trajectory_requirements[{index}].required_events",
            allow_empty=False,
        )
        prohibited_events = string_list(
            item.get("prohibited_events", []),
            f"trajectory_requirements[{index}].prohibited_events",
        )
        overlap = sorted(set(required_events).intersection(prohibited_events))
        if overlap:
            raise EvaluationError(
                f"trajectory requirement cannot both require and prohibit: {', '.join(overlap)}"
            )

    benchmark_revision = nonempty_string(
        plan.get("benchmark_revision"), "benchmark_revision"
    )
    rubric_revision = nonempty_string(
        plan.get("rubric_revision"), "rubric_revision"
    )
    isolation_requirement = nonempty_string(
        plan.get("isolation_requirement"), "isolation_requirement"
    )
    if plan.get("aggregate_verdict_rule") != "all_blocking_pass":
        raise EvaluationError("aggregate_verdict_rule must be all_blocking_pass")

    judge = plan.get("judge_policy")
    if not isinstance(judge, dict):
        raise EvaluationError("judge_policy must be an object")
    lm_allowed = bool_value(
        judge.get("lm_judge_allowed"), "judge_policy.lm_judge_allowed"
    )
    if bool_value(
        judge.get("can_override_deterministic"),
        "judge_policy.can_override_deterministic",
    ):
        raise EvaluationError("LM judges cannot override deterministic evidence")
    if bool_value(
        judge.get("can_open_authority_gates"),
        "judge_policy.can_open_authority_gates",
    ):
        raise EvaluationError("LM judges cannot open authority gates")
    judge_identity = nonempty_string(
        judge.get("judge_identity"), "judge_policy.judge_identity"
    )
    judge_prompt_revision = nonempty_string(
        judge.get("judge_prompt_revision"), "judge_policy.judge_prompt_revision"
    )
    if lm_allowed and (
        judge_identity == "not-applicable"
        or judge_prompt_revision == "not-applicable"
    ):
        raise EvaluationError(
            "enabled LM judge requires concrete identity and prompt revision"
        )
    if not lm_allowed and any(
        item.get("evaluator_type") == "lm_judge" for item in output
    ):
        raise EvaluationError(
            "output criterion uses lm_judge while judge policy disables it"
        )

    return {
        "evaluation_id": evaluation_id,
        "work_block_id": work_block_id,
        "revision": revision,
        "status": status,
        "subject": {
            "objective": objective,
            "specification_revision": specification_revision,
            "frozen_revision": frozen_revision,
        },
        "deterministic": deterministic,
        "output": output,
        "trajectory": trajectory,
        "rubric_revision": rubric_revision,
        "benchmark_revision": benchmark_revision,
        "isolation_requirement": isolation_requirement,
        "judge_policy": judge,
    }


def result_map(items: object, label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(criterion_list(items, label)):
        criterion_id = nonempty_string(
            item.get("criterion_id"), f"{label}[{index}].criterion_id"
        )
        state = nonempty_string(item.get("state"), f"{label}[{index}].state")
        if state not in RESULT_STATES:
            raise EvaluationError(f"{label}[{index}].state is unsupported: {state}")
        result[criterion_id] = item
    return result


def validate_report(
    report: dict[str, Any], plan: dict[str, Any] | None = None
) -> dict[str, Any]:
    reject_hidden_reasoning(report)
    if report.get("schema_version") != SCHEMA_VERSION:
        raise EvaluationError(
            f"evaluation report requires schema_version={SCHEMA_VERSION}"
        )
    if report.get("artifact_type") != "evaluation_report":
        raise EvaluationError("artifact_type must be evaluation_report")

    evaluation_id = nonempty_string(report.get("evaluation_id"), "evaluation_id")
    work_block_id = nonempty_string(report.get("work_block_id"), "work_block_id")
    plan_revision = nonempty_string(report.get("plan_revision"), "plan_revision")
    subject_revision = nonempty_string(
        report.get("subject_revision"), "subject_revision"
    )
    status = nonempty_string(report.get("status"), "status")
    if status not in {"draft", "review", "complete", "blocked"}:
        raise EvaluationError(f"unsupported evaluation report status: {status}")
    for field in ("runtime", "logical_role", "model_class", "isolation"):
        value = nonempty_string(report.get(field), field)
        if status == "complete" and value in {"replace-me", "unknown"}:
            raise EvaluationError(f"complete report requires concrete {field}")
    if status == "complete":
        nonempty_string(report.get("completed_at"), "completed_at")

    deterministic = result_map(
        report.get("deterministic_results"), "deterministic_results"
    )
    output = result_map(report.get("output_results"), "output_results")
    trajectory = result_map(
        report.get("trajectory_results"), "trajectory_results"
    )

    for criterion_id, item in deterministic.items():
        if item["state"] == "pass":
            nonempty_string(
                item.get("evidence"),
                f"deterministic_results[{criterion_id}].evidence",
            )

    for criterion_id, item in output.items():
        evaluator_type = nonempty_string(
            item.get("evaluator_type"),
            f"output_results[{criterion_id}].evaluator_type",
        )
        if evaluator_type not in EVALUATOR_TYPES:
            raise EvaluationError(
                f"output_results[{criterion_id}].evaluator_type is unsupported"
            )
        if item["state"] == "pass":
            number_value(item.get("score"), f"output_results[{criterion_id}].score")
            nonempty_string(
                item.get("evidence"), f"output_results[{criterion_id}].evidence"
            )

    trajectory_values: dict[str, dict[str, Any]] = {}
    for criterion_id, item in trajectory.items():
        event_source = nonempty_string(
            item.get("event_source"),
            f"trajectory_results[{criterion_id}].event_source",
        )
        observed = string_list(
            item.get("observed_events"),
            f"trajectory_results[{criterion_id}].observed_events",
        )
        missing = string_list(
            item.get("missing_events"),
            f"trajectory_results[{criterion_id}].missing_events",
        )
        prohibited = string_list(
            item.get("prohibited_events_observed"),
            f"trajectory_results[{criterion_id}].prohibited_events_observed",
        )
        trajectory_values[criterion_id] = {
            "event_source": event_source,
            "observed": observed,
            "missing": missing,
            "prohibited": prohibited,
        }
        if item["state"] == "pass" and (not observed or missing or prohibited):
            raise EvaluationError(
                f"trajectory result {criterion_id} cannot pass with missing/prohibited/empty observable events"
            )

    judge_evidence = report.get("judge_evidence")
    if not isinstance(judge_evidence, list) or any(
        not isinstance(item, dict) for item in judge_evidence
    ):
        raise EvaluationError("judge_evidence must be an array of objects")

    aggregate = report.get("aggregate")
    if not isinstance(aggregate, dict):
        raise EvaluationError("aggregate must be an object")
    blocking_failures = string_list(
        aggregate.get("blocking_failures"), "aggregate.blocking_failures"
    )
    blocked_checks = string_list(
        aggregate.get("blocked_checks"), "aggregate.blocked_checks"
    )
    inspection_gaps = string_list(
        aggregate.get("inspection_gaps"), "aggregate.inspection_gaps"
    )
    verdict = nonempty_string(aggregate.get("verdict"), "aggregate.verdict")
    if verdict not in EVALUATION_VERDICTS:
        raise EvaluationError(f"unsupported evaluation verdict: {verdict}")

    plan_info: dict[str, Any] | None = None
    if plan is not None:
        plan_info = validate_plan(plan, require_approved=status == "complete")
        if evaluation_id != plan_info["evaluation_id"]:
            raise EvaluationError("report evaluation_id does not match plan")
        if work_block_id != plan_info["work_block_id"]:
            raise EvaluationError("report work_block_id does not match plan")
        if plan_revision != plan_info["revision"]:
            raise EvaluationError("report plan_revision does not match plan revision")
        if subject_revision != plan_info["subject"]["frozen_revision"]:
            raise EvaluationError(
                "report subject_revision does not match plan frozen_revision"
            )

        result_groups = {
            "deterministic": deterministic,
            "output": output,
            "trajectory": trajectory,
        }
        for group_name, planned in (
            ("deterministic", plan_info["deterministic"]),
            ("output", plan_info["output"]),
            ("trajectory", plan_info["trajectory"]),
        ):
            planned_ids = {item["criterion_id"] for item in planned}
            result_ids = set(result_groups[group_name])
            if planned_ids != result_ids:
                raise EvaluationError(
                    f"{group_name} result IDs do not exactly match the approved plan"
                )

        for criterion in plan_info["output"]:
            criterion_id = criterion["criterion_id"]
            result = output[criterion_id]
            if result.get("evaluator_type") != criterion.get("evaluator_type"):
                raise EvaluationError(
                    f"output evaluator type does not match plan: {criterion_id}"
                )
            if result["state"] == "pass":
                score = number_value(
                    result.get("score"), f"output_results[{criterion_id}].score"
                )
                threshold = number_value(
                    criterion.get("threshold"),
                    f"output_criteria[{criterion_id}].threshold",
                )
                if score < threshold:
                    raise EvaluationError(
                        f"output result {criterion_id} cannot pass below approved threshold"
                    )
            if criterion.get("evaluator_type") == "lm_judge":
                if not plan_info["judge_policy"].get("lm_judge_allowed"):
                    raise EvaluationError("LM judge result is not allowed by plan")
                if result["state"] == "pass" and not judge_evidence:
                    raise EvaluationError(
                        f"LM judge pass requires judge_evidence: {criterion_id}"
                    )

        for criterion in plan_info["trajectory"]:
            criterion_id = criterion["criterion_id"]
            result = trajectory[criterion_id]
            values = trajectory_values[criterion_id]
            if values["event_source"] != criterion.get("event_source"):
                raise EvaluationError(
                    f"trajectory event source does not match plan: {criterion_id}"
                )
            required = set(criterion.get("required_events") or [])
            planned_prohibited = set(criterion.get("prohibited_events") or [])
            observed = set(values["observed"])
            actual_missing = required.difference(observed)
            if set(values["missing"]) != actual_missing:
                raise EvaluationError(
                    f"trajectory missing_events does not match required events: {criterion_id}"
                )
            if not set(values["prohibited"]).issubset(planned_prohibited):
                raise EvaluationError(
                    f"trajectory report lists unplanned prohibited events: {criterion_id}"
                )
            if result["state"] == "pass" and (
                actual_missing or values["prohibited"]
            ):
                raise EvaluationError(
                    f"trajectory result {criterion_id} cannot pass without every required event and zero prohibited events"
                )

        if verdict == "READY":
            if status != "complete":
                raise EvaluationError("READY verdict requires complete report status")
            if blocking_failures or blocked_checks or inspection_gaps:
                raise EvaluationError(
                    "READY verdict cannot contain blocking failures or gaps"
                )
            for group_name, planned in (
                ("deterministic", plan_info["deterministic"]),
                ("output", plan_info["output"]),
                ("trajectory", plan_info["trajectory"]),
            ):
                for criterion in planned:
                    if (
                        criterion["blocking"]
                        and result_groups[group_name][criterion["criterion_id"]][
                            "state"
                        ]
                        != "pass"
                    ):
                        raise EvaluationError(
                            "READY verdict requires blocking criterion pass: "
                            f"{criterion['criterion_id']}"
                        )
            for criterion in plan_info["deterministic"]:
                result = deterministic[criterion["criterion_id"]]
                if result.get("evaluator_type") == "lm_judge":
                    raise EvaluationError(
                        "deterministic result cannot rely on an LM judge"
                    )

    if verdict == "READY" and (
        blocking_failures or blocked_checks or inspection_gaps
    ):
        raise EvaluationError("READY verdict cannot contain blocking failures or gaps")

    return {
        "evaluation_id": evaluation_id,
        "work_block_id": work_block_id,
        "plan_revision": plan_revision,
        "subject_revision": subject_revision,
        "status": status,
        "verdict": verdict,
        "plan": plan_info,
    }


def repo_relative_file(
    root: Path, raw: object, label: str, prefix: str
) -> Path:
    value = nonempty_string(raw, label).strip("\"'")
    path = Path(value)
    if path.is_absolute():
        try:
            path = path.resolve().relative_to(root)
        except (OSError, ValueError) as exc:
            raise EvaluationError(f"{label} is outside repository: {value}") from exc
    pure = PurePosixPath(path.as_posix())
    if ".." in pure.parts:
        raise EvaluationError(f"{label} escapes repository: {value}")
    normalized = pure.as_posix().lstrip("./")
    if not normalized.startswith(prefix):
        raise EvaluationError(f"{label} must be under {prefix}: {normalized}")
    full = root / normalized
    if not full.is_file() or full.stat().st_size == 0:
        raise EvaluationError(
            f"{label} does not exist or is empty: {normalized}"
        )
    return full


def validate_closeout(root: Path) -> dict[str, Any]:
    gate_path = root / ".agent/active-work-block.json"
    gate = load_json_object(gate_path, str(gate_path))
    if gate.get("schema_version") != ACTIVE_WORK_BLOCK_SCHEMA_VERSION:
        raise EvaluationError(
            f"active Work Block requires schema_version={ACTIVE_WORK_BLOCK_SCHEMA_VERSION}"
        )
    if gate.get("authority_mode") != ACTIVE_AUTHORITY_MODE:
        raise EvaluationError(
            f"active Work Block requires authority_mode={ACTIVE_AUTHORITY_MODE}"
        )
    work_block_id = nonempty_string(gate.get("work_block_id"), "work_block_id")
    assurance = gate.get("assurance")
    if not isinstance(assurance, dict):
        raise EvaluationError("active Work Block requires assurance object")
    state = assurance.get("evaluation")
    if not isinstance(state, dict):
        raise EvaluationError(
            "active Work Block requires assurance.evaluation state"
        )

    required = state.get("required") is True
    status = nonempty_string(
        state.get("status"), "assurance.evaluation.status"
    )
    verdict = nonempty_string(
        state.get("verdict"), "assurance.evaluation.verdict"
    )
    skip_reason = str(state.get("skip_reason") or "").strip()
    if status not in ASSURANCE_STATUSES:
        raise EvaluationError(f"unsupported evaluation assurance status: {status}")
    if required and status == "SKIPPED":
        raise EvaluationError("required evaluation cannot be SKIPPED")
    if not required and status == "SKIPPED":
        if not skip_reason:
            raise EvaluationError(
                "skipped optional evaluation requires skip_reason"
            )
        if verdict not in {"PENDING", "UNVERIFIED"}:
            raise EvaluationError(
                "skipped optional evaluation verdict must be PENDING or UNVERIFIED"
            )
        return {"required": required, "status": status, "verdict": verdict}
    if status == "PENDING":
        raise EvaluationError("evaluation assurance is still PENDING")
    if verdict not in EVALUATION_VERDICTS:
        raise EvaluationError(
            f"evaluation verdict is unresolved or invalid: {verdict}"
        )

    plan_path = repo_relative_file(
        root, state.get("plan"), "assurance.evaluation.plan", "docs/evals/"
    )
    report_path = repo_relative_file(
        root,
        state.get("report"),
        "assurance.evaluation.report",
        "docs/reports/",
    )
    isolation = nonempty_string(
        state.get("isolation"), "assurance.evaluation.isolation"
    )
    if isolation == "unknown":
        raise EvaluationError("evaluation isolation must record the actual boundary")
    rubric_revision = nonempty_string(
        state.get("rubric_revision"), "assurance.evaluation.rubric_revision"
    )
    benchmark_revision = nonempty_string(
        state.get("benchmark_revision"),
        "assurance.evaluation.benchmark_revision",
    )

    plan = load_json_object(plan_path, str(plan_path))
    report = load_json_object(report_path, str(report_path))
    plan_info = validate_plan(plan, require_approved=True)
    report_info = validate_report(report, plan)
    if plan_info["work_block_id"] != work_block_id:
        raise EvaluationError(
            "evaluation plan Work Block does not match active Work Block"
        )
    if rubric_revision != plan_info["rubric_revision"]:
        raise EvaluationError(
            "active Work Block rubric revision does not match plan"
        )
    if benchmark_revision != plan_info["benchmark_revision"]:
        raise EvaluationError(
            "active Work Block benchmark revision does not match plan"
        )
    if verdict != report_info["verdict"]:
        raise EvaluationError(
            "active Work Block evaluation verdict does not match report"
        )
    if isolation != report.get("isolation"):
        raise EvaluationError(
            "active Work Block evaluation isolation does not match report"
        )

    mode = str(gate.get("closeout_mode") or "")
    if mode == "success-closeout":
        if required and (status != "READY" or verdict != "READY"):
            raise EvaluationError(
                "success-closeout requires required evaluation status/verdict READY"
            )
        if status == "READY" and verdict != "READY":
            raise EvaluationError(
                "evaluation READY status requires READY verdict"
            )
    elif mode != "reporting-only":
        raise EvaluationError(
            "closeout_mode must be success-closeout or reporting-only for evaluation closeout"
        )

    return {
        "required": required,
        "status": status,
        "verdict": verdict,
        "plan": plan_path.as_posix(),
        "report": report_path.as_posix(),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan_parser = subparsers.add_parser("plan")
    plan_parser.add_argument("path", type=Path)
    plan_parser.add_argument("--require-approved", action="store_true")

    report_parser = subparsers.add_parser("report")
    report_parser.add_argument("report", type=Path)
    report_parser.add_argument("plan", type=Path)

    closeout_parser = subparsers.add_parser("closeout")
    closeout_parser.add_argument("root", nargs="?", type=Path, default=Path.cwd())

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(argv or sys.argv[1:]))
    try:
        if args.command == "plan":
            info = validate_plan(
                load_json_object(args.path, str(args.path)),
                require_approved=args.require_approved,
            )
        elif args.command == "report":
            plan = load_json_object(args.plan, str(args.plan))
            report = load_json_object(args.report, str(args.report))
            info = validate_report(report, plan)
        else:
            info = validate_closeout(args.root.resolve())
    except EvaluationError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(info, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
