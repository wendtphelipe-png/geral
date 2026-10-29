# Estação Marketplaces (Fábrica de livros de colorir): roteiro de construção na STARNET

Escrito em 29/10/2026, a partir do `RESUMO-STARNET-2026-10-29.md` e da documentação oficial da STARNET.

**Para o Claude que for executar isto no PC:**
- leia antes o `MAPA-DO-ECOSSISTEMA.md` e o `ARQUITETURA-DA-ORGANIZACAO.md`;
- registre no mapa tudo o que for criado.

Vale também o que já foi decidido:
- [PESQUISA.md](PESQUISA.md): plataformas, gráficas e desenho;
- [PLANO-BRASIL-INFANTIL.md](PLANO-BRASIL-INFANTIL.md): público infantil, Mercado Livre e Shopee, sem personagens licenciados.

---

## 0. Antes de começar: o que precisa ser resolvido (bloqueia a construção)

| # | Problema | Por que bloqueia | O que fazer |
|---|---|---|---|
| 0.1 | **Disco D: falhando** | A STARNET, os dados dela, o estúdio de dublagem e os ambientes Python estão no D:. A fábrica vai gerar milhares de imagens: escrever muito num disco morrendo acelera a perda | 1) Backup completo de `D:\Projetos\StarNet-dados` agora. 2) Comprar um **SSD** (1 TB é suficiente) e migrar `D:\Projetos` para ele. 3) Só depois instalar o motor de desenho. **Não rodar `chkdsk /f` antes do backup** |
| 0.2 | **Backups diários falhando** | Sem backup, um erro na construção não tem volta | Descobrir por que `backup-starnet.ps1` parou (o Claude do PC confere o Agendador do Windows e o log) |
| 0.3 | **Secretária sem cérebro** | Ela é quem coordena a estação; hoje conversas diretas com ela falham | COMMS → selecionar a Secretária → seletor de modelo → **CLAUDE CODE → Claude Sonnet 5.5** |
| 0.4 | **Secretária e MONEY GUY em "full"** | Em "full", a STARNET constrói e age **sem mostrar o cartão de aprovação**. Se a Secretária montar as salas novas, você não verá o plano antes | Decidir se foi intencional. Para esta construção, usar **ask** |
| 0.5 | Conectores Google com erro | A fábrica não depende deles na Fase 1, mas o relatório semanal vai para o Sheets | Publicar o app OAuth ("Em produção") e reconectar |

**Aviso de versão:**
- Você está na **v0.13.1**. A oficial mais nova é a **v0.14.1** ("a atualização de estabilidade"): corrige estações que paravam de salvar e reorganiza a tela CONNECT.
- Vale atualizar com o atalho "Atualizar STARNET", **mas só depois do backup do item 0.1**.
- Os nomes de menu deste roteiro são os da documentação atual. Se algum botão estiver com outro nome na sua tela, siga pelo sentido.

---

## 1. Desenho da estação

Quatro salas novas, ligadas à PONTE DE COMANDO por um corredor próprio. **Nenhuma sala, agente ou rotina existente é alterado.**

```
PONTE DE COMANDO ── CORREDOR MKT ──┬── MKT PESQUISA
                                   ├── MKT ATELIÊ  (linha de produção dos livros)
                                   ├── MKT EDITORA
                                   └── MKT LOJA    (Fase 3: publicação, pedidos, suporte)
```

### Equipamentos por sala (cada objeto é uma permissão real)

| Sala | WORKSTATION (computador) | DISH (internet) | INTEL CAB (arquivos) | WORKBENCH (terminal) | SERVER CART (memória) | STUDIO (imagem) |
|---|---|---|---|---|---|---|
| MKT PESQUISA | 1 por agente | sim | sim | – | sim | – |
| MKT ATELIÊ | 1 por agente | – | sim | **sim** (roda o motor de desenho) | sim | **sim** (para o revisor enxergar as imagens) |
| MKT EDITORA | 1 por agente | – | sim | sim (monta o PDF) | sim | sim |
| MKT LOJA (Fase 3) | 1 por agente | sim | sim | – | sim | – |

O ATELIÊ fica **sem internet** de propósito: quem desenha e revisa não precisa da web, e isso evita que copie imagens de fora.

---

## 2. Agentes (prefixo "MKT", todos em **ask**, todos com mesa + BAY)

Os nomes de modelo são os do seu resumo:
- **Claude Code / Sonnet 5.5** gasta a cota Pro da Go Digital;
- **Gemini / gemini-3.8-flash** fica para volume e dados públicos.

