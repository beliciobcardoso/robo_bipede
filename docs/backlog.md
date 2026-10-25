# Backlog do projeto

Acompanhamento do robô bípede. Marque `[x]` ao concluir. Cada item diz **quem** faz:
**(você)**, **(Claude)** ou **(juntos)**. Itens dentro de uma seção estão na ordem sugerida.

Documentos de apoio: [corpo inteiro](arquitetura_corpo.md) · [prévia 3D](previa.md) · [materiais](lista_materiais.md) · [capas](capas.md) · [medidas do servo](medidas_servo_sg90.md) ·
[tutorial PartDesign](tutorial_servo_partdesign.md) · [tutorial MuJoCo](tutorial_mujoco.md) · [plano de simulação](simulacao.md)

---

## 0. Já feito

- [x] Definir configuração: 8 DOF — quadril pitch, joelho, tornozelo pitch, tornozelo roll por perna **(juntos)**
- [x] Lista de materiais e ferramentas **(juntos)**
- [x] Medir o servo SG90 — 1ª rodada e remedição com paquímetro melhor **(você)**
- [x] Modelo de referência do servo por script (`cad/parts/servo_sg90.py`) **(Claude)**
- [x] Tutorial PartDesign do servo para iniciante **(Claude)**
- [x] Servo modelado à mão no PartDesign (`cad/manual/servo_sg90.FCStd`) **(você)**
- [x] Modelo de referência do rolamento 623ZZ (`cad/parts/bearing_623zz.py`) **(Claude)**
- [x] Comparador de modelos na GPU (`tools/compare_meshes.py`) **(Claude)**
- [x] Plano de simulação escrito e aprovado (`docs/simulacao.md`) **(juntos)**
- [x] F0 — ambiente de simulação na RTX 3060 (MuJoCo + MJX/Warp), teste de fumaça passando **(Claude)**
- [x] Cabeça com HC-SR04 (+ reserva de 10 g para câmera) e braços com 2 servos cada (ombro pitch + roll), simulados e aprovados em 24/10: 410 g com LiPo de 55 g, tornozelo roll 57 / 64 % a 0,5 / 1 passo/s **(juntos)**
- [x] Corpo inteiro num só modelo (`sim/tools/body.py`): servo por junta, capas com massa calculada pela forma, checagem do que fica fora das capas, estudo de proporções ([arquitetura_corpo.md](arquitetura_corpo.md)) — com capas honestas o robô atual tem 486 g **(Claude)**

## Decisão agora

- [x] Servos: **SG90 em todas as juntas** — decidido em 24/10 (hoje 17: 8 nas pernas, 8 nos braços, 1 na cintura) **(você)**
- [x] Proporção do corpo: tronco 68 mm, ombros 86 mm, cabeça grande, parede 1,2 mm — decidido em 24/10 ([arquitetura_corpo.md](arquitetura_corpo.md)) **(você)**
- [x] Aplicada em `sim/tools/body.py`; prévia, F1 e documentos refeitos: 254 mm, 518 g, ritmo com folga até ~0,7 passo/s **(Claude)**
- [x] Braço com cotovelo e punho que gira, mão fixa (4 SG90 por braço, 16 no total) — decidido em 24/10 **(você)**; cadeia modelada pelas marcações das 8 cabeças, simulado: 573 g, ritmo até ~0,67 passo/s ([arquitetura_corpo.md](arquitetura_corpo.md)) **(Claude)**
- [x] Forma das capas: quase retas — ombros 18,2 cm, 569 g — decidido em 24/10 **(você)**

- [ ] Correções do tronco, do regulador e dos documentos — tarefas em [plano_correcoes_tronco.md](plano_correcoes_tronco.md) **(juntos)**

## Sempre

- [ ] Atualizar a [prévia 3D](previa.md) a cada mudança de medida, peça ou conceito (`make preview` + histórico) **(Claude)** — item permanente

## 1. Compras

Detalhes e quantidades em [lista_materiais.md](lista_materiais.md).

