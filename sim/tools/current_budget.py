"""Servo-rail current budget: how many amps do the 16 SG90s draw, per scenario?

    .venv/bin/python sim/tools/current_budget.py [--model f1] [--tilt 12]

Servo current model (one number per servo, conservative): a DC motor's current follows its torque,
so I = I_idle + (I_stall - I_idle) * |torque| / stall torque. That is the motor current; the rail
sees it times the PWM duty (< 1 while moving or holding below stall), so the average is lower —
but the peaks are real and are what the regulator and the bulk capacitors must take. The servo
stall current is not in any datasheet: sources measure 0.36 to 0.75 A for SG90-type servos, so
every result is given for that whole range until the F3 bench measures our clones.

Simulated: standing, rising at the design speed and lateral rocking at walking pace (the same
motion as rocking_test.py). Not simulated, computed: power-on (every servo jumps to its first
command at once), a fall or a jam, and an arm gesture.
"""

import argparse
import sys
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from f1_experiments import MODELS, SG90, Robot, ramp  # noqa: E402
from rocking_test import A0, smooth, targets  # noqa: E402

I_IDLE_A = 0.010                         # servo electronics, holding with no load
I_MOVE_A = 0.25                          # moving with a light load (upper end of 0.10-0.25 A quoted)
I_STALL_A = (0.36, 0.55, 0.75)           # measured / typical / pessimistic SG90-type stall current
WINDOW_S = 0.020                         # one servo PWM frame: what a few hundred µF smooth out
RISE_SPEED = 0.7                         # rad/s of the crouch A: the design limit from F1
STEP_RATES = (0.50, 0.67, 1.00)          # steps/s


def run(m, schedule, seconds: float, watch_from: float):
    """Simulate; return the summed load fraction sum(|torque| / stall) over time from watch_from,
    and whether the robot fell."""
    r = Robot(m)
    d = mujoco.MjData(m)
    load = []
    while d.time < seconds:
        d.ctrl[:] = schedule(d.time)
        mujoco.mj_step(m, d)
        if d.time >= watch_from:
            load.append(float(np.sum(np.abs(d.actuator_force))) / SG90)
        if r.tilt(d) > 40.0:
            return np.array(load), True
    return np.array(load), False


def scenarios(m, tilt: float):
    r = Robot(m)
    crouch = lambda a: r.ctrl({"l": a, "r": a})  # noqa: E731
    settle = lambda t: crouch(A0 * smooth(t / 1.0))  # noqa: E731
    yield "em pé (agachado leve, parado)", *run(m, settle, 4.0, 2.0)

    a0 = 0.6
    t_down, t_up0 = a0 / 0.5, a0 / 0.5 + 1.5
    t_up1 = t_up0 + a0 / RISE_SPEED

    def rise(t):
        a = ramp(t, 0, t_down, 0, a0) if t < t_up0 else ramp(t, t_up0, t_up1, a0, 0)
        return crouch(a)
    yield f"levantar de A = 0,6 a {RISE_SPEED} rad/s", *run(m, rise, t_up1 + 0.5, t_up0)

    for rate in STEP_RATES:
        period = 2 / rate

        def rock(t, period=period):
            if t < 1.5:
                return settle(t)
            roll, a = targets(t - 1.5, period, tilt)
            return r.ctrl(a, roll=roll)
        yield f"balanço lateral {rate:.2f} passo/s", *run(m, rock, 1.5 + 4 * period, 1.5 + period)


def stats(load: np.ndarray, dt: float, n: int, i_stall: float):
    """(average, peak over one PWM frame, instantaneous peak) of the rail current in A."""
    amps = n * I_IDLE_A + (i_stall - I_IDLE_A) * load
    k = max(1, int(round(WINDOW_S / dt)))
    framed = np.convolve(amps, np.ones(k) / k, mode="valid")
    return amps.mean(), framed.max(), amps.max()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--model", default="f1")
    ap.add_argument("--tilt", type=float, default=9.0, help="ankle roll amplitude while rocking, degrees")
    args = ap.parse_args()
    m = mujoco.MjModel.from_xml_path(str(MODELS.get(args.model, args.model)))
    n, dt = m.nu, m.opt.timestep
    stalls = " / ".join(f"{i:.2f}" for i in I_STALL_A)
    print(f"ORÇAMENTO DE CORRENTE do trilho dos servos: {n} SG90, massa {m.body_subtreemass[1] * 1000:.0f} g")
    print(f"corrente de stall por servo {stalls} A (medida / típica / pessimista); "
          f"pico = média em {WINDOW_S * 1000:.0f} ms (um quadro de PWM)\n")
    print(f"  {'cenário':38s} {'carga':>6s}   {'média (A)':^17s}   {'pico 20 ms (A)':^17s}   {'pico instant. (A)':^17s}")
    for name, load, fell in scenarios(m, np.radians(args.tilt)):
        if fell:
            print(f"  {name:38s} CAIU — cenário não vale")
            continue
        cols = [stats(load, dt, n, i) for i in I_STALL_A]
        print(f"  {name:38s} {load.max():5.1f}×   "
              + "   ".join(" / ".join(f"{c[k]:4.1f}" for c in cols) for k in range(3)))
    print("\n  carga = soma de |torque| / stall nos servos, no pico (quantos servos travados equivale)")
    print("\nNÃO SIMULADO (conta):")
    for name, servos, amps in ((f"ligar: os {n} vão à 1ª posição juntos", n, I_STALL_A),
                               ("queda ou trava: as 8 juntas da perna no stall", 8, I_STALL_A),
                               ("gesto: 8 servos do braço movendo juntos, sem carga", 8, (I_MOVE_A,) * 3)):
        total = [servos * a + (n - servos) * I_IDLE_A for a in amps]
        print(f"  {name:52s} " + " / ".join(f"{t:4.1f}" for t in total) + " A")


if __name__ == "__main__":
    main()
