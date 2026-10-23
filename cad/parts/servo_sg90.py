"""Micro servo SG90 (clone) — functional reference model.

Used as a placeholder in assemblies and as the source of dimensions for
brackets (servo pocket, mounting holes, horn clearance). Not meant to be printed.

Coordinate system (shared by every part that mounts this servo):
    origin  = output shaft axis, on the UNDERSIDE of the mounting tabs (seat plane)
    +Z      = towards the output shaft
    +X      = along the body length, from the shaft end towards the far end
    Y       = across the body width (symmetric)

All dimensions in mm, measured with a caliper on the servo in hand
(see docs/medidas_servo_sg90.md). Values marked "nominal" were not measured.
"""

import os
import sys
from dataclasses import dataclass

import FreeCAD as App

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cadlib import add_box, add_cylinder, cut, export_part, fuse  # noqa: E402

DOC_NAME = "servo_sg90"


@dataclass(frozen=True)
class ServoDims:
    # Main case
    body_l: float = 23.1
    body_w: float = 12.2
    body_h: float = 24.2          # bottom to top face of the case (no gear tower)

    # Mounting tabs (one centred hole per tab)
    tab_l_total: float = 32.5     # tip to tip
    tab_t: float = 2.5
    tab_bottom_z: float = 17.0    # case bottom to tab underside
    hole_spacing: float = 27.8    # center to center
    hole_d: float = 2.0           # M2 self-tapping screw

    # Gear tower (top of case), flush with the shaft-side wall
    tower_d: float = 12.0
    tower_h: float = 4.0
    bump_d: float = 5.0           # secondary gear bump next to the tower (nominal)
    bump_x: float = 5.6           # shaft axis to bump axis (nominal)
    bump_h: float = 3.5           # nominal

    # Output shaft (spline modelled as plain cylinder over the teeth)
    shaft_d: float = 5.0
    shaft_h: float = 3.0          # above tower top
    spline_teeth: int = 21
    shaft_screw_d: float = 1.6    # nominal
    shaft_screw_depth: float = 3.0  # nominal

    # Cable exit: stub on the shaft-side end face
    cable_w: float = 4.0
    cable_t: float = 1.2          # nominal
    cable_len: float = 5.0        # keep-out length, not the real cable
    cable_z: float = 4.0          # case bottom to cable centre

    @property
    def shaft_offset(self) -> float:
        """Shaft-side end face to shaft axis (tower is flush with that face)."""
        return self.tower_d / 2

    @property
    def body_x0(self) -> float:
        return -self.shaft_offset

    @property
    def body_z0(self) -> float:
        return -self.tab_bottom_z

    @property
    def body_top_z(self) -> float:
        return self.body_z0 + self.body_h

    @property
    def tower_top_z(self) -> float:
        return self.body_top_z + self.tower_h

    @property
    def shaft_top_z(self) -> float:
        return self.tower_top_z + self.shaft_h

    @property
    def body_center_x(self) -> float:
        return self.body_x0 + self.body_l / 2

    @property
    def hole_positions(self) -> tuple[App.Vector, App.Vector]:
        half = self.hole_spacing / 2
        return (
            App.Vector(self.body_center_x - half, 0, 0),
            App.Vector(self.body_center_x + half, 0, 0),
        )


DIMS = ServoDims()


def build(doc, d: ServoDims = DIMS):
    """Create the servo as a parametric CSG tree; returns the final object."""
    body = add_box(doc, "Body", d.body_l, d.body_w, d.body_h,
                   d.body_x0, -d.body_w / 2, d.body_z0)

    tabs = add_box(doc, "Tabs", d.tab_l_total, d.body_w, d.tab_t,
                   d.body_center_x - d.tab_l_total / 2, -d.body_w / 2, 0)
    holes = [
        add_cylinder(doc, f"TabHole{i}", d.hole_d, d.tab_t + 2, p.x, p.y, -1)
        for i, p in enumerate(d.hole_positions)
    ]
    tabs_drilled = cut(doc, "TabsDrilled", tabs, fuse(doc, "TabHoles", holes))

    tower = add_cylinder(doc, "Tower", d.tower_d, d.tower_h, 0, 0, d.body_top_z)
    bump = add_cylinder(doc, "GearBump", d.bump_d, d.bump_h, d.bump_x, 0, d.body_top_z)

    shaft = add_cylinder(doc, "Shaft", d.shaft_d, d.shaft_h, 0, 0, d.tower_top_z)
    shaft_screw = add_cylinder(doc, "ShaftScrewHole", d.shaft_screw_d, d.shaft_screw_depth + 1,
                               0, 0, d.shaft_top_z - d.shaft_screw_depth)
    shaft_drilled = cut(doc, "ShaftDrilled", shaft, shaft_screw)

    cable = add_box(doc, "CableStub", d.cable_len, d.cable_w, d.cable_t,
                    d.body_x0 - d.cable_len, -d.cable_w / 2,
                    d.body_z0 + d.cable_z - d.cable_t / 2)

    return fuse(doc, "ServoSG90", [body, tabs_drilled, tower, bump, shaft_drilled, cable])


def main():
    doc = App.newDocument(DOC_NAME)
    export_part(doc, build(doc), DOC_NAME)


# FreeCADCmd runs a script file with __name__ == its module name, not "__main__"
if __name__ in ("__main__", DOC_NAME):
    main()
