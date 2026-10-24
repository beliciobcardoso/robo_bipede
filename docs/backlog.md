# Backlog do projeto

Acompanhamento do robô bípede. Marque `[x]` ao concluir. Cada item diz **quem** faz:
**(você)**, **(Claude)** ou **(juntos)**. Itens dentro de uma seção estão na ordem sugerida.

Documentos de apoio: [materiais](lista_materiais.md) · [medidas do servo](medidas_servo_sg90.md) ·
[tutorial PartDesign](tutorial_servo_partdesign.md) · [plano de simulação](simulacao.md)

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
- [x] Plano de simulação escrito (`docs/simulacao.md`) **(Claude)**

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

- [ ] Aprovar o plano de simulação **(você)**
- **F0 — Ambiente**
  - [ ] Instalar MuJoCo + JAX com CUDA no `.venv` **(Claude)**
  - [ ] Teste de fumaça: simulação rodando na RTX 3060 **(Claude)**
- **F1 — Uma perna de caixinhas**
  - [ ] Modelo MuJoCo de 1 perna (4 juntas) com blocos e massas estimadas **(Claude)**
  - [ ] Abrir no visualizador, mexer as juntas e ler os torques **(você)**
- **F2 — Varredura na GPU**
  - [ ] Varrer coxa/canela × agachamento × peso → torque necessário vs SG90 **(Claude)**
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

- [ ] Documento da arquitetura da perna (`docs/arquitetura_perna.md`): medidas e esqueleto, a partir da F2 **(juntos)**
- [ ] Tutorial do suporte do servo + rolamento **(Claude)**
- [ ] Suporte do servo + rolamento 623ZZ — peça base que se repete nas juntas **(você)**
- [ ] Revisão do suporte: encaixe do servo, passagem do cabo pelo canal de baixo, alinhamento do rolamento **(Claude)**
- [ ] Coxa (quadril → joelho) **(você)**
- [ ] Canela (joelho → tornozelo) **(você)**
- [ ] Bloco do tornozelo: pitch + roll cruzados **(você)**
- [ ] Pé com sola **(você)**
- [ ] Quadril/tronco: ESP32, bateria, MPU-6050 no centro, placa de distribuição **(você)**
- [ ] Montagem virtual: checar colisões e amplitude de cada junta **(juntos)**
- [ ] Modelos de referência que faltam: parafusos/porcas M3, ESP32 DevKit, MPU-6050, bateria **(Claude)**

## 4. Impressão e montagem

- [ ] Peça de teste de tolerância: bolso do servo, alojamento do rolamento, furos M2/M3 **(juntos)**
- [ ] Ajustar folgas no CAD conforme o teste **(você)**
- [ ] Imprimir uma perna completa e montar **(você)**
- [ ] Testar a perna presa na bancada antes da segunda **(juntos)**
- [ ] Imprimir e montar o robô completo **(você)**

## 5. Eletrônica

- [ ] Esquema elétrico: bateria → fusível → chave → buck → trilho dos servos; ESP32; MPU; divisor da bateria **(juntos)**
- [ ] Placa de distribuição em placa perfurada **(você)**
- [ ] Teste com fonte de bancada limitando corrente, antes da bateria **(você)**
- [ ] Fiação no robô com extensões e organização dos cabos **(você)**

## 6. Firmware (ESP32)

- [ ] PWM dos 8 servos pelo LEDC **(juntos)**
- [ ] Calibração de cada servo: centro e limites de cada junta, salvos na memória **(juntos)**
- [ ] Leitura do MPU-6050 + filtro (da F6) **(juntos)**
- [ ] Postura em pé estável **(juntos)**
- [ ] Passada no robô real (da F5/F8) **(juntos)**
- [ ] Equilíbrio com IMU no robô real **(juntos)**
- [ ] Monitoramento da bateria: corte por subtensão, buzzer **(juntos)**
- [ ] Telemetria por Wi-Fi: ângulos, correntes e bateria em tempo real **(juntos)**
