#!/usr/bin/env python3
"""
QAG Virology Capsid Clearance Calculator
Hybrid Bio-Acoustic Carbon Capture & O2 Synthesis — Pillar 2

Computes, for a candidate viral delivery vector:
  Z_v      = (MW_kDa * density_proxy) / K_ASB          (affinitic impedance)
  f_kill   = (f_H / Phi) * log10(Z_v + 1)             (disruptive resonant freq, MHz)
  zeta_est = -15.0 - 10.0 * sin(f_kill*1e6 * t_pixel) (estimated zeta potential, mV)
  Δζ       = |zeta_host - zeta_est|  (host safety margin; SECURE iff >= 20.0 mV)

Canonical constants (Hybrid Bio-Acoustic Blueprint V4):
  f_H = 1420.405 MHz   (neutral hydrogen hyperfine line)
  K_ASB = 0.013829      (affinity symmetry bias)
  Phi = 1.194797        (base-12 symmetry scaling factor)
  t_pixel = 3.41e-7 s   (temporal latency window)
  zeta_host = -55.0 mV  (extremophile host baseline)

Badge: 🟣 THEORETICAL QAG MODEL (equations) · dataset values per Blueprint V4.
License: Apache 2.0 — R&R Droids, 2026.
"""

import math

# ---- QAG canonical constants ----
F_H = 1420.405        # MHz
K_ASB = 0.013829
PHI = 1.194797
T_PIXEL = 3.41e-7     # s
ZETA_HOST = -55.0     # mV
SAFETY_THRESHOLD_MV = 20.0


def run_qag_virology_simulation(mw_kda, density_proxy, host_zeta=ZETA_HOST):
    """Return (Z_v, f_kill_MHz, zeta_est_mV, delta_zeta_mV, is_safe)."""
    z_v = (mw_kda * density_proxy) / K_ASB
    f_kill = (F_H / PHI) * math.log10(z_v + 1)
    zeta_est = -15.0 - (10.0 * math.sin(f_kill * 1e6 * T_PIXEL))
    delta_zeta = abs(host_zeta - zeta_est)
    return z_v, f_kill, zeta_est, delta_zeta, delta_zeta >= SAFETY_THRESHOLD_MV


# ---- Blueprint V4 screening dataset ----
# (name, PDB proxy, MW_kDa, Z_v as published). Density proxies are derived at full
# float precision (rho = Z_v * K_ASB / MW) so f_kill reproduces the table.
# NOTE on zeta: zeta_est = -15 - 10*sin(f_kill*1e6*t_pixel) with f_kill*1e6*t_pixel
# ~ 2,480 rad — the sine is exquisitely sensitive to sub-0.01% changes in f_kill, so
# printed zeta_v may differ from the table's last digit. The safety verdict is robust:
# every Δζ sits 30–50 mV, far above the 20.0 mV lock threshold.
VECTORS = [
    ("PBCV-1 Virion Assembly",      "1M4X",   15400.0, 1.314e6),
    ("PBCV-1 Capsid Vp54",          "1J5Q",     324.0,  2.694e4),
    ("Chlorella Virus AR158",       "3J42",   14800.0,  1.241e6),
    ("Chlorella Virus NY-2A",       "3J41",   15100.0,  1.278e6),
    ("ATCV-1 Broad-Host Capsid",    "3J24",   13900.0,  1.146e6),
    ("Recombinant CA II Cassette",  "2VVA",      58.4,  4.434e3),
    ("Thermostable CA II (DvCA10)", "1V9E",      64.2,  4.921e3),
    ("RuBisCO Activase Complex",    "3ZXG",     440.0,  3.500e4),
    ("BiFeO3 Doped Nanogel",        "SYN_NP",  2800.0,  2.733e5),
    ("Extremophile Host Baseline",  "HOST",   85000.0,  6.269e6),
]


def main():
    print(f"{'Vector':32s} {'Z_v':>12s} {'f_kill (MHz)':>13s} {'zeta_v':>8s} {'Δζ':>7s}  status")
    print("-" * 92)
    all_secure = True
    for name, pdb, mw, z_v in VECTORS:
        rho = z_v * K_ASB / mw  # full precision — reproduces published Z_v
        z2, f_kill, zeta_est, dz, safe = run_qag_virology_simulation(mw, rho)
        all_secure &= safe
        print(f"{name:32s} {z2:12.3e} {f_kill:13.2f} {zeta_est:8.2f} {dz:7.2f}  "
              f"{'SECURE' if safe else 'REVIEW'}")
    print("-" * 92)
    print(f"Host safety margin lock (Δζ ≥ {SAFETY_THRESHOLD_MV} mV): "
          f"{'ALL 10 VECTORS SECURE' if all_secure else 'REVIEW REQUIRED'}")


if __name__ == "__main__":
    main()
