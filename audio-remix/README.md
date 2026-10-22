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

A tela é como a de um editor de áudio:
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
  - "apaga esses oitos".

  Pedidos que ainda não existem (eco, filtros, paradas, mudar o tom, trazer a voz de outro trecho, injetar estilo) são avisados, e nada é mudado.
- **Música original (embaixo):** os oitos da música. Clique para ouvir, arraste para o mix ou dê dois cliques para inserir depois da seleção. As setas ajustam onde fica o "1" da contagem.

Atalhos:
- Espaço: tocar ou pausar;
- L: repetir a seleção;
- Ctrl+Z: desfazer;
- Ctrl+D: repetir a seleção;
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
