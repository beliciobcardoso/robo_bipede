"""Export the solid of a FreeCAD document to a fine binary STL (read-only on the source).

Run with FreeCADCmd; arguments come from env vars because FreeCADCmd eats argv:
    SRC=<file.FCStd>  OBJ=<object name, or "Body" for the first PartDesign body>  OUT=<file.stl>
"""

import os

import FreeCAD as App
import MeshPart

LINEAR_DEFLECTION = 0.005   # mm, max chord error
ANGULAR_DEFLECTION = 0.05   # rad

src, obj_name, out = os.environ["SRC"], os.environ["OBJ"], os.environ["OUT"]
doc = App.openDocument(src)   # never saved: the source file stays untouched
if obj_name == "Body":
    obj = next(o for o in doc.Objects if o.TypeId == "PartDesign::Body")
else:
    obj = doc.getObject(obj_name)
shape = obj.Shape
mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=LINEAR_DEFLECTION,
                              AngularDeflection=ANGULAR_DEFLECTION, Relative=False)
mesh.write(out)
print(f"[export_stl] {obj.Label}: solid vol={shape.Volume:.2f} mesh vol={mesh.Volume:.2f} "
      f"triangles={mesh.CountFacets} closed={mesh.isSolid()} -> {out}")
App.closeDocument(doc.Name)
