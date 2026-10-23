# Lista de materiais e ferramentas

Marque `[x]` no que já tem. Itens **(opcional)** não bloqueiam o projeto.

Meta de massa total: **≤ 400 g**. Acima disso o joelho e o tornozelo do SG90 trabalham sem margem
no apoio de uma perna só — por isso bateria e eletrônica leves importam.

> **Configuração: 8 DOF** — por perna: quadril pitch, joelho, tornozelo pitch, tornozelo roll.

## Atuadores

- [X] **Servo SG90 (clone)** — 8 — juntas
- [X] **Servo SG90 reserva** — 2 a 4 — engrenagem plástica de clone espana; ter reserva evita parar o projeto
- [X] **Horns** (braço simples e cruz) — vêm com o servo — fixação no eixo
- [X] **Parafusos do servo** (abas + horn) — vêm com o servo

## Controle e sensores

- [X] **ESP32 DevKit** — 1 — controle; PWM dos servos direto pelo LEDC (16 canais)
- [X] **MPU-6050** (acelerômetro + giroscópio 3 eixos) — 1 — equilíbrio; I2C, montar no centro do tronco
- [ ] **PCA9685** (driver PWM 16 canais, I2C) **(opcional)** — 1 — tira o PWM do ESP32; não é necessário para 6–8 servos
- [ ] **INA219** (sensor de corrente/tensão I2C) **(opcional)** — 1 — medir consumo dos servos, detectar travamento
- [ ] **FSR / sensor de força no pé** **(opcional)** — 2 a 8 — detectar contato do pé com o chão
- [X] **Buzzer + LED de status** **(opcional)** — 1 — feedback de estado e bateria fraca

## Alimentação

Pico de corrente: SG90 trava em ~0,7 A cada → 8 servos podem pedir **~6 A** em pico.

- [X] **Bateria 2S (7,4 V)** — 1 — LiPo 800–1500 mAh (~50–80 g) ou 2× 18650 em série (~95 g)
- [X] **BMS 2S** — 1 — só se usar 18650 sem proteção
- [ ] **Regulador buck 5–6 V, ≥ 5 A contínuo** (UBEC ou módulo XL4015/equivalente) — 1 — trilho dos servos
- [X] **Capacitor eletrolítico 470–1000 µF / 16 V** — 2 — junto ao trilho dos servos, segura queda nos picos
- [X] **Chave liga/desliga ≥ 5 A** — 1
- [X] **Fusível ou PTC ~5 A** — 1 — proteção da bateria
- [X] **Divisor resistivo para medir bateria** (ex.: 100 kΩ + 33 kΩ) — 1 — ADC do ESP32, corte por subtensão
- [X] **Carregador balanceado 2S** (ou carregador 18650) — 1
- [X] **Conector de bateria** (XT30 ou JST) — 1 par

## Cabeamento e montagem eletrônica

- [X] **Extensão de cabo de servo 15–30 cm** — 4 a 8 — servos do joelho e tornozelo até o tronco
- [X] **Barra de pinos macho 3 vias** — para placa de distribuição dos servos
- [X] **Placa perfurada** (ou PCB própria) — 1 — distribuição de alimentação + ESP32 + MPU
- [X] **Fio silicone 18–20 AWG** — trilho de potência
- [X] **Fio fino / jumpers Dupont** — sinais
- [X] **Conectores JST-XH ou Dupont + crimpador**
- [X] **Termorretrátil**
- [X] **Abraçadeiras pequenas / espiral organizadora**

## Mecânica e fixação

- [ ] **Filamento PETG** (ou PLA) — 1 rolo — PETG aguenta melhor impacto de queda
- [ ] **Rolamento 623ZZ (3×10×4 mm, aço carbono)** **(comprado, aguardando entrega)** — 8 (+2 reserva) — pivô do lado oposto ao eixo do servo; sem isso a junta fica em balanço e força o servo
- [ ] **Parafusos M3** (8, 10, 12, 16 mm) — eixos de pivô e estrutura
- [ ] **Porcas M3 autotravantes (nylon)** — pivôs não soltam com vibração
- [ ] **Arruelas M3**
- [ ] **Parafusos M2** (6, 8 mm) + porcas — fixações pequenas
- [ ] **Insertos roscados M2/M3 a quente** **(opcional)** — rosca durável no plástico
- [ ] **Borracha antiderrapante para a sola** — 2 — EVA, borracha de câmara ou TPU impresso

## Ferramentas

- [ ] **Impressora 3D**
- [X] **Paquímetro**
- [X] **Multímetro**
- [X] **Fonte de bancada com limite de corrente** — primeiros testes sem risco para servos e bateria
- [X] **Ferro de solda + estanho + fluxo**
- [X] **Chaves Phillips PH00 / PH0**
- [X] **Chaves Allen / chave de boca 5,5 mm (M3)**
- [X] **Alicate de corte e desencapador**
- [X] **Testador de servo** **(opcional)** — centralizar servo antes de montar o horn
- [ ] **Analisador lógico / osciloscópio** **(opcional)** — depurar PWM e I2C

## Software

- [x] **FreeCAD 1.1** — modelagem
- [ ] **Fatiador** (OrcaSlicer, PrusaSlicer ou Cura)
- [x] **Arduino IDE 2** — já instalado; alternativa: PlatformIO
- [ ] **Biblioteca do MPU-6050** (Electronic Cats MPU6050 / i2cdevlib, com DMP)
- [X] **Git** — versionar scripts CAD e firmware
