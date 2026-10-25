"""Generate the F1 biped model (sim/models/f1_biped.xml) from the body parameters (sim/tools/body.py).

    .venv/bin/python sim/tools/build_biped.py            # write sim/models/f1_biped.xml
    .venv/bin/python sim/tools/build_biped.py --preview  # also the 3D preview model
    from build_biped import BipedParams, build_xml       # sweeps build variants in memory

Whole robot made of simple shapes with the estimated masses placed where the real parts will be:
torso (battery, ESP32, MPU-6050 board, UBEC, frame, torso cover), two legs with 4 joints each
(hip pitch, knee, ankle pitch, ankle roll), a head fixed to the torso (HC-SR04 + camera reserve)
and two arms with 2 joints each (shoulder pitch, shoulder roll). Each servo is a box with its
model's mass at its joint, carried by the segment that holds its body; its actuator gets that
model's stall torque and speed. Joint range = mechanical stop, actuator ctrlrange = software
limit 5° inside it (docs/arquitetura_perna.md).

Input dimensions are in mm and g (like the CAD); the MJCF is written in m and kg.
Contacts: only feet, torso and floor collide (leg-to-leg contact is ignored in F1).
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import body  # noqa: E402
from body import (ARM_STOPS, ELBOW_STACK_CENTRE_MM, JOINT_STOPS, SERVO_HALF_MM, SERVOS,  # noqa: E402,F401
                  SHOULDER_ROLL_STACK_X_MM, SOFT_MARGIN_DEG, WRIST_HOLDER_X_MM, BipedParams, shells)

OUT = Path(__file__).resolve().parents[1] / "models" / "f1_biped.xml"
PREVIEW_OUT = OUT.with_name("preview_biped.xml")
PREVIEW_ASSETS = """
    <mesh name="servo_sg90" file="servo_sg90.stl" scale="0.001 0.001 0.001"/>
    <mesh name="bearing_623zz" file="bearing_623zz.stl" scale="0.001 0.001 0.001"/>
    <material name="servo_pv" rgba="0.2 0.35 0.85 1"/>
    <material name="holder" rgba="0.9 0.9 0.92 0.45"/>
    <material name="yoke" rgba="0.55 0.6 0.65 1"/>
    <material name="horn" rgba="0.97 0.97 0.97 1"/>
    <material name="bearing" rgba="0.75 0.75 0.78 1"/>
    <material name="battery" rgba="0.15 0.55 0.3 1"/>
    <material name="board" rgba="0.1 0.3 0.15 1"/>
    <material name="visor" rgba="0.12 0.13 0.16 1" specular="0.6" shininess="0.8"/>"""
COVER_RGBA = "0.95 0.95 0.94 1"     # printed covers in the preview (white PETG)


def _m(mm: float) -> str:
    return f"{mm / 1000:.5f}"


def _v(*mm: float) -> str:
    return " ".join(_m(x) for x in mm)


def _kg(g: float) -> str:
    return f"{g / 1000:.5f}"


def _servo_geom(name: str, mass_g: float, z_mm: float, y_mm: float = 0.0, x_mm: float = 0.0) -> str:
    hx, hy, hz = SERVO_HALF_MM
    return (f'<geom name="{name}" type="box" size="{_v(hx, hy, hz)}" pos="{_v(x_mm, y_mm, z_mm)}" '
            f'mass="{_kg(mass_g)}" material="servo" class="visual"/>')


def _hidden(geom: str, preview: bool) -> str:
    """Mass boxes stay in the preview (same physics as F1) but are drawn invisible."""
    return geom.replace("/>", ' rgba="0 0 0 0"/>') if preview else geom


# ---------------------------------------------------------------- preview (visual only)
# Servo frame (cad/parts/servo_sg90.py): origin on the shaft axis at the tab underside, +Z toward
# the shaft, +X along the body. Each joint's servo frame is given by its axes in the robot frame
# and placed so the middle of the horn+servo+bearing stack (servo z = -3 mm) sits on the joint point.
STACK_CENTRE_MM = -3.0
# Bracket concept (docs/suporte_servo.md), in the servo frame: (centre xyz, half sizes xyz), mm
HOLDER_BOX = ((9.0, 0.0, -8.25), (17.0, 8.1, 10.75))
HORN_BOX = ((6.0, 0.0, 15.25), (8.0, 2.5, 0.75))
YOKE_BOXES = (((-12.75, 0.0, -3.25), (1.25, 8.0, 21.25)),    # base, beyond the shaft-side end
              ((-4.25, 0.0, 16.75), (9.75, 6.0, 1.25)),      # arm on the horn
              ((-4.25, 0.0, -22.0), (9.75, 6.0, 2.5)))       # arm with the bearing, 0.5 mm spacer gap
BEARING_Z_MM = -23.5           # 4 mm bearing face at -19.5: holder floor -19 + 0.5 mm spacer
HORN_TOP_MM = HORN_BOX[0][2] + HORN_BOX[1][2]
SHOULDER_HORN_OUT_MM = 1.0     # shoulder pitch horn top beyond the torso frame side wall


def _servo_axes(joint: str, sign: int):
    """(xs, ys, zs) of the joint's servo frame in the robot frame."""
    if joint == "ankle_roll":                       # shaft forward, body toward the inside
        xs, zs = (0, -sign, 0), (1, 0, 0)
    elif joint == "shoulder_roll":                  # shaft forward, body down inside the upper arm
        xs, zs = (0, 0, -1), (1, 0, 0)
    elif joint in ("shoulder_pitch", "elbow"):      # shaft outward, body down
        xs, zs = (0, 0, -1), (0, sign, 0)
    elif joint == "wrist":                          # shaft up along the forearm, body front-back in the hand
        xs, zs = (1, 0, 0), (0, 0, 1)
    else:                                           # leg pitch: shaft outward, body up
        xs, zs = (0, 0, 1), (0, sign, 0)
    ys = (zs[1] * xs[2] - zs[2] * xs[1], zs[2] * xs[0] - zs[0] * xs[2], zs[0] * xs[1] - zs[1] * xs[0])
    return xs, ys, zs


