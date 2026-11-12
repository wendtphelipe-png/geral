# Dossiê do Audio Remix: passagem para o Claude no PC do Phelipe

Escrito em 12/11/2026 pelo Claude da nuvem (claude.ai/code), que tocou o projeto de 22/10 a 11/11/2026. A partir de agora, quem assume é o Claude Code no app do PC. Leia este dossiê inteiro antes de mexer em qualquer coisa. Depois leia, nesta ordem: `README.md` (como usar), `PLANO.md` (visão e etapas), `DESCOBERTAS.md` (a fórmula da IDL) e `PESQUISA-ESTILOS.md`.

---

## 1. Quem é o Phelipe e como falar com ele

- **Não é programador.** Responda sempre em **português, com linguagem simples**: o que mudou, o que ele precisa fazer e o que você testou.
- **Sem emojis**, em nada: respostas, tela ou commits.
- A filha dele é **dançarina de danças urbanas** em competições. O app é, primeiro, para ela e alguns colegas. Licenças de música ficam para depois, por decisão dele.
- Ele é **exigente com a qualidade e com a interface.** Já reprovou uma versão inteira do editor ("ficou bem confuso", "não ficou bom") e um mix automático ("o resultado foi horrível"). **Nunca entregue sem testar de ponta a ponta.**
- Ele testa no PC e manda fotos da tela. Peça a foto ou o segundo exato do problema quando algo falhar.
- **Motores gratuitos primeiro.** Os pagos só entram com a aprovação dele. O Lyria (Google) já foi aprovado e conectado.
- Ele tem as assinaturas do Claude e do Google AI Pro. Deixe claro que assinatura de app não inclui uso por API.

## 2. O objetivo do produto (na voz dele)

> "Meu objetivo principal é que o próprio programa entenda os padrões de mixagem para competição e consiga criar os mixes sozinho. E que as alterações possam ser feitas por prompt em setores específicos que eu selecione manualmente."

Os três modos pedidos desde o início:
1. **Colagem com transições** entre várias músicas (Etapa 2, ainda não feita).
2. **Injetar estilos numa música só** sem perder a assinatura dela. É o modo preferido; está em andamento com estruturas, blocos de estilo e Lyria.
3. **Música do zero** por texto. Feito via Lyria ("Criar com IA"), ainda não testado com a chave real.

Pedidos de detalhe que ele já fez e que viraram requisito:
- editar por **contagens de 8** ("oitos");
- "nesta contagem de 8, quero mais batidas graves";
- "tira a voz deste trecho";
- "coloque nesse trecho a voz do oito 5 como um eco distante 30% mais baixa": já funciona;
- **não renderizar a trilha inteira a cada mudança**: há cache por bloco;
- a interface deve parecer a de um **editor de áudio comum**: horizontal, faixas empilhadas, M/S;
- **lista de estruturas de mix** e um **montador de arrastar**;
- **analisar um mix** a partir de link ou arquivo: descobrir as músicas, comparar com as originais, extrair o padrão e salvar na biblioteca;
- ignorar o grito da plateia nos vídeos de competição.

## 3. Onde as coisas ficam

