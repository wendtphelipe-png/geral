"""Peças de Natal desenhadas do zero (formas próprias), no estilo arredondado da coleção.

Gera <nome>_fig.stl (frente para +z, altura ~56 mm) para passar depois pelo relevo3d.py.
Uso: python desenhos_proprios.py pasta_saida [meia presente bengala guirlanda sino treno]
"""
import os
import sys

import numpy as np
import trimesh
from skimage.measure import marching_cubes

DX = 0.3
L = 33.0
xs = np.arange(-L, L, DX, dtype=np.float32)
zs_ = np.arange(-14, 16, DX, dtype=np.float32)
X, Y, Z = np.meshgrid(xs, xs, zs_, indexing="ij")


# ---------- primitivas (distância com sinal, mm) ----------
def smin(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)


def esfera(c, r):
    return np.sqrt((X - c[0]) ** 2 + (Y - c[1]) ** 2 + (Z - c[2]) ** 2) - r


def elipsoide(c, r):
    k0 = np.sqrt(((X - c[0]) / r[0]) ** 2 + ((Y - c[1]) / r[1]) ** 2 + ((Z - c[2]) / r[2]) ** 2)
    return (k0 - 1) * min(r)


def caixa(c, meia, raio=0.0):
    q = np.stack([np.abs(X - c[0]) - meia[0] + raio, np.abs(Y - c[1]) - meia[1] + raio,
                  np.abs(Z - c[2]) - meia[2] + raio])
    fora = np.sqrt(np.sum(np.maximum(q, 0) ** 2, axis=0))
    dentro = np.minimum(np.max(q, axis=0), 0)
    return fora + dentro - raio


def tubo(p, q, r):
    p = np.asarray(p, np.float32); q = np.asarray(q, np.float32)
    v = q - p
    if float(v @ v) < 1e-9:
        return esfera(p, r)
    t = np.clip(((X - p[0]) * v[0] + (Y - p[1]) * v[1] + (Z - p[2]) * v[2]) / float(v @ v), 0, 1)
    return np.sqrt((X - p[0] - t * v[0]) ** 2 + (Y - p[1] - t * v[1]) ** 2 + (Z - p[2] - t * v[2]) ** 2) - r


def caminho(pts, r):
    d = tubo(pts[0], pts[1], r)
    for a, b in zip(pts[1:-1], pts[2:]):
        d = np.minimum(d, tubo(a, b, r))
    return d


def arco(c, raio, a0, a1, z=0.0, n=24):
    t = np.linspace(np.radians(a0), np.radians(a1), n)
    return [(c[0] + raio * np.cos(a), c[1] + raio * np.sin(a), z) for a in t]


def laco(c, larg, alt, prof=4.0):
    """Laço de presente: duas alças gordinhas, nó redondo e duas pontas."""
    cx, cy, cz = c
    d = esfera(c, alt * 0.32)
    for s in (1, -1):
        alca = elipsoide((cx + s * larg * 0.5, cy + alt * 0.12, cz), (larg * 0.48, alt * 0.42, prof))
        furo = elipsoide((cx + s * larg * 0.55, cy + alt * 0.14, cz + prof * 0.7), (larg * 0.22, alt * 0.18, prof))
        alca = smax(alca, -furo, 0.8)
        d = smin(d, alca, 1.2)
        ponta = tubo((cx + s * 1.0, cy - 1.0, cz), (cx + s * larg * 0.45, cy - alt * 0.75, cz), alt * 0.17)
        d = smin(d, ponta, 1.0)
    return d


def sulcos(d, campo, passo, largura=0.8, prof=0.7):
    """Sulcos rasos na superfície para separar faixas de pintura (ex.: listras da bengala)."""
    g = np.abs(((campo / passo) + 0.5) % 1.0 - 0.5) * passo - largura / 2
    corte = np.maximum(g, -(d + prof))
    return np.maximum(d, -corte)


# ---------- peças ----------
def meia():
    cano = caixa((2, 4, 0), (10.5, 15, 7.5), 6.5)
    pe = elipsoide((-6, -16, 0), (15.5, 9.5, 7.8))
    d = smin(cano, pe, 4.0)
    punho = caixa((2.5, 21, 0.3), (13.5, 6.2, 9.0), 4.5)
    d = smin(d, punho, 0.8)
    # bolinhas no punho, como pelúcia
    for x in np.linspace(-8, 13, 6):
        d = smin(d, esfera((x, 21 + 2.5 * np.sin(x), 8.2), 1.6), 0.6)
    # calcanhar e bico em relevo para pintar de outra cor
    calc = smax(elipsoide((10.5, -15, 0), (8, 8, 8.4)), cano - 1, 0.5)
    bico = smax(elipsoide((-17, -17, 0), (9, 9, 8.4)), pe - 0.0001 + 0.6, 0.5)
    d = smin(d, calc, 0.4)
    d = smin(d, bico, 0.4)
    # estrela de 5 pontas em relevo no cano
    ang = np.arctan2(Y - 1, X - 2) + np.pi / 2
    raio = np.hypot(X - 2, Y - 1)
    estrela2d = raio - (4.2 + 2.4 * np.cos(5 * ang)) / 1.0
    d = smin(d, np.maximum(estrela2d, np.abs(Z - 7.3) - 1.2), 0.5)
    return d


def presente():
    caixa_ = caixa((0, -6, 0), (19, 15, 11), 3.5)
    tampa = caixa((0, 10, 0), (21, 4.5, 12.2), 2.5)
    d = smin(caixa_, tampa, 0.6)
    fita_v = caixa((0, -2, 0), (3.6, 17, 12.6), 1.2)
    fita_h = caixa((0, -7, 0), (19.6, 3.4, 11.7), 1.2)
    d = smin(d, smin(fita_v, fita_h, 0.4), 0.4)
    d = smin(d, laco((0, 20, 2), 22, 14, 5.0), 1.0)
    return d


