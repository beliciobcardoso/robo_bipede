# Tutorial: primeiros passos no MuJoCo

Para quem nunca usou simulador de física. Cada passo diz **onde clicar**, **o que fazer** e
**o que você deve ver**. Os nomes dos painéis estão exatamente como aparecem na janela.

---

## Parte 1 — O que é o MuJoCo

O MuJoCo é um **laboratório virtual de física**. Você descreve o robô num arquivo de texto
(peças, juntas, motores) e ele calcula, passo a passo, como tudo se move: gravidade puxando,
pé encostando no chão, motor fazendo força.

Para que serve no nosso projeto: testar o robô **antes** de imprimir. Por exemplo, saber se o
SG90 aguenta o robô agachado, ou se a perna cai, sem quebrar nenhuma peça de verdade.

## Parte 2 — Vocabulário

| Palavra | O que é |
|---------|---------|
| **Modelo** | O arquivo `.xml` que descreve o robô. O nosso: `sim/models/f0_smoke.xml`. |
| **Corpo** (body) | Uma peça rígida com massa: o tronco, a coxa, a canela, o pé. |
| **Junta** (joint) | A dobradiça entre duas peças. A nossa perna tem 4: quadril, joelho, tornozelo pitch, tornozelo roll. |
| **Atuador** (actuator) | O motor de cada junta. Aqui ele imita o SG90: recebe um **ângulo** e tenta chegar nele. |
| **Torque** | A "força de giro" que o motor faz, em **N·m** (newton-metro). O SG90 aguenta no máximo **0,18 N·m**. |
| **Radiano** (rad) | Unidade de ângulo que o MuJoCo usa. **1 rad ≈ 57°**. 0,4 rad ≈ 23°. 1,57 rad = 90°. |
| **Passo** (step) | Um "quadro" do cálculo. O nosso modelo calcula a cada 2 milésimos de segundo. |

## Parte 3 — O nosso modelo de teste

Um robô de mentira, só para aprender:

- **bloco azul** = tronco. Representa o peso do robô (200 g).
- **perna cinza** = coxa, canela, tornozelo e pé, feitos de caixinhas.
- **uma perna só.** É de propósito: é o caso mais difícil, o robô apoiado numa perna enquanto a outra dá o passo.

## Parte 4 — A janela

```
┌──────────────┬─────────────────────────────────────┬──────────────┐
│ File         │                                     │ Joint        │
│ Option       │                                     │ Control      │
│ Simulation   │          área 3D (o robô)           │ Equality     │
│ Watch        │                                     │              │
│ Physics      │                                     │              │
│ Rendering    │                                     │              │
│ Visualization│                                     │              │
│ ...          │                                     │              │
└──────────────┴─────────────────────────────────────┴──────────────┘
```

Clique no **nome** de uma seção (barra vermelha) para abrir ou fechar.

| Seção | Para que serve agora |
|-------|----------------------|
| **Simulation** (esquerda) | Botões **Pause** / **Run** e **Reset** (recomeçar do zero) |
| **Watch** (esquerda) | Mostrar um número da simulação, ex.: o torque do joelho |
| **Rendering** (esquerda) | Ligar desenhos extras, ex.: as forças no chão |
| **Joint** (direita) | Mostra o ângulo atual de cada junta (só leitura enquanto roda) |
| **Control** (direita) | **Os comandos dos motores**: um controle deslizante por junta |

As outras seções (Physics, Visualization, Group enable, Logging, Equality) não precisam ser
mexidas agora.

### Mouse e teclado

| Ação | Como |
|------|------|
| Girar a câmera | Botão **esquerdo** + arrastar no fundo |
| Mover a câmera | Botão **direito** + arrastar |
| Zoom | **Roda** do mouse |
| Pausar / continuar | **Espaço** |
| Recomeçar do zero | **Backspace** |
| Avançar um passo (pausado) | Seta **→** |
| Esconder / mostrar painéis | **Tab** (esquerdo), **Shift+Tab** (direito) |

---

## Passo 1 — Abrir

```bash
.venv/bin/python -m mujoco.viewer --mjcf=sim/models/f0_smoke.xml
```

**Você deve ver**: o bloco azul em cima da perna, de pé, no chão quadriculado. Ele cai alguns
milímetros no começo e para — é a perna se acomodando no chão.

O terminal fica "preso" enquanto a janela estiver aberta. Normal. Para sair: feche a janela
(ou **File → Quit**).

## Passo 2 — Girar a câmera

