"""Lateral rocking test: shift the body from one foot to the other at walking pace (open loop).

    .venv/bin/python sim/tools/rocking_test.py [--model f1] [--tilt 12] [--cycles 4] [--arm 60]

With no hip roll, the weight moves sideways by tilting the whole body over the stance foot with
both ankle rolls (feet kept parallel to the floor). One cycle = shift onto the left foot, lift and
lower the right foot, shift back, then the same to the right. To break the left/right symmetry
while shifting, the leg on the far side extends a little (pushes the body over).

--arm opens one arm sideways by that many degrees, following the shift, as a counterweight:
the free-leg side (opposite the stance leg, default) or, with --arm-side stance, the stance side.

No balance feedback: if a pace only works with feedback, it falls here — that tells us what the
IMU controller (F6) will have to do. Reports, per cycle period: how far the body tilts, how high
the free foot lifts, whether it falls, and the peak torque of every joint type.
"""

import argparse
import sys
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from f1_experiments import MODELS, SG90, TYPES, Robot  # noqa: E402

A0 = 0.25          # base crouch (rad) — bent knees give room to extend / lift
PUSH = 0.05        # far leg extends by this much of A while shifting
LIFT = 0.20        # free leg crouches this much more to lift the foot
FALL_TILT_DEG = 40.0


def smooth(x: float) -> float:
    """0 -> 1 with zero velocity at both ends (cosine ramp)."""
    x = min(1.0, max(0.0, x))
    return 0.5 - 0.5 * np.cos(np.pi * x)


def targets(t: float, period: float, roll_max: float):
    """Roll (both ankles) and crouch per side at time t. Six equal phases per cycle."""
    ph = (t % period) / (period / 6)
    k, x = int(ph), smooth(ph - int(ph))
    side = +1 if k < 3 else -1          # +1: stance on the left foot, right foot free
    kk = k % 3
    if kk == 0:                         # shift over the stance foot, far leg pushes
        roll, push, lift = x, x, 0.0
    elif kk == 1:                       # lift and lower the free foot
        roll, push, lift = 1.0, 1.0, np.sin(np.pi * (ph - int(ph)))
    else:                               # shift back to the middle
        roll, push, lift = 1.0 - x, 1.0 - x, 0.0
    free = A0 - PUSH * push + LIFT * lift
    a = {"l": A0, "r": free} if side > 0 else {"l": free, "r": A0}
    return side * roll * roll_max, a


def run(m, period: float, roll_max: float, cycles: int, arm: float = 0.0, arm_side: str = "free"):
    r = Robot(m)
    d = mujoco.MjData(m)
    # settle into the base crouch first
    while d.time < 1.5:
        d.ctrl[:] = r.ctrl({"l": A0 * smooth(d.time / 1.0), "r": A0 * smooth(d.time / 1.0)})
        mujoco.mj_step(m, d)
    t0 = d.time
    peak = np.zeros(m.nu)
    tilt_max, clear_max = 0.0, {"l": 0.0, "r": 0.0}
    sole = {s: m.site(f"sole_{s}").id for s in "lr"}
    while d.time - t0 < cycles * period:
        roll, a = targets(d.time - t0, period, roll_max)
        d.ctrl[:] = r.ctrl(a, roll=roll)
        if arm and roll_max:
            stance = "l" if roll > 0 else "r"                     # roll > 0: stance on the left foot
            side = stance if arm_side == "stance" else {"l": "r", "r": "l"}[stance]
            i = r.idx[f"shoulder_roll_{side}"]
            d.ctrl[i] = np.clip(arm * abs(roll) / roll_max, r.lo[i], r.hi[i])
        mujoco.mj_step(m, d)
        if d.time - t0 > period:                  # skip the first cycle's start-up transient
            peak = np.maximum(peak, np.abs(d.actuator_force))
            tilt_max = max(tilt_max, r.tilt(d))
            for s in "lr":
                clear_max[s] = max(clear_max[s], float(d.site_xpos[sole[s]][2]) * 1000)
        if r.tilt(d) > FALL_TILT_DEG:
            return dict(fell=True, at=d.time - t0)
    by_type = {t: max(peak[r.idx[f"{t}_{s}"]] for s in "lr") for t in TYPES}
    return dict(fell=False, tilt=tilt_max, clear=min(clear_max.values()), peak=by_type)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="f1")
    ap.add_argument("--tilt", type=float, default=12.0, help="ankle roll amplitude, degrees")
    ap.add_argument("--arm", type=float, default=0.0, help="arm opening, degrees")
    ap.add_argument("--arm-side", choices=("free", "stance"), default="free", help="which arm opens")
    ap.add_argument("--cycles", type=int, default=4)
    args = ap.parse_args()
    m = mujoco.MjModel.from_xml_path(str(MODELS.get(args.model, args.model)))
    roll = np.radians(args.tilt)
    print(f"BALANÇO LATERAL (sem controle de equilíbrio): tornozelos roll ±{args.tilt:.0f}°, "
          f"{args.cycles} ciclos, massa {m.body_subtreemass[1] * 1000:.0f} g")
    print("  ciclo   passos/s  inclinação máx  pé livre sobe  caiu?   picos: quadril  joelho  tornozelo  tornoz.roll")
    for period in (6.0, 4.0, 3.0, 2.0, 1.5, 1.0):
        res = run(m, period, roll, args.cycles, np.radians(args.arm), args.arm_side)
        steps = 2 / period
        if res["fell"]:
            print(f"  {period:4.1f} s   {steps:5.2f}        —              —        SIM (t={res['at']:.1f}s)")
            continue
        p = res["peak"]
        print(f"  {period:4.1f} s   {steps:5.2f}      {res['tilt']:5.1f}°        {res['clear']:5.1f} mm     não     "
              + "   ".join(f"{100 * p[t] / SG90:5.0f}%" for t in TYPES))


if __name__ == "__main__":
    main()
