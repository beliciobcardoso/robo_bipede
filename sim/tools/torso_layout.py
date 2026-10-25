"""Fit the torso contents (body.TORSO_PARTS) between the servos inside the torso frame.

    .venv/bin/python sim/tools/torso_layout.py --search    # find a layout, print it for body.TORSO_LAYOUT
    .venv/bin/python sim/tools/torso_layout.py              # check the stored layout + free volume left

1 mm voxel grid of the frame interior (walls 2 mm, width tapering from the hips to the shoulders).
Taken: the servos and holders inside the torso (from the preview model) and everything the hip
yokes and the shoulder horns sweep over their joint range. Each part is a box plus envelopes kept
free for what plugs into it (servo plugs, wires, USB); an access envelope must reach the wall so
the cable can come from outside. The search tries every axis-aligned rotation of every part and
every position (summed-volume table, so all positions are tested at once), places the parts
largest first with a preference per part, and backtracks over the best few candidates.
"""

import argparse
import itertools
import sys
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import body  # noqa: E402
from body import TORSO_PARTS, BipedParams  # noqa: E402
from build_biped import load_preview  # noqa: E402

WALL_MM = 2.0
CLEAR_MM = 1                       # air kept around the servos and the swept parts
SWEEP_STEP_DEG = 10.0
CANDIDATES = 16                    # positions tried per part when backtracking
DIVERSE_MM = 8.0                   # candidates of one rotation at least this far apart
STRIDE = 2                         # candidate centres sampled every STRIDE mm (all positions still checked)
ORDER = ("bateria", "regulador", "pca9685", "controle", "distribuicao", "chave", "regulador_logica", "mpu6050")


# ------------------------------------------------------------------ grid
class Grid:
    """Torso-frame voxels: index i <-> coordinate lo + i (mm)."""

    def __init__(self, p: BipedParams):
        tx, ty, tz = p.torso_size_mm
        self.lo = np.array([-tx / 2, -max(ty, p.torso_top_width_mm) / 2, -tz / 2])
        self.shape = (int(tx), int(max(ty, p.torso_top_width_mm)), int(tz))
        x, y, z = (np.arange(n) + 0.5 + lo for n, lo in zip(self.shape, self.lo))
        X, Y, Z = np.meshgrid(x, y, z, indexing="ij")
        half_y = ty / 2 + (p.torso_top_width_mm - ty) / 2 * (Z + tz / 2) / tz - WALL_MM
        self.inside = (abs(X) < tx / 2 - WALL_MM) & (abs(Y) < half_y) & (abs(Z) < tz / 2 - WALL_MM)
        self.taken = ~self.inside

    def box(self, lo_mm, hi_mm):
        a = np.clip(np.floor(np.asarray(lo_mm) - self.lo).astype(int), 0, self.shape)
        b = np.clip(np.ceil(np.asarray(hi_mm) - self.lo).astype(int), 0, self.shape)
        return tuple(slice(i, j) for i, j in zip(a, b))


def _torso_frame_aabb(m, d, g, torso):
    if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_MESH:
        mid = m.geom_dataid[g]
        v = m.mesh_vert[m.mesh_vertadr[mid]:m.mesh_vertadr[mid] + m.mesh_vertnum[mid]]
    else:
        v = np.array(list(itertools.product((-1, 1), repeat=3))) * m.geom_size[g]
    w = d.geom_xpos[g] + v @ d.geom_xmat[g].reshape(3, 3).T
    local = (w - d.xpos[torso]) @ d.xmat[torso].reshape(3, 3) * 1000
    return local.min(0), local.max(0)


def mark_servos(grid: Grid, p: BipedParams):
    """Servo, holder, horn, yoke visuals near the torso: fixed ones as they are, the hip and shoulder
    ones over their whole joint range."""
    m = load_preview(p)
    d = mujoco.MjData(m)
    torso = m.body("torso").id
    movers = {m.body(f"{b}_{s}").id: f"{j}_{s}" for b, j in (("thigh", "hip_pitch"), ("shoulder", "shoulder_pitch"))
              for s in "lr"}
    for body, joint in [(torso, None), *movers.items()]:
        geoms = [g for g in range(m.ngeom) if m.geom_bodyid[g] == body and m.geom(g).name.startswith("pv_")
                 and not m.geom(g).name.startswith(("pv_battery", "pv_esp32", "pv_mpu", "pv_part"))]
        if joint is None:
            angles = [0.0]
        else:
            lo, hi = m.jnt_range[m.joint(joint).id]
            angles = np.arange(lo, hi + 1e-9, np.radians(SWEEP_STEP_DEG))
        for a in angles:
            if joint is not None:
                d.qpos[m.jnt_qposadr[m.joint(joint).id]] = a
            mujoco.mj_kinematics(m, d)
            for g in geoms:
                lo_, hi_ = _torso_frame_aabb(m, d, g, torso)
                grid.taken[grid.box(lo_ - CLEAR_MM, hi_ + CLEAR_MM)] = True
        if joint is not None:
            d.qpos[m.jnt_qposadr[m.joint(joint).id]] = 0.0


