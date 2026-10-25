# Alimentação dos servos — orçamento de corrente e regulador

Fase 0.1 do [plano de correções do tronco](plano_correcoes_tronco.md). Números de 25/10/2026,
modelo de 620 g (tronco 76 × 78 × 68 mm). Para refazer: `.venv/bin/python sim/tools/current_budget.py`.

## Decisão (25/10/2026, você)

- **Trilho dos servos:** ~~Pololu D24V150F5 (5 V, 15 A)~~ → **UBEC genérico 5 V / 7 A** (entrada 5,5–26 V, 16 g, R$ 59), trocado no mesmo dia por custo. A margem é curta: 7 A contra ~6 A numa queda ou trava; depende do ligar escalonado e não aguenta 2 servos travados por muito tempo além disso. Fusível de 7,5 A continua (~5,8 A da bateria a 7 A).
- **Lógica:** ESP32, lógica do PCA9685, MPU-6050 e HC-SR04 num regulador separado, o Pololu D24V10F5
  (5 V, 1 A), direto da bateria e com terra comum. Esse regulador não tem proteção contra inversão:
  fica depois da chave e do conector polarizado.
- **Fusível:** 7,5 A de ação retardada.
- **Firmware:** liga os servos em grupos (item na §6 do backlog).
- **Massas:** nenhum dos dois reguladores tem massa no site da Pololu. No modelo (`body.TORSO_PARTS`)
  estão 10 g + 1 g estimados; pesar quando chegarem.
- **Revisão:** esta escolha é revista se a bancada da F3 medir corrente de stall bem acima de 0,75 A.

## Divisão tronco / quadril (25/10/2026, você)

| Onde | O que fica |
|---|---|
| **Tronco** | ESP32, que gera o PWM dos 8 servos dos braços (LEDC); o HC-SR04 na cabeça |
| **Quadril** | bateria, reguladores, placa de força, chave, MPU-6050, PCA9685 (8 servos das pernas + o da cintura) |
| **Pela cintura** | 7 fios: trilho dos servos + GND, 5 V lógica, 3,3 V, SDA, SCL, VBAT (sinal); nenhum cabo de servo ([esquema_eletrico.md](esquema_eletrico.md)) |

- **I2C:** o PCA9685 (0x40) e o MPU (0x68) ficam no mesmo barramento.
- **IMU:** fica presa às pernas; o tronco gira na cintura.
- **Modelo:** lugar de cada peça em `body.BODY_PARTS` (`seat`).

## Como a corrente foi estimada

- **Modelo do servo:** a corrente de um motor DC segue o torque. Cada servo puxa
  `I = I_parado + (I_stall − I_parado) × |torque| / torque de stall`.
  - Esse é o pico. A média que a bateria vê é menor, porque o PWM do servo só fica ligado parte do tempo.
  - Os picos são o que o regulador e os capacitores precisam aguentar.
- **Corrente de stall do SG90:** nenhum datasheet informa. As fontes vão de **0,36 A** (medida) a
  **0,75 A**. Cada resultado aparece para três valores: 0,36 / 0,55 / 0,75 A, até a bancada da F3
  medir os nossos clones.
  - Parado sem carga: ~10 mA. Movendo leve: 0,10–0,25 A.
- **Pico de 20 ms:** é a média num quadro de PWM, o pico que alguns capacitores de centenas de µF
  já não seguram mais.

## Resultado

| Cenário | Carga¹ | Média (A) | Pico 20 ms (A) |
|---|---|---|---|
| Em pé, parado | 0,5× | 0,3 / 0,4 / 0,5 | 0,3 / 0,4 / 0,5 |
| Levantar de A = 0,6 a 0,7 rad/s | 1,7× | 0,4 / 0,5 / 0,6 | 0,8 / 1,1 / 1,4 |
| Balanço lateral 0,50 passo/s | 2,3× | 0,6 / 0,9 / 1,1 | 1,0 / 1,4 / 1,9 |
| Balanço lateral 0,67 passo/s (ritmo de projeto) | 2,0× | 0,6 / 0,9 / 1,2 | 0,9 / 1,2 / 1,6 |
| Balanço lateral 1,00 passo/s | 3,0× | 0,7 / 1,1 / 1,4 | 1,2 / 1,8 / 2,4 |
| *Conta:* gesto, 8 servos do braço movendo juntos | — | — | 2,1 |
| *Conta:* queda ou trava, 8 juntas da perna no stall | — | — | 3,0 / 4,5 / **6,1** |
| *Conta:* ligar, os 16 indo à 1ª posição juntos | — | — | 5,8 / 8,8 / **12,0** |

¹ Soma de |torque| / stall de todos os servos: equivale a quantos servos travados.

**O que isso diz**

