# Tutorial: servo SG90 no PartDesign (FreeCAD 1.1)

Tutorial para quem está começando no FreeCAD. Cada passo diz **onde clicar**, **o que digitar** e
**o que você deve ver**. Os nomes de botões e menus estão exatamente como aparecem no FreeCAD 1.1
em inglês.

- Medidas de onde vieram os números: [medidas_servo_sg90.md](medidas_servo_sg90.md)
- Arquivo onde salvar: **`cad/manual/servo_sg90.FCStd`**
  (não salve em `cad/build/` — essa pasta é apagada e refeita a cada `make`)

---

## Parte 1 — Vocabulário

Leia antes de começar. São só estas palavras:

| Palavra | O que é |
|---------|---------|
| **Linha** | Um traço reto do desenho. O retângulo tem 4 linhas. |
| **Vértice** | Um **ponto**: a bolinha no canto, onde duas linhas se encontram. O retângulo tem 4 vértices. O centro de um círculo também é um vértice. |
| **Origem** | O ponto (0, 0): onde o eixo vermelho cruza o eixo verde no desenho. É um vértice também. |
| **Sketch** (esboço) | Um desenho 2D, plano. Sozinho não tem volume. |
| **Restrição** (constraint) | Uma medida ou regra que você dá ao desenho: "esta linha mede 23,1", "este ponto está a 6,0 da origem". |
| **Totalmente restrito** | O desenho não pode mais se mexer: todas as medidas foram dadas. O desenho fica **verde**. É o objetivo de todo sketch. |
| **Pad** | Transforma o sketch em sólido, "puxando" o desenho para cima (como massinha num molde). |
| **Body** | A "caixa" que guarda o sólido. Tudo que você fizer com Pad se junta dentro dela. |

```
 vértice ●───────── linha ─────────● vértice
         │                         │
       linha                     linha
         │                         │
 vértice ●───────── linha ─────────● vértice
```

## Parte 2 — A tela do FreeCAD

```
┌──────────────────────────────────────────────────────────────┐
│ File  Edit  View  ...  Part Design  ...      ← menus         │
│ [ícones dos botões]                          ← barras        │
├──────────────┬───────────────────────────────────────────────┤
│ Model | Tasks│                                               │
│              │                                               │
│  (árvore)    │            área 3D / desenho                  │
│              │                                               │
│──────────────│                                               │
│ View | Data  │                                               │
│ (propriedades│                                               │
└──────────────┴───────────────────────────────────────────────┘
```

- **Painel da esquerda** (*Combo View*) tem duas abas no topo:
  - **Model**: a árvore com tudo que você criou.
  - **Tasks**: as janelas das ferramentas (ex.: o Pad abre aqui). Abre sozinha quando precisa.
- Se não estiver vendo esse painel: menu **View → Panels → Combo View**.
- **Passar o mouse sobre um ícone** mostra o nome dele. Use isso para achar os botões deste tutorial.

### Como selecionar dentro do sketch

- Clique em um elemento → ele fica **verde-claro** (selecionado).
- Clique em outro → ele **entra junto** na seleção (não precisa segurar Ctrl).
- Para **limpar a seleção**: clique num espaço vazio.
- Passe o mouse antes de clicar: o que vai ser selecionado fica **amarelo**. Para pegar um
  **vértice**, chegue bem perto da bolinha até **só ela** ficar amarela (não a linha inteira).

### Como sair de uma ferramenta

Se uma ferramenta de desenho ficou ativa (o cursor muda de forma), aperte **Esc** ou clique com o
**botão direito**.

### Errou?

**Ctrl+Z** desfaz. Sempre.

---

## Parte 3 — Onde fica o servo no espaço

Os suportes do robô vão ser desenhados em cima destas regras. Siga exatamente:

- O **ponto (0, 0, 0)** fica no **centro do eixo de saída** (o eixinho branco), na altura da
  **face de baixo das abas**.
- O corpo do servo vai **para baixo** (até −17,0) e um pouco **para cima** (até +7,2).
- O corpo se estende **para a direita** (+X). O eixo fica perto da ponta esquerda.

Vista de cima (o desenho do Passo 3):

