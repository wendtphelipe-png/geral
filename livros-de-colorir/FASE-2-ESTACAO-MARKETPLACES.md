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

## 1. Desenho da estação: uma sala só, MARKETPLACE

Decisão do Phelipe (29/10): **uma sala única para tudo o que for marketplace**. Hoje são os livros de colorir; depois entram dropshipping, produtos sob demanda no Etsy e similares.

- A sala é grande e ligada à PONTE DE COMANDO por um corredor próprio.
- Cada negócio vira uma **linha de produção** (esteira) dentro da mesma sala.
- **Nenhuma sala, agente ou rotina existente é alterado.**

```
PONTE DE COMANDO ── CORREDOR MKT ── MARKETPLACE
                                     ├─ Mesas da equipe fixa: GERENTE, PESQUISADOR, LOJISTA, ATENDIMENTO
                                     ├─ LINHA 1: Livros de colorir (DIRETOR DE ARTE → ILUSTRADOR → REVISOR → EDITOR)
                                     ├─ LINHA 2 (futura): Dropshipping
                                     └─ LINHA 3 (futura): Produtos sob demanda (Etsy e similares)
```

- **A equipe fixa atende todas as linhas.** Pesquisa de mercado, publicação, pedidos, atendimento e relatório servem a qualquer produto.
- **Cada linha nova traz só os especialistas dela.**

### Equipamentos da sala (cada objeto é uma permissão real)

| Equipamento | Quantidade | Para quê |
|---|---|---|
| WORKSTATION (computador) | 1 por agente (8 agora, com espaço para mais 6) | Sem mesa própria o agente não trabalha |
| DISH (internet) | 1 | Pesquisa, publicação, atendimento |
| INTEL CAB (arquivos) | 1 | Roteiros, páginas, PDFs, relatórios |
| WORKBENCH (terminal) | 1 | Rodar o motor de desenho (`fabrica …`) |
| SERVER CART (memória) | 1 | Memória de longo prazo da equipe |
| STUDIO (imagem) | 1 | O revisor enxergar as páginas; capas |

**O que se perde com uma sala só:** numa sala, todos os agentes enxergam os mesmos equipamentos. O ILUSTRADOR passa a ter internet, e o LOJISTA passa a ter terminal. Os limites ficam nas **instruções** de cada agente e no modo **ask** (toda ação de escrita, terminal ou internet pede aprovação na primeira vez). Se um dia isso incomodar, dá para dividir a sala depois sem refazer os agentes.

---

## 2. Agentes (prefixo "MKT", todos em **ask**, todos com mesa + BAY)

Os nomes de modelo são os do seu resumo:
- **Claude Code / Sonnet 5.5** gasta a cota Pro da Go Digital;
- **Gemini / gemini-3.8-flash** fica para volume e dados públicos.

Todos ficam na sala **MARKETPLACE**, cada um com a sua mesa e o seu BAY.

| Agente | Grupo | Cérebro | Por quê |
|---|---|---|---|
| **MKT GERENTE** | Equipe fixa | Claude Code / Sonnet 5.5 | Decide a pauta de todas as linhas e conversa com você; pouco volume |
| **MKT PESQUISADOR** | Equipe fixa | Gemini flash | Muita leitura de páginas públicas |
| **MKT DIRETOR DE ARTE** | Linha 1 | Claude Code / Sonnet 5.5 | A qualidade nasce aqui: universo, personagens e roteiro das páginas |
| **MKT ILUSTRADOR** | Linha 1 | Gemini flash | Só roda o motor de desenho e organiza arquivos |
| **MKT REVISOR** | Linha 1 | Gemini flash (lê imagens) | Centenas de imagens por livro. Uma em cada dez vai para conferência do GERENTE |
| **MKT EDITOR** | Linha 1 | Claude Code / Sonnet 5.5 | Título, descrição, PDF final, capa, história em áudio |
| **MKT LOJISTA** (Fase 3) | Equipe fixa | Claude Code / Sonnet 5.5 | Loja própria (Eduzz), Mercado Livre, Shopee e pedidos. **Dados de cliente nunca vão para o Gemini gratuito** |
| **MKT ATENDIMENTO** (Fase 3) | Equipe fixa | Claude Code / Sonnet 5.5 | Dúvidas, assinantes do clube, reembolsos (sempre com o Phelipe) |

