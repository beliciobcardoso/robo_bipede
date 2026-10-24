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

## Passo 5 — Experimento: agachar (com o monitor)

Arrastar os controles até um número exato é difícil. Para este experimento use o **monitor**:
o mesmo visualizador, mas com teclas que põem as juntas na posição exata, o torque mostrado no
terminal e **tudo gravado num arquivo** que eu consigo ler e analisar depois.

Para agachar sem cair, as três juntas de frente/trás se mexem **juntas**, numa regra simples:

> **quadril = A · joelho = −2 × A · tornozelo = A**

Isso dobra o joelho e mantém o tronco em cima do pé (como você agacha: joelho para frente,
quadril e tornozelo compensam). O monitor aplica essa regra sozinho; você só escolhe o **A**.

1. Feche o visualizador que estiver aberto e rode:

   ```bash
   .venv/bin/python sim/tools/monitor.py
   ```

2. Abre a mesma janela. **Clique uma vez dentro da área 3D** — assim as teclas vão para ela.
3. Use as teclas:

   | Tecla | O que faz |
   |-------|-----------|
   | **1** / **2** / **3** / **4** | A = 0 / 0,2 / 0,4 / 0,6 rad |
   | **+** ou **=** | Agacha mais 0,05 rad |
   | **−** | Agacha menos 0,05 rad |
   | **Backspace** | Recomeça com a perna esticada |

   O robô vai até a posição **devagar**, na velocidade de um servo, e não num salto.
4. Olhe o **terminal**: uma linha se atualiza sozinha, assim:

   ```
   t= 12.4s | auto | A=0.40 rad ( 23°) | joelho 0.041 N·m =  23% do SG90 | inclinação  1.6° | tronco 136.2 mm
   ```

   Espere o número do joelho parar de mudar (1–2 segundos) e anote na tabela.
5. Quando terminar, feche a janela. O terminal mostra onde ficou a gravação, algo como
   `log salvo: sim/logs/monitor_20261024_154454.csv`. **Me avise que eu analiso o arquivo.**

| A | Graus | Torque do joelho esperado | % do SG90 | Seu valor |
|---|-------|---------------------------|-----------|-----------|
| 0 (tecla 1) | 0° | 0,000 N·m | 0 % | |
| 0,2 (tecla 2) | 11° | 0,021 N·m | 12 % | |
| 0,4 (tecla 3) | 23° | 0,041 N·m | 23 % | |
| 0,6 (tecla 4) | 34° | 0,059 N·m | 33 % | |
| 0,7 (tecla 4 + duas vezes **+**) | 40° | 0,067 N·m | 37 % | |
| mais **+** | 40° | não passa disso: aparece **limite de software: ankle_pitch** | — | |

Valores calculados rodando a mesma simulação (`sim/tools/monitor.py --sweep`).

### O que o experimento ensina

- **Quanto mais agacha, mais o joelho trabalha.** O peso do tronco fica mais longe do eixo do
  joelho (a alavanca aumenta), então o motor precisa fazer mais torque.
- **Quem limita o agachamento é o limite de software, não a força.** Cada junta tem um
  **batente** (o ponto onde a peça impressa encosta e para) e um **limite de software** 5° antes
  dele. O motor nunca é mandado além do limite de software, então nunca empurra o batente.
  Aqui o primeiro a chegar no limite é o **tornozelo** (40°), com o joelho ainda a 37 % da força.
- **Por que dois limites:** o batente protege o servo em quedas e empurrões — o impacto vai para
  a peça impressa, não para a engrenagem plástica. O limite de software impede o motor de forçar
  contra o batente, o que faria o SG90 puxar muita corrente e esquentar. Se aparecer
  **NO BATENTE** no terminal, foi um impacto (queda, empurrão), não o motor.
- **Movimento rápido derruba.** Se você arrastar os controles do painel **Control** depressa
  (o monitor passa para o modo *manual* quando você mexe neles), o tranco tira o tronco de cima
  do pé e o robô pode cair — mesmo numa posição em que, chegando devagar, ele fica de pé. (Saltar direto de 0 para A = 0,6 derruba; chegar devagar, não.) Isso é
  **dinâmica**: não importa só onde o robô está, mas como ele chegou lá.