# ------------------------------------------------------------------ parts
ROTATIONS = [np.array(r) for r in itertools.product(*[[(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]] * 3)
             if abs(np.linalg.det(np.array(r))) == 1 and round(np.linalg.det(np.array(r))) == 1]


def boxes(part, rot: np.ndarray):
    """[(centre, half), ...] in the torso frame for a part at the origin: the body, then envelopes."""
    out = [(np.zeros(3), np.abs(rot @ np.array(part.size_mm) / 2))]
    out += [(rot @ np.array(c), np.abs(rot @ np.array(h))) for c, h in part.envelopes]
    return out


def _sat(a: np.ndarray) -> np.ndarray:
    s = np.zeros(tuple(n + 1 for n in a.shape), dtype=np.int32)
    s[1:, 1:, 1:] = a.astype(np.int32).cumsum(0).cumsum(1).cumsum(2)
    return s


def _box_sums(s: np.ndarray, size):
    """Sum of every size-shaped box, indexed by its low corner."""
    a, b, c = size
    return (s[a:, b:, c:] - s[:-a, b:, c:] - s[a:, :-b, c:] - s[a:, b:, :-c]
            + s[:-a, :-b, c:] + s[:-a, b:, :-c] + s[a:, :-b, :-c] - s[:-a, :-b, :-c])


def _shifted(arr: np.ndarray, off, shape, fill) -> np.ndarray:
    """out[i] = arr[i + off] where that index exists, else fill."""
    out = np.full(shape, fill, arr.dtype)
    src, dst = [], []
    for o, n, m in zip(off, shape, arr.shape):
        a, b = max(0, -o), min(n, m - o)          # range of i with 0 <= i + o < m
        if b <= a:
            return out
        dst.append(slice(a, b))
        src.append(slice(a + o, b + o))
    out[tuple(dst)] = arr[tuple(src)]
    return out


def free_positions(grid: Grid, part, rot, sat, outside_sat):
    """Bool map over the part-centre voxel: the body and every envelope land on free voxels, and every
    access envelope touches the wall (outside voxels within 2 mm around it)."""
    ok = np.ones(grid.shape, bool)
    for k, (c, h) in enumerate(boxes(part, rot)):
        size = np.maximum(1, np.round(2 * h).astype(int))
        off = np.round(c - size / 2).astype(int)                       # low corner relative to the centre voxel
        ok &= _shifted(_box_sums(sat, size), off, grid.shape, 1) == 0
        if k - 1 in part.access:
            touch = _box_sums(outside_sat, size + 4) > 0
            ok &= _shifted(touch, off - 2, grid.shape, False)
    return ok


def score(name, centres: np.ndarray, rot, p: BipedParams) -> np.ndarray:
    """Preference of each candidate centre (N x 3, mm), lower is better."""
    x, y, z = centres.T
    if name == "bateria":
        # TODO(human): where should the battery (55 g, the heaviest part in the torso) go?
        # Return one number per candidate (array like x), lower = better. Torso frame in mm:
        # x forward (back wall -36, front +36), y left (+-37 at the hips), z up (floor -32, top +32).
        raise NotImplementedError("battery placement preference")
    if name == "mpu6050":
        return np.abs(x) + np.abs(y) + np.abs(z + 10)  # near the middle of the robot
    return -2 * np.abs(x) - 0.5 * np.abs(y)            # boards against the walls: the middle stays free for cables


def place(grid: Grid, name, centre, rot, value=True):
    for c, h in boxes(TORSO_PARTS[name], rot):
        grid.taken[grid.box(np.array(centre) + c - h, np.array(centre) + c + h)] = value


def _options(grid: Grid, name, p, sat, outside_sat):
    """Every free (centre, rotation) of a part, best score first, thinned to positions at least
    DIVERSE_MM apart (per rotation) so backtracking tries different places, not 1 mm nudges."""
    part = TORSO_PARTS[name]
    out, total = [], 0
    for rot in ROTATIONS:
        if part.flat and abs(rot[2, 2]) != 1:
            continue
        ok = free_positions(grid, part, rot, sat, outside_sat)
        count = int(ok.sum())
        if count == 0:
            continue
        idx = np.argwhere(ok[::STRIDE, ::STRIDE, ::STRIDE]) * STRIDE
        if len(idx) == 0:
            idx = np.argwhere(ok)
        centres = idx + grid.lo + 0.5
        sc = score(name, centres, rot, p)
        best = np.argsort(sc)[:CANDIDATES * 40]
        out += [(sc[i], tuple(np.round(centres[i], 1)), rot) for i in best]
        total += count
    out.sort(key=lambda o: o[0])
    picked = []
    for o in out:
        if all(not np.array_equal(o[2], q[2]) or np.abs(np.subtract(o[1], q[1])).max() >= DIVERSE_MM for q in picked):
            picked.append(o)
            if len(picked) == CANDIDATES:
                break
    return picked, total


def search(grid: Grid, p: BipedParams, chosen=None):
    """Depth-first: place the part with the fewest free positions next (MRV); give up on a branch
    as soon as any remaining part has nowhere to go (forward checking)."""
    chosen = chosen or {}
    left = [n for n in ORDER if n not in chosen]
    if not left:
        return chosen
    sat, outside_sat = _sat(grid.taken), _sat(~grid.inside)
    opts = {n: _options(grid, n, p, sat, outside_sat) for n in left}
    if any(count == 0 for _, count in opts.values()):
        return None
    name = min(left, key=lambda n: opts[n][1])
    for _, centre, rot in opts[name][0]:
        snapshot = grid.taken.copy()
        place(grid, name, centre, rot)
        found = search(grid, p, {**chosen, name: (centre, rot)})
        if found:
            return found
        grid.taken = snapshot
    return None


def check(grid: Grid, layout) -> list:
    """Overlaps of the stored layout (mm³ per part)."""
    problems = []
    for name, (centre, rot) in layout.items():
        for k, (c, h) in enumerate(boxes(TORSO_PARTS[name], np.array(rot))):
            sl = grid.box(np.array(centre) + c - h, np.array(centre) + c + h)
            clash = int(grid.taken[sl].sum())
            if clash:
                problems.append((name, "corpo" if k == 0 else f"envelope {k - 1}", clash))
        place(grid, name, centre, np.array(rot))
    return problems


def render(p: BipedParams, out: Path, title: str):
    """Torso interior from the front, the side and above: covers, torso box, arms and head hidden."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    m = load_preview(p)
    d = mujoco.MjData(m)
    mujoco.mj_forward(m, d)
    names = [m.geom(i).name for i in range(m.ngeom)]
    keep = [i for i, n in enumerate(names) if n.startswith("pv_part") or
            (n.startswith("pv_") and any(k in n for k in ("hip_pitch", "shoulder_pitch")))]
    hide = [i for i in range(m.ngeom) if i not in keep and names[i] != "floor"]
    m.geom_matid[hide], m.geom_rgba[hide] = -1, 0
    r = mujoco.Renderer(m, height=560, width=560)
    torso = d.xpos[m.body("torso").id]
    fig, axes = plt.subplots(1, 3, figsize=(16, 5.6))
    for ax, (label, az, el) in zip(axes, (("frente", 180, 0), ("lado (esquerdo)", 90, 0), ("de cima", 180, -89))):
        cam = mujoco.MjvCamera()
        cam.azimuth, cam.elevation, cam.distance = az, el, 0.24
        cam.lookat[:] = torso
        r.update_scene(d, cam)
        ax.imshow(r.render())
        ax.set_title(label)
        ax.axis("off")
    fig.suptitle(title, fontsize=11)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=80, bbox_inches="tight")
    plt.close(fig)
    r.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--search", action="store_true")
    args = ap.parse_args()
    p = BipedParams()
    grid = Grid(p)
    mark_servos(grid, p)
    free0 = int((grid.inside & ~grid.taken).sum())
    print(f"tronco {p.torso_size_mm} (ombros {p.torso_top_width_mm:.0f}), ombro pitch com o corpo '{p.shoulder_pitch_body}': "
          f"interior {grid.inside.sum() / 1000:.0f} cm³, livre entre os servos {free0 / 1000:.0f} cm³")
    if args.search:
        layout = search(grid, p)
        if layout is None:
            print("NÃO CABE: nenhuma arrumação encontrada")
            sys.exit(1)
        print("TORSO_LAYOUT = {")
        for name, (centre, rot) in layout.items():
            print(f'    "{name}": ({tuple(float(v) for v in centre)}, {tuple(tuple(int(v) for v in row) for row in rot)}),')
        print("}")
    else:
        problems = check(grid, {k: (v[0], v[1]) for k, v in body.TORSO_LAYOUT.items()})
        for name, what, mm3 in problems:
            print(f"  COLISÃO {name} ({what}): {mm3} mm³")
        if not problems:
            print("  todas as peças cabem, sem colisão")
    left = int((grid.inside & ~grid.taken).sum())
    print(f"livre para cabos depois das peças: {left / 1000:.0f} cm³")


if __name__ == "__main__":
    main()