**No PC (Windows):**
- Repositório: `D:\Projetos\geral`. O projeto fica na pasta `audio-remix\`. Abra o Claude Code nessa pasta.
- Ambiente Python: `D:\Projetos\remix-py` (Python **3.12**). O 3.14 quebra o PyTorch e o shazamio; não recrie com ele.
- Placa de vídeo: **GTX 1070 Ti**, 8 GB, arquitetura Pascal. O PyTorch é o 2.14+cu126. As compilações cu128 e mais novas não aceitam Pascal.
- FFmpeg e Deno instalados pelo winget. O Deno é exigido pelo yt-dlp para o YouTube.
- Dados locais, fora do Git: `audio-remix\dados\`
  - `projetos\<id>\`: `fonte.wav`, `faixas\` (voz, bateria, baixo e outros em wav), `analise.json`, `projeto.json` (linha do tempo, camadas, mixer), `importados\`;
  - `estruturas\`: as estruturas salvas pelo usuário;
  - `padroes\<id>\`: as análises de mix;
  - `ia-cache\`: os áudios gerados pelo Lyria, para não pagar duas vezes;
  - `modelos\`: o modelo Demucs, uns 84 MB, baixado uma vez;
  - `exportados\`: os MP3 finais;
  - `chave-google.txt`: a chave do Lyria. **Nunca leia, mostre nem envie ao Git.**
- O checkpoint do Beat This! fica no cache do torch, com uns 77 MB, baixado de cloud.cp.jku.at na primeira vez.

**GitHub:** `github.com/wendtphelipe-png/geral`, um repositório **público**. O único branch, que também é o padrão, é `claude/sweet-brahmagupta-le71g8`. Continue nele, a menos que o Phelipe peça outro. Nunca envie áudio, chave ou nada de `dados\`.

Existe outro projeto do Phelipe, o `brainaudiovisual` (site, Cabine e Estúdio de dublagem), com o próprio CLAUDE.md. **Não misture.** O Audio Remix só copiou do Estúdio a paleta e a fonte.

## 4. Como rodar

| Arquivo (na pasta `audio-remix`) | O que faz |
|---|---|
| `PREPARAR-ANALISADOR.bat` | Cria e repara o ambiente: Python 3.12, PyTorch cu126, audio-separator[cpu]+audioread, shazamio, FFmpeg, Deno. Termina com `analisador\conferir.py` (lista OK e FALTA). |
| `ABRIR-EDITOR.bat` | Instala google-genai e beat_this se faltarem e abre o editor em http://127.0.0.1:3060 (`editor\servidor.py`). |
| `ANALISAR-PLAYLIST.bat` | Etapa 0: baixa uma playlist ou vídeo, faz o raio-x de cada mix e envia **só os relatórios** para `analises\`. |

Comandos úteis, com `PY=D:\Projetos\remix-py\Scripts\python.exe`:
- Editor sem abrir o navegador, em outra porta: `%PY% editor\servidor.py --porta 3062 --sem-navegador`
- Testes do entendedor de pedidos: `node editor\testes\comandos.test.js`. Hoje são **41/41**; mantenha todos passando.
- Conferir a instalação: `%PY% analisador\conferir.py`

## 5. Arquitetura (código em `audio-remix\`)

```
analisador/        Etapa 0: raio-x de mixes de competição
  baixar.py        yt-dlp (lista a playlist e baixa cada vídeo; tenta sem login e depois com cookies do Chrome, Edge e Firefox)
  analisar.py      separar() (audio-separator/htdemucs), BPM, trechos, transições, paradas, Shazam
  resumo.py        padrões do conjunto -> analises/RESUMO.md
  conferir.py      confere a instalação
biblioteca/
  estilos.json     11 estilos: BPM, groove, padrão de bateria de 16 passos, instrumentos, efeitos, 266 referências
  estruturas.json  17 MODOS do mix automático e 7 ESTRUTURAS prontas
editor/
  servidor.py      HTTP da biblioteca padrão (ThreadingHTTPServer), rotas /api/... e validação de tudo o que chega
  motor.py         projeto: preparar (baixar/converter -> separar -> batidas/oitos -> partes A/B/C), Projeto (render com cache)
  arranjador.py    MIX AUTOMÁTICO: executa uma estrutura passo a passo (classe Montador)
  efeitos.py       eco (ping-pong, no tempo), reverb (resposta sintética), filtros abafado/rádio/grave, paradas
  bateria.py       bateria sintetizada que toca os padrões de estilos.json no BPM da música
  ia.py            Lyria pela biblioteca google-genai: gerar(), encaixar() no tempo, prompt_estilo()
  padrao.py        "Analisar um mix": raio-x + comparação com as originais + estrutura aprendida
  public/index.html  a tela inteira (CSS e JS num arquivo só)
  public/comandos.js entendedor de pedidos em português, por regras (gratuito); também roda no Node para testes
  testes/comandos.test.js