- O robô de verdade terá **duas pernas** e massas reais — os números da F1 serão outros.

## Passo 6 (opcional) — Ver as forças no chão

Painel da esquerda → **Rendering** → ligue **Contact Point** e **Contact Force**
(atalhos: teclas **C** e **F**). Aparecem setas saindo do pé: a força com que o chão empurra o robô.

## Passo 7 (opcional) — Empurrar o robô

1. **Duplo clique** no bloco azul (ele fica destacado).
2. Segure **Ctrl** e arraste com o botão **direito**: você empurra o tronco.

**Você deve ver**: o robô balançar e, se empurrar forte, cair. **Backspace** para recomeçar.

---

## Passo 8 — O robô completo (F1)

Até aqui foi um robô de mentira, com uma perna só. Agora o modelo é o **robô inteiro**, ainda
feito de caixinhas, mas com as massas estimadas das peças de verdade (**359 g** no total):

- **caixa laranja** = tronco (bateria, ESP32, MPU-6050, regulador e capa);
- **caixinhas azuis** = os 8 servos SG90, cada um no lugar onde vai ficar;
- **cinza** = coxas, canelas e pés.

1. Feche o visualizador que estiver aberto e rode:

   ```bash
   .venv/bin/python sim/tools/monitor.py --model f1
   ```

2. Clique uma vez na área 3D e use **as mesmas teclas** do Passo 5 (1, 2, 3, 4, +, −, Backspace).
   As **duas pernas** agacham juntas.
3. Anote o torque do joelho no terminal:

| A | Graus | Torque do joelho esperado | % do SG90 | Seu valor |
|---|-------|---------------------------|-----------|-----------|
| 0 (tecla 1) | 0° | 0,000 N·m | 0 % | |
| 0,2 (tecla 2) | 11° | 0,010 N·m | 5 % | |
| 0,4 (tecla 3) | 23° | 0,019 N·m | 10 % | |
| 0,6 (tecla 4) | 34° | 0,027 N·m | 15 % | |
| 0,7 (tecla 4 + duas vezes **+**) | 40° | 0,031 N·m | 17 % | |

**Por que é menos que no Passo 5**, mesmo o robô sendo mais pesado: agora são **duas pernas**
dividindo o peso, e o tronco é mais leve em relação ao total.

### O que eu já medi com este modelo

Rodei os testes que você ainda não consegue fazer pelo visualizador
(`.venv/bin/python sim/tools/f1_experiments.py` — roda sem janela, só texto):

- **Levantar rápido é o que mais exige do servo.** Saindo de 34° de agachamento: em 1,2 s o
  joelho chega a 43 % do SG90; em 0,6 s, 71 %; em 0,3 s, 100 % (o servo não dá conta); em 0,15 s
  o robô cai.
- **Ficar numa perna exige inclinar o corpo inteiro para o lado** (uns 18°), porque o robô não
  tem junta de quadril para o lado. Inclinado assim, o peso fica em cima do pé de apoio e o
  servo trabalha pouco (joelho 11 %). Inclinação menor que 10° ou maior que 26°: tomba.

## Problemas comuns

| Problema | O que fazer |
|----------|-------------|
| A área 3D está vazia/cinza | Feche e abra de novo; se continuar, me mande um print |
| Mexi no controle e nada aconteceu | A simulação está pausada: aperte **Espaço** (o botão **Run** fica verde) |
| No monitor, as teclas 1–4 não fazem nada | Clique uma vez dentro da área 3D antes de apertar |
| Aparece `maior: ankle_roll_l …` no terminal | É a junta que está fazendo mais força naquele momento — normal ao se mexer |
| O robô caiu e não levanta | Normal — ele não sabe levantar. **Backspace** |
| Não acho o campo do **Watch** | Clique na barra **Watch** para abrir a seção |
| O terminal não responde | Ele está esperando a janela fechar. Feche a janela do MuJoCo |
