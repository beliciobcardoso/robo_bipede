# Tutorial: servo SG90 no PartDesign (FreeCAD 1.1)

Objetivo: modelar o servo à mão com sketches totalmente restritos. Medidas digitadas direto nas
restrições — para ajustar depois, abra o sketch e edite a cota.

- Medidas: [medidas_servo_sg90.md](medidas_servo_sg90.md)
- Referência para conferir: `make servo_sg90` → `cad/build/servo_sg90.FCStd` (gerado por script)
- **Salve o seu em `cad/manual/servo_sg90.FCStd`** — `cad/build/` é sobrescrito a cada `make`.

## Convenção de eixos (obrigatória)

Os suportes vão depender disso:

- **Origem** no centro do eixo de saída, na face **de baixo** das abas.
- **+Z** aponta para o eixo de saída. **+X** ao longo do corpo, saindo do lado do eixo para o lado oposto.
- O corpo fica, portanto, de z = −17,0 até z = +7,2, e de x = −6,0 até x = +17,1.

## Conceitos que você vai usar

| Conceito | O que é |
|----------|---------|
| **Body** | Container de um sólido único no PartDesign. Tudo que você adiciona se funde nele. |
| **Sketch** | Desenho 2D num plano. Só vira 3D com Pad/Pocket. |
| **Restrição (constraint)** | Regra no sketch: distância, horizontal, simétrico, coincidente… |
| **Totalmente restrito** | Nenhum grau de liberdade sobrando. Geometria fica **verde** e o painel mostra *Fully constrained*. Sempre deixe assim — sketch frouxo "anda" quando algo muda. |
| **Pad / Pocket** | Extruda o sketch adicionando / removendo material. |
| **Attachment Offset** | Desloca o plano do sketch em relação ao plano onde foi anexado. Usado aqui no lugar de anexar em faces — mais robusto quando o modelo muda. |

Sinal das distâncias no Sketcher: ao selecionar **ponto A e depois ponto B**, a distância horizontal
é positiva se B está à direita de A (vertical: se B está acima de A).

## Medidas usadas

| Medida | Valor (mm) |
|--------|-----------|
| Corpo (comprimento × largura × altura) | 23,1 × 12,2 × 24,2 |
| Eixo → parede do lado do eixo | 6,0 (= metade do Ø da torre) |
| Topo do corpo (z) | 7,2 (= 24,2 − 17,0) |
| Abas (comprimento total × espessura) | 32,5 × 2,5 |
| Base do corpo → face de baixo da aba | 17,0 |
| Entre furos / Ø furo | 27,8 / 2,0 |
| Torre (Ø × altura) | 12,0 × 4,0 |
| Eixo de saída (Ø × altura) | 5,0 × 3,0 |
| Cabo (largura × espessura × comprimento) | 4,0 × 1,2 × 5,0 |
| Base do corpo → centro do cabo | 4,0 |

> **Atenção:** a torre rente à parede liga duas cotas. Se um dia mudar o Ø da torre, mude também
> o 6,0 do Passo 2 (metade do novo Ø).

---

## Passo 0 — Documento

`Arquivo → Novo`. Salve já como `cad/manual/servo_sg90.FCStd` (crie a pasta `manual`).

## Passo 1 — Body

Workbench **Part Design** → *Create body*. O Body fica ativo (nome em negrito). Expanda **Origin**
dentro dele: lá estão `XY_Plane`, `XZ_Plane`, `YZ_Plane` e os eixos.

## Passo 2 — Corpo (caixa principal)

1. Selecione `XY_Plane` → *Create sketch*.
2. Ferramenta **Rectangle**: desenhe um retângulo qualquer em volta da origem.
3. Restrições:
   - **Symmetric**: selecione o vértice de cima-esquerda, o de baixo-esquerda e o **eixo X** (linha
     horizontal vermelha) → *Constrain symmetric*. Isso centra o retângulo em Y.
   - **Distância vertical** no lado esquerdo → `12,2`.
   - **Distância horizontal** no lado de baixo → `23,1`.
   - **Distância horizontal**: selecione o vértice de baixo-esquerda, depois o ponto de origem → `6,0`.
4. Confira *Fully constrained* → *Close*.
5. Com o sketch selecionado → **Pad**:
   - *Type*: **Two dimensions**
   - *Length*: `7,2` (para cima)
   - *2nd length*: `17,0` (para baixo)
   - OK.