- [ ] Rolamentos 623ZZ chegarem (já comprados) **(você)**
- [ ] Impressora 3D **(você)**
- [ ] Filamento PETG **(você)**
- [ ] Regulador dos servos: UBEC 5 V / 7 A genérico, R$ 59 — **comprado em 25/10, aguardando entrega**; escolhido no lugar do D24V150F5, por custo ([alimentacao.md](alimentacao.md)) **(você)**
- [ ] Regulador da lógica Pololu D24V10F5 (5 V, 1 A) — ESP32 fora do trilho dos servos, decidido em 25/10 **(você)**
- [ ] LiPo 2S ~800 mAh, ~55 g (se a bateria atual for 2× 18650) **(você)**
- [ ] Pack 2S1P 14500 alta descarga com BMS — testar contra a LiPo; os dois com XT30 + JST-XH 3 pinos (25/10) **(você)**
- [ ] Comparar as duas baterias na bancada: queda de tensão a 5–6 A, autonomia, temperatura; escolher uma **(juntos)**
- [ ] SG90: o robô usa 17 (8 pernas, 8 braços, 1 cintura) + 2 a 4 reservas; você tem 4 → comprar **15 a 17**, de preferência do mesmo lote **(você)**
- [ ] PCA9685 — no quadril, para os 8 servos das pernas + o da cintura; os 8 dos braços vão direto no LEDC do ESP32, no tronco (25/10) **(você)**
- [ ] HC-SR04 **(você)**
- [ ] Fusível 7,5 A de ação retardada no lugar do de 5 A — decidido em 25/10 **(você)**
- [ ] Parafusaria: M3 (8/10/12/16), porcas M3 autotravantes, arruelas M3, M2 (6/8) **(você)**
- [ ] Borracha antiderrapante para a sola **(você)**
- [ ] INA219 — necessário para a bancada do servo (F3) **(você)**
- [ ] Insertos M2/M3 a quente chegarem (kit de 400, comprado em 25/10) **(você)**
- [ ] Opcionais: sensores de força no pé, analisador lógico **(você)**
- [ ] Futuro: ESP32-CAM para a câmera na cabeça **(você)**

## 2. Simulação

Fases detalhadas em [simulacao.md](simulacao.md). Cada fase só começa quando o projeto mecânico pede.

- [x] Aprovar o plano de simulação **(você)**
- **F0 — Ambiente**
  - [x] Instalar MuJoCo + JAX com CUDA no `.venv` — versões fixadas em `requirements.txt` **(Claude)**
  - [x] Teste de fumaça: simulação rodando na RTX 3060 — `sim/tools/smoke_test.py`, motor Warp 4,7 M passos/s **(Claude)**
  - [x] Fazer o [tutorial do MuJoCo](tutorial_mujoco.md): abrir, mexer as juntas, ler o torque, experimento de agachar **(você)**
- **F1 — Robô completo de caixinhas**
  - [x] Modelo MuJoCo do bípede (2 pernas × 4 juntas, 359 g) gerado por `sim/tools/build_biped.py` **(Claude)**
  - [x] Medir torques: agachar, levantar em várias velocidades, ficar numa perna (`sim/tools/f1_experiments.py`) **(Claude)**
  - [x] Abrir o robô completo no monitor (Passo 8 do tutorial do MuJoCo) **(você)**
  - [x] Decidir entre manter 8 DOF ou acrescentar quadril roll — **decidido em 24/10: manter 8 DOF** (corpo inclina ~18° para apoiar numa perna; ver `arquitetura_perna.md`) **(você)**
  - [x] Teste de balanço lateral em ritmo de passada (`sim/tools/rocking_test.py`): tornozelo roll 53 % a 0,5 passo/s, 61 % a 1 passo/s — passa até 1 passo/s **(Claude)**
  - [ ] Rever a decisão dos 8 DOF se o tornozelo roll passar de ~70 % do SG90 no ritmo desejado, ou se a inclinação continuar acima de ~20° depois de afinar o quadril (F2) **(juntos)**
    Decidido em 25/10 (você): vale no ritmo de projeto, 0,67 passo/s. Com o robô de 615 g não dispara (roll 56 %, inclinação 14°): mantém 8 DOF.
  - [ ] Margem do joelho: 79 % ao levantar a 1 rad/s e no balanço (limite 70 %) — o quadril roll não ajuda o joelho; atacar com agachamento base menor, massa ou ritmo de levantar **(juntos)**
