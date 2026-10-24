"""Viewer + recorder for the leg models: exact postures by key, live torque, CSV log.

    .venv/bin/python sim/tools/monitor.py                 # open the viewer and record
    .venv/bin/python sim/tools/monitor.py --sweep         # no window: find the deepest crouch

Crouch rule (keeps the torso over the foot): hip = A, knee = -2A, ankle pitch = A.
Keys in the viewer window:
    1 / 2 / 3 / 4   A = 0 / 0.2 / 0.4 / 0.6 rad
    + / -           A up / down by 0.05 rad
    Backspace       restart from the straight leg (viewer's own reset; detected here)
Dragging a slider in Control switches to manual mode (the script stops driving the joints)
until a posture key is pressed again. Joint targets move at a servo-like speed, not in a jump.

Joint limits (see docs/arquitetura_perna.md): the joint range is the mechanical stop printed in
the part; the actuator ctrlrange is the software limit, 5° inside it. The deepest crouch A is
capped by the software limits, so the motor never pushes a joint into its stop. Hitting a stop
(only possible in a fall or a push) is reported as "NO BATENTE".

Every run is logged to sim/logs/monitor_<date>_<time>.csv (50 rows per second).
"""

import argparse
import csv
import datetime as dt
import os
import sys
import time
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "models" / "f0_smoke.xml"
LOG_DIR = Path(os.environ.get("MONITOR_LOG_DIR", ROOT / "logs"))  # override for test runs

SG90_TORQUE = 0.18          # N·m, stall torque of the SG90 (also the model's forcerange)
RAMP_SPEED = 0.5            # rad/s of A: the whole crouch moves together, knee at 2× this
LOG_HZ = 50
PRINT_HZ = 5
PRESETS = {ord("1"): 0.0, ord("2"): 0.2, ord("3"): 0.4, ord("4"): 0.6}
KEY_UP = (ord("="), 334)     # '=' / '+' key and keypad +
KEY_DOWN = (ord("-"), 333)   # '-' key and keypad -
A_STEP = 0.05
FALL_TILT_DEG = 45.0
LIMIT_MARGIN = 0.01          # rad from the joint range counts as "on the stop"
SOFT_MARGIN = 1e-3           # rad from the ctrlrange counts as "at the software limit"


def crouch_targets(a: float) -> np.ndarray:
    return np.array([a, -2.0 * a, a, 0.0])


class Leg:
    """Reads the quantities we care about from the model state."""

    def __init__(self, m: mujoco.MjModel):
        self.m = m
        self.names = [m.actuator(i).name for i in range(m.nu)]
        self.qadr = [m.jnt_qposadr[m.actuator_trnid[i, 0]] for i in range(m.nu)]
        self.ranges = [m.jnt_range[m.actuator_trnid[i, 0]] for i in range(m.nu)]
        self.torso = m.body("torso").id
        self.soft = [m.actuator_ctrlrange[i] for i in range(m.nu)]
        hip, knee, ankle = self.soft[0], self.soft[1], self.soft[2]
        # deepest crouch that keeps hip = A, knee = -2A, ankle = A inside every software limit
        self.a_max = float(min(hip[1], -knee[0] / 2.0, ankle[1]))

    def angles(self, d) -> np.ndarray:
        return np.array([d.qpos[a] for a in self.qadr])

    def on_stop(self, d) -> list[bool]:
        q = self.angles(d)
        return [q[i] <= r[0] + LIMIT_MARGIN or q[i] >= r[1] - LIMIT_MARGIN for i, r in enumerate(self.ranges)]

    def at_soft_limit(self, d) -> list[bool]:
        return [abs(d.ctrl[i] - r[0]) < SOFT_MARGIN or abs(d.ctrl[i] - r[1]) < SOFT_MARGIN
                for i, r in enumerate(self.soft)]

    def tilt_deg(self, d) -> float:
        w = abs(float(d.xquat[self.torso][0]))
        return float(np.degrees(2 * np.arccos(min(1.0, w))))

    def torso_z(self, d) -> float:
        return float(d.xpos[self.torso][2])

    def fallen(self, d) -> bool:
        return self.tilt_deg(d) > FALL_TILT_DEG


