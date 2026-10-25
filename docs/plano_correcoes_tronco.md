# Plano de correções — tronco, regulador e documentação

Criado em 25/10/2026, a partir da análise do branch `feat/torso-packaging` (trabalho não commitado).
Marque `[x]` ao concluir. Cada item diz **quem** faz: **(você)**, **(Claude)** ou **(juntos)**.
As fases estão em ordem: as decisões da fase 0 mudam medidas e massa, então tudo o que vem
depois espera por elas. Ao terminar, os itens que sobrarem viram linhas no [backlog](backlog.md).

## Ponto de partida (medido em 25/10)

- Tronco 76 × 78 × 68 mm (profundidade × largura no quadril × altura), 86 mm nos ombros. O V da
  armação é só 86 / 78 = 1,10, e a profundidade é quase igual à largura: visto de lado, é um cubo.
- Massa: 569 → **620 g** (+51 g), porque o tronco cresceu e o conteúdo agora é contado peça a peça (116 g).
- Balanço lateral (`rocking_test.py --tilt 12`), antes → agora:

  | passos/s | joelho | tornozelo roll | inclinação |
  |---|---|---|---|
  | 0,33 | 46 → 57 % | 62 → 63 % | 15,7 → 17,0° |
  | 0,50 | 49 → 56 % | 68 → 63 % | 17,0 → 17,5° |
  | 0,67 | 46 → 55 % | 64 → 66 % | 16,7 → 17,9° |
  | 1,00 | 71 → 71 % | 87 → 89 % | 18,5 → **21,4°** |

  A 1 passo/s a inclinação passa do gatilho de ~20° do backlog (F1), que manda rever os 8 DOF.
- `TORSO_LAYOUT` está vazio. Por isso o `torso_layout.py` sem `--search` diz que "todas as peças
  cabem" sem ter checado nada. E o `--search` para no `TODO(human)` da bateria.
- `f1_biped.xml` regenerado = idêntico ao do working tree (código e XML em sincronia).
- O regulador escolhido no código (Pololu D24V90F5, **9 A**) não atende o requisito que os docs já
  pedem (**≥ 10 A**). A troca veio da sugestão de um agente de IA, não de uma conta.

## Fase 0 — Decisões (bloqueiam o resto)

### 0.1 Regulador dos servos

- [x] Orçamento de corrente dos 16 SG90 — feito em 25/10: [alimentacao.md](alimentacao.md), `sim/tools/current_budget.py`. Corrente por servo em três situações: parado, movendo e
      travado (stall do clone, com a faixa nominal do datasheet até a bancada medir). Cenários: em pé,
      balanço lateral, passada e pior caso (servo travado no batente ou na queda). Para cada junta,
      usar os picos de torque da simulação, convertidos em corrente pela curva torque × corrente
      **(Claude)**
- [x] Comparar as opções (recomendação: Pololu D24V150F5 15 A, ver [alimentacao.md](alimentacao.md)), cada uma com massa, corrente contínua e de pico, tensão (5 vs 6 V: torque
      do SG90), queda de tensão no trilho e risco de o ESP32 reiniciar quando a tensão do trilho cai
      (brownout) **(Claude)**:
      - A. Pololu D24V90F5 (5 V, 9 A, ~5 g)
      - B. UBEC ≥ 10 A (~36 g)
      - C. Dois reguladores menores, um para as pernas e outro para os braços. A lista de materiais
        descartou o trilho separado pela fiação extra; reavaliar só se A e B não passarem.
- [x] Decidir o regulador e o fusível que acompanha — 25/10: D24V150F5 nos servos, D24V10F5 na lógica, fusível 7,5 A retardado **(você)**
- [x] Registrar a decisão com o motivo: `lista_materiais.md`, `body.py` (`TORSO_PARTS["regulador"]`:
      medidas, massa, fonte) e backlog §1 **(Claude)**
- [x] ~~Confirmar na bancada da F3 a corrente real de stall do clone~~ → movido para o backlog (F3), depende de hardware **(você)**

### 0.2 Tronco em V suave (silhueta masculina)

- [x] Definir a métrica do V pelo que se vê, **com as capas**, a partir das referências do usuário
      (`docs/img/silhueta01–06.png`, medidas em 25/10; ver abaixo) **(Claude)**

**Métrica (25/10).** Vista de frente, robô de pé, com as capas. Medida por renderização de
segmentação, quase ortográfica; nas variantes, calculada direto das formas das capas (`body.shells`). Larguras:

