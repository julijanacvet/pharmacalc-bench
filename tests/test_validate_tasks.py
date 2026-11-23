"""Tests for scripts/validate_tasks.py."""

from pathlib import Path

import pytest
import yaml

from scripts import validate_tasks

SOLUTIONS = '''
def solve_sample(dose_mg, vd_l):
    return {"c0_mg_per_l": dose_mg / vd_l}


def solve_missing(dose_mg, vd_l):
    return {}


def solve_extra(dose_mg, vd_l):
    return {"c0_mg_per_l": dose_mg / vd_l, "extra": 1.0}


def solve_raises(dose_mg, vd_l):
    raise ValueError("boom")


def solve_nan(dose_mg, vd_l):
    return {"c0_mg_per_l": float("nan")}


def solve_bool(dose_mg, vd_l):
    return {"c0_mg_per_l": True}
'''


def _write_task(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    remove: tuple[str, ...] = (),
    answer_format: list[dict[str, object]] | None = None,
    **overrides: object,
) -> Path:
    """Write a valid sample task and its temporary solution module."""
    (tmp_path / "sample_solutions.py").write_text(
        SOLUTIONS, encoding="utf-8"
    )
    monkeypatch.syspath_prepend(str(tmp_path))

    task: dict[str, object] = {
        "id": "PK-001",
        "track": "pk",
        "difficulty": "easy",
        "status": "draft",
        "verified_by": None,
        "title": "Sample task",
        "problem": "A sample problem.",
        "inputs": {"dose_mg": 500.0, "vd_l": 50.0},
        "reference_solution": "sample_solutions:solve_sample",
        "answer_format": [
            {"name": "c0_mg_per_l", "unit": "mg/L"},
        ],
        "common_pitfalls": [],
        "tags": ["sample"],
    }
    if answer_format is not None:
        task["answer_format"] = answer_format
    for field_name in remove:
        task.pop(field_name, None)
    task.update(overrides)

    path = tmp_path / "tasks" / "pk" / "PK-001.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(task, sort_keys=False), encoding="utf-8"
    )
    return path


def test_valid_task_passes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(tmp_path, monkeypatch)
    result = validate_tasks.validate_task_file(path)

    assert result.errors == []
    assert result.answers["c0_mg_per_l"] == pytest.approx(10.0)


def test_missing_required_field_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(tmp_path, monkeypatch, remove=("title",))
    result = validate_tasks.validate_task_file(path)

    assert any("title" in error for error in result.errors)


