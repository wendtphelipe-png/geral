# Motor da fábrica de livros de colorir

Programa que roda **no PC do Phelipe**, na placa de vídeo, e transforma um roteiro de livro em páginas prontas para imprimir. Quem dá os comandos são os agentes da sala MARKETPLACE da STARNET, mas também dá para usar à mão.

## O que ele faz

| Etapa | Comando | O que acontece |
|---|---|---|
| Desenhar | `fabrica desenhar dino-01` | Gera de 4 a 8 versões de cada página na placa (SDXL + estilo "livro de colorir") |
| Acabar | `fabrica acabar dino-01` | Deixa só preto e branco, tira sujeira, transforma mancha preta em contorno, iguala a espessura do traço, centraliza com margem e grava em 300 dpi (A4 = 2480 × 3508 pixels) |
| Conferir | `fabrica conferir dino-01` | Mede sombra, corte na borda, manchas, número de áreas para pintar e áreas pequenas demais para a idade. Dá uma nota e sugere a melhor versão de cada página |
| Tudo acima | `fabrica livro dino-01` | Desenhar + acabar + conferir |
| Montar | `fabrica montar dino-01` | Junta as versões escolhidas pelo revisor num PDF: página "Este livro pertence a", cada desenho com o verso em branco e a página final |
| Placa livre? | `fabrica status` | Diz se a placa está livre. **O estúdio de dublagem tem prioridade**: se ele estiver processando, a fábrica espera |
| Teste | `fabrica teste` | Desenha 1 página de exemplo e mede o tempo |

A conferência automática não substitui o olho. Mão deformada, cena sem sentido e personagem parecido com o de outra empresa ficam com o **MKT REVISOR** e com o Phelipe.

## Instalar (uma vez)

1. Copie a pasta do repositório `geral` para o **SSD novo**. Não use o G: (Google Drive) nem o D: (com defeito).
2. Dê dois cliques em `livros-de-colorir\motor\INSTALAR-MOTOR.bat`. Ele instala o PyTorch (cerca de 3 GB) e o restante; demora de 10 a 20 minutos.
3. Abra o arquivo `config.json`, que o instalador criou, e em `"livros"` coloque a pasta onde ficam os livros, com barras duplas. Exemplo: `"livros": "E:\\Fabrica\\livros"`.
4. Teste:
   1. Abra a pasta `motor` no Explorador.
   2. Clique na barra de endereço, digite `cmd` e aperte Enter.
   3. Digite `fabrica status` e aperte Enter.
   4. Depois digite `fabrica teste` e aperte Enter.
   5. O primeiro teste baixa os modelos (cerca de 7 GB) para a pasta `modelos`.
   6. A página de teste fica em `exemplos\teste\paginas\01\` (`v1.png` é o desenho cru, `v1-final.png` é a página pronta).
5. Mande ao Claude o tempo que apareceu em `"segundos"` e as duas imagens.

## Como é um livro

Cada livro tem uma pasta com o `roteiro.json`, escrito pelo MKT DIRETOR DE ARTE:

```json
{
  "codigo": "dino-01",
  "titulo": "Dino e a Turma do Ovo",
  "idade": "5-8",
  "variacoes": 6,
  "semente": 1000,
  "pagina": { "formato": "A4", "margem_mm": 12 },
  "estilo": { "traco_mm": 1.3 },
  "personagens": {
    "dino": { "referencia": "personagens/dino.png", "forca": 0.6 }
  },
  "paginas": [
    { "n": 1, "cena": "Dino sai do ovo", "prompt": "a cute baby dinosaur hatching from an egg", "personagem": "dino" },
    { "n": 2, "cena": "Dino na floresta", "prompt": "a cute baby dinosaur walking among giant leaves", "personagem": "dino", "negativo": "trees cut off" }
  ]
}
```

- `idade`: `2-4`, `5-8` ou `9-12`. Define a espessura do traço e o tamanho mínimo das áreas:

  | Idade | Traço | Área mínima para pintar |
  |---|---|---|
  | 2-4 | 2,0 mm | 100 mm² |
  | 5-8 | 1,3 mm | 36 mm² |
  | 9-12 | 0,8 mm | 12 mm² |

- `personagens`: uma imagem de referência de cada personagem próprio. O motor usa a referência (IP-Adapter) para manter a mesma cara em todas as páginas.
- O revisor grava a escolha de cada página em `escolhas.json`, assim: `{"1": "v3", "2": "v1"}`. O `montar` usa esse arquivo.
- Formatos: `A4` (padrão), `A5` e `carta`.

## Arquivos

| Arquivo | Função |
|---|---|
| `fabrica.py` / `fabrica.bat` | O comando único |
| `desenhar.py` | Desenho na placa (SDXL base 1.0 + LoRA ColoringBookRedmond V2 + VAE fp16-fix; IP-Adapter para personagens) |
| `acabamento.py` | Acabamento da página |
| `conferir.py` | Conferência automática e regras por idade |
| `montar.py` | PDF do miolo |
| `placa.py` | Revezamento com o estúdio de dublagem |
| `testes/` | Testes sem placa: `python -m unittest discover testes` |

## Licenças dos modelos

| Modelo | Licença |
|---|---|
| SDXL base 1.0 | CreativeML OpenRAIL++-M: permite uso comercial das imagens |
| ColoringBookRedmond V2 | CreativeML OpenRAIL-M |
| IP-Adapter | Apache-2.0 |

Antes da primeira venda, vale ler o texto das licenças.

## Limites conhecidos

- **Velocidade:** a GTX 1070 Ti não é rápida em float16. A estimativa é de 1 a 3 minutos por imagem; o `fabrica teste` mede o tempo real. Se o float16 der imagem preta ou erro, troque `"precisao"` para `"float32"` no `config.json` (fica mais lento).
- **Capa colorida:** ainda não está no motor (próxima etapa).