- **ombros:** largura externa total na altura dos ombros (ombreiras e braços);
- **peito:** capa do tronco na altura das axilas, sem os braços;
- **cintura:** a menor largura da capa do tronco abaixo do peito;
- **quadril:** largura externa na altura do eixo do quadril, com as coxas;
- **cabeça:** largura máxima da cabeça.

Medido nas imagens com as linhas desenhadas por cima e conferido no olho (figura gerada em 25/10;
não vai para o repositório porque as referências têm marca d'água).

| | 01 | 02 | 03 | 05 | 06 | Robô hoje | Meta "V suave" |
|---|---|---|---|---|---|---|---|
| **M1** peito ÷ cintura (o V) | 1,90 | 2,07 | 1,88 | 1,74 | 1,52 | **1,09** (99 / 90 mm) | **≥ 1,5** |
| **M2** ombros ÷ quadril | 2,00 | 1,85 | 1,50 | 2,79 | 1,76 | 1,76 (176 / 100 mm) | manter (≥ 1,5) |
| **M3** ombros ÷ altura | 0,58 | 0,56 | 0,46 | 0,68 | 0,45 | 0,70 (176 / 253 mm) | não piorar (≤ 0,75) |
| **M4** cabeça ÷ peito | 0,61 | 0,49 | 0,66 | 0,39 | 0,67 | 0,59 (58 / 99 mm) | manter |

**O que falta é só a cintura.**
- Ombros contra quadril (M2), largura geral (M3) e cabeça (M4) já estão dentro da faixa das referências.
- O V (M1) é o único fora: 1,09 contra 1,52–2,07.
- Para M1 ≥ 1,5 com o peito de hoje (99 mm), a cintura da capa precisa ficar em **≤ 66 mm** (hoje 90).
  Outra forma é alargar um pouco o peito e afinar menos a cintura.
- A cintura é a base da capa do tronco, acima dos servos do quadril, então ela pode ficar mais
  estreita que o quadril. Com os ombros a 1,76 × o quadril, isso dá V, como nas referências.

Todas as referências são de frente: o perfil lateral (peito ÷ barriga) não tem referência e fica a
critério visual.
- [x] Gerar 3 ou 4 variantes renderizadas de frente e de lado — 25/10, com o tronco novo (só o ESP32 dentro). O ESP32 só cabe com cintura fina se o peito alargar (base 62, ombros 96) e o tronco tiver ≥ 50 mm; variantes A (hoje), B (V, 50 mm), C (V, 55 mm), D (V, 65 mm). Pedido original:
      cintura fina com o tronco mais fundo ou mais alto, e peito um pouco mais largo com cintura média. Para cada uma: se a eletrônica cabe
      (`torso_layout.py --search`), massa, picos do `rocking_test` e folga do braço até a perna **(Claude)**
- [x] Escolher a variante — 25/10: **B** (V, tronco 50 mm) **(você)**
- [x] Aplicar em `BipedParams` — feito em 25/10 (tronco 50 × 62 × 50, ombros 96; ESP32 recolocado no `TORSO_LAYOUT`). Se a escolhida afinar a profundidade de cima para baixo, isso precisa
      de um parâmetro novo no `body.py` (hoje só a largura afina) **(Claude)**

Limites que as variantes têm de respeitar:

- **Cintura:** é a base da capa do tronco, acima dos servos do quadril, então pode ficar mais
  estreita que o quadril. O limite é caber a eletrônica: cintura fina → tronco mais fundo ou mais alto.
- **Quadril:** ~100 mm, fixado pelas pernas. Estreitar exige reabrir o conceito do suporte.
- **Ombros:** mais largos → braço mais pesado e mais longe do centro (mais inércia no balanço lateral)
  e mais folga até a perna (hoje 3 mm).

### 0.3 Posição da bateria

- [x] ~~Tronco~~ Quadril: escrever a preferência da bateria em `score()` — 25/10: atrás e embaixo (`2·x + z`), pela gaveta traseira que você decidiu; o layout do quadril já usa (a bateria foi para o quadril em 25/10; vale para o layout do quadril) (`sim/tools/torso_layout.py`, `TODO(human)`),
      já com as medidas da 0.2 **(você)**. Trade-offs:
      - **Bateria baixa:** centro de massa mais baixo, menos torque no tornozelo roll e no joelho ao
        inclinar. Em compensação o pêndulo fica mais rápido, e o acesso ao conector de carga é pior.
      - **Bateria centrada em X (frente/trás):** evita que o robô fique pendendo para a frente ou
        para trás.
      - **Conector:** o envelope dos cabos precisa ficar perto de uma parede com acesso pela capa.

## Fase 1 — Fechar o tronco no código

- [x] Rodar `torso_layout.py --search` e gravar o resultado em `body.TORSO_LAYOUT` — 25/10: com a divisão tronco/quadril, só o ESP32 fica no tronco (50 × 78 × 45) e cabe **(Claude)**
- [x] Checar o encaixe das peças no quadril — 25/10: `torso_layout.py --seat pelvis`; o menor que cabe é 76 × 92 × 52 (60 × 38 não cabe), bateria encostada na parede de trás (gaveta); gravado em `body.PELVIS_LAYOUT` **(Claude)**
- [x] Corte de torque (25/10): capas 0,8 mm e quadril 76 × 92 × 52 → 612 g, 283 mm; numa perna 80 → 61 %, troca de pé 0,67 passo/s 119 → 108 % (estimativa F2) **(juntos)**
- [x] O modo de checagem falha quando `TORSO_LAYOUT` está vazio ou falta alguma peça de — feito em 25/10 (aponta peça sem posição)
      `TORSO_PARTS`. Hoje ele aprova o que não checou **(Claude)**
- [x] Renomear a variável `body` em `mark_servos` (`torso_layout.py`), que sombreia o módulo `body` — feito em 25/10
      importado, e tirar do filtro os prefixos `pv_battery` / `pv_esp32` / `pv_mpu`, que não existem
      mais **(Claude)**
- [x] `rocking_test.py`: mudar o `--tilt` padrão de 16° para 12° (feito em 25/10). Com 16° o robô cai em qualquer
      ritmo, inclusive na versão de antes **(Claude)**

## Fase 2 — Re-simular e registrar

- [x] Rodar de novo `build_biped.py`, `f1_experiments.py`, `rocking_test.py` e `f2_sweep.py --quick` — 25/10; `--tilt` padrão passou a 9° (12° derruba o robô de 615 g)
      com o tronco final, e conferir que o `f1_biped.xml` regenerado é o que vai no commit **(Claude)**
- [x] Registrar os números novos (massa, picos, inclinação) em `simulacao.md` e
      `arquitetura_corpo.md`, com a comparação antes/depois **(Claude)**
- [x] Rever o gatilho dos 8 DOF com os números novos (decidido em 25/10: ritmo de projeto, não dispara; joelho virou item próprio no backlog): a inclinação a 1 passo/s passou de 20°, mas o
      ritmo de projeto é ~0,67 passo/s. Decidir se o gatilho vale para o ritmo de projeto ou para
      1 passo/s, e escrever isso no backlog **(juntos)**
      Recomendação (25/10): o gatilho vale no ritmo de projeto (0,67 passo/s). Lá a inclinação é 14° e o
      tornozelo roll 56 %, então não dispara; o limite agora é o joelho (79 %), não o roll.

## Fase 3 — Prévia e documentos

- [x] `make preview`, linha nova no histórico de `previa.md` e imagem — 25/10 **(Claude)**
- [x] Sincronizar os números defasados (25/10) **(Claude)**:
      - "569 g": `CLAUDE.md`, `lista_materiais.md`, `arquitetura_perna.md`, `tutorial_mujoco.md`
      - ~~"12 juntas" no backlog~~ (feito em 25/10)
      - ~~"quadris 45 mm, pé 40 × 70" em `backlog.md` e `simulacao.md`~~ (feito em 25/10)
      - ~~"UBEC" em `arquitetura_corpo.md`, backlog e `CLAUDE.md`~~ (feito com a decisão 0.1)
      - tamanho do tronco e V no `CLAUDE.md` e em `arquitetura_corpo.md`
- [x] Backlog §3.1 "Orçamento de massa das capas" (decidido em 25/10: feito pela forma, conferir na F4): decidir se o cálculo pela forma (`body.py`) fecha o
      item ou se ele só fecha na F4, com a massa das peças reais **(juntos)**
      Recomendação (25/10): o orçamento pela forma (133 g com 0,8 mm) vale como orçamento; o item fecha na F4,
      conferindo na balança.

## Fase 4 — Entrega

- [x] Revisão do diff inteiro (código + docs) — 25/10 **(Claude)**
- [ ] Commit e PR do branch `feat/torso-packaging`, depois do seu OK **(Claude)**

## Em paralelo — caminho crítico da mecânica (não depende deste plano)

Já está no backlog §3; listado aqui só para não perder a ordem:

1. Medir o horn ([ficha](medidas_horn_sg90.md)) **(você)**
2. Tutorial do suporte e do garfo **(Claude)**
3. Suporte do servo no FreeCAD **(você)**