Com o botão esquerdo, arraste no fundo cinza e dê a volta no robô. Use a roda para chegar
perto. Se se perder: **Backspace** recomeça a simulação; feche e abra de novo para a câmera voltar.

## Passo 3 — Mexer uma junta

1. Painel da direita → clique em **Control** para abrir.
2. Aparecem 4 controles deslizantes: **hip_pitch** (quadril), **knee** (joelho),
   **ankle_pitch** (tornozelo frente/trás), **ankle_roll** (tornozelo para o lado).
3. Arraste o **ankle_roll** devagar para um lado.

**Você deve ver**: o robô inclinar para o lado. Solte e volte o controle para o meio (0).

Os valores estão em **radianos**: o controle vai de −1,57 a +1,57 (−90° a +90°).

## Passo 4 — Ver o torque do joelho

1. Painel da esquerda → clique em **Watch** para abrir.
2. Campo **Field**: digite `actuator_force`
3. Campo **Index**: digite `1`
   (os motores são numerados a partir de 0: **0** quadril, **1** joelho, **2** tornozelo pitch, **3** tornozelo roll)
4. Ao lado aparece o **valor**: é o torque que o motor do joelho está fazendo, em N·m.

Com a perna esticada, deve ficar perto de **0** — o peso passa reto pelos ossos, o motor
quase não trabalha.

## Passo 5 — Experimento: agachar

Para agachar sem cair, as três juntas de frente/trás se mexem **juntas**, numa regra simples:

> **quadril = A · joelho = −2 × A · tornozelo = A**

Isso dobra o joelho e mantém o tronco em cima do pé (como você agacha: joelho para frente,
quadril e tornozelo compensam).

1. **Backspace** para recomeçar.
2. No **Control**, ponha os três valores de uma linha da tabela (clique no controle e arraste;
   olhe o número ao lado).
3. Espere 2–3 segundos e anote o torque do joelho no **Watch**.

| A | quadril (hip_pitch) | joelho (knee) | tornozelo (ankle_pitch) | Torque do joelho esperado | Seu valor |
|---|---|---|---|---|---|
| 0 | 0 | 0 | 0 | ~0,00 N·m | |
| 0,2 (≈ 11°) | 0,2 | −0,4 | 0,2 | ~0,02 N·m | |
| 0,4 (≈ 23°) | 0,4 | −0,8 | 0,4 | ~0,04 N·m (≈ 23 % do SG90) | |
| 0,6 (≈ 34°) | 0,6 | −1,2 | 0,6 | **o robô cai** | |

O valor esperado eu calculei rodando a mesma simulação. Pequenas diferenças são normais — mexer
os controles com o mouse não é exato.

### O que o experimento ensina

- **Quanto mais agacha, mais o joelho trabalha.** O peso do tronco fica mais longe do eixo do
  joelho (a alavanca aumenta), então o motor precisa fazer mais torque.
- **Por que ele cai em 0,6**: em pé numa perna só, com um pé pequeno, qualquer desequilíbrio
  derruba. Agachando mais, o motor do joelho cede um pouco (ele é fraco, como o SG90), o tronco
  sai de cima do pé e o robô tomba. Isso é exatamente o que o **equilíbrio com o MPU-6050** vai
  corrigir mais adiante.
- O robô de verdade terá **duas pernas** e massas reais — os números da F1 serão outros.

## Passo 6 (opcional) — Ver as forças no chão

Painel da esquerda → **Rendering** → ligue **Contact Point** e **Contact Force**
(atalhos: teclas **C** e **F**). Aparecem setas saindo do pé: a força com que o chão empurra o robô.

## Passo 7 (opcional) — Empurrar o robô

1. **Duplo clique** no bloco azul (ele fica destacado).
2. Segure **Ctrl** e arraste com o botão **direito**: você empurra o tronco.

**Você deve ver**: o robô balançar e, se empurrar forte, cair. **Backspace** para recomeçar.

---

## Problemas comuns

| Problema | O que fazer |
|----------|-------------|
| A área 3D está vazia/cinza | Feche e abra de novo; se continuar, me mande um print |
| Mexi no controle e nada aconteceu | A simulação está pausada: aperte **Espaço** (o botão **Run** fica verde) |
| O robô caiu e não levanta | Normal — ele não sabe levantar. **Backspace** |
| Não acho o campo do **Watch** | Clique na barra **Watch** para abrir a seção |
| O terminal não responde | Ele está esperando a janela fechar. Feche a janela do MuJoCo |
