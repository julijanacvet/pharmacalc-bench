# Methodology

This document describes how PharmaCalc-Bench tasks are designed, how ground
truth is produced, and how model answers are collected and reviewed.

## Four-part task design

Every task consists of four artefacts.

### 1. Problem

The problem is the exact text given to an AI model. It must:

- use a hypothetical drug ("Drug A", "Drug B", ...);
- state every parameter needed to solve it, with units;
- state the model assumptions that a solver cannot infer, such as
  one-compartment behaviour, first-order elimination, or average
  steady-state conditions;
- say which quantities the model must report, with units and the expected
  rounding.

The problem is self-contained. A reader should not need outside data or a
particular clinical guideline to solve it.

### 2. Reference solution

The reference solution is a Python function that computes the ground truth from
the task inputs. It lives in `pharmacalc/` and uses the shared functions in the
`pharmacalc` package. The function returns a dictionary with one entry for
every value the problem asks for.

The ground-truth rule is absolute:

- expected answers are computed by code, never written from memory;
- task YAML files contain inputs and answer names, never numeric answers;
- every reference formula is checked by pytest against independent hand
  calculations shown in the test comments;
- the task validator imports each reference function, runs it with the task
  inputs, and confirms that every requested answer is present and finite.

#### Cockcroft-Gault convention

The Cockcroft-Gault equation is used only for adults. In this benchmark:

- the weight input is total (actual) body weight unless a task explicitly
  states otherwise;
- serum creatinine is expressed in mg/dL;
- the equation assumes stable renal function;
- it is not valid for children (patients under 18 years of age).

Every task that uses Cockcroft-Gault must state in the problem which body
weight is used. This statement is checked during expert verification.

### 3. Model answer

The model answer is collected by the human author. For each answer, the author
records:

- the task ID and the exact model name and version;
- the date of collection and the interface used;
- the exact prompt sent to the model;
- the complete answer, pasted verbatim;
- the final values extracted from the answer for scoring.

Answers are not edited, shortened, or corrected. If a model is run more than
once, each run is stored as a separate record.

### 4. Expert critique

The expert critique is written by the human author. It contains:

- **Verdict** — whether the answer is correct, partly correct, or incorrect;
- **Final-answer check** — each requested value compared with the reference;
- **Errors found** — classified as assumption, unit, arithmetic, missing
  constraint, or hallucinated fact;
- **Where the reasoning went wrong** — the specific step or steps that failed;
- **Severity** — critical, major, or minor;
- **Notes** — any additional observation worth recording.

### Error categories

| Category | Meaning |
| --- | --- |
| Assumption | Uses an unstated or incorrect model assumption, such as assuming immediate absorption or linear kinetics without justification. |
| Unit | Converts or combines units incorrectly, or drops a conversion factor. |
| Arithmetic | Sets the calculation up correctly but makes a numerical error. |
| Missing constraint | Ignores a condition stated in the problem, such as renal impairment, a dosing interval, or incomplete steady state. |
| Hallucinated fact | Invents a parameter, formula, or clinical fact that is not in the problem and is not a standard pharmacokinetic relation. |

### Severity

| Severity | Meaning |
| --- | --- |
| Critical | A final value is wrong, or an error changes the result by more than the stated tolerance. |
| Major | The final values are correct, but a substantive reasoning step, assumption, or constraint is wrong or missing. |
| Minor | A presentation, notation, or rounding issue that does not change the final values. |

Severity is the author's expert judgment. It is recorded per critique and is
not generated automatically.

## Verification workflow

1. The engineering assistant creates a task with `status: draft` and
   `verified_by: null`.
2. The author independently recomputes the reference values, checks the problem
   wording, units, assumptions, and answer format, and runs the validator.
3. Only the author changes the status to `verified` and records their name in
   `verified_by`.
4. Any later change to the problem, inputs, or reference solution requires
   re-verification.

The benchmark therefore distinguishes between tasks that exist and tasks that
have been checked by the domain expert.

## Reproducibility

- The Python environment is described in `requirements.txt`.
- Reference calculations are deterministic and have no hidden state.
- The validator and scorer compute reference values at run time from the task
  inputs.
- Tests show the hand calculation behind every formula and cover invalid
  inputs as well as expected results.

## Limitations

- The task set is small and is not a leaderboard.
- Most tasks use one-compartment, linear pharmacokinetic models; this is a
  deliberate simplification, not a claim about all drugs.
- Hypothetical drugs keep the benchmark free of memorised clinical answers, but
  they also limit clinical realism.
- A model answer is a snapshot of one model, version, and date. It does not
  support general claims about a model family.
- Critiques are one expert's judgment. They are not inter-rater validated.

## Results

Coming in v0.1.
