# Simulação e algoritmos — plano

Objetivo: testar mecânica e controle no computador **antes** de imprimir e montar, usando a
RTX 3060 (12 GB) onde ela faz diferença, e evoluir junto com o aprendizado de modelagem e robótica.

> Status: plano **aprovado** (24/10). **F0, F1 e F2 concluídas** — resultados abaixo.

## Resultado da F0 (24/10)

Teste: `sim/tools/smoke_test.py` com `sim/models/f0_smoke.xml` (tronco + 1 perna de 4 juntas de
caixinhas agachando), 1 s simulado = 500 passos.

| Onde | Robôs em paralelo | Passos/s | × CPU | Resultado igual à CPU? |
|------|------------------:|---------:|------:|------------------------|
| CPU (1 núcleo) | 1 | ~66 mil | 1 | — |
| GPU, motor JAX | 4 096 | ~196 mil | 3,0 | sim (0,04 mm) |
| GPU, motor JAX | 16 384 | ~207 mil | 3,1 | sim (0,04 mm) |
| GPU, motor **Warp** | 4 096 | ~3,7 milhões | 56 | sim (0,000 mm) |
| GPU, motor **Warp** | 16 384 | **~4,7 milhões** | **71** | sim (0,000 mm) |

Compilação: motor JAX 13–52 s por tamanho de lote; motor Warp 1–3 s.

Conclusões:
- **Usar o motor Warp** do MJX (NVIDIA) no modo de captura `WARP`. O modo padrão falha nesta
  combinação driver/CUDA, e o Warp é ~19–23× mais rápido que o motor JAX e compila em segundos.
- A GPU só compensa com **muitos robôs em paralelo**: com 1 robô a CPU é muito mais rápida.
  Para ver e depurar um robô, CPU; para varreduras e treino, GPU.
- Sanidade física: agachado sobre uma perna, o joelho pede 0,043 N·m (24 % do SG90) neste
  modelo de caixinhas — número a ser refeito com massas reais na F1/F2.
- Versões fixadas em `requirements.txt`.

## Resultado da F1 (24/10) — robô completo de caixinhas

Modelo `sim/models/f1_biped.xml`, gerado por `sim/tools/build_biped.py` a partir de parâmetros
(comprimentos em mm, massas em g). Duas pernas × 4 juntas, **359 g** no total, coxa e canela de
45 mm, quadris a 55 mm um do outro. Testes em `sim/tools/f1_experiments.py` e `monitor.py --model f1 --sweep`.

| Situação | Junta mais exigida | % do SG90 |
|----------|--------------------|-----------|
| Em pé, duas pernas | — | 0 % |
| Agachado 40° (limite), duas pernas, parado | joelho | 17 % |
| Levantar de 34° em 1,2 s | joelho (pico) | 34 % |
| Levantar de 34° em 0,6 s | joelho (pico) | 53 % |
| Levantar de 34° em 0,3 s | joelho (pico) | 90 % |
| Levantar de 34° em 0,15 s | joelho | **100 % — servo no limite** |
| Numa perna, inclinado 18° (meio da faixa estável) | joelho / tornozelo roll | 11 % / 2 % |
| Numa perna, nas bordas da faixa (10° ou 26°) | tornozelo roll | 40 % |
| **Balanço lateral** a 0,5 passo/s (sem controle de equilíbrio) | tornozelo roll / joelho | 53 % / 36 % |
| Balanço lateral a 1 passo/s | tornozelo roll / joelho | 61 % / 69 % |
| Balanço lateral a 1,33 passo/s | tornozelo roll / joelho | 85 % / 90 % |

Amortecimento das juntas no modelo: **0,017 N·m·s/rad**, estimado pelo próprio SG90 (torque de
travamento ÷ velocidade sem carga = 0,18 ÷ 10,5). Representa a perda de força com a velocidade.
Um primeiro chute de 0,05 inflava os picos em movimento em até ~30 pontos. A F3 (bancada) mede o
valor real.

Conclusões:
- **Parado, o SG90 sobra.** O que aperta é **movimento rápido**: levantar em ~0,3 s já leva o
  joelho a 90 %. A passada (F5) precisa respeitar essa velocidade.
