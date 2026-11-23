"""Tests for the one-compartment pharmacokinetic functions.

Every expected value is derived by hand in the comment above its assertion.
"""

import math

import pytest

from pharmacalc import pk


def test_elimination_rate_constant() -> None:
    # t_half = 6 h.
    # k = ln(2) / 6 = 0.6931471805599453 / 6 = 0.11552453009332421 h^-1.
    assert pk.elimination_rate_constant(6.0) == pytest.approx(
        0.11552453009332421, rel=1e-12
    )


def test_half_life() -> None:
    # k = 0.1 h^-1.
    # t_half = ln(2) / 0.1 = 6.931471805599453 h.
    assert pk.half_life(0.1) == pytest.approx(6.931471805599453, rel=1e-12)


@pytest.mark.parametrize("t_half_h", [0.5, 2.0, 6.0, 24.0, 100.0])
def test_half_life_round_trip(t_half_h: float) -> None:
    # k = ln(2) / t_half, then t_half = ln(2) / k, so the original value returns.
    k_per_h = pk.elimination_rate_constant(t_half_h)
    assert pk.half_life(k_per_h) == pytest.approx(t_half_h, rel=1e-12)


@pytest.mark.parametrize("k_per_h", [0.01, 0.1, 0.693, 2.0])
def test_rate_constant_round_trip(k_per_h: float) -> None:
    # t_half = ln(2) / k, then k = ln(2) / t_half, so the original value returns.
    t_half_h = pk.half_life(k_per_h)
    assert pk.elimination_rate_constant(t_half_h) == pytest.approx(
        k_per_h, rel=1e-12
    )


def test_clearance() -> None:
    # k = 0.1 h^-1 and Vd = 50 L.
    # CL = k * Vd = 0.1 * 50 = 5 L/h.
    assert pk.clearance(k_per_h=0.1, vd_l=50.0) == pytest.approx(5.0, rel=1e-12)


def test_initial_concentration_iv_bolus() -> None:
    # Dose = 500 mg and Vd = 50 L.
    # C0 = Dose / Vd = 500 / 50 = 10 mg/L.
    assert pk.initial_concentration_iv_bolus(
        dose_mg=500.0, vd_l=50.0
    ) == pytest.approx(10.0, rel=1e-12)


def test_concentration_iv_bolus_at_six_hours() -> None:
    # Dose = 500 mg, Vd = 50 L, k = 0.1 h^-1, t = 6 h.
    # C0 = 500 / 50 = 10 mg/L.
    # C(6) = 10 * exp(-0.1 * 6) = 10 * exp(-0.6) = 5.488116360940265 mg/L.
    assert pk.concentration_iv_bolus(
        dose_mg=500.0, vd_l=50.0, k_per_h=0.1, t_h=6.0
    ) == pytest.approx(5.488116360940265, rel=1e-12)


def test_concentration_iv_bolus_at_time_zero() -> None:
    # At t = 0, exp(0) = 1, so C(0) must equal the initial concentration.
    c0_mg_per_l = pk.initial_concentration_iv_bolus(dose_mg=500.0, vd_l=50.0)
    assert pk.concentration_iv_bolus(
        dose_mg=500.0, vd_l=50.0, k_per_h=0.1, t_h=0.0
    ) == pytest.approx(c0_mg_per_l, rel=1e-12)


def test_concentration_iv_bolus_at_one_half_life() -> None:
    # t_half = 6 h, so k = ln(2) / 6 h^-1.
    # After one half-life, C = C0 / 2 = 10 / 2 = 5 mg/L.
    k_per_h = math.log(2.0) / 6.0
    assert pk.concentration_iv_bolus(
        dose_mg=500.0, vd_l=50.0, k_per_h=k_per_h, t_h=6.0
    ) == pytest.approx(5.0, rel=1e-12)


def test_time_to_concentration() -> None:
    # C0 = 10 mg/L, C_target = 5 mg/L, k = ln(2) / 6 h^-1.
    # t = ln(10 / 5) / k = ln(2) / (ln(2) / 6) = 6 h (one half-life).
    assert pk.time_to_concentration(
        c0=10.0, c_target=5.0, k_per_h=math.log(2.0) / 6.0
    ) == pytest.approx(6.0, rel=1e-12)


def test_time_to_concentration_second_case() -> None:
    # C0 = 10 mg/L, C_target = 2.5 mg/L, k = 0.1 h^-1.
    # t = ln(10 / 2.5) / 0.1 = ln(4) / 0.1 = 13.862943611198904 h.
    assert pk.time_to_concentration(
        c0=10.0, c_target=2.5, k_per_h=0.1
    ) == pytest.approx(13.862943611198904, rel=1e-12)