def test_id_must_match_filename(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(tmp_path, monkeypatch, id="PK-002")
    result = validate_tasks.validate_task_file(path)

    assert any("does not match filename" in error for error in result.errors)


def test_track_must_match_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(tmp_path, monkeypatch, track="other")
    result = validate_tasks.validate_task_file(path)

    assert any("does not match parent folder" in error for error in result.errors)


def test_verified_task_requires_verified_by(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(
        tmp_path,
        monkeypatch,
        status="verified",
        verified_by=None,
    )
    result = validate_tasks.validate_task_file(path)

    assert any("verified_by" in error for error in result.errors)


def test_draft_task_requires_null_verified_by(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(
        tmp_path,
        monkeypatch,
        verified_by="Julijana Cvetkovska",
    )
    result = validate_tasks.validate_task_file(path)

    assert any("verified_by must be null" in error for error in result.errors)


def test_invalid_difficulty_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(tmp_path, monkeypatch, difficulty="expert")
    result = validate_tasks.validate_task_file(path)

    assert any("difficulty" in error for error in result.errors)


def test_reference_import_failure_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(
        tmp_path,
        monkeypatch,
        reference_solution="missing_module:solve",
    )
    result = validate_tasks.validate_task_file(path)

    assert any("cannot import" in error for error in result.errors)


def test_missing_reference_answer_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(
        tmp_path,
        monkeypatch,
        reference_solution="sample_solutions:solve_missing",
        answer_format=[
            {"name": "c0_mg_per_l", "unit": "mg/L"},
            {"name": "t_half_h", "unit": "h"},
        ],
    )
    result = validate_tasks.validate_task_file(path)

    assert any("did not return answer 'c0_mg_per_l'" in error for error in result.errors)
    assert any("did not return answer 't_half_h'" in error for error in result.errors)


def test_extra_reference_answer_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(
        tmp_path,
        monkeypatch,
        reference_solution="sample_solutions:solve_extra",
    )
    result = validate_tasks.validate_task_file(path)

    assert any("unexpected answer" in error for error in result.errors)


def test_reference_exception_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(
        tmp_path,
        monkeypatch,
        reference_solution="sample_solutions:solve_raises",
    )
    result = validate_tasks.validate_task_file(path)

    assert any("ValueError" in error and "boom" in error for error in result.errors)


def test_non_finite_reference_answer_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(
        tmp_path,
        monkeypatch,
        reference_solution="sample_solutions:solve_nan",
    )
    result = validate_tasks.validate_task_file(path)

    assert any("must be finite" in error for error in result.errors)


def test_boolean_reference_answer_is_reported(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(
        tmp_path,
        monkeypatch,
        reference_solution="sample_solutions:solve_bool",
    )
    result = validate_tasks.validate_task_file(path)

    assert any("must be a real number" in error for error in result.errors)


def test_duplicate_answer_names_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(
        tmp_path,
        monkeypatch,
        answer_format=[
            {"name": "c0_mg_per_l", "unit": "mg/L"},
            {"name": "c0_mg_per_l", "unit": "mg/L"},
        ],
    )
    result = validate_tasks.validate_task_file(path)

    assert any("is duplicated" in error for error in result.errors)


def test_tolerance_must_be_positive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _write_task(
        tmp_path,
        monkeypatch,
        answer_format=[
            {"name": "c0_mg_per_l", "unit": "mg/L", "tolerance_rel": 0},
        ],
    )
    result = validate_tasks.validate_task_file(path)

    assert any("tolerance_rel" in error for error in result.errors)


def test_invalid_yaml_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "tasks" / "pk" / "PK-001.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("id: [unclosed", encoding="utf-8")

    result = validate_tasks.validate_task_file(path)

    assert any("invalid YAML" in error for error in result.errors)


def test_non_mapping_yaml_is_reported(tmp_path: Path) -> None:
    path = tmp_path / "tasks" / "pk" / "PK-001.yaml"
    path.parent.mkdir(parents=True)
    path.write_text("- item\n", encoding="utf-8")

    result = validate_tasks.validate_task_file(path)

    assert any("must contain a YAML mapping" in error for error in result.errors)


def test_main_returns_zero_for_valid_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_task(tmp_path, monkeypatch)

    exit_code = validate_tasks.main([], tasks_dir=tmp_path / "tasks")

    assert exit_code == 0


def test_show_prints_problem_and_reference_answers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write_task(tmp_path, monkeypatch)

    exit_code = validate_tasks.main(
        ["--show"], tasks_dir=tmp_path / "tasks"
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "A sample problem." in output
    assert "c0_mg_per_l = 10 mg/L" in output


def test_main_returns_one_for_invalid_task(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _write_task(tmp_path, monkeypatch, remove=("title",))

    exit_code = validate_tasks.main([], tasks_dir=tmp_path / "tasks")

    assert exit_code == 1


def test_main_returns_zero_with_no_tasks(tmp_path: Path) -> None:
    exit_code = validate_tasks.main([], tasks_dir=tmp_path / "empty")

    assert exit_code == 0


def test_duplicate_task_ids_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_path = _write_task(tmp_path, monkeypatch)
    task = yaml.safe_load(first_path.read_text(encoding="utf-8"))
    task["track"] = "other"

    second_path = tmp_path / "tasks" / "other" / "PK-001.yaml"
    second_path.parent.mkdir(parents=True)
    second_path.write_text(
        yaml.safe_dump(task, sort_keys=False), encoding="utf-8"
    )

    results = validate_tasks.validate_all(tmp_path / "tasks")

    assert len(results) == 2
    assert all(
        any("duplicate task id" in error for error in result.errors)
        for result in results
    )
