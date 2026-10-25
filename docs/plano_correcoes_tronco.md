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
- [ ] Confirmar na bancada da F3 a corrente real de stall do clone. Se passar da margem, voltar a esta
      seção **(você)**

### 0.2 Tronco em V suave (silhueta masculina)

- [ ] Definir a métrica do V pelo que se vê, **com as capas**: largura externa nos ombros ÷ largura
      externa na cintura (vista de frente), e peito ÷ barriga (vista de lado). Medir a do Alpha 1 nas
      fotos como referência **(Claude)**
- [ ] Gerar 3 ou 4 variantes renderizadas de frente e de lado (por exemplo: o V de hoje; ombros mais
      largos; cintura mais fina; peito mais fundo que a barriga). Para cada uma: se a eletrônica cabe
      (`torso_layout.py --search`), massa, picos do `rocking_test` e folga do braço até a perna **(Claude)**
- [ ] Escolher a variante **(você)**
- [ ] Aplicar em `BipedParams`. Se a escolhida afinar a profundidade de cima para baixo, isso precisa
      de um parâmetro novo no `body.py` (hoje só a largura afina) **(Claude)**

Limites que as variantes têm de respeitar:

- **Cintura:** não fica mais estreita que os quadris de 50 mm mais a largura da perna (~42 mm), e
  precisa caber a eletrônica. Cintura fina → tronco mais fundo ou mais alto.
- **Ombros:** mais largos → braço mais pesado e mais longe do centro (mais inércia no balanço lateral)
  e mais folga até a perna (hoje 3 mm).

### 0.3 Posição da bateria

- [ ] Escrever a preferência da bateria em `score()` (`sim/tools/torso_layout.py`, `TODO(human)`),
      já com as medidas da 0.2 **(você)**. Trade-offs:
      - **Bateria baixa:** centro de massa mais baixo, menos torque no tornozelo roll e no joelho ao
        inclinar. Em compensação o pêndulo fica mais rápido, e o acesso ao conector de carga é pior.
      - **Bateria centrada em X (frente/trás):** evita que o robô fique pendendo para a frente ou
        para trás.
      - **Conector:** o envelope dos cabos precisa ficar perto de uma parede com acesso pela capa.

## Fase 1 — Fechar o tronco no código

- [ ] Rodar `torso_layout.py --search` e gravar o resultado em `body.TORSO_LAYOUT` **(Claude)**
- [ ] O modo de checagem falha quando `TORSO_LAYOUT` está vazio ou falta alguma peça de
      `TORSO_PARTS`. Hoje ele aprova o que não checou **(Claude)**
- [ ] Renomear a variável `body` em `mark_servos` (`torso_layout.py`), que sombreia o módulo `body`
      importado, e tirar do filtro os prefixos `pv_battery` / `pv_esp32` / `pv_mpu`, que não existem
      mais **(Claude)**
- [ ] `rocking_test.py`: mudar o `--tilt` padrão de 16° para 12°. Com 16° o robô cai em qualquer
      ritmo, inclusive na versão de antes **(Claude)**

## Fase 2 — Re-simular e registrar

- [ ] Rodar de novo `build_biped.py`, `f1_experiments.py`, `rocking_test.py` e `f2_sweep.py --quick`
      com o tronco final, e conferir que o `f1_biped.xml` regenerado é o que vai no commit **(Claude)**
- [ ] Registrar os números novos (massa, picos, inclinação) em `simulacao.md` e
      `arquitetura_corpo.md`, com a comparação antes/depois **(Claude)**
- [ ] Rever o gatilho dos 8 DOF com os números novos: a inclinação a 1 passo/s passou de 20°, mas o
      ritmo de projeto é ~0,67 passo/s. Decidir se o gatilho vale para o ritmo de projeto ou para
      1 passo/s, e escrever isso no backlog **(juntos)**

## Fase 3 — Prévia e documentos

- [ ] `make preview`, linha nova no histórico de `previa.md` e imagem commitada **(Claude)**
- [ ] Sincronizar os números defasados **(Claude)**:
      - "569 g": `CLAUDE.md`, `lista_materiais.md`, `arquitetura_perna.md`, `tutorial_mujoco.md`
      - "12 juntas" no backlog (são 16)
      - "quadris 45 mm, pé 40 × 70" em `backlog.md` (F2) e `simulacao.md` (agora 50 mm e 45 × 70,
        revistos pelo conceito do suporte)
      - "UBEC" em `arquitetura_corpo.md`, no backlog (§1 e §5) e no `CLAUDE.md`, conforme a decisão 0.1
      - tamanho do tronco e V no `CLAUDE.md` e em `arquitetura_corpo.md`
- [ ] Backlog §3.1 "Orçamento de massa das capas": decidir se o cálculo pela forma (`body.py`) fecha o
      item ou se ele só fecha na F4, com a massa das peças reais **(juntos)**

## Fase 4 — Entrega

- [ ] Revisão do diff inteiro (código + docs) **(Claude)**
- [ ] Commit e PR do branch `feat/torso-packaging`, depois do seu OK **(Claude)**

## Em paralelo — caminho crítico da mecânica (não depende deste plano)

Já está no backlog §3; listado aqui só para não perder a ordem:

1. Medir o horn ([ficha](medidas_horn_sg90.md)) **(você)**
2. Tutorial do suporte e do garfo **(Claude)**
3. Suporte do servo no FreeCAD **(você)**
