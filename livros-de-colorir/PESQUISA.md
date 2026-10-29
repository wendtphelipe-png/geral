# Fábrica de livros de colorir: pesquisa inicial

Pesquisa feita em 29/10/2026. Objetivo: vender livros de colorir no mundo inteiro, em arquivo (PDF) e em papel (impresso sob demanda), com o trabalho tocado por agentes de IA dentro da StarNet.

> **Como ler os números.** Muitos dados de preço e de vendas vêm de blogs e ferramentas de terceiros, não das próprias plataformas. Onde a informação não foi confirmada na fonte oficial, está marcado como **(confirmar)**. Antes de gastar dinheiro, confere-se no site de cada empresa.

---

## 1. Resumo em 10 linhas

1. **A Amazon KDP já é o "fornecedor de impressão" para quem compra na Amazon.** Ela imprime, embala e entrega sozinha; você só sobe o PDF. Não precisa de gráfica externa para vender na Amazon.
2. **A gráfica externa (Lulu, Gelato etc.) só é necessária para vender o livro físico fora da Amazon**: na sua própria loja (Shopify), no Etsy ou na Hotmart.
3. **PDF para imprimir em casa** vende melhor no **Etsy**; depois vêm Payhip, Gumroad e Creative Fabrica.
4. **No Brasil**, o caminho mais simples para o físico é **Hotmart + UICLAP** (integração pronta) ou o **Clube de Autores**.
5. **A moda atual é o estilo "Bold & Easy" / "Cozy"** (traço grosso, formas grandes, cenas aconchegantes). Em outubro de 2025, quase metade dos livros de colorir adultos mais vendidos da Amazon era desse estilo.
6. **Concorrente de referência: Coco Wyo**, um coletivo de artistas do Vietnã que começou se autopublicando na Amazon e assinou contrato de seis dígitos com a Penguin Random House.
7. **Desenho:** o caminho gratuito é o modelo **FLUX** (ou SDXL) com um "estilo de livro de colorir" (LoRA), rodando na placa de vídeo do PC, mais limpeza automática do traço. Mandalas e padrões geométricos podem ser desenhados por código, sem IA de imagem.
8. **A Amazon KDP não tem API.** A publicação lá terá de ser feita pelo navegador, com o Phelipe aprovando cada livro. Etsy, Lulu, Gelato e Shopify têm API.
9. **StarNet** (encontrei: `github.com/androoAGI/starnet`) é um programa gratuito que roda no PC e organiza agentes de IA em "salas" e "linhas de produção", com agendamento, aprovações e conexão com outros serviços. Serve bem para essa fábrica.
10. **Maior risco:** a Amazon endureceu com livros de colorir feitos por IA de baixa qualidade. O diferencial tem de ser **qualidade e identidade visual**, não volume.

---

## 2. StarNet: o que é e como serviria

Não havia nada sobre StarNet nos seus repositórios, Notion ou Drive. Na internet, encontrei o projeto abaixo, que bate com o que você descreveu. **Confirme se é esta a StarNet que você quer usar.**

