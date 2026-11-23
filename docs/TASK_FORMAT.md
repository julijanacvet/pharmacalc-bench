# Task Format

This document defines the file format for PharmaCalc-Bench tasks, model
answers, and critiques. It is the reference for task authors, reviewers, and
the validation scripts.

## Ground-truth rule

Task YAML files never contain numeric answers. They contain the problem, the
inputs, and the name of the Python reference function. The reference function
computes the answers, and the validator checks them at run time.

## Task files

### Location and naming

- One task per YAML file.
- Path: `tasks/<track>/<id>.yaml`.
- The task ID has the form `PK-###`, for example `PK-001`.
- The file name must equal the task ID: `PK-001.yaml`.
- The `track` field must equal the parent folder name: `pk`.
- Files are UTF-8 encoded.

### Fields

| Field | Type | Required | Rules |
| --- | --- | --- | --- |
| `id` | string | yes | `PK-###`; must match the file name. |
| `track` | string | yes | Must match the parent folder, currently `pk`. |
| `difficulty` | string | yes | One of `easy`, `medium`, `hard`. |
| `status` | string | yes | One of `draft`, `verified`. |
| `verified_by` | string or null | yes | `null` for a draft; a non-empty name for a verified task. |
| `title` | string | yes | Short human-readable title. |
| `problem` | string | yes | Exact text given to the model. Use a hypothetical drug, state every parameter with units, and state the required outputs and assumptions. |
| `inputs` | mapping | yes | Machine-readable parameters passed to the reference function as keyword arguments. |
| `reference_solution` | string | yes | `module:function`, for example `pharmacalc.tasks_pk:solve_pk_001`. |
| `answer_format` | list | yes | Non-empty list of answer specifications (see below). |
| `common_pitfalls` | list | yes | Written by the human author. The engineering assistant leaves it empty. |
| `tags` | list | yes | Short strings for discovery. |

### Answer format

Each entry in `answer_format` is a mapping:

| Key | Type | Required | Rules |
| --- | --- | --- | --- |
| `name` | string | yes | Must match a key returned by the reference function. Names must be unique within a task. |
| `unit` | string | yes | Unit shown to the reader, for example `mg/L`, `h`, or `mL/min`. |
| `tolerance_rel` | number | no | Relative tolerance; default `0.01` (1%). Must be greater than 0. |

The scorer uses:

```text
relative error = |given - reference| / |reference|
```

A value passes when the relative error is less than or equal to
`tolerance_rel`. If the reference value is zero, only an exact zero passes.

### Reference solution contract

The reference solution is a Python callable in the `pharmacalc` package. It:

- is imported from a `module:function` string;
- is called as `function(**inputs)`;
- returns a mapping whose keys are exactly the names in `answer_format`;
- returns finite real numbers, not booleans, strings, or missing values;
- uses the tested functions in `pharmacalc/` rather than hard-coded answers.

Missing answers, extra answers, import failures, exceptions, and non-finite
values are validation errors.

### Status and verification

- `draft` means the task exists but has not been checked by the human author.
  `verified_by` must be `null`.
- `verified` means the human author has checked the problem, inputs,
  reference solution, units, assumptions, and answer format. `verified_by`
  must contain the author's name.
- Only the human author changes `status` and `verified_by`.
- Any later change to the problem, inputs, or reference solution requires
  re-verification.

### Cockcroft-Gault tasks

Every task that uses Cockcroft-Gault must:

- state in the problem which body weight is used; the benchmark default is
  total (actual) body weight unless the task explicitly says otherwise;
- use serum creatinine in mg/dL;
- state the stable-renal-function assumption;
- use an adult patient, because the equation is not valid for children.

The `inputs` mapping should contain `age_y`, `weight_kg`, `scr_mg_per_dl`, and
`female`, using the same units.

### Skeleton

The following skeleton shows the field structure. Replace every placeholder;
it is not a runnable task.

```yaml
id: "PK-XXX"
track: "pk"
difficulty: "easy"
status: "draft"
verified_by: null
title: "<short descriptive title>"
problem: |
  <Exact problem text with a hypothetical drug, all parameters and units,
  assumptions, and the values the model must report.>
inputs:
  <parameter_name>: <number>
reference_solution: "pharmacalc.tasks_pk:solve_pk_xxx"
answer_format:
  - name: "<answer_name>"
    unit: "<unit>"
common_pitfalls: []
tags:
  - "<tag>"
```

## Model answer files

Model answers are written by the human author, never by the engineering
assistant.

### Location and naming

- Path: `model_answers/<track>/<id>__<model-slug>.md`.
- Example: `model_answers/pk/PK-001__example-model.md`.
- One file per task, model, and run.
- `TEMPLATE.md` is a template, not a result.

### Metadata

The file starts with a YAML metadata block delimited by `---`:

| Field | Type | Rules |
| --- | --- | --- |
| `task_id` | string | Must match an existing task ID. |
| `model` | string | Model or product name. |
| `model_version` | string | Exact model version or snapshot identifier. |
| `date` | string | Collection date in ISO 8601 form, `YYYY-MM-DD`. |
| `interface` | string | Where the answer was collected, for example a web chat or API. |
| `extracted_values` | mapping | Answer name to numeric value, used for scoring. Keys must match the task's `answer_format` names. |

The body contains:

- `## Prompt` — the exact prompt sent to the model;
- `## Answer` — the complete model answer, pasted verbatim.

Do not edit, shorten, or correct the model answer.

## Critique files

Critiques are written by the human author, never by the engineering assistant.

### Location and naming

- Path: `critiques/<track>/<id>__<model-slug>.md`.
- The `task_id`, `model`, and `model_version` values must match the corresponding
  model answer file.
- `TEMPLATE.md` is a template, not a result.

### Metadata

The file starts with a YAML metadata block delimited by `---`:

| Field | Type | Rules |
| --- | --- | --- |
| `task_id` | string | Must match an existing task ID. |
| `model` | string | Must match the model answer's `model`. |
| `model_version` | string | Must match the model answer's `model_version`. |
| `verdict` | string | One of `correct`, `partly_correct`, `incorrect`. |
| `error_types` | list | Any of `assumption`, `unit`, `arithmetic`, `missing_constraint`, `hallucinated_fact`. Empty when there are no errors. |
| `severity` | string or null | One of `critical`, `major`, `minor`, or `null` when there are no errors. |

The body uses these headings:

- `## Verdict`
- `## Final-answer check`
- `## Errors found` with `### Assumption`, `### Unit`, `### Arithmetic`,
  `### Missing constraint`, and `### Hallucinated fact`
- `## Where the reasoning went wrong`
- `## Severity`
- `## Notes`

## Validation and scoring

Run from the repository root:

```powershell
python scripts/validate_tasks.py
python scripts/validate_tasks.py --show
python scripts/score_answer.py PK-001 --answer c_6h=5.49 --answer t_below=14.0
```

`validate_tasks.py` exits with code 0 when every task is valid and code 1 when
any task fails. `--show` also prints each valid problem and its computed
reference answers. `score_answer.py` prints PASS or FAIL for each requested
value and exits with code 1 if any value fails. Every answer in `answer_format`
must be supplied; a missing value is a FAIL.
