# Simulação e algoritmos — plano

Objetivo: testar mecânica e controle no computador **antes** de imprimir e montar, usando a
RTX 3060 (12 GB) onde ela faz diferença, e evoluir junto com o aprendizado de modelagem e robótica.

> Status: plano **aprovado** (24/10). **F0 e F1 concluídas** — resultados abaixo.

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
| Levantar de 34° em 1,2 s | joelho (pico) | 43 % |
| Levantar de 34° em 0,6 s | joelho (pico) | 71 % |
| Levantar de 34° em 0,3 s | todas | **100 % — servo no limite** |
| Levantar de 34° em 0,15 s | — | **cai** |
| Numa perna, inclinado 18° (meio da faixa estável) | joelho / tornozelo roll | 11 % / 2 % |
| Numa perna, nas bordas da faixa (10° ou 26°) | tornozelo roll | 32 % |

Conclusões:
- **Parado, o SG90 sobra.** O que aperta é **movimento rápido**: levantar em menos de ~0,5 s já
  satura o joelho. A passada (F5) precisa respeitar essa velocidade.
- **Sem quadril roll, ficar numa perna exige inclinar o corpo inteiro ~18° para o lado** (faixa
  estável de 10° a 26°). Com os dois pés no chão, os tornozelos roll ficam travados — não dá para
  deslocar o peso para o lado sem tirar um pé. É o andar "rebolado" (tipo Otto).
- A inclinação necessária depende da **largura do quadril** e da altura do centro de massa:
  quadris mais próximos pedem menos inclinação. Isso entra na varredura da F2.

## 1. Princípio: usar o que existe, medir, só então criar

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