- **F2 — Varredura na GPU**
  - [x] Varrer coxa/canela × largura do quadril × peso das capas → torque vs SG90, parado e em movimento — 360 robôs em `sim/tools/f2_sweep.py` **(Claude)**
  - [x] Escolher as medidas da perna — **aprovadas em 24/10:** quadris 45 mm, coxa 45, canela 45, pé 40 × 70, capas meta 35 g / limite 50 g (`arquitetura_perna.md`); revistas pelo conceito do suporte para quadris 50 mm e pé 45 × 70 **(juntos)**
- **F3 — Modelo do servo SG90**
  - [ ] Montar a bancada: ESP32 + INA219 + servo **(você)**
  - [ ] Firmware da bancada: degrau de posição, gravar posição e corrente **(juntos)**
  - [ ] Medir os 8 servos (+ reservas) e escolher os melhores para joelhos/tornozelos **(você)**
  - [ ] Medir a corrente de stall real do clone e confirmar o UBEC 5 V / 7 A ([alimentacao.md](alimentacao.md)); se passar de 0,75 A, a margem acaba e é preciso um regulador maior **(você)**
  - [ ] Modelo do servo (torque × velocidade, folga, zona morta, atraso) calibrado **(Claude)**
  - [ ] Simular degraus de posição sem rampa com o servo calibrado (o SG90 satura e puxa o stall): pico de torque e de corrente; refazer `current_budget.py` e conferir a margem do UBEC 5 V / 7 A ([alimentacao.md](alimentacao.md)) **(Claude)**
- **F4 — Ponte CAD → simulação**
  - [ ] Script FreeCAD → modelo MuJoCo com massa, centro de massa e inércia de cada peça **(Claude)**
  - [ ] Conferir massa simulada × massa na balança **(você)**
- **F5 — Passada clássica**
  - [ ] Cinemática inversa de 2 elos (coxa + canela) **(juntos)**
  - [ ] Gerador de passada: pêndulo invertido linear + ZMP **(juntos)**
  - [ ] Robô completo andando na simulação sem cair **(juntos)**
- **F6 — Equilíbrio com IMU**
  - [ ] Gravar ruído real do MPU-6050 parado e em movimento **(você)**
  - [ ] Filtro complementar → depois Kalman **(juntos)**
  - [ ] Controlador de tornozelo (PD → LQR) resistindo a empurrões simulados **(juntos)**
  - [ ] Simular o controle de equilíbrio ativo na passada (correções rápidas + empurrões): pico de torque e de corrente; refazer `current_budget.py` — hoje a conta usa ×2 de margem por falta disso ([alimentacao.md](alimentacao.md)) **(Claude)**
- **F7 — Andar por reforço (GPU)**
  - [ ] Treinar política no MJX com variações aleatórias (massa, folga, atrito) **(Claude)**
  - [ ] Comparar com a passada clássica (F5) em números **(juntos)**
- **F8 — Para o robô real**
  - [ ] Passada (F5) ou política pequena (F7) rodando no ESP32 **(juntos)**

## 3. Mecânica (CAD)

Peças estruturais são desenhadas por você no FreeCAD, com tutorial e revisão do Claude.
Peças compradas têm modelo de referência por script.

**Regra de projeto:** o esqueleto inteiro já nasce com os **pontos de encaixe das capas**
(seção 3.1). Cada peça estrutural abaixo só está pronta quando tiver os encaixes dela.

