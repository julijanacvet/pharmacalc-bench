"""Validate PharmaCalc-Bench task files.

The validator checks the YAML schema, task-ID and filename consistency, status
rules, and the reference-solution contract. It imports each reference function,
runs it with the task inputs, and confirms that every requested answer is
returned as a finite number.

Usage:
    python scripts/validate_tasks.py
    python scripts/validate_tasks.py --show
"""

from __future__ import annotations

import argparse
import importlib
import math
import re
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TASKS_DIR = REPO_ROOT / "tasks"
TASK_ID_RE = re.compile(r"^PK-\d{3}$")
TRACK_RE = re.compile(r"^[a-z][a-z0-9-]*$")
REFERENCE_RE = re.compile(r"^[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*$")

REQUIRED_FIELDS = (
    "id",
    "track",
    "difficulty",
    "status",
    "verified_by",
    "title",
    "problem",
    "inputs",
    "reference_solution",
    "answer_format",
    "common_pitfalls",
    "tags",
)
DIFFICULTIES = {"easy", "medium", "hard"}
STATUSES = {"draft", "verified"}


@dataclass
class ValidationResult:
    """Outcome of validating one task file."""

    path: Path
    task: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)
    answers: dict[str, float] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """Return True when no validation errors were recorded."""
        return not self.errors


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _display_path(path: Path) -> str:
    """Return a repository-relative path when possible."""
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _validate_answer_format(
    value: Any, errors: list[str]
) -> list[dict[str, Any]]:
    """Validate answer_format and return normalised answer specifications."""
    if not isinstance(value, list) or not value:
        errors.append("answer_format must be a non-empty list")
        return []

    specs: list[dict[str, Any]] = []
    names: set[str] = set()

    for index, item in enumerate(value, start=1):
        prefix = f"answer_format[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{prefix} must be a mapping")
            continue

        name = item.get("name")
        unit = item.get("unit")
        tolerance = item.get("tolerance_rel", 0.01)
        item_errors_before = len(errors)

        if not _is_non_empty_string(name):
            errors.append(f"{prefix}.name must be a non-empty string")
        elif name in names:
            errors.append(f"{prefix}.name {name!r} is duplicated")
        else:
            names.add(name)

        if not _is_non_empty_string(unit):
            errors.append(f"{prefix}.unit must be a non-empty string")

        if isinstance(tolerance, bool) or not isinstance(
            tolerance, (int, float)
        ):
            errors.append(f"{prefix}.tolerance_rel must be a number")
        else:
            tolerance_value = float(tolerance)
            if not math.isfinite(tolerance_value) or tolerance_value <= 0.0:
                errors.append(
                    f"{prefix}.tolerance_rel must be finite and greater than 0"
                )

        if len(errors) == item_errors_before:
            specs.append(
                {
                    "name": name,
                    "unit": unit,
                    "tolerance_rel": float(tolerance),
                }
            )

    return specs


def _run_reference_solution(
    task: dict[str, Any],
    answer_specs: list[dict[str, Any]],
    result: ValidationResult,
) -> None:
    """Import and run the reference solution, recording answers or errors."""
    reference = task["reference_solution"]
    module_name, function_name = reference.split(":", 1)

    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report any import failure
        result.errors.append(
            f"cannot import reference module {module_name!r}: "
            f"{type(exc).__name__}: {exc}"
        )
        return

    function = getattr(module, function_name, None)
    if not callable(function):
        result.errors.append(
            f"reference function {function_name!r} was not found in "
            f"module {module_name!r}"
        )
        return

    try:
        output = function(**task["inputs"])
    except Exception as exc:  # noqa: BLE001 - report any solver failure
        result.errors.append(
            f"reference function raised {type(exc).__name__}: {exc}"
        )
        return

    if not isinstance(output, Mapping):
        result.errors.append(
            "reference function must return a mapping of answer names to numbers"
        )
        return

    expected_names = [spec["name"] for spec in answer_specs]
    for name in expected_names:
        if name not in output:
            result.errors.append(
                f"reference function did not return answer {name!r}"
            )
            continue
        value = output[name]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            result.errors.append(
                f"answer {name!r} must be a real number, got {value!r}"
            )
            continue
        number = float(value)
        if not math.isfinite(number):
            result.errors.append(
                f"answer {name!r} must be finite, got {value!r}"
            )
            continue
        result.answers[name] = number

    unexpected = [key for key in output if key not in expected_names]
    if unexpected:
        result.errors.append(
            "reference function returned unexpected answer(s): "
            + ", ".join(repr(key) for key in unexpected)
        )