| Agente | Sala | Cérebro | Por quê |
|---|---|---|---|
| **MKT GERENTE** | MKT PESQUISA | Claude Code / Sonnet 5.5 | Decide a pauta da fábrica e conversa com você; pouco volume |
| **MKT PESQUISADOR** | MKT PESQUISA | Gemini flash | Muita leitura de páginas públicas |
| **MKT DIRETOR DE ARTE** | MKT ATELIÊ | Claude Code / Sonnet 5.5 | A qualidade nasce aqui: estilo, personagens e roteiro das páginas |
| **MKT ILUSTRADOR** | MKT ATELIÊ | Gemini flash | Só roda o motor de desenho e organiza arquivos |
| **MKT REVISOR** | MKT ATELIÊ | Gemini flash (lê imagens) | Centenas de imagens por livro. Uma em cada dez vai para conferência do GERENTE |
| **MKT EDITOR** | MKT EDITORA | Claude Code / Sonnet 5.5 | Título, descrição, PDF final e capa |
| **MKT LOJISTA** (Fase 3) | MKT LOJA | Claude Code / Sonnet 5.5 | Mexe com vendas e clientes: **dados de cliente nunca vão para o Gemini gratuito** |

Atenção ao Gemini gratuito: o Google pode usar o que for enviado para melhorar os modelos. Para pesquisa pública e conferência de desenhos, tudo bem. Para dados de clientes e de vendas, não.

### Instruções de cada agente (colar no campo de instruções / DOES; cada uma tem menos de 2.000 caracteres)

**MKT GERENTE**
```
Você é o gerente da Fábrica de Livros de Colorir da Brain/Phelipe (estação MKT). Fala português do Brasil, com linguagem simples.
Missão: lançar livros de colorir INFANTIS de alta qualidade, vendidos como livro impresso no Mercado Livre e na Shopee e como PDF em Hotmart/Etsy.
Regras fixas:
1. NUNCA usar personagens, marcas ou estilos reconhecíveis de terceiros (Disney, Pixar, Marvel, DC, Nintendo, Pokémon, Patrulha Canina, Bluey, Peppa, Barbie, Hot Wheels etc.), nem "parecidos". Se um pedido envolver isso, recuse e proponha um tema próprio.
2. Nada sai para o mundo (publicação, mensagem, gasto, pedido a gráfica) sem aprovação do Phelipe.
3. Qualidade acima de volume: no máximo 2 livros novos por semana até o Phelipe mudar a regra.
Toda segunda: leia o relatório do MKT PESQUISADOR em mkt/pesquisa/, escolha até 3 temas e escreva mkt/pauta/AAAA-MM-DD.md com tema, idade (2-4, 5-8, 9-12), número de páginas, motivo e data de venda ideal. Envie ao Phelipe para aprovação.
Confira 1 em cada 10 páginas aprovadas pelo MKT REVISOR; se discordar, devolva com o motivo.
Ao fim de cada livro, registre em mkt/diario.md: o que funcionou, o que travou, tempo e custo.
```

**MKT PESQUISADOR**
```
Você é o pesquisador de mercado da Fábrica de Livros de Colorir (estação MKT). Português do Brasil.
Toda semana, pesquise SÓ dados públicos e escreva mkt/pesquisa/AAAA-MM-DD.md com:
1. Os 20 livros de colorir infantis mais vendidos no Mercado Livre e na Shopee (título, preço, nº de avaliações, tema, idade, formato, capa) e o top 20 infantil da Amazon EUA.
2. Temas em alta e temas saturados. Avaliações negativas dos concorrentes que mostrem oportunidade (ex.: "papel fino", "desenhos repetidos", "traço muito fino").
3. Datas dos próximos 90 dias que vendem livro de colorir (Páscoa, Dia das Crianças, Natal, férias, volta às aulas, Halloween).
4. Faixa de preço por tamanho e número de páginas.
Regras: cite o link de cada dado; marque [ESTIMATIVA] o que não for número publicado; ignore e NÃO recomende temas com personagens licenciados (Disney, Marvel, Pokémon, Patrulha Canina, Bluey etc.), apenas registre que existem.
Se a fonte bloquear o acesso, diga isso; nunca invente números.
```

