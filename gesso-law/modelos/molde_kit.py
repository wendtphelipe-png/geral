"""Molde KIT M (6 peças): uma BANDEJA por kit + uma TAMPA universal.

Substitui moldura + base + miolo do molde padrão M, gastando bem menos filamento e sem suporte:
  - a bandeja segue o contorno de cada peça (parede de ~10 mm em volta), em vez de blocos retangulares;
  - a altura é só a que a peça mais grossa do kit precisa;
  - nada fica no ar: imprime com o fundo plano na mesa e as cavidades para cima, sem suporte;
  - o silicone vai direto nas cavidades (cada peça fica com a sua "pele" de silicone).

  bandeja.stl   uma por kit. Nome da coleção e das peças gravados no fundo.
  tampa_kit_M.stl  universal (impressa uma vez): placa de 2,5 mm com os 6 encaixes em D das peças,
                   os furos dos 2 pinos da bandeja, respiros e os números 1 a 6.

Como usar:
  1. Desmoldante na bandeja, na tampa e nas peças de resina.
  2. Encaixar as 6 peças de resina na tampa pelos pinos em D, conferindo os números (ficam penduradas,
     de frente para baixo). O número de cada vaga está gravado no fundo da bandeja, junto do nome.
  3. Despejar em cada cavidade o volume de silicone indicado em LEIA.txt.
  4. Descer a tampa pelos 2 pinos até encostar na bandeja. Ela só entra de um jeito.
     O excesso sai pelos respiros. Peso em cima até curar.

Uso:
  python molde_kit.py tampa saida
  python molde_kit.py bandeja pasta_pecas saida "NATAL 2026" "PARTE 1 de 2" p1:Nome ... p6:Nome
     (peças finais com pino, centradas no retângulo, costas em z = 0; vagas 1 a 3 em cima, 4 a 6 embaixo)
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, Manifold
from scipy import ndimage
from skimage.measure import marching_cubes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finalizar_lote import PINO_CORTE, PINO_RAIO, para_trimesh  # noqa: E402

PECA_L, PECA_A, PECA_E = 64.0, 82.0, 35.0     # limites do tamanho M (sem o pino)
SIL = 3.9        # silicone: 3,5 mm + 0,4 que o arredondamento da malha come
ABA = 4.0        # aba do silicone além do contorno da peça
ABA_ESP = 3.0    # espessura da aba
PAREDE = 2.5     # parede da bandeja em volta da aba
FUNDO = 2.0      # fundo mínimo sob a peça mais grossa
SX, SY = 85.0, 103.0            # distância entre os centros das vagas
BARRA = 5.0                     # barras que ligam as cavidades (largura)
PINOS = [(SX, 106.0), (0.0, 106.0)]   # assimétricos: a tampa só encaixa de um jeito
PINO_R, PINO_H = 2.5, 2.5
TAMPA_ESP = 2.5
FOLGA_PINO, FOLGA_D = 0.25, 0.2
DX = 0.5

R = SIL + ABA + PAREDE
XMAX = SX + PECA_L / 2 + R
YMIN, YMAX = -(SY / 2 + PECA_A / 2 + R), PINOS[0][1] + PINO_R + 3


def centros():
    return [(c * SX, r * SY / 2) for r in (1, -1) for c in (-1, 0, 1)]


def texto_pol(t, altura):
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), t, size=altura, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    pol = [np.asarray(p) for p in tp.to_polygons() if len(p) > 2]
    allp = np.vstack(pol)
    c = (allp.min(0) + allp.max(0)) / 2
    return [p - c for p in pol], allp.max(0) - allp.min(0)


def tampa(sai):
    os.makedirs(sai, exist_ok=True)
    x0, x1 = -XMAX, XMAX
    t = Manifold.cube((x1 - x0, YMAX - YMIN, TAMPA_ESP)).translate((x0, YMIN, -TAMPA_ESP))
    d = CrossSection.circle(PINO_RAIO + FOLGA_D, 96) - CrossSection.square((14, 14)).translate((-7, PINO_CORTE + FOLGA_D))
    for k, (cx, cy) in enumerate(centros(), 1):
        t = t - Manifold.extrude(d, TAMPA_ESP + 2).translate((cx, cy, -TAMPA_ESP - 1))
        # número da vaga, gravado na face de cima (quando a tampa está em uso), legível de cima
        pol, tam = texto_pol(str(k), 9)
        # em uso a tampa fica virada (giro em x): o texto é espelhado em y para ler certo de cima
        cs = CrossSection([(np.column_stack([p[:, 0], -p[:, 1]]) + [cx + 13, cy]).tolist() for p in pol],
                          fillrule=FillRule.EvenOdd)
        t = t - Manifold.extrude(cs, 0.8).translate((0, 0, -TAMPA_ESP - 0.01))
    for px, py in PINOS:
        t = t - Manifold.cylinder(TAMPA_ESP + 2, PINO_R + FOLGA_PINO, PINO_R + FOLGA_PINO, 48).translate((px, py, -TAMPA_ESP - 1))
    n = 0
    for gx in np.arange(x0 + 6, x1 - 5, 7.0):
        for gy in np.arange(YMIN + 6, YMAX - 5, 7.0):
            if any((gx - cx) ** 2 + (gy - cy) ** 2 < 10 ** 2 or (abs(gx - cx - 13) < 6 and abs(gy - cy) < 7)
                   for cx, cy in centros()):
                continue
            if any((gx - px) ** 2 + (gy - py) ** 2 < 6 ** 2 for px, py in PINOS):
                continue
            t = t - Manifold.cylinder(TAMPA_ESP + 2, 1.5, 1.5, 16).translate((gx, gy, -TAMPA_ESP - 1))
            n += 1
    m = para_trimesh(t)
    m.apply_translation([0, 0, TAMPA_ESP])
    m.export(os.path.join(sai, "tampa_kit_M.stl"))
    e = m.extents
    print(f"tampa_kit_M: {e[0]:.0f} x {e[1]:.0f} x {e[2]:.1f} mm, {n} respiros, fechada={m.is_watertight}")


def bandeja(pasta, sai, colecao, parte, args):
    from relevo3d import _camadas, _ocupacao
    os.makedirs(sai, exist_ok=True)
    nomes = [a.split(":")[0] for a in args]
    rot = [a.split(":")[1].upper() for a in args]
    pecas = []
    for n, (cx, cy) in zip(nomes, centros()):
        p = trimesh.load(os.path.join(pasta, n + ".stl"))
        b = p.bounds
        e = b[1] - b[0]
        if e[0] > PECA_L + 0.5 or e[1] > PECA_A + 0.5 or b[1, 2] > PECA_E + 0.5:
            print(f"  ATENÇÃO: {n} passa do tamanho M ({e[0]:.1f} x {e[1]:.1f} x {b[1, 2]:.1f})")
        p = p.copy()
        p.apply_translation([cx, cy, 0])
        pecas.append(p)
    H = max(p.bounds[1, 2] for p in pecas) + SIL + FUNDO
    x0, y0 = -XMAX - 2, YMIN - 2
    nx, ny = int((2 * XMAX + 4) / DX), int((YMAX - YMIN + 4) / DX)
    zs = np.arange(-PINO_H - 1, H + 1.5, DX)
    X = x0 + (np.arange(nx) + 0.5) * DX
    Y = y0 + (np.arange(ny) + 0.5) * DX
    Zg = zs[None, None, :]
    Xg, Yg = np.meshgrid(X, Y)
    occ = np.zeros((ny, nx, len(zs)), bool)
    vols = []
    for p in pecas:
        z, sen, cont = _camadas(p.vertices[p.faces].astype(np.float64), x0, y0, DX, nx, ny)
        o = _ocupacao(z, sen, cont, zs, DX) > 0.5
        o[:, :, zs < 0] = False
        occ |= o
    contorno = occ.any(axis=2)
    d2 = ndimage.distance_transform_edt(~contorno) * DX
    dist = ndimage.distance_transform_edt(~occ) * DX
    env = ((dist <= SIL) | ((d2 <= SIL + ABA)[:, :, None] & (Zg <= ABA_ESP))) & (Zg >= 0)
    del dist
    pe = d2 <= R
    # barras que ligam as 6 cavidades e levam os pinos (de fora a fora)
    for _, cy in centros()[::3]:
        pe |= (np.abs(Yg - cy) <= BARRA / 2) & (np.abs(Xg) <= SX)
    for cx in (-SX, 0, SX):
        pe |= (np.abs(Xg - cx) <= BARRA / 2) & (Yg >= -SY / 2) & (Yg <= YMAX)
    for px, py in PINOS:
        pe |= ((Xg - px) ** 2 + (Yg - py) ** 2) <= (PINO_R + 3) ** 2
    corpo = pe[:, :, None] & (Zg >= 0) & (Zg <= H) & ~env
    for px, py in PINOS:
        corpo |= ((((Xg - px) ** 2 + (Yg - py) ** 2) <= PINO_R ** 2)[:, :, None] & (Zg < 0) & (Zg >= -PINO_H))
    # textos gravados no fundo (0,6 mm), legíveis olhando o fundo
    from matplotlib.path import Path as MPath
    pts = np.column_stack([Xg.ravel(), Yg.ravel()])

    def gravar(t, alt, cx, cy, larg):
        pol, tam = texto_pol(t, alt)
        esc = min(1.0, larg / tam[0])
        msk = np.zeros(len(pts), bool)
        for q in pol:
            msk ^= MPath(q * esc + [cx, cy]).contains_points(pts)
        return msk.reshape(Xg.shape)

    gr = np.zeros_like(contorno)
    for k, ((cx, cy), r) in enumerate(zip(centros(), rot), 1):
        gr |= gravar(f"{k} {r}", 5.5, cx, cy + 4, 50)
        gr |= gravar(f"{colecao} {parte}", 4, cx, cy - 5, 46)
    corpo &= ~((gr & pe)[:, :, None] & (Zg > H - 0.6))
    for k, p in enumerate(pecas):
        cx, cy = centros()[k]
        m2 = (np.abs(Xg - cx) <= SX / 2) & (np.abs(Yg - cy) <= SY / 2)
        vols.append((env & ~occ)[m2].sum() * DX ** 3 / 1000)
    del occ, env

    f = ndimage.gaussian_filter(np.pad(corpo, 2).astype(np.float32), 0.55)
    del corpo
    v, fa, _, _ = marching_cubes(f, 0.5, spacing=(DX, DX, DX))
    del f
    v = v - 2 * DX
    verts = np.column_stack([x0 + v[:, 1] + DX / 2, y0 + v[:, 0] + DX / 2, zs[0] + v[:, 2]])
    import fast_simplification
    for red in (0.7, 0.65, 0.6, 0.5, 0.0):   # simplifica menos se a malha abrir ou soltar lascas
        if red:
            vv, ff = fast_simplification.simplify(verts.astype(np.float32), fa[:, ::-1], target_reduction=red)
        else:
            vv, ff = verts, fa[:, ::-1]
        tm = trimesh.Trimesh(vv, ff, process=False)
        if tm.is_watertight and len(trimesh.Trimesh(vv, ff).split(only_watertight=False)) == 1:
            break
    if tm.volume < 0:
        tm.invert()
    tm.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))   # fundo na mesa
    tm.apply_translation([0, 0, -tm.bounds[0, 2]])
    tm.export(os.path.join(sai, "bandeja.stl"))
    e = tm.extents
    linhas = [f"Bandeja {colecao} {parte}: {e[0]:.0f} x {e[1]:.0f} x {e[2]:.0f} mm, fechada={tm.is_watertight}",
              "Silicone por cavidade (já com 10% de sobra):"]
    linhas += [f"  vaga {k} {r}: ~{v * 1.1:.0f} ml" for k, (r, v) in enumerate(zip(rot, vols), 1)]
    linhas.append(f"  total: ~{sum(vols) * 1.1:.0f} ml")
    open(os.path.join(sai, "LEIA.txt"), "w").write("\n".join(linhas) + "\n")
    print("\n".join(linhas))


if __name__ == "__main__":
    if sys.argv[1] == "tampa":
        tampa(sys.argv[2])
    else:
        bandeja(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6:])