Checagem: o corpo deve ir de z = −17 a z = +7,2. Se crescer só para um lado, confira *Type*.

## Passo 3 — Abas com furos

Um sketch só: o retângulo das abas e os dois círculos. Círculo **dentro** de retângulo vira furo no Pad.

1. `XY_Plane` → *Create sketch* (z = 0 é a face de baixo das abas — por isso a origem foi posta aí).
2. **Rectangle** em volta da origem, maior que o corpo.
   - Symmetric dos dois vértices da esquerda com o eixo X.
   - Vertical do lado esquerdo → `12,2`.
   - Horizontal do lado de baixo → `32,5`.
   - Horizontal: vértice de baixo-esquerda → origem → `10,7`
     (centra as abas no corpo, não no eixo: 32,5/2 − (23,1/2 − 6,0)).
3. Dois **Circle**, um perto de cada ponta.
   - **Point on object**: centro de cada círculo → eixo X.
   - **Equal** entre os dois círculos + **Diameter** de um → `2,0`.
   - Horizontal: vértice de baixo-esquerda do retângulo → centro do círculo esquerdo → `2,35`
     ((32,5 − 27,8) / 2).
   - Horizontal: centro esquerdo → centro direito → `27,8`.
4. *Fully constrained* → *Close* → **Pad**, *Type* Dimension, *Length* `2,5` (para cima).

## Passo 4 — Torre

1. `XY_Plane` → *Create sketch* (desenha-se em z = 0; o plano sobe no item 3).
2. **Circle** com centro **na origem** (clique exatamente no ponto da origem — vira coincidente).
   - Diameter → `12,0`.
3. *Close*. Com o sketch selecionado, na aba **Data** das propriedades:
   *Attachment* → *Attachment Offset* → *Position* → **z** → `7,2`.
   O sketch sobe para o topo do corpo.
4. **Pad**, *Length* `4,0`.

Checagem: vista de cima (tecla 2) — a borda da torre deve tangenciar a parede do lado do eixo.

## Passo 5 — Eixo de saída

1. Mesmo processo do passo 4: círculo na origem, diâmetro `5,0`.
2. Attachment Offset z → `11,2` (7,2 + 4,0).
3. **Pad**, *Length* `3,0`.

## Passo 6 — Saída do cabo

Agora o sketch fica num plano vertical: `YZ_Plane`. Nele, o eixo horizontal do sketch é o **Y** global
e o vertical é o **Z** global; a normal do plano é **+X**.

1. `YZ_Plane` → *Create sketch*. **Rectangle** perto da base.
   - Symmetric: dois vértices de baixo com o **eixo vertical** do sketch.
   - Horizontal do lado de baixo → `4,0`.
   - Vertical do lado esquerdo → `1,2`.
   - Vertical: vértice de baixo-esquerda → origem → `13,6`
     (17,0 − 4,0 + 1,2/2; a origem está acima do cabo, por isso positivo).
2. *Close*. Attachment Offset → **z** (= X global, ao longo da normal) → `-6,0`.
   O sketch encosta na parede do lado do eixo.
3. **Pad**, *Length* `5,0`, marque **Reversed** — o padrão segue a normal (+X) e
   entraria no corpo; o cabo tem que sair para −X.

## Passo 7 (opcional) — Detalhes

- **Ressalto da engrenagem**: círculo Ø5,0 com centro a 5,6 mm da origem em +X, offset z = 7,2, Pad 3,5.
- **Furo do parafuso do eixo**: círculo Ø1,6 na origem, offset z = 14,2 (topo do eixo), **Pocket** 3,0.

## Teste final: está tudo restrito?

1. Abra cada sketch: todos devem estar verdes, com *Fully constrained*.
2. No Passo 2, mude o comprimento do corpo para 25 → Recompute (Ctrl+R): o corpo cresce para +X e
   torre, eixo e cabo continuam no lugar. Volte para 23,1.

Se algum sketch ficar vermelho ou laranja, ele estava sub-restrito ou com restrição conflitante —
abra, veja o painel *Solver messages* e corrija.

## Quando terminar

Salve em `cad/manual/servo_sg90.FCStd` e me avise: eu abro pelo FreeCADCmd e comparo volume e
caixa envolvente com o modelo gerado pelo script (sem o passo 7, a diferença esperada é de algumas
dezenas de mm³, do ressalto e do furo; a caixa envolvente deve bater).
