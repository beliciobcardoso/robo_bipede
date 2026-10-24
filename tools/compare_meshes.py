"""Volumetric diff of two STL solids on the GPU (CuPy) by vertical ray casting.

For every column of an XY grid a ray is cast along Z; its exact crossings with
each mesh give the inside intervals. Comparing the intervals of A and B per
column yields the volume only in A, only in B, and where they are.

    .venv/bin/python tools/compare_meshes.py A.stl B.stl [--step 0.05] [--png out.png]

A and B must share the coordinate system. The grid is offset by an irrational
amount so rays practically never hit a mesh edge or vertex exactly; columns with
an odd crossing count (cracks in a non-watertight mesh) are counted and skipped.
"""

import argparse
import time

import cupy as cp
import numpy as np

STL_DTYPE = np.dtype([("n", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")])
GRID_OFFSET = (0.0123457, 0.0098765)
TILE_MM = 1.0
Z_BIN = 0.1     # mm, resolution of the location maps (volumes are exact in Z)

# Regions of the servo in its own coordinate frame (see cad/parts/servo_sg90.py).
REGIONS = ("eixo", "torre/ressalto", "abas", "cabo", "corpo")


def load_stl(path: str) -> np.ndarray:
    with open(path, "rb") as f:
        f.seek(80)
        count = int(np.frombuffer(f.read(4), "<u4")[0])
        data = np.frombuffer(f.read(count * STL_DTYPE.itemsize), STL_DTYPE)
    return data["v"].astype(np.float64)          # (n, 3 vertices, xyz)


class GpuMesh:
    """Non-vertical triangles of a mesh, prepared for XY point-in-triangle tests."""

    def __init__(self, tris: np.ndarray):
        t = cp.asarray(tris)
        x0, y0 = t[:, 0, 0], t[:, 0, 1]
        e1, e2 = t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
        det = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]   # 2 x signed XY area; sign = normal z
        keep = cp.abs(det) > 1e-14                          # vertical faces never cross a Z ray
        self.x0, self.y0, self.z0 = x0[keep], y0[keep], t[keep, 0, 2]
        self.e1, self.e2, self.det = e1[keep], e2[keep], det[keep]
        self.xmin, self.xmax = t[keep, :, 0].min(1), t[keep, :, 0].max(1)
        self.ymin, self.ymax = t[keep, :, 1].min(1), t[keep, :, 1].max(1)
        self.count = int(keep.sum())

    def crossings(self, px: cp.ndarray, py: cp.ndarray, box) -> cp.ndarray:
        """Sorted Z crossings for each ray (rows); NaN-padded. Shape (rays, k)."""
        sel = cp.nonzero((self.xmax >= box[0]) & (self.xmin <= box[1])
                         & (self.ymax >= box[2]) & (self.ymin <= box[3]))[0]
        if sel.size == 0:
            return cp.full((px.size, 0), cp.nan)
        dx = px[:, None] - self.x0[sel][None, :]
        dy = py[:, None] - self.y0[sel][None, :]
        e1, e2, det = self.e1[sel], self.e2[sel], self.det[sel]
        u = (dx * e2[None, :, 1] - dy * e2[None, :, 0]) / det[None, :]
        v = (dy * e1[None, :, 0] - dx * e1[None, :, 1]) / det[None, :]
        hit = (u >= 0) & (v >= 0) & (u + v <= 1)
        z = self.z0[sel][None, :] + u * e1[None, :, 2] + v * e2[None, :, 2]
        z = cp.where(hit, z, cp.nan)
        k = int(hit.sum(1).max())
        return cp.sort(z, axis=1)[:, :k]


def inside_at(zs: cp.ndarray, zc: cp.ndarray) -> cp.ndarray:
    """Parity test: is height zc (S,) inside, per ray? -> bool (rays, S)."""
    below = (zs[:, :, None] < zc[None, None, :]) & ~cp.isnan(zs)[:, :, None]
    return (below.sum(1) % 2) == 1


def interval_diff(za: cp.ndarray, zb: cp.ndarray):
    """Exact per-ray lengths only-in-A, only-in-B, in-A, in-B from sorted crossings."""
    z = cp.concatenate([za, zb], axis=1)
    lab = cp.concatenate([cp.zeros(za.shape, cp.int8), cp.ones(zb.shape, cp.int8)], axis=1)
    order = cp.argsort(cp.where(cp.isnan(z), cp.inf, z), axis=1)
    z = cp.take_along_axis(z, order, 1)
    lab = cp.take_along_axis(lab, order, 1)
    valid = ~cp.isnan(z)
    pa = (cp.cumsum((lab == 0) & valid, axis=1) % 2).astype(bool)
    pb = (cp.cumsum((lab == 1) & valid, axis=1) % 2).astype(bool)
    dz = cp.nan_to_num(cp.diff(z, axis=1), nan=0.0)
    pa, pb = pa[:, :-1], pb[:, :-1]
    return ((pa & ~pb) * dz).sum(1), ((pb & ~pa) * dz).sum(1), (pa * dz).sum(1), (pb * dz).sum(1)


def region_of(x, y, z):
    reg = np.full(z.shape, "corpo", dtype=object)
    reg[x < -6.0] = "cabo"
    reg[(z > -0.05) & (z < 2.55) & ((x < -6.0) | (x > 17.0))] = "abas"
    reg[z > 7.05] = "torre/ressalto"
    reg[z > 11.05] = "eixo"
    return reg


def compare(path_a: str, path_b: str, step: float):
    ta, tb = load_stl(path_a), load_stl(path_b)
    lo = np.minimum(ta.reshape(-1, 3).min(0), tb.reshape(-1, 3).min(0)) - step
    hi = np.maximum(ta.reshape(-1, 3).max(0), tb.reshape(-1, 3).max(0)) + step
    ga, gb = GpuMesh(ta), GpuMesh(tb)

    xs = np.arange(lo[0] + GRID_OFFSET[0], hi[0], step)
    ys = np.arange(lo[1] + GRID_OFFSET[1], hi[1], step)
    zc = cp.arange(lo[2] + Z_BIN / 2, hi[2], Z_BIN)
    nx, ny, nz = xs.size, ys.size, zc.size
    only_a, only_b, len_a, len_b = (np.zeros((ny, nx)) for _ in range(4))
    map_a_xz, map_b_xz = np.zeros((nz, nx)), np.zeros((nz, nx))
    map_a_yz, map_b_yz = np.zeros((nz, ny)), np.zeros((nz, ny))
    vox_a, vox_b = np.zeros((nz, ny, nx), bool), np.zeros((nz, ny, nx), bool)
    bad = 0

    per_tile = max(1, int(round(TILE_MM / step)))
    t0 = time.time()
    for iy in range(0, ny, per_tile):
        for ix in range(0, nx, per_tile):
            tx, ty = xs[ix:ix + per_tile], ys[iy:iy + per_tile]
            gx, gy = np.meshgrid(tx, ty)
            px, py = cp.asarray(gx.ravel()), cp.asarray(gy.ravel())
            box = (tx[0], tx[-1], ty[0], ty[-1])
            za, zb = ga.crossings(px, py, box), gb.crossings(px, py, box)
            odd = ((~cp.isnan(za)).sum(1) % 2 == 1) | ((~cp.isnan(zb)).sum(1) % 2 == 1)
            bad += int(odd.sum())
            za[odd], zb[odd] = cp.nan, cp.nan
            oa, ob, la, lb = (cp.asnumpy(r).reshape(gx.shape) for r in interval_diff(za, zb))
            sl = (slice(iy, iy + per_tile), slice(ix, ix + per_tile))
            only_a[sl], only_b[sl], len_a[sl], len_b[sl] = oa, ob, la, lb
            ia, ib = inside_at(za, zc), inside_at(zb, zc)
            ia = cp.asnumpy(ia).reshape(*gx.shape, nz).transpose(2, 0, 1)
            ib = cp.asnumpy(ib).reshape(*gx.shape, nz).transpose(2, 0, 1)
            vox_a[:, sl[0], sl[1]], vox_b[:, sl[0], sl[1]] = ia, ib
    cp.cuda.Stream.null.synchronize()
    elapsed = time.time() - t0

    da, db = vox_a & ~vox_b, vox_b & ~vox_a
    map_a_xz, map_b_xz = da.sum(1) * step, db.sum(1) * step
    map_a_yz, map_b_yz = da.sum(2) * step, db.sum(2) * step
    zz, yy, xx = np.meshgrid(cp.asnumpy(zc), ys, xs, indexing="ij")
    vox = step * step * Z_BIN
    regions = {r: [0.0, 0.0] for r in REGIONS}
    for mask, k in ((da, 0), (db, 1)):
        for r, n in zip(*np.unique(region_of(xx[mask], yy[mask], zz[mask]), return_counts=True)):
            regions[r][k] = n * vox

    area = step * step
    return dict(
        vol_a=len_a.sum() * area, vol_b=len_b.sum() * area,
        only_a=only_a.sum() * area, only_b=only_b.sum() * area,
        rays=nx * ny, tris=(ga.count, gb.count), bad=bad, seconds=elapsed,
        regions=regions, extent=(lo, hi), only_a_map=only_a, only_b_map=only_b,
        xz=(map_a_xz, map_b_xz), yz=(map_a_yz, map_b_yz), xs=xs, ys=ys, zc=cp.asnumpy(zc),
    )


def plot(res, png, name_a, name_b):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs, ys, zc = res["xs"], res["ys"], res["zc"]
    views = [
        ("Topo (XY) — espessura em Z", res["only_a_map"], res["only_b_map"], (xs[0], xs[-1], ys[0], ys[-1]), "X", "Y"),
        ("Frente (XZ) — espessura em Y", *res["xz"], (xs[0], xs[-1], zc[0], zc[-1]), "X", "Z"),
        ("Lado (YZ) — espessura em X", *res["yz"], (ys[0], ys[-1], zc[0], zc[-1]), "Y", "Z"),
    ]
    fig, axes = plt.subplots(2, 3, figsize=(17, 9.5), gridspec_kw=dict(width_ratios=[2.6, 2.6, 1.2]))
    for col, (title, ma, mb, ext, xl, yl) in enumerate(views):
        for row, (m, cmap, who) in enumerate(((ma, "Greens", f"só no {name_a}"), (mb, "Reds", f"só no {name_b}"))):
            ax = axes[row, col]
            mm = np.ma.masked_less_equal(m, 1e-9)
            im = ax.imshow(mm, origin="lower", extent=ext, cmap=cmap, vmin=0,
                           vmax=max(float(m.max()), 1e-3), interpolation="nearest", aspect="equal")
            ax.set_facecolor("#f1f3f5")
            ax.set_title(f"{title}\n{who}", fontsize=10)
            ax.set_xlabel(f"{xl} (mm)"); ax.set_ylabel(f"{yl} (mm)")
            fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02, label="mm")
    fig.suptitle(f"{name_a}: {res['vol_a']:.1f} mm³   |   {name_b}: {res['vol_b']:.1f} mm³   |   "
                 f"só no {name_a}: {res['only_a']:.1f} mm³   |   só no {name_b}: {res['only_b']:.1f} mm³",
                 fontsize=12)
    fig.tight_layout()
    fig.savefig(png, dpi=95)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("a"), ap.add_argument("b")
    ap.add_argument("--step", type=float, default=0.05, help="XY ray spacing in mm")
    ap.add_argument("--names", default="A,B", help="labels for A and B")
    ap.add_argument("--png")
    args = ap.parse_args()
    name_a, name_b = args.names.split(",")

    res = compare(args.a, args.b, args.step)
    print(f"GPU: {cp.cuda.runtime.getDeviceProperties(0)['name'].decode()}  "
          f"rays={res['rays']:,}  triangles={res['tris'][0]:,}/{res['tris'][1]:,}  "
          f"time={res['seconds']:.1f}s  skipped odd rays={res['bad']}")
    print(f"volume {name_a}={res['vol_a']:.2f}  {name_b}={res['vol_b']:.2f} mm3")
    print(f"only in {name_a}={res['only_a']:.2f}  only in {name_b}={res['only_b']:.2f} mm3")
    print("by region (only A / only B, mm3, Z sampled at 0.1 mm):")
    for r, (a, b) in res["regions"].items():
        print(f"  {r:16s} {a:8.2f} / {b:8.2f}")
    if args.png:
        plot(res, args.png, name_a, name_b)
        print(f"map -> {args.png}")


if __name__ == "__main__":
    main()