def _quat(xs, ys, zs) -> str:
    """Quaternion (w x y z) of the rotation whose columns are xs, ys, zs."""
    m = [[xs[i], ys[i], zs[i]] for i in range(3)]
    tr = m[0][0] + m[1][1] + m[2][2]
    if tr > 0:
        w = math.sqrt(1 + tr) / 2
        q = (w, (m[2][1] - m[1][2]) / (4 * w), (m[0][2] - m[2][0]) / (4 * w), (m[1][0] - m[0][1]) / (4 * w))
    else:
        i = max(range(3), key=lambda k: m[k][k])
        j, k = (i + 1) % 3, (i + 2) % 3
        r = math.sqrt(1 + m[i][i] - m[j][j] - m[k][k])
        q = [0.0] * 4
        q[0] = (m[k][j] - m[j][k]) / (2 * r)
        q[1 + i] = r / 2
        q[1 + j] = (m[j][i] + m[i][j]) / (2 * r)
        q[1 + k] = (m[k][i] + m[i][k]) / (2 * r)
    return " ".join(f"{c:.6f}" for c in q)


def _shoulder_pitch_axes(p: BipedParams, sign: int):
    """Shoulder pitch servo frame: shaft outward, body toward BipedParams.shoulder_pitch_body."""
    xs = {"down": (0, 0, -1), "back": (-1, 0, 0), "front": (1, 0, 0)}[p.shoulder_pitch_body]
    zs = (0, sign, 0)
    ys = (zs[1] * xs[2] - zs[2] * xs[1], zs[2] * xs[0] - zs[0] * xs[2], zs[0] * xs[1] - zs[1] * xs[0])
    return xs, ys, zs


def _place(joint: str, sign: int, at_mm, local_mm, axes=None):
    """Body-frame position (mm) of a point given in the joint's servo frame."""
    xs, ys, zs = axes or _servo_axes(joint, sign)
    o = [at_mm[i] - STACK_CENTRE_MM * zs[i] for i in range(3)]
    return [o[i] + xs[i] * local_mm[0] + ys[i] * local_mm[1] + zs[i] * local_mm[2] for i in range(3)]


def _vis(name, joint, sign, at_mm, centre, half=None, mesh=None, material="link", axes=None) -> str:
    q = _quat(*(axes or _servo_axes(joint, sign)))
    pos = _v(*_place(joint, sign, at_mm, centre, axes))
    shape = f'type="mesh" mesh="{mesh}"' if mesh else f'type="box" size="{_v(*half)}"'
    return f'<geom name="{name}" {shape} pos="{pos}" quat="{q}" mass="0" material="{material}" class="visual"/>'


