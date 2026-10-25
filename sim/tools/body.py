"""Design parameters of the whole biped — legs, torso, arms, head — in mm and g.

    from body import BipedParams, SERVOS, shells

Shared by the MJCF generator (build_biped.py), the 3D preview and the sweeps, so every tool sees
the same robot. The printed covers ("capas") are not guessed masses: each one is a thin shell
whose surface comes from its shape, times the wall thickness and PETG density, plus an allowance
for clips, locating pins and ribs. Changing a proportion therefore changes the cover masses too.
"""

import math
from dataclasses import dataclass, field

PETG_G_PER_MM3 = 1.27e-3
SOFT_MARGIN_DEG = 5.0
# joint: (mechanical stop min, max) in degrees; sign convention: crouch = hip +, knee -, ankle +
JOINT_STOPS = {
    "hip_pitch": (-30.0, 90.0),
    "knee": (-120.0, 5.0),
    "ankle_pitch": (-45.0, 45.0),
    "ankle_roll": (-30.0, 30.0),
}
# arm joints: positive shoulder roll lifts the arm sideways, outward; positive elbow bends the
# forearm forward; the wrist turns the hand about the forearm axis
ARM_STOPS = {
    "shoulder_pitch": (-90.0, 90.0),
    "shoulder_roll": (-10.0, 90.0),
    "elbow": (-10.0, 120.0),
    "wrist": (-90.0, 90.0),
}
# waist yaw (2026-10-25, user): the upper body turns +-45 deg on the pelvis; servo fixed in the pelvis
# above the hip servos, shaft up, horn under the torso; the pivot bearing carries the upper body
WAIST_STOPS = {"waist_yaw": (-50.0, 50.0)}
# optional hip roll (BipedParams.hip_roll): servo in the pelvis, shaft forward; it tilts the whole leg
# sideways so the pelvis can move over the stance foot without tilting the robot
HIP_ROLL_STOPS = {"hip_roll": (-30.0, 30.0)}
SERVO_HALF_MM = (6.1, 11.8, 11.5)        # SG90 body: 12.2 x 23.6 x 23 mm, shaft along Y (pitch)
# The shoulder roll servo hangs body-down inside the upper arm, slid forward along its shaft so its
# holder is centred in the arm; its horn + bearing stack (along X) is then centred this far forward.
SHOULDER_ROLL_STACK_X_MM = 5.25
# Elbow: servo body down inside the forearm, shaft outward; no 623ZZ (the light forearm + hand
# would not need it, and a 42.5 mm stack would make the arm 5 mm wider). Horn-side yoke arm to
# holder floor spans servo z -19..+18 (centre -0.5) across the arm.
ELBOW_STACK_HALF_MM = 18.5
ELBOW_STACK_CENTRE_MM = -0.5
# Wrist: servo inside the hand, shaft up along the forearm, horn on the forearm end; slid back
# along its body so the holder (servo x -8..26) is centred in the hand.
WRIST_HOLDER_X_MM = 9.0
SERVO_BELOW_HORN_MM = 35.0     # horn top -> holder floor (servo z +16 .. -19)
ELBOW_HOLDER_DOWN_MM = 27.0    # elbow axis -> bottom of the elbow servo holder (+1 mm): the forearm is wide only this far


@dataclass(frozen=True)
class Servo:
    label: str
    mass_g: float
    stall_nm: float          # at the 5 V servo rail (conservative design point; 6 V gives more)
    no_load_rad_s: float     # at 5 V
    note: str

    @property
    def damping(self) -> float:
        """Torque lost per rad/s of speed: stall torque / no-load speed."""
        return self.stall_nm / self.no_load_rad_s


# Decision 2026-10-24 (user): SG90 clones on every joint. Calibrate on the F3 bench.
SERVOS = {
    "sg90": Servo("SG90 (clone)", 9.0, 0.18, 10.5, "1,8 kg·cm, 0,10 s/60°"),
}


