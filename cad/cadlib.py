"""Shared helpers for part scripts: CSG primitives as document objects + export.

Part scripts put the `cad/` directory on sys.path (FreeCADCmd does not add the
script's directory) and import from here.
"""

import os
import sys

import FreeCAD as App
import Import

DEFAULT_OUT_DIR = "cad/build"


def add_box(doc, name, l, w, h, x, y, z):
    obj = doc.addObject("Part::Box", name)
    obj.Length, obj.Width, obj.Height = l, w, h
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def add_cylinder(doc, name, d, h, x, y, z):
    obj = doc.addObject("Part::Cylinder", name)
    obj.Radius, obj.Height = d / 2, h
    obj.Placement.Base = App.Vector(x, y, z)
    return obj


def add_tube(doc, name, od, id_, h, x, y, z):
    """Hollow cylinder along +Z; the bore overshoots so the cut is clean."""
    outer = add_cylinder(doc, f"{name}Outer", od, h, x, y, z)
    bore = add_cylinder(doc, f"{name}Bore", id_, h + 2, x, y, z - 1)
    return cut(doc, name, outer, bore)


def cut(doc, name, base, tool):
    obj = doc.addObject("Part::Cut", name)
    obj.Base, obj.Tool = base, tool
    return obj


def fuse(doc, name, shapes):
    obj = doc.addObject("Part::MultiFuse", name)
    obj.Shapes = shapes
    obj.Refine = True
    return obj


def _validate(obj):
    shape = obj.Shape
    if shape.isNull() or not shape.isValid() or len(shape.Solids) != 1:
        raise RuntimeError(f"{obj.Name}: invalid shape (solids={len(shape.Solids)})")


def export_part(doc, obj, part_name):
    """Validate `obj` and write <part_name>.FCStd + .step to $CAD_OUT_DIR."""
    doc.recompute()
    _validate(obj)

    out_dir = os.environ.get("CAD_OUT_DIR", DEFAULT_OUT_DIR)
    os.makedirs(out_dir, exist_ok=True)
    fcstd_path = os.path.abspath(os.path.join(out_dir, f"{part_name}.FCStd"))
    step_path = os.path.abspath(os.path.join(out_dir, f"{part_name}.step"))

    if os.path.exists(fcstd_path):
        os.remove(fcstd_path)  # avoid FreeCAD piling up .FCBak backups on every build
    doc.saveAs(fcstd_path)
    Import.export([obj], step_path)

    bb = obj.Shape.BoundBox
    print(f"[{part_name}] volume={obj.Shape.Volume:.1f} mm3 "
          f"bbox x[{bb.XMin:.1f},{bb.XMax:.1f}] y[{bb.YMin:.1f},{bb.YMax:.1f}] "
          f"z[{bb.ZMin:.1f},{bb.ZMax:.1f}]")
    print(f"[{part_name}] saved {os.path.relpath(fcstd_path)}, {os.path.relpath(step_path)}")


def run_as_script(module_name: str, part_name: str) -> bool:
    """True when this part script is the one FreeCADCmd was asked to run, not just imported.

    FreeCADCmd runs a script with __name__ == its module name, which is also what an import gives,
    so the script path in sys.argv tells the two apart."""
    if module_name == "__main__":
        return True
    return module_name == part_name and os.path.basename(sys.argv[-1]) == f"{part_name}.py"