```
                 Y
                 ↑
   ●─────────────┼─────────────────────────────────┐
   │             │                                 │
   │    eixo →   ┼─────────────────────────────────┼──→ X
   │           origem                              │
   ●─────────────┴─────────────────────────────────┘
   ↑                                               
 vértice de baixo-esquerda
   |←── 6,0 ───→|←──────────── 17,1 ──────────────→|
   |←────────────────── 23,1 ─────────────────────→|
```

---

## Passo 1 — Criar e salvar o documento

1. Menu **File → New** (ou Ctrl+N).
2. Menu **File → Save As…**
3. Navegue até a pasta do projeto → `cad` → `manual` (se não existir, crie).
4. Nome: `servo_sg90` → **Save**.

Daqui em diante, aperte **Ctrl+S** de vez em quando.

## Passo 2 — Abrir o Part Design e criar o Body

1. Na barra de cima há uma lista de *workbenches* (bancadas). Escolha **Part Design**.
   Se não achar: menu **View → Workbench → Part Design**.
2. Menu **Part Design → New Body**.
   (É o ícone de um **cubo azul com contorno amarelo**, o primeiro da barra do Part Design.)

**Você deve ver**: na aba **Model**, um item **Body** em **negrito** (negrito = ativo).
Dentro dele, uma pasta **Origin**.

## Passo 3 — Corpo do servo

### 3.1 Abrir o sketch

1. Menu **Part Design → New Sketch**.
2. Na aba **Tasks** aparece uma lista de planos. Clique em **XY_Plane** → **OK**.

**Você deve ver**: uma grade, o **eixo vermelho** (horizontal, X) e o **eixo verde** (vertical, Y)
cruzando no meio. O cruzamento é a **origem**.

### 3.2 Desenhar o retângulo

1. Menu **Sketch → Sketcher geometries → Rectangle** (ou o ícone de retângulo na barra).
2. Clique **uma vez** abaixo e à esquerda da origem (canto de baixo-esquerda).
3. Clique **uma vez** acima e bem à direita da origem (canto de cima-direita).
   A origem deve ficar **dentro** do retângulo, **perto do lado esquerdo** — igual ao desenho da
   Parte 3. O tamanho não importa agora.
4. Aperte **Esc** para sair da ferramenta.

Se aparecerem caixinhas com números enquanto desenha, ignore — só clique.

**Não clique em cima dos eixos** (vermelho ou verde) ao desenhar o retângulo: o FreeCAD
"prende" o canto no eixo e isso atrapalha as medidas. Clique sempre num espaço livre da grade.

### 3.3 Dar as medidas

Cada medida: **selecione** o que diz a tabela → clique na **ferramenta** → digite o **valor** → **OK**.
As ferramentas estão no menu **Sketch → Sketcher constraints** (ou nos ícones de cota da barra).

| # | Selecione | Ferramenta | Valor |
|---|-----------|------------|-------|
| a | a **linha de baixo** | **Horizontal Dimension** | `23,1` |
| b | a **linha da esquerda** | **Vertical Dimension** | `12,2` |
| c | o **vértice de baixo-esquerda**, depois a **origem** | **Horizontal Dimension** | `6,0` |
| d | o **vértice de baixo-esquerda**, depois a **origem** | **Vertical Dimension** | `6,1` |

Depois de cada uma, limpe a seleção clicando num espaço vazio.

O que cada uma faz: (a) e (b) dão o tamanho do retângulo; (c) diz que a parede esquerda fica 6,0 à
esquerda da origem; (d) diz que a linha de baixo fica 6,1 abaixo da origem — como 6,1 é metade de
12,2, o retângulo fica centrado no eixo vermelho.

**Você deve ver**: o desenho inteiro fica **verde**, e na aba **Tasks**, em *Solver messages*,
aparece **Fully constrained**. Se não ficou verde, falta medida. Se algo ficou **vermelho**, a
última medida conflita: **Ctrl+Z** e confira a tabela.

### 3.4 Fechar o sketch

Na aba **Tasks**, clique em **Close** (no topo do painel).

### 3.5 Transformar em sólido (Pad)

1. Na aba **Model**, clique no sketch que você acabou de criar (**Sketch**).
2. Menu **Part Design → Pad**.
3. Na aba **Tasks**:
   - **Type**: troque de *Dimension* para **Two dimensions**.
   - **Length**: `7,2` (quanto sobe acima da origem)
   - **2nd length**: `17,0` (quanto desce abaixo da origem)