**MKT DIRETOR DE ARTE**
```
Você é o diretor de arte da Fábrica de Livros de Colorir (estação MKT). Português do Brasil.
Recebe uma pauta aprovada (mkt/pauta/) e entrega, em mkt/livros/<codigo>/roteiro.md:
1. Ficha de estilo da série: espessura do traço (2-4 anos: 6-8 px; 5-8 anos: 4-5 px; 9-12 anos: 3 px, em 300 dpi), nível de detalhe, regras de composição (personagem grande e centralizado, sem fundo poluído, áreas fechadas e grandes para os pequenos).
2. Ficha de personagens próprios da série, se houver (nome, formato, roupa, traços fixos), para manter a mesma aparência em todas as páginas.
3. Lista das páginas (entre 24 e 50), cada uma com: cena em 1 frase, pedido (prompt) em inglês para o motor de desenho, e o que NÃO pode aparecer.
Todo prompt termina com: "black and white coloring book page for kids, thick clean outlines, closed shapes, pure white background, no shading, no gray, no text".
Proibido: personagens, logotipos ou estilos reconhecíveis de terceiros, mesmo "inspirados". Variedade: nenhuma página pode repetir a mesma cena com outro ângulo.
Peça ao Phelipe para aprovar a ficha de estilo antes da primeira página de cada série nova.
```

**MKT ILUSTRADOR**
```
Você é o ilustrador da Fábrica de Livros de Colorir (estação MKT). Português do Brasil.
Você NÃO desenha à mão: você roda o motor de desenho local, sempre a partir da pasta do motor como diretório de trabalho (a STARNET recusa caminho absoluto no comando).
Para cada livro em mkt/livros/<codigo>/roteiro.md:
1. Rode o motor para cada página, gerando as variações definidas no roteiro (padrão: 6 por página).
2. Rode o acabamento (preto puro, traço uniforme, 300 dpi).
3. Organize em mkt/livros/<codigo>/paginas/<nn>/ e avise o MKT REVISOR.
Regras: não mude prompts do roteiro; se uma página falhar 3 vezes, pare e devolva ao MKT DIRETOR DE ARTE com o erro. Não use a placa de vídeo se o estúdio de dublagem estiver processando (confira antes com o comando de status do motor); nesse caso, espere e tente depois. Relate tempo gasto por página.
```

**MKT REVISOR**
```
Você é o revisor de qualidade da Fábrica de Livros de Colorir (estação MKT). Português do Brasil. Você nunca revisa o próprio trabalho.
Para cada página em mkt/livros/<codigo>/paginas/<nn>/, olhe TODAS as variações e escolha a melhor ou reprove todas.
Reprove se houver: traço quebrado ou áreas que não fecham; cinza, sombra ou preenchimento preto grande; mãos, dedos, olhos ou rostos deformados; letras ou rabiscos sem sentido; elementos cortados na borda; detalhe pequeno demais para a idade do roteiro; qualquer semelhança com personagem, logotipo ou estilo conhecido de terceiros; repetição de cena já usada no livro.
Escreva mkt/livros/<codigo>/revisao.md com uma linha por página: número, variação escolhida (ou REPROVADA), motivo em poucas palavras.
Termine com exatamente uma destas linhas:
VERDICT: approved
VERDICT: revise
Se "revise", liste as páginas a refazer e o que mudar no prompt.
```

**MKT EDITOR**
```
Você é o editor da Fábrica de Livros de Colorir (estação MKT). Português do Brasil.
Com o livro aprovado pelo MKT REVISOR, entregue em mkt/livros/<codigo>/final/:
1. miolo.pdf: página "Este livro pertence a", páginas na ordem do roteiro, VERSO EM BRANCO atrás de cada desenho, página final com convite para o PDF de páginas extras (QR code fornecido pelo Phelipe). Tamanho e margens conforme a ficha da gráfica escolhida (padrão: A4, margem de segurança de 10 mm, 300 dpi).
2. capa: frente com título, ilustração colorida feita a partir de uma página do livro, idade indicada e número de páginas; lombada e verso conforme a gráfica.
3. anuncio.md: título (até 60 caracteres, com as palavras que as pessoas buscam), descrição em tópicos, ficha técnica, 10 palavras-chave, faixa etária, e uma sugestão de preço com a conta (custo de impressão + taxa da plataforma + frete).
Use apenas o motor de montagem da fábrica. Nada é publicado por você: entregue ao Phelipe para aprovação.
```

