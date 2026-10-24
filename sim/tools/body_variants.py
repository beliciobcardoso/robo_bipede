"""Body proportion study with SG90 servos on every joint: how close to the UBTECH Alpha 1 look
(head / torso / legs ~ 21 / 30 / 47 % of the height) can the robot get and still pass?

    .venv/bin/python sim/tools/body_variants.py            # ~5 min on all CPU cores
    .venv/bin/python sim/tools/body_variants.py --no-images

Grid: torso height x torso width at the shoulders x head size x cover wall thickness. Every variant
gets covers sized to enclose its own skeleton (body.shells), so a bigger torso or head also weighs more.
For each one: lateral rocking at 0.5 and 1 step/s for several ankle-roll amplitudes (open loop, as
rocking_test.py), the one-leg stance scan and the rise from a crouch (f1_experiments.py). Torques are
in % of the stall torque of the servo actually on that joint. Peaks are read at the ankle-roll
amplitude closest to the middle of that variant's own one-leg stance range: a taller robot needs
less tilt to put its weight over one foot, so one fixed amplitude would overshoot it.

Writes sim/results/body_variants.csv (sorted: passing first, then closest to the Alpha look) and
sim/results/variants/comparacao.png (current robot vs the closest passing variants).
"""

import argparse
import csv
import itertools
import sys
from dataclasses import replace
from multiprocessing import Pool
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rocking_test as rk  # noqa: E402
from body import JOINT_STOPS, BipedParams  # noqa: E402
from build_biped import build_xml, load_preview  # noqa: E402
from f1_experiments import one_leg_scan, rise_peak  # noqa: E402

RESULTS = Path(__file__).resolve().parents[1] / "results"
LIMIT_PCT = 70.0                      # same pass line as F2: peak <= 70 % of the servo's stall torque
ROLLS_DEG = (10, 12, 14, 16)
PACES = {"0.5": 4.0, "1.0": 2.0}       # steps/s -> rocking cycle period (s)

ALPHA_PCT = (21.0, 30.0, 47.0)        # head, torso, legs — measured on photos of the Alpha 1
TORSO_HEIGHTS_MM = (45.0, 52.0, 60.0, 68.0)
TOP_WIDTHS_MM = (70.0, 86.0)          # 86: both shoulder pitch stacks get their 623ZZ
HEADS_MM = {"P": (40.0, 50.0, 30.0), "M": (46.0, 54.0, 40.0), "G": (52.0, 58.0, 48.0)}
SHELLS_MM = (1.2, 1.0, 0.8)
PROPORTIONS = {f"t{h:.0f}_o{w:.0f}_c{k}": dict(torso_size_mm=(50.0, 70.0, h), torso_top_width_mm=w, head_size_mm=hd)
               for h in TORSO_HEIGHTS_MM for w in TOP_WIDTHS_MM for k, hd in HEADS_MM.items()}
CURRENT = "t45_o70_cP"                # the robot before the 2026-10-24 proportion change


def params(prop: str, shell: float) -> BipedParams:
    return replace(BipedParams(), shell_mm=shell, **PROPORTIONS[prop])


def proportions_pct(p: BipedParams) -> dict:
    """Head / torso / legs as % of the total height (torso = hip axis to torso top)."""
    h = p.total_height_mm
    legs = p.stand_height_mm - p.torso_size_mm[2] / 2 - p.hip_drop_mm
    torso = p.torso_size_mm[2] + p.hip_drop_mm
    return dict(head=100 * (h - legs - torso) / h, torso=100 * torso / h, legs=100 * legs / h)


def pct(p: BipedParams, joint: str, nm: float) -> float:
    return 100 * nm / p.servo(joint).stall_nm


def job(args):
    key, kind, arg = args
    p = params(*key)
    m = mujoco.MjModel.from_xml_string(build_xml(p))
    if kind == "rock":
        pace, roll = arg
        r = rk.run(m, PACES[pace], np.radians(roll), 4)
        if r["fell"]:
            return key, kind, arg, None
        return key, kind, arg, {t: pct(p, t, v) for t, v in r["peak"].items()}
    if kind == "one_leg":
        rows = [r for r in one_leg_scan(m) if r[1]]
        if not rows:
            return key, kind, arg, None
        worst = {t: max(pct(p, t, r[3][t]) for r in rows) for t in JOINT_STOPS}
        return key, kind, arg, dict(lo=rows[0][0], hi=rows[-1][0], **worst)
    peak, fell = rise_peak(m, 1.0)
    return key, kind, arg, None if fell else {t: pct(p, t, v) for t, v in peak.items()}


def alpha_distance(p: BipedParams) -> float:
    """How far the head / torso / legs split is from the Alpha 1 (percentage points)."""
    pr = proportions_pct(p)
    return float(np.linalg.norm(np.subtract((pr["head"], pr["torso"], pr["legs"]), ALPHA_PCT)))


