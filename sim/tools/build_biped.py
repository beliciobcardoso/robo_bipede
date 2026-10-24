"""Generate the F1 biped model (sim/models/f1_biped.xml) from a few design parameters.

    .venv/bin/python sim/tools/build_biped.py            # write sim/models/f1_biped.xml
    from build_biped import BipedParams, build_xml       # F2 sweeps build variants in memory

Whole robot made of boxes with estimated masses placed where the real parts will be:
torso (battery, ESP32, MPU-6050 board, buck, torso covers) and two legs with 4 joints each
(hip pitch, knee, ankle pitch, ankle roll). Each SG90 is a 9 g box at its joint, carried by
the segment that holds its body. Joint ranges follow docs/arquitetura_perna.md: joint range =
mechanical stop, actuator ctrlrange = software limit 5° inside it.

Input dimensions are in mm and g (like the CAD); the MJCF is written in m and kg.
Contacts: only feet, torso and floor collide (leg-to-leg contact is ignored in F1).
"""

import math
from dataclasses import dataclass, field
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "models" / "f1_biped.xml"

SERVO_G = 9.0
SERVO_HALF_MM = (6.1, 11.8, 11.5)        # SG90 body: 12.2 x 23.6 x 23 mm, shaft along Y (pitch)
SOFT_MARGIN_DEG = 5.0
# joint: (mechanical stop min, max) in degrees; sign convention: crouch = hip +, knee -, ankle +
JOINT_STOPS = {
    "hip_pitch": (-30.0, 90.0),
    "knee": (-120.0, 5.0),
    "ankle_pitch": (-45.0, 45.0),
    "ankle_roll": (-30.0, 30.0),
}


@dataclass(frozen=True)
class BipedParams:
    # Lengths between joint axes (mm)
    thigh_mm: float = 45.0          # hip pitch -> knee
    shin_mm: float = 45.0           # knee -> ankle pitch
    ankle_link_mm: float = 12.0     # ankle pitch -> ankle roll
    roll_to_sole_mm: float = 14.0   # ankle roll axis -> bottom of the sole
    hip_half_width_mm: float = 27.5  # torso centre -> each hip (55 mm between legs)
    hip_drop_mm: float = 10.0       # torso bottom -> hip pitch axis

    # Torso box (mm) and what it carries (g)
    torso_size_mm: tuple = (50.0, 70.0, 45.0)
    battery_g: float = 95.0         # 2 x 18650
    electronics_g: float = 35.0     # ESP32, MPU-6050, perfboard, buck
    torso_struct_g: float = 25.0
    torso_cover_g: float = 20.0

    # Per-leg segment masses (g), excluding the servos (added separately)
    thigh_struct_g: float = 10.0
    shin_struct_g: float = 10.0
    ankle_struct_g: float = 6.0
    foot_struct_g: float = 15.0
    leg_cover_g: float = 15.0       # split over thigh / shin / foot
    foot_size_mm: tuple = (70.0, 45.0, 6.0)

    # Servo model (SG90-like position servo; to be calibrated in F3)
    stall_torque_nm: float = 0.18
    kp: float = 1.5
    # torque falls with speed: stall torque / no-load speed = 0.18 N·m / 10.5 rad/s (0.1 s/60°)
    joint_damping: float = 0.017
    armature: float = 0.0005

    @property
    def total_mass_g(self) -> float:
        torso = self.battery_g + self.electronics_g + self.torso_struct_g + self.torso_cover_g
        leg = (self.thigh_struct_g + self.shin_struct_g + self.ankle_struct_g + self.foot_struct_g
               + self.leg_cover_g + 3 * SERVO_G)
        return torso + 2 * SERVO_G + 2 * leg       # 2 hip servos sit in the torso

    @property
    def stand_height_mm(self) -> float:
        """Torso centre height when standing straight with flat feet on the floor."""
        return (self.torso_size_mm[2] / 2 + self.hip_drop_mm + self.thigh_mm + self.shin_mm
                + self.ankle_link_mm + self.roll_to_sole_mm)


def _m(mm: float) -> str:
    return f"{mm / 1000:.5f}"


def _v(*mm: float) -> str:
    return " ".join(_m(x) for x in mm)


def _kg(g: float) -> str:
    return f"{g / 1000:.5f}"


def _servo_geom(name: str, z_mm: float, y_mm: float = 0.0) -> str:
    hx, hy, hz = SERVO_HALF_MM
    return (f'<geom name="{name}" type="box" size="{_v(hx, hy, hz)}" pos="{_v(0, y_mm, z_mm)}" '
            f'mass="{_kg(SERVO_G)}" material="servo" class="visual"/>')