@dataclass(frozen=True)
class CarriedPart:
    """Something carried inside the torso or pelvis frame (`seat`): a box in its own axes (length,
    width, thickness), plus envelopes kept free for what plugs into it. An envelope listed in
    `access` must reach the wall (a cable plugged from outside: USB, switch). Sizes are catalogue
    values — measure the real part and update."""
    seat: str                  # "torso" or "pelvis"
    label: str
    size_mm: tuple
    mass_g: float
    source: str
    envelopes: tuple = ()      # ((centre xyz in the part frame, half sizes xyz), ...) mm
    access: tuple = ()         # indices into envelopes
    flat: bool = False         # thickness must stay vertical (the IMU)


# What the body carries. Split decided 2026-10-25 (user): the ESP32 rides in the torso and drives the
# 8 arm servos directly (LEDC); the pelvis holds the power, the IMU (fixed to the legs, the torso turns)
# and a PCA9685 for the 8 leg servos + the waist servo. Only the servo 5 V rail, the logic 5 V and
# I2C cross the waist — no servo cable does. Torso positions: TORSO_LAYOUT (sim/tools/torso_layout.py).
BODY_PARTS = {
    # 2026-10-25 (user): two packs to test, same XT30 + JST-XH balance plug; the bay is the LiPo's,
    # which also holds the 2S1P 14500 pack (~28 x 14 x 51 mm, ~53 g) — mass kept at the heavier one
    "bateria": CarriedPart("pelvis", "bateria 2S: LiPo 800 mAh ou 2S1P 14500", (56.0, 31.0, 17.0), 55.0,
                         "Gens Ace 2S 800 mAh: 55 × 30 × 16 mm, 50 g + cabos e XT30; 2S1P 14500 cabe no mesmo vão",
                         # leads at one end; the other end slides out through a drawer door in the back
                         # of the pelvis cover (2026-10-25, user: swap and maintenance without opening the pelvis)
                         envelopes=(((34.0, 0.0, 0.0), (6.0, 12.0, 7.0)), ((-29.0, 0.0, 0.0), (1.0, 15.5, 8.5))),
                         access=(1,)),
    # 2026-10-25 (user): servo rail and logic on separate regulators; docs/alimentacao.md
    "regulador": CarriedPart("pelvis", "regulador dos servos 5 V 15 A (Pololu D24V150F5)", (43.2, 31.8, 11.0), 10.0,
                           "Pololu D24V150F5: 43,2 × 31,8 × 11 mm; massa não informada, 10 g estimado — pesar",
                           envelopes=(((26.6, 0.0, 0.0), (5.0, 10.0, 5.5)),)),       # wires at one end
    "regulador_logica": CarriedPart("pelvis", "regulador da lógica 5 V 1 A (Pololu D24V10F5)", (18.0, 13.0, 3.5), 1.0,
                                  "Pololu D24V10F5: 18 × 13 × 3,5 mm; massa não informada, 1 g estimado — pesar",
                                  envelopes=(((12.0, 0.0, 0.0), (3.0, 5.0, 3.0)),)),  # wires at one end
    "controle": CarriedPart("torso", "ESP32 DevKit em placa perfurada", (56.0, 34.0, 16.0), 18.0,
                          "ESP32 DevKit V1 51,8 × 28,2 mm em barra fêmea sobre placa 56 × 34 mm",
                          envelopes=(((-35.0, 0.0, 4.0), (7.0, 6.0, 5.0)),), access=(0,)),   # USB plug
    "pca9685": CarriedPart("pelvis", "PCA9685 (8 servos das pernas + cintura)", (62.5, 25.4, 11.0), 9.0,
                         "Adafruit PCA9685: 62,5 × 25,4 mm; bornes ~10 mm de altura",
                         envelopes=(((0.0, 23.7, 0.0), (31.25, 11.0, 5.5)),)),       # 16 plugs, right-angle headers
    "distribuicao": CarriedPart("pelvis", "placa de força", (45.0, 30.0, 14.0), 15.0,
                              "capacitores 2 × 1000 µF deitados, fusível 7,5 A retardado, divisor da bateria, buzzer, XT30 (estimado)"),
    "mpu6050": CarriedPart("pelvis", "MPU-6050 (GY-521)", (21.0, 16.0, 5.0), 2.0, "GY-521: 21 × 16 mm", flat=True),
    "chave": CarriedPart("pelvis", "chave liga/desliga", (21.0, 15.0, 18.0), 4.0, "rocker mini 21 × 15 mm, 18 mm de corpo",
                       envelopes=(((0.0, 0.0, -10.0), (10.5, 7.5, 1.0)),), access=(0,)),  # button face on the cover
}
WIRING_G = {"torso": 3.0, "pelvis": 6.0}   # power leads, I2C, signals (servo cables count with the servos)
# name -> (centre xyz mm in the torso frame, rotation: rows = torso axes, columns = part length/width/thickness)
TORSO_LAYOUT = {                 # torso_layout.py --search, 2026-10-25
    "controle": ((-6.0, -6.0, -4.0), ((0, 1, 0), (-1, 0, 0), (0, 0, 1))),
}
PELVIS_LAYOUT = {                # torso_layout.py --seat pelvis --search, 2026-10-25
    "pca9685": ((-30.0, -13.0, 11.0), ((0, 0, 1), (-1, 0, 0), (0, -1, 0))),
    "bateria": ((-6.0, 28.0, 8.0), ((1, 0, 0), (0, 0, 1), (0, -1, 0))),
    "regulador": ((14.0, -38.0, 8.0), ((-1, 0, 0), (0, 0, 1), (0, 1, 0))),
    "distribuicao": ((12.0, -24.0, 8.0), ((1, 0, 0), (0, 0, 1), (0, -1, 0))),
    "chave": ((-26.0, 34.0, -16.0), ((1, 0, 0), (0, 0, 1), (0, -1, 0))),
    "mpu6050": ((18.0, 0.0, -14.0), ((0, 1, 0), (1, 0, 0), (0, 0, -1))),
    "regulador_logica": ((32.0, -34.0, -16.0), ((0, 0, 1), (1, 0, 0), (0, 1, 0))),
}