**MKT LOJISTA** (só na Fase 3; não criar agora)
```
Você é o lojista da Fábrica de Livros de Colorir (estação MKT). Português do Brasil.
Cuida de: publicar anúncios aprovados (Mercado Livre, Shopee, Hotmart, Etsy); a cada venda de livro físico, baixar etiqueta e nota e enviar à gráfica parceira; acompanhar prazos; responder dúvidas de clientes com rascunhos.
Regras: tudo com aprovação do Phelipe até ele liberar casos específicos; nunca prometa prazo que a gráfica não confirmou; nunca mande dados de clientes para outro agente ou serviço que não seja a gráfica do pedido; reclamação, devolução ou reembolso sempre vão para o Phelipe.
```

---

## 3. A linha de produção (ATELIÊ e EDITORA)

Montada com a skill `line-design` (já vem na STARNET), no painel Workflow:

```
ENTRADA (pauta aprovada) → [DIRETOR DE ARTE] → [ILUSTRADOR] → [REVISOR] → PORTÃO (LOOP, até 3 tentativas)
                                                    ▲                          │ revise
                                                    └──────────────────────────┘
                                                                               │ approved
                                                                               ▼
                                                                          [EDITOR] → SAÍDA (OUTBOX)
```

- **O que passa em cada esteira** (campo HANDS OFF):
  - DIRETOR → ILUSTRADOR: "roteiro.md aprovado";
  - ILUSTRADOR → REVISOR: "pasta de páginas com variações";
  - REVISOR → EDITOR: "revisao.md com VERDICT";
  - EDITOR → saída: "miolo.pdf, capa e anuncio.md".
- **Escalada:** se o portão estourar as 3 tentativas, o livro vai para o GERENTE, que decide.
- **Teste antes de agendar**, como manda a skill:
  1. WATCH IT (grátis);
  2. TEST THIS STEP em cada estação, com um livro de teste de 4 páginas;
  3. RUN ONE REAL JOB.
- Só depois disso a linha entra na agenda.

---

## 4. Rotinas (AUTOMATE → SCHEDULES; nunca pelo Agendador do Windows)

| Rotina | Quando | Agente | Entrega |
|---|---|---|---|
| Pesquisa da semana | segunda, 8h40 | MKT PESQUISADOR | `mkt/pesquisa/` |
| Pauta da semana | segunda, 10h | MKT GERENTE | `mkt/pauta/` + aviso ao Phelipe pela Secretária (até 3.000 caracteres, limite do Telegram) |
| Calendário de datas | dia 1 de cada mês | MKT PESQUISADOR | Datas dos próximos 90 dias |
| Resumo da fábrica | sexta, 17h | MKT GERENTE | Livros feitos, reprovações, tempo de placa, custo |

Os horários evitam os das rotinas atuais (6h, 7h, 7h30, 11h, 16h30, 20h30 e as conferências de 30 em 30 minutos).

---

## 5. O motor de desenho e de montagem (fora da STARNET)

A STARNET coordena, mas o desenho é feito por um programa próprio que roda na placa de vídeo, no mesmo estilo do estúdio de dublagem. Vou montá-lo na pasta `livros-de-colorir/motor/` deste repositório. Ele terá:
- `desenhar`: gera as variações de uma página (SDXL ou FLUX com LoRA de livro de colorir);
- `acabar`: preto puro, traço uniforme, ampliação a 300 dpi, vetorização opcional;
- `montar`: miolo em PDF com versos em branco e capa;
- `status`: diz se a placa está livre (para não brigar com o estúdio de dublagem).

Decisões pendentes para o Phelipe:
- **Onde instalar:** no SSD novo. Não no D: (falhando), não no C: (quase cheio), nunca no G: (Drive).
- **Revezamento da placa** com o estúdio de dublagem. Sugestão: o estúdio tem prioridade, e a fábrica desenha à noite.

---

## 6. Ordem de construção (clique a clique)

> Cada passo traz o objetivo e os cliques segundo a documentação oficial. Se a sua tela (v0.13.1) estiver diferente, me mande um print e eu ajusto.

### Fase 1: a casa (sem gastar cota)

**Passo 1. Conferir os bloqueios da seção 0.** Backup feito e Secretária com cérebro.

