"""Molde KIT M (6 peças, silicone numa peça só): CONTRAMOLDE por kit + TAMPA universal.

Mesma ideia do molde padrão M (sanduíche: contramolde, camada de silicone de ~3,5 mm, peças na tampa
pressionadas por cima, excesso saindo pelos respiros), mas feito para imprimir rápido e barato:
  - o contramolde já é a moldura: tem a parede contra vazamento e o degrau (batente) onde a tampa assenta;
  - a altura é só a que a peça mais grossa do kit precisa;
  - imprime com o fundo plano na mesa e as cavidades para cima: nada fica no ar, SEM SUPORTE;
  - é maciço no desenho, mas o fatiador enche por dentro com preenchimento leve
    (recomendado: "Relâmpago"/Lightning, que só sustenta as superfícies de cima);
  - a base vira uma tampa fina (3 mm + nervuras), universal, impressa uma vez só.

O silicone sai numa peça única: as 6 cavidades ligadas por uma lâmina de 3,5 mm.

  contramolde.stl   um por kit. Nomes das peças e da coleção gravados no fundo.
  tampa_kit_M.stl   universal: 6 encaixes em D (números 1 a 6), respiros, nervuras e um canto
                    chanfrado (só entra de um jeito no contramolde).

Uso:
  python molde_kit.py tampa saida
  python molde_kit.py contramolde pasta_pecas saida "NATAL 2026" "PARTE 1 de 2" p1:Nome ... p6:Nome
     (peças finais com pino, centradas no retângulo, costas em z = 0; vagas 1 a 3 numa fileira, 4 a 6 na outra)

Coordenadas de montagem: costas das peças em z = 0, frente para +z. Tampa de z = -3 a 0 (nervuras para -z),
lâmina de silicone de 0 a 3,5, contramolde acima. Em uso tudo fica virado: contramolde embaixo
(cavidades para cima) e a tampa com as peças por cima.
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
SIL = 3.9          # silicone em volta das peças: 3,5 mm + 0,4 que o arredondamento da malha come
LAMINA = 3.0       # lâmina de silicone que liga as 6 cavidades: 3,0 + 0,5 do degrau da malha = 3,5 mm (medido)
FUNDO = 2.0        # plástico mínimo sob a peça mais grossa
MARGEM = 6.0       # silicone além da cavidade mais externa (faixa onde ficam os respiros da borda)
SX, SY = 85.0, 103.0           # distância entre os centros das vagas
DEGRAU = 2.0       # largura do batente onde a tampa assenta (em volta da lâmina)
FOLGA = 0.3        # folga da tampa dentro da parede
PAREDE = 3.0
GUIA = 4.0         # quanto a parede sobe além do batente (guia a tampa)
CHANFRO = 18.0     # canto chanfrado: a tampa só entra de um jeito
TAMPA_ESP, NERV_ALT, NERV_L, NERV_PASSO = 3.0, 4.0, 2.0, 28.0
FOLGA_D = 0.2
DX = 0.5

AX = SX + PECA_L / 2 + SIL + MARGEM            # meia-largura da lâmina de silicone
AY = SY / 2 + PECA_A / 2 + SIL + MARGEM


RESP_R, RESP_R_FORA = 1.5, 2.5   # respiro afunilado: 3 mm na face do silicone, 5 mm do lado de fora
RESP_BORDA = 3.0                 # distância dos respiros da borda até a beira da lâmina


def respiros():
    """Poucos respiros, em lugares que nunca caem sobre uma cavidade (qualquer peça M):
    4 cantos, meio dos 4 lados (na faixa da margem) e 2 no corredor entre as fileiras."""
    d = RESP_BORDA
    c = CHANFRO
    return [(-(AX - d), -(AY - d)), (AX - d, -(AY - d)), (-(AX - d), AY - d),
            (AX - d, AY - c - 2.0),                                           # ao lado do canto chanfrado
            (-(AX - d), 0.0), (AX - d, 0.0), (0.0, -(AY - d)), (0.0, AY - d),
            (-SX / 2, 0.0), (SX / 2, 0.0)]


def centros():
    return [(c * SX, r * SY / 2) for r in (1, -1) for c in (-1, 0, 1)]


def _chanfro(d):
    return CHANFRO - 2 * d + d * np.sqrt(2)     # o chanfro acompanha o afastamento d


def retangulo(d):
    """Contorno da lâmina afastado de d mm (canto +x+y chanfrado), como polígono."""
    ax, ay, c = AX + d, AY + d, _chanfro(d)
    return [(-ax, -ay), (ax, -ay), (ax, ay - c), (ax - c, ay), (-ax, ay)]


def dentro(X, Y, d):
    ax, ay = AX + d, AY + d
    return (np.abs(X) <= ax) & (np.abs(Y) <= ay) & (X + Y <= ax + ay - _chanfro(d))


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
    contorno = CrossSection([retangulo(DEGRAU)])
    t = Manifold.extrude(contorno, TAMPA_ESP).translate((0, 0, -TAMPA_ESP))
    ax, ay = AX + DEGRAU, AY + DEGRAU
    nx_ = np.arange(-ax + 14, ax - 5, NERV_PASSO)
    ny_ = np.arange(-ay + 14, ay - 5, NERV_PASSO)
    # nervuras na face de fora (z < -3), longe dos encaixes e dos números
    nerv = None
    for x in nx_:
        b = Manifold.cube((NERV_L, 2 * ay, NERV_ALT)).translate((x - NERV_L / 2, -ay, -TAMPA_ESP - NERV_ALT))
        nerv = b if nerv is None else nerv + b
    for y in ny_:
        nerv = nerv + Manifold.cube((2 * ax, NERV_L, NERV_ALT)).translate((-ax, y - NERV_L / 2, -TAMPA_ESP - NERV_ALT))
    nerv = nerv ^ Manifold.extrude(contorno.offset(-1.0), 40).translate((0, 0, -20))
    for cx, cy in centros():
        nerv = nerv - Manifold.cylinder(40, 10, 10, 48).translate((cx, cy, -20))
        nerv = nerv - Manifold.cylinder(40, 7, 7, 32).translate((cx, cy - 15, -20))
    t = t + nerv
    d = CrossSection.circle(PINO_RAIO + FOLGA_D, 96) - CrossSection.square((14, 14)).translate((-7, PINO_CORTE + FOLGA_D))
    for k, (cx, cy) in enumerate(centros(), 1):
        t = t - Manifold.extrude(d, 40).translate((cx, cy, -20))
        # número da vaga na face de fora; em uso a tampa fica virada (giro em x): espelhado em y
        pol, _ = texto_pol(str(k), 8)
        cs = CrossSection([(np.column_stack([p[:, 0], -p[:, 1]]) + [cx, cy - 15]).tolist() for p in pol],
                          fillrule=FillRule.EvenOdd)
        t = t - Manifold.extrude(cs, 0.8).translate((0, 0, -TAMPA_ESP - 0.01))
    furos = None
    for gx, gy in respiros():
        # afunilado: estreito na face do silicone (z = 0), largo para fora; o silicone quebra rente à lâmina
        f = (Manifold.cylinder(TAMPA_ESP + 0.2, RESP_R_FORA, RESP_R, 32).translate((gx, gy, -TAMPA_ESP - 0.1))
             + Manifold.cylinder(30, RESP_R_FORA, RESP_R_FORA, 32).translate((gx, gy, -TAMPA_ESP - 30)))
        furos = f if furos is None else furos + f
    n = len(respiros())
    t = t - furos
    m = para_trimesh(t)
    # para imprimir: a face lisa (a que encosta no silicone) na mesa, nervuras para cima
    m.apply_transform(trimesh.transformations.rotation_matrix(np.pi, [1, 0, 0]))
    m.apply_translation([0, 0, -m.bounds[0, 2]])
    m.export(os.path.join(sai, "tampa_kit_M.stl"))
    e = m.extents
    print(f"tampa_kit_M: {e[0]:.0f} x {e[1]:.0f} x {e[2]:.0f} mm, {n} respiros, fechada={m.is_watertight}")


# Sulcos por baixo (túneis com teto em 45°, sem suporte). DESLIGADO de propósito: medido no PrusaSlicer 2.7
# em 24/11/2026, os sulcos AUMENTAM o filamento (cada parede e teto ganha perímetros e camadas sólidas):
#   maciço 273 g | sulcos a cada 16 mm 364 g | a cada 34 mm 315 g (relâmpago 10%). A economia vem do fatiador.
OCO = False
OCO_CASCA = 2.0      # plástico mínimo entre o silicone e o sulco
OCO_PASSO = 16.0     # distância entre os sulcos
OCO_PAREDE = 1.6     # parede entre dois sulcos (no pé)
OCO_BORDA = 2.0      # faixa maciça por dentro da borda da lâmina


def esvaziar(corpo, env, Xg, Yg, zs, H):
    """Abre sulcos por baixo (lado da mesa): túneis ao longo de y, paredes retas e teto em 45° (sem suporte)."""
    perto = ndimage.distance_transform_edt(~env) * DX <= OCO_CASCA
    livre = corpo & ~perto & dentro(Xg, Yg, -OCO_BORDA)[:, :, None] & (zs >= 0)[None, None, :]
    kb = int(np.searchsorted(zs, H, side="right")) - 1          # camada que encosta na mesa
    run = np.cumprod(livre[:, :, kb::-1], axis=2).sum(axis=2)   # quantas camadas livres a partir da mesa
    x = Xg[0]
    meio = (np.arange(-AX - DEGRAU, AX + DEGRAU + OCO_PASSO, OCO_PASSO))
    i = np.argmin(np.abs(x[:, None] - meio[None, :]), axis=1)
    dxv = np.abs(x - meio[i]) / DX
    dentro_t = dxv <= (OCO_PASSO - OCO_PAREDE) / 2 / DX
    A = np.full(run.shape, -1.0)
    for t in np.unique(i[dentro_t]):
        cols = np.where((i == t) & dentro_t)[0]
        ap = np.min(run[:, cols] - 1 + dxv[cols][None, :], axis=1)      # teto do sulco t ao longo de y
        for y in range(1, len(ap)):                                     # cumeeira desce no máximo 45° em y
            ap[y] = min(ap[y], ap[y - 1] + 1)
        for y in range(len(ap) - 2, -1, -1):
            ap[y] = min(ap[y], ap[y + 1] + 1)
        A[:, cols] = ap[:, None] - dxv[cols][None, :]
    j = kb - np.arange(len(zs))
    cav = (j[None, None, :] >= 0) & (j[None, None, :] <= A[:, :, None])
    return corpo & ~cav


def contramolde(pasta, sai, colecao, parte, args):
    from relevo3d import _camadas, _ocupacao
    os.makedirs(sai, exist_ok=True)
    nomes = [a.split(":")[0] for a in args]
    rot = [a.split(":")[1].upper() for a in args]
    pecas = []
    for nm, (cx, cy) in zip(nomes, centros()):
        p = trimesh.load(os.path.join(pasta, nm + ".stl"))
        b = p.bounds
        e = b[1] - b[0]
        if e[0] > PECA_L + 0.5 or e[1] > PECA_A + 0.5 or b[1, 2] > PECA_E + 0.5:
            print(f"  ATENÇÃO: {nm} passa do tamanho M ({e[0]:.1f} x {e[1]:.1f} x {b[1, 2]:.1f})")
        p = p.copy()
        p.apply_translation([cx, cy, 0])
        pecas.append(p)
    H = max(max(p.bounds[1, 2] for p in pecas) + SIL, LAMINA) + FUNDO
    ext = DEGRAU + FOLGA + PAREDE
    x0, y0 = -(AX + ext) - 1, -(AY + ext) - 1
    nx, ny = int((2 * (AX + ext) + 2) / DX), int((2 * (AY + ext) + 2) / DX)
    zs = np.arange(-GUIA - 1, H + 1.5, DX)
    X = x0 + (np.arange(nx) + 0.5) * DX
    Y = y0 + (np.arange(ny) + 0.5) * DX
    Zg = zs[None, None, :]
    Xg, Yg = np.meshgrid(X, Y)
    occ = np.zeros((ny, nx, len(zs)), bool)
    for p in pecas:
        z, sen, cont = _camadas(p.vertices[p.faces].astype(np.float64), x0, y0, DX, nx, ny)
        o = _ocupacao(z, sen, cont, zs, DX) > 0.5
        o[:, :, zs < 0] = False
        occ |= o
    dist = ndimage.distance_transform_edt(~occ) * DX
    lam = dentro(Xg, Yg, 0)
    env = ((dist <= SIL) | (Zg <= LAMINA)) & (Zg >= 0) & lam[:, :, None]
    del dist
    silicone = (env & ~occ).sum() * DX ** 3 / 1000
    del occ
    fora = dentro(Xg, Yg, ext)
    corpo = fora[:, :, None] & (Zg >= 0) & (Zg <= H) & ~env
    parede = fora & ~dentro(Xg, Yg, DEGRAU + FOLGA)
    corpo |= parede[:, :, None] & (Zg < 0) & (Zg >= -GUIA)
    if OCO:
        corpo = esvaziar(corpo, env, Xg, Yg, zs, H)
    del env
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

    gr = np.zeros_like(lam)
    for k, ((cx, cy), r) in enumerate(zip(centros(), rot), 1):
        gr |= gravar(f"{k} {r}", 6, cx, cy, 60)
    gr |= gravar(f"PALCO & PINCEL  {colecao}  {parte}", 5, 0, 0, 2 * SX)
    corpo &= ~(gr[:, :, None] & (Zg > H - 0.6))

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
    tm.export(os.path.join(sai, "contramolde.stl"))
    e = tm.extents
    linhas = [f"Contramolde {colecao} {parte}: {e[0]:.0f} x {e[1]:.0f} x {e[2]:.0f} mm, fechado={tm.is_watertight}",
              "Vagas: " + ", ".join(f"{k} {r}" for k, r in enumerate(rot, 1)),
              f"Silicone (peça única): ~{silicone:.0f} ml; preparar ~{silicone * 1.1:.0f} ml (10% de sobra)"]
    open(os.path.join(sai, "LEIA.txt"), "w").write("\n".join(linhas) + "\n")
    print("\n".join(linhas))


if __name__ == "__main__":
    if sys.argv[1] == "tampa":
        tampa(sys.argv[2])
    else:
        contramolde(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6:])