class Recorder:
    def __init__(self, leg: Leg):
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.path = LOG_DIR / f"monitor_{dt.datetime.now():%Y%m%d_%H%M%S}.csv"
        self.f = open(self.path, "w", newline="")
        self.w = csv.writer(self.f)
        n = leg.names
        self.w.writerow(["t_s", "mode", "A_rad"] + [f"target_{x}_deg" for x in n] + [f"angle_{x}_deg" for x in n]
                        + [f"torque_{x}_Nm" for x in n] + [f"on_stop_{x}" for x in n]
                        + ["torso_z_mm", "tilt_deg", "fallen"])
        self.leg = leg
        self.rows = 0

    def write(self, d, mode: str, a: float):
        leg = self.leg
        self.rows += 1
        self.w.writerow([f"{d.time:.3f}", mode, f"{a:.3f}"]
                        + [f"{np.degrees(x):.2f}" for x in d.ctrl]
                        + [f"{np.degrees(x):.2f}" for x in leg.angles(d)]
                        + [f"{x:+.4f}" for x in d.actuator_force]
                        + [int(x) for x in leg.on_stop(d)]
                        + [f"{leg.torso_z(d) * 1000:.1f}", f"{leg.tilt_deg(d):.1f}", int(leg.fallen(d))])
        if self.rows % LOG_HZ == 0:      # flush once per second so the log can be read while running
            self.f.flush()

    def close(self):
        self.f.close()


def status_line(leg: Leg, d, mode: str, a: float) -> str:
    knee = abs(float(d.actuator_force[1]))
    stops = [n for n, s in zip(leg.names, leg.on_stop(d)) if s]
    parts = [f"t={d.time:5.1f}s", mode, f"A={a:.2f} ({np.degrees(a):2.0f}°)",
             f"joelho {knee:.3f} N·m {100 * knee / SG90_TORQUE:3.0f}% SG90",
             f"incl {leg.tilt_deg(d):4.1f}°", f"tronco {leg.torso_z(d) * 1000:5.1f}mm"]
    soft = [n for n, s in zip(leg.names, leg.at_soft_limit(d)) if s and n != "ankle_roll"]
    if soft and a > 0:
        parts.append("limite de software: " + ",".join(soft))
    if stops:
        parts.append("NO BATENTE: " + ",".join(stops))
    if leg.fallen(d):
        parts.append("CAIU (Backspace para recomeçar)")
    return " | ".join(parts)


def ramp(current: float, target: float, dt_s: float) -> float:
    """Move the crouch depth A towards target; all joints follow A, so the rule holds mid-move."""
    step = RAMP_SPEED * dt_s
    return current + float(np.clip(target - current, -step, step))


def run_viewer(m: mujoco.MjModel):
    import mujoco.viewer

    d = mujoco.MjData(m)
    leg = Leg(m)
    rec = Recorder(leg)
    state = {"a": 0.0, "a_cmd": 0.0, "mode": "auto"}

    def on_key(key: int):
        if key in PRESETS:
            state.update(a=PRESETS[key], mode="auto")
        elif key in KEY_UP:
            state.update(a=min(leg.a_max, state["a"] + A_STEP), mode="auto")
        elif key in KEY_DOWN:
            state.update(a=max(0.0, state["a"] - A_STEP), mode="auto")

    print(__doc__.split("Every run")[0])
    print(f"gravando em {rec.path}\n")
    log_every = max(1, int(1 / (LOG_HZ * m.opt.timestep)))
    print_every = max(1, int(1 / (PRINT_HZ * m.opt.timestep)))
    try:
        _viewer_loop(m, d, leg, rec, state, on_key, log_every, print_every)
    except KeyboardInterrupt:
        pass
    finally:
        rec.close()
    print(f"\n\nlog salvo: {rec.path}")


