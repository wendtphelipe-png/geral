# Gesso Law

Ideia de negócio física: lembranças de gesso para aniversários e datas comemorativas.

## A ideia
- Peças de gesso feitas em **moldes personalizados** (personagens, objetos, temas de festa).
- Cada peça vai embalada com **potinhos de tinta** para crianças e adultos pintarem.
- Usos: lembrancinha de aniversário, enfeite de árvore de Natal, presente, decoração.

## O desafio principal: os moldes
Caminho escolhido:
1. Modelar a peça em 3D (arquivo `.stl`).
2. Imprimir na impressora 3D: essa é a **peça-mestre**.
3. Fazer o molde de silicone a partir da peça-mestre.
4. Produzir as peças de gesso no molde de silicone, quantas vezes for preciso.

## O que o Claude consegue modelar
O Claude não usa um programa de desenho com o mouse; ele escreve um pequeno programa que gera a peça.
Isso funciona muito bem para:
- formas geométricas e silhuetas: estrelas, corações, bolas de Natal, nuvens, balões, coroas, números e letras;
- placas e medalhões com relevo, bordas para pintar dentro e furo para fita;
- personagens **simples e estilizados** desenhados a partir de formas (ex.: ursinho, foguete, árvore, carrinho);
- versões em vários tamanhos, com nome ou número, a partir da mesma base;
- conferir se a peça está fechada e pronta para imprimir, e a medida exata.

Onde há limite:
- personagens orgânicos e muito detalhados (rosto realista, pelos, roupa com dobras) ficam melhores
  num escultor digital (Blender, Nomad Sculpt, ZBrush) ou comprando o modelo pronto;
- personagens de marca (Disney, Marvel, etc.) têm direitos autorais: para vender, é preciso licença.

Um bom caminho misto: o Claude faz a base técnica (placa, borda, furo, saída do molde) e
o personagem entra como relevo baixo a partir de um desenho de contorno.

## Regras para uma boa peça de gesso
- **Costas planas**: a peça assenta no fundo do molde e fica em pé ou pendurada.
- **Ângulo de saída**: as laterais levemente inclinadas (topo menor que a base) para desmoldar fácil.
- **Sem "ganchos" (contrassaídas)**: nada que prenda o gesso no molde.
- **Relevo baixo e arredondado**: entre 1 e 3 mm; nada de pontas finas que quebram.
- **Espessura mínima** de uns 6 a 8 mm na base para não trincar.
- **Borda alta** em volta das áreas de cor: ajuda a criança a pintar dentro.
- **Furo com reforço** (uns 4 mm) para fita, longe da borda.
- Tamanho de lembrancinha: entre 5 e 9 cm.

## Peça-teste: `modelos/estrela_natal`
- `estrela_natal.stl`: arquivo para a impressora (72 x 69 x 9 mm, peça fechada).
- `estrela_natal.png`: prévia.
- `estrela_natal.py`: o programa que gera a peça. As medidas ficam no topo do arquivo.

Para gerar de novo: `pip install manifold3d trimesh numpy` e depois `python estrela_natal.py`.

## Como pedir uma nova peça
Mande, do jeito que for mais fácil:
- o tema e o que deve aparecer (ex.: "foguete com o número 5");
- o tamanho aproximado em centímetros;
- se vai pendurar (furo) ou ficar em pé (base);
- se possível, uma foto ou desenho de referência.
