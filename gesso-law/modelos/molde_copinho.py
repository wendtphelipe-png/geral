"""Molde COPINHO (tamanho M): um contramolde pequeno por peça + uma tampa universal.

Substitui moldura + base + miolo grande. Cada peça ganha um "copinho" que segue o contorno dela
(só ~10 mm de parede em volta) e cuja altura acompanha a espessura da peça (o Floco sai baixinho).
O copinho já recebe o silicone direto: tem parede contra vazamento e dois pinos de centragem.

  copinho_<peca>.stl   imprime com o fundo plano na mesa e a cavidade para cima: sem suporte.
  tampa_M.stl          universal (serve em todos os copinhos M): placa de 3 mm com o encaixe em D
                       da peça no centro, 2 furos para os pinos do copinho e respiros.

Como usar (por peça):
  1. Desmoldante no copinho, na tampa e na peça de resina.
  2. Encaixar a peça de resina na tampa pelo pino em D (a peça fica pendurada, de frente para baixo).
  3. Despejar no copinho o volume de silicone indicado (sai na tela e no arquivo LEIA.txt).
  4. Descer a tampa com a peça pelos 2 pinos até a tampa encostar no copinho. O excesso sai pelos respiros.
  5. Peso em cima até curar. O silicone sai com uma aba fina em volta, que volta para o copinho na hora do gesso.

Uso:
  python molde_copinho.py tampa saida
  python molde_copinho.py copinhos pasta_pecas saida "NATAL 2026" peca1:Nome peca2:Nome ...
     (peças finais, com pino, centradas no retângulo, costas em z = 0 e frente para +z)
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold
from scipy import ndimage
from skimage.measure import marching_cubes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finalizar_lote import PINO_CORTE, PINO_RAIO, para_trimesh  # noqa: E402

PECA_L, PECA_A, PECA_E = 64.0, 82.0, 35.0     # limites do tamanho M (sem o pino)
SIL = 3.9        # espessura do silicone (3,5 mm + 0,4 que o arredondamento da malha come)
ABA = 4.0        # aba do silicone além da peça (ajuda a recolocar o silicone no copinho)
ABA_ESP = 3.0    # espessura dessa aba
PAREDE = 2.5     # parede do copinho em volta da aba
FUNDO = 2.0      # fundo mínimo do copinho
PINO_X = 46.0    # pinos de centragem em (±PINO_X, PINO_Y): fora de qualquer peça M
PINO_Y = 8.0     # os dois deslocados para o mesmo lado: a tampa só encaixa de um jeito
PINO_R, PINO_H = 2.5, 2.5
TAMPA_X, TAMPA_Y, TAMPA_ESP = 104.0, 106.0, 3.0
FOLGA_PINO = 0.25
FOLGA_D = 0.2
DX = 0.5


def texto(t, altura):
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), t, size=altura, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    return [np.asarray(p) for p in tp.to_polygons() if len(p) > 2]


def tampa(sai):
    os.makedirs(sai, exist_ok=True)
    t = Manifold.cube((TAMPA_X, TAMPA_Y, TAMPA_ESP)).translate((-TAMPA_X / 2, -TAMPA_Y / 2, -TAMPA_ESP))
    d = CrossSection.circle(PINO_RAIO + FOLGA_D, 96) - CrossSection.square((14, 14)).translate((-7, PINO_CORTE + FOLGA_D))
    t = t - Manifold.extrude(d, TAMPA_ESP + 2).translate((0, 0, -TAMPA_ESP - 1))
    for sx in (-1, 1):
        t = t - Manifold.cylinder(TAMPA_ESP + 2, PINO_R + FOLGA_PINO, PINO_R + FOLGA_PINO, 48).translate((sx * PINO_X, PINO_Y, -TAMPA_ESP - 1))
    n = 0
    for gx in np.arange(-TAMPA_X / 2 + 6, TAMPA_X / 2 - 5, 7.0):
        for gy in np.arange(-TAMPA_Y / 2 + 6, TAMPA_Y / 2 - 5, 7.0):
            if gx ** 2 + gy ** 2 < 10 ** 2 or any((gx - sx * PINO_X) ** 2 + (gy - PINO_Y) ** 2 < 6 ** 2 for sx in (-1, 1)):
                continue
            t = t - Manifold.cylinder(TAMPA_ESP + 2, 1.5, 1.5, 16).translate((gx, gy, -TAMPA_ESP - 1))
            n += 1
    m = para_trimesh(t)
    m.apply_translation([0, 0, TAMPA_ESP])            # para imprimir: deitada na mesa
    m.export(os.path.join(sai, "tampa_M.stl"))
    print(f"tampa_M: {TAMPA_X:.0f} x {TAMPA_Y:.0f} x {TAMPA_ESP:.0f} mm, {n} respiros, fechada={m.is_watertight}, "
          f"~{m.volume / 1000 * 1.05:.0f} g")


def copinho(peca, rotulo, colecao, sai):
    from relevo3d import _camadas, _ocupacao
    b = peca.bounds
    e = b[1] - b[0]
    if e[0] > PECA_L + 0.5 or e[1] > PECA_A + 0.5 or b[1, 2] > PECA_E + 0.5:
        print(f"  ATENÇÃO: {rotulo} passa do tamanho M ({e[0]:.1f} x {e[1]:.1f} x {b[1, 2]:.1f})")
    R = SIL + ABA + PAREDE
    x0, y0 = -(PINO_X + PINO_R + 3), -(PECA_A / 2 + R + 2)
    nx, ny = int(-2 * x0 / DX), int(-2 * y0 / DX)
    H = b[1, 2] + SIL + FUNDO
    zs = np.arange(-PINO_H - 1, H + 1.5, DX)
    X = x0 + (np.arange(nx) + 0.5) * DX
    Y = y0 + (np.arange(ny) + 0.5) * DX
    Zg = zs[None, None, :]
    z, sen, cont = _camadas(peca.vertices[peca.faces].astype(np.float64), x0, y0, DX, nx, ny)
    occ = _ocupacao(z, sen, cont, zs, DX) > 0.5
    occ[:, :, zs < 0] = False
    contorno = occ.any(axis=2)
    d2 = ndimage.distance_transform_edt(~contorno) * DX
    dist = ndimage.distance_transform_edt(~occ) * DX
    env = ((dist <= SIL) | ((d2 <= SIL + ABA)[:, :, None] & (Zg <= ABA_ESP))) & (Zg >= 0)
    Xg, Yg = np.meshgrid(X, Y)
    pe = d2 <= R
    # "orelhas" que levam os 2 pinos de centragem (faixa horizontal até os pinos)
    pe |= (np.abs(Yg - PINO_Y) <= PINO_R + 3) & (np.abs(Xg) <= PINO_X + PINO_R + 3)
    corpo = pe[:, :, None] & (Zg >= 0) & (Zg <= H) & ~env
    for sx in (-1, 1):
        cil = (((Xg - sx * PINO_X) ** 2 + (Yg - PINO_Y) ** 2) <= PINO_R ** 2)[:, :, None] & (Zg < 0) & (Zg >= -PINO_H)
        corpo |= cil
    # nome gravado no fundo (0,6 mm), legível olhando o fundo
    from matplotlib.path import Path as MPath
    pts = np.column_stack([Xg.ravel(), Yg.ravel()])
    for linha, dy in ((colecao, 7), (rotulo, -7)):
        pol = texto(linha, 6)
        if not pol:
            continue
        allp = np.vstack(pol)
        lo, hi = allp.min(0), allp.max(0)
        esc = min(1.0, (2 * PINO_X - 30) / (hi[0] - lo[0]))
        msk = np.zeros(len(pts), bool)
        for p in pol:
            q = (p - (lo + hi) / 2) * esc + [0, dy]
            msk ^= MPath(q).contains_points(pts)
        msk = msk.reshape(Xg.shape) & (d2 <= R - 2.0)
        corpo &= ~(msk[:, :, None] & (Zg > H - 0.6))
    silicone = (env & ~occ).sum() * DX ** 3 / 1000

    f = ndimage.gaussian_filter(np.pad(corpo, 2).astype(np.float32), 0.55)
    v, fa, _, _ = marching_cubes(f, 0.5, spacing=(DX, DX, DX))
    v = v - 2 * DX
    verts = np.column_stack([x0 + v[:, 1] + DX / 2, y0 + v[:, 0] + DX / 2, zs[0] + v[:, 2]])
    import fast_simplification
    for red in (0.7, 0.5, 0.0):
        if red:
            vv, ff = fast_simplification.simplify(verts.astype(np.float32), fa[:, ::-1], target_reduction=red)
        else:
            vv, ff = verts, fa[:, ::-1]
        tm = trimesh.Trimesh(vv, ff, process=False)
        if tm.is_watertight:
            break
    if tm.volume < 0:
        tm.invert()
    # posição de impressão: fundo na mesa, cavidade e pinos para cima
    tm.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    tm.apply_translation([0, 0, -tm.bounds[0, 2]])
    return tm, silicone, H


def copinhos(pasta, sai, colecao, args):
    os.makedirs(sai, exist_ok=True)
    linhas = []
    for a in args:
        n, rot = a.split(":")
        peca = trimesh.load(os.path.join(pasta, n + ".stl"))
        tm, sil, H = copinho(peca, rot.upper(), colecao, sai)
        tm.export(os.path.join(sai, f"copinho_{n}.stl"))
        e = tm.extents
        txt = (f"{rot}: copinho {e[0]:.0f} x {e[1]:.0f} x {e[2]:.0f} mm | silicone ~{sil * 1.1:.0f} ml "
               f"(já com 10% de sobra) | fechado={tm.is_watertight}")
        print(txt)
        linhas.append(txt)
    with open(os.path.join(sai, "LEIA.txt"), "w") as f:
        f.write("Copinhos " + colecao + "\n" + "\n".join(linhas) + "\n")


if __name__ == "__main__":
    if sys.argv[1] == "tampa":
        tampa(sys.argv[2])
    else:
        copinhos(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5:])
