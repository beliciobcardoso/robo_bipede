# Medidas do servo SG90 / MG90S

Ficha para conferir com paquímetro as dimensões usadas em [`cad/parts/servo_sg90.py`](../cad/parts/servo_sg90.py).
Preencha a coluna **Medido** (mm). Se alguma medida der trabalho, deixe em branco que mantém o valor nominal.

**Modelo:** clone de SG90 (engrenagem plástica)

> Clones variam alguns décimos de mm em relação ao SG90 original — por isso a medição.
>
> **Valores em uso: coluna Remedido (24/10)** — refeitos com paquímetro melhor e modelados à mão em
> `cad/manual/servo_sg90.FCStd`. O item 4 é derivado: torre rente à parede → `tower_d / 2`.
> Ressalto da engrenagem (do modelo manual): Ø5,5 a 7,0 mm do eixo, mesma altura da torre.
> Furo do parafuso do eixo: Ø2,0 × 3,0.

## Corpo

Servo deitado de lado, sem horn.

| # | Medida | Como medir | Nominal | Medido (23/10) | **Remedido (24/10)** |
|---|--------|-----------|---------|--------|--------|
| 1 | Comprimento do corpo (`body_l`) | Ponta a ponta do corpo, sem as abas | 22,8 | 23,1 | **23,0** |
| 2 | Largura do corpo (`body_w`) | Lado a lado | 12,2 | 12,2 | **12,0** |
| 3 | Altura do corpo (`body_h`) | Da base até a face de cima da caixa, sem a torre | 22,7 | 24,2 | **24,0** |
| 4 | Distância do eixo à ponta (`shaft_offset`) | Da face da ponta do lado do eixo até o centro do eixo | 6,1 | ~~5,5~~ 6,0 | **6,0** |

## Abas de fixação

| # | Medida | Como medir | Nominal | Medido (23/10) | **Remedido (24/10)** |
|---|--------|-----------|---------|--------|--------|
| 5 | Comprimento total das abas (`tab_l_total`) | Da ponta de uma aba à ponta da outra | 32,2 | 32,5 | **33,0** |
| 6 | Espessura da aba (`tab_t`) | Espessura de uma aba | 2,5 | 2,5 | **2,5** |
| 7 | Altura da aba (`tab_bottom_z`) | Da base do corpo até a face **de baixo** da aba | 15,9 | 17,00 | **17,0** |
| 8 | Distância entre furos (`hole_spacing`) | Centro a centro. Mais fácil: borda externa a borda externa menos o diâmetro de um furo | 27,8 | 27,8 | **28,0** |
| 9 | Diâmetro do furo (`hole_d`) | Diâmetro de um furo | 2,0 | 2,0 | **2,0** |

## Topo (torre e eixo)

| # | Medida | Como medir | Nominal | Medido (23/10) | **Remedido (24/10)** |
|---|--------|-----------|---------|--------|--------|
| 10 | Diâmetro da torre (`tower_d`) | Cilindro grande em volta do eixo | 11,8 | 12,0 | **12,0** |
| 11 | Altura da torre (`tower_h`) | Da face de cima da caixa até o topo da torre | 4,0 | 4,0 | **4,0** |
| 12 | Diâmetro do eixo (`shaft_d`) | Por cima dos dentes do spline | 4,8 | 5,0 | **5,0** |
| 13 | Altura do eixo (`shaft_h`) | Do topo da torre até o topo do eixo | 3,0 | 3,0 | **3,0** |
| 14 | Altura total | Da base até o topo do eixo. Serve só para conferir as medidas 3, 11 e 13 | 29,7 | 31,2 | **31,0** |
| 15 | Dentes do spline | Contar, se der (normalmente 20 ou 21) | — | 21 | **21** |

## Cabo

| # | Medida | Como medir | Nominal | Medido (23/10) | **Remedido (24/10)** |
|---|--------|-----------|---------|--------|--------|
| 16 | Lado de saída do cabo | O cabo sai pela ponta do lado do eixo ou pela ponta oposta? | oposto | eixo | **eixo** |
| 17 | Altura do cabo (`cable_z`) | Da base do corpo até o centro do cabo, onde ele sai | 4,5 | 4,0 | **— (mantido 4,0)** |
| 18 | Largura do cabo (`cable_w`) | Largura do conjunto de 3 fios | 3,6 | 4,0 | **— (mantido 4,0)** |

## Prioridade

As medidas **1, 3, 5, 7 e 8** são as mais críticas, porque definem o encaixe no suporte.