def summarise(results) -> list:
    by = {}
    for key, kind, arg, val in results:
        by.setdefault(key, {})[(kind, arg)] = val
    rows = []
    for key, r in by.items():
        p = params(*key)
        row = dict(proporcao=key[0], parede_mm=key[1], massa_g=round(p.total_mass_g),
                   capas_g=round(p.covers_total_g), altura_mm=round(p.total_height_mm),
                   **{f"{k}_pct_altura": round(v) for k, v in proportions_pct(p).items()},
                   dist_alpha=round(alpha_distance(p), 1))
        leg = r[("one_leg", None)]
        row["uma_perna"] = f"{leg['lo']:.0f} a {leg['hi']:.0f}°" if leg else "tomba"
        mid = abs(leg["lo"] + leg["hi"]) / 2 if leg else 14.0
        check = min(ROLLS_DEG, key=lambda roll: (abs(roll - mid), -roll))
        row["roll_teste_graus"] = check
        for pace in PACES:
            ok = [roll for roll in ROLLS_DEG if r[("rock", (pace, roll))] is not None]
            row[f"balanco_{pace}_faixa"] = f"{min(ok)}-{max(ok)}" if ok else "cai"
            chk = r[("rock", (pace, check))]
            row[f"roll_{pace}_pct"] = round(chk["ankle_roll"]) if chk else None
            row[f"joelho_{pace}_pct"] = round(chk["knee"]) if chk else None
        rise = r[("rise", None)]
        row["levantar_joelho_pct"] = round(rise["knee"]) if rise else None
        peaks = [row["roll_1.0_pct"], row["joelho_1.0_pct"], row["levantar_joelho_pct"]]
        row["pior_pico_pct"] = max(peaks) if None not in peaks else None
        row["passa"] = row["pior_pico_pct"] is not None and row["pior_pico_pct"] <= LIMIT_PCT \
            and leg is not None and row["balanco_0.5_faixa"] != "cai"
        rows.append(row)
    return sorted(rows, key=lambda w: (not w["passa"], w["dist_alpha"], -w["parede_mm"]))


def comparison_image(out: Path, picks: list):
    """Variants side by side at the same scale, covers on, front and 3/4. picks: [(label, key)]."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from render_preview import hidden, settle

    fig, axes = plt.subplots(2, len(picks), figsize=(5.2 * len(picks), 11))
    for col, (label, key) in enumerate(picks):
        p = params(*key)
        m = load_preview(p)
        d = settle(m)
        r = mujoco.Renderer(m, height=640, width=520)
        hide = hidden(m, "capas")
        m.geom_matid[hide], m.geom_rgba[hide] = -1, 0
        for row, (az, el) in enumerate(((180, -4), (145, -12))):
            cam = mujoco.MjvCamera()
            cam.azimuth, cam.elevation, cam.distance = az, el, 0.62
            cam.lookat[:] = [d.qpos[0], d.qpos[1], 0.135]
            r.update_scene(d, cam)
            ax = axes[row, col]
            ax.imshow(r.render())
            ax.axis("off")
            if row == 0:
                pr = proportions_pct(p)
                ax.set_title(f"{label}\n{p.total_height_mm:.0f} mm · {p.total_mass_g:.0f} g · parede {key[1]} mm\n"
                             f"cabeça {pr['head']:.0f} % · tronco {pr['torso']:.0f} % · pernas {pr['legs']:.0f} %", fontsize=12)
        r.close()
    fig.suptitle("SG90 em todas as juntas — mesma escala, capas conceito (Alpha 1: cabeça 21 · tronco 30 · pernas 47 %)",
                 fontsize=13)
    fig.savefig(out, dpi=80, bbox_inches="tight")
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--no-images", action="store_true")
    args = ap.parse_args()
    keys = list(itertools.product(PROPORTIONS, SHELLS_MM))
    jobs = [(k, "rock", (pace, roll)) for k in keys for pace in PACES for roll in ROLLS_DEG]
    jobs += [(k, "one_leg", None) for k in keys] + [(k, "rise", None) for k in keys]
    with Pool() as pool:
        results = pool.map(job, jobs, chunksize=1)
    rows = summarise(results)
    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "body_variants.csv"
    with out.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    cols = ("proporcao", "parede_mm", "massa_g", "capas_g", "altura_mm", "head_pct_altura", "torso_pct_altura",
            "legs_pct_altura", "dist_alpha", "roll_teste_graus", "balanco_0.5_faixa", "balanco_1.0_faixa",
            "roll_0.5_pct", "roll_1.0_pct", "joelho_1.0_pct", "levantar_joelho_pct", "pior_pico_pct", "passa")
    print("  ".join(cols))
    for r in rows:
        print("  ".join(str(r[c]) for c in cols))
    print(f"-> {out.relative_to(RESULTS.parents[1])}")
    if not args.no_images:
        passing = [r for r in rows if r["passa"]]
        picks = [("antes (24/10)", (CURRENT, 1.2))]
        if passing:
            picks.append(("mais perto do Alpha que passa", (passing[0]["proporcao"], passing[0]["parede_mm"])))
            margin = [r for r in passing if r["pior_pico_pct"] <= LIMIT_PCT - 5]
            if margin and margin[0] is not passing[0]:
                picks.append(("idem, com 5 pontos de folga", (margin[0]["proporcao"], margin[0]["parede_mm"])))
        img = RESULTS / "variants" / "comparacao.png"
        img.parent.mkdir(exist_ok=True)
        comparison_image(img, picks)
        print(f"-> {img.relative_to(RESULTS.parents[1])}")


if __name__ == "__main__":
    main()