- **Balanço lateral** (`sim/tools/rocking_test.py`): o robô passa o peso de um pé para o outro e
  levanta o pé livre ~22 mm **sem controle de equilíbrio** até 1,33 passo/s. O tornozelo roll fica
  abaixo de 70 % até **1 passo/s** (61 %); o joelho chega a 69 % nesse ritmo. **Ritmo-alvo da
  primeira passada: 0,5 passo/s; teto: 1 passo/s.** Os picos dependem bastante do padrão de
  movimento (empurrar menos e levantar menos o pé reduz o joelho de 100 % para 69 %) — a F5 vai
  refinar.
- **Sem quadril roll, ficar numa perna exige inclinar o corpo inteiro ~18° para o lado** (faixa
  estável de 10° a 26°). Com os dois pés no chão, os tornozelos roll ficam travados — não dá para
  deslocar o peso para o lado sem tirar um pé. É o andar "rebolado" (tipo Otto).
- A inclinação necessária depende da **largura do quadril** e da altura do centro de massa:
  quadris mais próximos pedem menos inclinação. Isso entra na varredura da F2.

## Resultado da F2 (24/10) — varredura de medidas

`sim/tools/f2_sweep.py`: 360 robôs (coxa e canela de 35 a 60 mm, quadris de 40 a 60 mm, capas
nominais e pesadas) em **12 s** nos 28 núcleos da CPU. Resultados em `sim/results/f2_sweep.csv`
e `sim/results/f2_sweep.png`.

**Por que CPU e não GPU aqui:** cada combinação é um robô com geometria diferente, simulado
poucas vezes. A GPU ganha quando é o mesmo robô milhares de vezes (robustez, treino da F7).

**Como o deslocamento de peso foi medido:** o balanço lateral sem controle de equilíbrio
(`rocking_test.py`) depende demais do padrão de movimento para comparar projetos. Usei a física:
o tornozelo de apoio precisa girar o robô inteiro sobre o pé, torque ≈ m·g·(distância entre
quadris ÷ 2) + inércia × aceleração. No robô da F1 a estimativa deu 61 % contra 53 % medidos
— **conservadora**.

| Quadris | Inclinação numa perna | Deslocar peso a 0,5 passo/s | a 1 passo/s | Passam a 1 passo/s |
|---------|----------------------|-----------------------------|-------------|--------------------|
| 40 mm | 10–16° | 44–45 % | 57–63 % | 36 de 36 |
| **45 mm** | **12–16°** | **49–51 %** | **63–70 %** | **34 de 36** |
| 50 mm | 14–18° | 54–57 % | 71–80 % | 0 de 36 |
| 55 mm (F1) | 14–20° | 60–62 % | 78–86 % | 0 de 36 |
| 60 mm | 16–22° | 66–68 % | 86–95 % | 0 de 36 |

Conclusões:
- **A largura do quadril decide.** O esforço para deslocar o peso cresce em linha reta com ela;
  o comprimento das pernas quase não muda.
- **Pernas mais longas pedem menos inclinação** (centro de massa mais alto em relação aos pés),
  mas aumentam o esforço do joelho ao levantar (coxa 40 mm: 51 %; coxa 50 mm: 55 %).
- **As capas pesam na conta:** com capas pesadas (100 g em vez de 50 g, 409 g no total) nenhuma
  combinação a 45 mm passa a 1 passo/s (74–77 %); todas continuam passando a 0,5 passo/s.
- **Medidas aprovadas (24/10):** quadris 45 mm, coxa = canela = 45 mm, pé 40 × 70 mm, capas
  com meta de 35 g e limite de 50 g.
- **Revisão no conceito do suporte (24/10):** com as peças reais a perna tem ~42 mm de largura,
  então os quadris foram para **50 mm** (pé 45 mm) e o tornozelo pitch→roll de 12 para **22 mm**.
  A estimativa física conservadora da tabela acima marca 50 mm como reprovado a 1 passo/s (71–80 %),
  mas o balanço simulado no robô atualizado dá **tornozelo roll 57 %** e joelho 69 % a 1 passo/s,
  e 50 % / 36 % a 0,5 passo/s; inclinação numa perna 14°. As duas condições dos 8 DOF passam.
