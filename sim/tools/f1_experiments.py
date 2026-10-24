"""F1 experiments on the whole biped (headless, CPU): how hard do the SG90s work?

    .venv/bin/python sim/tools/f1_experiments.py [--model f1]

1. Rise speed: from a crouch (A = 0.6) stand up at several speeds; peak torque per joint type.
2. One-leg stance: with no hip roll joint, the only way to stand on one foot is to tilt the
   whole robot sideways over it (ankle rolls keep the feet flat). Starts the robot already tilted
   over the left foot with the right leg lifted, searches the tilt range where it stays up with
   no feedback, and reports the stance-leg torques.

Crouch rule: hip = A, knee = -2A, ankle pitch = A. SG90 stall torque 0.18 N·m.
"""

import argparse
from pathlib import Path

import mujoco
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MODELS = {"f0": ROOT / "models" / "f0_smoke.xml", "f1": ROOT / "models" / "f1_biped.xml"}
SG90 = 0.18
FALL_TILT_DEG = 30.0
TYPES = ("hip_pitch", "knee", "ankle_pitch", "ankle_roll")
CROUCH = {"hip_pitch": 1.0, "knee": -2.0, "ankle_pitch": 1.0, "ankle_roll": 0.0}


class Robot:
    def __init__(self, m: mujoco.MjModel):
        self.m = m
        self.idx = {m.actuator(i).name: i for i in range(m.nu)}
        self.torso = m.body("torso").id
        self.lo, self.hi = m.actuator_ctrlrange[:, 0], m.actuator_ctrlrange[:, 1]

    def ctrl(self, crouch: dict, roll: float = 0.0, lift_r: float = 0.0) -> np.ndarray:
        """crouch: A per side; roll: both ankle rolls; lift_r: extra crouch on the right leg."""
        u = np.zeros(self.m.nu)
        for side, a in crouch.items():
            a_side = a + (lift_r if side == "r" else 0.0)
            for t in TYPES:
                u[self.idx[f"{t}_{side}"]] = CROUCH[t] * a_side
            u[self.idx[f"ankle_roll_{side}"]] = roll
        return np.clip(u, self.lo, self.hi)

    def tilt(self, d) -> float:
        return float(np.degrees(2 * np.arccos(min(1.0, abs(float(d.xquat[self.torso][0]))))))

    def torques(self, d, side: str) -> dict:
        return {t: abs(float(d.actuator_force[self.idx[f"{t}_{side}"]])) for t in TYPES}


def run(m, schedule, seconds, watch=None):
    """schedule(t) -> ctrl. Returns (data, fallen, peak torque per actuator name during `watch`)."""
    d = mujoco.MjData(m)
    r = Robot(m)
    peak = np.zeros(m.nu)
    while d.time < seconds:
        d.ctrl[:] = schedule(d.time)
        mujoco.mj_step(m, d)
        if watch is None or watch[0] <= d.time <= watch[1]:
            peak = np.maximum(peak, np.abs(d.actuator_force))
        if r.tilt(d) > FALL_TILT_DEG:
            return d, True, peak
    return d, False, peak


def ramp(t, t0, t1, v0, v1):
    if t <= t0:
        return v0
    if t >= t1:
        return v1
    return v0 + (v1 - v0) * (t - t0) / (t1 - t0)


def rise_speed(m):
    r = Robot(m)
    a0 = 0.6
    print("1) LEVANTAR: de A = 0,6 (34°) até em pé, em várias velocidades")
    print("   velocidade A   tempo   pico quadril  pico joelho  pico tornozelo   caiu?")
    for speed in (0.5, 1.0, 2.0, 4.0):
        t_down, hold = a0 / 0.5, 1.5
        t_up0 = t_down + hold
        t_up1 = t_up0 + a0 / speed

        def sched(t):
            a = ramp(t, 0, t_down, 0, a0) if t < t_up0 else ramp(t, t_up0, t_up1, a0, 0)
            return r.ctrl({"l": a, "r": a})

        _, fell, peak = run(m, sched, t_up1 + 1.0, watch=(t_up0, t_up1 + 0.5))
        p = {t: max(peak[r.idx[f"{t}_l"]], peak[r.idx[f"{t}_r"]]) for t in TYPES}
        print(f"   {speed:4.1f} rad/s   {a0 / speed:4.2f} s   "
              + "   ".join(f"{100 * p[t] / SG90:5.0f}%     " for t in ("hip_pitch", "knee", "ankle_pitch"))
              + f"  {'SIM' if fell else 'não'}")


