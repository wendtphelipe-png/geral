# Desenha as fichas de modelo da turma dos Rabiscos em SVG (traço vetorial).
#
# Cada personagem sai em duas versões:
#   - para colorir (preto e branco), que é a referência do motor de desenho;
#   - colorida, com as cores oficiais, para capas, site e cartas.
# A ficha traz o corpo inteiro e três expressões. Os braços e as pernas ficam
# separados do corpo de propósito: é o que permite animar o desenho pintado
# pela criança no "Ganha Vida".
#
# Uso: python desenhar_turma.py   (grava em fichas/)
import os

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, 'fichas')
TRACO = 9  # espessura do traço principal

CORES = {
    'cacho': '#FFC93C',
    'zuzu': '#3FA9F5',
    'pingo': '#7BD389',
    'lala': '#FF8FB1',
    'compasso': '#A88BEB',
    'cinzao': '#A7A9AC',
    'bochecha': '#FFB3A7',
    'branco': '#FFFFFF',
}


class Tinta:
    """Escolhe a cor de preenchimento: branco na versão para colorir."""
    def __init__(self, colorida):
        self.colorida = colorida

    def __call__(self, nome):
        return CORES[nome] if self.colorida else '#FFFFFF'


def caminho(d, fill='#FFFFFF', largura=TRACO):
    return (f'<path d="{d}" fill="{fill}" stroke="#111" stroke-width="{largura}" '
            f'stroke-linecap="round" stroke-linejoin="round"/>')


def linha(d, largura=TRACO):
    return caminho(d, fill='none', largura=largura)


def circulo(x, y, r, fill='#FFFFFF', largura=TRACO):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="#111" '
            f'stroke-width="{largura}"/>')


def elipse(x, y, rx, ry, fill='#FFFFFF', largura=TRACO, giro=0):
    return (f'<ellipse cx="{x}" cy="{y}" rx="{rx}" ry="{ry}" fill="{fill}" stroke="#111" '
            f'stroke-width="{largura}" transform="rotate({giro} {x} {y})"/>')


# ---------- rosto (olhos, boca, bochechas) ----------

def olho(x, y, r, expr):
    partes = [elipse(x, y, r, r * 1.2, largura=TRACO * 0.8)]
    if expr == 'triste':
        partes.append(f'<circle cx="{x}" cy="{y + r * 0.35}" r="{r * 0.5}" fill="#111"/>')
    elif expr == 'surpreso':
        partes.append(f'<circle cx="{x}" cy="{y}" r="{r * 0.38}" fill="#111"/>')
    else:
        partes.append(f'<circle cx="{x + r * 0.12}" cy="{y + r * 0.1}" r="{r * 0.55}" fill="#111"/>')
    # brilho no olho: deixa o personagem vivo
    partes.append(f'<circle cx="{x + r * 0.32}" cy="{y - r * 0.25}" r="{r * 0.2}" fill="#fff"/>')
    return ''.join(partes)


def sobrancelhas(x1, x2, y, r, expr):
    if expr == 'surpreso':
        return (linha(f'M{x1 - r} {y - r * 2.1} Q{x1} {y - r * 2.7} {x1 + r} {y - r * 2.1}', TRACO * 0.7)
                + linha(f'M{x2 - r} {y - r * 2.1} Q{x2} {y - r * 2.7} {x2 + r} {y - r * 2.1}', TRACO * 0.7))
    if expr == 'triste':
        return (linha(f'M{x1 - r} {y - r * 1.6} L{x1 + r * 0.8} {y - r * 2.1}', TRACO * 0.7)
                + linha(f'M{x2 - r * 0.8} {y - r * 2.1} L{x2 + r} {y - r * 1.6}', TRACO * 0.7))
    if expr == 'bravo':
        return (linha(f'M{x1 - r} {y - r * 2.1} L{x1 + r * 0.9} {y - r * 1.5}', TRACO * 0.8)
                + linha(f'M{x2 - r * 0.9} {y - r * 1.5} L{x2 + r} {y - r * 2.1}', TRACO * 0.8))
    return ''