- [x] Faixas de cada junta com batente mecânico + limite de software 5° antes (provisório, em `docs/arquitetura_perna.md`) **(juntos)**
- [ ] Validar as faixas das juntas na passada simulada (F5) e ajustar **(juntos)**
- [x] Documento da arquitetura da perna (`docs/arquitetura_perna.md`): medidas e esqueleto, a partir da F2, **com o espaço reservado para as capas em volta de cada segmento** **(juntos)**
- [x] Padrão de encaixe das capas — clipe + pinos-guia, modelo de referência pronto (ver 3.1) **(juntos)**
- [x] Conceito do suporte do servo: suporte + garfo padrão, pivô M3 + rolamento, quadris 50 mm, tornozelo 22 mm — aprovado em 24/10 ([suporte_servo.md](suporte_servo.md)) **(juntos)**
- [x] Ficha de medidas do horn de braço simples ([medidas_horn_sg90.md](medidas_horn_sg90.md)) **(Claude)**
- [ ] Medir o horn **(você)**
- [ ] Tutorial do suporte e do garfo **(Claude)**
- [ ] Suporte do servo — peça padrão das juntas pitch, **com os encaixes da capa e os batentes da junta** **(você)**
- [ ] Garfo com alojamento do rolamento 623ZZ e rebaixo do horn — peça padrão **(você)**
- [ ] Revisão do suporte: encaixe do servo, passagem do cabo pelo canal de baixo, alinhamento do rolamento, **batentes da junta**, **encaixes da capa** **(Claude)**
- [ ] Coxa (quadril → joelho), com encaixes da capa e caminho dos fios **(você)**
- [ ] Canela (joelho → tornozelo), com encaixes da capa e caminho dos fios **(você)**
- [ ] Bloco do tornozelo: pitch + roll cruzados, com encaixes da capa **(você)**
- [ ] Pé com sola, com encaixes da capa **(você)**
- [ ] Quadril modular: suporte do quadril com espaço reservado no tronco para um servo de quadril roll de cada lado, caso a decisão dos 8 DOF mude **(juntos)**
- [ ] Quadril/tronco: ESP32, bateria, MPU-6050 no centro, placa de distribuição, **com encaixes da capa e acesso de manutenção** **(você)**
- [ ] Conceito do ombro: servo do ombro pitch dentro do tronco com 623ZZ (tronco de 86 mm nos ombros), elo até o garfo do ombro roll; servo do ombro roll dentro do braço; braço a 3 mm da perna — provisório na [prévia](previa.md) **(juntos)**
- [ ] Ombro (suporte do pitch no tronco + elo + suporte do roll), braço, cotovelo (garfo sem rolamento), antebraço, punho e mão, com encaixes da capa **(você)**
- [ ] Cabeça: suporte do HC-SR04 voltado para a frente, espaço e passagem de cabo para a câmera futura, com encaixes da capa **(você)**
- [ ] Montagem virtual: checar colisões e amplitude de cada junta — **com as capas montadas** **(juntos)**
- [ ] Modelos de referência que faltam: parafusos/porcas M3, ESP32 DevKit, MPU-6050, bateria **(Claude)**

### 3.1 Capas encaixadas (proteção e acabamento)

Capas impressas que fecham o esqueleto e protegem circuitos, servos e fios, presas por
**encaixe** (sem cola). O esqueleto é projetado para recebê-las desde o início.