- **Andar não é o problema:** no ritmo de projeto, o pico fica abaixo de 2 A.
- **Margem para o que a simulação não tem:**
  - controle de equilíbrio corrigindo rápido (F6);
  - degraus de posição sem rampa (o servo analógico satura e puxa o stall por alguns ms);
  - tremor dos clones parados.

  Contando ×2 sobre o pior balanço, a conta fica em **~5 A**.
- **Onde a corrente é alta:** queda ou trava (**~6 A**) e ligar tudo de uma vez (**~12 A**).
- **O ligar se resolve no firmware.** Basta mandar a primeira posição em grupos de 2 a 4 servos,
  com ~150 ms entre os grupos. O PCA9685 já tem o pino OE para manter todos desligados até lá.
  Com isso, o pico de ligar cai para **~2–3 A**, e o requisito vira **≥ 6 A contínuos com margem**,
  não 12 A.

## Opções

| | A. Pololu D24V90F5 | B. Hobbywing UBEC 10A (30603000) | C. Pololu D24V150F5 |
|---|---|---|---|
| Saída | 5 V fixa | 5 / 6 / 7,4 / 8,4 V | 5 V fixa |
| Corrente contínua | **4–8 A típicos** (o "9 A" é o máximo sem garantia; depende de calor e ventilação) | 10 A (pico 20 A) | 15 A (instantâneo ~32 A) |
| Entrada | 5–38 V, queda 0,5–1,5 V | 6–25,2 V | 4,5–40 V |
| Tamanho | 40,6 × 20,3 × 7,6 mm | 43,1 × 32,3 × 12,5 mm | 43,2 × 31,8 × 11 mm |
| Massa | ~5 g (estimada; pesar) | 36 g | não informada; pesar |
| Proteções | curto, temperatura, inversão, partida suave, saída PG² | — (não informadas) | curto, temperatura, inversão, partida suave |
| Cobre queda/trava (6 A) | no limite, depende de calor | sim, com sobra | sim, com sobra |
| Cobre ligar sem escalonar (12 A) | não | só no pico | sim |

² PG = sinal de *power good*: avisa o ESP32 quando o trilho cai abaixo de 4,5 V.

A opção do trilho separado (pernas / braços, 2 reguladores menores) continua descartada, como na
[lista de materiais](lista_materiais.md). Ela só tira 2 A dos braços do trilho das pernas e dobra a fiação.

### Trade-offs

- **A:**
  - **A favor:** é a mais leve (+0 g sobre o modelo atual) e é a única com PG.
  - **Contra:** os 6 A de uma queda ficam dentro da faixa "típica", mas sem margem garantida. Dentro
    do tronco fechado pela capa, sem ventilação, a corrente real fica mais perto do 4 A do que do 8 A.
- **B:**
  - **A favor:** sobra corrente, e a saída de 6 V dá ~20 % mais torque ao SG90.
  - **Contra:** 6 V também aquece mais os clones. São **+31 g** (~5 % da massa, ~5 % a mais em todo
    torque) e ocupa 2,5× o volume de A dentro do tronco. Pede entrada de 6 V mínimo, o que fica no
    limite com a LiPo 2S descarregada (6,0–6,4 V).
- **C:**
  - **A favor:** a margem de B com as proteções de A.
  - **Contra:** ocupa o volume de B, e a massa é desconhecida até pesar (provavelmente bem abaixo dos
    36 g, por ser placa nua).

## Recomendação

**C (D24V150F5).** É a única que cobre queda ou trava (6 A) **dentro do tronco fechado, sem
ventilação**, com margem que não depende de calor. Também aguenta o ligar mesmo se o firmware
escalonado falhar ou ainda não existir, o que acontece nos primeiros testes da perna na bancada.

A só serve se a bancada da F3 medir stall ≤ 0,5 A **e** o teste de temperatura dentro do tronco
passar. B perde para C: tem a mesma corrente, mais massa e uma entrada que fica no limite com a LiPo.

**Vale para qualquer opção**

- **Escalonar o ligar no firmware.** Entra como item da §6 do backlog.
- **Fusível pela corrente de entrada, não de saída.** Com 6 A a 5 V, saem ~5 A da bateria a 7,4 V.
  Um fusível de **7,5 A de ação retardada** protege a fiação sem queimar na queda. Hoje a lista pede
  10 A.
- **ESP32 fora do trilho dos servos.** Uma queda do trilho num stall reinicia o ESP32 no meio da
  passada. Recomendação: um regulador pequeno só para a lógica (ESP32, PCA9685, MPU), direto da
  bateria. Alternativa: diodo + capacitor grande na entrada do ESP32.
- **Capacitores de 2 × 1000 µF no trilho**, perto do PCA9685. Já estão previstos na placa de força.