def boca(x, y, l, expr):
    if expr == 'surpreso':
        return elipse(x, y + l * 0.1, l * 0.22, l * 0.3, fill='#fff', largura=TRACO * 0.8)
    if expr == 'triste':
        return linha(f'M{x - l * 0.4} {y + l * 0.25} Q{x} {y - l * 0.15} {x + l * 0.4} {y + l * 0.25}', TRACO * 0.8)
    if expr == 'bravo':
        return linha(f'M{x - l * 0.45} {y + l * 0.1} Q{x - l * 0.1} {y - l * 0.15} {x + l * 0.15} {y + l * 0.05} '
                     f'Q{x + l * 0.35} {y + l * 0.2} {x + l * 0.5} {y - l * 0.05}', TRACO * 0.8)
    # feliz: sorriso aberto
    return caminho(f'M{x - l * 0.5} {y - l * 0.05} Q{x} {y + l * 0.75} {x + l * 0.5} {y - l * 0.05} Z',
                   fill='#fff', largura=TRACO * 0.8)


def rosto(cx, cy, escala, expr, tinta, bochechas=True):
    r = 22 * escala
    sep = 46 * escala
    partes = [olho(cx - sep, cy, r, expr), olho(cx + sep, cy, r, expr),
              sobrancelhas(cx - sep, cx + sep, cy, r, expr),
              boca(cx, cy + 58 * escala, 60 * escala, expr)]
    if bochechas:
        partes.append(elipse(cx - sep * 1.75, cy + 45 * escala, 15 * escala, 10 * escala,
                             fill=tinta('bochecha'), largura=TRACO * 0.6))
        partes.append(elipse(cx + sep * 1.75, cy + 45 * escala, 15 * escala, 10 * escala,
                             fill=tinta('bochecha'), largura=TRACO * 0.6))
    return ''.join(partes)


# ---------- braços e pernas (separados do corpo, para a animação) ----------

def braco(x, y, lado, tinta, cor, comprimento=110, sobe=-40):
    """Braço em curva com mãozinha redonda. lado = -1 (esquerda) ou 1 (direita)."""
    fx, fy = x + lado * comprimento, y + sobe
    cx, cy = x + lado * comprimento * 0.5, y + 30
    return (caminho(f'M{x} {y - 18} Q{cx} {cy - 14} {fx} {fy - 15} L{fx} {fy + 15} Q{cx} {cy + 26} {x} {y + 18} Z',
                    fill=tinta(cor))
            + circulo(fx + lado * 12, fy, 27, fill=tinta(cor)))


def perna(x, y, lado, tinta, cor, comprimento=70):
    fy = y + comprimento
    return (caminho(f'M{x - 15} {y} L{x - 13} {fy} L{x + 13} {fy} L{x + 15} {y} Z', fill=tinta(cor))
            + elipse(x + lado * 14, fy + 8, 40, 20, fill=tinta(cor)))


# ---------- personagens (cada um num quadro de 600 x 720) ----------

def cacho(tinta, expr='feliz'):
    """Cacho: o protagonista. Corpo de feijão e um cacho em espiral na cabeça."""
    c = 'cacho'
    p = [perna(250, 600, -1, tinta, c), perna(350, 600, 1, tinta, c),
         braco(165, 430, -1, tinta, c, sobe=-70), braco(435, 430, 1, tinta, c, sobe=10)]
    p.append(caminho('M300 175 C430 175 470 290 465 420 C460 560 400 625 300 625 '
                     'C200 625 140 560 135 420 C130 290 170 175 300 175 Z', fill=tinta(c)))
    # o cacho: uma espiral que nasce no topo da cabeça
    p.append(linha('M300 178 C300 120 340 80 380 95 C420 110 415 165 375 170 '
                   'C345 173 335 140 355 128 C368 120 380 130 375 142', TRACO * 1.1))
    p.append(rosto(300, 360, 1.15, expr, tinta))
    return ''.join(p)


