"""Transforma um modelo 3D (STL, OBJ, GLB) em peça para molde de gesso.

Modo "inteiro" (padrão): a peça é a metade da frente do personagem, com o
volume real. As costas são cortadas num plano reto (--profundidade).
As laterais seguem a curva verdadeira do modelo (sem paredes retas).
Atrás de partes finas (orelha, aba do chapéu, braço) entra um "miolo" de
suporte arredondado, recuado da superfície, que se une à peça com curvas
suaves: ele fica escondido e impede que essas partes quebrem no gesso.

Modo "medalha": comprime a profundidade, como numa medalha.

Uso:
  python relevo3d.py modelo.stl saida --tamanho 60 --profundidade 25 --furo 0 24
  --girar X Y Z     gira o modelo (graus) até ele ficar de frente
  --recuo 2.5       quanto o miolo de suporte fica escondido atrás da superfície (mm)
  --curva 2.0       raio das curvas que unem o suporte à peça (mm)
"""
import argparse
import os
import sys

import numpy as np
import trimesh
from numba import njit
from scipy import ndimage, sparse
from scipy.sparse.linalg import spsolve

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gesso import Peca  # noqa: E402

MAX_CAMADAS = 64


@njit(cache=True)
def _camadas(tri, x0, y0, dx, n, m):
    """Para cada pixel, todas as profundidades em que a superfície do modelo é cruzada."""
    z = np.full((m, n, MAX_CAMADAS), np.inf)
    sen = np.zeros((m, n, MAX_CAMADAS), np.int8)
    cont = np.zeros((m, n), np.int32)
    for t in range(tri.shape[0]):
        ax, ay, az = tri[t, 0]
        bx, by, bz = tri[t, 1]
        cx, cy, cz = tri[t, 2]
        den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
        if abs(den) < 1e-12:
            continue
        i0 = max(int((min(ax, bx, cx) - x0) / dx) - 1, 0)
        i1 = min(int((max(ax, bx, cx) - x0) / dx) + 1, n - 1)
        j0 = max(int((min(ay, by, cy) - y0) / dx) - 1, 0)
        j1 = min(int((max(ay, by, cy) - y0) / dx) + 1, m - 1)
        for j in range(j0, j1 + 1):
            py = y0 + (j + 0.5) * dx
            for i in range(i0, i1 + 1):
                px = x0 + (i + 0.5) * dx
                w1 = ((by - cy) * (px - cx) + (cx - bx) * (py - cy)) / den
                w2 = ((cy - ay) * (px - cx) + (ax - cx) * (py - cy)) / den
                w3 = 1 - w1 - w2
                if w1 >= 0 and w2 >= 0 and w3 >= 0 and cont[j, i] < MAX_CAMADAS:
                    z[j, i, cont[j, i]] = w1 * az + w2 * bz + w3 * cz
                    sen[j, i, cont[j, i]] = 1 if den > 0 else -1
                    cont[j, i] += 1
    return z, sen, cont


@njit(cache=True)
def _ocupacao(z, sen, cont, zs, dz):
    """Fração de cada voxel que fica dentro do modelo (0 a 1).

    Dentro/fora por número de voltas: funciona mesmo com peças sobrepostas
    (olho dentro da cabeça, chapéu encostado no cabelo). A fração exata
    deixa a superfície lisa, sem degraus.
    """
    m, n = cont.shape
    occ = np.zeros((m, n, zs.shape[0]), np.float32)
    for j in range(m):
        for i in range(n):
            c = cont[j, i]
            if c < 2:
                continue
            ordem = np.argsort(-z[j, i, :c])
            w = 0
            ultimo_z = np.inf
            ultimo_s = 0
            for q in range(c):
                zq = z[j, i, ordem[q]]
                sq = sen[j, i, ordem[q]]
                if abs(zq - ultimo_z) < 1e-6 and sq == ultimo_s:
                    continue  # mesma passagem contada por dois triângulos vizinhos
                if w > 0:
                    for s in range(zs.shape[0]):
                        lo = max(zq, zs[s] - dz / 2)
                        hi = min(ultimo_z, zs[s] + dz / 2)
                        if hi > lo:
                            occ[j, i, s] = min(1.0, occ[j, i, s] + (hi - lo) / dz)
                w += sq
                ultimo_z = zq
                ultimo_s = sq
    return occ


