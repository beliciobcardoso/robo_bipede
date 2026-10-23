# Robô bípede

Bípede de 8 DOF com servos SG90, ESP32 e MPU-6050 para equilíbrio.

| Perna (×2) | Junta | Eixo |
|------------|-------|------|
| 1 | Quadril | pitch |
| 2 | Joelho | pitch |
| 3 | Tornozelo | pitch |
| 4 | Tornozelo | roll |

Materiais: [docs/lista_materiais.md](docs/lista_materiais.md).

## CAD

Cada peça é um script Python paramétrico em `cad/parts/<peca>.py` que gera
`cad/build/<peca>.FCStd` e `cad/build/<peca>.step` via FreeCAD 1.1 (flatpak) headless.
Os scripts são a fonte da verdade; `cad/build/` é gerado e não vai para o git.

```bash
make              # gera todas as peças
make servo_sg90   # gera uma peça
make clean
```

Convenções:

- Unidade: mm.
- Peças que fixam um servo usam o sistema de coordenadas do servo:
  origem no eixo de saída, no plano inferior das abas; +Z para o eixo; +X ao longo do corpo.
- Medidas de peças compradas vêm de paquímetro na peça real; o que não foi medido fica marcado `nominal` no script.

| Peça | Script | Status |
|------|--------|--------|
| Servo SG90 clone (referência) | `cad/parts/servo_sg90.py` | medido ([ficha](docs/medidas_servo_sg90.md)) |
| Rolamento 623ZZ 3×10×4 (referência) | `cad/parts/bearing_623zz.py` | d/D/B norma ISO; anéis e encostos nominais |
