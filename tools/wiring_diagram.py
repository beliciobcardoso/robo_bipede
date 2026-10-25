"""Wiring diagram of the robot (docs/esquema_eletrico.md) -> docs/img/esquema_eletrico.{svg,png}.

    .venv/bin/python tools/wiring_diagram.py

Drawn from the pin map below, so the picture and the table in the doc come from the same place:
change a pin here, run again, update the doc table.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Rectangle  # noqa: E402

OUT = Path(__file__).resolve().parents[1] / "docs" / "img" / "esquema_eletrico"

# wire colours
SERVO = "#d62728"     # servo rail 5.25 V (UBEC)
LOGIC = "#ff7f0e"     # 5 V logic (MP1584EN)
V33 = "#bcbd22"       # 3.3 V from the ESP32
I2C = "#1f77b4"
SIG = "#2ca02c"       # PWM / sensor signals
BAT = "#9467bd"       # battery after the switch
GND = "#222222"

# ESP32 pins (torso)
ARM_L = (("ombro pitch E", 13), ("ombro roll E", 14), ("cotovelo E", 25), ("punho E", 26))
ARM_R = (("ombro pitch D", 27), ("ombro roll D", 32), ("cotovelo D", 33), ("punho D", 4))
TRIG, ECHO, BUZZER, SDA, SCL, VBAT_ADC = 18, 19, 16, 21, 22, 35
# PCA9685 channels (pelvis)
LEGS = ("quadril pitch E", "joelho E", "tornozelo pitch E", "tornozelo roll E",
        "quadril pitch D", "joelho D", "tornozelo pitch D", "tornozelo roll D", "cintura (yaw)")
# wires across the waist: (label, colour, x)
WAIST = (("trilho servos 5,25 V", SERVO, 22), ("GND", GND, 30), ("5 V lógica", LOGIC, 66),
         ("3,3 V", V33, 74), ("SDA", I2C, 82), ("SCL", I2C, 88), ("VBAT (sinal)", BAT, 96))


def box(ax, x0, y0, x1, y1, title, lines=(), fc="#f4f4f4", ec="#444", size=8.5):
    ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0.25", fc=fc, ec=ec, lw=1.2))
    ax.text((x0 + x1) / 2, y1 - 1.3, title, ha="center", va="top", fontsize=size + 0.5, weight="bold")
    for k, s in enumerate(lines):
        ax.text((x0 + x1) / 2, y1 - 3.6 - 2.1 * k, s, ha="center", va="top", fontsize=size - 1)


def wire(ax, pts, color, lw=1.8):
    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="round", zorder=1)


def dot(ax, x, y, color):
    ax.plot([x], [y], "o", color=color, ms=4, zorder=3)


def main():
    fig, ax = plt.subplots(figsize=(17, 11))
    ax.set_xlim(0, 160); ax.set_ylim(-4, 102); ax.axis("off")
    ax.text(80, 101.5, "Esquema elétrico do robô bípede — divisão tronco / quadril (25/10/2026)",
            ha="center", va="top", fontsize=14, weight="bold")

    # regions
    ax.add_patch(Rectangle((1, 57), 158, 41, fc="#eef4fb", ec="#7a9cc6", lw=1.5, zorder=0))
    ax.text(3, 96.5, "TRONCO  (gira ±45° na cintura)", fontsize=11, weight="bold", color="#3d5a80")
    ax.add_patch(Rectangle((1, 49), 158, 8, fc="#fff6e0", ec="#c9a227", lw=1.5, zorder=0))
    ax.text(104, 53, "CINTURA — só estes 7 fios cruzam a junta\n(deixar folga em laço para os ±45°)", fontsize=9, color="#8a6d00", va="center")
    ax.add_patch(Rectangle((1, 1), 158, 48, fc="#f1f8ee", ec="#7fb069", lw=1.5, zorder=0))
    ax.text(3, 47, "QUADRIL", fontsize=11, weight="bold", color="#3b6e22")

    # ---------------- torso
    box(ax, 60, 63, 94, 93, "ESP32 DevKit V1", (
        "VIN ← 5 V lógica   ·   3V3 → quadril",
        f"I2C: SDA GPIO{SDA}, SCL GPIO{SCL}",
        "braços: PWM direto (LEDC)",
        f"HC-SR04: TRIG {TRIG}, ECHO {ECHO}",
        f"buzzer GPIO{BUZZER} (via NPN)",
        f"VBAT: GPIO{VBAT_ADC} (ADC1)",
        "USB pela capa (gravação)"), fc="#dfe9f5")
    for side, arms, x0, x1, xpin in (("E", ARM_L, 5, 33, 60), ("D", ARM_R, 127, 155, 94)):
        box(ax, x0, 63, x1, 93, f"Braço {'esquerdo' if side == 'E' else 'direito'} — 4 SG90", fc="#fdebd3")
        for k, (name, gpio) in enumerate(arms):
            y = 86 - 6 * k
            ax.text((x0 + x1) / 2, y, f"{name}  ←  GPIO{gpio}", ha="center", va="center", fontsize=8)
            xs = x1 if side == "E" else x0
            wire(ax, [(xs, y), (xpin, 83 - 3 * k)], SIG, 1.2)
        # servo power for the arm group
        xb = x0 + 3 if side == "E" else x1 - 3
        wire(ax, [(22, 60), (xb, 60), (xb, 63)], SERVO, 2.4)
        wire(ax, [(30, 59), (xb + (2 if side == "E" else -2), 59), (xb + (2 if side == "E" else -2), 63)], GND, 1.4)
    box(ax, 98, 86, 124, 96, "HC-SR04 (cabeça)", ("VCC 5 V lógica · TRIG, ECHO", "ECHO por divisor 1 k / 2 k → 3,3 V"), fc="#e4ecf7")
    wire(ax, [(94, 79), (101, 79), (101, 86)], SIG, 1.2)
    box(ax, 98, 66, 116, 74, "Buzzer ativo", ("NPN + 1 k na base",), fc="#e4ecf7")
    wire(ax, [(94, 70), (98, 70)], SIG, 1.2)

    # ---------------- waist wires
    for label, color, x in WAIST:
        wire(ax, [(x, 45 if x != 96 else 9), (x, 61 if x != 30 else 59)], color, 2.6 if color in (SERVO, GND) else 1.8)
        ax.text(x + 0.6, 52.5, label, fontsize=7.5, rotation=90, va="center", color=color, weight="bold")
    wire(ax, [(66, 61), (66, 63)], LOGIC); wire(ax, [(74, 61), (74, 63)], V33)
    wire(ax, [(82, 61), (82, 63)], I2C); wire(ax, [(88, 61), (88, 63)], I2C); wire(ax, [(96, 61), (92, 63)], BAT)
    wire(ax, [(66, 61), (66, 62), (111, 62), (111, 86)], LOGIC, 1.4)   # 5 V to the HC-SR04

    # ---------------- pelvis: power
    box(ax, 3, 30, 19, 42, "Bateria 2S", ("7,4 V (8,4 cheia)", "XT30 + JST-XH", "gaveta traseira"), fc="#ece2f6")
    box(ax, 22, 33, 30, 40, "Fusível", ("7,5 A lento",), fc="#ece2f6", size=7.5)
    box(ax, 33, 33, 41, 40, "Chave", ("liga/desl.",), fc="#ece2f6", size=7.5)
    wire(ax, [(19, 36.5), (22, 36.5)], BAT, 2.6); wire(ax, [(30, 36.5), (33, 36.5)], BAT, 2.6)
    wire(ax, [(41, 36.5), (46, 36.5)], BAT, 2.6); dot(ax, 46, 36.5, BAT)
    wire(ax, [(46, 36.5), (46, 19), (49, 19)], BAT, 1.8)
    wire(ax, [(46, 19), (46, 7), (49, 7)], BAT, 1.2)
    box(ax, 49, 31, 63, 42, "UBEC 5 V / 7 A", ("entrada 5,5–26 V", "saída 5,25 V", "trilho dos 17 servos"), fc="#fbe3e3")
    wire(ax, [(46, 36.5), (49, 36.5)], BAT, 2.6)
    box(ax, 49, 14, 63, 24, "MP1584EN", ("5,0 V lógica (ajustar", "e travar o trimpot);", "depois da chave"), fc="#fdebd3")
    box(ax, 49, 3, 63, 11, "Divisor VBAT", ("100 k / 33 k", "8,4 V → 2,1 V"), fc="#ece2f6", size=7.5)
    wire(ax, [(63, 7), (96, 7), (96, 9)], BAT, 1.2)
    # servo rail and caps
    wire(ax, [(63, 38), (70, 38), (70, 45), (22, 45)], SERVO, 2.6)      # up to the waist
    box(ax, 68, 26, 82, 34, "2 × 1000 µF", ("no trilho, perto", "do PCA9685"), fc="#fbe3e3", size=7.5)
    wire(ax, [(70, 38), (70, 34)], SERVO, 2.0)
    wire(ax, [(70, 38), (98, 38)], SERVO, 2.6)
    wire(ax, [(63, 19), (66, 19), (66, 45)], LOGIC, 1.8)
    # ---------------- pelvis: PCA9685, MPU, leg servos
    box(ax, 98, 15, 124, 43, "PCA9685 (0x40)", (
        "V+ ← trilho 5,25 V (borne)", "VCC ← 3,3 V (não 5 V!)", "SDA / SCL ← ESP32",
        "OE: deixar solto", "canais 0–8 → servos", "liga desligado: firmware", "liga em grupos de 2–4"), fc="#dfe9f5")
    wire(ax, [(74, 45), (74, 41), (98, 41)], V33, 1.6)
    wire(ax, [(82, 45), (82, 40), (98, 40)], I2C, 1.6)
    wire(ax, [(88, 45), (88, 39.2), (98, 39.2)], I2C, 1.6)
    box(ax, 72, 12, 92, 22, "MPU-6050 (0x68)", ("VCC 3,3 V · AD0 → GND", "fica no quadril: presa às pernas"), fc="#e4ecf7", size=7.5)
    wire(ax, [(74, 41), (76, 41), (76, 22)], V33, 1.2)
    wire(ax, [(82, 40), (84, 40), (84, 22)], I2C, 1.2)
    wire(ax, [(88, 39.2), (88, 22)], I2C, 1.2)
    box(ax, 128, 4, 157, 45, "Pernas + cintura — 9 SG90", fc="#fdebd3")
    for ch, name in enumerate(LEGS):
        y = 39.5 - 3.9 * ch
        ax.text(142.5, y, f"canal {ch}  →  {name}", ha="center", va="center", fontsize=8)
        wire(ax, [(124, 34 - 2 * ch), (128, y)], SIG, 1.0)
    # ground bus
    wire(ax, [(3, 2.2), (157, 2.2)], GND, 1.6)
    ax.text(80, 0.9, "todos os módulos e servos ligam o GND neste barramento comum", ha="center", fontsize=8)
    wire(ax, [(11, 2.2), (11, 30)], GND, 1.4)                              # battery -
    wire(ax, [(30, 45), (30, 44), (1.8, 44), (1.8, 2.2), (3, 2.2)], GND, 2.4)   # waist GND, around the battery

    # legend
    items = ((SERVO, "trilho dos servos 5,25 V (fio 20 AWG)"), (LOGIC, "5 V lógica"), (V33, "3,3 V"),
             (I2C, "I2C (SDA / SCL)"), (SIG, "PWM / sinais"), (BAT, "bateria após a chave"), (GND, "GND comum"))
    x = 4
    for c, s in items:
        ax.plot([x, x + 3], [-2.6, -2.6], color=c, lw=3)
        ax.text(x + 3.6, -2.6, s, va="center", fontsize=8.5)
        x += 6 + 0.95 * len(s)
    fig.savefig(OUT.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(OUT.with_suffix(".png"), dpi=90, bbox_inches="tight")
    print(f"-> {OUT.with_suffix('.svg')} / .png")


if __name__ == "__main__":
    main()