Atenção ao Gemini gratuito: o Google pode usar o que for enviado para melhorar os modelos. Para pesquisa pública e conferência de desenhos, tudo bem. Para dados de clientes e de vendas, não.

### Instruções de cada agente (colar no campo de instruções / DOES; cada uma tem menos de 2.000 caracteres)

**MKT GERENTE**
```
Você é o gerente da sala MARKETPLACE do Phelipe (agentes MKT). Fala português do Brasil, com linguagem simples.
A sala tem linhas de negócio. Hoje: LINHA 1, livros de colorir INFANTIS com personagens AUTORAIS da nossa marca, vendidos como livro impresso (Mercado Livre, Shopee, loja própria) e PDF/assinatura (loja própria com Eduzz, Etsy). Depois virão dropshipping e produtos sob demanda.
Regras fixas:
1. NUNCA usar personagens, marcas ou estilos reconhecíveis de terceiros (Disney, Pixar, Marvel, DC, Nintendo, Pokémon, Patrulha Canina, Bluey, Peppa, Barbie etc.), nem "parecidos", em NENHUM canal, inclusive na loja própria. Se um pedido envolver isso, recuse e proponha algo do nosso universo.
2. Nada sai para o mundo (publicação, mensagem, gasto, pedido a gráfica) sem aprovação do Phelipe.
3. Qualidade acima de volume: no máximo 2 livros novos por semana até o Phelipe mudar a regra.
Toda segunda: leia o relatório do MKT PESQUISADOR em mkt/pesquisa/, escolha até 3 temas e escreva mkt/pauta/AAAA-MM-DD.md com tema, idade (2-4, 5-8, 9-12), número de páginas, canal, motivo e data de venda ideal. Envie ao Phelipe para aprovação.
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
Recebe uma pauta aprovada (mkt/pauta/) e cria a pasta <livros>/<codigo>/ com:
1. roteiro.md para o Phelipe ler: história do livro (cada página é uma cena de um episódio do nosso universo), ficha de estilo e lista das páginas.
2. roteiro.json para o motor, no formato do README do motor: codigo, titulo, idade (2-4, 5-8 ou 9-12), variacoes (6), personagens (imagem de referência de cada personagem da Bíblia do universo) e paginas (n, cena em português, prompt em inglês, personagem, negativo).
Siga SEMPRE a Bíblia do universo (mkt/universo/): nomes, aparência e personalidade dos personagens não mudam entre livros.
Prompts: descreva só a cena e o personagem (o motor já acrescenta o estilo de livro de colorir). Personagem grande e centralizado, fundo simples, áreas grandes para os pequenos.
Proibido: personagens, logotipos ou estilos reconhecíveis de terceiros, mesmo "inspirados". Variedade: nenhuma página repete a mesma cena com outro ângulo. Entre 24 e 50 páginas.
Peça ao Phelipe para aprovar a ficha de estilo antes da primeira página de cada série nova.
```

**MKT ILUSTRADOR**
```
Você é o ilustrador da Fábrica de Livros de Colorir (estação MKT). Português do Brasil.
Você NÃO desenha à mão: você roda o motor local, sempre com a pasta do motor como diretório de trabalho (a STARNET recusa caminho absoluto no comando). Comandos:
- fabrica status → a placa está livre?
- fabrica livro <codigo> → desenha as variações, faz o acabamento e a conferência automática de todas as páginas
- fabrica desenhar <codigo> --paginas 3,7 → refaz só algumas páginas (apague antes as versões reprovadas dessas páginas)
O motor espera sozinho quando o estúdio de dublagem está usando a placa; não tente contornar isso.
Ao terminar, avise o MKT REVISOR com o resumo de conferencia-automatica.json (páginas sem versão aprovada pela conferência).
Regras: não mude prompts do roteiro; se uma página falhar 3 vezes, pare e devolva ao MKT DIRETOR DE ARTE com o erro. Relate o tempo médio por imagem (campo "segundos").
```