def zuzu(tinta, expr='feliz'):
    """Zuzu: feita de zigue-zague. Corpo de gota invertida com crista em raio."""
    c = 'zuzu'
    p = [perna(255, 610, -1, tinta, c), perna(345, 610, 1, tinta, c),
         braco(175, 460, -1, tinta, c, sobe=-90), braco(425, 460, 1, tinta, c, sobe=-90)]
    p.append(caminho('M300 150 L340 215 L395 195 L405 265 L470 280 L450 340 '
                     'C495 430 480 560 400 615 C350 645 250 645 200 615 C120 560 105 430 150 340 '
                     'L130 280 L195 265 L205 195 L260 215 Z', fill=tinta(c)))
    # raiozinho no peito: a marca da Zuzu
    p.append(caminho('M310 470 L270 540 L305 540 L285 600 L345 520 L310 520 L335 470 Z', fill='#fff',
                     largura=TRACO * 0.7))
    p.append(rosto(300, 380, 1.05, expr, tinta))
    return ''.join(p)


def pingo(tinta, expr='feliz'):
    """Pingo: o caçula. Uma gotinha com a pontinha virada."""
    c = 'pingo'
    p = [perna(265, 615, -1, tinta, c, comprimento=50), perna(335, 615, 1, tinta, c, comprimento=50),
         braco(200, 520, -1, tinta, c, comprimento=80, sobe=-20), braco(400, 520, 1, tinta, c, comprimento=80, sobe=-20)]
    p.append(caminho('M300 300 C315 340 350 370 385 410 C450 480 440 625 300 625 '
                     'C160 625 150 480 215 410 C250 370 285 340 300 300 Z', fill=tinta(c)))
    p.append(linha('M300 302 C310 270 340 262 352 282', TRACO))
    p.append(rosto(300, 480, 0.95, expr, tinta))
    return ''.join(p)


def lala(tinta, expr='feliz'):
    """Lalá: feita de laços. Laço grande na cabeça e saia em looping."""
    c = 'lala'
    p = [perna(260, 590, -1, tinta, c), perna(340, 590, 1, tinta, c)]
    # saia em looping (três ondas)
    p.append(caminho('M190 520 C160 600 215 615 240 580 C260 625 340 625 360 580 '
                     'C385 615 440 600 410 520 Z', fill=tinta(c)))
    p += [braco(185, 440, -1, tinta, c, sobe=-110), braco(415, 440, 1, tinta, c, sobe=20)]
    p.append(circulo(300, 380, 155, fill=tinta(c)))
    # o laço
    p.append(caminho('M300 230 C250 160 170 170 190 225 C205 270 270 250 300 230 Z', fill=tinta(c)))
    p.append(caminho('M300 230 C350 160 430 170 410 225 C395 270 330 250 300 230 Z', fill=tinta(c)))
    p.append(circulo(300, 230, 24, fill=tinta(c)))
    p.append(rosto(300, 370, 1.05, expr, tinta))
    return ''.join(p)


