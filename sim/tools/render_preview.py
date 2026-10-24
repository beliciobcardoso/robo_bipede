"""Render the 3D preview of the robot (sim/models/preview_biped.xml) to docs/img/previa_robo.png.

    MUJOCO_GL=glfw .venv/bin/python sim/tools/render_preview.py     (or: make preview)

The preview is generated from the same parameters as the simulation (build_biped.BipedParams),
the scripted servo and bearing meshes, and the bracket concept, so it changes whenever the design
does. Shown slightly crouched, as the robot will stand.
"""

import datetime as dt
import os
import sys
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_biped import PREVIEW_OUT, BipedParams  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "img" / "previa_robo.png"
POSE_A = 0.2              # crouch: hip = A, knee = -2A, ankle = A
# title, azimuth, elevation, distance factor, look-at (x, y, z factors of the standing torso height),
# what to show: "capas" (covers on) or "esqueleto" (covers off) or "detalhe" (one leg, nothing else)
VIEWS = (
    ("com capas: frente", 180, -5, 1.15, (0, 0, 0.7), "capas"),
    ("com capas: lado", 90, -5, 1.15, (0, 0, 0.7), "capas"),
    ("com capas: 3/4", 140, -15, 1.15, (0, 0, 0.7), "capas"),
    ("esqueleto: frente", 180, -5, 1.15, (0, 0, 0.7), "esqueleto"),
    ("esqueleto: 3/4", 140, -18, 1.15, (0, 0, 0.7), "esqueleto"),
    ("detalhe: perna esquerda", 35, -12, 0.55, (0, 0.16, 0.42), "detalhe"),
)


def settle(m: mujoco.MjModel) -> mujoco.MjData:
    d = mujoco.MjData(m)
    coef = {"hip_pitch": 1.0, "knee": -2.0, "ankle_pitch": 1.0, "ankle_roll": 0.0}
    u = np.array([coef.get(m.actuator(i).name.rsplit("_", 1)[0], 0.0) * POSE_A for i in range(m.nu)])
    while d.time < 1.5:
        d.ctrl[:] = u * min(1.0, d.time / 1.0)
        mujoco.mj_step(m, d)
    return d


def hidden(m: mujoco.MjModel, mode: str) -> list[int]:
    """Geoms hidden in a view: the covers (cv_*) unless mode is "capas"; in "detalhe" also the right
    leg, the arms, the head and the torso contents."""
    names = [m.geom(i).name for i in range(m.ngeom)]
    out = []
    for i, n in enumerate(names):
        if mode != "capas" and n.startswith("cv_"):
            out.append(i)
        elif mode == "detalhe" and (n.endswith("_r") or any(k in n for k in ("shoulder", "arm", "elbow", "wrist", "hand"))
                                    or n.startswith(("ultrasonic", "us_eye", "pv_battery", "pv_esp32", "pv_mpu"))
                                    or n == "torso"):
            out.append(i)
    return out


def render_sheet(m: mujoco.MjModel, p: BipedParams, out: Path, heading: str = "Prévia 3D"):
    """Render the six views of a preview model to a PNG."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    d = settle(m)
    r = mujoco.Renderer(m, height=480, width=560)
    base = p.stand_height_mm / 1000
    fig, axes = plt.subplots(2, len(VIEWS) // 2, figsize=(4.6 * len(VIEWS) // 2, 9.4))
    for ax, (title, az, el, dist, look, mode) in zip(axes.flat, VIEWS):
        cam = mujoco.MjvCamera()
        cam.azimuth, cam.elevation, cam.distance = az, el, base * 2.4 * dist
        cam.lookat[:] = [d.qpos[0] + base * look[0], d.qpos[1] + base * look[1], base * look[2]]
        hide = hidden(m, mode)
        saved = (m.geom_matid[hide].copy(), m.geom_rgba[hide].copy())
        m.geom_matid[hide], m.geom_rgba[hide] = -1, 0      # invisible only while rendering this view
        r.update_scene(d, cam)
        m.geom_matid[hide], m.geom_rgba[hide] = saved
        ax.imshow(r.render())
        ax.set_title(title)
        ax.axis("off")
    fig.suptitle(
        f"{heading} — {dt.date.today():%d/%m/%Y} — {p.total_mass_g:.0f} g (capas {p.covers_total_g:.0f} g), "
        f"altura {p.total_height_mm:.0f} mm, {p.servo_count} servos, quadris a {2 * p.hip_half_width_mm:.0f} mm, "
        f"coxa {p.thigh_mm:.0f} / canela {p.shin_mm:.0f} mm\n"
        "capas brancas (conceito de forma) · azul: servos · cinza translúcido: suportes · cinza escuro: garfos · "
        "branco: horns · laranja: tronco · azul-escuro: HC-SR04",
        fontsize=11)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=85, bbox_inches="tight")
    plt.close(fig)
    r.close()


def main():
    m = mujoco.MjModel.from_xml_path(str(PREVIEW_OUT))
    render_sheet(m, BipedParams(), OUT)
    print(f"preview -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    os.environ.setdefault("MUJOCO_GL", "glfw")
    main()
