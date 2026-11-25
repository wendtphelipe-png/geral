# Criar um kit novo no Fusion 360 (molde kit M, 6 peças)

Versão para ler na tela (página): https://claude.ai/artifact/DJTtVmiBLe6L5YGBZPmZZn (cópia em `guia.html`).

Arquivos desta pasta:
| Arquivo | Para que serve |
|---|---|
| `kit_M_modelo.step` | Modelo completo: contramolde em branco + 6 caixas-limite das vagas + 6 pinos de referência |
| `contramolde_M_em_branco.step` | Só o contramolde em branco (se preferir montar do zero) |
| `pino_D.step` | O pino de encaixe em D, para juntar nas costas de cada peça |
| `../tampa_kit_M.stl` | A tampa universal (já impressa uma vez, serve em todos os kits) |

## Os números que não podem mudar
| O quê | Medida |
|---|---|
| Tamanho máximo de cada peça (tamanho M) | 64 mm de largura (X) × 82 mm de altura (Y) × 35 mm de espessura (Z), sem contar o pino |
| Silicone em volta das peças | **4 mm** (o modelo já tem a lâmina de 4 mm; as cavidades você faz com 4 mm de afastamento) |
| Plástico mínimo embaixo da cavidade mais funda | 2 mm |
| Pino D | 10 mm de diâmetro, lado reto a 3 mm do centro, sai 3,4 mm das costas, **no centro do retângulo da peça**, lado reto virado para o **topo** da peça |
| Centros das vagas (no modelo) | vaga 1 (−85; −51,5) · vaga 2 (0; −51,5) · vaga 3 (85; −51,5) · vaga 4 (−85; 51,5) · vaga 5 (0; 51,5) · vaga 6 (85; 51,5) |
| Altura das costas das peças (batente da tampa) | Z = 41 mm |

## Antes de começar (uma vez)
1. Unidades em **mm**: menu do usuário > Preferências > Unidades padrão > Projeto > mm.
2. Eixo **Z para cima**: Preferências > Geral > Orientação de modelagem padrão > **Z para cima**.

---

## Parte A: preparar cada peça (6 vezes)

Faça um arquivo do Fusion por peça. Posição de trabalho: **peça deitada de costas, frente para cima (+Z),
cabeça apontando para +Y, costas planas no plano XY (Z = 0)**.

1. **Trazer o modelo**
   - Desenho seu no Fusion: já é um sólido, siga para o passo 2.
   - STL baixado: Inserir > Inserir malha. Se tiver mais de uns 50 mil triângulos, use Malha > Modificar > Reduzir
     (uns 20 mil), depois Malha > Modificar > Converter malha (Facetado). Se a conversão falhar, me mande o STL.
2. **Costas planas**: se o modelo for um boneco inteiro (3D completo), corte ao meio:
   Modificar > Dividir corpo, usando um plano paralelo ao XY. Fique com a metade da frente.
   A peça precisa ter as costas **totalmente planas** em Z = 0.
3. **Tamanho**: Modificar > Escala (uniforme) até caber em 64 × 82 × 35 mm. Para ver a medida:
   clique com o botão direito no corpo > Propriedades > Caixa delimitadora.
   No kit todo, use a **mesma escala** nas 6 peças (fica uniforme).
4. **Centralizar**: nas Propriedades, anote Mín e Máx de X e Y da caixa delimitadora.
   Modificar > Mover/Copiar > Mover livre: X = −(MínX + MáxX) ÷ 2 ; Y = −(MínY + MáxY) ÷ 2.
   Agora o centro do retângulo da peça está na origem (0; 0) e as costas em Z = 0.
5. **Lugar do pino**: o centro das costas precisa ser maciço num círculo de 14 mm.
   Se ali for vazado (como o meio da Guirlanda), faça um esboço no plano XY, círculo de 14 mm na origem,
   e Extrudar 3 mm para dentro da peça (Unir).