def bengala():
    pts = [(7, -28, 0), (7, 6, 0)] + arco((-2, 6), 9, 0, 180) + [(-11, 1, 0)]
    d = caminho(pts, 4.6)
    d = smin(d, esfera((-11, 1, 0), 4.6), 0.1)
    # listras diagonais no cabo e radiais na curva
    cabo = (Y < 6.5)
    d_cabo = sulcos(d, (Y - 0.7 * X) / 1.22, 6.0)
    ang = np.degrees(np.arctan2(Y - 6, X + 2))
    d_curva = sulcos(d, ang / 180 * np.pi * 9, 6.0)
    d = np.where(cabo, d_cabo, d_curva)
    d = smin(d, laco((7, -8, 4), 16, 11, 4.0), 1.0)
    return d


def guirlanda():
    rng = np.random.default_rng(7)
    d = np.sqrt((np.hypot(X, Y) - 17.5) ** 2 + (Z / 1.0) ** 2) - 6.0
    for i in range(26):                                   # folhas gordinhas em volta do aro
        a = i / 26 * 2 * np.pi + rng.uniform(-0.1, 0.1)
        rr = 17.5 + rng.uniform(-4.5, 4.5)
        cx, cy = rr * np.cos(a), rr * np.sin(a)
        d = smin(d, elipsoide((cx, cy, rng.uniform(3, 5.5)), (4.2, 2.6, 2.6)), 1.4)
    for a in (40, 70, 140, 200, 230, 320, 350):          # trios de frutinhas
        for k, (ox, oy) in enumerate(((0, 0), (2.4, 1.2), (0.6, 2.6))):
            ar = np.radians(a)
            d = smin(d, esfera((19 * np.cos(ar) + ox, 19 * np.sin(ar) + oy, 6.3), 1.7), 0.5)
    d = smin(d, laco((0, -21, 4), 20, 13, 5.0), 1.2)
    return d


def sino():
    rho = np.hypot(X, Z * 1.7)
    y = Y + 4
    # perfil do sino: cúpula redonda que se abre numa saia
    raio_perfil = np.where(y > 10, np.sqrt(np.maximum(0, 13 ** 2 - (y - 10) ** 2)),
                           13 + 0.0115 * np.maximum(10 - y, 0) ** 2.0)
    d = smax(rho - raio_perfil, np.maximum(y - 23, -12 - y), 2.0)
    d = smin(d, np.sqrt((np.hypot(X, Z * 1.7) - 17.8) ** 2 + (y + 12.0) ** 2) - 3.0, 1.5)  # borda
    d = smin(d, elipsoide((0, -16.2, 0), (17.5, 3.2, 10)), 1.5)                          # fundo fechado
    d = smin(d, esfera((0, -18.5, 0), 4.2), 1.0)          # badalo
    d = smin(d, laco((0, 21, 5), 22, 13, 5.0), 1.0)
    for s in (1, -1):                                      # azevinho: duas folhas e frutinhas
        d = smin(d, elipsoide((s * 8, 15, 9.5), (6.5, 3.0, 2.2)), 1.0)
    for ox, oy in ((-1.6, 13.5), (1.6, 13.5), (0, 16)):
        d = smin(d, esfera((ox, oy, 11), 1.9), 0.5)
    return d


def treno():
    # caixa do trenó, com frente enrolada para cima
    corpo = caixa((2, -2, 0), (19, 7.5, 9), 3.5)
    frente = np.sqrt((np.hypot(X + 17, Y - 4) - 6.5) ** 2 + Z ** 2 / 2.0) - 4.0
    frente = np.maximum(frente, -(X + 17))                 # só a metade da frente
    d = smin(corpo, frente, 2.0)
    encosto = caixa((17, 6, 0), (4, 9, 9), 3.0)
    d = smin(d, encosto, 1.5)
    # patins: tubo grosso com a ponta enrolada, ligado ao corpo por duas hastes
    patim = [(20, -16, 0), (-14, -16, 0)] + arco((-14, -10), 6, 270, 120)
    d = smin(d, caminho(patim, 2.6), 0.5)
    for x in (-6, 12):
        d = smin(d, tubo((x, -15, 0), (x, -8, 0), 2.4), 1.2)
    # presentes em cima
    d = smin(d, caixa((-4, 11, 0), (7, 6, 7), 2.0), 0.8)
    d = smin(d, caixa((-4, 11, 0), (1.6, 6.3, 7.4), 0.6), 0.3)
    d = smin(d, caixa((8, 9, 0), (5, 4.5, 6), 1.8), 0.8)
    d = smin(d, laco((-4, 19.5, 2), 11, 7, 3.0), 0.8)
    return d


PECAS = {"meia": meia, "presente": presente, "bengala": bengala, "guirlanda": guirlanda,
         "sino": sino, "treno": treno}


def main():
    saida = sys.argv[1]
    nomes = sys.argv[2:] or list(PECAS)
    os.makedirs(saida, exist_ok=True)
    for n in nomes:
        d = PECAS[n]().astype(np.float32)
        v, f, _, _ = marching_cubes(d, 0.0, spacing=(DX, DX, DX))
        v = v + np.array([xs[0], xs[0], zs_[0]])
        m = trimesh.Trimesh(v, f[:, ::-1], process=False)
        trimesh.smoothing.filter_taubin(m, iterations=6)
        if m.volume < 0:
            m.invert()
        m.export(os.path.join(saida, n + "_fig.stl"))
        print(n, np.round(m.extents, 1), m.is_watertight)


if __name__ == "__main__":
    main()