def carregar(caminho, girar=(0, 0, 0), tamanho=60.0, busto=1.0, ajuste="maior"):
    """Gira, recorta (busto = fração de cima que fica) e escala para caber em `tamanho`."""
    malha = trimesh.load(caminho, force="mesh")
    for eixo, ang in zip(np.eye(3), girar):
        if ang:
            malha.apply_transform(trimesh.transformations.rotation_matrix(np.radians(ang), eixo))
    topo, base = malha.bounds[1, 1], malha.bounds[0, 1]
    corte = topo - busto * (topo - base)
    v = malha.vertices[malha.vertices[:, 1] >= corte]
    lo, hi = v.min(axis=0), v.max(axis=0)
    centro = (lo + hi) / 2
    if ajuste == "altura":
        centro[0] = np.median(v[:, 0])
    centro[2] = malha.bounds[1, 2]  # frente em z = 0
    malha.apply_translation(-centro)
    escala = tamanho / ((hi[1] - lo[1]) if ajuste == "altura" else max(hi[0] - lo[0], hi[1] - lo[1]))
    malha.apply_scale(escala)
    return malha, (corte - centro[1]) * escala


def _dist(occ, dx):
    """Distância com sinal: negativa dentro, positiva fora (mm)."""
    return (ndimage.distance_transform_edt(~occ) - ndimage.distance_transform_edt(occ)).astype(np.float32) * dx


def _dist_fina(frac, dx):
    """Distância com sinal usando a fração de cada voxel perto da superfície."""
    occ = frac > 0.5
    d = _dist(occ, dx)
    d = np.where(d > 0, d - 0.5 * dx, d + 0.5 * dx)
    borda = (frac > 0.02) & (frac < 0.98)
    d[borda] = (0.5 - frac[borda]) * dx
    return d


