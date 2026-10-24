"""Deep groove ball bearing 623ZZ (3x10x4, double metal shield) — reference model.

Used as the passive pivot opposite each servo shaft: a printed housing holds the
outer ring, an M3 screw through the bore is the joint pin.

Coordinate system:
    origin  = bearing axis, on one side face
    +Z      = along the axis, other face at z = width

All dimensions in mm. d, D, B are ISO 15 standard (tolerances in the hundredths);
the rest are catalogue values, marked "nominal".
"""

import os
import sys
from dataclasses import dataclass

import FreeCAD as App

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cadlib import add_tube, export_part, fuse, run_as_script  # noqa: E402

DOC_NAME = "bearing_623zz"


@dataclass(frozen=True)
class BearingDims:
    bore_d: float = 3.0           # d
    outer_d: float = 10.0         # D
    width: float = 4.0            # B

    # Ring lands visible around the shields (nominal)
    inner_land_d: float = 5.2     # inner ring OD (d1)
    outer_land_d: float = 8.2     # outer ring ID at the shield (D2)
    shield_recess: float = 0.2    # shield sits below the ring faces

    # Design limits for parts touching the bearing (nominal)
    abutment_inner_min_d: float = 4.2   # da min: shaft shoulder / spacer must reach this
    abutment_outer_max_d: float = 8.8   # Da max: housing shoulder must not go below this


DIMS = BearingDims()


def build(doc, d: BearingDims = DIMS):
    """Create the bearing as a parametric CSG tree; returns the final object."""
    outer_ring = add_tube(doc, "OuterRing", d.outer_d, d.outer_land_d, d.width, 0, 0, 0)
    inner_ring = add_tube(doc, "InnerRing", d.inner_land_d, d.bore_d, d.width, 0, 0, 0)
    shields = add_tube(doc, "Shields", d.outer_land_d, d.inner_land_d,
                       d.width - 2 * d.shield_recess, 0, 0, d.shield_recess)
    return fuse(doc, "Bearing623ZZ", [outer_ring, inner_ring, shields])


def main():
    doc = App.newDocument(DOC_NAME)
    export_part(doc, build(doc), DOC_NAME)


if run_as_script(__name__, DOC_NAME):
    main()