- **Cabeça e braços (24/10):** HC-SR04 + 10 g de reserva para câmera e 2 servos por braço levam o robô
  a 450 g com as 2× 18650 — a 0,5 passo/s a faixa de balanço que não tomba encolhe de 10–16° para
  10–14°. Com LiPo de 55 g: **410 g**, tornozelo roll **57 % / 64 %** e joelho 36 % / 68 % a 0,5 / 1
  passo/s (roll 14°); numa perna equilibra entre −18° e −8°. Aprovado.
- **Corpo inteiro com capas calculadas (24/10):** capas pela forma (164 g) e proporção estilo Alpha 1
  com SG90 em tudo (`body_variants.py`, 72 variantes): **518 g, 254 mm** — é o modelo F1 atual.
  A roll ±12°: tornozelo roll 64 / 70 % e joelho 43 / 70 % a 0,5 / 1 passo/s; uma perna entre −14° e −10°;
  levantar a 1 rad/s com joelho a 67 %. Ritmo com folga até ~0,7 passo/s.
- **Braços com cotovelo e punho (24/10):** 16 servos, 573 g (569 g com as capas quase retas, mesmos picos). A roll ±12°: tornozelo roll 68 / 64 / 87 % e
  joelho 50 / 46 / 71 % a 0,5 / 0,67 / 1 passo/s; levantar a 1 rad/s com joelho a 72 %. Ritmo até ~0,67 passo/s.

 usar o que existe, medir, só então criar

1. Começa com ferramenta aberta e consolidada.
2. Mede contra o robô real (ou contra uma conta conhecida).
3. **Cria algoritmo próprio só quando** um destes for verdade:
   - nenhuma ferramenta modela aquilo (ex.: o comportamento do *nosso* SG90 clone);
   - a ferramenta diverge da medição real além do aceitável, e a causa é a ferramenta;
   - o objetivo é aprender (fazer à mão uma vez para entender, depois comparar com a pronta).
4. Todo algoritmo próprio é comparado (A/B) com a solução pronta, com números.

**Não vamos escrever motor de física.** É um trabalho de anos, e o MuJoCo já é referência na área.
O que vale a pena ser nosso é o que ninguém tem pronto para este robô.

## 2. Ferramentas

| Ferramenta | Para quê | CPU/GPU |
|------------|----------|---------|
| **MuJoCo** | Motor de física padrão em robôs com pernas. Visualizador para ver e mexer no robô. | CPU (rápido) |
| **MJX** (MuJoCo em JAX) | Mesma física, rodando **milhares de robôs em paralelo** na placa de vídeo. Motor **Warp** (NVIDIA) — escolhido na F0. | **GPU** |
| **MuJoCo Playground / Brax** | Treino de andar por aprendizado por reforço (PPO) em cima do MJX. | **GPU** |
| **CuPy** | Cálculos próprios na GPU (já usado em `tools/compare_meshes.py`). | **GPU** |
| **Isaac Lab** (NVIDIA) | Alternativa mais pesada. Fica para depois, só se o MJX não der conta. | GPU |

Por que MuJoCo/MJX e não Isaac Lab primeiro: instala com `pip` no `.venv` que já existe,
é leve, roda bem em 12 GB, e o mesmo modelo serve para ver (CPU) e para treinar (GPU).
Isaac exige instalação de dezenas de GB e é mais do que precisamos agora.

## 3. Onde a placa de vídeo ajuda (e onde não)

| Ajuda muito | Não precisa |
|-------------|-------------|
| **Varreduras**: testar centenas de combinações (comprimento da perna × postura × peso) e ver qual dá folga de torque | Ver o robô se mexendo na tela (CPU dá conta) |
| **Robustez (Monte Carlo)**: o mesmo passo com milhares de variações de massa, folga do servo, atrito | Cinemática inversa de uma perna (conta pequena) |
| **Treinar o andar por reforço**: milhares de robôs simulados aprendendo ao mesmo tempo | Firmware do ESP32 |
| Comparar peças do CAD (já fazemos) | |

## 4. O que será nosso (algoritmos próprios planejados)