def test_concentration_and_time_are_inverse() -> None:
    # C0 = 8 mg/L, k = 0.2 h^-1, t = 5 h.
    # C(5) = 8 * exp(-0.2 * 5) = 8 * exp(-1) = 2.9430355293715387 mg/L.
    # Recovering t from that concentration must return 5 h.
    c0 = 8.0
    k_per_h = 0.2
    t_h = 5.0
    c_after_5_h = pk.concentration_iv_bolus(
        dose_mg=c0 * 50.0, vd_l=50.0, k_per_h=k_per_h, t_h=t_h
    )
    assert c_after_5_h == pytest.approx(2.9430355293715387, rel=1e-12)
    assert pk.time_to_concentration(
        c0=c0, c_target=c_after_5_h, k_per_h=k_per_h
    ) == pytest.approx(t_h, rel=1e-12)


def test_loading_dose_with_bioavailability() -> None:
    # C_target = 10 mg/L, Vd = 50 L, F = 0.8.
    # LD = (10 * 50) / 0.8 = 500 / 0.8 = 625 mg.
    assert pk.loading_dose(
        c_target_mg_per_l=10.0, vd_l=50.0, f=0.8
    ) == pytest.approx(625.0, rel=1e-12)


def test_loading_dose_iv_default() -> None:
    # F defaults to 1.0 for IV dosing.
    # LD = (10 * 50) / 1.0 = 500 mg.
    assert pk.loading_dose(
        c_target_mg_per_l=10.0, vd_l=50.0
    ) == pytest.approx(500.0, rel=1e-12)


def test_maintenance_dose_with_bioavailability() -> None:
    # Css_avg = 10 mg/L, CL = 5 L/h, tau = 12 h, F = 0.8.
    # MD = (10 * 5 * 12) / 0.8 = 600 / 0.8 = 750 mg per interval.
    assert pk.maintenance_dose(
        css_avg_mg_per_l=10.0,
        cl_l_per_h=5.0,
        tau_h=12.0,
        f=0.8,
    ) == pytest.approx(750.0, rel=1e-12)


def test_maintenance_dose_iv_default() -> None:
    # F defaults to 1.0.
    # MD = (10 * 5 * 12) / 1.0 = 600 mg per interval.
    assert pk.maintenance_dose(
        css_avg_mg_per_l=10.0, cl_l_per_h=5.0, tau_h=12.0
    ) == pytest.approx(600.0, rel=1e-12)


def test_accumulation_factor_at_one_half_life() -> None:
    # k = ln(2) / 6 h^-1 and tau = 6 h.
    # exp(-k * tau) = exp(-ln(2)) = 0.5.
    # R = 1 / (1 - 0.5) = 2.
    assert pk.accumulation_factor(
        k_per_h=math.log(2.0) / 6.0, tau_h=6.0
    ) == pytest.approx(2.0, rel=1e-12)


def test_accumulation_factor_second_case() -> None:
    # k = 0.1 h^-1 and tau = 12 h.
    # exp(-1.2) = 0.30119421191220214.
    # R = 1 / (1 - 0.30119421191220214) = 1.4310127606933334.
    assert pk.accumulation_factor(
        k_per_h=0.1, tau_h=12.0
    ) == pytest.approx(1.4310127606933334, rel=1e-12)


def test_css_max_min_iv_bolus_at_one_half_life() -> None:
    # Dose = 500 mg, Vd = 50 L, k = ln(2) / 6 h^-1, tau = 6 h.
    # Cmax_single = 500 / 50 = 10 mg/L.
    # R = 1 / (1 - exp(-ln(2))) = 2.
    # Cmax_ss = 10 * 2 = 20 mg/L.
    # Cmin_ss = 20 * exp(-ln(2)) = 20 * 0.5 = 10 mg/L.
    cmax_ss, cmin_ss = pk.css_max_min_iv_bolus(
        dose_mg=500.0,
        vd_l=50.0,
        k_per_h=math.log(2.0) / 6.0,
        tau_h=6.0,
    )
    assert cmax_ss == pytest.approx(20.0, rel=1e-12)
    assert cmin_ss == pytest.approx(10.0, rel=1e-12)


def test_css_max_min_iv_bolus_second_case() -> None:
    # Dose = 500 mg, Vd = 50 L, k = 0.1 h^-1, tau = 12 h.
    # Cmax_single = 10 mg/L.
    # exp(-1.2) = 0.30119421191220214.
    # R = 1.4310127606933334.
    # Cmax_ss = 10 * 1.4310127606933334 = 14.310127606933333 mg/L.
    # Cmin_ss = 14.310127606933333 * 0.30119421191220214
    #         = 4.3101276069333325 mg/L.
    cmax_ss, cmin_ss = pk.css_max_min_iv_bolus(
        dose_mg=500.0,
        vd_l=50.0,
        k_per_h=0.1,
        tau_h=12.0,
    )
    assert cmax_ss == pytest.approx(14.310127606933333, rel=1e-12)
    assert cmin_ss == pytest.approx(4.3101276069333325, rel=1e-12)


