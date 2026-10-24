"""Cover mount standard, skeleton side: pocket for the clip hook + 2 locating-pin holes.

A small coupon of a skeleton part (bracket, thigh, torso...) with the features every part needs
to receive a cover: a pocket in the side face where the hook snaps in, and two holes in the top
face for the locating pins. It is the skeleton half of the tolerance test print. Same coordinate
system and SnapDims as snap_clip.py (assembled position), so the two coupons fit as modelled.

The build also checks the assembly: the cover coupon must touch the skeleton coupon only where
intended (no overlapping material).
"""

import os
import sys

import FreeCAD as App

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cadlib import add_box, add_cylinder, cut, export_part, fuse, run_as_script  # noqa: E402
import snap_clip  # noqa: E402
from snap_clip import DIMS, SnapDims  # noqa: E402

DOC_NAME = "snap_socket"
BLOCK_DEPTH = 8.0          # skeleton coupon thickness (+Y)
BLOCK_H = 12.0             # skeleton coupon height below the top face
OVERLAP_TOL_MM3 = 1e-3


def build(doc, d: SnapDims = DIMS):
    block = add_box(doc, "Block", d.coupon_len, BLOCK_DEPTH, BLOCK_H, 0, 0, -BLOCK_H)
    (hx0, hx1), (hz0, hz1) = d.hook_x, d.hook_z
    c = d.pocket_clearance
    pocket = add_box(doc, "HookPocket", hx1 - hx0 + 2 * c, d.pocket_depth, hz1 - hz0 + 2 * c,
                     hx0 - c, -1e-3, hz0 - c)
    depth = d.pin_len + 0.5
    holes = [add_cylinder(doc, f"PinHole{i}", d.hole_d, depth + 1, x, d.pin_y, -depth)
             for i, x in enumerate(d.pin_xs)]
    return cut(doc, "SkeletonCoupon", block, fuse(doc, "Recesses", [pocket, *holes]))


def check_fit(socket_shape, d: SnapDims = DIMS) -> float:
    """Volume where the cover coupon and the skeleton coupon overlap when assembled (mm³)."""
    tmp = App.newDocument("fit_check")
    cover = snap_clip.build(tmp, d)
    tmp.recompute()
    overlap = cover.Shape.common(socket_shape).Volume
    App.closeDocument(tmp.Name)
    return overlap


def main():
    doc = App.newDocument(DOC_NAME)
    socket = build(doc)
    export_part(doc, socket, DOC_NAME)
    overlap = check_fit(socket.Shape)
    status = "ok" if overlap < OVERLAP_TOL_MM3 else "OVERLAP"
    print(f"[{DOC_NAME}] assembled with snap_clip: overlap {overlap:.4f} mm3 ({status})")
    if overlap >= OVERLAP_TOL_MM3:
        raise RuntimeError("cover and skeleton coupons overlap when assembled")


if run_as_script(__name__, DOC_NAME):
    main()