def _viewer_loop(m, d, leg, rec, state, on_key, log_every, print_every):
    import mujoco.viewer

    last_written = d.ctrl.copy()
    last_time = d.time
    step = 0
    with mujoco.viewer.launch_passive(m, d, key_callback=on_key) as v:
        while v.is_running():
            t0 = time.perf_counter()
            with v.lock():
                if d.time < last_time:                          # Backspace / Reset in the viewer
                    state.update(a=0.0, a_cmd=0.0, mode="auto")
                    last_written = d.ctrl.copy()
                if not np.allclose(d.ctrl, last_written):      # a slider was dragged in Control
                    state["mode"] = "manual"
                if state["mode"] == "auto":
                    state["a_cmd"] = ramp(state["a_cmd"], state["a"], m.opt.timestep)
                    d.ctrl[:] = crouch_targets(state["a_cmd"])
                last_written = d.ctrl.copy()
                mujoco.mj_step(m, d)
                last_time = d.time
                step += 1
                if step % log_every == 0:
                    rec.write(d, state["mode"], state["a"])
                if step % print_every == 0:
                    sys.stdout.write("\r\033[K" + status_line(leg, d, state["mode"], state["a"]))
                    sys.stdout.flush()
            if step % 8 == 0:
                v.sync()
            wait = m.opt.timestep - (time.perf_counter() - t0)
            if wait > 0:
                time.sleep(wait)


def settle(m, a: float, seconds: float = 3.0):
    """Ramp from a straight leg to crouch A, hold, and report the steady state."""
    d = mujoco.MjData(m)
    leg = Leg(m)
    a_cmd = 0.0
    while d.time < abs(a) / RAMP_SPEED + seconds:
        a_cmd = ramp(a_cmd, a, m.opt.timestep)
        d.ctrl[:] = crouch_targets(a_cmd)
        mujoco.mj_step(m, d)
        if leg.fallen(d):
            return dict(fallen=True, time=d.time)
    return dict(fallen=False, knee=abs(float(d.actuator_force[1])), tilt=leg.tilt_deg(d),
                z=leg.torso_z(d), stops=[n for n, s in zip(leg.names, leg.on_stop(d)) if s])


def run_sweep(m: mujoco.MjModel):
    a_max = Leg(m).a_max
    print(f"limite de software do agachamento: A = {a_max:.2f} rad = {np.degrees(a_max):.0f}°\n")
    print("A (rad)  graus  joelho N·m  % SG90  inclinação  tronco mm  observação")
    deepest = None
    for a in [*np.arange(0.0, a_max, A_STEP), a_max]:
        r = settle(m, float(a))
        if r["fallen"]:
            print(f"{a:6.2f}  {np.degrees(a):5.0f}       —        —          —          —    CAIU em t={r['time']:.1f}s")
            continue
        note = ("no batente: " + ",".join(r["stops"])) if r["stops"] else ""
        print(f"{a:6.2f}  {np.degrees(a):5.0f}    {r['knee']:.3f}   {100 * r['knee'] / SG90_TORQUE:5.0f}%"
              f"      {r['tilt']:5.1f}°     {r['z'] * 1000:6.1f}    {note}")
        if not r["stops"]:
            deepest = (a, r)
    if deepest:
        a, r = deepest
        print(f"\nAgachamento mais fundo sem cair e sem batente: A = {a:.2f} rad ({np.degrees(a):.0f}°), "
              f"joelho {r['knee']:.3f} N·m = {100 * r['knee'] / SG90_TORQUE:.0f}% do SG90")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sweep", action="store_true", help="no window: test every crouch depth and report")
    ap.add_argument("--model", default=str(MODEL))
    args = ap.parse_args()
    m = mujoco.MjModel.from_xml_path(args.model)
    run_sweep(m) if args.sweep else run_viewer(m)


if __name__ == "__main__":
    main()