| Item | O que é |
|---|---|
| Endereço | [github.com/androoAGI/starnet](https://github.com/androoAGI/starnet) (download em [starnet-releases](https://github.com/androoAGI/starnet-releases/releases/latest)) |
| O que faz | Uma "estação espacial" em pixel-art onde cada agente de IA é um tripulante. **Sala = equipe com permissões. Corredor = passagem de trabalho de um agente para outro. Objeto colocado = uma permissão real.** |
| Licença e custo | Gratuita, código aberto (MIT). Paga-se só o uso da IA (ou nada, com modelo local via Ollama) |
| Onde roda | Windows (o mais testado) e Mac. Versão atual 0.14.1. Ainda é "early release" |
| Cérebro | OpenRouter, Anthropic, OpenAI, Google, Ollama, e **o próprio Claude Code instalado no PC** (usa a sua assinatura, sem chave guardada na StarNet) |
| Recursos úteis para nós | Vários agentes ao mesmo tempo, cada um com memória e permissões próprias; **linhas de produção** (entrada → estações → saída), **agendamento** (cron), **"Night Shift"** (trabalha à noite com limites e registro de tudo), **pergunta antes de adivinhar** (manda a dúvida pelo Telegram, Slack, Discord etc.), **conectores MCP**, **controle do computador** no Windows, controle de **gastos e orçamento**, pasta **OUTBOX** com os arquivos prontos |
| Habilidades (skills) | Aceita skills no padrão `SKILL.md` (o mesmo do Claude Code). Já vem com 56, entre elas `line-design` (montar linha de produção), `seo-audit`, `pricing-strategy`, `customer-research`, `competitor-news-monitor`, `brand-assets` |

Avaliação honesta: um analista que testou disse que, por enquanto, ela é "mais divertida do que pronta para automação séria". Por isso, a sugestão é **deixar na StarNet a coordenação e as tarefas de texto/pesquisa**, e colocar as partes que mexem com dinheiro e pedidos em integrações prontas e previsíveis (por exemplo, Shopify enviando o pedido sozinho para a Lulu).

---

## 3. Onde vender

### 3.1 Livro físico (impresso sob demanda)

| Plataforma | Alcance | Quanto fica para você | Automação | Observações |
|---|---|---|---|---|
| **Amazon KDP** | EUA, Reino Unido, Europa, Japão, Canadá, Austrália etc. Brasil **(confirmar)** | 60% do preço menos o custo de impressão. **Abaixo de US$ 9,99, cai para 50%** (desde 10/06/2025). Distribuição expandida: 40% | **Sem API.** Só pelo site (dá para semiautomatizar com navegador) | A Amazon imprime e entrega. Exige marcar quando o conteúdo é gerado por IA. Rejeita traço quebrado, cinza, páginas repetidas, menos de 24 páginas. Fontes citam limite de novos títulos por dia **(confirmar)** |
| **IngramSpark** | 45 mil livrarias, bibliotecas e lojas | Taxa de acesso ao mercado de 1,875% (desde 01/02/2026) + desconto de livraria | Sem API pública encontrada | Bom para chegar a livrarias. Sem taxa de revisão desde 2026 **(confirmar taxa de cadastro)** |
| **Sua loja (Shopify)** + gráfica | Mundo | Preço que você definir menos impressão e frete | Total: Lulu e BookVault têm app oficial para Shopify | Margem maior, mas você precisa trazer o público |
| **Mercado Livre / Shopee** | Brasil | Comissão da plataforma | APIs existem | Mercado de físicos competitivo (R$ 10 a R$ 60 por livro) |
| **Hotmart (produto físico)** | Brasil | Preço menos produção e frete | Integração pronta com a UICLAP | Só para produtores no Brasil |

### 3.2 Arquivo para imprimir em casa (PDF)

| Plataforma | Por que usar | Taxas (aprox.) | API |
|---|---|---|---|
| **Etsy** | O maior mercado de "printables" do mundo, com compradores procurando | US$ 0,20 por anúncio + 6,5% de transação + ~3% + US$ 0,25 de pagamento + anúncios externos de 12–15% quando a venda vem deles | **Sim** (API v3 cria anúncio e sobe o arquivo digital) |
| **Creative Fabrica** | Público de artesãos e designers; vende por assinatura | Repasse por participação **(confirmar)** | Não encontrada |
| **Payhip** | Taxa baixa, entrega na hora, cuida do imposto europeu | 5% no plano grátis | Limitada |
| **Gumroad** | Ele é o "vendedor oficial" e cuida dos impostos no mundo todo | 10% | Sim |
| **Teachers Pay Teachers** | Professores (páginas educativas) | **(confirmar)** | Não |
| **Hotmart** | Brasil e América Latina, em reais | Comissão da Hotmart | Sim |

Observação: o **Kindle (e-book) não serve** para livro de colorir. Na Amazon, o produto é o livro impresso.

---

## 4. Concorrentes e produtos parecidos

| Quem | O que faz | Lição para nós |
|---|---|---|
| **Coco Wyo** (Vietnã) | Coletivo de artistas. Estilo "Bold & Easy" e "Cozy" (ex.: *Cozy Friends*, *Cozy Days*), a partir de US$ 7,99. Chegou a ter 5 livros no Top 100 dos EUA e 4 dos 18 mais vendidos adultos. Vende na Amazon e PDF no Etsy. Assinou com a Penguin Random House | **Identidade visual forte + séries** com o mesmo estilo. Também há polêmica de cópias do estilo deles, então nada de imitar |
| **Meg Miles Coloring** | Apontada como uma das criadoras do estilo "Bold & Easy" | O estilo nasceu em comunidades (Reddit, 2024) |
| **Jade Summer** | Editora grande de colorir para adultos, muitas séries | Volume com padrão de qualidade |
| **Imagi Press** | Infantil (toddler). Um título com ~4.400 avaliações e ~800 vendas/mês estimadas a US$ 5,99 | Infantil vende muito, mas a margem é pequena |
| Nichos citados | Mandalas para adultos, humor adulto, enfermagem, anatomia (veterinária), axolote (best-seller rendendo US$ 1.200–1.800/mês) | Nichos específicos e profissões funcionam |

Tamanho do mercado: uma estimativa coloca o mercado mundial de colorir para adultos em US$ 151 milhões (2024), indo a US$ 320 milhões em 2030 **(estimativa de terceiros)**.

---

## 5. Fornecedores de impressão e envio (print on demand)

### Internacionais

| Fornecedor | Base | Como recebe o pedido | Custos | Pontos fortes | Atenção |
|---|---|---|---|---|---|
| **Amazon KDP** | EUA/Europa/Japão etc. | Automático (é a própria Amazon) | Custo fixo + por página, conforme a loja | Zero trabalho | Só vende na Amazon |
| **Lulu (Print API / Lulu Direct)** | EUA, imprime perto do comprador | **API REST** e apps para Shopify, Wix e WooCommerce | Sem mensalidade. Paga impressão + frete + US$ 0,75 por pedido. Referência antiga: 8,5×11" brochura ~US$ 5,48 **(confirmar no calculador)** | Mais de 150 países, 3.200 combinações, espiral e capa dura | – |
| **Gelato** | 250+ gráficas em 32 países | **API REST** + integrações | Paga só quando vende | Imprime no país do comprador (frete menor) | Linha de livros focada em infantil personalizado, até 200 páginas. **Confirmar papel adequado para colorir** |
| **Peecho** | Holanda, rede mundial | **API grátis** | Sob consulta | Feita para livros | Se uniu à Prodigi; conferir como ficou |
| **BookVault** | Reino Unido | App para Shopify e WooCommerce | Sob consulta | Bom para Europa e Reino Unido, acabamentos especiais | API pública não encontrada |
| **IngramSpark** | Mundo | Distribuição para livrarias | Ver item 3.1 | Livrarias e bibliotecas | Não é para pedido direto de loja própria |
| Printful / Printify | – | – | – | – | **Não encontrei livro de colorir no catálogo deles** |

### Nacionais (Brasil)

| Fornecedor | Como funciona | Automação | Atenção |
|---|---|---|---|
| **UICLAP** | Imprime sob demanda; o autor paga só produção e frete das unidades vendidas | **Integração pronta com a Hotmart** (produtos físicos) | Há reclamação pública (dez/2025) de qualidade e troca de papel. **Pedir amostra antes** |
| **Clube de Autores** | Publica grátis, vende no site deles e em livrarias parceiras; o custo é descontado e o resto vai para o autor | API não encontrada | Reclamação isolada de atendimento (dez/2025) |
| **UmLivro (Meta Brasil)** | Gráfica industrial de impressão sob demanda (atende editoras grandes) | B2B, por contato comercial | Para volume |
| **Bookwire Brasil** | Distribuição digital e impressão sob demanda para editoras | B2B | Para quando virar editora |

Ponto em aberto: **não confirmei se a Amazon.com.br já vende livro impresso da KDP**. Se vender, ela resolve também o Brasil.

---

## 6. Como criar desenhos de alta qualidade

Importante: **o Claude não gera imagens de pixel diretamente.** Ele escreve desenhos vetoriais (SVG) por código, o que é ótimo para mandalas, padrões e formas geométricas, e controla os programas de imagem. Para animais, pessoas e cenas, é preciso um modelo de imagem.

### 6.1 Motores de imagem

| Opção | Custo | Onde roda | Comentário |
|---|---|---|---|
| **FLUX.1-dev + LoRA "Coloring Book"** ([renderartist/coloringbookflux](https://huggingface.co/renderartist/coloringbookflux)) | Grátis | Placa de vídeo do PC | O mais indicado para traço limpo. Treinado em pessoas, veículos e animais; ajuda escrever "white background". Na GTX 1070 Ti (8 GB) só roda em versão comprimida e devagar. **Conferir a licença do FLUX.1-dev para uso comercial das imagens** |
| [prithivMLmods/Coloring-Book-Flux-LoRA](https://huggingface.co/prithivMLmods/Coloring-Book-Flux-LoRA) | Grátis | PC | Ainda "em treinamento" segundo o autor; segunda opção |
| **SDXL + LoRA de line art + ControlNet** | Grátis | PC (cabe em 8 GB) | Mais leve, muito controle de pose e composição |
| GPT Image, Gemini (Nano Banana), Ideogram, Midjourney | Pago | Nuvem | Boa qualidade, mas pago. Fica para depois, com aprovação |
| **Recraft** | Pago | Nuvem | O único que entrega **vetor nativo**, ideal para impressão |
| **Desenho por código (SVG)** | Grátis | Qualquer lugar | Mandalas, padrões, labirintos, "cor por número". Skill `algorithmic-art` da Anthropic |

### 6.2 Linha de acabamento (o que separa o amador do profissional)

1. **Gerar** 3 a 4 versões de cada página.
2. **Avaliar com visão** (o próprio Claude olha a imagem): traço contínuo, áreas fechadas, sem cinza, sem mãos e dedos defeituosos, sem texto estranho, sem marca registrada.
3. **Limpar**: converter para preto e branco puro e engrossar o traço de forma uniforme.
4. **Ampliar**: Real-ESRGAN (versão para anime/line art) até **300 dpi**. Página 8,5×11" com sangria = **2625 × 3375 pixels**.
5. **Vetorizar** (opcional, recomendado): **vtracer** (modo preto e branco, rápido, código aberto) ou **potrace**.
6. **Montar o livro**: verso em branco atrás de cada desenho (a tinta não vaza), página "este livro pertence a", página de teste de cores, margens da KDP, capa com lombada calculada pelo número de páginas.
7. **Conferir** contra as regras da KDP antes de enviar.

### 6.3 Skills e repositórios úteis

- [anthropics/skills](https://github.com/anthropics/skills): `pdf` (montar o livro), `canvas-design` (capas e peças em PNG/PDF), `algorithmic-art` (arte por código, ótimo para mandalas).
- Skills que já vêm na StarNet: `line-design`, `brand-assets`, `seo-audit`, `pricing-strategy`, `customer-research`, `competitor-news-monitor`.
- [visioncortex/vtracer](https://github.com/visioncortex/vtracer): vetorização.
- Não encontrei um repositório pronto que faça tudo (gerar → limpar → vetorizar → PDF da KDP). **Vale montar o nosso**, no mesmo estilo do estúdio de dublagem: um motor que roda no PC com a placa de vídeo.

---

## 7. Como a StarNet tocaria a fábrica

Proposta de "estação" com salas (equipes) e uma linha de produção por livro:

```
 [PESQUISA] ──► [DIREÇÃO DE ARTE] ──► [ILUSTRAÇÃO] ──► [CONTROLE DE QUALIDADE] ──► [EDITORA] ──► [PUBLICAÇÃO]
                                         ▲                    │ (reprova)
                                         └────────────────────┘
 [VENDAS E PEDIDOS]   [SUPORTE]   [FINANÇAS E RELATÓRIOS]   (salas que rodam por agendamento)
```

| Sala | O que faz | Ferramentas | Precisa do Phelipe? |
|---|---|---|---|
| **Pesquisa** | Toda semana: tendências e nichos (mais vendidos da Amazon e do Etsy, ranking, avaliações ruins dos concorrentes = oportunidade), em vários países | Navegador, busca na web | Aprova a lista de temas |
| **Direção de arte** | Define o estilo de cada série (traço, nível de detalhe, público) e escreve os pedidos de cada página | Texto | Aprova o estilo da série |
| **Ilustração** | Chama o motor de desenho no PC (placa de vídeo) | Script local, como o estúdio | Não |
| **Controle de qualidade** | Olha cada página e reprova o que tiver defeito; devolve para refazer | Visão | Não (só vê o relatório) |
| **Editora** | Monta o PDF interno e a capa; escreve título, descrição e palavras-chave **em PT, EN, ES, DE, FR, IT, JA** | `pdf`, tradução | Aprova o livro final |
| **Publicação** | Etsy, Payhip, Gumroad e Shopify pela API. **KDP pelo navegador**, preenchendo os campos e parando antes do "Publicar" | API + navegador | **Sim: login e o clique final na KDP** |
| **Vendas e pedidos** | Pedido físico na loja própria vai sozinho para a gráfica (Shopify → Lulu). O agente só acompanha e avisa atrasos | Integração pronta | Não |
| **Suporte** | Lê o e-mail, responde dúvidas comuns (download, reembolso), deixa rascunhos dos casos difíceis | Gmail | Aprova casos difíceis |
| **Finanças** | Relatório semanal: vendas por livro, plataforma e país; custo de IA; o que reimprimir ou abandonar | Planilhas | Lê o relatório |

Regras que eu manteria desde o início:
- **Logins e senhas sempre pelo Phelipe.** A StarNet guarda as chaves no cofre do Windows.
- **Nada é publicado sem aprovação** nas primeiras semanas.
- **Ritmo humano na Amazon:** poucos livros por semana, todos de alta qualidade. Conta banida na KDP é difícil de recuperar.
- **Sem personagens e marcas de terceiros** (Disney, Barbie, Pokémon etc.).

---

## 8. Riscos e cuidados

| Risco | Cuidado |
|---|---|
| Amazon reprovar ou banir a conta por "IA de baixa qualidade" | Marcar o uso de IA, revisar página por página, poucos títulos por semana |
| Desenho feito por IA não tem direito autoral garantido (EUA), então outros podem copiar | Estilo próprio, marca e séries; parte do trabalho com edição humana |
| Licença dos modelos de imagem | Conferir antes se o uso comercial das imagens é permitido |
| Impostos e recebimento do exterior | Amazon e Etsy pedem o formulário fiscal dos EUA (W-8BEN). Ver com o contador como declarar no Brasil |
| Imposto europeu (IVA) em PDF | Gumroad, Etsy, Payhip e Creative Fabrica já cuidam. Na loja própria, precisa configurar |
| Gráfica brasileira com qualidade irregular | Pedir amostras de 2 ou 3 gráficas antes de vender |
| StarNet ainda é versão inicial | Começar pequeno; dinheiro e pedidos ficam em integrações prontas |

---

## 9. Próximos passos sugeridos

1. **Confirmar a StarNet** (é a `androoAGI/starnet`?) e instalar no PC.
2. **Escolher o primeiro nicho e o estilo.** Sugestão: uma série "Bold & Easy" com tema próprio (ex.: Brasil aconchegante, bichos da fauna brasileira, cafés do mundo) — fácil de ilustrar, na moda, e com cara própria.
3. **Teste de desenho no PC:** 20 páginas com FLUX + LoRA e 20 com SDXL, para comparar qualidade e tempo na GTX 1070 Ti.
4. **Livro piloto:** 30 a 50 páginas, publicado em **KDP (EUA)** + **Etsy (PDF)**.
5. **Pedir amostras impressas** à Lulu e à UICLAP.
6. Só depois: Shopify + Lulu, Hotmart + UICLAP, outros idiomas e a automação completa na StarNet.

### Perguntas para o Phelipe
- A StarNet é a do link acima?
- Primeiro público: **adultos** (relaxamento) ou **crianças**?
- Vai vender como pessoa física ou pela empresa (CNPJ)? Isso muda impostos e cadastros.
- Quer que o motor de desenho rode no mesmo PC do estúdio de dublagem? (A placa é uma só; os dois teriam de revezar.)

---

## Fontes

Plataformas e regras
- [KDP: royalties de livro impresso (oficial)](https://kdp.amazon.com/help/topic/G8BKPU9AGVZSF9QF) · [KDP: lojas com livro impresso (oficial)](https://kdp.amazon.com/help/topic/G201834280)
- [Regras de IA na KDP para livros de colorir (Inkfluence)](https://www.inkfluenceai.com/blog/sell-ai-coloring-books-on-kdp-2026) · [Política de IA da KDP (Univers)](https://univers.studio/blog/kdp-ai-content-policy-2026/)
- [Sem API pública na KDP (OpsDesk)](https://theopsdesk.pages.dev/blog/kdp-publishing-automation-manuscript-to-listing.html) · [Etsy API: anúncios (oficial)](https://developer.etsy.com/documentation/tutorials/listings)
- [Como vender printables (Checkout Page)](https://checkoutpage.com/blog/how-to-sell-printables-online) · [Print on demand no Etsy 2026](https://unil.ink/blog/print-on-demand-etsy-2026)
- [IngramSpark: mudanças de 2026 (oficial)](https://help.ingramspark.com/hc/en-us/articles/41657495062029-Changes-in-Print-Cost-Market-Access-Fee-and-More)

Concorrentes e tendências
- [Coco Wyo assina com a Penguin Random House (The Bookseller)](https://thebookseller.com/rights/vietnamese-artists-collective-coco-wyo-signs-with-penguin-random-house-childrens-in-six-figure-deal)
- [Polêmicas do "Bold & Cozy" (Book Riot)](https://bookriot.com/bold-and-cozy-coloring-coco-wyo-controversies/) · [A onda do "cozy coloring" (AOL)](https://www.aol.com/articles/rise-cozy-coloring-finding-calm-090526323.html)
- [Nichos infantis na KDP (Recapio)](https://recapio.com/digest/the-best-kids-coloring-book-niches-on-amazon-kdp-right-now-by-jeffsetlife) · [Mandalas (Book Bolt)](https://bookbolt.io/?p=6143) · [Humor adulto (Book Bolt)](https://bookbolt.io/?p=5350)

Gráficas
- [Lulu Print API (oficial)](https://www.lulu.com/sell/sell-on-your-site/print-api) · [Taxas da Lulu API (oficial)](https://help.api.lulu.com/en/support/solutions/articles/64000254631-are-there-fees-to-use-lulu-s-print-api-)
- [Gelato: livros](https://www.gelato.com/products/childrens-books) · [Peecho: apps e plataformas](https://www.peecho.com/apps-and-platforms) · [BookVault no Shopify](https://apps.shopify.com/bookvault)
- [Livros de colorir sob demanda (Printkk)](https://www.printkk.com/blog/articles/print-on-demand-coloring-books)
- [Hotmart + UICLAP (oficial)](https://help.hotmart.com/pt-br/article/31702447015821/) · [Reclamação UICLAP (Reclame Aqui)](https://www.reclameaqui.com.br/uiclap-editora-e-distribuidora/qualidade-de-impressao-insatisfatoria-e-miolo-do-livro-impresso-em-papel-diferente-do-solicitado_uPzLA0iejoNhqRWJ/)
- [Clube de Autores (Canaltech)](https://canaltech.com.br/inovacao/site-publique-seu-proprio-livro-172138/) · [POD no Brasil (PublishNews)](https://www.publishnews.com.br/materias/2021/07/02/libros-que-viajan)

Desenho
- [Coloring Book Flux (renderartist)](https://huggingface.co/renderartist/coloringbookflux) · [Coloring-Book-Flux-LoRA (prithivMLmods)](https://huggingface.co/prithivMLmods/Coloring-Book-Flux-LoRA)
- [vtracer](https://github.com/visioncortex/vtracer) · [Comparativo de ferramentas de colorir (março/2026)](https://ai-tools-compared.pages.dev/ai-tools-for-generating-coloring-book-pages-compared)
- [Skills da Anthropic: canvas-design](https://mcpservers.org/claude-skills/anthropic/canvas-design)

StarNet
- [StarNet (GitHub)](https://github.com/androoAGI/starnet) · [Análise da StarNet (AI Tools Review)](https://aitoolsreview.co.uk/video/starnet-just-changed-ai-agents-forever?tag=AI)