4. **OK**.

**Você deve ver**: uma caixa. Aperte **0** (zero) no teclado para a vista em perspectiva.
A maior parte da caixa fica **abaixo** do plano da origem.

## Passo 4 — Abas com os furos

Agora um sketch com o retângulo das abas **e** dois círculos. Círculo dentro de retângulo vira **furo**.

Vista de cima, cotas medidas a partir da origem:

```
  ●────────────────────────────┼──────────────────────────────────────┐
  │   ○                        │                                  ○   │
  │ furo                       ┼ origem                         furo  │
  │                            │                                      │
  ●────────────────────────────┴──────────────────────────────────────┘
  |←──────── 10,7 ────────────→|
      |←──── 8,35 ────────────→|←─────────────── 19,45 ──────────→|
                          (centro dos furos)
```

### 4.1 Abrir o sketch

**Part Design → New Sketch** → **XY_Plane** → **OK**.
(O corpo some de vista? Normal: o FreeCAD esconde o sólido enquanto edita. Pode continuar.)

### 4.2 Desenhar

1. **Rectangle**: um retângulo **maior** que o do corpo, com a origem dentro, um pouco à esquerda
   do meio. Cantos fora dos eixos, como antes. **Esc**.
2. Menu **Sketch → Sketcher geometries → Circle From Center** (ícone de círculo).
3. Clique **em cima do eixo vermelho**, perto da ponta esquerda do retângulo (centro do círculo),
   depois clique um pouco ao lado (tamanho do círculo).
4. Repita perto da ponta direita, também **em cima do eixo vermelho**. **Esc**.

Ao clicar em cima do eixo vermelho aparece um símbolo pequeno ao lado do cursor: o FreeCAD já
"prendeu" o centro no eixo. Se não apareceu, tudo bem — o item **g** abaixo resolve.

### 4.3 Dar as medidas

| # | Selecione | Ferramenta | Valor |
|---|-----------|------------|-------|
| a | a **linha de baixo** do retângulo | **Horizontal Dimension** | `32,5` |
| b | a **linha da esquerda** do retângulo | **Vertical Dimension** | `12,2` |
| c | **vértice de baixo-esquerda** do retângulo, depois a **origem** | **Horizontal Dimension** | `10,7` |
| d | **vértice de baixo-esquerda** do retângulo, depois a **origem** | **Vertical Dimension** | `6,1` |
| e | a **borda** de um círculo, depois a **borda** do outro | **Equal Constraint** | (sem valor) |
| f | a **borda** de um círculo | **Diameter Dimension** | `2,0` |
| g | o **centro** de cada círculo + o **eixo vermelho** (um círculo por vez) — só se o símbolo não apareceu no 4.2 | **Point-On-Object Constraint** | (sem valor) |
| h | o **centro do círculo esquerdo**, depois a **origem** | **Horizontal Dimension** | `8,35` |
| i | a **origem**, depois o **centro do círculo direito** | **Horizontal Dimension** | `19,45` |

Para pegar o **centro** do círculo: passe o mouse no meio dele até a bolinha central ficar amarela.

De onde vêm os números: abas com 32,5 centradas no corpo → a ponta esquerda fica a 10,7 da origem;
furos a 27,8 um do outro, também centrados no corpo → 8,35 à esquerda e 19,45 à direita.

**Você deve ver**: tudo **verde** e **Fully constrained**. **Close**.

### 4.4 Pad

1. Selecione o novo sketch na árvore (**Sketch001**).
2. **Part Design → Pad**.
3. **Type**: **Dimension**. **Length**: `2,5`. **OK**.

**Você deve ver**: uma placa fina atravessando o corpo, sobrando dos dois lados, com um furo em
cada ponta.

## Passo 5 — Torre (o cilindro grande no topo)

Truque para não complicar: o sketch fica no mesmo plano da origem e o Pad **sobe direto até o
topo da torre**. A parte que fica dentro do corpo some na junção — o resultado é o mesmo.

1. **New Sketch** → **XY_Plane** → **OK**.
2. **Circle From Center**: clique **exatamente na origem** para o centro (a origem fica amarela
   antes de clicar), depois clique ao lado. **Esc**.
