"""Gera o molde de uma coleção (6 peças): BASE + CONTRAMOLDE, para impressora de filamento,
e o SILICONE que fica entre os dois (só para prévia e cálculo de volume).

Uso:
  python gerar_molde.py pasta_pecas pasta_saida peca1 peca2 ... peca6

As peças são as finais do finalizar_lote.py (costas em z = 0, pino em D para baixo).

Como funciona (vista com as costas das peças para baixo):
- BASE: placa de 8 mm. As peças encaixam pelo pino em D (folga 0,2 mm). Tem 4 cones de
  centragem nos cantos e furos de respiro por onde sai o excesso de silicone.
- CONTRAMOLDE: bloco que cobre as peças deixando 3,5 mm em volta de cada uma e uma lâmina de
  3,5 mm sobre a base. Parede em volta que abraça a base (anti-vazamento), batentes nos
  cantos que param a base na distância exata e pequenos "dentes" que travam o silicone.
- Para fazer o silicone: vire o contramolde (cavidades para cima), despeje o silicone e desça
  a base com as peças até encostar nos batentes. O excesso sai pelos respiros da base.
- Para usar: o silicone volta para dentro do contramolde e serve de apoio ao despejar o gesso.
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, Manifold
from scipy import ndimage
from skimage.measure import marching_cubes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from relevo3d import _camadas, _ocupacao  # noqa: E402
from finalizar_lote import para_trimesh  # noqa: E402

SILICONE = 3.5     # espessura do silicone em volta das peças e da lâmina de fundo
VAO = 5.0          # parede de contramolde entre duas cavidades
BORDA = 6.0        # lâmina de silicone além da última peça
FOLGA_PINO = 0.2
FOLGA_PAREDE = 0.25
PAREDE = 4.0
BASE_ESP = 8.0
PAREDE_DESCE = 6.0     # quanto a parede do contramolde abraça a base (a base sobra 2 mm)
CANTO = 14.0           # batente de canto (sem silicone)
CAPA = 3.0             # contramolde acima da peça mais alta
DX = 0.5


def carregar(pasta, nomes):
    pecas = []
    for n in nomes:
        m = trimesh.load(os.path.join(pasta, n + ".stl"))
        pecas.append((n, m))
    return pecas


def arranjar(pecas):
    """3 colunas x 2 linhas; as mais largas dividem coluna para o molde ficar estreito."""
    ordem = sorted(pecas, key=lambda p: -p[1].extents[0])
    colunas = [ordem[0:2], ordem[2:4], ordem[4:6]]
    larg = [max(p[1].extents[0] for p in c) + 2 * SILICONE for c in colunas]
    alt = [max(c[r][1].extents[1] for c in colunas) + 2 * SILICONE for r in (0, 1)]
    W = sum(larg) + VAO * 2
    H = sum(alt) + VAO
    colocadas = []
    x = -W / 2
    for c, lw in zip(colunas, larg):
        y = H / 2
        for r, (n, m) in enumerate(c):
            yc = y - alt[r] / 2
            mm = m.copy()
            b = mm.bounds
            mm.apply_translation([x + lw / 2 - (b[0, 0] + b[1, 0]) / 2, yc - (b[0, 1] + b[1, 1]) / 2, 0])
            colocadas.append((n, mm))
            y -= alt[r] + VAO
        x += lw + VAO
    return colocadas, W, H


def furo_d(m):
    """Contorno do pino em D (corte a 2 mm abaixo das costas), com folga."""
    s = m.section(plane_origin=[0, 0, -2.0], plane_normal=[0, 0, 1])
    poli, para3d = s.to_2D()
    p = max(poli.polygons_full, key=lambda q: q.area).buffer(FOLGA_PINO, join_style=1)
    pts = trimesh.transform_points(np.column_stack([np.array(p.exterior.coords), np.zeros(len(p.exterior.coords))]), para3d)[:, :2]
    cs = CrossSection([pts[:-1].tolist()])
    if cs.area() <= 0:
        cs = CrossSection([pts[:-1][::-1].tolist()])
    return cs


def texto(t, altura, espelhar=False):
    """Texto -> CrossSection (mm), centralizado na origem."""
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), t, size=altura, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    polis = [np.asarray(p) for p in tp.to_polygons() if len(p) > 2]
    cs = CrossSection([p.tolist() for p in polis], fillrule=FillRule.EvenOdd)
    b = cs.bounds()
    cs = cs.translate((-(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2))
    if espelhar:
        cs = cs.mirror((0, 1))
    return cs


def caixa_texto(cs):
    b = cs.bounds()
    return b[2] - b[0], b[3] - b[1]


def main():
    ent, sai = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    colecao, parte = "", ""
    if "--colecao" in args:
        i = args.index("--colecao"); colecao = args[i + 1]; del args[i:i + 2]
    if "--parte" in args:
        i = args.index("--parte"); parte = args[i + 1]; del args[i:i + 2]
    nomes = [a.split(":")[0] for a in args]
    rotulos = {a.split(":")[0]: (a.split(":")[1] if ":" in a else a.split(":")[0]).upper() for a in args}
    os.makedirs(sai, exist_ok=True)
    pecas, W, H = arranjar(carregar(ent, nomes))
    iw, ih = W + 2 * BORDA, H + 2 * BORDA                       # área interna (= tamanho da base)
    ow, oh = iw + 2 * (FOLGA_PAREDE + PAREDE), ih + 2 * (FOLGA_PAREDE + PAREDE)
    zmax = max(m.bounds[1, 2] for _, m in pecas)
    ztopo = zmax + SILICONE + CAPA
    print(f"base {iw:.1f} x {ih:.1f} mm | contramolde {ow:.1f} x {oh:.1f} x {ztopo + PAREDE_DESCE:.1f} mm (mesa 270 x 270)")
    cantos = [(sx * (iw / 2 - CANTO / 2), sy * (ih / 2 - CANTO / 2)) for sx in (1, -1) for sy in (1, -1)]

    # ---------- grade de voxels ----------
    x0, y0 = -ow / 2 - 2, -oh / 2 - 2
    nx, ny = int((ow + 4) / DX), int((oh + 4) / DX)
    zs = np.arange(-BASE_ESP - 2, ztopo + 2, DX)
    X = x0 + (np.arange(nx) + 0.5) * DX
    Y = y0 + (np.arange(ny) + 0.5) * DX
    occ = np.zeros((ny, nx, len(zs)), bool)
    for n, m in pecas:
        z, sen, cont = _camadas(m.vertices[m.faces].astype(np.float64), x0, y0, DX, nx, ny)
        occ |= _ocupacao(z, sen, cont, zs, DX) > 0.5
        del z, sen
    occ[:, :, zs < 0] = False                                   # o pino fica dentro da base
    dist = ndimage.distance_transform_edt(~occ) * DX
    Zg = zs[None, None, :]
    dentro_int = (np.abs(X)[None, :] <= iw / 2) & (np.abs(Y)[:, None] <= ih / 2)
    canto = np.zeros_like(dentro_int)
    for cx, cy in cantos:
        canto |= (np.abs(X[None, :] - cx) <= CANTO / 2) & (np.abs(Y[:, None] - cy) <= CANTO / 2)
    lamina = (dentro_int & ~canto)[:, :, None] & (Zg >= 0) & (Zg <= SILICONE)
    env = ((dist <= SILICONE) & (Zg >= 0)) | lamina
    env &= dentro_int[:, :, None]
    # dentes que travam o silicone no contramolde: meias-esferas no teto da lâmina, entre as peças
    Xg, Yg = np.meshgrid(X, Y)
    for gx in np.linspace(-iw / 2 + 10, iw / 2 - 10, 7):
        for gy in np.linspace(-ih / 2 + 10, ih / 2 - 10, 5):
            j, i = int((gy - y0) / DX), int((gx - x0) / DX)
            if dist[j, i, np.searchsorted(zs, 1.0)] < SILICONE + 3:
                continue
            bola = (Xg - gx) ** 2 + (Yg - gy) ** 2
            env &= ~(((bola[:, :, None] + (Zg - SILICONE) ** 2) <= 2.0 ** 2) & (Zg > 1.4))
    silicone = env & ~occ
    print(f"silicone: {silicone.sum() * DX ** 3 / 1000:.0f} ml")

    # ---------- contramolde (voxels) ----------
    caixa = (np.abs(X)[None, :] <= ow / 2) & (np.abs(Y)[:, None] <= oh / 2)
    contra = caixa[:, :, None] & (Zg >= -PAREDE_DESCE) & (Zg <= ztopo)
    contra &= ~env
    folga_int = (np.abs(X)[None, :] <= iw / 2 + FOLGA_PAREDE) & (np.abs(Y)[:, None] <= ih / 2 + FOLGA_PAREDE)
    contra &= ~(folga_int[:, :, None] & (Zg < 0))               # lugar da base
    for cx, cy in cantos:                                        # furo cônico de centragem
        r = 3.8 - (Zg - 0) * (1.5 / 5.5)
        contra &= ~((((Xg - cx) ** 2 + (Yg - cy) ** 2)[:, :, None] <= r ** 2) & (Zg >= 0) & (Zg <= 5.6))

    # nome da coleção gravado (1 mm) na lateral da frente do contramolde
    if colecao or parte:
        from matplotlib.path import Path as MPath
        rot = f"{colecao}  {parte}".strip()
        cs = texto(rot, 7.0)
        w, h = caixa_texto(cs)
        esc = min(1.0, (ow - 30) / w)
        zc = (ztopo - PAREDE_DESCE) / 2
        Xz = np.stack(np.meshgrid(X, zs, indexing="ij"), -1).reshape(-1, 2)
        mask = np.zeros(len(Xz), bool)
        for poly in cs.scale((esc, esc)).to_polygons():
            mask ^= MPath(np.asarray(poly) + [0, zc]).contains_points(Xz)
        mask = mask.reshape(len(X), len(zs))
        face = Y < -oh / 2 + 1.0
        contra &= ~(face[:, None, None] & mask[None, :, :])

    def malha(vol, nome):
        f = ndimage.gaussian_filter(np.pad(vol, 2).astype(np.float32), 0.6)
        v, fa, _, _ = marching_cubes(f, 0.5, spacing=(DX, DX, DX))
        v = v - 2 * DX
        verts = np.column_stack([x0 + v[:, 1] + DX / 2, y0 + v[:, 0] + DX / 2, zs[0] + v[:, 2]])
        tm = trimesh.Trimesh(verts, fa[:, ::-1], process=False)
        import fast_simplification
        vv, ff = fast_simplification.simplify(tm.vertices.astype(np.float32), tm.faces, target_reduction=0.75)
        tm = trimesh.Trimesh(vv, ff, process=False)
        if tm.volume < 0:
            tm.invert()
        tm.export(os.path.join(sai, nome))
        return tm

    c = malha(contra, "contramolde.stl")
    s = malha(silicone, "silicone_previa.stl")

    # ---------- base (geometria exata) ----------
    base = Manifold.cube((iw, ih, BASE_ESP)).translate((-iw / 2, -ih / 2, -BASE_ESP))
    for n, m in pecas:
        base = base - Manifold.extrude(furo_d(m), 4.6 + 0.01).translate((0, 0, -4.6))
    for cx, cy in cantos:
        base = base + Manifold.cylinder(5.0, 3.5, 2.1, 64).translate((cx, cy, 0))
    # nome de cada peça gravado ao lado do encaixe, escondido atrás da peça
    for n, m in pecas:
        sec = m.section(plane_origin=[0, 0, 0.3], plane_normal=[0, 0, 1])
        poli, para3d = sec.to_2D()
        costas = max(poli.polygons_full, key=lambda q: q.area)
        off = trimesh.transform_points([[0, 0, 0]], para3d)[0][:2]
        from shapely.affinity import translate as sh_translate
        from shapely.geometry import box as sh_box
        costas = sh_translate(costas, off[0], off[1]).buffer(-2.0)
        d = m.section(plane_origin=[0, 0, -2.0], plane_normal=[0, 0, 1]).to_2D()
        dp = max(d[0].polygons_full, key=lambda q: q.area)
        dc = trimesh.transform_points([[dp.centroid.x, dp.centroid.y, 0]], d[1])[0][:2]
        colocado = False
        for alt in (4.5, 3.8, 3.2, 2.6):
            cs = texto(rotulos[n], alt)
            w, h = caixa_texto(cs)
            for dx_, dy in [(0, -(7 + h / 2)), (0, 7 + h / 2), (0, -(10 + h / 2)), (0, 10 + h / 2)] + \
                    [(sx * (6 + w / 2), sy * k) for sx in (1, -1) for k in (0, 6, 12, 18) for sy in (1, -1)] + \
                    [(sx * k, sy * (14 + h / 2)) for k in (6, 12) for sx in (1, -1) for sy in (1, -1)]:
                cx, cy = dc[0] + dx_, dc[1] + dy
                if costas.contains(sh_box(cx - w / 2 - 0.5, cy - h / 2 - 0.5, cx + w / 2 + 0.5, cy + h / 2 + 0.5)):
                    base = base - Manifold.extrude(cs, 0.81).translate((cx, cy, -0.8))
                    colocado = True
                    break
            if colocado:
                break
        if not colocado:
            print(f"aviso: sem espaço para o nome de {n}")
    # coleção e parte gravados nas costas da base (espelhado para ler olhando por trás)
    if colecao or parte:
        for t, alt, dy in ((colecao, 12.0, 9.0), (parte, 9.0, -9.0)):
            if not t:
                continue
            cs = texto(t, alt, espelhar=True)
            w, h = caixa_texto(cs)
            esc = min(1.0, (iw - 40) / w)
            base = base - Manifold.extrude(cs.scale((esc, esc)), 1.01).translate((0, dy, -BASE_ESP - 0.01))
    respiros = 0
    for gx in np.arange(-iw / 2 + 8, iw / 2 - 7, 12.5):
        for gy in np.arange(-ih / 2 + 8, ih / 2 - 7, 12.5):
            j, i = int((gy - y0) / DX), int((gx - x0) / DX)
            if dist[j, i, np.searchsorted(zs, 0.5)] < SILICONE + 2.5:
                continue
            if any(abs(gx - cx) < CANTO / 2 + 2 and abs(gy - cy) < CANTO / 2 + 2 for cx, cy in cantos):
                continue
            if (colecao or parte) and abs(gy) < 18 and abs(gx) < (iw - 30) / 2:
                continue
            base = base - Manifold.cylinder(BASE_ESP + 1, 1.6, 1.6, 32).translate((gx, gy, -BASE_ESP - 0.5))
            respiros += 1
    b = para_trimesh(base)
    b.export(os.path.join(sai, "base.stl"))
    print(f"base: {respiros} respiros | fechada={b.is_watertight}")
    print(f"contramolde fechado={c.is_watertight} | volume {c.volume / 1000:.0f} cm3")

    # peças na posição do molde (para conferir)
    trimesh.util.concatenate([m for _, m in pecas]).export(os.path.join(sai, "pecas_posicionadas.stl"))
    with open(os.path.join(sai, "posicoes.txt"), "w") as f:
        for n, m in pecas:
            cx, cy = m.bounds[:, :2].mean(axis=0)
            f.write(f"{n}: centro x={cx:.1f} y={cy:.1f} mm\n")


if __name__ == "__main__":
    main()
