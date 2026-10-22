# O que as análises mostram: a fórmula da Brotherhood na IDL

Análise de 22/10/2026, com voz, bateria, baixo e outros separados na placa de vídeo.

**O que foi analisado.** A playlist tem 14 vídeos, que são **10 apresentações diferentes**: 4 aparecem duas vezes, filmadas de frente e de longe. Os resultados das duas filmagens de uma mesma apresentação saíram praticamente iguais, o que mostra que o analisador é consistente.

| Etapa | Round | Música principal (identificada) | Outras músicas |
|---|---|---|---|
| Launch 2025 | 1 | Lecrae & 1K Phew – MOVE | – |
| Launch 2025 | 2 (1º lugar) | Tyga – Wish | Justin Bieber – All That Matters; P-LO – Going Off |
| Nova York 2026 | 1 | Doja Cat – Jealous Type | – |
| Nova York 2026 | 2 (1º lugar) | Pop Smoke – Mannequin | Busta Rhymes & Janet Jackson – What's It Gonna Be?!; Lil Wayne – Uproar; trechos não identificados |
| Vancouver 2026 | 1 | Ludacris – Get Back | um remix de clube no final |
| Vancouver 2026 | 2 (1º lugar) | *NSYNC – I Want You Back | um bloco de funk/popping de 40 s no meio |
| Sydney 2026 | 1 | Britney Spears – Toxic | – |
| Sydney 2026 | 2 (1º lugar) | Don Toliver – After Party | segunda metade não identificada |
| Seul 2026 | 1 | (não identificada: provavelmente muito editada ou produção própria) | – |
| Seul 2026 | 2 | HUNTR/X – Takedown (KPop Demon Hunters) | – |

## Os padrões

### 1. Uma música âncora, famosa
- Em **6 das 9** apresentações com música identificada, uma única música ocupa quase o mix inteiro. Nas outras, são 2 ou 3 músicas, em blocos grandes.
- As músicas são **sucessos que a plateia reconhece**: Toxic, I Want You Back, Get Back, Takedown. Isso confirma a sua ideia do "modo 2": a familiaridade é a base e a surpresa vem da edição.

### 2. Picotar e reorganizar, sempre no tempo
- Há uma mudança forte a cada **11 a 13 segundos**, cerca de **4,4 mudanças por minuto**.
- Cada trecho tem de **2 a 4 oitos**.
- **69% das mudanças são cortes**, mas cortes feitos na batida e no mesmo BPM. Por isso não soam "secos": a música continua no tempo e só muda de parte.
- O volume quase não varia dentro de um mix (2 a 3 dB). Foi tudo **nivelado**.

### 3. Abertura sem grave, depois "a queda"
- Em **7 das 10** apresentações, os primeiros 3 a 12 segundos praticamente não têm baixo: voz, efeito ou só bateria. Depois o grave entra de uma vez.

### 4. Final na voz
- Em **6 das 10**, o último trecho é dominado pela voz, com pouco ou nenhum grave: um fim falado, cantado ou "a capela" sobre a pose final.

### 5. Respiros no meio: tirar o grave ou tirar a bateria
São dois recursos diferentes, ambos de 1 a 2 oitos:
- **Sem grave:** fica só bateria e voz. Aparece em Nova York R2, Vancouver R1 e R2, e Seul R1.
- **Sem bateria:** fica voz e instrumentos. Aparece em Launch R2.

### 6. Meio tempo e tempo dobrado
- Em **44% das mudanças** o BPM muda, mas a maioria é a **mesma música em meio tempo ou em tempo dobrado**. Exemplo: em Toxic ela alterna 144 e 72.
- Trocas de BPM de verdade acontecem quase só na troca de música, por exemplo de 96 para 129 na Launch R2.

### 7. Injeção de outro estilo dentro da música
- Em **Vancouver R2** (1º lugar), um bloco de **cerca de 40 segundos de funk/popping** entra no meio de I Want You Back, no mesmo BPM, e depois a música volta. É exatamente o "injetar um estilo" que você quer no app.
- Em **Vancouver R1**, o final vira um remix de clube num BPM um pouco mais alto, de 86 para 99.

### 8. Paradas curtas (hits)
- Em média são **2,6 paradas por minuto**, de cerca de **0,2 segundo**: cortes de um tempo para os "hits" da coreografia.
- Uma apresentação teve muito mais: **Sydney R1 (Toxic)**, com 17 paradas em 3 minutos.

### 9. Duração
- A duração total dos vídeos varia de **2:35 a 3:15**, com metade entre **2:41 e 2:55** (mediana de 2:50). Isso inclui alguns segundos de entrada e de saída.
- Para o app: **duração padrão de 2:45**, que você pode mudar.

## O que isso vira no app (ferramentas, em ordem de importância)
1. **Escolher a música âncora** e ver as partes dela em oitos (refrão, verso, ponte).
2. **Cortar, reordenar e repetir oitos**, com o corte sempre encaixado na batida e o volume nivelado sozinho.
3. **Ligar e desligar faixas por oito**: grave, bateria, voz e instrumentos.
4. **Meio tempo e tempo dobrado** num trecho, sem mudar o tom da voz.
5. **Bloco de estilo:** inserir 2 a 6 oitos de outro estilo (funk, house, breaking...) no mesmo BPM. Vem da biblioteca de estilos.
6. **Paradas/hits:** marcar o tempo exato e o app corta o som por meio tempo ou um tempo.
7. **Moldes prontos:** "abertura sem grave + queda" e "final na voz".

## Cuidados com estes números
- A identificação de músicas às vezes erra. O mesmo bloco de funk de Vancouver R2 foi identificado como "Funkenstein" numa filmagem e "Da Popping" na outra. Os dois nomes são de músicas de estúdio parecidas, então o certo é só "bloco de funk/popping".
- Os BPMs vêm em degraus (117,5; 129,2; 143,6) por causa da precisão da medição. O valor real pode estar 1 ou 2 BPM ao lado.
- O tom (a nota) detectado não é confiável em música com rap e plateia.
- O resumo automático (`analises/RESUMO.md`) conta as apresentações filmadas duas vezes como dois mixes. Os números acima consideram só as 10 apresentações.