def _leg(p: BipedParams, side: str, sign: int) -> str:
    cover = p.leg_cover_g / 3
    fx, fy, fz = p.foot_size_mm
    s = f"_{side}"
    return f"""
      <body name="thigh{s}" pos="{_v(0, sign * p.hip_half_width_mm, -p.torso_size_mm[2] / 2 - p.hip_drop_mm)}">
        <joint name="hip_pitch{s}" class="hip_pitch"/>
        <geom name="thigh{s}" type="box" size="{_v(7, 9, p.thigh_mm / 2)}" pos="{_v(0, 0, -p.thigh_mm / 2)}" mass="{_kg(p.thigh_struct_g + cover)}" material="link" class="visual"/>
        {_servo_geom(f"servo_knee{s}", -p.thigh_mm + SERVO_HALF_MM[2] - 4)}
        <body name="shin{s}" pos="{_v(0, 0, -p.thigh_mm)}">
          <joint name="knee{s}" class="knee"/>
          <geom name="shin{s}" type="box" size="{_v(7, 9, p.shin_mm / 2)}" pos="{_v(0, 0, -p.shin_mm / 2)}" mass="{_kg(p.shin_struct_g + cover)}" material="link" class="visual"/>
          {_servo_geom(f"servo_ankle_pitch{s}", -p.shin_mm + SERVO_HALF_MM[2] - 4)}
          <body name="ankle{s}" pos="{_v(0, 0, -p.shin_mm)}">
            <joint name="ankle_pitch{s}" class="ankle_pitch"/>
            <geom name="ankle{s}" type="box" size="{_v(10, 8, p.ankle_link_mm / 2)}" pos="{_v(0, 0, -p.ankle_link_mm / 2)}" mass="{_kg(p.ankle_struct_g + SERVO_G)}" material="servo" class="visual"/>
            <body name="foot{s}" pos="{_v(0, 0, -p.ankle_link_mm)}">
              <joint name="ankle_roll{s}" class="ankle_roll"/>
              <geom name="foot{s}" type="box" size="{_v(fx / 2, fy / 2, fz / 2)}" pos="{_v(0, 0, -p.roll_to_sole_mm + fz / 2)}" mass="{_kg(p.foot_struct_g + cover)}" material="link" class="contact"/>
              <site name="sole{s}" pos="{_v(0, 0, -p.roll_to_sole_mm)}" size="0.002"/>
            </body>
          </body>
        </body>
      </body>"""


def build_xml(p: BipedParams = BipedParams()) -> str:
    tx, ty, tz = p.torso_size_mm
    torso_g = p.battery_g + p.electronics_g + p.torso_struct_g + p.torso_cover_g
    stops = "\n".join(
        f'    <default class="{j}"><joint axis="{"1 0 0" if j == "ankle_roll" else "0 1 0"}" range="{lo} {hi}"/></default>'
        for j, (lo, hi) in JOINT_STOPS.items())
    actuators = []
    for side in ("l", "r"):
        for j, (lo, hi) in JOINT_STOPS.items():
            clo, chi = math.radians(lo + SOFT_MARGIN_DEG), math.radians(hi - SOFT_MARGIN_DEG)
            actuators.append(f'    <position name="{j}_{side}" joint="{j}_{side}" ctrlrange="{clo:.4f} {chi:.4f}"/>')
    sensors = []
    for side in ("l", "r"):
        for j in JOINT_STOPS:
            sensors.append(f'    <actuatorfrc name="torque_{j}_{side}" actuator="{j}_{side}"/>')
    z0 = p.stand_height_mm + 1.0
    return f"""<!--
  GENERATED by sim/tools/build_biped.py - edit the parameters there, not this file.
  F1 biped: torso + 2 legs x 4 joints (hip pitch, knee, ankle pitch, ankle roll), boxes with
  estimated masses. Total mass {p.total_mass_g:.0f} g. Thigh {p.thigh_mm:.0f} mm, shin {p.shin_mm:.0f} mm.
  Joint range = mechanical stop; actuator ctrlrange = software limit {SOFT_MARGIN_DEG:.0f} deg inside it.
  Units: m, kg, s.
-->
<mujoco model="f1_biped">
  <option timestep="0.002"/>
  <statistic center="0 0 {_m(p.stand_height_mm * 0.6)}" extent="{_m(p.stand_height_mm * 1.8)}"/>
  <visual>
    <headlight ambient="0.3 0.3 0.3" diffuse="0.5 0.5 0.5" specular="0 0 0"/>
    <global azimuth="135" elevation="-20"/>
  </visual>
  <asset>
    <texture name="sky" type="skybox" builtin="gradient" rgb1="0.35 0.5 0.7" rgb2="0 0 0" width="256" height="256"/>
    <texture name="grid" type="2d" builtin="checker" rgb1="0.2 0.25 0.3" rgb2="0.3 0.35 0.4" width="256" height="256"/>
    <material name="floor" texture="grid" texrepeat="20 20" reflectance="0.1"/>
    <material name="servo" rgba="0.2 0.35 0.8 1"/>
    <material name="link" rgba="0.85 0.85 0.85 1"/>
    <material name="torso" rgba="0.95 0.55 0.15 1"/>
  </asset>
  <default>
    <joint damping="{p.joint_damping}" armature="{p.armature}" limited="true"/>
    <position kp="{p.kp}" forcerange="{-p.stall_torque_nm} {p.stall_torque_nm}" ctrllimited="true"/>
    <default class="visual"><geom contype="0" conaffinity="0"/></default>
    <default class="contact"><geom contype="1" conaffinity="1" friction="0.8 0.02 0.001"/></default>
{stops}
  </default>
  <worldbody>
    <light name="sun" pos="0.3 -0.3 1" dir="-0.3 0.3 -1" directional="true" diffuse="0.6 0.6 0.6"/>
    <geom name="floor" type="plane" size="1 1 0.1" material="floor" class="contact"/>
    <body name="torso" pos="0 0 {_m(z0)}">
      <freejoint/>
      <geom name="torso" type="box" size="{_v(tx / 2, ty / 2, tz / 2)}" mass="{_kg(torso_g)}" material="torso" class="contact"/>
      {_servo_geom("servo_hip_pitch_l", -tz / 2 + SERVO_HALF_MM[2], +p.hip_half_width_mm)}
      {_servo_geom("servo_hip_pitch_r", -tz / 2 + SERVO_HALF_MM[2], -p.hip_half_width_mm)}
      <site name="imu" pos="0 0 0" size="0.004"/>{_leg(p, "l", +1)}{_leg(p, "r", -1)}
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


def main():
    p = BipedParams()
    OUT.write_text(build_xml(p))
    print(f"wrote {OUT.relative_to(OUT.parents[2])}: total {p.total_mass_g:.0f} g, "
          f"standing torso centre at {p.stand_height_mm:.0f} mm")


if __name__ == "__main__":
    main()
