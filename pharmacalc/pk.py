"""One-compartment pharmacokinetic reference calculations.

These functions compute the ground truth for PharmaCalc-Bench tasks. They are
pure, deterministic, and independent of any task file.

Unit conventions:
    dose_mg: mg
    vd_l: L
    cl_l_per_h: L/h
    k_per_h: 1/h
    t_half_h, t_h, tau_h: h
    concentration: mg/L
    age_y: years
    weight_kg: kg
    scr_mg_per_dl: mg/dL
    creatinine clearance: mL/min

Model assumptions:
    Linear one-compartment pharmacokinetics with first-order elimination,
    immediate IV bolus input where named, constant dosing intervals, and
    steady state where named. No protein-binding correction, body-size
    normalisation, or inter-individual variability is applied.

Validation:
    All public functions reject non-numeric, non-finite, and out-of-range
    inputs with ValueError.
"""

import math

_LN2 = math.log(2.0)


def _finite_real(name: str, value: float) -> float:
    """Return ``value`` as a finite float, or raise ValueError."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a real number, got {value!r}")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name} must be finite, got {value!r}") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return number


def _positive(name: str, value: float) -> float:
    """Return ``value`` as a finite float greater than zero."""
    number = _finite_real(name, value)
    if number <= 0.0:
        raise ValueError(f"{name} must be greater than 0, got {value!r}")
    return number


def _non_negative(name: str, value: float) -> float:
    """Return ``value`` as a finite float greater than or equal to zero."""
    number = _finite_real(name, value)
    if number < 0.0:
        raise ValueError(f"{name} must be 0 or greater, got {value!r}")
    return number


def _bioavailability(f: float) -> float:
    """Return a validated bioavailability fraction in (0, 1]."""
    f = _positive("f", f)
    if f > 1.0:
        raise ValueError("f must be greater than 0 and at most 1")
    return f


def elimination_rate_constant(t_half_h: float) -> float:
    """Return the first-order elimination rate constant.

    Formula: k = ln(2) / t_half.
    Units: t_half_h in hours, k_per_h in 1/hour.
    Assumption: first-order elimination (constant half-life).
    """
    t_half_h = _positive("t_half_h", t_half_h)
    return _LN2 / t_half_h


def half_life(k_per_h: float) -> float:
    """Return the first-order elimination half-life.

    Formula: t_half = ln(2) / k.
    Units: k_per_h in 1/hour, t_half_h in hours.
    Assumption: first-order elimination (constant half-life).
    """
    k_per_h = _positive("k_per_h", k_per_h)
    return _LN2 / k_per_h


def clearance(k_per_h: float, vd_l: float) -> float:
    """Return total clearance from the rate constant and volume of distribution.

    Formula: CL = k * Vd.
    Units: k_per_h in 1/hour, vd_l in litres, cl_l_per_h in L/hour.
    Assumption: one-compartment linear kinetics, so clearance is constant.
    """
    k_per_h = _positive("k_per_h", k_per_h)
    vd_l = _positive("vd_l", vd_l)
    return k_per_h * vd_l


def initial_concentration_iv_bolus(dose_mg: float, vd_l: float) -> float:
    """Return the concentration immediately after an IV bolus.

    Formula: C0 = Dose / Vd.
    Units: dose_mg in mg, vd_l in litres, C0 in mg/L.
    Assumption: instantaneous delivery into one compartment, with no
    elimination before t = 0.
    """
    dose_mg = _positive("dose_mg", dose_mg)
    vd_l = _positive("vd_l", vd_l)
    return dose_mg / vd_l


def concentration_iv_bolus(
    dose_mg: float,
    vd_l: float,
    k_per_h: float,
    t_h: float,
) -> float:
    """Return the plasma concentration after an IV bolus at time t.

    Formula: C(t) = (Dose / Vd) * exp(-k * t).
    Units: dose_mg in mg, vd_l in litres, k_per_h in 1/hour, t_h in hours,
    C(t) in mg/L.
    Assumptions: one-compartment model, immediate IV bolus, first-order
    elimination, and t >= 0.
    """
    dose_mg = _positive("dose_mg", dose_mg)
    vd_l = _positive("vd_l", vd_l)
    k_per_h = _positive("k_per_h", k_per_h)
    t_h = _non_negative("t_h", t_h)
    c0_mg_per_l = dose_mg / vd_l
    return c0_mg_per_l * math.exp(-k_per_h * t_h)


def time_to_concentration(
    c0: float,
    c_target: float,
    k_per_h: float,
) -> float:
    """Return the time for a first-order concentration to fall to a target.

    Formula: t = ln(C0 / C_target) / k.
    Units: c0 and c_target in mg/L, k_per_h in 1/hour, t_h in hours.
    Assumption: one-compartment first-order decline with
    0 < C_target < C0, so that the time is positive.
    """
    c0 = _positive("c0", c0)
    c_target = _positive("c_target", c_target)
    k_per_h = _positive("k_per_h", k_per_h)
    if c_target >= c0:
        raise ValueError("c_target must be less than c0 for a positive time")
    return math.log(c0 / c_target) / k_per_h


def loading_dose(
    c_target_mg_per_l: float,
    vd_l: float,
    f: float = 1.0,
) -> float:
    """Return a loading dose for a target concentration.

    Formula: LD = (C_target * Vd) / F.
    Units: C_target in mg/L, vd_l in litres, LD in mg.
    Assumptions: one-compartment model, the target is the concentration
    immediately after the dose, and F is bioavailability (1.0 for IV).
    """
    c_target_mg_per_l = _positive("c_target_mg_per_l", c_target_mg_per_l)
    vd_l = _positive("vd_l", vd_l)
    f = _bioavailability(f)
    return (c_target_mg_per_l * vd_l) / f


def maintenance_dose(
    css_avg_mg_per_l: float,
    cl_l_per_h: float,
    tau_h: float,
    f: float = 1.0,
) -> float:
    """Return the maintenance dose per dosing interval at steady state.

    Formula: MD = (Css_avg * CL * tau) / F.
    Units: Css_avg in mg/L, cl_l_per_h in L/hour, tau_h in hours, MD in mg per
    interval.
    Assumptions: linear kinetics, average steady-state concentration over the
    interval, and F is bioavailability (1.0 for IV).
    """
    css_avg_mg_per_l = _positive("css_avg_mg_per_l", css_avg_mg_per_l)
    cl_l_per_h = _positive("cl_l_per_h", cl_l_per_h)
    tau_h = _positive("tau_h", tau_h)
    f = _bioavailability(f)
    return (css_avg_mg_per_l * cl_l_per_h * tau_h) / f


def accumulation_factor(k_per_h: float, tau_h: float) -> float:
    """Return the accumulation factor for repeated IV bolus dosing.

    Formula: R = 1 / (1 - exp(-k * tau)).
    Units: k_per_h in 1/hour, tau_h in hours, R dimensionless.
    Assumption: identical IV bolus doses at a fixed interval, with first-order
    elimination and steady state reached.
    """
    k_per_h = _positive("k_per_h", k_per_h)
    tau_h = _positive("tau_h", tau_h)
    return 1.0 / -math.expm1(-k_per_h * tau_h)


def css_max_min_iv_bolus(
    dose_mg: float,
    vd_l: float,
    k_per_h: float,
    tau_h: float,
) -> tuple[float, float]:
    """Return steady-state maximum and minimum concentrations for IV boluses.

    Formulas:
        Cmax_ss = (Dose / Vd) * R
        Cmin_ss = Cmax_ss * exp(-k * tau)
        R = 1 / (1 - exp(-k * tau))
    Units: dose_mg in mg, vd_l in litres, k_per_h in 1/hour, tau_h in hours,
    concentrations in mg/L.
    Assumptions: one-compartment model, immediate IV bolus, first-order
    elimination, identical doses at a fixed interval, and steady state.
    """
    dose_mg = _positive("dose_mg", dose_mg)
    vd_l = _positive("vd_l", vd_l)
    k_per_h = _positive("k_per_h", k_per_h)
    tau_h = _positive("tau_h", tau_h)
    c0_mg_per_l = dose_mg / vd_l
    r = 1.0 / -math.expm1(-k_per_h * tau_h)
    cmax_ss = c0_mg_per_l * r
    cmin_ss = cmax_ss * math.exp(-k_per_h * tau_h)
    return cmax_ss, cmin_ss


def time_to_fraction_of_steady_state(t_half_h: float, fraction: float) -> float:
    """Return the time to reach a fraction of steady state.

    Formula: t = -ln(1 - fraction) / k, where k = ln(2) / t_half.
    Units: t_half_h and t in hours, fraction dimensionless.
    Assumptions: first-order approach to steady state, with
    0 < fraction < 1. A fraction of 0.5 corresponds to one half-life.
    """
    t_half_h = _positive("t_half_h", t_half_h)
    fraction = _positive("fraction", fraction)
    if fraction >= 1.0:
        raise ValueError("fraction must be greater than 0 and less than 1")
    k_per_h = _LN2 / t_half_h
    return -math.log1p(-fraction) / k_per_h


def creatinine_clearance_cockcroft_gault(
    age_y: float,
    weight_kg: float,
    scr_mg_per_dl: float,
    female: bool,
) -> float:
    """Return estimated creatinine clearance by the Cockcroft-Gault equation.

    Formula:
        CrCl = ((140 - age) * weight) / (72 * SCr)
    multiplied by 0.85 when ``female`` is True.
    Units: age_y in years, weight_kg in kg, scr_mg_per_dl in mg/dL, CrCl in
    mL/min.
    Assumptions: adult patient (18 years or older; the equation is not valid
    for children), stable renal function, total (actual) body weight unless a
    task states otherwise, serum creatinine in mg/dL, and the original
    Cockcroft-Gault equation. The result is not normalised to body surface
    area.
    """
    age_y = _finite_real("age_y", age_y)
    if not 18.0 <= age_y < 140.0:
        raise ValueError("age_y must be at least 18 and less than 140 years")
    weight_kg = _positive("weight_kg", weight_kg)
    scr_mg_per_dl = _positive("scr_mg_per_dl", scr_mg_per_dl)
    if not isinstance(female, bool):
        raise ValueError("female must be True or False")

    crcl_ml_per_min = ((140.0 - age_y) * weight_kg) / (72.0 * scr_mg_per_dl)
    if female:
        crcl_ml_per_min *= 0.85
    return crcl_ml_per_min
