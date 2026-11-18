"""Lote-teste Gesso Law: 6 rostos com tema Toy Story.

Padrão único da coleção (para as peças parecerem da mesma família):
- só a cabeça, vista de frente, estilo "fofinho" (olhos grandes, formas arredondadas);
- todas cabem em 64 x 64 mm (impressora: máximo 70 mm);
- placa de base de 5 mm, costas planas, paredes com saída de ~11 graus;
- volumes em "almofada" com as mesmas alturas: rosto ~2,5 mm, chapéu/capuz ~4 a 5 mm;
- o mesmo olho em todos (branco, íris, pupila e um brilho rebaixado);
- furo de 3,6 mm no alto para a fita.

Uso: python toy_story.py            (gera todos)
     python toy_story.py woody rex  (gera só alguns)
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from gesso import Peca, simetrica  # noqa: E402

PELE = (246, 206, 172)
BRANCO = (252, 252, 250)
PRETO = (35, 32, 30)
BOCA = (120, 35, 45)
LINGUA = (235, 120, 130)


# ---------- peças em comum (o "padrão" da coleção) ----------
def olho(p, cx, cy, rx, ry, iris, olhar=(0.0, -0.12)):
    branco = p.elipse(cx, cy, rx, ry)
    p.relevo(branco, 0.7, 0.6, BRANCO)
    ri = min(rx, ry) * 0.62
    ix, iy = cx + olhar[0] * rx, cy + olhar[1] * ry
    p.relevo(p.circulo(ix, iy, ri) & branco, 0.45, 0.4, iris)
    p.relevo(p.circulo(ix, iy, ri * 0.5), 0.3, 0.3, PRETO)
    p.rebaixo(p.circulo(ix + ri * 0.38, iy + ri * 0.42, ri * 0.24), 0.35, 0.2, BRANCO)


def sobrancelha(p, pontos, largura, cor, espelhar=True):
    p.relevo(p.traco(pontos, largura), 0.9, 0.6, cor)
    if espelhar:
        p.relevo(p.traco([(-x, y) for x, y in pontos], largura), 0.9, 0.6, cor)


def boca_aberta(p, contorno, linha_dentes, lingua=None):
    boca = p.rebaixo(p.poligono(contorno), 1.4, 0.6, BOCA)
    p.relevo(boca & (p.Y > linha_dentes), 1.0, 0.4, BRANCO)
    if lingua is not None:
        p.relevo(lingua & boca & (p.Y <= linha_dentes - 0.6), 0.5, 0.8, LINGUA)
    return boca


# ---------- personagens ----------
def woody():
    p = Peca("woody")
    MARROM = (165, 112, 62)
    CABELO = (110, 70, 40)
    rosto = p.poligono(simetrica([(0, 13), (10, 12), (15.5, 6), (16.5, -4), (15, -15), (11, -24), (5, -29), (0, -30)]))
    orelhas = p.elipse(-16.5, -5, 4, 6) | p.elipse(16.5, -5, 4, 6)
    aba = p.poligono([(-31, 17), (-29.5, 21), (-26, 19), (-15, 16.5), (0, 16), (15, 16.5), (26, 19), (29.5, 21),
                      (31, 17), (28, 13), (16, 10.5), (0, 10), (-16, 10.5), (-28, 13)])
    copa = p.poligono(simetrica([(0, 28.3), (4, 30.5), (10, 30), (13.5, 26), (14.5, 19), (14, 15), (0, 15)]))
    for m in (rosto, orelhas, aba, copa):
        p.contorno(m)
    p.iniciar()
    p.parte(orelhas, 1.6, 3, PELE)
    p.parte(rosto, 2.2, 9, PELE)
    for s in (1, -1):  # costeletas
        p.relevo(p.poligono([(s * 15.5, 11), (s * 12, 11), (s * 12.5, 5), (s * 14, 2.5), (s * 16, 5)]), 0.6, 0.6, CABELO)
        p.sulco([(s * 15.5, -2), (s * 18, -3.5), (s * 18, -6.5), (s * 15.5, -8.5)], 0.8, 0.5)
    p.parte(aba, 3.6, 2.5, MARROM)
    p.parte(copa, 5.0, 6, MARROM)
    faixa = p.parte(copa & (p.Y > 16.5) & (p.Y < 19.5), 5.0, 6, (95, 60, 35))
    p.sulco([(-14, 16.5), (14, 16.5)], 0.8, 0.5, suave=False)
    p.sulco([(-14.3, 19.5), (14.3, 19.5)], 0.8, 0.5, suave=False)
    p.sulco([(0, 29.5), (0, 26.8)], 2.0, 0.8, suave=False)  # amassado da copa
    sobrancelha(p, [(-10.5, 7.2), (-7, 8.7), (-3, 7.7)], 1.8, CABELO)
    olho(p, -6.3, 1, 4.0, 5.0, (125, 80, 40))
    olho(p, 6.3, 1, 4.0, 5.0, (125, 80, 40))
    p.relevo(p.elipse(0, -5.5, 2.4, 4.2), 1.5, 2.0)  # nariz comprido
    boca_aberta(p, [(-9, -12), (0, -11.6), (9, -12), (7, -17.5), (0, -21), (-7, -17.5)], -14.4, p.elipse(0, -19, 4.5, 2.2))
    p.furo(0, 23.2)
    return p


def buzz():
    p = Peca("buzz")
    ROXO = (130, 85, 175)
    capuz = p.poligono(simetrica([(0, 29), (11, 28), (18.5, 22), (22, 10), (22, -4), (20.5, -14), (17, -21), (12, -23), (0, -22)]))
    rosto = p.poligono(simetrica([(0, 19), (9, 18.5), (14.5, 13), (16, 2), (15.5, -9), (13.5, -18), (9, -25.5), (4, -29.5), (0, -30)]))
    p.contorno(capuz)
    p.contorno(rosto)
    p.iniciar()
    p.parte(capuz & ~rosto, 4.0, 3.5, ROXO)
    p.parte(rosto, 2.6, 8, PELE)
    p.relevo(p.elipse(0, -22, 8.5, 6.5) & rosto, 1.0, 4)  # queixo grande
    p.sulco([(0, -22.3), (0, -25.6)], 1.0, 0.6, suave=False)  # covinha do queixo
    sobrancelha(p, [(-12, 8.2), (-8, 10.6), (-3, 9.3)], 2.4, (90, 60, 50))
    olho(p, -6.3, 3.5, 3.9, 4.4, (80, 140, 220), olhar=(0.1, -0.12))
    olho(p, 6.3, 3.5, 3.9, 4.4, (80, 140, 220), olhar=(-0.1, -0.12))
    p.relevo(p.elipse(0, -3, 2.2, 2.8), 1.2, 1.5)
    p.sulco([(-7, -9.4), (-3.5, -11.6), (0, -12), (3.5, -11.6), (7, -9.4)], 1.1, 0.8)
    p.sulco([(-7.6, -8.4), (-7.2, -10.4)], 0.8, 0.5, suave=False)
    p.sulco([(7.6, -8.4), (7.2, -10.4)], 0.8, 0.5, suave=False)
    p.furo(0, 24)
    return p


def jessie():
    p = Peca("jessie")
    VERMELHO = (205, 45, 45)
    CABELO = (200, 70, 40)
    AMARELO = (250, 205, 60)
    rosto = p.poligono(simetrica([(0, 12), (9, 11.5), (14, 6), (15, -4), (13, -13), (8.5, -20), (3.5, -23), (0, -23.5)]))
    cabelo = p.poligono(simetrica([(0, 14), (13, 13), (17.5, 6), (18, -3), (16, -9), (0, -9)]))
    gomos = [(17.6, -8.2), (18.8, -12.4), (19.9, -16.6), (20.9, -20.7)]
    tranca = np.zeros_like(rosto)
    for gx, gy in gomos:
        tranca |= p.elipse(gx, gy, 3.5, 2.7, ang=-15)
    laco = p.elipse(19.2, -25, 2.6, 1.8, ang=15) | p.elipse(24.2, -25, 2.6, 1.8, ang=-15) | p.circulo(21.7, -24.8, 1.4)
    ponta = p.poligono([(19.8, -26), (23.6, -26), (24.6, -29.2), (21.7, -30.6), (18.8, -29.2)])
    aba = p.poligono([(-31, 15), (-29, 18), (-24, 16.5), (-14, 15.5), (0, 15.3), (14, 15.5), (24, 16.5), (29, 18),
                      (31, 15), (26, 11.5), (15, 9.5), (0, 9), (-15, 9.5), (-26, 11.5)])
    copa = p.poligono(simetrica([(0, 29.2), (7, 29.8), (12, 27.2), (13.5, 21), (13, 15), (0, 15)]))
    for m in (rosto, cabelo, tranca, laco, ponta, aba, copa):
        p.contorno(m)
    p.iniciar()
    p.parte(cabelo, 1.8, 2, CABELO)
    p.parte(tranca | ponta, 2.0, 2, CABELO)
    for (ax, ay), (bx, by) in zip(gomos[:-1], gomos[1:]):
        mx, my = (ax + bx) / 2, (ay + by) / 2
        p.sulco([(mx - 3, my + 0.9), (mx, my - 0.3), (mx + 3, my - 1.1)], 0.7, 0.5)
    p.parte(laco, 2.4, 1.5, AMARELO)
    p.parte(rosto, 2.4, 9, PELE)
    franja = p.poligono([(-13, 11.5), (-10, 12), (10, 12), (13, 11.5), (11, 8), (8, 9.5), (5, 7.3), (2, 9.2),
                         (-1, 7.5), (-4, 9.3), (-7, 7.6), (-10, 9.4)])
    p.relevo(franja & rosto, 0.7, 0.6, CABELO)
    p.parte(aba, 3.6, 2.5, VERMELHO)
    p.parte(copa, 4.8, 6, VERMELHO)
    p.parte(copa & (p.Y > 16.3) & (p.Y < 19.0), 4.8, 6, BRANCO)
    p.sulco([(-13.2, 16.3), (13.2, 16.3)], 0.8, 0.5, suave=False)
    p.sulco([(-13.4, 19.0), (13.4, 19.0)], 0.8, 0.5, suave=False)
    sobrancelha(p, [(-9.5, 7.0), (-6, 8.0), (-3, 7.2)], 1.1, (170, 60, 35))
    olho(p, -6, 0, 4.4, 5.4, (70, 160, 90))
    olho(p, 6, 0, 4.4, 5.4, (70, 160, 90))
    for s in (1, -1):  # cílios
        p.relevo(p.traco([(s * 9.6, 3.2), (s * 11.4, 4.5)], 1.0, suave=False), 0.7, 0.4, PRETO)
        p.relevo(p.traco([(s * 10.3, 1.4), (s * 12.3, 2.0)], 1.0, suave=False), 0.7, 0.4, PRETO)
    p.relevo(p.elipse(0, -5.5, 1.6, 1.4), 0.9, 1.0)
    boca_aberta(p, [(-6.5, -10), (0, -9.6), (6.5, -10), (4.5, -14), (0, -15.8), (-4.5, -14)], -11.6, p.elipse(0, -14.6, 3, 1.6))
    p.furo(0, 23.5)
    return p


def rex():
    """De perfil (olhando para a esquerda): de frente ele parece um sapo; de lado é dinossauro na hora."""
    p = Peca("rex")
    VERDE = (125, 190, 85)
    VERDE_ESC = (80, 140, 60)
    cabeca = p.poligono([(6, 24), (15, 22.5), (20.5, 16), (21.5, 6), (20.5, -6), (19.5, -18), (19, -26),
                         (15, -30.3), (8.5, -30.3), (5.2, -26), (5, -21), (1, -14), (-8, -11), (-20, -8.5), (-27, -5), (-29.5, -1),
                         (-31, 3), (-30, 8), (-24, 11), (-13, 13.5), (-4, 19)])
    espinhos = p.circulo(17, 20.5, 3.4) | p.circulo(20.8, 11, 3.4) | p.circulo(21.2, 0.5, 3.4) | p.circulo(20.6, -10, 3.4)
    braco = p.elipse(1.5, -22.5, 5, 2.7, ang=20)
    for m in (cabeca, espinhos, braco):
        p.contorno(m)
    p.iniciar()
    p.parte(espinhos, 2.0, 2, VERDE_ESC)
    p.parte(braco, 1.8, 1.5, VERDE)
    p.parte(cabeca, 2.6, 10, VERDE)
    p.relevo(p.elipse(-14, 6, 13, 6.5, ang=-8), 0.8, 5)  # focinho
    p.relevo(p.traco([(-4, 19.5), (2.5, 21.2), (9.5, 19)], 2.4), 0.9, 0.8, VERDE_ESC)  # sobrancelha óssea
    p.rebaixo(p.elipse(-25.5, 7.5, 1.7, 1.1, ang=-20), 0.8, 0.4, VERDE_ESC)  # narina
    olho(p, 3, 12.5, 5.0, 5.5, (150, 110, 40), olhar=(-0.2, -0.1))
    boca = p.rebaixo(p.poligono([(-28, -0.5), (-16, -1.8), (-6, -1.5), (2, 1.5), (-2, -4.5), (-12, -7.5), (-23, -5.5)]),
                     1.6, 0.6, BOCA)
    for x in (-24, -19, -14, -9, -4):
        topo = -1.5 + 0.004 * (x + 6) ** 2 * (-1) - 0.2
        dente = p.poligono([(x - 2.0, topo + 1.2), (x + 2.0, topo + 1.2), (x, topo - 3.0)], suave=False)
        p.relevo(dente & boca, 1.3, 0.4, BRANCO)
    p.relevo(p.elipse(-10, -5.6, 6, 1.8, ang=-12) & boca, 0.6, 0.8, LINGUA)
    p.sulco([(19, -12), (11, -14), (6, -12)], 0.8, 0.5)  # dobra do pescoço
    p.furo(12.5, 17)
    return p


def alien():
    p = Peca("alien")
    VERDE = (140, 220, 90)
    cabeca = p.poligono(simetrica([(0, 15), (9, 14.5), (16, 10), (19.5, 2), (19, -7), (15.5, -14), (9, -18.5), (0, -20)]))
    orelhas = np.zeros_like(cabeca)
    for s in (1, -1):
        orelhas |= p.poligono([(s * 18, -5), (s * 24, -1), (s * 29, 6), (s * 29.5, 9), (s * 27, 9.5), (s * 22, 7), (s * 18, 5)])
    haste = p.traco([(0, 13), (0, 23)], 4.6, suave=False)
    bola = p.circulo(0, 25.5, 4.2)
    for m in (cabeca, orelhas, haste, bola):
        p.contorno(m)
    p.iniciar()
    p.parte(orelhas, 1.8, 3, VERDE)
    p.parte(haste, 1.6, 1.5, VERDE)
    p.parte(bola, 2.8, 3.5, VERDE)
    p.parte(cabeca, 2.6, 10, VERDE)
    for s in (1, -1):
        p.sulco([(s * 20, 0), (s * 24, 3), (s * 27.5, 7.5)], 0.8, 0.5)
    for cx, cy in ((-9, 0.5), (0, 2.5), (9, 0.5)):
        olho(p, cx, cy, 4.1, 5.0, (70, 55, 45))
    boca_aberta(p, [(-4, -10), (0, -9.7), (4, -10), (2.5, -12.8), (0, -13.5), (-2.5, -12.8)], -10.9)
    p.furo(0, 10.5)
    return p


def batata():
    p = Peca("batata")
    BATATA = (210, 165, 105)
    ROSA = (240, 150, 150)
    corpo = p.poligono(simetrica([(0, 21), (9, 20.5), (16, 15), (19.5, 5), (20, -6), (18, -17), (12, -26), (5, -29.5), (0, -30)]))
    orelhas = p.elipse(-21.5, 1, 5.5, 7.5, ang=-10) | p.elipse(21.5, 1, 5.5, 7.5, ang=10)
    copa = p.poligono(simetrica([(0, 31), (6, 30.6), (10, 27.5), (11, 22), (10.5, 19), (0, 19)]))
    aba = p.poligono([(-16.5, 21.5), (-12, 20.5), (0, 20.8), (12, 20.5), (16.5, 21.5), (15, 18), (0, 16.8), (-15, 18)])
    for m in (corpo, orelhas, copa, aba):
        p.contorno(m)
    p.iniciar()
    p.parte(orelhas, 2.0, 3, ROSA)
    for s in (1, -1):
        p.sulco([(s * 20, 5), (s * 23, 4), (s * 23.5, -1), (s * 21, -3.5)], 0.8, 0.5)
    p.parte(corpo, 2.6, 10, BATATA)
    p.parte(aba, 3.8, 2, (55, 55, 60))
    p.parte(copa, 4.6, 6, (55, 55, 60))
    sobrancelha(p, [(-12.5, 15.3), (-8, 17), (-2.5, 15)], 2.6, PRETO)
    for s in (1, -1):
        olho(p, s * 6.8, 8, 5.2, 6.0, (110, 80, 50))
        p.relevo(p.elipse(s * 6.8, 8, 5.2, 6.0) & (p.Y > 10.5), 0.6, 0.5, BATATA)  # pálpebra
    p.relevo(p.elipse(0, 0, 5.5, 4.3), 2.0, 3.5, ROSA)  # nariz
    bigode = np.zeros_like(corpo)
    for x in (-10, -6, -2, 2, 6, 10):
        bigode |= p.circulo(x, -6.3 + 0.012 * x * x, 2.9)
    p.relevo(bigode, 1.4, 1.5, PRETO)
    p.relevo(p.elipse(0, -14.5, 8, 5), 0.8, 1.0, (210, 60, 70))  # lábios
    boca_aberta(p, [(-5.8, -13), (0, -11.8), (5.8, -13), (4, -16.5), (0, -17.6), (-4, -16.5)], -13.6)
    p.furo(0, 25.5)
    return p


PERSONAGENS = {"woody": woody, "buzz": buzz, "jessie": jessie, "rex": rex, "alien": alien, "batata": batata}


def main():
    pasta = os.path.dirname(os.path.abspath(__file__))
    nomes = sys.argv[1:] or list(PERSONAGENS)
    previas = []
    for nome in nomes:
        p = PERSONAGENS[nome]().finalizar()
        tm = p.malha()
        tm.export(os.path.join(pasta, f"{nome}.stl"))
        e = tm.extents
        print(f"{nome}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm | {len(tm.faces)} triângulos | "
              f"fechada={tm.is_watertight} | gesso ~{tm.volume / 1000 * 1.2:.0f} g")
        crua, pintada = p.previa(), p.previa(pintada=True)
        img = Image.fromarray(np.hstack([crua, pintada]))
        img.save(os.path.join(pasta, f"{nome}.png"))
        previas.append((nome, img))
    if len(previas) == len(PERSONAGENS):
        w, h = previas[0][1].size
        folha = Image.new("RGB", (w * 2, (h + 40) * 3), "white")
        d = ImageDraw.Draw(folha)
        for i, (nome, img) in enumerate(previas):
            x, y = (i % 2) * w, (i // 2) * (h + 40)
            folha.paste(img, (x, y + 30))
            d.text((x + 12, y + 8), nome.upper(), fill=(40, 40, 40))
        folha.save(os.path.join(pasta, "colecao.png"))


if __name__ == "__main__":
    main()