3. Selecione a borda do círculo → **Diameter Dimension** → `12,0`.
4. Deve ficar **verde / Fully constrained**. **Close**.
5. Selecione o sketch na árvore → **Pad** → **Type**: Dimension → **Length**: `11,2` → **OK**.

(11,2 = 7,2 do topo do corpo + 4,0 de altura da torre.)

**Confira**: aperte **2** (vista de cima). A borda da torre deve encostar na parede esquerda do
corpo, sem passar dela.

## Passo 6 — Eixo de saída

Igual ao passo 5:

1. **New Sketch** → **XY_Plane** → **OK**.
2. **Circle From Center** com centro **na origem**. **Esc**.
3. Borda do círculo → **Diameter Dimension** → `5,0`. **Close**.
4. **Pad** → **Length**: `14,2` → **OK**.

(14,2 = 11,2 do topo da torre + 3,0 do eixo.)

## Passo 7 — Saída do cabo

Agora o sketch fica num plano **em pé**, o **YZ_Plane**. Nele, o eixo horizontal do desenho é a
**largura** do servo e o vertical é a **altura**.

Vista do desenho (olhando de lado):

```
                 ┼  origem
                 │
                 │  13,6
                 │
            ●────┼────┐  ← cabo: 4,0 de largura × 1,2 de altura
            │    │    │
            ●────┴────┘
            |←2,0→|
```

1. **New Sketch** → **YZ_Plane** → **OK**.
2. **Rectangle** pequeno **bem abaixo** da origem, cruzando o eixo vertical. **Esc**.
3. Medidas:

| # | Selecione | Ferramenta | Valor |
|---|-----------|------------|-------|
| a | a **linha de baixo** | **Horizontal Dimension** | `4,0` |
| b | a **linha da esquerda** | **Vertical Dimension** | `1,2` |
| c | **vértice de baixo-esquerda**, depois a **origem** | **Horizontal Dimension** | `2,0` |
| d | **vértice de baixo-esquerda**, depois a **origem** | **Vertical Dimension** | `13,6` |

(13,6 = 17,0 − 4,0 + 0,6: o centro do cabo fica 4,0 acima da base do corpo.)

4. **Verde / Fully constrained** → **Close**.
5. Selecione o sketch → **Pad** → **Type**: Dimension → **Length**: `11,0`.
6. Olhe a prévia: o cabo tem que **sair pela parede esquerda** (o lado onde a torre encosta).
   Se ele estiver saindo pelo outro lado, marque **Reversed**.
7. **OK**.

(11,0 = 6,0 de dentro do corpo + 5,0 para fora.)

## Passo 8 (opcional) — Ressalto da engrenagem

O cilindrinho ao lado da torre. Mesma ideia do passo 5:

1. **New Sketch** → **XY_Plane**.
2. **Circle From Center** com o centro **em cima do eixo vermelho**, à direita da torre.
3. Medidas: **Diameter Dimension** `5,0`; **origem → centro** com **Horizontal Dimension** `5,6`.
4. **Close** → **Pad** → **Length** `10,7` (7,2 + 3,5).

---

## Conferência final

1. Aperte **0** (perspectiva) e gire com o botão do meio do mouse. O servo deve parecer com o real.
2. Na árvore, dê **duplo clique** em cada sketch: todos devem abrir **verdes**. **Close** em cada um.
3. **Ctrl+S**.

### Problemas comuns

| Problema | Causa provável | O que fazer |
|----------|----------------|-------------|
| Botão cinza, não clica | Nada selecionado, ou seleção errada | Confira a coluna "Selecione" da tabela |
| Desenho não fica verde | Falta medida | Compare com a tabela, linha por linha |
| Algo fica vermelho | Medida conflitante ou repetida | Ctrl+Z e refaça só a última |
| A cota foi para o lugar errado | Pegou a linha em vez do vértice | Ctrl+Z, passe o mouse até **só a bolinha** ficar amarela |
| Pad cresceu para o lado errado | Direção | Marque/desmarque **Reversed** |
| Sumiu a árvore ou o painel | Painel fechado | **View → Panels → Combo View** |

## Quando terminar

Salve e me avise. Eu abro o seu arquivo e comparo com o modelo gerado pelo script (volume e
tamanho total). Se travar em algum passo, me diga **o número do passo e da linha da tabela** e,
se der, mande um print.