def lean_state(m, r: Robot, phi: float, crouch: float, lift: float):
    """Robot tilted sideways by phi about the left sole, left foot flat on the floor, right leg
    lifted. Ankle rolls = -phi keep both feet parallel to the floor. Returns (data, ctrl)."""
    d = mujoco.MjData(m)
    u = r.ctrl({"l": crouch, "r": crouch}, roll=-phi, lift_r=lift)
    for name, i in r.idx.items():
        d.qpos[m.jnt_qposadr[m.actuator_trnid[i, 0]]] = u[i]
    d.qpos[3:7] = [np.cos(phi / 2), np.sin(phi / 2), 0, 0]      # torso rotated phi about X
    d.qpos[0:3] = [0, 0, 0.3]
    mujoco.mj_kinematics(m, d)
    sole = d.site_xpos[m.site("sole_l").id].copy()
    d.qpos[0:3] -= [sole[0], sole[1], sole[2] - 0.0003]           # left sole on the floor
    mujoco.mj_forward(m, d)
    return d, u


def one_leg(m, crouch=0.2, lift=0.4, hold=3.0):
    r = Robot(m)
    print(f"\n2) UMA PERNA: corpo inclinado de lado sobre o pé esquerdo, pé direito no ar")
    print(f"   (agachamento A = {crouch}, perna direita encolhida +{lift}; segura {hold:.0f} s sem controle)")
    print("   inclinação  fica de pé?  pé dir. no ar   apoio (esq.): quadril  joelho  tornozelo  tornoz.roll")
    stable = []
    for phi_deg in np.arange(-26, 27, 2):
        phi = np.radians(phi_deg)
        d, u = lean_state(m, r, phi, crouch, lift)
        if d.site_xpos[m.site("sole_r").id][2] < 0.002:
            continue                                     # leaning the wrong way: right foot in the floor
        peak = np.zeros(m.nu)
        tilt0 = r.tilt(d)
        ok = True
        while d.time < hold:
            d.ctrl[:] = u
            mujoco.mj_step(m, d)
            if d.time > 0.5:
                peak = np.maximum(peak, np.abs(d.actuator_force))
            if abs(r.tilt(d) - tilt0) > 5 or d.site_xpos[m.site("sole_r").id][2] < 0.001:
                ok = False
                break
        clear = d.site_xpos[m.site("sole_r").id][2] * 1000
        stance = {t: peak[r.idx[f"{t}_l"]] for t in TYPES}
        if ok:
            stable.append((phi_deg, clear, stance))
            print(f"   {phi_deg:+5.0f}°       SIM        {clear:5.1f} mm             "
                  + "   ".join(f"{100 * stance[t] / SG90:4.0f}%" for t in TYPES))
        else:
            print(f"   {phi_deg:+5.0f}°       não (tomba)")
    if stable:
        lo, hi = stable[0][0], stable[-1][0]
        mid = stable[len(stable) // 2]
        worst = {t: max(s[2][t] for s in stable) for t in TYPES}
        print(f"\n   Fica de pé numa perna com inclinação entre {lo:+.0f}° e {hi:+.0f}° "
              f"(faixa de {abs(hi - lo):.0f}°). No meio ({mid[0]:+.0f}°) o pé direito fica {mid[1]:.0f} mm no ar.")
        print("   Pior caso na perna de apoio: " + ", ".join(
            f"{t} {100 * worst[t] / SG90:.0f}%" for t in TYPES))
    else:
        print("\n   Nenhuma inclinação equilibrou o robô numa perna só.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="f1")
    args = ap.parse_args()
    m = mujoco.MjModel.from_xml_path(str(MODELS.get(args.model, args.model)))
    print(f"modelo: {args.model}  massa total {m.body_subtreemass[1] * 1000:.0f} g\n")
    rise_speed(m)
    one_leg(m)


if __name__ == "__main__":
    main()
