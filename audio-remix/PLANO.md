# Audio Remix: plano do aplicativo

Criado em 22/10/2026. Documento vivo: vai mudar conforme as respostas do Phelipe e os testes.

## O objetivo
Um app em que qualquer pessoa (coreógrafo, dançarina, família) cria um mix profissional para coreografia de danças urbanas, sem precisar estudar produção musical por anos.

## Os três modos do app

### Modo 1: Colagem com transições (o mix clássico de competição)
Junta trechos de várias músicas (um de house, um de locking, um de breaking...).
- O app ajusta o BPM e o tom de cada trecho para que eles "conversem".
- Cria a transição. Opções:
  - fade com filtro (o grave some de uma e entra na outra);
  - eco ou reverb que "carrega" o fim de uma música;
  - "riser" (som que sobe e cria expectativa) seguido de impacto;
  - "tape stop" (a música desacelera e para);
  - "rewind" (a fita volta);
  - scratch;
  - silêncio dramático;
  - voz de uma música por cima da batida da outra (mashup);
  - efeitos sonoros e falas de filme.
- Nada de corte seco nem salto de volume: o app iguala o volume percebido (loudness) entre os trechos.

### Modo 2: Injeção de estilo numa música (o mais desejado)
Uma música só, transformada em vários estilos sem perder a identidade.
1. O app separa a música em **faixas**: voz, bateria, baixo, outros instrumentos (e, quando der, piano e guitarra).
2. A **assinatura** fica: a voz, o refrão ou a melodia principal continuam presentes o tempo todo, mesmo que em segundo plano.
3. Em cada trecho escolhido, o app troca o **groove**:
   - a bateria original sai e entra uma bateria do estilo (quatro no chão para house, break para breaking, tamborzão para passinho);
   - o BPM muda sem mudar o tom da voz;
   - o baixo é reforçado ou trocado.
4. As passagens entre um estilo e outro usam as mesmas transições do Modo 1.

### Modo 3: Música do zero
- A partir de um texto ("começa com house a 124, depois vira krump em meio tempo, termina com breaking, use metais e um coro gospel"), e opcionalmente de links de referência.
- Sem direito autoral de terceiros.
- Usa modelos de IA que geram música, por trechos, e depois o mesmo editor dos outros modos para ajustar.

## Duração da trilha
- O usuário define o **tempo total** (por exemplo 2:30, ou "20 oitos a 120 BPM"). O app mostra quantos oitos cabem, conforme o BPM.
- A sugestão inicial (duração total, tamanho de cada trecho, quantidade de transições) vem do `RESUMO.md` da análise da playlist da Brotherhood.
- Se a trilha passar ou faltar tempo, o app sugere onde cortar ou repetir oitos, sempre em blocos de 8 para não quebrar a contagem.

## O editor: mexer em pedaços pequenos sem renderizar tudo

É o coração do app. Funciona como um **projeto não destrutivo**:
- O áudio original e as faixas separadas nunca são alterados.
- O projeto guarda só uma **lista de instruções**, por exemplo: "no oito 12, bateria +30% de grave"; "no oito 14, voz desligada"; "no oito 20, copiar a voz do oito 5, com eco distante e volume -30%".
- O app desenha a música em **oitos numerados** (contagens de 8), com uma linha por faixa (voz, bateria, baixo, outros).
- Quando algo muda, o app recalcula **só os oitos afetados** (mais um pedacinho antes e depois para emendar sem clique) e guarda o resto em memória. Ouvir uma mudança leva segundos, não minutos.
- **Pedido por texto ou por clique:** o Phelipe pode clicar (botões de estilo, controles de volume e efeito) ou escrever o pedido. O texto vira instruções que aparecem na tela antes de serem aplicadas, para conferir.
- Desfazer e refazer ilimitado; versões salvas ("mix v1", "mix v2 mais grave").

Exemplos de pedidos que o editor precisa entender:
| Pedido | O que o app faz |
|---|---|
| "Neste oito, mais batidas graves" | Reforça o bumbo e o baixo, ou acrescenta bumbos no padrão do estilo |
| "Tira a voz deste trecho" | Desliga a faixa de voz só nesses oitos |
| "Coloca a voz do trecho X aqui, como eco distante, 30% mais baixa" | Copia a voz do trecho X, aplica eco e reverb longos, filtro e -30% de volume |
| "Faz este trecho em meio tempo" | Estica o trecho (duas vezes mais lento), sem mudar o tom |
| "Um impacto no 5 e uma parada no 7" | Insere um som de impacto no tempo 5 e silencia no tempo 7 |

