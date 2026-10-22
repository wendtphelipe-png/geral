# Pesquisa: a música de cada estilo de dança urbana

Base de conhecimento do app. Cada estilo vira um **"kit de estilo"** dentro do programa: uma ficha com BPM, groove, instrumentos e recursos de mixagem que o app usa para "injetar" o estilo numa música.

> A lista completa de referências (mais de 260 músicas) e os padrões de bateria de cada estilo estão em [biblioteca/BIBLIOTECA.md](biblioteca/BIBLIOTECA.md).

> Os BPMs são faixas típicas, não regras. O que mais define o estilo é o **groove** (onde caem as batidas fortes e o balanço) e a **sonoridade**. Tudo aqui deve ser conferido com a filha do Phelipe e com coreógrafos antes de virar regra no app.

## Resumo rápido

| Estilo | BPM típico | Groove / batida | Sonoridade assinatura | Músicas e artistas de referência |
|---|---|---|---|---|
| Breaking | 105–135 | Breakbeat: bateria "quebrada" e repetida, sincopada | Bateria crua de funk, metais, bongôs, scratches | "Apache" (Incredible Bongo Band), "It's Just Begun" (Jimmy Castor), "Give It Up or Turnit a Loose" (James Brown) |
| Locking | 100–120 | Funk anos 70, caixa forte no 2 e no 4, muitos "stops" | Metais, baixo slap, guitarra funk "chicken scratch" | James Brown, Kool & the Gang, Earth Wind & Fire, era Soul Train |
| Popping | 90–110 | Funk/electro-funk lento e pesado; cada caixa é um "hit" | Sintetizador, talkbox, baixo synth, caixa seca e alta | Zapp & Roger, Dayton, electro, G-funk; hoje também glitch/dubstep |
| Hip-Hop (dança) | 85–100 (trap 130–150 em meio tempo) | Boom bap: bumbo e caixa marcados, balanço "bounce" e "rock" | Samples de soul/jazz, scratch, vocal de rap, grave forte | Hip-hop anos 90 (Pete Rock, Tribe Called Quest), new school, trap |
| House | 118–128 | Quatro no chão: bumbo em todo tempo, chimbal aberto no contratempo | Piano, vocal soul/gospel, percussão latina, órgão | House de Chicago e Nova York, garage, deep house |
| Waacking | 110–130 | Disco: bumbo no tempo, chimbal no contratempo, viradas | Cordas, metais, vocal de diva, baixo disco | Disco anos 70 (Donna Summer, Chic, Sylvester) |
| Vogue | 120–135 | Ballroom beat, com o prato "ha" marcando os golpes | Batida eletrônica seca, prato "crash" do "The Ha Dance", chamadas do MC | "The Ha Dance" (Masters at Work), ballroom beats |
| Krump | 70–100 (ou meio tempo de 140) | Pesado, agressivo, muito espaço entre as batidas | Grave distorcido, sintetizadores escuros, impactos, clima tenso | Batidas de "buck" feitas para a cena de Los Angeles (anos 2000) |
| Passinho | 130 (funk) / 150 ("150 BPM") | Tamborzão e "beat do funk carioca" | Atabaque/tamborzão, vocal de MC, sample de "pancadão" | Funk carioca; passinho das favelas do Rio, desde ~2008 |

Estilos que vale incluir depois: **Dancehall** (90–110, riddims jamaicanos), **Afro / Amapiano** (110–115, o "log drum" do amapiano), **Litefeet** (Nova York), **Memphis Jookin**, **Animation/Tutting** (popping com música glitch), **Brega funk** (Recife), **Heels** e **Jazz-funk** (comerciais).

## Fichas detalhadas

### Breaking
- **Origem:** Bronx, Nova York, começo dos anos 70. O DJ Kool Herc repetia o trecho só de bateria (o "break") de discos de funk usando dois toca-discos. Os dançarinos dançavam nesses trechos: daí "b-boys" e "b-girls".
- **O que a música precisa ter:** bateria bem presente e repetida; energia constante para os "power moves"; espaços para os "freezes" (paradas).
- **Recursos de mix comuns:** loop de break, scratch, "back-to-back" do mesmo trecho, acelerar o break.
- **Para o app:** detectar e isolar trechos só de bateria; ferramenta de loop de break; kit de bateria "funk crua".