def _all_sg90() -> dict:
    return {j: "sg90" for j in (*JOINT_STOPS, *ARM_STOPS, *WAIST_STOPS, *HIP_ROLL_STOPS)}


@dataclass(frozen=True)
class BipedParams:
    # Lengths between joint axes (mm) — thigh = shin = 45, approved after F2 (docs/arquitetura_perna.md)
    thigh_mm: float = 45.0          # hip pitch -> knee
    shin_mm: float = 45.0           # knee -> ankle pitch
    ankle_link_mm: float = 22.0     # ankle pitch -> ankle roll (ankle yoke + roll-servo holder, docs/suporte_servo.md)
    roll_to_sole_mm: float = 14.0   # ankle roll axis -> bottom of the sole
    hip_half_width_mm: float = 25.0  # torso centre -> each hip (50 mm between legs; legs are ~42 mm wide)
    leg_width_mm: float = 42.0      # along the pitch axes: horn + servo + bearing stack
    hip_drop_mm: float = 10.0       # pelvis bottom -> hip pitch axis

    # Pelvis (2026-10-25): carries the 2 hip pitch servos and the legs; the torso turns on it about
    # the waist yaw axis. Box x depth, z height (mm); its width is the two hip servo stacks.
    # 2026-10-25: holds the power, IMU and leg PCA9685 (BODY_PARTS seat "pelvis", PELVIS_LAYOUT) with
    # the waist servo stacked over the hip servos (they reach 16 mm above the pelvis bottom); 76 x 52 is
    # the smallest box where the layout search fits everything (60 x 38 was wished for the torques)
    pelvis_depth_mm: float = 76.0
    pelvis_height_mm: float = 52.0
    waist_pivot_g: float = 8.0      # nominal: bearing + pin of the waist yaw pivot (to choose)
    hip_roll: bool = False          # hip roll servo per leg (not approved; studied 2026-10-25)
    hip_roll_link_mm: float = 22.0  # hip roll axis -> hip pitch axis (like the ankle block)
    hip_roll_struct_g: float = 6.0

    # Torso frame (the skeleton box, x depth, y width, z height, mm) and what it carries (g)
    # Proportions approved 2026-10-24 (Alpha 1 look with SG90, docs/arquitetura_corpo.md): torso 68 mm,
    # 86 mm at the shoulders, big head -> head / torso / legs = 20 / 31 / 50 % of 254 mm
    # 2026-10-25: 76 deep and 78 at the hips (was 50 x 70) so the electronics fit between the 4 torso
    # servos (sim/tools/torso_layout.py); a mild V from the shoulders down, chosen by the user
    # 2026-10-25 (user, variant B): V torso — 62 at the waist, 96 at the shoulders, 50 tall: cover chest
    # / waist = 1.52 (the user's reference silhouettes: 1.5-2.1); only the ESP32 and the shoulder servos
    # ride inside (the electronics went to the pelvis); 50 tall is the least where the ESP32 fits
    torso_size_mm: tuple = (50.0, 62.0, 50.0)
    torso_top_width_mm: float = 96.0  # frame width at the shoulders
    shoulder_pitch_body: str = "front"  # shoulder pitch servo body lies "back" / "front" / "down" from its shaft
    torso_struct_g_per_cm2: float = 25.0 / 178.0   # frame plates: 25 g on a 50 x 70 x 45 mm frame (scaled by area)

    # Per-leg segment structure (g), excluding servos and covers
    thigh_struct_g: float = 10.0
    shin_struct_g: float = 10.0
    ankle_struct_g: float = 6.0
    foot_struct_g: float = 15.0
    foot_size_mm: tuple = (70.0, 45.0, 6.0)   # 45 wide = hip spacing - 5 mm, feet never touch

    # Head (fixed to the torso): HC-SR04 + printed shell, room reserved for a camera
    head: bool = True
    ultrasonic_g: float = 8.5
    camera_reserve_g: float = 10.0  # future camera (ESP32-CAM); counted now so the budget holds
    head_size_mm: tuple = (52.0, 58.0, 48.0)   # ellipsoid shell, full sizes x y z
    neck_mm: float = 2.0            # torso top -> bottom of the head

    # Arms (4 servos each, 2026-10-24): shoulder pitch (servo in the torso), shoulder roll (servo in
    # the upper arm), elbow (servo in the forearm), wrist rotation (servo in the hand); fixed hand.
    # Lengths follow the 8-head landmarks: elbow at the navel, wrist at the crotch, hand 2/3-1 head,
    # fingertips at mid-thigh — as short as the servo chain allows (docs/arquitetura_corpo.md).
    arms: bool = True
    upper_arm_mm: float = 42.0      # shoulder roll axis -> elbow axis (roll servo 26 + elbow yoke base 14 + 2)
    forearm_mm: float = 36.0        # elbow axis -> wrist (elbow holder 26 + wrist plate)
    hand_mm: float = 38.0           # wrist -> fingertips (0.75 head; holds the 35 mm wrist servo)
    upper_arm_struct_g: float = 5.0
    forearm_struct_g: float = 4.0
    hand_struct_g: float = 3.0
    arm_leg_gap_mm: float = 3.0     # sideways clearance between an arm cover and the torso / leg cover

    # Covers (snap-fit shells, docs/capas.md)
    shell_mm: float = 0.8           # wall thickness: 0.8 mm (2 PETG perimeters) since 2026-10-25, was 1.2 — -68 g
    shell_extra: float = 0.15       # clips, locating pins, ribs: fraction of the shell mass
    cover_scale: float = 1.0        # F2 "heavy covers" multiplies every cover mass
    cover_gap_mm: float = 1.0       # air between the skeleton and the inside of a cover
    cover_corner_n: float = 8.0     # section shape: 2 = ellipse, 4 = rounded, 8 = nearly square (chosen 2026-10-24: shoulders 18.2 cm)
    leg_cover_fraction: float = 0.75     # length of each thigh / shin covered (the joints stay free)
    upper_arm_cover_r_mm: float = 15.0   # holds the shoulder roll servo (body down inside the upper arm)
    shoulder_cover_half_mm: tuple = (31.0, 16.0, 19.0)   # ellipsoid on the shoulder pitch, around the roll yoke
    shoulder_cover_z_mm: float = 4.0     # its centre above the shoulder roll axis

    # Servo per joint type (SERVOS key), position-servo model to be calibrated in F3
    servos: dict = field(default_factory=_all_sg90)
    kp: float = 1.5
    armature: float = 0.0005

    # ------------------------------------------------------------------ derived geometry
    @property
    def stand_height_mm(self) -> float:
        """Torso centre height when standing straight with flat feet on the floor."""
        return (self.torso_size_mm[2] / 2 + self.pelvis_height_mm + self.hip_drop_mm + self.hip_link_mm
                + self.thigh_mm + self.shin_mm + self.ankle_link_mm + self.roll_to_sole_mm)

    @property
    def hip_link_mm(self) -> float:
        """Hip roll axis -> hip pitch axis (0 without hip roll)."""
        return self.hip_roll_link_mm if self.hip_roll else 0.0

    @property
    def leg_stops(self) -> dict:
        """Joint stops of one leg, top to bottom."""
        return dict(HIP_ROLL_STOPS, **JOINT_STOPS) if self.hip_roll else dict(JOINT_STOPS)

    @property
    def pelvis_width_mm(self) -> float:
        return 2 * self.hip_half_width_mm + self.leg_width_mm

    @property
    def hip_z_mm(self) -> float:
        """Hip pitch axes height in the torso frame (waist yaw at zero)."""
        return -self.torso_size_mm[2] / 2 - self.pelvis_height_mm - self.hip_drop_mm - self.hip_link_mm

    @property
    def total_height_mm(self) -> float:
        top = self.stand_height_mm + self.torso_size_mm[2] / 2
        return top + (self.neck_mm + self.head_size_mm[2] if self.head else 3.0)

    def cover_half_mm(self, inside_half_mm: float) -> float:
        """Half size of a cover section that encloses a rectangle of this half size (both axes
        scaled alike), with the air gap and the wall."""
        return (inside_half_mm + self.cover_gap_mm + self.shell_mm) * 2 ** (1 / self.cover_corner_n)

    @property
    def leg_cover_half_mm(self) -> tuple:
        """(x, y) half sizes of the thigh / shin cover: around the servo + holder + yoke stack
        (x +-8.1 holder, y +-21 horn-servo-bearing)."""
        return self.cover_half_mm(8.1), self.cover_half_mm(self.leg_width_mm / 2)

    @property
    def forearm_cover_half_mm(self) -> tuple:
        """(x, y) half sizes of the forearm cover: around the elbow holder (x +-8.1) and the elbow stack (y)."""
        return self.cover_half_mm(8.1), self.cover_half_mm(ELBOW_STACK_HALF_MM)

    @property
    def wrist_cover_half_mm(self) -> tuple:
        """(x, y) half sizes of the slim lower forearm, below the elbow servo: link + wrist plate."""
        return self.cover_half_mm(8.1), self.cover_half_mm(8.1)

    @property
    def hand_cover_half_mm(self) -> tuple:
        """(x, y) half sizes of the hand cover: around the wrist servo holder (x +-17, y +-8.1)."""
        return self.cover_half_mm(17.0), self.cover_half_mm(8.1)

    def _torso_cover_half_y(self, z: float) -> float:
        """Half width of the torso cover at height z (torso frame); 0 below it."""
        rings = shells(self)["torso"].rings
        if z < rings[0][0]:
            return 0.0
        for (z0, _, y0), (z1, _, y1) in zip(rings, rings[1:]):
            if z <= z1:
                return y0 + (y1 - y0) * (z - z0) / (z1 - z0)
        return rings[-1][2]

    @property
    def shoulder_z_mm(self) -> float:
        """Shoulder axes height in the torso frame."""
        return self.torso_size_mm[2] / 2 - 10

    @property
    def shoulder_y_mm(self) -> float:
        """Arm axis distance from the centre line: every hanging arm piece clears what is beside it —
        the torso cover over its whole height, and the leg cover where it reaches below the hips."""
        g, zs = self.arm_leg_gap_mm, self.shoulder_z_mm
        hip = self.hip_z_mm
        thigh_top = hip - self.thigh_mm * (1 - self.leg_cover_fraction) / 2
        leg_out = self.hip_half_width_mm + self.leg_cover_half_mm[1]
        elbow, wrist = zs - self.upper_arm_mm, zs - self.upper_arm_mm - self.forearm_mm
        pieces = ((zs, elbow, self.upper_arm_cover_r_mm),            # (top, bottom, half width in y)
                  (elbow, elbow - ELBOW_HOLDER_DOWN_MM, self.forearm_cover_half_mm[1]),
                  (elbow - ELBOW_HOLDER_DOWN_MM, wrist, self.wrist_cover_half_mm[1]),
                  (wrist, wrist - self.hand_mm, self.hand_cover_half_mm[1]))
        need = []
        for top, bottom, half in pieces:
            need.append(self._torso_cover_half_y(top) + g + half)     # the torso cover widens upward
            if bottom < thigh_top:
                need.append(leg_out + g + half)
        return max(need)

    @property
    def shoulder_width_mm(self) -> float:
        """Outside width across the arms (the widest arm piece)."""
        half = max(self.shoulder_cover_half_mm[1], self.upper_arm_cover_r_mm,
                   self.forearm_cover_half_mm[1], self.wrist_cover_half_mm[1], self.hand_cover_half_mm[1])
        return 2 * (self.shoulder_y_mm + half)

    def servo(self, joint: str) -> Servo:
        return SERVOS[self.servos[joint]]

    # ------------------------------------------------------------------ masses
    @property
    def contents_g(self) -> dict:
        """Mass of what each segment carries (BODY_PARTS + wiring), g: {"torso": .., "pelvis": ..}."""
        return {seat: sum(q.mass_g for q in BODY_PARTS.values() if q.seat == seat) + w for seat, w in WIRING_G.items()}

    @property
    def torso_struct_g(self) -> float:
        x, y, z = self.torso_size_mm
        y = (y + self.torso_top_width_mm) / 2
        return self.torso_struct_g_per_cm2 * 2 * (x * y + x * z + y * z) / 100

    @property
    def pelvis_struct_g(self) -> float:
        x, y, z = self.pelvis_depth_mm, self.pelvis_width_mm, self.pelvis_height_mm
        return self.torso_struct_g_per_cm2 * 2 * (x * y + x * z + y * z) / 100 + self.waist_pivot_g

    @property
    def covers_g(self) -> dict:
        """Cover mass per piece (g); arm and leg pieces are per side."""
        k = self.shell_mm * PETG_G_PER_MM3 * (1 + self.shell_extra) * self.cover_scale
        out = {name: shell.area_mm2 * k for name, shell in shells(self).items()}
        if self.arms:                     # upper arm: open tube with a round end, the top inside the shoulder cover
            ru = self.upper_arm_cover_r_mm
            out["shoulder"] = ellipsoid_area(*self.shoulder_cover_half_mm) * k
            out["upper_arm"] = (2 * math.pi * ru * self.upper_arm_cyl_mm + 2 * math.pi * ru * ru) * k
        return out

    @property
    def upper_arm_cyl_mm(self) -> float:
        """Straight part of the upper arm cover: it ends 2 mm above the elbow axis (round end included)."""
        return max(0.0, self.upper_arm_mm - 2 - self.upper_arm_cover_r_mm)

    @property
    def covers_total_g(self) -> float:
        c = self.covers_g
        per_side = ("thigh", "shin", "ankle", "shoulder", "upper_arm", "forearm", "wrist", "hand")
        return sum(v * (2 if n in per_side else 1) for n, v in c.items())

    @property
    def servo_count(self) -> int:
        return 2 * (len(self.leg_stops) + (len(ARM_STOPS) if self.arms else 0)) + len(WAIST_STOPS)

    @property
    def total_mass_g(self) -> float:
        c = self.covers_g
        torso = (sum(self.contents_g.values()) + self.torso_struct_g + c["torso"] + self.servo("waist_yaw").mass_g
                 + self.pelvis_struct_g + c["pelvis"])
        leg = (self.thigh_struct_g + self.shin_struct_g + self.ankle_struct_g + self.foot_struct_g
               + c["thigh"] + c["shin"] + c["ankle"] + sum(self.servo(j).mass_g for j in self.leg_stops)
               + (self.hip_roll_struct_g if self.hip_roll else 0.0))
        head = (self.ultrasonic_g + self.camera_reserve_g + c["head"]) if self.head else 0.0
        arm = (self.upper_arm_struct_g + self.forearm_struct_g + self.hand_struct_g
               + c["shoulder"] + c["upper_arm"] + c["forearm"] + c["wrist"] + c["hand"]
               + sum(self.servo(j).mass_g for j in ARM_STOPS)) if self.arms else 0.0
        return torso + 2 * leg + head + 2 * arm


