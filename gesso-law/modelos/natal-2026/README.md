# Kit de Natal 2026 (versão 2): 8 peças

![Coleção](colecao.png)

| Peça | Arquivo | Medida (L x A x espessura) | Gesso aprox. |
|---|---|---|---|
| Papai Noel | `noel.stl` | 59 x 79 x 25 mm | 60 g |
| Boneco de Neve | `boneco.stl` | 51 x 78 x 25 mm | 55 g |
| Rena | `rena.stl` | 55 x 79 x 25 mm | 54 g |
| Pinguim com presente | `pinguim.stl` | 63 x 79 x 37 mm | 106 g |
| Árvore de Natal | `arvore.stl` | 51 x 79 x 25 mm | 36 g |
| Floco de Neve (desenho próprio) | `floco.stl` | 71 x 79 x 12 mm | 33 g |
| Meia de Natal | `meia.stl` | 63 x 79 x 25 mm | 83 g |
| Papai Noel na Chaminé | `chamine.stl` | 66 x 79 x 28 mm | 67 g |

(+ pino de encaixe de 4 mm nas costas)

## Regras desta versão
- **Sem alça e sem furo.** Cordão vai dentro do molde antes do gesso; ímã é enviado à parte.
- **Fundo orgânico**: placa de bordas arredondadas atrás do personagem que preenche os vãos de
  partes finas (galhada e orelhas da rena, braços do floco); o personagem fica em relevo sobre ela.
- **Pino de encaixe em D** nas costas (10 mm, 4 mm de altura, lado reto virado para o topo da peça),
  para plugar na base do molde.
- **Tamanho máximo para a Elegoo Mars 5** (mesa 143 x 90 mm): mesma escala para o lote todo, ~79 mm de
  altura. Pasta `mesas-resina/`: arquivos com 2 peças lado a lado, prontos para a mesa.

## Gerar de novo
Peças: `../relevo3d.py` com `--fundo` (ver `gerar.sh` da versão anterior). Floco: `floco_desenho.py`.
Finalização (escala, pino e mesas): `python ../finalizar_lote.py entrada saida noel boneco rena pinguim arvore floco meia chamine`.

## Origem dos modelos (Printables)
Papai Noel 1496792 · Boneco 1486887 · Rena 1487047 · Pinguim 1545550 · Árvore 1492523 ·
Meia 1445843 · Chaminé 1481334. Floco de neve: desenho próprio.
