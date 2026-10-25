# Capas encaixadas

Capas impressas que fecham o esqueleto e protegem servos, circuitos e fios, presas **sem cola**.
Itens de acompanhamento no [backlog](backlog.md), seção 3.1.

## Decisão: clipe de pressão + 2 pinos-guia (24/10)

Cada capa se prende ao esqueleto por **clipes de pressão** (uma lingueta flexível com um gancho
que estala num rebaixo) e é alinhada por **2 pinos-guia** (pino na capa, furo no esqueleto, ou o
contrário). Os pinos alinham e seguram contra deslizar; o clipe só segura contra sair.

Por quê:

- **Sai da própria impressão**: sem peças extras, sem cola.
- **PETG flexiona sem trincar** — é o material certo para clipe (no PLA ele trinca com o uso).
- **Segura nas quedas**, que vão ser frequentes no começo.
- Com os pinos fazendo o alinhamento, o clipe pode ser macio e durar mais.

Comparadas e descartadas:

| Opção | Por que não |
|-------|-------------|
| Trilho deslizante | precisa de um caminho livre para deslizar, difícil numa perna cheia de juntas; sensível a atrito e ao "pé de elefante" da impressão |
| Ímã (neodímio 3×2 mm) | a capa solta e voa nas quedas; peças extras para comprar. **É o plano B** se os clipes falharem no teste de impressão |

Trocar para ímãs, se preciso, só muda o tipo de encaixe — as **posições** dos pontos de fixação
nas peças são as mesmas.

## Regras de projeto

- **Orientação na impressão:** a lingueta do clipe é impressa **deitada** (comprimento no plano da
  mesa). Em pé, ela quebra entre as camadas.
- **Espaço para flexionar:** atrás da lingueta precisa haver folga igual ao tamanho do gancho,
  senão o clipe não entra.
- **Ponto para soltar:** cada capa tem um ponto acessível para empurrar o clipe e tirá-la sem
  ferramenta (ou com uma chave de fenda fina).
- **Todas as peças usam o mesmo clipe e o mesmo pino** — um modelo de referência único.
- Primeiro na **peça de teste de tolerância**: encaixar e soltar várias vezes antes de imprimir
  qualquer capa.

## Dimensões do padrão

> **Clipe e pino-guia aprovados em 24/10.** Parede da capa e quantidade de encaixes: valores iniciais, a confirmar ao desenhar as capas.

### Clipe (lingueta em balanço)

| Medida | Valor | Por quê |
|--------|-------|---------|
| Comprimento da lingueta (L) | 8 mm | mais comprida = mais macia |
| Espessura (t) | 1,2 mm | 3 voltas de bico 0,4 mm — parede cheia, sem vazio no meio |
| Largura | 4 mm | |
| Altura do gancho (y) | 0,6 mm | quanto a lingueta dobra para passar |
| Ângulo de entrada | 30° | entra fácil |
| Ângulo de retenção | 60° | segura, mas sai puxando firme (90° não sairia mais) |
| Profundidade do rebaixo no esqueleto | 0,8 mm | gancho + 0,2 mm (a lingueta dobra para **fora**, no ar, através de um rasgo de 0,5 mm em volta dela) |

Conferência da deformação (fórmula padrão de clipe retangular): ε = 1,5 · t · y / L² =
1,5 × 1,2 × 0,6 / 8² ≈ **1,7 %**. O PETG escoa por volta de 4–5 %; para abrir e fechar muitas
vezes recomenda-se ficar abaixo de ~2 %. Força para dobrar a lingueta: ~4 N por clipe
(≈ 400 g na mão) — firme, mas fácil.

### Pino-guia

| Medida | Valor |
|--------|-------|
| Diâmetro do pino | 3,0 mm |
| Diâmetro do furo | 3,3 mm (0,15 mm de folga de cada lado) |
| Comprimento do pino | 3 mm |
| Chanfro na ponta | 0,5 mm (entra sem enroscar) |

### Capa

| Medida | Valor inicial |
|--------|---------------|
| Parede da capa | 0,8 mm (2 voltas de bico 0,4 mm) desde 25/10, para baixar o torque (era 1,2 mm, −68 g no robô); o clipe continua com 1,2 mm (região engrossada) |
| Encaixes por capa pequena (coxa, canela, pé) | 2 clipes + 2 pinos-guia |
| Encaixes por capa grande (tronco) | 4 clipes + 2 pinos-guia |

## Modelo de referência

Dois scripts, no mesmo sistema de coordenadas (posição montada), geram as duas metades — que são
também as duas peças da parte de encaixe da **peça de teste de tolerância**:

| Script | Metade | O que tem |
|--------|--------|-----------|
| `cad/parts/snap_clip.py` | **capa** | parede vertical com a lingueta + gancho, aba no topo que apoia no esqueleto, 2 pinos-guia descendo da aba |
| `cad/parts/snap_socket.py` | **esqueleto** | bloco com o rebaixo do gancho na face lateral e os 2 furos dos pinos na face de cima |

```
        aba da capa (apoia no topo do esqueleto)
   ┌───────────────────────────────┐   ← pinos-guia descem daqui para os furos
   │ parede lateral da capa        │
   │   ┌──────────lingueta───┐▶gancho entra no rebaixo da lateral do esqueleto
   │   └─────────────────────┘     │
   └───────────────────────────────┘
     a capa é empurrada para baixo; o gancho desliza na lateral e estala no rebaixo
```

Como a capa entra: **de cima para baixo**. Por isso:
- a lingueta corre **na horizontal** dentro da parede lateral — impressa deitada, como manda a regra;
- os pinos-guia são **verticais**, na mesma direção da entrada (de lado, a capa não desceria);
- a capa é impressa **de cabeça para baixo** (aba na mesa): lingueta na horizontal, pinos para cima.

O build do lado do esqueleto **monta as duas metades e confere** que não há material sobreposto
(a checagem foi testada: com o rebaixo 0,3 mm mais raso que o gancho, ela acusa).

Nota: os pinos têm 3 mm e o gancho começa a 4 mm do topo, então **o gancho toca a lateral antes de
os pinos entrarem nos furos** — alinhe a capa com a mão no começo; os pinos guiam os últimos 3 mm.
Se no teste isso incomodar, a saída é pino mais longo.

Cortes do encaixe montado: `cad/build/snap_preview.png` (gerado; não versionado).

As folgas (0,2 mm do gancho, 0,15 mm do pino) são o ponto de partida; o valor final sai da peça de
teste de tolerância, porque depende da impressora.