def _servo_side(joint: str, sign: int, at_mm, s: str, axes=None) -> str:
    """Parent-body visuals of a joint: the servo and its holder."""
    return (_vis(f"pv_servo_{joint}{s}", joint, sign, at_mm, (0, 0, 0), mesh="servo_sg90", material="servo_pv", axes=axes)
            + _vis(f"pv_holder_{joint}{s}", joint, sign, at_mm, *HOLDER_BOX, material="holder", axes=axes))


def _yoke_side(joint: str, sign: int, s: str, at=(0, 0, 0), bearing: bool = True) -> str:
    """Visuals of a joint's output side: horn, yoke and (unless bearing=False) the 623ZZ side."""
    out = [_vis(f"pv_horn_{joint}{s}", joint, sign, at, *HORN_BOX, material="horn")]
    boxes = YOKE_BOXES
    if bearing:
        out.append(_vis(f"pv_bearing_{joint}{s}", joint, sign, at, (0, 0, BEARING_Z_MM), mesh="bearing_623zz", material="bearing"))
    else:                                    # base shortened to the horn side, no bearing arm
        (bc, bh) = YOKE_BOXES[0]
        lo, hi = ELBOW_STACK_CENTRE_MM * 2 - (YOKE_BOXES[1][0][2] + YOKE_BOXES[1][1][2]), YOKE_BOXES[1][0][2] + YOKE_BOXES[1][1][2]
        boxes = (((bc[0], bc[1], (lo + hi) / 2), (bh[0], bh[1], (hi - lo) / 2)), YOKE_BOXES[1])
    out += [_vis(f"pv_yoke{i}_{joint}{s}", joint, sign, at, c, h, material="yoke") for i, (c, h) in enumerate(boxes)]
    return "".join(out)


def _cover(name: str, mesh: str, pos_mm) -> str:
    return (f'<geom name="cv_{name}" type="mesh" mesh="cv_{mesh}" pos="{_v(*pos_mm)}" mass="0" '
            f'rgba="{COVER_RGBA}" class="visual"/>')


def _cover_assets(p: BipedParams) -> str:
    return "".join(f'\n    <mesh name="cv_{n}" vertex="{" ".join(_v(*pt) for pt in sh.vertices_mm())}"/>'
                   for n, sh in shells(p).items())


PART_RGBA = {"bateria": "0.15 0.55 0.3 1", "ubec": "0.75 0.2 0.2 1", "pca9685": "0.15 0.25 0.6 1",
             "controle": "0.1 0.3 0.15 1", "distribuicao": "0.55 0.45 0.1 1", "chave": "0.2 0.2 0.2 1",
             "mpu6050": "0.6 0.1 0.6 1"}
ENVELOPE_RGBA = "1 0.85 0.3 0.25"   # kept free for plugs, wires, USB


def _torso_parts_preview() -> list:
    """Boxes of the torso contents at their body.TORSO_LAYOUT places, plus their keep-free envelopes."""
    import numpy as np
    out = []
    for name, (centre, rot) in body.TORSO_LAYOUT.items():
        part, rot = body.TORSO_PARTS[name], np.array(rot)
        half = np.abs(rot @ np.array(part.size_mm)) / 2
        out.append(f'<geom name="pv_part_{name}" type="box" size="{_v(*half)}" pos="{_v(*centre)}" mass="0" '
                   f'rgba="{PART_RGBA.get(name, "0.3 0.3 0.3 1")}" class="visual"/>')
        for k, (c, h) in enumerate(part.envelopes):
            pos = np.array(centre) + rot @ np.array(c)
            out.append(f'<geom name="pv_part_{name}_env{k}" type="box" size="{_v(*np.abs(rot @ np.array(h)))}" '
                       f'pos="{_v(*pos)}" mass="0" rgba="{ENVELOPE_RGBA}" class="visual"/>')
    return out


def _torso_preview(p: BipedParams) -> str:
    tx, ty, tz = p.torso_size_mm
    out = [_cover("torso", "torso", shells(p)["torso"].pos_mm)]
    out += _torso_parts_preview()
    hip = -tz / 2 - p.hip_drop_mm
    for side, sign in (("l", +1), ("r", -1)):
        out.append(_servo_side("hip_pitch", sign, (0, sign * p.hip_half_width_mm, hip), f"_{side}"))
    return "\n      ".join(out)


