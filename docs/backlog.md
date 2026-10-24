# Backlog do projeto

Acompanhamento do robô bípede. Marque `[x]` ao concluir. Cada item diz **quem** faz:
**(você)**, **(Claude)** ou **(juntos)**. Itens dentro de uma seção estão na ordem sugerida.

Documentos de apoio: [materiais](lista_materiais.md) · [medidas do servo](medidas_servo_sg90.md) ·
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

## 1. Compras

Detalhes e quantidades em [lista_materiais.md](lista_materiais.md).

- [ ] Rolamentos 623ZZ chegarem (já comprados) **(você)**
- [ ] Impressora 3D **(você)**
- [ ] Filamento PETG **(você)**
- [ ] Regulador buck 5–6 V ≥ 5 A **(você)**
- [ ] Parafusaria: M3 (8/10/12/16), porcas M3 autotravantes, arruelas M3, M2 (6/8) **(você)**
- [ ] Borracha antiderrapante para a sola **(você)**
- [ ] INA219 — necessário para a bancada do servo (F3) **(você)**
- [ ] Opcionais: PCA9685, sensores de força no pé, insertos roscados, analisador lógico **(você)**

## 2. Simulação

Fases detalhadas em [simulacao.md](simulacao.md). Cada fase só começa quando o projeto mecânico pede.

- [x] Aprovar o plano de simulação **(você)**
- **F0 — Ambiente**
  - [x] Instalar MuJoCo + JAX com CUDA no `.venv` — versões fixadas em `requirements.txt` **(Claude)**
  - [x] Teste de fumaça: simulação rodando na RTX 3060 — `sim/tools/smoke_test.py`, motor Warp 4,7 M passos/s **(Claude)**
  - [ ] Fazer o [tutorial do MuJoCo](tutorial_mujoco.md): abrir, mexer as juntas, ler o torque, experimento de agachar **(você)**
- **F1 — Robô completo de caixinhas**
  - [x] Modelo MuJoCo do bípede (2 pernas × 4 juntas, 359 g) gerado por `sim/tools/build_biped.py` **(Claude)**
  - [x] Medir torques: agachar, levantar em várias velocidades, ficar numa perna (`sim/tools/f1_experiments.py`) **(Claude)**
  - [ ] Abrir o robô completo no monitor (Passo 8 do tutorial do MuJoCo) **(você)**
  - [ ] Decidir depois da F2: manter 8 DOF (corpo inclina ~18° para apoiar numa perna) ou acrescentar quadril roll **(juntos)**
- **F2 — Varredura na GPU**
  - [ ] Varrer coxa/canela × largura do quadril × agachamento × peso → torque necessário vs SG90 (parado **e** em movimento), **incluindo a massa estimada das capas** **(Claude)**
  - [ ] Escolher as medidas da perna com base no mapa **(juntos)**
- **F3 — Modelo do servo SG90**
  - [ ] Montar a bancada: ESP32 + INA219 + servo **(você)**
  - [ ] Firmware da bancada: degrau de posição, gravar posição e corrente **(juntos)**
  - [ ] Medir os 8 servos (+ reservas) e escolher os melhores para joelhos/tornozelos **(você)**
  - [ ] Modelo do servo (torque × velocidade, folga, zona morta, atraso) calibrado **(Claude)**
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
- [ ] Documento da arquitetura da perna (`docs/arquitetura_perna.md`): medidas e esqueleto, a partir da F2, **com o espaço reservado para as capas em volta de cada segmento** **(juntos)**
- [ ] Padrão de encaixe das capas — definir **antes** do suporte (ver 3.1) **(juntos)**
- [ ] Tutorial do suporte do servo + rolamento **(Claude)**
- [ ] Suporte do servo + rolamento 623ZZ — peça base que se repete nas juntas, **com os encaixes da capa e os batentes da junta** **(você)**
- [ ] Revisão do suporte: encaixe do servo, passagem do cabo pelo canal de baixo, alinhamento do rolamento, **batentes da junta**, **encaixes da capa** **(Claude)**
- [ ] Coxa (quadril → joelho), com encaixes da capa e caminho dos fios **(você)**
- [ ] Canela (joelho → tornozelo), com encaixes da capa e caminho dos fios **(você)**
- [ ] Bloco do tornozelo: pitch + roll cruzados, com encaixes da capa **(você)**
- [ ] Pé com sola, com encaixes da capa **(você)**
- [ ] Quadril/tronco: ESP32, bateria, MPU-6050 no centro, placa de distribuição, **com encaixes da capa e acesso de manutenção** **(você)**
- [ ] Montagem virtual: checar colisões e amplitude de cada junta — **com as capas montadas** **(juntos)**
- [ ] Modelos de referência que faltam: parafusos/porcas M3, ESP32 DevKit, MPU-6050, bateria **(Claude)**