# ---------------------------------------------------------------------- cover shapes
def ellipsoid_area(a: float, b: float, c: float) -> float:
    """Knud Thomsen's approximation (error < 1.1 %)."""
    q = 1.6075
    return 4 * math.pi * (((a * b) ** q + (a * c) ** q + (b * c) ** q) / 3) ** (1 / q)


@dataclass(frozen=True)
class Shell:
    """A convex cover: stacked sections, mounted in a body of the MJCF.

    rings: ((z, half_x, half_y), ...) from bottom to top in the shell frame; each section is a
    superellipse |x/a|^n + |y/b|^n = 1 (n = 2 ellipse, 4 rounded rectangle). pos_mm: where the
    frame sits in the body. The preview draws the convex hull of the ring points; the area is the
    exact area of that polygon loft."""
    body: str
    pos_mm: tuple
    rings: tuple
    n: float = 4.0
    cap_bottom: bool = False
    cap_top: bool = False

    def _ring(self, z, ax, ay, k: int):
        pts = []
        for i in range(k):
            t = 2 * math.pi * i / k
            c, s = math.cos(t), math.sin(t)
            pts.append((ax * math.copysign(abs(c) ** (2 / self.n), c),
                        ay * math.copysign(abs(s) ** (2 / self.n), s), z))
        return pts

    def vertices_mm(self, k: int = 48) -> list:
        return [pt for ring in self.rings for pt in self._ring(*ring, k)]

    @property
    def area_mm2(self, k: int = 96) -> float:
        rings = [self._ring(*ring, k) for ring in self.rings]
        area = 0.0
        for lo, hi in zip(rings, rings[1:]):
            for i in range(k):
                a, b, c, d = lo[i], lo[(i + 1) % k], hi[(i + 1) % k], hi[i]
                area += _tri(a, b, c) + _tri(a, c, d)
        for ring, use in ((rings[0], self.cap_bottom), (rings[-1], self.cap_top)):
            if use:
                area += abs(sum(p[0] * q[1] - q[0] * p[1] for p, q in zip(ring, ring[1:] + ring[:1]))) / 2
        return area


