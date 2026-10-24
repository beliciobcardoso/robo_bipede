# Suporte do servo — conceito

> **Status: aprovado em 24/10** (as 4 decisões da seção 6). Próximo: medir o horn, depois o tutorial passo a passo.

## 1. Primeiro, um ajuste nas medidas aprovadas

Fazendo a conta com as peças reais, a perna é **larga**: nas juntas pitch o eixo do servo aponta
para o lado, então a largura da perna é a "pilha" ao longo do eixo:

| Camada (ao longo do eixo) | mm |
|---------------------------|----|
| Braço do garfo sobre o horn | 2,5 |
| Horn + topo do eixo até o corpo do servo | ~7 |
| Corpo do servo (base até o topo da torre) | 28 |
| Fundo do suporte + espaçador | 2 |
| Rolamento 623ZZ no braço de baixo do garfo (4 mm + parede) | ~5 |
| **Largura da perna (estrutura)** | **~42 mm** |

Com os quadris a **45 mm** sobram **~3 mm** entre as pernas: não cabe capa na face de dentro.
(Na F2 a perna era uma caixinha de 18 mm — por isso o conflito não apareceu.)

O mesmo raciocínio corrige o **tornozelo**: entre o eixo pitch e o eixo roll cabem o garfo e o
suporte do servo roll, ~**22 mm** (o modelo usava 12).

Simulação com as duas correções:

| Quadris | Tornozelo pitch→roll | Folga entre pernas | Inclinação numa perna | Balanço 0,5 passo/s (roll / joelho) | Balanço 1 passo/s (roll / joelho) |
|---------|---------------------|--------------------|-----------------------|-------------------------------------|-----------------------------------|
| 45 mm (aprovado) | 12 mm | ~3 mm | 14° | 45 % / 36 % | 50 % / 68 % |
| **50 mm (proposto)** | **22 mm** | **~8 mm** | **14°** | **50 % / 36 %** | **57 % / 69 %** |

**Proposta: quadris a 50 mm** (pé continua 45 mm de largura, folga de 5 mm entre os pés) e
tornozelo pitch→roll de 22 mm. As duas condições dos 8 DOF continuam passando. Coxa e canela
ficam em 45 mm.

## 2. Estratégia: duas peças padrão por junta

Cada junta é feita de **duas peças padrão**, iguais em todas as juntas pitch:

| Peça | Função | Fica presa em |
|------|--------|---------------|
| **Suporte** | segura o **corpo** do servo (pelas abas) e tem, embaixo, o **pino do pivô** no eixo | o segmento de cima |
| **Garfo** ("U") | abraça o servo: um braço preso no **horn**, o outro com o **rolamento** girando no pino do pivô | o segmento de baixo |

```
      vista de frente (o eixo da junta é horizontal, ←→)

        braço do garfo preso no horn
      ┌─────────────────────────┐
      │ ▓▓ horn                 │
      │ ┌───────────────────┐   │
      │ │   servo SG90      │   │  ← dentro do SUPORTE
      │ │   (corpo preso    │   │
      │ │    pelas abas)    │   │
      │ └───────────────────┘   │
      │  ◎ rolamento no pino    │
      └─────────────────────────┘
        braço do garfo com o rolamento
```

Os segmentos são **suporte + garfo parafusados costas com costas**:

| Segmento | Garfo de cima | Suporte de baixo |
|----------|---------------|------------------|
| Coxa | junta do quadril | servo do joelho |
| Canela | junta do joelho | servo do tornozelo pitch |
| Bloco do tornozelo | junta do tornozelo pitch | servo do tornozelo roll, **girado 90°** — peça especial |
| Pé | junta do tornozelo roll | sola |
| Quadril (no tronco) | — | servo do quadril |

**Por que peças padrão e não um segmento inteiriço:** você desenha **2 peças** em vez de 6, e
cada teste de impressão vale para todas as juntas. O custo é um pouco mais de massa (~2 g por
junta em parafusos) e uma junção a mais. Conta: suporte (eixo → costas) ~24 mm + garfo (eixo →
base) ~14 mm = **38 mm**, cabe nos 45 mm entre eixos com 7 mm para a junção. Quando o projeto
estabilizar, dá para fundir suporte + garfo num segmento inteiriço.

O **bloco do tornozelo** é a exceção: os eixos pitch e roll ficam a só 22 mm um do outro, então
garfo e suporte viram uma peça única.

## 3. Suporte

| Item | Valor | Por quê |
|------|-------|---------|
| Bolso do servo | corpo + **0,2 mm** de folga por lado | a peça de teste confirma |
| Paredes | **2,0 mm** (5 voltas de bico 0,4) | rígido sem pesar |
| Fixação do servo | abas sobre um degrau, **2 parafusos M2 autoatarraxantes** (vêm com o servo) | os furos das abas já existem (27,8 → medido 28,0 mm entre eles) |
| Pino do pivô | **parafuso M3** passando pelo rolamento e roscado num **inserto M3** no fundo do suporte, **no eixo do servo** | eixo alinhado com o do servo, sem folga |
| Espaçador do pivô | anel Ø5,0 × 0,5 mm no fundo, em volta do parafuso | encosta **só no anel interno** do rolamento (entre Ø4,2 e Ø5,2) |
| Passagem do cabo | rasgo no fundo, na ponta do lado do eixo (onde o cabo sai) | o cabo desce e corre pela face do suporte até as costas |
| Batentes | duas faces na ponta do lado do eixo, no ângulo de cada junta (tabela em `arquitetura_perna.md`) | o garfo encosta nelas antes de o servo chegar ao batente interno |
| Encaixe da capa | rebaixo + furos do padrão (`snap_socket`) nas faces externas | |
| Costas | 2 furos M3 a 20 mm + 2 pinos-guia para a junção com o garfo do segmento | |

## 4. Garfo

| Item | Valor | Por quê |
|------|-------|---------|
| Braço do horn | 2,5 mm, com **rebaixo no formato do horn** + os parafusos do horn | o formato transmite a força; os parafusos só seguram |
| Braço do rolamento | alojamento **Ø9,9 mm** (0,1 mm de interferência no Ø10) × 4 mm, com ressalto de Ø8,5 | o ressalto encosta **só no anel externo** (Da máx 8,8 mm) |
| Distância eixo → base | ~14 mm | o suporte gira por dentro sem raspar (canto do suporte a ~10,5 mm do eixo + 1 mm de folga) |
| Batente | um dente na base que encosta nas faces de batente do suporte | |
| Impressão | **deitado**, braços na mesa | as camadas ficam ao longo dos braços — o garfo não racha |

## 5. O que falta medir

**O horn** — o rebaixo do braço do garfo copia o formato dele. Preciso de uma ficha de medidas do
horn de braço simples (diâmetro e altura do cubo, comprimento, largura e espessura do braço,
posição e diâmetro dos furos). Faço a ficha no mesmo formato da do servo.

## 6. Decisões (aprovadas em 24/10)

1. Quadris de 45 → **50 mm** e tornozelo pitch→roll de 12 → **22 mm**.
2. **Duas peças padrão** (suporte + garfo) parafusadas costas com costas; bloco do tornozelo como peça especial.
3. Pivô com **parafuso M3 + inserto** no suporte, rolamento no garfo.
4. Paredes de 2,0 mm e folga de 0,2 mm no bolso do servo (a confirmar no teste).