```

**Modelo de dados do projeto (`projeto.json`):**
- `timeline`: a trilha principal, uma lista de blocos em sequência. Cada bloco:
  `{u: id da unidade ("o12", "intro", "final"), faixas: {voz, bateria, baixo, outros: 0..2}, vel: 1|0.5|2, de/ate: 0..1 (recorte), env: [[x, ganho]...] (curva de fade), fx: {"tudo"|faixa: {eco, reverb, tamanho, filtro, distante, batidas_eco}}, paradas: [[batida, duração em batidas]], papel: texto}`
- `camadas`: faixas extras com clipes livres no tempo: `{id, nome, ganho, mudo, solo, auto?, clipes: [{id, fonte, pos, ini, dur, ganho, fi, fo, fx}]}`. A `fonte` pode ser `importado` (arquivo do projeto), `faixa` (trecho de uma faixa separada de um oito) ou `estilo` (bateria sintetizada).
- `mixer`: M/S/volume das 4 faixas; `alvo`: a duração desejada (padrão 165 s).
- A tela manda a linha do tempo **efetiva** (já com mixer, mudo e solo) para `/audio` e `/exportar`.

**Render (`motor.Projeto`):**
- cada bloco vira (seco, núcleo, molhado);
- emenda de 12 ms entre blocos; o "molhado" (cauda de eco e reverb) continua depois do bloco;
- os clipes das camadas são somados por cima;
- proteção de pico;
- cache por md5 do bloco: só o que mudou é recalculado.

**Contagem (`motor.analisar_projeto`):**
- as batidas e os começos de compasso vêm do **Beat This!**; se ele faltar, usa o `librosa.beat_track`;
- `achar_o_um()` escolhe a fase de 4 por votação dos começos de compasso, e a paridade de 8 pela mudança de harmonia/timbre mais o bumbo;
- `deslocamento` (0 a 7) é o "1"; o usuário corrige com as setas.

**Mix automático (`arranjador.criar_mix`):**
- os passos `auto` repartem a duração restante (por `peso`);
- `pegar_em_ordem()` pega **frases inteiras** de 2 ou 4 oitos a partir do começo de cada parte e pula **partes fracas** (força menor que 0,6 da mediana);
- a "queda" usa a seção mais forte do refrão e o mix **continua dali**;
- os blocos de estilo tiram a bateria para 0,25, mantêm o baixo e põem a camada de estilo; o servidor iguala o volume da camada ao da bateria original;
- as paradas extras seguem a densidade da estrutura (poucas 0,5, normal 1,2 ou densas 4 por minuto).

## 6. O que está pronto, e o que foi testado de verdade

**Atenção ao nível de confiança:**
- **testado na nuvem** quer dizer que rodou no ambiente da nuvem (CPU) com uma música de teste sintética ou com faixas de licença livre do Frenic (hip-hop/funk), e que a tela foi conferida com o Playwright;
- **testado no PC pelo Phelipe** está indicado em cada caso.

| Função | Estado |
|---|---|
| Etapa 0 (análise da playlist da Brotherhood) | Rodou no PC; 14 vídeos analisados (10 apresentações). Resultados em `analises\` e `DESCOBERTAS.md`. |
| Importar música (link ou arquivo), separar e achar os oitos | Rodou no PC (ele confirmou a separação). **A contagem estava 1 tempo errada** na música dele. Corrigida com o Beat This!, **ainda não confirmada no PC**. |
| Editor (régua, faixas, M/S, cortar, fades, camadas, importar mp3, arrastar, desfazer, exportar) | Testado na nuvem. No PC, ele usou e criticou a versão anterior; a versão horizontal ainda não teve retorno detalhado. |
| Pedidos por texto (comandos.js) | 41 testes passando. No PC, um pedido "ia:" falhou pelo erro do Lyria (corrigido). |
| Eco, reverb, filtros, paradas, "voz do oito N aqui" | Testado na nuvem. |
| Mix automático + 7 estruturas + montador | Testado na nuvem. **No PC, ele achou o resultado horrível** (antes das correções de 11/11: contagem errada, cortes no meio das frases, volta para a introdução calma, silêncios demais). As correções foram medidas na nuvem com uma faixa real, mas **não foram ouvidas**. |
| Analisar um mix (padrao.py) | Testado na nuvem só por upload, sem Shazam e sem YouTube. **O fluxo completo por link nunca rodou.** |
| Lyria (blocos de estilo, "ia: ...", música do zero) | Erro "client has been closed" corrigido e reproduzido. **Nunca gerou um áudio real.** O teste na nuvem usou um Lyria falso. |
| Bateria sintetizada dos estilos | Funciona. Ele ainda não disse se soa aceitável. |

## 7. Problemas conhecidos e riscos

1. **Qualidade musical do mix automático:** é o ponto mais sensível. Ouça a opinião do Phelipe e meça (veja a seção 8).
2. **Meio tempo e tempo dobrado** usam o phase vocoder do librosa e soam borrados. Uma melhoria possível é o Rubber Band (pyrubberband mais o executável no Windows), ou fazer o meio tempo trocando só a bateria em vez de esticar tudo.
3. **O "1" da contagem** pode errar a paridade de 8 (qual dos dois compassos começa o oito). Há o botão Contagem e as setas, mas o ideal é acertar sozinho.
4. **As partes A/B/C** vêm de um agrupamento por harmonia e timbre (linkage cosseno, limite 0,5). Funcionou na música de teste e na faixa do Frenic; pode falhar em músicas muito repetitivas.
5. **Analisar um mix:** a classificação de trechos (sem grave, sem bateria, só voz) usa limites simples; o estilo de uma "outra música" é só um palpite pelo BPM.
6. **O Lyria:** os nomes dos modelos mudam, e `ia.modelos()` pergunta ao Google. O `encaixar()` acerta o tempo por detecção de batidas; confira com música real. O Lyria Clip gera 30 s, e trechos maiores são repetidos em compassos inteiros.
7. A separação simples (sem Demucs) existe só como reserva; ela não separa a voz.
8. A tela foi feita para o computador; no celular ela abre, mas é apertada.

## 8. Como testar antes de mostrar ao Phelipe (o protocolo)

No PC você tem a placa de vídeo, o YouTube e a chave do Lyria: use tudo isso.

1. **Músicas de teste reais:** baixe com o `analisador\baixar.py`. Algumas das que a Brotherhood usou:
   - "Toxic" (Britney Spears)
   - "I Want You Back" (*NSYNC)
   - "Get Back" (Ludacris)
   - "Jealous Type" (Doja Cat)
   - "MOVE" (Lecrae & 1K Phew)

   Importe pelo editor ou chame `motor.preparar()` direto.
2. **Contagem:** compare os começos de oito com os `compassos` do Beat This! e com a entrada da voz (um script assim foi usado na nuvem: veja onde a voz entra e em que tempo do oito cai). Gere um áudio com `clique=True` (`Projeto.montar(..., clique=True)`) para o Phelipe conferir.
3. **Mix automático, medidas objetivas** (o script usado na nuvem fazia exatamente isto):
   - buracos de silêncio: janelas de 100 ms abaixo de −30 dB da mediana por mais de 0,3 s (só a cauda final é aceitável);
   - volume por bloco (mediana e menor valor) e a maior queda entre blocos vizinhos (hoje fica em torno de −4,6 dB);
   - ordem das unidades usadas: deve haver trechos contínuos (21, 22, 23...) e os saltos devem cair em começos de parte;
   - número de paradas por minuto, perto da densidade da estrutura.
4. **Lyria:** gere um bloco de estilo real, meça o BPM do resultado e confira se `encaixar()` entrega o número exato de batidas, começando numa batida forte.
5. **Analisar um mix:** rode por link com um vídeo da Brotherhood e confira se as músicas identificadas batem com `DESCOBERTAS.md`.
6. **Tela:** use o Playwright (no Node ou no Python) para clicar nos fluxos e tirar fotos em 1920, 1440, 1366 e 1100 de largura; nenhuma barra pode vazar para os lados (`scrollWidth == innerWidth`). Antes de mexer na tela, leia o CSS existente.
7. **Testes do entendedor:** `node editor\testes\comandos.test.js` (41/41). Todo pedido novo ganha um teste.
8. Só então entregue, dizendo **o que foi testado e o que não foi**.

## 9. Próximos passos sugeridos (por prioridade)

1. Pegar o retorno do Phelipe sobre a versão de 11/11, depois de ele importar a música de novo para recalcular a contagem; consertar o que ele apontar, com medição.
2. Confirmar o **Lyria** de ponta a ponta com a chave dele: blocos de estilo, "ia:" e "Criar com IA".
3. Rodar **"Analisar um mix"** por link com 2 ou 3 vídeos da IDL e salvar os padrões na biblioteca.
4. Melhorar o **meio tempo** (Rubber Band ou meio tempo só da bateria).
5. **Etapa 2: colagem de várias músicas** (acertar BPM e tom entre elas, transições prontas: filtro, eco jogado, riser, tape stop, corte na batida).
6. Deixar a IA de texto mais esperta: hoje o entendedor funciona por regras. A ideia combinada é o Claude (pela API, com aprovação do Phelipe) transformar pedidos livres em ações do editor, e o Gemini "ouvir" um áudio de referência. Veja a seção "A IA que supervisiona e cria" do `PLANO.md`.

## 10. Regras de trabalho

- **Segurança:** nunca ler, mostrar ou enviar `audio-remix\dados\chave-google.txt`, nem nada de `dados\`. Nunca digitar senhas ou chaves pelo Phelipe; ele mesmo cola no editor (botão da varinha).
- Pergunte antes de qualquer ação destrutiva: apagar projetos, `reset --hard`, apagar dados.
- Commits em português, explicando o que mudou e por quê. Continue no branch `claude/sweet-brahmagupta-le71g8`.
- `.bat`: use finais de linha CRLF e não use acentos dentro dos `echo`, porque o console do Windows pode estragar.
- Mantenha o padrão do código: português nos nomes e comentários, comentários só onde explicam o porquê, nada de dependência nova sem necessidade (o servidor usa só a biblioteca padrão de propósito).
- Design: paleta azul-noite (`--noite #080C13`); cores das faixas: voz `#5CC8FF`, bateria `#FF7A59`, baixo `#A08BFF`, outros `#3DD6B5`; amarelo `#FFC93C` só para o mix automático. Fonte Archivo. Ícones SVG no estilo Lucide. Sem emojis.
- Ao terminar um trabalho: atualize `README.md` (como usar) e o diário em `PLANO.md`, e faça commit e push.