def _leg(p: BipedParams, side: str, sign: int, preview: bool = False) -> str:
    c = p.covers_g
    fx, fy, fz = p.foot_size_mm
    s = f"_{side}"
    hide = ' rgba="0 0 0 0"' if preview else ""
    pv = dict(thigh="", shin="", ankle="", foot="")
    if preview:
        sh = shells(p)
        pv["thigh"] = (_yoke_side("hip_pitch", sign, s) + _servo_side("knee", sign, (0, 0, -p.thigh_mm), s)
                       + _cover(f"thigh{s}", "thigh", sh["thigh"].pos_mm))
        pv["shin"] = (_yoke_side("knee", sign, s) + _servo_side("ankle_pitch", sign, (0, 0, -p.shin_mm), s)
                      + _cover(f"shin{s}", "shin", sh["shin"].pos_mm))
        pv["ankle"] = (_yoke_side("ankle_pitch", sign, s) + _servo_side("ankle_roll", sign, (0, 0, -p.ankle_link_mm), s)
                       + _cover(f"ankle{s}", "ankle", sh["ankle"].pos_mm))
        pv["foot"] = _yoke_side("ankle_roll", sign, s)
    knee_g, ankle_pitch_g, ankle_roll_g = (p.servo(j).mass_g for j in ("knee", "ankle_pitch", "ankle_roll"))
    return f"""
      <body name="thigh{s}" pos="{_v(0, sign * p.hip_half_width_mm, -p.torso_size_mm[2] / 2 - p.hip_drop_mm)}">
        <joint name="hip_pitch{s}" class="hip_pitch"/>
        <geom name="thigh{s}" type="box" size="{_v(7, p.leg_width_mm / 2, p.thigh_mm / 2)}" pos="{_v(0, 0, -p.thigh_mm / 2)}" mass="{_kg(p.thigh_struct_g + c["thigh"])}" material="link" class="visual"{hide}/>
        {_hidden(_servo_geom(f"servo_knee{s}", knee_g, -p.thigh_mm + SERVO_HALF_MM[2] - 4), preview)}
        {pv["thigh"]}
        <body name="shin{s}" pos="{_v(0, 0, -p.thigh_mm)}">
          <joint name="knee{s}" class="knee"/>
          <geom name="shin{s}" type="box" size="{_v(7, p.leg_width_mm / 2, p.shin_mm / 2)}" pos="{_v(0, 0, -p.shin_mm / 2)}" mass="{_kg(p.shin_struct_g + c["shin"])}" material="link" class="visual"{hide}/>
          {_hidden(_servo_geom(f"servo_ankle_pitch{s}", ankle_pitch_g, -p.shin_mm + SERVO_HALF_MM[2] - 4), preview)}
          {pv["shin"]}
          <body name="ankle{s}" pos="{_v(0, 0, -p.shin_mm)}">
            <joint name="ankle_pitch{s}" class="ankle_pitch"/>
            <geom name="ankle{s}" type="box" size="{_v(10, 8, p.ankle_link_mm / 2)}" pos="{_v(0, 0, -p.ankle_link_mm / 2)}" mass="{_kg(p.ankle_struct_g + ankle_roll_g + c["ankle"])}" material="servo" class="visual"{hide}/>
            {pv["ankle"]}
            <body name="foot{s}" pos="{_v(0, 0, -p.ankle_link_mm)}">
              <joint name="ankle_roll{s}" class="ankle_roll"/>
              <geom name="foot{s}" type="box" size="{_v(fx / 2, fy / 2, fz / 2)}" pos="{_v(0, 0, -p.roll_to_sole_mm + fz / 2)}" mass="{_kg(p.foot_struct_g)}" material="link" class="contact"/>
              <site name="sole{s}" pos="{_v(0, 0, -p.roll_to_sole_mm)}" size="0.002"/>
              {pv["foot"]}
            </body>
          </body>
        </body>
      </body>"""


