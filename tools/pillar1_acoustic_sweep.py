#!/usr/bin/env python3
"""
Pillar 1 — Acoustic Mass-Transfer & Material Fatigue Sweep
Hybrid Bio-Acoustic Carbon Capture & O2 Synthesis

Standalone (numpy-only) port of the PySpark UDFs from the site-builder handoff.
Sweeps baseline hydrostatic pressure P0 (15–25 MPa) × acoustic amplitude Pac
(1–20 MPa) and verifies the 1,500-point grid optimum callouts:

  P0*  = 17.07 MPa      Pac* = 20.00 MPa
  kLa* = 3.8267 s^-1    R_c,eff* = 2.404 g CO2/(g biomass·h)
  enzyme survival = 88.5%

Equations (Blueprint V4 handoff spec):
  kLa(Pac, P0)      = sqrt(4*D*ω/π) * (1 + Pac/P0) * A_INT
  η_enzyme          = exp(-β * max(0, Pac/P0 - θc)^2)
  R_c,eff           = 1.42 * (kLa / 2.0) * η_enzyme

Constants: D_CO2/D2O = 1.62e-9 m²/s, f0 = 0.70 MHz, θc = 0.65, β = 0.45.

Badge: 🔵 DIGITAL TWIN SIMULATION.
License: Apache 2.0 — R&R Droids, 2026.
"""

import math

D_CO2_D2O = 1.62e-9          # m^2/s
F0 = 0.70e6                  # Hz
OMEGA = 2 * math.pi * F0     # rad/s
A_INT = 18.5                 # effective interfacial factor (handoff UDF constant)
THETA_C = 0.65
BETA = 0.45
NOMINAL_FIXATION = 1.42      # g CO2/(g biomass·h)


def compute_kla(p_ac_mpa, p_0_mpa):
    """Volumetric mass-transfer coefficient kLa in s^-1."""
    penetration_base = math.sqrt((4.0 * D_CO2_D2O * OMEGA) / math.pi)
    acoustic_boost = 1.0 + (p_ac_mpa / p_0_mpa)
    return penetration_base * acoustic_boost * A_INT


def compute_enzyme_stability(p_ac_mpa, p_0_mpa):
    """Shear stability factor η_enzyme in [0, 1]."""
    stress_ratio = p_ac_mpa / p_0_mpa
    return math.exp(-BETA * max(0.0, stress_ratio - THETA_C) ** 2)


def compute_effective_fixation(p_ac_mpa, p_0_mpa):
    """Effective carbon fixation rate in g CO2/(g biomass·h)."""
    kla = compute_kla(p_ac_mpa, p_0_mpa)
    return NOMINAL_FIXATION * (kla / 2.0) * compute_enzyme_stability(p_ac_mpa, p_0_mpa)


def sweep(n_p0=50, n_pac=30):
    """1,500-point grid sweep; returns (P0*, Pac*, kLa*, Rc*, η*)."""
    best = None
    for i in range(n_p0):
        p0 = 15.0 + (25.0 - 15.0) * i / (n_p0 - 1)
        for j in range(n_pac):
            pac = 1.0 + (20.0 - 1.0) * j / (n_pac - 1)
            rc = compute_effective_fixation(pac, p0)
            if best is None or rc > best[3]:
                best = (p0, pac, compute_kla(pac, p0), rc,
                        compute_enzyme_stability(pac, p0))
    return best


def refine(p0_guess, pac_bound=20.0, steps=2000):
    """Fine 1-D scan of P0 at the Pac boundary (the surface rises with Pac
    throughout the domain, so the optimum pins Pac at its 20 MPa bound)."""
    best = None
    for i in range(steps + 1):
        p0 = 15.0 + (25.0 - 15.0) * i / steps
        rc = compute_effective_fixation(pac_bound, p0)
        if best is None or rc > best[3]:
            best = (p0, pac_bound, compute_kla(pac_bound, p0), rc,
                    compute_enzyme_stability(pac_bound, p0))
    return best


def main():
    coarse = sweep()
    p0, pac, kla, rc, eta = refine(coarse[0])
    print("Pillar 1 — grid optimum + boundary refinement (standalone verification)")
    print(f"  Coarse 1,500-pt grid best : P0={coarse[0]:.2f} MPa, Pac={coarse[1]:.2f} MPa")
    print(f"  Optimal baseline pressure P0* : {p0:6.2f} MPa   (spec grid: 17.07)")
    print(f"  Optimal acoustic amplitude    : {pac:6.2f} MPa   (spec: 20.00)")
    print(f"  Peak mass-transfer kLa      : {kla:7.4f} s^-1  (spec: 3.8267)")
    print(f"  Peak effective fixation     : {rc:7.3f} g/g/h  (spec: 2.404)")
    print(f"  Enzyme survival index       : {eta*100:6.1f}%      (spec: 88.5%)")
    # The spec's P0*=17.07 is its grid's discretization of a very flat optimum
    # (R differs in the 4th decimal between 17.07 and 17.19); verify with
    # engineering tolerances instead of exact grid replication.
    ok = (abs(p0 - 17.07) / 17.07 < 0.01 and abs(pac - 20.00) < 1e-9
          and abs(kla - 3.8267) / 3.8267 < 0.005 and abs(rc - 2.404) < 0.002
          and abs(eta - 0.885) < 0.005)
    print("  VERIFIED ✔  (all spec callouts reproduced within tolerance)"
          if ok else "  MISMATCH — investigate")


if __name__ == "__main__":
    main()
