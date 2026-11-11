# Audio Remix

App para criar mixes profissionais e personalizados para coreografias de danças urbanas. Roda no PC do Phelipe (precisa da placa de vídeo).

- [PLANO.md](PLANO.md): os três modos do app, o editor por contagens de 8, motores e etapas.
- [PESQUISA-ESTILOS.md](PESQUISA-ESTILOS.md): a música de cada estilo, com origem e explicação.
- [biblioteca/BIBLIOTECA.md](biblioteca/BIBLIOTECA.md): fichas de 11 estilos com BPM, groove, padrão de bateria, instrumentos, efeitos e mais de 260 músicas de referência. A fonte que o app usa é `biblioteca/estilos.json`.
- [DESCOBERTAS.md](DESCOBERTAS.md): a fórmula dos mixes da Brotherhood na IDL.
- `analisador/`: Etapa 0, o raio-x de mixes de competição.
- `editor/`: Etapa 1, o editor por oitos.

## Etapa 1: editor por oitos (no PC)

Dois cliques em `ABRIR-EDITOR.bat`. O navegador abre em http://127.0.0.1:3060. Para desligar, feche a janela preta.

### Criar mix automático (o principal)
Escolha uma **estrutura** na lista amarela ao lado do botão e clique em **Criar mix automático**. O mix sai na duração do campo de duração desejada (padrão 2:45). Cada oito mostra na régua o papel dele, e a explicação aparece na barra de comando. Clicar de novo cria outra versão; Ctrl+Z volta à anterior. Depois, selecione oitos e peça ajustes por texto.

Estruturas prontas (biblioteca/estruturas.json), inspiradas nas diferenças entre as apresentações campeãs da IDL:
- **Clássico IDL:** abertura sem grave, queda, música picotada em ordem, dois respiros, meio tempo e final na voz.
- **Muda no começo:** abre com a música em outro estilo e revela a original na queda.
- **Muda no meio:** música original e, no meio, um bloco de outro estilo (como o bloco de funk/popping de Vancouver R2).
- **Muda no final:** termina em outro estilo (como o remix de clube de Vancouver R1).
- **Picotado com muitos hits:** cortes curtos, muitas paradas, meio tempo e tempo dobrado (como Sydney R1, com Toxic).
- **Acapella dramática:** a voz sozinha abre e volta em dois momentos.
- **Viagem de estilos:** a mesma música passa por house, breaking e krump.

**Blocos de outro estilo:** a música continua, a bateria original sai e entra a bateria do estilo, tocada no BPM da música (sons sintetizados a partir dos padrões da biblioteca de estilos). Ela aparece como uma camada "Bateria house" (ou outro estilo), que dá para silenciar, mover ou ajustar.

### IA do Google (Lyria)
Botão com a varinha, no alto à direita (o ponto fica verde quando está conectado):
- **Conectar:** cole a chave do Google AI Studio (aistudio.google.com, "Get API key") e clique em **Salvar e testar**. A chave fica só no PC, em `audio-remix\dados\chave-google.txt` (fora do GitHub). Também funciona com a variável de ambiente `GEMINI_API_KEY`.
- **Blocos de estilo com IA:** marque **Lyria** ao lado da lista de estruturas. Nos blocos de outro estilo, o Lyria cria o groove do estilo no BPM e no tom da música, e o programa acerta o andamento e o começo para encaixar exato nos oitos. Se a IA falhar, o mix usa a bateria sintetizada e avisa no roteiro.
- **Trecho por texto:** selecione oitos e escreva um pedido começando com `ia:`, por exemplo `ia: metais de funk animados`. O trecho é criado no tempo e no tom da música, numa camada nova, do tamanho da seleção.
- **Música do zero:** em **Nova música**, descreva a música no campo de texto e clique em **Criar com IA**. A música é criada inteira (sem direitos autorais de terceiros), separada em faixas e dividida em oitos, como qualquer outra.

