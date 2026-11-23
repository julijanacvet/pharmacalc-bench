# AGENTS.md

Working rules for this repository. These rules apply to every agent and every
phase of the project.

## Project

PharmaCalc-Bench is a benchmark of computational pharmacology problems. Each
task has: (a) a problem, (b) a Python reference solution that computes the
ground truth, (c) a model answer collected by the human author from an AI
model, (d) a critique of that answer written by the human author. Author:
Julijana Cvetkovska.

## Rules

1. Project: PharmaCalc-Bench is a benchmark of computational pharmacology
   problems. Each task has: (a) a problem, (b) a Python reference solution
   that computes the ground truth, (c) a model answer collected by the human
   author from an AI model, (d) a critique of that answer written by the human
   author. Author: Julijana Cvetkovska.
2. Ground truth comes from tested code, never from memory. Every expected
   answer is computed by a Python function in `pharmacalc/` and checked with
   pytest. Never type a numeric answer into a task file by hand.
3. The agent never writes model answers or critiques. Files in
   `model_answers/` and `critiques/` are written by the human author. The
   agent may only create empty templates.
4. Every task the agent creates has `status: draft` and `verified_by: null`.
   Only the human author changes these.
5. Use hypothetical drugs only ("Drug A", "Drug B"...) with realistic but
   invented parameters. This prevents memorized answers and keeps the project
   from being clinical dosing advice.
6. Safety scope: only pharmacokinetics, medication safety and drug-property
   content. Never create content about toxins, poisons, chemical weapons, or
   synthesis or extraction of hazardous substances.
7. Ask first before: deleting files, changing licences, git push, tags or
   releases, installing packages not in `requirements.txt`, or downloading
   data.
8. Keep it simple: plain Python 3.11+, numpy, scipy, pyyaml, pytest. Small
   functions. Docstrings with formula, units and assumptions. Units in
   variable names (`dose_mg`, `vd_l`, `cl_l_per_h`, `t_half_h`,
   `conc_mg_per_l`).
9. Licences: code MIT, task data CC BY 4.0.
10. Done means: pytest passes, `python scripts/validate_tasks.py` passes,
    README is accurate.

## Working agreement

- Work in five phases, one phase at a time. At the end of each phase, list
  every file created or changed, show the test output, give the exact commands
  to check the work, then stop and wait for the author's "continue".
- The human author is the domain expert and makes the final scientific and
  editorial decisions. When something is scientifically unclear, ask instead
  of guessing.
- The agent creates drafts. The author verifies every task before it is marked
  `verified`.
- Keep every file readable for a senior scientist and a hiring manager: clear
  English, explicit formulas and units, no unnecessary complexity, and no
  claims the project cannot support.