# Arm concept (provisional, no bracket designed yet): the shoulder pitch servo sits inside the top
# of the torso frame with its horn just outside the side wall, body lying toward
# BipedParams.shoulder_pitch_body; a shoulder link on the horn carries the shoulder roll servo
# (holder + yoke, like a leg joint) out to the arm plane. No yoke or 623ZZ inside the torso: it would
# sweep the top of the torso (and the head) as the arm swings — the room is for the electronics.
def _shoulder_pitch_at(p: BipedParams, sign: int):
    """Torso-frame stack point of the shoulder pitch servo (see _place)."""
    origin_y = p.torso_top_width_mm / 2 + SHOULDER_HORN_OUT_MM - HORN_TOP_MM
    return (0.0, sign * (origin_y + STACK_CENTRE_MM), p.shoulder_z_mm)


def _arm_preview(p: BipedParams, sign: int, s: str) -> dict:
    """Visuals per arm body. The roll yoke hangs from the shoulder link and the roll servo rides in
    the upper arm; the elbow yoke (no bearing) hangs from the upper arm and the elbow servo rides in
    the forearm; the wrist horn is on the forearm end and the wrist servo rides in the hand."""
    tx, ty, tz = p.torso_size_mm
    at = _shoulder_pitch_at(p, sign)
    at_local = (0.0, at[1] - sign * p.shoulder_y_mm, 0.0)
    pitch = _vis(f"pv_horn_shoulder_pitch{s}", "shoulder_pitch", sign, at_local, *HORN_BOX, material="horn",
                 axes=_shoulder_pitch_axes(p, sign))
    y0 = p.torso_top_width_mm / 2 + SHOULDER_HORN_OUT_MM             # horn top -> top of the roll yoke base
    y1 = p.shoulder_y_mm - YOKE_BOXES[0][1][1]
    link_z = -YOKE_BOXES[0][0][0] + YOKE_BOXES[0][1][0]               # roll yoke base top (servo body down)
    link = (f'<geom name="pv_shoulder_link{s}" type="box" size="{_v(6, max(1.0, (y1 - y0) / 2), 2)}" '
            f'pos="{_v(SHOULDER_ROLL_STACK_X_MM, -sign * (p.shoulder_y_mm - (y0 + y1) / 2), link_z - 2)}" '
            f'mass="0" material="yoke" class="visual"/>')
    roll_at = (SHOULDER_ROLL_STACK_X_MM, 0, 0)
    # elbow stack centred on the arm axis: servo z = ELBOW_STACK_CENTRE_MM on the axis
    shift = STACK_CENTRE_MM - ELBOW_STACK_CENTRE_MM
    elbow_at = (0.0, sign * shift, 0.0)
    wrist_at = (-WRIST_HOLDER_X_MM, 0.0, -HORN_TOP_MM + STACK_CENTRE_MM)   # horn top on the wrist plane
    plate = (f'<geom name="pv_wrist_plate{s}" type="box" size="{_v(8, 6, 1)}" pos="{_v(0, 0, -p.forearm_mm + 1)}" '
             f'mass="0" material="yoke" class="visual"/>')
    return dict(
        shoulder=pitch + link + _yoke_side("shoulder_roll", sign, s, roll_at),
        arm=(_servo_side("shoulder_roll", sign, roll_at, s)
             + _yoke_side("elbow", sign, s, (elbow_at[0], elbow_at[1], -p.upper_arm_mm), bearing=False)),
        forearm=(_servo_side("elbow", sign, elbow_at, s) + plate
                 + _vis(f"pv_horn_wrist{s}", "wrist", sign, (wrist_at[0], wrist_at[1], wrist_at[2] - p.forearm_mm),
                        *HORN_BOX, material="horn")
                 + _cover(f"forearm{s}", "forearm", shells(p)["forearm"].pos_mm)
                 + _cover(f"wrist{s}", "wrist", shells(p)["wrist"].pos_mm)),
        hand=_servo_side("wrist", sign, wrist_at, s) + _cover(f"hand{s}", "hand", shells(p)["hand"].pos_mm))