O Lyria é pago por uso. Tudo o que ele gera fica guardado em `audio-remix\dados\ia-cache\`, e um pedido igual não é pago de novo.

### Estruturas: montar a sua
Botão **Estruturas**, aba **Montar estrutura**:
- arraste os modos da esquerda para a sequência, ou clique para pôr no fim, e arraste os passos para mudar a ordem;
- os modos são: abertura sem grave, só voz ou original; queda; música em ordem; picotado; refrão; respiros; só a voz; meio tempo; tempo dobrado; bloco de outro estilo (escolha o estilo); e finais (voz, seco, fade, outro estilo);
- em cada passo, escolha quantos oitos ou "auto" (o "auto" completa a duração);
- dê um nome e escolha quantas paradas o mix deve ter;
- **Salvar na biblioteca** guarda em `audio-remix\dados\estruturas\`, e ela aparece na lista;
- **Criar mix com esta estrutura** usa a sequência na hora.

### Estruturas: analisar um mix pronto
Botão **Estruturas**, aba **Analisar um mix**: cole o link (YouTube) ou solte o arquivo. Em alguns minutos aparece um relatório:
- as músicas usadas e em que trechos (Shazam);
- a comparação com as originais, que o programa baixa sozinho: se a música foi acelerada, desacelerada, posta em meio tempo ou mudou de tom (o tom é uma medida aproximada);
- os trechos sem grave, sem bateria, só voz, meio tempo e tempo dobrado;
- quantos cortes e paradas o mix tem;
- a **estrutura aprendida**.

Depois é só salvar a estrutura na biblioteca ou criar na hora um mix com ela, na música aberta. Os trechos em que entra outra música viram "blocos de outro estilo", com o estilo sugerido pelo BPM; dá para trocar no montador.

### A tela
A tela é como a de um editor de áudio:
- **Barra do mix (segunda linha):** a lista de estruturas, a opção Lyria, o botão Estruturas, **Criar mix automático** e as ferramentas Cortar, Fade in, Fade out e Importar áudio.
- **Barra de cima:** tocar e pausar, voltar ao início, repetir a seleção sem parar, o relógio, o BPM, a duração do mix e a duração desejada (padrão 2:45), desfazer e refazer, aproximar e afastar, nova música e exportar MP3.
- **Régua da contagem:** cada oito do mix, com o número grande, as 8 batidas marcadas e a cor da "parte" da música (partes iguais têm a mesma cor e letra).
  - clique para selecionar;
  - Shift + clique ou arrastar seleciona vários;
  - arrastar um oito já selecionado muda ele de lugar.
- **Faixas na horizontal:** Voz, Bateria, Baixo e Outros.
  - **M** silencia a faixa inteira;
  - **S** deixa só aquela faixa;
  - o controle deslizante muda o volume da faixa inteira;
  - passando o mouse num oito de uma faixa, o botão de alto-falante liga ou desliga aquela faixa só naquele oito.
- **Barra de comando:** selecione oitos e escreva o que fazer, ou use os botões rápidos. Exemplos que ele entende:
  - "tira a voz e deixa o grave 30% mais alto";
  - "deixe apenas os instrumentos";
  - "só a voz";
  - "voz 30% mais baixa";
  - "meio tempo";
  - "repete 2 vezes";
  - "apaga esses oitos";
  - "eco na voz", "muito reverb", "deixa distante", "som de rádio", "abafado", "tira os efeitos";
  - "parada no 5 e no 7", "freeze no 1 de 2 tempos", "tira as paradas";
  - "coloca a voz do oito 5 aqui como eco distante, 30% mais baixa" (cria uma camada com aquele trecho, já com o efeito; o número é o do oito na música original).

  Pedidos que ainda não existem (mudar o tom, injetar estilo) são avisados, e nada é mudado.
- **Ferramentas de edição (barra de cima):**
  - **Cortar** (tecla C): corta no cursor, a linha branca. Para pôr o cursor no lugar, clique na régua do tempo. Se um clipe estiver selecionado, corta o clipe; se não, corta o oito da trilha principal na batida mais próxima (com Alt, no ponto exato).
  - **Fade in / Fade out:** aplicam na seleção. Em vários oitos, o fade atravessa a seleção inteira. Também dá para escrever: "fade out de 2 oitos", "fade in 3 segundos". A curva do volume aparece desenhada sobre as faixas.
  - **Importar áudio** (tecla I): qualquer mp3, wav, m4a etc. Vira uma camada nova, no ponto do cursor. Também dá para arrastar o arquivo do Windows para dentro do editor.
- **Camadas (abaixo das 4 faixas):** quantas quiser, cada uma com nome, M, S, volume e um botão para apagar.
  - **+ Nova camada** cria uma vazia.
  - **Arrastar um oito de uma faixa** (por exemplo, a voz do oito 5) para uma camada copia aquele trecho. Serve para "colocar a voz daquele trecho aqui".
  - **Clipes:** arraste para mudar de lugar (encaixa nas batidas; com Alt, fica livre) ou para outra camada. Puxe as bordas para encurtar. Puxe as bolinhas brancas dos cantos para fazer fade. Dois cliques tocam a partir do clipe.
  - Com um clipe selecionado, a barra de comando muda o volume ("30% mais baixo"), faz fade, repete ou apaga o clipe.
- **Música original (embaixo):** os oitos da música. Clique para ouvir, arraste para o mix ou dê dois cliques para inserir depois da seleção. As setas ajustam onde fica o "1" da contagem.

Atalhos:
- Espaço: tocar ou pausar;
- L: repetir a seleção;
- Ctrl+Z: desfazer;
- Ctrl+D: repetir a seleção;
- C: cortar no cursor;
- I: importar áudio;
- Delete: apagar;
- Ctrl+A: selecionar tudo;
- Enter: escrever um pedido;
- Ctrl + rodinha do mouse: zoom.

Tudo é salvo sozinho em `audio-remix\dados\projetos\`. A música original nunca é alterada. O MP3 vai para `audio-remix\dados\exportados\`.

Teste do entendedor de pedidos: `node editor/testes/comandos.test.js`.

## Etapa 0: analisar os mixes da Brotherhood (no PC)

O ambiente do Claude na nuvem não acessa o YouTube. Por isso o download e a análise rodam no PC, e só os relatórios (números e nomes de músicas) vão para o GitHub. Os áudios ficam em `audio-remix\dados\`, que não é enviado.

### Uma vez só
1. Baixar o repositório no PC (no Prompt de Comando):
   ```
   git clone https://github.com/wendtphelipe-png/geral D:\Projetos\geral
   ```
2. Dois cliques em `D:\Projetos\geral\audio-remix\PREPARAR-ANALISADOR.bat`. Ele:
   - cria o ambiente Python em `D:\Projetos\remix-py`;
   - instala o PyTorch para a placa de vídeo, o separador de faixas (Demucs), o yt-dlp e o identificador de músicas;
   - instala o FFmpeg e o Deno se faltarem.

   Leva alguns minutos e baixa uns 3 GB.

### Para analisar
1. Dois cliques em `ANALISAR-PLAYLIST.bat`.
2. Cole o link, ou aperte Enter para usar a playlist da Brotherhood.
3. Ele baixa o áudio de cada vídeo, separa as faixas, mede BPM e trechos, identifica as músicas e envia os relatórios para o GitHub.
4. Avise o Claude quando terminar.

Se o YouTube pedir login, o programa tenta os cookies do Chrome (onde está a conta Premium). Para isso o **Chrome precisa estar fechado** durante o download. Se mesmo assim falhar, ele tenta o Edge e o Firefox.

### O que sai em `analises/`
Para cada vídeo:
- `.md`: tabela dos trechos e das transições;
- `.json`: todos os números;
- `.png`: gráfico do BPM com as transições marcadas.

Para o conjunto: `RESUMO.md`, com os padrões de duração, tamanho dos trechos em oitos, tipos de transição e músicas mais usadas.

## Decisões do Phelipe (22/10/2026)
- Começar no PC.
- A biblioteca deve ter todos os estilos citados, com muitas referências.
- A duração padrão sai da análise da playlist, mas o usuário pode definir o tempo total da música.
- Uso inicial só pela filha e alguns colegas. Licenças ficam para depois.
