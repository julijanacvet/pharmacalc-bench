# PharmaCalc-Bench

A benchmark of computational pharmacology problems with Python-computed ground
truth and expert-written reviews of AI answers.

**Status:** v0.1.0 in development — no tasks released yet.

## What this is

PharmaCalc-Bench is a public benchmark of pharmacokinetic and medication-safety
calculation problems. Each task gives a model a self-contained problem about a
hypothetical drug. The correct answer is produced by a small, tested Python
function, and an AI model's answer is reviewed line by line by a domain expert.

Every numeric answer is computed, not recalled. Task files contain the problem,
the inputs, and the name of the reference function; they do not contain
hand-typed answers. The reference value is calculated when the task is
validated, which makes the benchmark reproducible and auditable.

## Why

Language models can produce plausible pharmacology calculations that are
subtly wrong. Typical failures include:

- unit conversion errors, such as mixing mL/min with L/h;
- applying bioavailability to the wrong quantity;
- confusing average steady-state concentration with peak or trough
  concentration;
- forgetting drug accumulation during repeated dosing;
- ignoring a stated constraint, such as renal impairment or a dosing interval
  shorter than the time needed to reach steady state;
- rounding early and carrying the error into the final answer.

Each task isolates a small number of these failure modes. The expert critique
records what the model did, why it was wrong, and how severe the error is.

## Task structure

Task YAML, model-answer, and critique formats are documented in
[docs/TASK_FORMAT.md](docs/TASK_FORMAT.md).

Every task has four parts:

1. **Problem** — the exact text given to the AI model, including the
   hypothetical drug, all parameters with units, and the values the model must
   report.
2. **Reference solution** — a Python function in `pharmacalc/` that computes
   the ground truth. Its result is checked by pytest and by the task validator.
3. **Model answer** — collected by the author from a named AI model and stored
   verbatim in `model_answers/`.
4. **Expert critique** — written by the author in `critiques/`, with a verdict,
   the final-answer check, the errors found, the reasoning failure, and a
   severity rating.

## Repository layout

```text
PharmaCalc-Bench/
├── pharmacalc/          # tested reference calculations (ground truth)
├── tasks/pk/            # task definitions in YAML
├── model_answers/pk/    # collected AI answers, written by the author
├── critiques/pk/        # expert critiques, written by the author
├── scripts/             # task validation and scoring tools
├── tests/               # pytest suite
├── docs/                # methodology and safety scope
├── AGENTS.md            # build rules for AI assistants
├── CITATION.cff         # citation metadata
├── DATA_LICENSE.md      # CC BY 4.0 for task data
├── LICENSE              # MIT for code
└── README.md
```

## How to run the tests

PharmaCalc-Bench requires Python 3.11 or later.

```bash
python -m pip install -r requirements.txt
python -m pytest -q
```

Validate task files with:

```powershell
python scripts/validate_tasks.py
python scripts/validate_tasks.py --show
```

## Safety scope

The benchmark covers pharmacokinetics, medication safety, and drug-property
calculations only, and it uses hypothetical drugs with realistic but invented
parameters. It contains no content about toxins, poisons, chemical weapons, or
the synthesis or extraction of hazardous substances.

See [docs/SAFETY_SCOPE.md](docs/SAFETY_SCOPE.md) for the full scope and the
reasoning behind it.

> **Disclaimer:** Educational and research use only. Uses hypothetical drugs.
> Not medical advice.

## Author

**Julijana Cvetkovska** — Independent Researcher

Julijana is an AI evaluator, AI red teamer, and training data specialist with a
pharmacy technician education (pharmacology, analytical chemistry,
biochemistry), a BA in linguistics, and more than 15 years of experience in
technical research and software quality assurance.

- GitHub: <https://github.com/julijanacvet>
- LinkedIn: <https://www.linkedin.com/in/julijanacvetkovska>
- Email: <julijana.cvet@gmail.com>

## Licence

The Python code is released under the MIT Licence (see [LICENSE](LICENSE)).
The task data in `tasks/` is released under the Creative Commons Attribution
4.0 International Licence (see [DATA_LICENSE.md](DATA_LICENSE.md)).

## How to cite

Citation metadata is provided in [CITATION.cff](CITATION.cff). A DOI will be
assigned through Zenodo when version 0.1.0 is released. Until then, please cite
the repository and the version listed in the citation file.