### 3.1 Capas encaixadas (proteção e acabamento)

Capas impressas que fecham o esqueleto e protegem circuitos, servos e fios, presas por
**encaixe** (sem cola). O esqueleto é projetado para recebê-las desde o início.

- [ ] Definir o tipo de encaixe: clipe de pressão (snap-fit em balanço), trava em trilho ou ímã — com prós e contras **(juntos)**
- [ ] Definir o padrão: dimensões do clipe e do rebaixo, folga, espessura da parede da capa, quantos encaixes por capa **(juntos)**
- [ ] Modelo de referência do encaixe padrão, para todas as peças usarem o mesmo **(Claude)**
- [ ] Orçamento de massa das capas — elas pesam e entram na conta de torque (F2/F4) **(juntos)**
- [ ] Lista de acessos que as capas **não** podem fechar: USB do ESP32, chave liga/desliga, carga da bateria, troca de servo, calibração **(juntos)**
- [ ] Caminho dos fios por dentro das capas sem prender as juntas em nenhuma posição **(juntos)**
- [ ] Ventilação: saída de ar para o regulador buck e os servos **(juntos)**
- [ ] Capas da perna: coxa, canela, tornozelo e pé **(você)**
- [ ] Capa do quadril/tronco, com as aberturas de acesso **(você)**
- [ ] Revisão: capas não limitam a amplitude das juntas nem encostam umas nas outras **(Claude)**

## 4. Impressão e montagem

- [ ] Peça de teste de tolerância: bolso do servo, alojamento do rolamento, furos M2/M3 **e o encaixe padrão da capa** (encaixar e soltar várias vezes) **(juntos)**
- [ ] Ajustar folgas no CAD conforme o teste **(você)**
- [ ] Imprimir uma perna completa e montar **(você)**
- [ ] Testar a perna presa na bancada antes da segunda **(juntos)**
- [ ] Imprimir e montar o robô completo **(você)**
- [ ] Imprimir e montar as capas; conferir massa final na balança **(você)**

## 5. Eletrônica

- [ ] Esquema elétrico: bateria → fusível → chave → buck → trilho dos servos; ESP32; MPU; divisor da bateria **(juntos)**
- [ ] Placa de distribuição em placa perfurada **(você)**
- [ ] Teste com fonte de bancada limitando corrente, antes da bateria **(você)**
- [ ] Fiação no robô com extensões e organização dos cabos **(você)**

## 6. Firmware (ESP32)

- [ ] PWM dos 8 servos pelo LEDC **(juntos)**
- [ ] Calibração de cada servo: centro e limites de cada junta, salvos na memória; usar o batente como referência **(juntos)**
- [ ] Limites de software 5° antes de cada batente, aplicados em todo comando de servo **(juntos)**
- [ ] Leitura do MPU-6050 + filtro (da F6) **(juntos)**
- [ ] Postura em pé estável **(juntos)**
- [ ] Passada no robô real (da F5/F8) **(juntos)**
- [ ] Equilíbrio com IMU no robô real **(juntos)**
- [ ] Monitoramento da bateria: corte por subtensão, buzzer **(juntos)**
- [ ] Telemetria por Wi-Fi: ângulos, correntes e bateria em tempo real **(juntos)**