- [x] Definir o tipo de encaixe — **decidido em 24/10: clipe de pressão + 2 pinos-guia por capa**; ímã é o plano B ([capas.md](capas.md)) **(juntos)**
- [x] Definir as dimensões do clipe e do pino-guia — **aprovadas em 24/10** ([capas.md](capas.md)) **(juntos)**
- [ ] Confirmar parede da capa (0,8 mm desde 25/10; resiste a queda? testar na peça de tolerância) e encaixes por capa (2 clipes + 2 pinos; tronco 4 + 2) ao desenhar as capas **(juntos)**
- [x] Modelo de referência do encaixe padrão: `cad/parts/snap_clip.py` (capa) e `snap_socket.py` (esqueleto), com checagem do encaixe montado **(Claude)**
- [x] Orçamento de massa das capas — elas pesam e entram na conta de torque (F2/F4) **(juntos)** — 25/10: calculado pela forma no `body.py` (133 g com parede de 0,8 mm) e já nas simulações; conferir na balança na F4
- [ ] Gaveta da bateria pela traseira do quadril, com tampa de encaixe própria: troca em ~10 s sem abrir o quadril; plug de balanceamento (JST-XH) acessível para carregar sem tirar a bateria — decidido em 25/10 **(você)**
- [ ] Lista de acessos que as capas **não** podem fechar: USB do ESP32, chave liga/desliga, carga e troca da bateria (gaveta traseira do quadril), troca de servo, calibração **(juntos)**
- [ ] Caminho dos fios por dentro das capas sem prender as juntas em nenhuma posição **(juntos)**
- [ ] Ventilação: saída de ar para o regulador buck e os servos **(juntos)**
- [ ] Capas da perna: coxa, canela, tornozelo e pé **(você)**
- [ ] Capa do quadril/tronco, com as aberturas de acesso **(você)**
- [ ] Capas dos braços e da cabeça (janela para os dois "olhos" do HC-SR04 e para a câmera) **(você)**
- [ ] Revisão: capas não limitam a amplitude das juntas nem encostam umas nas outras **(Claude)**

## 4. Impressão e montagem

- [ ] Peça de teste de tolerância: bolso do servo, alojamento do rolamento, furos M2/M3 **e o encaixe padrão da capa** (encaixar e soltar várias vezes) **(juntos)**
- [ ] Ajustar folgas no CAD conforme o teste **(você)**
- [ ] Imprimir uma perna completa e montar **(você)**
- [ ] Testar a perna presa na bancada antes da segunda **(juntos)**
- [ ] Imprimir e montar o robô completo **(você)**
- [ ] Imprimir e montar as capas; conferir massa final na balança **(você)**

## 5. Eletrônica

- [ ] Esquema elétrico — rascunho em [esquema_eletrico.md](esquema_eletrico.md) (25/10, gerado por `tools/wiring_diagram.py`): energia, 7 fios na cintura, pinos do ESP32 e canais do PCA9685; falta revisar juntos **(juntos)**
- [ ] Placa de distribuição em placa perfurada **(você)**
- [ ] Teste com fonte de bancada limitando corrente, antes da bateria **(você)**
- [ ] Fiação no robô com extensões e organização dos cabos **(você)**

## 6. Firmware (ESP32)

- [ ] PWM: 8 servos das pernas + cintura pelo PCA9685 (I2C, quadril); 8 servos dos braços pelo LEDC do ESP32 (tronco) **(juntos)**
- [ ] Ligar escalonado: PCA9685 e LEDC ligam sem pulso (servos soltos) até a 1ª posição; servos ligados em grupos de 2 a 4, ~150 ms entre grupos (sem isso, ~12 A ao ligar — [alimentacao.md](alimentacao.md)) **(juntos)**
- [ ] Leitura do HC-SR04: distância à frente, parar antes de obstáculo **(juntos)**
- [ ] Calibração de cada servo: centro e limites de cada junta, salvos na memória; usar o batente como referência **(juntos)**
- [ ] Limites de software 5° antes de cada batente, aplicados em todo comando de servo **(juntos)**
- [ ] Leitura do MPU-6050 + filtro (da F6) **(juntos)**
- [ ] Postura em pé estável **(juntos)**
- [ ] Passada no robô real (da F5/F8) **(juntos)**
- [ ] Equilíbrio com IMU no robô real **(juntos)**
- [ ] Monitoramento da bateria: corte por subtensão, buzzer **(juntos)**
- [ ] Telemetria por Wi-Fi: ângulos, correntes e bateria em tempo real **(juntos)**