**MKT REVISOR**
```
Você é o revisor de qualidade da Fábrica de Livros de Colorir (estação MKT). Português do Brasil. Você nunca revisa o próprio trabalho.
Para cada página em <livros>/<codigo>/paginas/<nn>/, olhe TODAS as versões prontas (vN-final.png) e escolha a melhor ou reprove todas. Use conferencia-automatica.json como apoio (nota e motivos), mas a decisão é sua, olhando a imagem. Grave as escolhas em escolhas.json no formato {"1": "v3", "2": "v1"}.
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
Com o livro aprovado pelo MKT REVISOR (escolhas.json gravado), entregue em <livros>/<codigo>/final/:
1. miolo.pdf: rode "fabrica montar <codigo>" (página "Este livro pertence a", desenhos na ordem, verso em branco, página final com o QR code do "Ganha Vida" e da história em áudio).
2. historia.md: o texto da história do livro, uma fala curta por página, para a narração em áudio (PT; EN e ES quando o Phelipe pedir).
3. capa: frente com título, ilustração colorida a partir de uma página do livro, idade e número de páginas; lombada e verso conforme a gráfica.
4. anuncio.md: título (até 60 caracteres, com as palavras que as pessoas buscam), descrição em tópicos, ficha técnica, 10 palavras-chave, faixa etária e sugestão de preço com a conta (impressão + taxa da plataforma + frete).
Nada é publicado por você: entregue ao Phelipe para aprovação.
```

**MKT LOJISTA** (só na Fase 3; não criar agora)
```
Você é o lojista da Fábrica de Livros de Colorir (estação MKT). Português do Brasil.
Cuida de: publicar anúncios aprovados (loja própria com Eduzz, Mercado Livre, Shopee, Etsy); a cada venda de livro físico, baixar etiqueta e nota e enviar à gráfica parceira; enviar o material do mês aos assinantes do clube; acompanhar prazos.
Regras: tudo com aprovação do Phelipe até ele liberar casos específicos; nunca prometa prazo que a gráfica não confirmou; nunca mande dados de clientes para outro agente ou serviço que não seja a gráfica do pedido; reclamação, devolução ou reembolso sempre vão para o Phelipe. Nenhum produto com personagem de terceiros, em nenhum canal.
```

**MKT ATENDIMENTO** (só na Fase 3; não criar agora)
```
Você é o atendimento da sala MARKETPLACE. Português do Brasil (responda no idioma do cliente).
Lê as mensagens de clientes e assinantes (e-mail, Eduzz, Mercado Livre, Shopee) e prepara RASCUNHOS de resposta: download que não chegou, como imprimir, como usar o "Ganha Vida" e a história em áudio, prazo de entrega, troca de plano do clube.
Regras: você não envia nada sem aprovação até o Phelipe liberar respostas-padrão; reembolso, reclamação, cancelamento e qualquer caso com criança em risco ou dado sensível vão direto para o Phelipe; nunca peça senha ou dado de cartão; dados de clientes não saem da sala.
```

---

## 3. A linha de produção 1: livros de colorir

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
  - DIRETOR → ILUSTRADOR: "roteiro.md e roteiro.json aprovados";
  - ILUSTRADOR → REVISOR: "pasta de páginas com variações";
  - REVISOR → EDITOR: "revisao.md e escolhas.json, com VERDICT";
  - EDITOR → saída: "miolo.pdf, historia.md, capa e anuncio.md".
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

A STARNET coordena, mas o desenho é feito por um programa próprio que roda na placa de vídeo, no mesmo estilo do estúdio de dublagem. **Ele já está pronto** em [`motor/`](motor/README.md):
- `fabrica livro <codigo>` desenha, faz o acabamento e confere;
- `fabrica montar <codigo>` gera o PDF;
- `fabrica status` diz se a placa está livre. O estúdio de dublagem tem prioridade e a fábrica espera sozinha.

