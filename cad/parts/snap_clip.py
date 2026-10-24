"""Cover mount standard, cover side: snap-fit clip + 2 locating pins (docs/capas.md).

A small coupon of a cover: a vertical side wall with the clip cut into it and a top flange that
rests on the skeleton, with the two locating pins pointing down. It is both the reference for
drawing every cover and the cover half of the tolerance test print. The skeleton half (pocket
and pin holes) is snap_socket.py; both share SnapDims and this coordinate system.

Coordinate system (assembled position):
    skeleton top face  = plane z = 0, skeleton below (z < 0)
    skeleton side face = plane y = 0, skeleton at y > 0; the cover wall sits at -wall < y < 0
    +X                 = along the wall
The cover is pushed down (-Z): the pins guide it, the flange stops it on the top face, the hook
rides over the side face (the beam bends outwards, -Y) and snaps into the pocket.

Print the cover flange-down (upside down): the beam then runs horizontally (layers along it,
never across) and the pins point straight up.

All dimensions in mm; clip and pin values approved 2026-10-24.
"""

import math
import os
import sys
from dataclasses import dataclass

import FreeCAD as App

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cadlib import add_box, add_cylinder, cut, export_part, fuse, run_as_script  # noqa: E402

DOC_NAME = "snap_clip"


@dataclass(frozen=True)
class SnapDims:
    # Cover wall
    wall: float = 1.2               # 3 perimeters with a 0.4 mm nozzle

    # Clip beam (horizontal, in the wall plane) and hook
    beam_len: float = 8.0
    beam_w: float = 4.0             # along Z
    hook_h: float = 0.6             # protrusion into the skeleton pocket
    hook_len: float = 2.0           # along X, at the free end of the beam
    entry_deg: float = 30.0         # lower face, met first while pushing the cover down
    retention_deg: float = 60.0     # upper face, holds the cover; 90 would never let go
    slot_gap: float = 0.5           # cut around the beam so it can bend
    pocket_clearance: float = 0.2   # around the hook inside the skeleton pocket

    # Locating pins (vertical, along the push direction)
    pin_d: float = 3.0
    hole_d: float = 3.3
    pin_len: float = 3.0
    pin_chamfer: float = 0.5

    # Coupon layout
    coupon_len: float = 26.0        # along X
    wall_h: float = 12.0            # cover wall below the top face
    flange_depth: float = 6.0       # flange reach over the skeleton top face (+Y)
    beam_x0: float = 3.0            # beam root
    beam_zc: float = -6.0           # beam centre height
    pin_xs: tuple = (16.0, 22.0)
    pin_y: float = 3.0

    @property
    def pocket_depth(self) -> float:
        """Depth of the skeleton pocket = hook + clearance (the 0.8 mm in docs/capas.md)."""
        return self.hook_h + self.pocket_clearance

    @property
    def entry_run(self) -> float:
        """Height (Z) of the entry ramp."""
        return self.hook_h / math.tan(math.radians(self.entry_deg))

    @property
    def retention_run(self) -> float:
        """Height (Z) of the retention face."""
        return self.hook_h / math.tan(math.radians(self.retention_deg))

    @property
    def hook_x(self) -> tuple[float, float]:
        end = self.beam_x0 + self.beam_len
        return end - self.hook_len, end

    @property
    def hook_z(self) -> tuple[float, float]:
        return self.beam_zc - self.beam_w / 2, self.beam_zc + self.beam_w / 2

    @property
    def strain_pct(self) -> float:
        """Peak strain of a rectangular cantilever bent by the hook height: 1.5 t y / L²."""
        return 100 * 1.5 * self.wall * self.hook_h / self.beam_len ** 2


DIMS = SnapDims()


def _hook(doc, d: SnapDims):
    """Trapezoid in the YZ plane (entry ramp below, retention face above), extruded along X."""
    (x0, x1), (z0, z1) = d.hook_x, d.hook_z
    w = doc.addObject("Part::Wedge", "Hook")
    w.Xmin, w.Xmax, w.X2min, w.X2max = x0, x1, x0, x1
    w.Ymin, w.Ymax = 0.0, d.hook_h
    w.Zmin, w.Zmax = z0, z1
    w.Z2min, w.Z2max = z0 + d.entry_run, z1 - d.retention_run
    return w


def _pin(doc, name: str, d: SnapDims, x: float, y: float):
    body = add_cylinder(doc, f"{name}Body", d.pin_d, d.pin_len - d.pin_chamfer, x, y, -(d.pin_len - d.pin_chamfer))
    tip = doc.addObject("Part::Cone", f"{name}Tip")
    tip.Radius1, tip.Radius2, tip.Height = d.pin_d / 2 - d.pin_chamfer, d.pin_d / 2, d.pin_chamfer
    tip.Placement.Base = App.Vector(x, y, -d.pin_len)
    return fuse(doc, name, [body, tip])


def build(doc, d: SnapDims = DIMS):
    """Cover coupon: wall with the clip, flange on top, two pins under the flange."""
    wall = add_box(doc, "Wall", d.coupon_len, d.wall, d.wall_h, 0, -d.wall, -d.wall_h)
    flange = add_box(doc, "Flange", d.coupon_len, d.wall + d.flange_depth, d.wall, 0, -d.wall, 0)
    (z0, z1) = d.hook_z
    slot = add_box(doc, "ClipSlot", d.beam_len + d.slot_gap, d.wall + 2, d.beam_w + 2 * d.slot_gap,
                   d.beam_x0, -d.wall - 1, z0 - d.slot_gap)
    beam = add_box(doc, "Beam", d.beam_len, d.wall, d.beam_w, d.beam_x0, -d.wall, z0)
    wall_cut = cut(doc, "WallSlotted", wall, slot)
    pins = [_pin(doc, f"Pin{i}", d, x, d.pin_y) for i, x in enumerate(d.pin_xs)]
    return fuse(doc, "CoverCoupon", [wall_cut, flange, beam, _hook(doc, d), *pins])


def main():
    doc = App.newDocument(DOC_NAME)
    export_part(doc, build(doc), DOC_NAME)
    print(f"[{DOC_NAME}] clip strain {DIMS.strain_pct:.2f} % (target < 2 %), "
          f"pocket depth {DIMS.pocket_depth:.1f} mm")


if run_as_script(__name__, DOC_NAME):
    main()
