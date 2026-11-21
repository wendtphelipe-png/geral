# Molde KIT M (desde 21/11/2026): contramolde por kit + tampa universal

Mesma ideia do molde padrão M (sanduíche com ~3,5 mm de silicone, **silicone numa peça só** com as 6
cavidades), feita para imprimir rápido e barato. Gerador: `../molde_kit.py`.

| Peça | Quando imprime | Medida | Material (ABS, aprox.) |
|---|---|---|---|
| `tampa_kit_M.stl` (aqui) | **uma vez só**, serve em todos os kits | 256 x 207 x 7 mm | ~171 g |
| `contramolde.stl` (em cada coleção, `parte-N/molde-kit/`) | um por kit | 263 x 214 x ~42 mm | ~270 g (Relâmpago) |

- O contramolde já é a moldura: parede contra vazamento + batente onde a tampa assenta.
  Altura só a da peça mais grossa do kit. Nomes das vagas e da coleção gravados no fundo.
- A tampa tem os 6 encaixes em D (números 1 a 6), respiros e nervuras. Um canto chanfrado faz ela
  só entrar de um jeito.

## Imprimir (nenhuma das duas precisa de suporte)
- Contramolde: fundo plano na mesa, cavidades para cima (o arquivo já vem assim).
  Preenchimento **Relâmpago (Lightning)** 10 a 15% (ou giroide 5 a 8%), 3 perímetros, 5 camadas de topo, camada 0,28 mm.
- Tampa: face lisa na mesa, nervuras para cima (o arquivo já vem assim). 3 perímetros.
- Contramolde e tampa no mesmo material e com a mesma compensação de encolhimento.

## Fazer o silicone
1. Desmoldante no contramolde, na tampa e nas peças de resina.
2. Encaixar as 6 peças na tampa pelos pinos em D, pela face lisa, seguindo os números (peças penduradas).
3. Despejar o silicone no contramolde (volume em `LEIA.txt` da coleção).
4. Descer a tampa (face lisa para baixo, canto chanfrado no canto chanfrado) até assentar no batente.
   O excesso sai pelos respiros. Peso em cima até curar.
5. Tirar a tampa com as peças: o silicone (peça única) fica no contramolde, pronto para o gesso.