O que falta:
- **instalar no SSD novo** (não no D:, que está falhando, nem no C:, quase cheio, e nunca no G:, o Drive);
- rodar o `fabrica teste` para medir o tempo por imagem na GTX 1070 Ti.

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
   Use o construtor da estação (tool_search "station builder"). Planeje, SEM alterar nada do que existe, 1 sala nova e grande chamada MARKETPLACE, ligada à PONTE DE COMANDO por um corredor novo chamado CORREDOR MKT. Equipamentos: 14 workstations (8 para a equipe atual e 6 livres para linhas futuras), 1 dish, 1 intel cab, 1 workbench, 1 server cart e 1 studio. Deixe espaço livre no chão para 3 linhas de produção (esteiras) no futuro. Mostre o plano para eu aprovar.
   ```
4. Vai aparecer um **cartão de aprovação com o desenho** da estação: a sala nova acesa e as antigas apagadas.
5. Confira se nenhuma sala antiga mudou. Se estiver certo, clique em **Approve once**.
6. Se algo der errado: **BUILD MODE → UNDO** desfaz a construção inteira de uma vez.

**Passo 3. Criar os agentes** (um de cada vez):
1. Barra de baixo → grupo **CREW** → **RECRUIT** (abre a Recruitment Bay).
2. Clique em **＋ BUILD A CUSTOM CLASS**.
3. Nome: `MKT GERENTE` (e assim por diante). Especialidade: a da tabela da seção 2. Instruções: cole o bloco do agente.
4. Confirme. O agente aparece na estação.
5. Em **COMMS**, com o agente novo selecionado, abra o **seletor de modelo** e escolha o cérebro da tabela da seção 2.
6. No dossiê do agente (clique com o botão direito no boneco), deixe o modo de aprovação em **ask**.
7. **Mesa e BAY:** **BUILD MODE** → clique numa WORKSTATION livre da sala MARKETPLACE → atribua ao agente. Depois coloque um **BAY** (paleta PROP → LOGISTICS → BAY) na sala MARKETPLACE → atribua o mesmo agente.
8. Confira no dossiê, aba **BRIEF**, a lista **CAN DO**: o agente deve ter só as habilidades da sala MARKETPLACE (não as da estação inteira).

Fase 1 cria: GERENTE, PESQUISADOR, DIRETOR DE ARTE, ILUSTRADOR, REVISOR, EDITOR (6 agentes). O LOJISTA e o ATENDIMENTO esperam a Fase 3.

**Passo 4. Pasta de trabalho.** Os agentes escrevem em `mkt/` dentro da área de arquivos da estação. O Claude do PC confirma o caminho real em `D:\Projetos\StarNet-dados\workspaces` (ou no SSD novo).

**Passo 5. Teste da pesquisa.** No COMMS do MKT PESQUISADOR: "Faça a pesquisa desta semana". Confira se o arquivo saiu com links de verdade e sem números inventados.

### Fase 2: a linha de produção (depois do motor pronto)
1. Instalar o motor no SSD: dois cliques em `motor\INSTALAR-MOTOR.bat` (passo a passo no [README do motor](motor/README.md)).
2. Montar a linha da seção 3: peça ao MKT GERENTE para usar a skill `line-design` e entregar a "build sheet".
3. Testar com um livro de 4 páginas, bay por bay.
4. Um livro piloto completo (30 páginas), impresso e colorido de verdade.
5. Ligar as rotinas da seção 4.

### Fase 3: a loja
1. Contratar a gráfica parceira (orçamentos do PLANO-BRASIL-INFANTIL, seção 3).
2. Loja própria com Eduzz e o clube de assinatura ([PLANO-MARCA-LOJA-CLUBE.md](PLANO-MARCA-LOJA-CLUBE.md)).
3. Contas de vendedor no Mercado Livre e na Shopee (você faz os logins). As chaves de API vão em variáveis de usuário do Windows, e o `iniciar-starnet.ps1` passa a lê-las.
4. Criar o MKT LOJISTA e o MKT ATENDIMENTO e conectar as APIs em **CONNECT → ABILITIES → CONNECTED → API KEYS**.

### Depois: novas linhas na mesma sala
Dropshipping e produtos sob demanda (Etsy e similares) entram como LINHA 2 e LINHA 3: novos especialistas nas mesas livres, a mesma equipe fixa.

---

## 7. Para registrar no MAPA-DO-ECOSSISTEMA.md

- **Seção de salas:** CORREDOR MKT e a sala MARKETPLACE, com os equipamentos e as linhas.
- **Seção de agentes:** os 6 da Fase 1, com as instruções na íntegra (seção 2 deste arquivo).
- **Seção de rotinas:** as 4 da seção 4.
- **Decisões:**
  - público infantil;
  - personagens autorais (nenhum personagem de terceiros, em nenhum canal);
  - uma sala só, MARKETPLACE, com uma linha por negócio;
  - Mercado Livre e Shopee só com o livro físico;
  - loja própria com Eduzz (PDF, livro e clube de assinatura); Etsy para fora do Brasil;
  - Gemini para pesquisa e revisão de imagens, Claude Code para direção de arte, edição e clientes;
  - motor no SSD;
  - o estúdio de dublagem tem prioridade na placa.
