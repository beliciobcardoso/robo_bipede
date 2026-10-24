# Arquitetura da perna

> Status: **em construção.** As faixas das juntas abaixo são **provisórias** — serão validadas
> na F5 (passada na simulação). As medidas da perna saem da F2.

## Juntas (por perna)

| # | Junta | Eixo | Gira para |
|---|-------|------|-----------|
| 1 | Quadril | pitch | frente / trás |
| 2 | Joelho | pitch | dobrar / esticar |
| 3 | Tornozelo | pitch | ponta do pé para cima / baixo |
| 4 | Tornozelo | roll | inclinar para o lado |

## Batentes e limites de software

Toda junta tem **dois limites**:

1. **Batente mecânico** — um ressalto desenhado na própria peça impressa, onde as duas peças da
   junta encostam e param. Protege o servo: em queda ou empurrão o impacto vai para o plástico
   impresso, e não para o batente interno e a engrenagem plástica do SG90.
2. **Limite de software** — no firmware (e na simulação), **5° antes do batente**. O motor nunca
   é mandado além dele, então **nunca empurra o batente**. Servo forçando parado puxa ~0,7 A,
   esquenta e desgasta.

| Junta | Batente mecânico | Limite de software | Observação |
|-------|------------------|--------------------|------------|
| Quadril pitch | −30° a +90° | −25° a +85° | +90° = coxa para frente (agachar, subir degrau) |
| Joelho | −120° a +5° | −115° a 0° | só dobra para um lado; batente em +5° impede o joelho de dobrar ao contrário |
| Tornozelo pitch | −45° a +45° | −40° a +40° | limita o agachamento mais fundo (40°) |
| Tornozelo roll | −30° a +30° | −25° a +25° | inclinação lateral para jogar o peso de um pé para o outro |

Convenção de sinal (simulação): agachar é quadril **+**, joelho **−**, tornozelo pitch **+**.

### Regras de projeto do batente

- O batente fica **na peça impressa**, nas duas partes da junta (um ressalto que encosta numa face).
- **Superfície de contato larga e parede grossa** no ponto do batente: ele leva o impacto de
  quedas. Evitar pontas finas ou cantos vivos.
- O batente **não pode depender do servo**: com o servo desmontado, a junta já deve parar no limite.
- O servo é montado com o horn **centralizado** de forma que o curso do servo (~180°) cubra a
  faixa inteira da junta com folga — o batente da peça chega antes do batente interno do servo.
- Na calibração do firmware, encostar a junta à mão no batente serve de referência para achar o
  zero de cada servo.

### O que a simulação já mostrou (modelo de caixinhas, F0)

- Agachando devagar com a regra quadril = A, joelho = −2A, tornozelo = A, o limite é o
  **software do tornozelo em 40°**, com o joelho fazendo 0,067 N·m (37 % do SG90).
- Em operação normal nenhuma junta chega ao batente.

### Deslocar o peso para o lado (resultado da F1)

O robô não tem **quadril roll**. Consequência: com os dois pés no chão, os tornozelos roll ficam
travados, e para apoiar numa perna o **corpo inteiro inclina para o lado** (~18°, faixa estável
10°–26° no modelo de 359 g com quadris a 55 mm). Quadris mais próximos reduzem essa inclinação.
Alternativa a avaliar depois da F2: acrescentar quadril roll (+2 servos, +18 g, 10 DOF) para o
tronco ficar nivelado.

## Medidas da perna

Pendente — sai da varredura na GPU (F2).