6. **Juntar o pino**: Inserir > Inserir em projeto atual > `pino_D.step`. Ele já vem no lugar certo
   (centro na origem, saindo das costas para −Z, lado reto para +Y). Modificar > Combinar > **Unir** (peça + pino).
   - Se a peça for malha: crie o pino como malha (Malha > Criar > Mosaico/Tessellate) e use Malha > Modificar > Combinar > Unir.
7. **Exportar a peça para a resina**: botão direito no corpo > Salvar como malha > STL (milímetros).
   Na Mars 5 cabem 2 peças por mesa (143 × 90 mm). Use as configurações de suporte que já temos.

---

## Parte B: fazer o contramolde do kit

1. Arquivo novo > Inserir > Inserir em projeto atual > `kit_M_modelo.step`.
   Você vai ver o contramolde em branco (azul), 6 caixas amarelas transparentes (limite de cada vaga)
   e 6 pinos rosa (referência). Ele já está **na posição de impressão**: fundo na mesa, lâmina para cima.
   Vagas 1-2-3 na frente (Y negativo), 4-5-6 atrás. Canto chanfrado na frente à direita.
2. **Trazer as 6 peças prontas (com pino)**: Inserir > Inserir em projeto atual > cada peça.
3. **Virar cada peça de frente para baixo**: Mover/Copiar > Girar **180° em torno do eixo X**.
   Agora a frente aponta para −Z, o pino para +Z e a cabeça para −Y.
4. **Encaixar no pino de referência da vaga**: Modificar > Alinhar.
   Selecione a face de cima (a ponta) do pino da peça e depois a face de cima do pino rosa da vaga.
   Confira: as costas da peça ficam em Z = 41 (na altura do batente) e a peça fica dentro da caixa amarela.
   Repita para as 6 peças, cada uma na sua vaga (anote: vaga 1 = ..., vaga 2 = ...).
5. **Fazer o "envelope" de 4 mm de cada peça** (o espaço do silicone):
   - Peça sólida (corpo do Fusion): botão direito na peça > Copiar e Colar (cria uma cópia no mesmo lugar).
     Selecione todas as faces da cópia (janela de seleção) > Modificar > **Deslocar face**: 4 mm para fora.
   - Peça malha: Malha > Modificar > **Casca** (Shell) na cópia, espessura 4 mm, direção **Para fora**;
     depois Malha > Modificar > Combinar > Unir a casca com a cópia. Isso dá o envelope maciço.
   - Se o Fusion travar ou der erro nesse passo, me mande as 6 peças em STL que eu faço o contramolde.
6. **Esculpir**: Modificar > Combinar > **Cortar**. Corpo de destino: `contramolde_em_branco`.
   Corpos de ferramenta: os 6 envelopes. Deixe "Manter ferramentas" desmarcado.
7. **Esconder** as caixas amarelas, os pinos rosa e as peças (não apague as peças: elas vão para a resina).
8. **Conferir com corte de seção** (Inspecionar > Análise de seção):
   - ~4 mm de folga entre cada peça e a cavidade;
   - pelo menos 2 mm de plástico embaixo da cavidade mais funda.
9. **(Opcional, economiza filamento) Baixar o bloco**: se a peça mais grossa do kit tiver menos de 35 mm,
   empurre a face de baixo para cima (Pressionar/Puxar) em (35 − espessura da mais grossa) mm.
   Confira de novo os 2 mm embaixo da cavidade mais funda.
10. **Quanto silicone**: Combinar > Unir os 6 envelopes com uma caixa da lâmina (desenhe o contorno da lâmina
    em Z = 37 e extrude até 41), depois Cortar as 6 peças desse corpo. Propriedades > Volume: cm³ = ml.
    Prepare 10% a mais.
11. **Exportar**: botão direito no contramolde > Salvar como malha > STL. Ele já está na posição certa de imprimir.
    Imprima com `../CONFIG_PRUSASLICER.md` (Relâmpago 10%, 2 perímetros, topo 4, base 3, sem suporte).

## Montar o molde de silicone
Igual aos kits de Natal (`../README.md`): peças encaixadas na tampa pelo pino D (pelos números),
silicone no contramolde, tampa descendo de um lado para o outro até assentar no batente, peso até curar.