def compasso(tinta, expr='feliz'):
    """Vô Compasso: o sábio. Pernas de compasso, óculos redondos e bigode."""
    c = 'compasso'
    p = []
    # pernas de compasso: uma termina em bolinha, a outra em ponta de lápis
    p.append(caminho('M270 360 L190 665 L225 672 L300 380 Z', fill=tinta(c)))
    p.append(circulo(205, 672, 16, fill='#fff'))
    p.append(caminho('M330 360 L410 640 L375 648 L300 380 Z', fill=tinta(c)))
    p.append(caminho('M410 640 L375 648 L405 700 Z', fill='#fff'))
    p += [braco(205, 300, -1, tinta, c, comprimento=95, sobe=60), braco(395, 300, 1, tinta, c, comprimento=95, sobe=-60)]
    # cabeça (a dobradiça do compasso) e o cabo, que parece um chapéu
    p.append(caminho('M285 90 L315 90 L318 150 L282 150 Z', fill=tinta(c)))
    p.append(circulo(300, 270, 125, fill=tinta(c)))
    # óculos redondos
    p.append(circulo(255, 255, 38, fill='#fff', largura=TRACO * 0.8))
    p.append(circulo(345, 255, 38, fill='#fff', largura=TRACO * 0.8))
    p.append(linha('M293 255 L307 255', TRACO * 0.8))
    for x in (255, 345):
        p.append(f'<circle cx="{x}" cy="{258 if expr != "triste" else 266}" r="11" fill="#111"/>')
    p.append(sobrancelhas(255, 345, 255, 22, expr))
    # bigode
    p.append(caminho('M300 315 C270 295 225 305 225 335 C250 330 275 335 300 325 '
                     'C325 335 350 330 375 335 C375 305 330 295 300 315 Z', fill='#fff'))
    p.append(boca(300, 345, 40, expr) if expr != 'feliz' else linha('M282 345 Q300 362 318 345', TRACO * 0.8))
    return ''.join(p)


def cinzao(tinta, expr='bravo'):
    """Cinzão: o vilão atrapalhado. Uma nuvem borrada que guarda as cores roubadas na barriga."""
    c = 'cinzao'
    p = [perna(240, 590, -1, tinta, c, comprimento=55), perna(360, 590, 1, tinta, c, comprimento=55),
         braco(135, 420, -1, tinta, c, sobe=-60), braco(465, 420, 1, tinta, c, sobe=-60)]
    p.append(caminho('M150 330 C110 260 170 190 235 210 C250 150 340 140 365 200 '
                     'C430 170 495 230 465 300 C520 350 500 450 445 470 '
                     'C470 540 400 610 330 585 C300 625 215 615 200 570 '
                     'C130 580 95 500 135 455 C80 420 95 340 150 330 Z', fill=tinta(c)))
    # a barriga transparente com as cores roubadas (bolinhas)
    p.append(elipse(300, 470, 105, 75, fill='#fff', largura=TRACO * 0.8))
    for (x, y, r, cor) in [(250, 460, 20, 'cacho'), (300, 495, 18, 'zuzu'), (345, 455, 22, 'lala'),
                           (300, 440, 14, 'pingo'), (265, 505, 12, 'compasso')]:
        p.append(circulo(x, y, r, fill=tinta(cor), largura=TRACO * 0.6))
    p.append(rosto(300, 315, 1.0, expr, tinta, bochechas=False))
    return ''.join(p)


TURMA = [
    ('cacho', 'Cacho', cacho),
    ('zuzu', 'Zuzu', zuzu),
    ('pingo', 'Pingo', pingo),
    ('lala', 'Lalá', lala),
    ('compasso', 'Vô Compasso', compasso),
    ('cinzao', 'Cinzão', cinzao),
]


def svg(largura, altura, conteudo):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largura} {altura}" '
            f'width="{largura}" height="{altura}"><rect width="100%" height="100%" fill="#fff"/>{conteudo}</svg>')


def ficha(chave, nome, funcao, colorida):
    """Ficha de modelo: corpo inteiro grande + três expressões."""
    tinta = Tinta(colorida)
    exprs = ['feliz', 'surpreso', 'triste'] if chave != 'cinzao' else ['bravo', 'surpreso', 'triste']
    partes = [f'<g transform="translate(40 60)">{funcao(tinta, exprs[0])}</g>']
    for i, e in enumerate(exprs):
        partes.append(f'<g transform="translate({700 + i * 270} 230) scale(0.42)">{funcao(tinta, e)}</g>')
    partes.append(f'<text x="40" y="70" font-family="Arial Rounded MT Bold, Arial, sans-serif" '
                  f'font-size="56" font-weight="bold" fill="#111">{nome}</text>')
    return svg(1540, 820, ''.join(partes))


