"""Micro servo SG90 / MG90S — functional reference model.

Used as a placeholder in assemblies and as the source of dimensions for
brackets (servo pocket, mounting holes, horn clearance). Not meant to be printed.

Coordinate system (shared by every part that mounts this servo):
    origin  = output shaft axis, on the UNDERSIDE of the mounting tabs (seat plane)
    +Z      = towards the output shaft
    +X      = along the body length, from the shaft end towards the far end
    Y       = across the body width (symmetric)

All dimensions in mm. Values marked "measure" vary between SG90/MG90S clones —
check them with a caliper on the servo in hand and update here.
"""

import os
from dataclasses import dataclass

import FreeCAD as App
import Import
import Part

DOC_NAME = "servo_sg90"
DEFAULT_OUT_DIR = "cad/build"


@dataclass(frozen=True)
class ServoDims:
    # Main case
    body_l: float = 22.8          # measure
    body_w: float = 12.2          # measure
    body_h: float = 22.7          # bottom to top face of the case (no gear tower)
    shaft_offset: float = 6.1     # shaft-side end face to shaft axis (measure)

    # Mounting tabs
    tab_l_total: float = 32.2     # tip to tip (measure)
    tab_t: float = 2.5            # thickness
    tab_bottom_z: float = 15.9    # case bottom to tab underside (measure)
    hole_spacing: float = 27.8    # center to center (measure)
    hole_d: float = 2.0           # M2 self-tapping screw

    # Gear tower (top of case)
    tower_d: float = 11.8
    tower_h: float = 4.0
    bump_d: float = 5.0           # secondary gear bump next to the tower
    bump_x: float = 5.6           # shaft axis to bump axis
    bump_h: float = 3.5

    # Output shaft (spline modelled as plain cylinder; real one is ~20-21T)
    shaft_d: float = 4.8
    shaft_h: float = 3.0          # above tower top (measure)
    shaft_screw_d: float = 1.6
    shaft_screw_depth: float = 3.0

    # Cable exit: stub on the end face opposite the shaft (confirm side)
    cable_w: float = 3.6
    cable_t: float = 1.2
    cable_len: float = 5.0
    cable_z: float = 4.5          # case bottom to cable centre (measure)

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


def _add_box(doc, name, l, w, h, x, y, z):
    obj = doc.addObject("Part::Box", name)
    obj.Length, obj.Width, obj.Height = l, w, h
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def _add_cylinder(doc, name, d, h, x, y, z):
    obj = doc.addObject("Part::Cylinder", name)
    obj.Radius, obj.Height = d / 2, h
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def _fuse(doc, name, shapes):
    obj = doc.addObject("Part::MultiFuse", name)
    obj.Shapes = shapes
    obj.Refine = True
    return obj


def build(doc, d: ServoDims = DIMS):
    """Create the servo as a parametric CSG tree; returns the final object."""
    body = _add_box(doc, "Body", d.body_l, d.body_w, d.body_h,
                    d.body_x0, -d.body_w / 2, d.body_z0)

    tabs = _add_box(doc, "Tabs", d.tab_l_total, d.body_w, d.tab_t,
                    d.body_center_x - d.tab_l_total / 2, -d.body_w / 2, 0)
    holes = [
        _add_cylinder(doc, f"TabHole{i}", d.hole_d, d.tab_t + 2, p.x, p.y, -1)
        for i, p in enumerate(d.hole_positions)
    ]
    tabs_drilled = doc.addObject("Part::Cut", "TabsDrilled")
    tabs_drilled.Base = tabs
    tabs_drilled.Tool = _fuse(doc, "TabHoles", holes)

    tower = _add_cylinder(doc, "Tower", d.tower_d, d.tower_h, 0, 0, d.body_top_z)
    bump = _add_cylinder(doc, "GearBump", d.bump_d, d.bump_h, d.bump_x, 0, d.body_top_z)

    shaft = _add_cylinder(doc, "Shaft", d.shaft_d, d.shaft_h, 0, 0, d.tower_top_z)
    shaft_screw = _add_cylinder(doc, "ShaftScrewHole", d.shaft_screw_d, d.shaft_screw_depth + 1,
                                0, 0, d.shaft_top_z - d.shaft_screw_depth)
    shaft_drilled = doc.addObject("Part::Cut", "ShaftDrilled")
    shaft_drilled.Base = shaft
    shaft_drilled.Tool = shaft_screw

    cable = _add_box(doc, "CableStub", d.cable_len, d.cable_w, d.cable_t,
                     d.body_x0 + d.body_l, -d.cable_w / 2,
                     d.body_z0 + d.cable_z - d.cable_t / 2)

    servo = _fuse(doc, "ServoSG90", [body, tabs_drilled, tower, bump, shaft_drilled, cable])
    doc.recompute()
    return servo


def _validate(obj):
    shape = obj.Shape
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
        raise RuntimeError(f"{obj.Name}: invalid shape (solids={len(shape.Solids)})")


def main():
    out_dir = os.environ.get("CAD_OUT_DIR", DEFAULT_OUT_DIR)
    os.makedirs(out_dir, exist_ok=True)

    doc = App.newDocument(DOC_NAME)
    servo = build(doc)
    _validate(servo)

    fcstd_path = os.path.join(out_dir, f"{DOC_NAME}.FCStd")
    step_path = os.path.join(out_dir, f"{DOC_NAME}.step")
    if os.path.exists(fcstd_path):
        os.remove(fcstd_path)  # avoid FreeCAD piling up .FCBak backups on every build
    doc.saveAs(os.path.abspath(fcstd_path))
    Import.export([servo], os.path.abspath(step_path))

    bb = servo.Shape.BoundBox
    print(f"[{DOC_NAME}] volume={servo.Shape.Volume:.1f} mm3 "
          f"bbox x[{bb.XMin:.1f},{bb.XMax:.1f}] y[{bb.YMin:.1f},{bb.YMax:.1f}] "
          f"z[{bb.ZMin:.1f},{bb.ZMax:.1f}]")
    print(f"[{DOC_NAME}] saved {fcstd_path}, {step_path}")


# FreeCADCmd runs a script file with __name__ == its module name, not "__main__"
if __name__ in ("__main__", DOC_NAME):
    main()