| Peça | Por que não tem pronto | Como valida |
|------|------------------------|-------------|
| **Modelo do SG90 clone** — torque × velocidade, folga das engrenagens, zona morta, atraso, limite de corrente | Simuladores modelam motor ideal; o SG90 de plástico está longe disso | Bancada com o servo real + ESP32 medindo posição e corrente (INA219) |
| **Ponte CAD → simulação** — ler massa, centro de massa e inércia das peças do FreeCAD e gerar o modelo MuJoCo | Ninguém conhece o nosso CAD; à mão erra e desatualiza | Massa simulada = massa da balança |
| **Gerador de passada clássico** — pêndulo invertido linear + ZMP + cinemática inversa 2 elos | Existe na literatura, mas fazer à mão é o melhor jeito de aprender | Robô simulado anda sem cair; depois o real |
| **Estimador de inclinação do MPU-6050** — filtro complementar, depois Kalman | Há bibliotecas, mas precisamos ajustar ao ruído do nosso sensor | Ruído real gravado do MPU injetado na simulação |
| **Varredura de projeto na GPU** — escolher medidas da perna pela margem de torque | Ferramenta específica do nosso problema | Comparar com a conta à mão |

## 5. Fases

Cada fase entrega algo que funciona e ensina um assunto. A ordem segue o projeto mecânico.

| Fase | Entrega | Você aprende | Depende de |
|------|---------|--------------|-----------|
| **F0 — Ambiente** | MuJoCo + JAX com CUDA no `.venv`; teste que roda na 3060 | Como a simulação usa CPU e GPU | — |
| **F1 — Uma perna de caixinhas** | Modelo MuJoCo de 1 perna (4 juntas) com blocos no lugar das peças; mexer juntas e ler torques | Junta, elo, inércia, torque | Medidas propostas da perna |
| **F2 — Varredura na GPU** | Mapa "comprimento da coxa/canela × agachamento → torque necessário vs SG90" | Estática, margem de segurança | F1 |
| **F3 — Modelo do servo** | Modelo do SG90 calibrado na bancada (ESP32 + INA219) | Sim-to-real, identificação de sistema | F1 + servo na bancada |
| **F4 — CAD → simulação** | Script que gera o modelo do robô a partir das peças do FreeCAD | Propriedades de massa | Primeiras peças estruturais |
| **F5 — Passada clássica** | Robô completo andando na simulação com LIPM/ZMP | Cinemática inversa, equilíbrio dinâmico | F3 + F4 |
| **F6 — Equilíbrio com IMU** | Filtro + controlador de tornozelo (PD, depois LQR) contra empurrões simulados | Filtros, controle | F5 + MPU gravado |
| **F7 — Andar por reforço (GPU)** | Política treinada no MJX com variações aleatórias; comparação com F5 | Aprendizado por reforço, robustez | F5 |
| **F8 — Para o robô real** | Passada (F5) ou política pequena (F7) rodando no ESP32 | Embarcado em tempo real | Robô montado |

## 6. Estrutura no repositório

```
sim/
  models/   modelos MuJoCo (gerados e escritos à mão)
  servo/    modelo do SG90 e dados da bancada
  gait/     gerador de passada, cinemática inversa
  tools/    varreduras, ponte CAD → MuJoCo
```

Tudo roda com o mesmo `.venv` das ferramentas de CAD.

## 7. Riscos

| Risco | Efeito | Como lidamos |
|-------|--------|--------------|
| **Sim-to-real**: simulação nunca é igual ao real | Passo que funciona na tela cai no chão | Modelo do servo calibrado (F3), variações aleatórias (F7), sempre testar no real |
| Clones de SG90 variam entre si | Um servo mais fraco que os outros | Medir os 8 na bancada; colocar os melhores nos joelhos/tornozelos |
| Versões de JAX/CUDA × driver | Ambiente quebra numa atualização | Versões fixadas no projeto; teste de fumaça na F0 |
| 12 GB de VRAM | Limita robôs em paralelo no treino | Robô pequeno; poucos milhares de robôs em paralelo cabem |
| Escopo cresce demais | Muita simulação e nenhum robô andando | Cada fase só começa quando o projeto mecânico pede |