def _tri(a, b, c) -> float:
    u = [b[i] - a[i] for i in range(3)]
    v = [c[i] - a[i] for i in range(3)]
    cx = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    return math.sqrt(sum(x * x for x in cx)) / 2


def _sleeve(p: BipedParams, body: str, length: float, half_x: float, half_y: float, centre_z: float) -> Shell:
    return Shell(body, (0, 0, centre_z), ((-length / 2, half_x, half_y), (length / 2, half_x, half_y)), p.cover_corner_n)


def shells(p: BipedParams) -> dict:
    """The loft-shaped covers (torso, head, leg pieces), each sized to enclose the skeleton inside
    it; the arm covers are capsules and a sphere (BipedParams.covers_g)."""
    tx, ty, tz = p.torso_size_mm
    out = {}
    hx, hy_bottom, hy_top = p.cover_half_mm(tx / 2), p.cover_half_mm(ty / 2), p.cover_half_mm(p.torso_top_width_mm / 2)
    out["torso"] = Shell("torso", (0, 0, 0), (           # open at the hips: the hip servos stay visible
        (-tz / 2 - 2, hx * 0.95, hy_bottom),
        (tz / 2, hx, hy_top),
        (tz / 2 + 6, hx * 0.8, hy_top * 0.8)), p.cover_corner_n, cap_top=True)
    # pelvis: around the hip servo bodies (y out to the hip stacks), mounted in the pelvis body
    px, py = p.cover_half_mm(p.pelvis_depth_mm / 2), p.cover_half_mm(p.pelvis_width_mm / 2)
    out["pelvis"] = Shell("pelvis", (0, 0, 0), ((-p.pelvis_height_mm / 2 - 2, px, py),
                                               (p.pelvis_height_mm / 2, px, py)), p.cover_corner_n)
    if p.head:
        ex, ey, ez = (v / 2 for v in p.head_size_mm)
        levels = [math.sin(math.pi * (i / 12 - 0.5)) for i in range(13)]
        out["head"] = Shell("head", (0, 0, 0), tuple(
            (ez * v, ex * math.sqrt(max(0.0, 1 - v * v)), ey * math.sqrt(max(0.0, 1 - v * v))) for v in levels), 2.0)
    wx, wy = p.leg_cover_half_mm
    out["thigh"] = _sleeve(p, "thigh", p.thigh_mm * p.leg_cover_fraction, wx, wy, -p.thigh_mm / 2)
    out["shin"] = _sleeve(p, "shin", p.shin_mm * p.leg_cover_fraction, wx, wy, -p.shin_mm / 2)
    fx, fy, fz = p.foot_size_mm
    h = p.ankle_link_mm + p.roll_to_sole_mm - fz - 2           # from the foot plate up to the ankle pitch axis
    out["ankle"] = _sleeve(p, "ankle", h, fx * 0.3, fy / 2, -(p.ankle_link_mm + p.roll_to_sole_mm - fz) + h / 2)
    if p.arms:
        fx_, fy_ = p.forearm_cover_half_mm
        wx_, wy_ = p.wrist_cover_half_mm
        top, mid, bottom = 0.0, -ELBOW_HOLDER_DOWN_MM, -p.forearm_mm + 1     # wide around the elbow servo, then slim
        out["forearm"] = Shell("forearm", (0, 0, 0), ((mid - 4, wx_, wy_), (mid, fx_, fy_), (top, fx_, fy_)),
                               p.cover_corner_n)
        out["wrist"] = _sleeve(p, "forearm", mid - bottom, wx_, wy_, (mid + bottom) / 2)
        hx_, hy_ = p.hand_cover_half_mm
        out["hand"] = _sleeve(p, "hand", p.hand_mm - 1, hx_, hy_, -(p.hand_mm + 1) / 2)
    return out