@pytest.mark.parametrize(
    ("fraction", "expected_h"),
    [
        (0.5, 6.0),
        (0.75, 12.0),
        (0.9375, 24.0),
    ],
)
def test_time_to_fraction_of_steady_state(
    fraction: float, expected_h: float
) -> None:
    # t_half = 6 h, so k = ln(2) / 6 h^-1.
    # fraction 0.5:   -ln(0.5)   = ln(2),   t = ln(2) / k = 6 h.
    # fraction 0.75:  -ln(0.25)  = ln(4),   t = 2 * ln(2) / k = 12 h.
    # fraction 0.9375: 1 - 0.9375 = 1/16,  -ln(1/16) = ln(16) = 4 * ln(2),
    #                  t = 4 * ln(2) / k = 24 h.
    assert pk.time_to_fraction_of_steady_state(
        t_half_h=6.0, fraction=fraction
    ) == pytest.approx(expected_h, rel=1e-12)


def test_creatinine_clearance_cockcroft_gault_male_and_female() -> None:
    # age = 70 years, weight = 80 kg, SCr = 1.0 mg/dL.
    # Male:   ((140 - 70) * 80) / (72 * 1.0) = 5600 / 72
    #         = 77.77777777777777 mL/min.
    # Female: 77.77777777777777 * 0.85 = 66.1111111111111 mL/min.
    male_crcl = pk.creatinine_clearance_cockcroft_gault(
        age_y=70.0, weight_kg=80.0, scr_mg_per_dl=1.0, female=False
    )
    female_crcl = pk.creatinine_clearance_cockcroft_gault(
        age_y=70.0, weight_kg=80.0, scr_mg_per_dl=1.0, female=True
    )
    assert male_crcl == pytest.approx(77.77777777777777, rel=1e-12)
    assert female_crcl == pytest.approx(66.1111111111111, rel=1e-12)


def test_creatinine_clearance_cockcroft_gault_second_case() -> None:
    # age = 40 years, weight = 70 kg, SCr = 0.8 mg/dL, male.
    # CrCl = ((140 - 40) * 70) / (72 * 0.8) = 7000 / 57.6
    #      = 121.52777777777777 mL/min.
    assert pk.creatinine_clearance_cockcroft_gault(
        age_y=40.0, weight_kg=70.0, scr_mg_per_dl=0.8, female=False
    ) == pytest.approx(121.52777777777777, rel=1e-12)


@pytest.mark.parametrize(
    ("func", "args"),
    [
        (pk.elimination_rate_constant, (0.0,)),
        (pk.elimination_rate_constant, (-6.0,)),
        (pk.elimination_rate_constant, (None,)),
        (pk.elimination_rate_constant, (float("nan"),)),
        (pk.half_life, (0.0,)),
        (pk.half_life, (float("inf"),)),
        (pk.clearance, (0.0, 50.0)),
        (pk.clearance, (0.1, 0.0)),
        (pk.initial_concentration_iv_bolus, (True, 50.0)),
        (pk.initial_concentration_iv_bolus, (500.0, -50.0)),
        (pk.concentration_iv_bolus, (500.0, 50.0, 0.1, -1.0)),
        (pk.concentration_iv_bolus, (500.0, 50.0, float("nan"), 1.0)),
        (pk.time_to_concentration, (10.0, 10.0, 0.1)),
        (pk.time_to_concentration, (10.0, 20.0, 0.1)),
        (pk.time_to_concentration, (0.0, 5.0, 0.1)),
        (pk.loading_dose, (10.0, 50.0, 0.0)),
        (pk.loading_dose, (10.0, 50.0, 1.1)),
        (pk.maintenance_dose, (10.0, 5.0, 12.0, 0.0)),
        (pk.maintenance_dose, (10.0, 5.0, 12.0, 1.1)),
        (pk.maintenance_dose, (10.0, 5.0, 0.0, 1.0)),
        (pk.accumulation_factor, (0.0, 6.0)),
        (pk.accumulation_factor, (0.1, 0.0)),
        (pk.css_max_min_iv_bolus, (0.0, 50.0, 0.1, 12.0)),
        (pk.css_max_min_iv_bolus, (500.0, 50.0, 0.1, 0.0)),
        (pk.time_to_fraction_of_steady_state, (6.0, 0.0)),
        (pk.time_to_fraction_of_steady_state, (6.0, 1.0)),
        (pk.time_to_fraction_of_steady_state, (6.0, 1.5)),
        (pk.time_to_fraction_of_steady_state, (0.0, 0.5)),
        (pk.creatinine_clearance_cockcroft_gault, (17.0, 80.0, 1.0, False)),
        (pk.creatinine_clearance_cockcroft_gault, (140.0, 80.0, 1.0, False)),
        (pk.creatinine_clearance_cockcroft_gault, (70.0, 0.0, 1.0, False)),
        (pk.creatinine_clearance_cockcroft_gault, (70.0, 80.0, 0.0, False)),
        (pk.creatinine_clearance_cockcroft_gault, (70.0, 80.0, 1.0, "yes")),
    ],
)
def test_invalid_inputs_raise_value_error(func, args) -> None:
    with pytest.raises(ValueError):
        func(*args)