def validate_task_file(path: Path) -> ValidationResult:
    """Validate one task file and compute its reference answers."""
    result = ValidationResult(path=path)

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        result.errors.append(f"cannot read file: {exc}")
        return result

    try:
        task = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        result.errors.append(f"invalid YAML: {exc}")
        return result

    if not isinstance(task, dict):
        result.errors.append("task file must contain a YAML mapping")
        return result

    result.task = task
    errors = result.errors

    missing = [name for name in REQUIRED_FIELDS if name not in task]
    if missing:
        errors.append("missing required field(s): " + ", ".join(missing))
        return result

    task_id = task["id"]
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        errors.append("id must be a string of the form 'PK-###'")
    elif task_id != path.stem:
        errors.append(
            f"id {task_id!r} does not match filename {path.stem!r}"
        )

    track = task["track"]
    if not isinstance(track, str) or not TRACK_RE.fullmatch(track):
        errors.append("track must be a lowercase string such as 'pk'")
    elif track != path.parent.name:
        errors.append(
            f"track {track!r} does not match parent folder "
            f"{path.parent.name!r}"
        )

    difficulty = task["difficulty"]
    if not isinstance(difficulty, str) or difficulty not in DIFFICULTIES:
        errors.append("difficulty must be 'easy', 'medium', or 'hard'")

    status = task["status"]
    verified_by = task["verified_by"]
    if not isinstance(status, str) or status not in STATUSES:
        errors.append("status must be 'draft' or 'verified'")
    elif status == "draft":
        if verified_by is not None:
            errors.append(
                "verified_by must be null when status is 'draft'"
            )
    elif not _is_non_empty_string(verified_by):
        errors.append(
            "verified_by must be a non-empty name when status is 'verified'"
        )

    for field_name in ("title", "problem"):
        if not _is_non_empty_string(task[field_name]):
            errors.append(f"{field_name} must be a non-empty string")

    inputs = task["inputs"]
    if not isinstance(inputs, dict):
        errors.append("inputs must be a mapping")
    elif any(not isinstance(key, str) for key in inputs):
        errors.append("every input name must be a string")

    reference = task["reference_solution"]
    if not isinstance(reference, str) or not REFERENCE_RE.fullmatch(reference):
        errors.append(
            "reference_solution must have the form 'module:function'"
        )

    answer_specs = _validate_answer_format(task["answer_format"], errors)

    pitfalls = task["common_pitfalls"]
    if not isinstance(pitfalls, list):
        errors.append("common_pitfalls must be a list")
    elif any(not _is_non_empty_string(item) for item in pitfalls):
        errors.append("common_pitfalls entries must be non-empty strings")

    tags = task["tags"]
    if not isinstance(tags, list):
        errors.append("tags must be a list")
    elif any(not _is_non_empty_string(item) for item in tags):
        errors.append("tags entries must be non-empty strings")

    if errors:
        return result

    _run_reference_solution(task, answer_specs, result)
    return result


def find_task_files(task_id: str, tasks_dir: Path = TASKS_DIR) -> list[Path]:
    """Return task files whose name matches task_id."""
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        return []
    return sorted(tasks_dir.glob(f"**/{task_id}.yaml"))


def validate_all(tasks_dir: Path = TASKS_DIR) -> list[ValidationResult]:
    """Validate every YAML task under tasks_dir, including duplicate IDs."""
    paths = sorted(tasks_dir.glob("**/*.yaml"))
    results = [validate_task_file(path) for path in paths]

    by_id: dict[str, list[ValidationResult]] = {}
    for result in results:
        if result.task is None:
            continue
        task_id = result.task.get("id")
        if isinstance(task_id, str) and TASK_ID_RE.fullmatch(task_id):
            by_id.setdefault(task_id, []).append(result)

    for task_id, group in by_id.items():
        if len(group) > 1:
            paths_text = ", ".join(_display_path(item.path) for item in group)
            for result in group:
                result.errors.append(
                    f"duplicate task id {task_id!r} in: {paths_text}"
                )

    return results


def _print_task_details(result: ValidationResult) -> None:
    """Print a task's problem and computed reference answers."""
    task = result.task
    assert task is not None
    print("  Problem:")
    for line in str(task["problem"]).rstrip().splitlines():
        print(f"    {line}")
    units = {
        spec["name"]: spec["unit"] for spec in task["answer_format"]
    }
    print("  Reference answers:")
    for name, value in result.answers.items():
        print(f"    {name} = {value:.12g} {units[name]}")


def main(
    argv: Sequence[str] | None = None,
    *,
    tasks_dir: Path | None = None,
) -> int:
    """Run the validator and return a process exit code."""
    parser = argparse.ArgumentParser(
        description="Validate PharmaCalc-Bench task files."
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="print each valid problem and its computed reference answers",
    )
    args = parser.parse_args(argv)

    directory = TASKS_DIR if tasks_dir is None else Path(tasks_dir)
    results = validate_all(directory)

    if not results:
        print(f"No task files found in {_display_path(directory)}.")
        return 0

    passed = 0
    for result in results:
        if result.ok:
            task = result.task
            assert task is not None
            print(
                f"[OK] {task['id']} "
                f"({task['difficulty']}, {task['status']}): {task['title']}"
            )
            if args.show:
                _print_task_details(result)
                print()
            passed += 1
        else:
            print(f"[FAIL] {_display_path(result.path)}")
            for error in result.errors:
                print(f"  - {error}")

    failed = len(results) - passed
    print(f"\nValidated {len(results)} task(s): {passed} passed, {failed} failed.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
