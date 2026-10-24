"""Which skeleton parts stick out of the covers? (preview model, standing pose)

    .venv/bin/python sim/tools/cover_check.py [--pose A]

Samples every skeleton visual of the preview (pv_* geoms: servo and bearing meshes, holders, yokes,
horns, boards) at its vertices / box corners and tests each point against every cover (cv_* geoms:
convex meshes, ellipsoids, capsules, spheres). Prints, per part, the share of points outside all
covers and how far the worst one sticks out. Joints left uncovered on purpose (knees, ankles, hip
servos below the torso cover, the shoulder link) show up here too — the list is for review, not a
pass/fail.
"""

import argparse
import sys
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial import ConvexHull

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_biped import PREVIEW_OUT  # noqa: E402

BOX_CORNERS = np.array([[x, y, z] for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)], float)


def geom_points(m, d, g) -> np.ndarray:
    """World-frame sample points of a geom (mesh vertices or box corners)."""
    if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
        mid = m.geom_dataid[g]
        local = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
    else:
        local = BOX_CORNERS * m.geom_size[g]
    return d.geom_xpos[g] + local @ d.geom_xmat[g].reshape(3, 3).T


def outside_depth(m, d, g, pts) -> np.ndarray:
    """How far each point is outside cover geom g (<= 0 inside), metres (approx. for meshes)."""
    local = (pts - d.geom_xpos[g]) @ d.geom_xmat[g].reshape(3, 3)
    t, size = m.geom_type[g], m.geom_size[g]
    if t == mujoco.mjtGeom.mjGEOM_SPHERE:
        return np.linalg.norm(local, axis=1) - size[0]
    if t == mujoco.mjtGeom.mjGEOM_ELLIPSOID:
        k = np.linalg.norm(local / size, axis=1)
        return (k - 1) * size.min()
    if t == mujoco.mjtGeom.mjGEOM_CAPSULE:
        z = np.clip(local[:, 2], -size[1], size[1])
        return np.linalg.norm(local - np.c_[0 * z, 0 * z, z], axis=1) - size[0]
    if t == mujoco.mjtGeom.mjGEOM_MESH:
        mid = m.geom_dataid[g]
        v = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
        eq = ConvexHull(v).equations                        # n.x + c <= 0 inside
        return (local @ eq[:, :3].T + eq[:, 3]).max(axis=1)
    raise ValueError(f"cover geom type {t} not handled")


def report(m, d) -> list:
    names = [m.geom(i).name for i in range(m.ngeom)]
    covers = [i for i, n in enumerate(names) if n.startswith("cv_") and n != "cv_visor"]
    rows = []
    for g, n in enumerate(names):
        if not n.startswith("pv_"):
            continue
        pts = geom_points(m, d, g)
        depth = np.min([outside_depth(m, d, c, pts) for c in covers], axis=0)
        out = depth > 0.0005
        if out.any():
            rows.append((n, out.mean(), depth.max() * 1000))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pose", type=float, default=0.0, help="crouch A (rad), hip = A, knee = -2A, ankle = A")
    args = ap.parse_args()
    m = mujoco.MjModel.from_xml_path(str(PREVIEW_OUT))
    d = mujoco.MjData(m)
    for i in range(m.nu):
        coef = {"hip_pitch": 1.0, "knee": -2.0, "ankle_pitch": 1.0}.get(m.actuator(i).name.rsplit("_", 1)[0], 0.0)
        d.qpos[m.jnt_qposadr[m.actuator_trnid[i, 0]]] = coef * args.pose
    mujoco.mj_forward(m, d)
    rows = report(m, d)
    print(f"peças do esqueleto fora das capas (A = {args.pose}):  parte   % dos pontos fora   quanto sai (mm)")
    for n, frac, mm in sorted(rows, key=lambda r: -r[2]):
        print(f"  {n:32s} {100 * frac:5.0f}%   {mm:5.1f}")


if __name__ == "__main__":
    main()
