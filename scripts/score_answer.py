"""Score a model answer against a task's computed reference values.

Usage:
    python scripts/score_answer.py PK-001 --answer c_6h=5.49 --answer t_below=14.0

The reference values are computed from the task inputs; they are never read
from the task file.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Sequence
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts import validate_tasks  # noqa: E402


def relative_error(reference: float, given: float) -> float:
    """Return |given - reference| / |reference|, or infinity if undefined."""
    if not math.isfinite(given):
        return math.inf
    if reference == 0.0:
        return 0.0 if given == 0.0 else math.inf
    return abs(given - reference) / abs(reference)


def _parse_answers(raw_answers: list[str]) -> dict[str, float]:
    """Parse repeated NAME=VALUE arguments into a mapping."""
    answers: dict[str, float] = {}
    for raw in raw_answers:
        name, separator, value_text = raw.partition("=")
        name = name.strip()
        if not separator or not name:
            raise ValueError(
                f"invalid --answer {raw!r}; expected name=value"
            )
        try:
            value = float(value_text)
        except ValueError as exc:
            raise ValueError(
                f"invalid value in --answer {raw!r}; expected a number"
            ) from exc
        if name in answers:
            raise ValueError(f"duplicate --answer for {name!r}")
        answers[name] = value
    return answers


def main(
    argv: Sequence[str] | None = None,
    *,
    tasks_dir: Path | None = None,
) -> int:
    """Run the scorer and return a process exit code."""
    parser = argparse.ArgumentParser(
        description="Score extracted model-answer values against a task."
    )
    parser.add_argument("task_id", help="task ID, for example PK-001")
    parser.add_argument(
        "--answer",
        action="append",
        required=True,
        metavar="NAME=VALUE",
        help="answer value to check; repeat for each requested answer",
    )
    args = parser.parse_args(argv)

    try:
        given_values = _parse_answers(args.answer)
    except ValueError as exc:
        parser.error(str(exc))

    directory = (
        validate_tasks.TASKS_DIR
        if tasks_dir is None
        else Path(tasks_dir)
    )
    matches = validate_tasks.find_task_files(args.task_id, directory)
    if not matches:
        print(f"Task {args.task_id!r} not found in {directory}.")
        return 1
    if len(matches) > 1:
        print(f"Task id {args.task_id!r} is duplicated:")
        for path in matches:
            print(f"  - {path}")
        return 1

    result = validate_tasks.validate_task_file(matches[0])
    if not result.ok:
        print(f"Task {args.task_id} is not valid; fix it before scoring:")
        for error in result.errors:
            print(f"  - {error}")
        return 1

    task = result.task
    assert task is not None
    specs = task["answer_format"]
    expected_names = [spec["name"] for spec in specs]
    unknown = sorted(set(given_values) - set(expected_names))
    if unknown:
        print("Unknown answer name(s): " + ", ".join(unknown))
        print("Expected: " + ", ".join(expected_names))
        return 1

    print(f"Task {task['id']}: {task['title']}")
    passed_count = 0
    for spec in specs:
        name = spec["name"]
        unit = spec["unit"]
        tolerance = float(spec.get("tolerance_rel", 0.01))
        reference = result.answers[name]

        if name not in given_values:
            print(
                f"  {name}: reference {reference:.10g} {unit} | "
                f"given: not provided | FAIL"
            )
            continue

        given = given_values[name]
        error = relative_error(reference, given)
        passed = math.isfinite(error) and error <= tolerance
        if passed:
            passed_count += 1
        error_text = f"{error:.4%}" if math.isfinite(error) else "n/a"
        print(
            f"  {name}: reference {reference:.10g} {unit} | "
            f"given {given:.10g} {unit} | "
            f"relative error {error_text} | "
            f"tolerance {tolerance:.2%} | "
            f"{'PASS' if passed else 'FAIL'}"
        )

    total = len(specs)
    all_passed = passed_count == total
    print(f"\n{passed_count}/{total} value(s) within tolerance.")
    print("Result: PASS" if all_passed else "Result: FAIL")
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