def turma(colorida):
    tinta = Tinta(colorida)
    partes = []
    posicoes = [(0, 120, 0.85), (440, 140, 0.8), (860, 260, 0.65), (1180, 130, 0.82),
                (1600, 70, 0.9), (2050, 120, 0.85)]
    for (chave, _nome, funcao), (x, y, s) in zip(TURMA, posicoes):
        expr = 'bravo' if chave == 'cinzao' else 'feliz'
        partes.append(f'<g transform="translate({x} {y}) scale({s})">{funcao(tinta, expr)}</g>')
    return svg(2600, 780, ''.join(partes))


def flor(x, y, r):
    partes = [linha(f'M{x} {y + r} C{x - 10} {y + r * 3} {x + 15} {y + r * 4} {x} {y + r * 5.2}', TRACO * 1.2)]
    partes.append(caminho(f'M{x} {y + r * 3.4} C{x + r} {y + r * 2.4} {x + r * 2.2} {y + r * 3} {x + r * 1.8} {y + r * 3.6} '
                          f'C{x + r * 1.3} {y + r * 4.1} {x + r * 0.4} {y + r * 4} {x} {y + r * 3.4} Z'))
    for i in range(6):
        import math
        a = math.pi * 2 * i / 6
        partes.append(elipse(x + math.cos(a) * r * 1.15, y + math.sin(a) * r * 1.15, r * 0.75, r * 0.5,
                             giro=math.degrees(a)))
    partes.append(circulo(x, y, r * 0.65))
    return ''.join(partes)


def pagina_exemplo():
    """Página 1 do episódio piloto: o Cacho encontra o Pingo, triste porque a
    flor dele ficou sem cor. Formato A4 em pé."""
    tinta = Tinta(False)
    p = []
    # sol, nuvem e morros ao fundo: poucas linhas, áreas grandes
    p.append(circulo(1040, 230, 95))
    for i in range(8):
        import math
        a = math.pi * 2 * i / 8
        p.append(linha(f'M{1040 + math.cos(a) * 125} {230 + math.sin(a) * 125} '
                       f'L{1040 + math.cos(a) * 175} {230 + math.sin(a) * 175}', TRACO * 1.2))
    p.append(caminho('M170 330 C150 270 230 230 280 260 C300 200 400 200 420 260 C480 240 530 300 490 340 Z'))
    p.append(linha('M0 1180 C250 1050 450 1060 650 1150 C850 1060 1050 1040 1240 1130', TRACO * 1.3))
    p.append(flor(860, 900, 70))
    p.append(f'<g transform="translate(60 820) scale(1.25)">{cacho(tinta, "surpreso")}</g>')
    p.append(f'<g transform="translate(700 1080) scale(0.85)">{pingo(tinta, "triste")}</g>')
    # gotinhas de choro do Pingo
    p.append(caminho('M890 1490 C900 1510 910 1525 900 1535 C890 1545 875 1535 880 1520 Z', largura=TRACO * 0.7))
    return svg(1240, 1754, ''.join(p))


def main():
    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(SAIDA, 'pagina-exemplo.svg'), 'w', encoding='utf-8') as f:
        f.write(pagina_exemplo())
    for chave, nome, funcao in TURMA:
        for colorida, sufixo in ((False, 'colorir'), (True, 'cores')):
            with open(os.path.join(SAIDA, f'{chave}-{sufixo}.svg'), 'w', encoding='utf-8') as f:
                f.write(ficha(chave, nome, funcao, colorida))
        # referência para o motor (IP-Adapter): só o personagem, de frente, sem texto
        with open(os.path.join(SAIDA, f'{chave}-referencia.svg'), 'w', encoding='utf-8') as f:
            f.write(svg(680, 780, f'<g transform="translate(40 40)">{funcao(Tinta(False), "bravo" if chave == "cinzao" else "feliz")}</g>'))
    for colorida, sufixo in ((False, 'colorir'), (True, 'cores')):
        with open(os.path.join(SAIDA, f'turma-{sufixo}.svg'), 'w', encoding='utf-8') as f:
            f.write(turma(colorida))


if __name__ == '__main__':
    main()
