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
**Decisão (24/10): manter 8 DOF, sem quadril roll.** O robô apoia numa perna inclinando o corpo
inteiro para o lado (andar "rebolado"). Motivos: menos peças, menos peso e menos servos para
calibrar, e na F1 o SG90 trabalhou com folga nessa postura (joelho 11 %, tornozelo roll 2–32 %).
Consequências para as próximas fases:
- a passada (F5) é do tipo "rebolado": inclina para o lado, levanta o pé de fora, dá o passo;
- a **largura do quadril** é a alavanca para reduzir a inclinação — entra na varredura da F2;
- o **tornozelo roll** é a junta que controla o equilíbrio lateral (pé de apoio).

Condições para manter a decisão:
1. **Balanço lateral em movimento:** o pico do tornozelo roll ao inclinar o corpo de um pé para o
   outro, no ritmo da passada, deve ficar abaixo de **~70 % do SG90**.
2. **Inclinação:** depois de afinar a largura do quadril (F2), a inclinação para apoiar numa
   perna deve ficar abaixo de **~20°**.
3. **Quadril modular:** o suporte do quadril e o tronco reservam espaço para um servo de quadril
   roll de cada lado, para que a mudança, se vier, não obrigue a refazer tronco, capas e fiação.

Se 1 ou 2 falhar, a decisão volta para discussão.

**Situação (24/10):**
- Condição 1 — **passa.** Com as medidas aprovadas: tornozelo roll 45 % a 0,5 passo/s e 50 % a 1 passo/s. Antes, com quadris a 55 mm, dava apertado: Balanço lateral sem controle: tornozelo
  roll 53 % a 0,5 passo/s e 61 % a 1 passo/s; passa de 70 % só acima disso (85 % a 1,33 passo/s).
  O joelho chega a 69 % a 1 passo/s. Números preliminares: dependem do amortecimento do servo
  (estimado; a F3 mede) e do padrão de movimento (a F5 refina).
- Condição 2 — **passa.** Com quadris a 45 mm a inclinação para apoiar numa perna fica entre 12° e 16° (F2).
- Condição 3 — entra no projeto do quadril.

## Medidas da perna

> **Aprovadas em 24/10** (proposta da F2). O modelo de simulação `sim/models/f1_biped.xml` já usa estas medidas.

| Medida | Valor | Por quê |
|--------|----------------|---------|
| Distância entre quadris | **45 mm** | Passa a 1 passo/s (deslocar peso 66 %, inclinação 14°). 40 mm seria melhor no torque, mas deixa só ~4 mm entre os conjuntos dos quadris (servo + suporte + rolamento ~36 mm de largura cada), sem espaço para as capas |
| Coxa (quadril → joelho) | **45 mm** | Cabe o servo do joelho (23,6 mm) + suporte + encaixes da capa; joelho a 53 % ao levantar |
| Canela (joelho → tornozelo) | **45 mm** | Idem para o servo do tornozelo; coxa = canela simplifica a cinemática inversa (F5) |
| Largura do pé | **40 mm** | Quadris − 5 mm, para os pés não se tocarem |
| Comprimento do pé | 70 mm | Mantido |
| Massa das capas | **meta 35 g, limite 50 g no total** | Validado a 1 passo/s com 50 g (tronco 20 g + 15 g por perna). Com 100 g o robô perde o ritmo de 1 passo/s |

Altura do centro do tronco em pé: ~148 mm. Massa total estimada: 359 g.

Robô aprovado na simulação (aberto, sem controle de equilíbrio):

| Teste | Resultado |
|-------|-----------|
| Ficar numa perna | inclinação de **14°** (faixa estável 8–20°); joelho 11 %, tornozelo roll até 33 % |
| Balanço lateral a 0,5 passo/s | tornozelo roll **45 %**, joelho 36 % |
| Balanço lateral a 1 passo/s | tornozelo roll **50 %**, joelho 68 % |
| Levantar de 34° em 0,6 s | joelho 53 % |
