# Safety Scope

PharmaCalc-Bench is an educational and research benchmark. This document
explains what it covers, what it deliberately excludes, and why.

## Hypothetical drugs only

Every task uses a hypothetical drug such as "Drug A", "Drug B", or "Drug C".
The parameters are realistic enough to make the calculation meaningful, but
they are invented for the benchmark.

This rule has two purposes:

1. **Benchmark integrity.** A model cannot answer from memorised clinical
   facts about a real product. It must reason from the parameters in the
   problem.
2. **Safety.** The numbers are not dosing recommendations for any real
   medicine, and the project cannot be mistaken for clinical guidance.

The benchmark does not tell anyone how much of a real drug to give.

## In scope

- Pharmacokinetic calculations: half-life, elimination rate constant,
  clearance, volume of distribution, concentrations after IV bolus dosing,
  loading and maintenance doses, accumulation, and time to steady state.
- Renal function adjustment using Cockcroft-Gault creatinine clearance.
- Medication-safety reasoning that follows from those calculations, such as
  unit conversion, checking assumptions, and noticing missing constraints.
- Drug properties only where they are needed for the calculation, such as
  bioavailability or the fraction of renal elimination.

## Out of scope

- Toxins, poisons, and chemical weapons.
- The synthesis, extraction, purification, or weaponisation of hazardous
  substances.
- Lethal or toxic dose calculations.
- Dosing recommendations for real patients or real medicines.
- Diagnosis, treatment decisions, or any form of medical advice.
- Content that requires clinical data the problem does not provide.

A task that drifts toward any of these topics is rewritten or removed. The
benchmark stays within calculation problems whose inputs are fully stated and
whose purpose is evaluating reasoning, not guiding care.

## Boundary examples

| Topic | Status |
| --- | --- |
| Clearance adjustment for a hypothetical drug in renal impairment | In scope |
| Half-life and accumulation during repeated dosing | In scope |
| Unit conversion from mL/min to L/h | In scope |
| How to synthesize a chemical compound | Out of scope |
| The lethal dose of a substance | Out of scope |
| A dosing schedule for a named medicine in a real patient | Out of scope |

## Disclaimer

> **Disclaimer:** Educational and research use only. Uses hypothetical drugs.
> Not medical advice.
