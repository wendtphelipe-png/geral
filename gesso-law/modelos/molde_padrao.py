"""Molde PADRÃO (tamanho M): moldura e base universais + miolo fino por coleção.

Tamanho M (2 peças por mesa da Elegoo Mars 5, 6 peças por molde):
  peça "em pé" de até 64 x 82 mm, até 35 mm de espessura (sem contar o pino),
  pino em D no CENTRO do retângulo da peça, lado reto para o topo.

Peças (impressão em filamento):
  moldura.stl  universal: caixa com tampa, parede anti-vazamento e paredes internas que
               apertam o miolo nas bordas e entre as cavidades.
  base.stl     universal: 6 encaixes em D sempre no mesmo lugar, número da vaga, respiros,
               cones de centragem.
  miolo.stl    um por coleção: casca de 2 mm que copia as 6 peças com vão de 3,5 mm,
               nervuras de apoio, batentes de canto e nomes gravados.

Uso:
  python molde_padrao.py universal saida
  python molde_padrao.py colecao entrada saida "NATAL 2026" "PARTE 1 de 2" escala p1:Nome p2:Nome ... (6)
     entrada = peças do relevo3d.py (costas em z=0, sem pino); escala = a do lote (ex.: 1.281).
     Gera as peças finais (com pino), as mesas da Mars 5 (2 por mesa) e o miolo.

Montagem para fazer o silicone (vista de baixo para cima):
  moldura com a tampa na mesa -> miolo dentro -> silicone -> base com as peças encaixadas,
  pressionada até encostar nos batentes. O excesso sai pelos respiros da base.
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, FillRule, Manifold
from scipy import ndimage
from skimage.measure import marching_cubes

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finalizar_lote import pino_d, para_manifold, para_trimesh  # noqa: E402

# ---------------- padrão M ----------------
PECA_L, PECA_A, PECA_E = 64.0, 82.0, 35.0
SIL = 3.5            # silicone
CASCA = 2.0          # espessura da casca do miolo
CORREDOR = 4.0       # parede da moldura entre duas vagas
BORDA = 12.0         # faixa livre em volta (batentes, nomes, parede da moldura)
FOLGA = 0.3
FOLGA_BASE = 0.25
FOLGA_PINO = 0.2
PAREDE = 4.0
BASE_ESP = 8.0
DESCE = 6.0          # parede da moldura que abraça a base
TAMPA = 3.0
CANTO = 11.0
NERVURA = 1.2
PASSO_NERV = 24.0
DX = 0.5

VAGA_L = PECA_L + 2 * SIL + 2 * CASCA      # 75
VAGA_A = PECA_A + 2 * SIL + 2 * CASCA      # 93
IW = 3 * VAGA_L + 2 * CORREDOR + 2 * BORDA
IH = 2 * VAGA_A + CORREDOR + 2 * BORDA
OW, OH = IW + 2 * (FOLGA_BASE + PAREDE), IH + 2 * (FOLGA_BASE + PAREDE)
Z_LAMINA = SIL + CASCA                     # topo da placa do miolo
Z_TOPO = PECA_E + SIL + CASCA              # topo das nervuras do miolo
Z_TAMPA = Z_TOPO + FOLGA                   # face de baixo da tampa da moldura


def centros():
    cs = []
    for r in (1, -1):                      # linha de cima (1) e de baixo (-1)
        for c in (-1, 0, 1):
            cs.append((c * (VAGA_L + CORREDOR), r * (VAGA_A + CORREDOR) / 2))
    return cs                              # vagas 1..6: cima esq->dir, baixo esq->dir


CANTOS = [(sx * (IW / 2 - BORDA / 2), sy * (IH / 2 - BORDA / 2)) for sx in (1, -1) for sy in (1, -1)]


def texto(t, altura, rot=0):
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    tp = TextPath((0, 0), t, size=altura, prop=FontProperties(family="DejaVu Sans", weight="bold"))
    cs = CrossSection([np.asarray(p).tolist() for p in tp.to_polygons() if len(p) > 2], fillrule=FillRule.EvenOdd)
    b = cs.bounds()
    cs = cs.translate((-(b[0] + b[2]) / 2, -(b[1] + b[3]) / 2))
    return cs.rotate(rot) if rot else cs


def caber(cs, w, h):
    b = cs.bounds()
    return cs.scale([min(1.0, w / (b[2] - b[0]), h / (b[3] - b[1]))] * 2)


# ---------------- universais ----------------
def universal(sai):
    os.makedirs(sai, exist_ok=True)
    # base
    base = Manifold.cube((IW, IH, BASE_ESP)).translate((-IW / 2, -IH / 2, -BASE_ESP))
    furo = pino_d().translate((0, 0, -0.6))                 # D com a ponta, de 0 a -4,6
    furo_cs = CrossSection.circle(5.0 + FOLGA_PINO, 96) - CrossSection.square((12, 12)).translate((-6, 3.0 + FOLGA_PINO))
    for k, (cx, cy) in enumerate(centros(), 1):
        base = base - Manifold.extrude(furo_cs, 4.61).translate((cx, cy, -4.6))
        base = base - Manifold.extrude(texto(str(k), 6), 0.81).translate((cx, cy - 10, -0.8))
    for cx, cy in CANTOS:
        base = base + Manifold.cylinder(5.0, 3.5, 2.1, 64).translate((cx, cy, 0))
    # respiros: só fora das vagas e dos cantos
    n = 0
    for gx in np.arange(-IW / 2 + 6, IW / 2 - 5, 9.0):
        for gy in np.arange(-IH / 2 + 6, IH / 2 - 5, 9.0):
            if any(abs(gx - cx) < VAGA_L / 2 + 1.5 and abs(gy - cy) < VAGA_A / 2 + 1.5 for cx, cy in centros()):
                continue
            if any(abs(gx - cx) < CANTO / 2 + 2.5 and abs(gy - cy) < CANTO / 2 + 2.5 for cx, cy in CANTOS):
                continue
            base = base - Manifold.cylinder(BASE_ESP + 1, 1.6, 1.6, 24).translate((gx, gy, -BASE_ESP - 0.5))
            n += 1
    for t, alt, dy in (("PALCO & PINCEL", 11, 12), ("BASE PADRAO M  64x82x35", 7.5, -10)):
        cs = caber(texto(t, alt).mirror((0, 1)), IW - 70, 14)
        base = base - Manifold.extrude(cs, 1.01).translate((0, dy, -BASE_ESP - 0.01))
    b = para_trimesh(base)
    b.export(os.path.join(sai, "base.stl"))

    # moldura
    topo = Z_TAMPA + TAMPA
    caixa = Manifold.cube((OW, OH, topo + DESCE)).translate((-OW / 2, -OH / 2, -DESCE))
    oco = Manifold.cube((IW + 2 * FOLGA_BASE, IH + 2 * FOLGA_BASE, Z_TAMPA + DESCE)).translate(
        (-IW / 2 - FOLGA_BASE, -IH / 2 - FOLGA_BASE, -DESCE - 0.01))
    m = caixa - oco
    # paredes internas na borda e entre as vagas, apertando a placa do miolo
    z0 = Z_LAMINA + FOLGA
    h = Z_TAMPA - z0 + 0.01
    paredes = Manifold.cube((IW + 0.6, IH + 0.6, h)).translate((-IW / 2 - 0.3, -IH / 2 - 0.3, z0))
    for cx, cy in centros():
        paredes = paredes - Manifold.cube((VAGA_L + 2 * FOLGA, VAGA_A + 2 * FOLGA, h + 1)).translate(
            (cx - VAGA_L / 2 - FOLGA, cy - VAGA_A / 2 - FOLGA, z0 - 0.5))
    m = m + paredes
    # identificação na lateral (gravada)
    for t, y in (("PALCO & PINCEL  MOLDURA PADRAO M", -OH / 2),):
        cs = caber(texto(t, 7), OW - 40, 9)
        gr = Manifold.extrude(cs, 1.01).rotate((90, 0, 0)).translate((0, y + 1.0, (topo - DESCE) / 2))
        m = m - gr
    mt = para_trimesh(m)
    mt.export(os.path.join(sai, "moldura.stl"))
    print(f"base {IW:.1f} x {IH:.1f} x {BASE_ESP:.0f} mm, {n} respiros | fechada={b.is_watertight}")
    print(f"moldura {OW:.1f} x {OH:.1f} x {topo + DESCE:.1f} mm (mesa 270 x 270) | fechada={mt.is_watertight}")


# ---------------- coleção ----------------
def preparar(entrada, nomes, escala):
    pecas = []
    for n in nomes:
        tm = trimesh.load(os.path.join(entrada, n + ".stl"))
        e = tm.extents
        s = min(escala, PECA_L / e[0], PECA_A / e[1], PECA_E / e[2])
        tm.apply_scale(s)
        b = tm.bounds
        tm.apply_translation([-(b[0, 0] + b[1, 0]) / 2, -(b[0, 1] + b[1, 1]) / 2, -b[0, 2]])
        # o centro precisa ter costas para receber o pino
        sec = tm.section(plane_origin=[0, 0, 0.3], plane_normal=[0, 0, 1])
        p2, t3 = sec.to_2D()
        from shapely.geometry import Point
        c2 = trimesh.transform_points([[0, 0, 0]], np.linalg.inv(t3))[0][:2]
        ok = any(q.contains(Point(c2).buffer(6.0)) for q in p2.polygons_full)
        corpo = para_manifold(tm)
        if not ok:
            # fecha os vãos das costas (ex.: miolo da guirlanda) com uma placa fina de 3 mm
            for q in p2.polygons_full:
                for furo in q.interiors:
                    pts = trimesh.transform_points(np.column_stack([np.array(furo.coords), np.zeros(len(furo.coords))]), t3)[:, :2]
                    cs = CrossSection([pts[:-1].tolist()])
                    if cs.area() <= 0:
                        cs = CrossSection([pts[:-1][::-1].tolist()])
                    corpo = corpo + Manifold.extrude(cs.offset(1.0), 3.0)
            ok = True
            print(f"  {n}: vão das costas fechado com placa de 3 mm para receber o pino")
        f = para_trimesh(corpo + pino_d())
        pecas.append((n, f, s, ok))
        e = tm.extents
        print(f"{n}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm (escala {s:.3f})" + ("" if ok else "  ATENÇÃO: centro sem costas para o pino"))
    return pecas


def mesas(pecas, sai):
    d = os.path.join(sai, "mesas-resina")
    os.makedirs(d, exist_ok=True)
    for (a, ma, _, _), (b, mb, _, _) in zip(pecas[0::2], pecas[1::2]):
        A, B = ma.copy(), mb.copy()
        A.apply_translation([-A.bounds[1, 0] - 3, 0, 0])
        B.apply_translation([-B.bounds[0, 0] + 3, 0, 0])
        trimesh.util.concatenate([A, B]).export(os.path.join(d, f"mesa_{a}_{b}.stl"))


def miolo(pecas, rotulos, colecao, parte, sai):
    x0, y0 = -IW / 2 - 2, -IH / 2 - 2
    nx, ny = int((IW + 4) / DX), int((IH + 4) / DX)
    zs = np.arange(-1.0, Z_TOPO + 2, DX)
    X = x0 + (np.arange(nx) + 0.5) * DX
    Y = y0 + (np.arange(ny) + 0.5) * DX
    Zg = zs[None, None, :]
    occ = np.zeros((ny, nx, len(zs)), bool)
    from relevo3d import _camadas, _ocupacao
    for (n, m, _, _), (cx, cy) in zip(pecas, centros()):
        mm = m.copy()
        mm.apply_translation([cx, cy, 0])
        z, sen, cont = _camadas(mm.vertices[mm.faces].astype(np.float64), x0, y0, DX, nx, ny)
        occ |= _ocupacao(z, sen, cont, zs, DX) > 0.5
    occ[:, :, zs < 0] = False
    dist = ndimage.distance_transform_edt(~occ) * DX
    dentro = ((np.abs(X)[None, :] <= IW / 2 - FOLGA) & (np.abs(Y)[:, None] <= IH / 2 - FOLGA))
    canto = np.zeros_like(dentro)
    for cx, cy in CANTOS:
        canto |= (np.abs(X[None, :] - cx) <= CANTO / 2) & (np.abs(Y[:, None] - cy) <= CANTO / 2)
    na_vaga = np.zeros_like(dentro)
    for cx, cy in centros():
        na_vaga |= (np.abs(X[None, :] - cx) <= VAGA_L / 2) & (np.abs(Y[:, None] - cy) <= VAGA_A / 2)
    lamina = (dentro & ~canto)[:, :, None] & (Zg >= 0) & (Zg <= SIL)
    env = (((dist <= SIL) & (Zg >= 0)) | lamina) & dentro[:, :, None]
    Xg, Yg = np.meshgrid(X, Y)
    # dentes de travamento do silicone (na faixa da borda, posições fixas)
    for gx in np.linspace(-IW / 2 + 30, IW / 2 - 30, 5):
        for gy in (IH / 2 - BORDA / 2, -IH / 2 + BORDA / 2):
            bola = ((Xg - gx) ** 2 + (Yg - gy) ** 2)[:, :, None] + (Zg - SIL) ** 2
            env &= ~((bola <= 2.0 ** 2) & (Zg > 1.4))
    silicone = env & ~occ
    d_env = ndimage.distance_transform_edt(~env) * DX
    casca = (d_env > 0) & (d_env <= CASCA) & dentro[:, :, None] & (Zg >= 0)
    placa = dentro[:, :, None] & (Zg >= 0) & (Zg <= Z_LAMINA) & ~env
    nerv = ((np.abs(((X[None, :] + 1000) % PASSO_NERV) - PASSO_NERV / 2) <= NERVURA / 2) |
            (np.abs(((Y[:, None] + 1000) % PASSO_NERV) - PASSO_NERV / 2) <= NERVURA / 2))
    borda_vaga = np.zeros_like(dentro)                      # contorno da vaga também vira nervura
    for cx, cy in centros():
        rx, ry = np.abs(X[None, :] - cx), np.abs(Y[:, None] - cy)
        borda_vaga |= ((rx <= VAGA_L / 2) & (ry <= VAGA_A / 2)) & ((rx >= VAGA_L / 2 - NERVURA) | (ry >= VAGA_A / 2 - NERVURA))
    nervuras = ((nerv | borda_vaga) & na_vaga)[:, :, None] & (Zg <= Z_TOPO) & ~env & (d_env > 0)
    # nervura só onde está "em cima" da casca (não pendurada no ar)
    tem_casca_abaixo = np.maximum.accumulate((casca | placa), axis=2)
    nervuras &= tem_casca_abaixo
    blocos = canto[:, :, None] & (Zg >= 0) & (Zg <= Z_LAMINA)
    for cx, cy in CANTOS:
        r = 3.8 - Zg * (1.5 / 5.5)
        blocos &= ~((((Xg - cx) ** 2 + (Yg - cy) ** 2)[:, :, None] <= r ** 2))
    mio = casca | placa | nervuras | blocos
    mio &= ~(env & ~occ)                                      # nunca invade o silicone
    # nomes gravados no topo da placa, na faixa da borda (0,6 mm)
    from matplotlib.path import Path as MPath
    pts = np.column_stack([Xg.ravel(), Yg.ravel()])

    def gravar(cs, dx_, dy_):
        msk = np.zeros(len(pts), bool)
        for poly in cs.to_polygons():
            msk ^= MPath(np.asarray(poly) + [dx_, dy_]).contains_points(pts)
        return msk.reshape(Xg.shape)

    gr = np.zeros_like(dentro)
    for k, ((n, _, _, _), (cx, cy)) in enumerate(zip(pecas, centros()), 1):
        cs = caber(texto(f"{k} {rotulos[n]}", 5.5), VAGA_L - 6, 7)
        gr |= gravar(cs, cx, cy + np.sign(cy) * (VAGA_A / 2 + CORREDOR / 2 + BORDA / 2 - 2))
    for t, sx in ((colecao, -1), (parte, 1)):
        if t:
            cs = caber(texto(t, 6, rot=90 * sx), 8, IH - 40)
            gr |= gravar(cs, sx * (IW / 2 - BORDA / 2), 0)
    mio &= ~(gr[:, :, None] & (Zg > Z_LAMINA - 0.6) & (Zg <= Z_LAMINA + 0.01))

    def malha(vol, nome):
        f = ndimage.gaussian_filter(np.pad(vol, 2).astype(np.float32), 0.55)
        v, fa, _, _ = marching_cubes(f, 0.5, spacing=(DX, DX, DX))
        v = v - 2 * DX
        verts = np.column_stack([x0 + v[:, 1] + DX / 2, y0 + v[:, 0] + DX / 2, zs[0] + v[:, 2]])
        import fast_simplification
        for red in (0.7, 0.6, 0.45, 0.0):                     # menos simplificação se a malha abrir
            if red:
                vv, ff = fast_simplification.simplify(verts.astype(np.float32), fa[:, ::-1], target_reduction=red)
            else:
                vv, ff = verts, fa[:, ::-1]
            tm = trimesh.Trimesh(vv, ff, process=False)
            if tm.is_watertight:
                break
        if tm.volume < 0:
            tm.invert()
        tm.export(os.path.join(sai, nome))
        return tm

    t_m = malha(mio, "miolo.stl")
    malha(silicone, "silicone_previa.stl")
    pos = trimesh.util.concatenate([p.copy().apply_translation([cx, cy, 0]) or p for p in []]) if False else None
    junt = []
    for (n, m, _, _), (cx, cy) in zip(pecas, centros()):
        mm = m.copy()
        mm.apply_translation([cx, cy, 0])
        junt.append(mm)
    trimesh.util.concatenate(junt).export(os.path.join(sai, "pecas_na_base.stl"))
    print(f"miolo: {t_m.volume / 1000:.0f} cm3 (~{t_m.volume / 1000 * 1.24:.0f} g de PLA maciço) | "
          f"silicone ~{silicone.sum() * DX ** 3 / 1000:.0f} ml | fechado={t_m.is_watertight}")


def main():
    if sys.argv[1] == "universal":
        universal(sys.argv[2])
        return
    _, _, ent, sai, colecao, parte, escala, *args = sys.argv
    nomes = [a.split(":")[0] for a in args]
    rot = {a.split(":")[0]: a.split(":")[1].upper() for a in args}
    os.makedirs(sai, exist_ok=True)
    pecas = preparar(ent, nomes, float(escala))
    for n, f, _, _ in pecas:
        f.export(os.path.join(sai, n + ".stl"))
    mesas(pecas, sai)
    miolo(pecas, rot, colecao, parte, sai)


if __name__ == "__main__":
    main()