def _suave_uniao(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def peca_inteira(malha, tamanho, profundidade, recuo, curva, furos, corte_y=-1e9, arco=0.0, minimo=2.0, ombro=None, largura=40.0, lateral=False, fundo_vaos=3.0, dx=0.2):
    from skimage.measure import marching_cubes
    import fast_simplification
    lado = tamanho + 6
    n = int(round(lado / dx))
    x0 = y0 = -lado / 2
    tri = malha.vertices[malha.faces].astype(np.float64)
    z, sen, cont = _camadas(tri, x0, y0, dx, n, n)
    X = (np.arange(n) + 0.5) * dx + x0
    frente = malha.bounds[1, 2]
    plano = max(frente - profundidade, malha.bounds[0, 2])
    zs = np.arange(plano - 2 * dx, frente + 3 * dx, dx, dtype=np.float64)
    frac = _ocupacao(z, sen, cont, zs, dx)
    del z, sen
    frac[:, :, zs < plano] = 0
    # recorte do busto: base em arco (mais baixa no meio, sobe nas laterais)
    fundo = corte_y + arco * (X[None, :] / (tamanho / 2)) ** 2
    manter = X[:, None] >= fundo
    if ombro is not None:
        # abaixo da linha dos ombros, só o que está dentro de um contorno oval (corta braços soltos)
        oval = (X[None, :] / (largura / 2)) ** 2 + ((X[:, None] - ombro) / max(ombro - corte_y, 1)) ** 2 <= 1
        manter &= (X[:, None] >= ombro) | oval
        if lateral:
            manter &= np.abs(X[None, :]) <= largura / 2
    # distância (mm) até a linha de corte do busto, para um corte liso e com borda arredondada
    d_corte = ndimage.gaussian_filter(
        (ndimage.distance_transform_edt(~manter) - ndimage.distance_transform_edt(manter)).astype(np.float32) * dx, 2.0)
    occ = frac > 0.5
    if fundo_vaos > 0:
        # vãos vazados no meio da peça (ex.: entre o aro do capacete e a cabeça)
        # ganham um fundo, para nada ficar solto
        sil = occ.any(axis=2)
        vaos = ndimage.binary_fill_holes(sil) & ~sil
        fundo_z = (zs >= plano) & (zs <= plano + fundo_vaos)
        frac = np.maximum(frac, (vaos[:, :, None] & fundo_z[None, None, :]).astype(np.float32))
        occ = frac > 0.5
    d_modelo = ndimage.gaussian_filter(np.clip(_dist_fina(frac, dx), -4, 4), 1.0)
    # partes finas (aba do chapéu, renda da borda): engrossa até o mínimo
    if minimo > 0:
        # meia-espessura local = maior distância até a superfície num raio de `minimo`
        meia = ndimage.maximum_filter(np.clip(-d_modelo, 0, None), size=2 * int(round(minimo / dx)) + 1)
        falta = ndimage.gaussian_filter(np.clip(minimo / 2 - meia, 0, None), 3.0)
        d_modelo = d_modelo - falta
    d_plano = np.broadcast_to((plano - zs)[None, None, :], d_modelo.shape)
    # miolo de suporte: tudo o que é visto de frente, preenchido até as costas,
    # recuado da superfície e arredondado
    alcance = np.maximum.accumulate(occ[:, :, ::-1], axis=2)[:, :, ::-1]
    alcance &= (zs >= plano)[None, None, :]
    d_miolo = ndimage.gaussian_filter(np.clip(_dist(alcance, dx), -20, 20), curva / dx / 2) + recuo
    d = _suave_uniao(d_modelo, d_miolo, curva)
    d = -_suave_uniao(-d, -(d_corte[:, :, None] + 0.2), 0.8)
    d = np.maximum(d, d_plano)
    for cx, cy, r in furos:
        dist_xy = np.hypot(X[None, :] - cx, X[:, None] - cy) - r
        d = np.maximum(d, -dist_xy[:, :, None])
    d = np.pad(d, 2, constant_values=10.0)
    v, f, _, _ = marching_cubes(d, 1e-3, spacing=(dx, dx, dx))
    verts = np.column_stack([v[:, 1] + x0 - 2 * dx, v[:, 0] + y0 - 2 * dx, v[:, 2] + zs[0] - 2 * dx - plano])
    # alisa os degraus da grade sem encolher a peça (filtro de Taubin)
    bruta = trimesh.Trimesh(verts, f[:, ::-1], process=False)
    trimesh.smoothing.filter_taubin(bruta, lamb=0.5, nu=0.53, iterations=12)
    verts, faces = fast_simplification.simplify(bruta.vertices.astype(np.float32), bruta.faces, target_reduction=0.6)
    tm = trimesh.Trimesh(verts, faces, process=False)
    partes = tm.split(only_watertight=False)
    if len(partes) > 1:  # descarta sobras soltas
        tm = max(partes, key=lambda p: len(p.faces))
    if tm.volume < 0:
        tm.invert()
    return tm


def baixo_relevo(Z, dentro, dx, altura, compressao=0.6):
    """Comprime a profundidade mantendo os detalhes (método do gradiente)."""
    gy, gx = np.gradient(np.where(dentro, Z, 0), dx)
    borda = dentro & ~ndimage.binary_erosion(dentro)
    vizinho_fora = ~ndimage.binary_erosion(dentro, iterations=2)
    for g in (gx, gy):
        g[vizinho_fora] = 0
        g[np.abs(g) > 4] = 0
        g[:] = np.sign(g) * compressao * np.log1p(np.abs(g) / compressao)
    div = (np.gradient(gx, dx, axis=1) + np.gradient(gy, dx, axis=0))
    idx = -np.ones(Z.shape, int)
    pts = np.argwhere(dentro & ~borda)
    idx[tuple(pts.T)] = np.arange(len(pts))
    linhas, cols, vals = [], [], []
    b = -div[tuple(pts.T)] * dx * dx
    for k, (j, i) in enumerate(pts):
        linhas.append(k); cols.append(k); vals.append(4.0)
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            v = idx[j + dj, i + di]
            if v >= 0:
                linhas.append(k); cols.append(v); vals.append(-1.0)
    A = sparse.csr_matrix((vals, (linhas, cols)), shape=(len(pts), len(pts)))
    h = np.zeros(Z.shape)
    h[tuple(pts.T)] = spsolve(A, b)
    h -= h[dentro].min()
    h *= altura / max(h.max(), 1e-9)
    return h * dentro


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("modelo")
    ap.add_argument("saida")
    ap.add_argument("--tamanho", type=float, default=60)
    ap.add_argument("--girar", type=float, nargs=3, default=(0, 0, 0))
    ap.add_argument("--modo", choices=["inteiro", "medalha"], default="inteiro")
    ap.add_argument("--profundidade", type=float, default=25.0, help="espessura máxima da peça (mm)")
    ap.add_argument("--recuo", type=float, default=2.5)
    ap.add_argument("--curva", type=float, default=2.0)
    ap.add_argument("--ombro", type=float, help="altura (mm) abaixo da qual o busto vira oval")
    ap.add_argument("--largura", type=float, default=40.0, help="largura do oval do busto (mm)")
    ap.add_argument("--lateral", action="store_true", help="corta também nas laterais, acima dos ombros")
    ap.add_argument("--ajuste", choices=["maior", "altura"], default="maior", help="o que define a escala")
    ap.add_argument("--fundo-vaos", type=float, default=3.0, help="espessura do fundo nos vãos vazados (mm)")
    ap.add_argument("--minimo", type=float, default=2.0, help="espessura mínima de partes finas (mm)")
    ap.add_argument("--altura", type=float, default=5.0, help="só no modo medalha")
    ap.add_argument("--compressao", type=float, default=0.6, help="só no modo medalha")
    ap.add_argument("--furo", type=float, nargs=2)
    ap.add_argument("--busto", type=float, default=1.0, help="fração de cima do modelo que vira peça (0.3 = 30%%)")
    ap.add_argument("--arco", type=float, default=0.0, help="curva da base do busto (mm)")
    a = ap.parse_args()

    malha, corte_y = carregar(a.modelo, a.girar, a.tamanho, a.busto, a.ajuste)
    furos = [(a.furo[0], a.furo[1], 1.8)] if a.furo else []
    if a.modo == "inteiro":
        tm = peca_inteira(malha, a.tamanho, a.profundidade, a.recuo, a.curva, furos, corte_y, a.arco, a.minimo, a.ombro, a.largura, a.lateral, a.fundo_vaos)
    else:
        p = Peca(os.path.basename(a.saida), largura=a.tamanho + 4, altura=a.tamanho + 4, dx=0.15)
        tri = malha.vertices[malha.faces].astype(np.float64)
        z, _, cont = _camadas(tri, p.X[0, 0] - p.dx / 2, p.Y[0, 0] - p.dx / 2, p.dx, p.X.shape[1], p.X.shape[0])
        Z = np.where(cont > 0, np.where(np.isinf(z), -np.inf, z).max(axis=2), -1e9)
        dentro = ndimage.binary_opening(ndimage.binary_fill_holes(cont > 0), iterations=2)
        rel = baixo_relevo(Z, dentro, p.dx, a.altura, a.compressao)
        p.contorno(dentro)
        p.iniciar()
        p.H = p.H + rel
        p.furos = furos
        p.finalizar()
        tm = p.malha()
    tm.export(a.saida + ".stl")
    e = tm.extents
    print(f"{a.saida}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm | {len(tm.faces)} triângulos | fechada={tm.is_watertight}")


if __name__ == "__main__":
    main()