def _arm(p: BipedParams, side: str, sign: int, preview: bool = False) -> str:
    """Shoulder at the upper side of the torso; the arm hangs down along -Z: shoulder (pitch) ->
    upper arm (roll) -> forearm (elbow) -> hand (wrist rotation). Mass boxes hold each segment's
    servo, structure and cover; the preview draws the covers and the brackets instead."""
    tx, ty, tz = p.torso_size_mm
    s = f"_{side}"
    c = p.covers_g
    ru = p.upper_arm_cover_r_mm
    look = f'rgba="{COVER_RGBA}"' if preview else 'material="link"'
    pv = _arm_preview(p, sign, s) if preview else dict(shoulder="", arm="", forearm="", hand="")
    ua, fa, hd = p.upper_arm_mm, p.forearm_mm, p.hand_mm
    fx, fy = p.forearm_cover_half_mm
    hx, hy = p.hand_cover_half_mm
    roll_box = _servo_geom(f"servo_shoulder_roll{s}", p.servo("shoulder_roll").mass_g, -ua / 2 + 8)
    elbow_box = _servo_geom(f"servo_elbow{s}", p.servo("elbow").mass_g, -9)
    wrist_box = _servo_geom(f"servo_wrist{s}", p.servo("wrist").mass_g, -hd / 2)
    return f"""
      <body name="shoulder{s}" pos="{_v(0, sign * p.shoulder_y_mm, p.shoulder_z_mm)}">
        <joint name="shoulder_pitch{s}" class="shoulder_pitch"/>
        <geom name="cv_shoulder{s}" type="ellipsoid" size="{_v(*p.shoulder_cover_half_mm)}" pos="{_v(SHOULDER_ROLL_STACK_X_MM, 0, p.shoulder_cover_z_mm)}" mass="{_kg(c["shoulder"])}" {look} class="visual"/>
        {pv["shoulder"]}
        <body name="arm{s}" pos="0 0 0">
          <joint name="shoulder_roll{s}" class="shoulder_roll" axis="{-sign} 0 0"/>
          {_hidden(roll_box, preview)}
          <geom name="cv_upper_arm{s}" type="capsule" size="{_m(ru)}" fromto="0 0 0 {_v(0, 0, -p.upper_arm_cyl_mm)}" mass="{_kg(p.upper_arm_struct_g + c["upper_arm"])}" {look} class="visual"/>
          {pv["arm"]}
          <body name="forearm{s}" pos="{_v(0, 0, -ua)}">
            <joint name="elbow{s}" class="elbow"/>
            {_hidden(elbow_box, preview)}
            <geom name="forearm{s}" type="box" size="{_v(fx * 0.8, fy * 0.8, fa / 2 - 1)}" pos="{_v(0, 0, -fa / 2)}" mass="{_kg(p.forearm_struct_g + c["forearm"] + c["wrist"])}" material="link" class="visual"{' rgba="0 0 0 0"' if preview else ''}/>
            {pv["forearm"]}
            <body name="hand{s}" pos="{_v(0, 0, -fa)}">
              <joint name="wrist{s}" class="wrist"/>
              {_hidden(wrist_box, preview)}
              <geom name="hand{s}" type="box" size="{_v(hx * 0.8, hy * 0.8, hd / 2)}" pos="{_v(0, 0, -hd / 2)}" mass="{_kg(p.hand_struct_g + c["hand"])}" material="link" class="visual"{' rgba="0 0 0 0"' if preview else ''}/>
              {pv["hand"]}
            </body>
          </body>
        </body>
      </body>"""


def _head(p: BipedParams, preview: bool) -> str:
    tx, ty, tz = p.torso_size_mm
    hx, hy, hz = (s / 2 for s in p.head_size_mm)
    look = f'rgba="{COVER_RGBA}"' if preview else 'rgba="0.95 0.55 0.15 1"'
    us_x = hx - 6                                   # HC-SR04 board behind the face, eyes through the visor
    visor = (f'\n        <geom name="cv_visor" type="ellipsoid" size="{_v(hx * 0.45, hy * 0.78, hz * 0.4)}" '
             f'pos="{_v(hx * 0.62, 0, 0)}" mass="0" material="visor" class="visual"/>') if preview else ""
    return f"""
      <body name="head" pos="{_v(0, 0, tz / 2 + p.neck_mm + hz)}">
        <geom name="cv_head" type="ellipsoid" size="{_v(hx, hy, hz)}" mass="{_kg(p.covers_g["head"] + p.camera_reserve_g)}" {look} class="visual"/>{visor}
        <geom name="ultrasonic" type="box" size="{_v(1.0, 22.5, 10)}" pos="{_v(us_x, 0, 0)}" mass="{_kg(p.ultrasonic_g)}" rgba="0.1 0.35 0.75 1" class="visual"/>
        <geom name="us_eye_l" type="cylinder" size="{_v(8, 6)}" pos="{_v(us_x + 6, 13, 0)}" quat="0.707107 0 0.707107 0" mass="0" rgba="0.75 0.75 0.78 1" class="visual"/>
        <geom name="us_eye_r" type="cylinder" size="{_v(8, 6)}" pos="{_v(us_x + 6, -13, 0)}" quat="0.707107 0 0.707107 0" mass="0" rgba="0.75 0.75 0.78 1" class="visual"/>
        <site name="ultrasonic" pos="{_v(us_x + 12, 0, 0)}" size="0.002"/>
      </body>"""