## Decifrar os mixes da Brotherhood (e de outros exemplos)

Uma ferramenta de **análise** que recebe um vídeo e devolve um "raio-x" do mix:
1. **Separar a plateia:** os gritos não somem por completo, mas a separação em faixas e um filtro de ruído reduzem muito.
2. **Linha do tempo de BPM:** mostra onde o andamento muda (cada mudança costuma ser um trecho ou uma música nova).
3. **Cortes e transições:** detecta mudanças bruscas de timbre, volume e tom, e classifica a transição (corte, fade, efeito, silêncio).
4. **Identificar as músicas originais:** compara pedaços com bancos de "impressão digital" de músicas (há opções gratuitas e outras pagas). Remixes muito alterados podem não ser reconhecidos; nesses casos o app mostra o trecho para o Phelipe ouvir e marcar.
5. **Padrões:** com vários exemplos analisados, montamos uma biblioteca do que os melhores fazem (tamanho médio dos trechos, tipos de transição mais usados, onde caem os acentos). Essa biblioteca vira as ferramentas e os modelos prontos do app.

## Onde roda

| Opção | Prós | Contras |
|---|---|---|
| **PC do Phelipe (recomendado no começo)** | Já tem a placa de vídeo GTX 1070 Ti e o mesmo esquema do Estúdio de dublagem (yt-dlp, Python, liga com o Windows) | Só funciona com o PC ligado |
| VPS | Acessível de qualquer lugar | Sem placa de vídeo: separar faixas e gerar música ficaria muito lento |
| Site (área oculta) | Fácil de abrir no celular | O processamento pesado precisa estar em outro lugar |

Proposta: o "motor" roda no PC, e a tela é uma página no navegador (igual ao Estúdio, em `http://127.0.0.1:<porta>`). Depois, se fizer sentido, a tela pode ir para o site ou para a VPS conversando com o PC.

## Motores (gratuitos primeiro)

| Tarefa | Gratuito (no PC) | Pago (só com aprovação) |
|---|---|---|
| Separar faixas | Demucs (HTDemucs) e modelos RoFormer (BS-RoFormer / Mel-RoFormer), hoje os melhores de código aberto | Serviços online de separação |
| BPM, tempos e oitos | Beat This!, madmom, librosa | – |
| Tom (key) e acordes | librosa / Essentia | – |
| Mudar BPM e tom sem estragar o som | Rubber Band | – |
| Efeitos (eco, reverb, filtros, distorção) | Pedalboard (Spotify) / FFmpeg | – |
| Identificar músicas | Chromaprint + AcoustID | ACRCloud, Audd |
| Gerar música do zero | ACE-Step, Stable Audio Open, MusicGen (qualidade ainda abaixo dos pagos) | Suno, Udio |
| Entender o pedido por texto | Regras simples no começo | Claude (API), quando houver verba |

Observação: a GTX 1070 Ti tem 8 GB de memória de vídeo. É suficiente para separar faixas. Para gerar música do zero, alguns modelos podem ficar lentos ou não caber; isso precisa ser testado no PC.

## Etapas sugeridas

1. **Etapa 0: Analisador (pronto para testar no PC).** Recebe vídeo ou link, separa as faixas, mostra o BPM ao longo do tempo, os oitos e as transições, e identifica as músicas. Usamos para estudar a playlist da Brotherhood. Veja o README.
2. **Etapa 1: Editor por oitos.** Abrir uma música, ver as faixas por oito, ligar e desligar voz e bateria, volume, eco, copiar trechos, ouvir na hora, exportar MP3/WAV.
3. **Etapa 2: Colagem com transições (Modo 1).** Várias músicas, ajuste automático de BPM, tom e volume, biblioteca de transições.
4. **Etapa 3: Kits de estilo e injeção (Modo 2).** Baterias e baixos por estilo (da pesquisa), troca de groove por trecho.
5. **Etapa 4: Pedidos por texto.** Escrever o pedido e o app transformar em instruções.
6. **Etapa 5: Música do zero (Modo 3).**

## Direitos autorais (para ter em mente)
- Usar remix de música de artista em apresentação ao vivo depende da licença do evento. Publicar o vídeo no YouTube ou no Instagram pode gerar bloqueio ou aviso de direitos autorais (Content ID).
- O Modo 3 evita isso, desde que os sons usados sejam livres.
- O app é uma ferramenta; quem decide como usar a música é o coreógrafo.