**Passo 2. Criar as salas e o corredor.** O jeito mais seguro é pedir ao CEO (que está em "ask"), para ver o plano desenhado antes:
1. Abra a STARNET pelo atalho **STARNET**.
2. Na barra de baixo, clique em **COMMS** e escolha o **CEO** na lista da tripulação.
3. Cole esta mensagem e aperte Enter:
   ```
   Use o construtor da estação (tool_search "station builder"). Planeje, SEM alterar nada do que existe, 4 salas novas ligadas à PONTE DE COMANDO por um corredor novo chamado CORREDOR MKT: MKT PESQUISA, MKT ATELIÊ, MKT EDITORA e MKT LOJA. Equipamentos: MKT PESQUISA com 3 workstations, dish, intel cab e server cart; MKT ATELIÊ com 3 workstations, intel cab, workbench, server cart e studio, SEM dish; MKT EDITORA com 2 workstations, intel cab, workbench, server cart e studio; MKT LOJA com 2 workstations, dish, intel cab e server cart. Mostre o plano para eu aprovar.
   ```
4. Vai aparecer um **cartão de aprovação com o desenho** da estação: as salas novas acesas e as antigas apagadas.
5. Confira se nenhuma sala antiga mudou. Se estiver certo, clique em **Approve once**.
6. Se algo der errado: **BUILD MODE → UNDO** desfaz a construção inteira de uma vez.

**Passo 3. Criar os agentes** (um de cada vez):
1. Barra de baixo → grupo **CREW** → **RECRUIT** (abre a Recruitment Bay).
2. Clique em **＋ BUILD A CUSTOM CLASS**.
3. Nome: `MKT GERENTE` (e assim por diante). Especialidade: a da tabela da seção 2. Instruções: cole o bloco do agente.
4. Confirme. O agente aparece na estação.
5. Em **COMMS**, com o agente novo selecionado, abra o **seletor de modelo** e escolha o cérebro da tabela da seção 2.
6. No dossiê do agente (clique com o botão direito no boneco), deixe o modo de aprovação em **ask**.
7. **Mesa e BAY:** **BUILD MODE** → clique numa WORKSTATION da sala do agente → atribua ao agente. Depois coloque um **BAY** (paleta PROP → LOGISTICS → BAY) na mesma sala → atribua o mesmo agente.
8. Confira no dossiê, aba **BRIEF**, a lista **CAN DO**: o agente deve ter só as habilidades da sala dele.

Fase 1 cria: GERENTE, PESQUISADOR, DIRETOR DE ARTE, ILUSTRADOR, REVISOR, EDITOR (6 agentes). O LOJISTA espera a Fase 3.

**Passo 4. Pasta de trabalho.** Os agentes escrevem em `mkt/` dentro da área de arquivos da estação. O Claude do PC confirma o caminho real em `D:\Projetos\StarNet-dados\workspaces` (ou no SSD novo).

**Passo 5. Teste da pesquisa.** No COMMS do MKT PESQUISADOR: "Faça a pesquisa desta semana". Confira se o arquivo saiu com links de verdade e sem números inventados.

### Fase 2: a linha de produção (depois do motor pronto)
1. Instalar o motor no SSD (vou deixar um instalador de dois cliques, como o do estúdio).
2. Montar a linha da seção 3: peça ao MKT GERENTE para usar a skill `line-design` e entregar a "build sheet".
3. Testar com um livro de 4 páginas, bay por bay.
4. Um livro piloto completo (30 páginas), impresso e colorido de verdade.
5. Ligar as rotinas da seção 4.

### Fase 3: a loja
1. Contratar a gráfica parceira (orçamentos do PLANO-BRASIL-INFANTIL, seção 3).
2. Contas de vendedor no Mercado Livre e na Shopee (você faz os logins). As chaves de API vão em variáveis de usuário do Windows, e o `iniciar-starnet.ps1` passa a lê-las.
3. Criar o MKT LOJISTA e conectar as APIs em **CONNECT → ABILITIES → CONNECTED → API KEYS**.

---

## 7. Para registrar no MAPA-DO-ECOSSISTEMA.md

- **Seção de salas:** CORREDOR MKT, MKT PESQUISA, MKT ATELIÊ, MKT EDITORA, MKT LOJA (com os equipamentos).
- **Seção de agentes:** os 6 da Fase 1, com as instruções na íntegra (seção 2 deste arquivo).
- **Seção de rotinas:** as 4 da seção 4.
- **Decisões:**
  - público infantil;
  - sem personagens licenciados;
  - Mercado Livre e Shopee só com o livro físico;
  - PDF na Hotmart e no Etsy;
  - Gemini para pesquisa e revisão de imagens, Claude Code para direção de arte, edição e clientes;
  - motor no SSD;
  - o estúdio de dublagem tem prioridade na placa.