def _joint_classes(p: BipedParams) -> str:
    """One default class per joint type: axis, mechanical stop, and that joint's servo model."""
    stops = dict(JOINT_STOPS, **(ARM_STOPS if p.arms else {}))
    out = []
    for j, (lo, hi) in stops.items():
        sv = p.servo(j)
        axis = {"ankle_roll": "1 0 0", "shoulder_roll": "1 0 0", "elbow": "0 -1 0", "wrist": "0 0 1"}.get(j, "0 1 0")
        out.append(f'    <default class="{j}"><joint axis="{axis}" range="{lo} {hi}" damping="{sv.damping:.4f}"/>'
                   f'<position forcerange="{-sv.stall_nm} {sv.stall_nm}"/></default>')
    return "\n".join(out)


def build_xml(p: BipedParams = BipedParams(), preview: bool = False) -> str:
    tx, ty, tz = p.torso_size_mm
    torso_g = p.torso_contents_g + p.torso_struct_g + p.covers_g["torso"]
    stops = dict(JOINT_STOPS, **(ARM_STOPS if p.arms else {}))
    actuators, sensors = [], []
    for group in (JOINT_STOPS, ARM_STOPS if p.arms else {}):
        for side in ("l", "r"):
            for j, (lo, hi) in group.items():
                clo, chi = math.radians(lo + SOFT_MARGIN_DEG), math.radians(hi - SOFT_MARGIN_DEG)
                actuators.append(f'    <position name="{j}_{side}" class="{j}" joint="{j}_{side}" ctrlrange="{clo:.4f} {chi:.4f}"/>')
    for side in ("l", "r"):
        for j in stops:
            sensors.append(f'    <actuatorfrc name="torque_{j}_{side}" actuator="{j}_{side}"/>')
    upper = ""
    if p.arms:
        upper += _arm(p, "l", +1, preview) + _arm(p, "r", -1, preview)
        for sd, sg in (("l", 1), ("r", -1)):
            at = _shoulder_pitch_at(p, sg)
            axes = _shoulder_pitch_axes(p, sg)
            cx, cy, cz = _place("shoulder_pitch", sg, at, HOLDER_BOX[0], axes)      # mass at the servo body
            box = _hidden(_servo_geom(f"servo_shoulder_pitch_{sd}", p.servo("shoulder_pitch").mass_g,
                                      cz, cy, cx), preview)
            if preview:
                box += _servo_side("shoulder_pitch", sg, at, f"_{sd}", axes)
            upper += "\n      " + box
    if p.head:
        upper += _head(p, preview)
    hip_g = p.servo("hip_pitch").mass_g
    hip_boxes = "\n      ".join(
        _hidden(_servo_geom(f"servo_hip_pitch_{sd}", hip_g, -tz / 2 + SERVO_HALF_MM[2], sg * p.hip_half_width_mm), preview)
        for sd, sg in (("l", 1), ("r", -1)))
    z0 = p.stand_height_mm + 1.0
    servo_list = ", ".join(sorted({SERVOS[k].label for k in p.servos.values()}))
    xml = f"""<!--
  GENERATED by sim/tools/build_biped.py from sim/tools/body.py - edit the parameters there, not this file.
  F1 biped: torso + 2 legs x 4 joints (hip pitch, knee, ankle pitch, ankle roll){' + head + 2 arms x 4 joints (shoulder pitch, shoulder roll, elbow, wrist)' if p.arms else ''},
  simple shapes with estimated masses. Total mass {p.total_mass_g:.0f} g (covers {p.covers_total_g:.0f} g),
  height {p.total_height_mm:.0f} mm, {p.servo_count} servos ({servo_list}).
  Joint range = mechanical stop; actuator ctrlrange = software limit {SOFT_MARGIN_DEG:.0f} deg inside it.
  Units: m, kg, s.
-->
<mujoco model="{'preview_biped' if preview else 'f1_biped'}">{'<compiler meshdir="meshes"/>' if preview else ''}
  <option timestep="0.002"/>
  <statistic center="0 0 {_m(p.stand_height_mm * 0.6)}" extent="{_m(p.stand_height_mm * 1.8)}"/>
  <visual>
    <headlight ambient="0.3 0.3 0.3" diffuse="0.5 0.5 0.5" specular="0 0 0"/>
    <global azimuth="135" elevation="-20"{' offwidth="1600" offheight="1200"' if preview else ''}/>
  </visual>
  <asset>
    <texture name="sky" type="skybox" builtin="gradient" rgb1="0.35 0.5 0.7" rgb2="0 0 0" width="256" height="256"/>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.2 0.25 0.3" rgb2="0.3 0.35 0.4" width="256" height="256"/>
    <material name="floor" texture="grid" texrepeat="20 20" reflectance="0.1"/>
    <material name="servo" rgba="0.2 0.35 0.8 1"/>
    <material name="link" rgba="0.85 0.85 0.85 1"/>
    <material name="torso" rgba="0.95 0.55 0.15 {0.25 if preview else 1}"/>{PREVIEW_ASSETS + _cover_assets(p) if preview else ""}
  </asset>
  <default>
    <joint damping="{SERVOS['sg90'].damping:.4f}" armature="{p.armature}" limited="true"/>
    <position kp="{p.kp}" ctrllimited="true"/>
    <default class="visual"><geom contype="0" conaffinity="0"/></default>
    <default class="contact"><geom contype="1" conaffinity="1" friction="0.8 0.02 0.001"/></default>
{_joint_classes(p)}
  </default>
  <worldbody>
    <light name="sun" pos="0.3 -0.3 1" dir="-0.3 0.3 -1" directional="true" diffuse="0.6 0.6 0.6"/>
    <geom name="floor" type="plane" size="1 1 0.1" material="floor" class="contact"/>
    <body name="torso" pos="0 0 {_m(z0)}">
      <freejoint/>
      <geom name="torso" type="box" size="{_v(tx / 2, ty / 2, tz / 2)}" mass="{_kg(torso_g)}" material="torso" class="contact"/>
      {hip_boxes}
      {_torso_preview(p) if preview else ""}
      <site name="imu" pos="0 0 0" size="0.004"/>{_leg(p, "l", +1, preview)}{_leg(p, "r", -1, preview)}{upper}
    </body>
  </worldbody>
  <actuator>
{chr(10).join(actuators)}
  </actuator>
  <sensor>
    <accelerometer name="imu_acc" site="imu"/>
    <gyro name="imu_gyro" site="imu"/>
    <framequat name="imu_quat" objtype="site" objname="imu"/>
{chr(10).join(sensors)}
  </sensor>
</mujoco>
"""
    return "\n".join(line for line in xml.splitlines() if line.strip()) + "\n"   # drop empty preview slots


def load_preview(p: BipedParams):
    """Compile the preview of any parameter set in memory (meshes from sim/models/meshes)."""
    import mujoco
    meshes = PREVIEW_OUT.parent / "meshes"
    assets = {f.name: f.read_bytes() for f in meshes.glob("*.stl")}
    xml = build_xml(p, preview=True).replace('<compiler meshdir="meshes"/>', "")
    return mujoco.MjModel.from_xml_string(xml, assets)


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preview", action="store_true",
                    help="also write sim/models/preview_biped.xml: same robot with covers, servo meshes, holders, yokes")
    args = ap.parse_args()
    p = BipedParams()
    OUT.write_text(build_xml(p))
    print(f"wrote {OUT.relative_to(OUT.parents[2])}: total {p.total_mass_g:.0f} g (covers {p.covers_total_g:.0f} g), "
          f"height {p.total_height_mm:.0f} mm, standing torso centre at {p.stand_height_mm:.0f} mm")
    if args.preview:
        PREVIEW_OUT.write_text(build_xml(p, preview=True))
        print(f"wrote {PREVIEW_OUT.relative_to(OUT.parents[2])}")


if __name__ == "__main__":
    main()