### Locking
- **Origem:** Los Angeles, fim dos anos 60/70, com Don Campbell ("Campbellock"). Popularizado pelo programa Soul Train e pelo grupo The Lockers.
- **O que a música precisa ter:** funk alegre, com "stops" e acentos fortes. O "lock" (parar o movimento de repente) e os "points" (apontar) caem nos acentos da caixa e dos metais.
- **Para o app:** marcar acentos de metais; criar paradas de 1 tempo ("stop"); kit com metais e baixo slap.

### Popping
- **Origem:** Fresno e Long Beach, Califórnia, anos 70. Boogaloo Sam e os Electric Boogaloos.
- **O que a música precisa ter:** caixa seca e forte. Cada caixa é um "pop" (contração do músculo). Ritmo lento o bastante para os movimentos de robô, "waving" e "tutting".
- **Para o app:** aumentar e secar a caixa; adicionar talkbox/vocoder; ferramenta para "glitch" (picotar) em trechos de animation.

### Hip-Hop Dance (freestyle)
- **Origem:** Nova York, anos 80 e 90, nas festas e clubes ("party dances" como running man, roger rabbit, bart simpson).
- **O que a música precisa ter:** bumbo e caixa claros para o "bounce" (para baixo) e o "rock" (para frente e para trás). O balanço ("swing", batidas ligeiramente atrasadas) é essencial.
- **Para o app:** controle de "swing" na bateria; kits boom bap, new school e trap; reforço de grave.

### House Dance
- **Origem:** Chicago (club The Warehouse, DJ Frankie Knuckles) e Nova York (Paradise Garage), anos 80.
- **O que a música precisa ter:** bumbo em todos os tempos e chimbal no contratempo. Os passos ("footwork", "jacking", "lofting") seguem o balanço contínuo.
- **Para o app:** transformar qualquer bateria em quatro no chão; acelerar para 120–125; percussões latinas (congas, shakers); piano house.

### Waacking
- **Origem:** clubes gays de Los Angeles nos anos 70 ("punking"), na era da disco. Tyrone Proctor é um dos nomes principais.
- **O que a música precisa ter:** disco com cordas, metais e vocais dramáticos. Os braços giram nas notas e as poses ("posing") caem nos acentos e nas pausas.
- **Para o app:** adicionar cordas disco; "filtro" de disco; ferramenta para marcar poses (pausas ou acentos com eco).

### Vogue
- **Origem:** cena ballroom de Nova York (comunidades negras e latinas LGBTQ+), anos 70 e 80. Estilos: Old Way, New Way e Vogue Femme.
- **O que a música precisa ter:** o prato "ha" (do "The Ha Dance") marca os "dips" e "duckwalks"; chamadas do MC ("commentator").
- **Para o app:** biblioteca de sons ballroom; colocar o "ha" nos tempos que a coreografia pedir; meio tempo para "catwalk".

### Krump
- **Origem:** South Central, Los Angeles, começo dos anos 2000. Veio do "clowning" (Tommy the Clown) com Tight Eyez e Big Mijo.
- **O que a música precisa ter:** peso e tensão. Os "stomps", "chest pops" e "arm swings" pedem impactos fortes e grave distorcido. Muito espaço entre as batidas.
- **Para o app:** meio tempo (deixar a música "em câmera lenta" mantendo o tom); distorção de grave; impactos cinematográficos.

### Passinho
- **Origem:** favelas do Rio de Janeiro, por volta de 2008, com vídeos de "batalhas do passinho" nas redes. Mistura funk carioca, frevo, samba, break e kuduro.
- **O que a música precisa ter:** o tamborzão ou o beat de funk; velocidade alta (130, e depois 150 BPM); vocal de MC.
- **Para o app:** kit de tamborzão e "funk 150"; acelerar trechos mantendo a voz natural.

## O que todos têm em comum (e por que isso importa para o app)

1. **A contagem de 8.** Quase toda coreografia é contada em blocos de 8 tempos. O app vai mostrar a música dividida em "oitos" numerados, e cada pedido pode apontar para um deles.
2. **BPM e groove são o que "troca" o estilo.** Para levar uma música para outro estilo, o app troca ou reforça a **bateria** e o **baixo** (o groove), ajusta o BPM e mantém a **voz** ou a **melodia** original (a assinatura).
3. **Acentos.** Os "hits" da coreografia precisam de som: uma caixa forte, um impacto, um "ha", uma parada. O app terá uma ferramenta para colocar acentos exatamente onde a coreografia pede.
