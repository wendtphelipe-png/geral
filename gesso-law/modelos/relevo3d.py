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
                    cont[j, i] += 1
    return z, cont


@njit(cache=True)
def _ocupacao(z, cont, zs):
    m, n = cont.shape
    occ = np.zeros((m, n, zs.shape[0]), np.bool_)
    for j in range(m):
        for i in range(n):
            c = cont[j, i]
            if c < 2:
                continue
            v = np.sort(z[j, i, :c])
            # remove cruzamentos repetidos (aresta compartilhada por dois triângulos)
            u = np.empty(c)
            k = 0
            for q in range(c):
                if k == 0 or v[q] - u[k - 1] > 1e-6:
                    u[k] = v[q]
                    k += 1
            for p in range(0, k - 1, 2):
                for s in range(zs.shape[0]):
                    if u[p] <= zs[s] <= u[p + 1]:
                        occ[j, i, s] = True
    return occ


def carregar(caminho, girar=(0, 0, 0), tamanho=60.0):
    malha = trimesh.load(caminho, force="mesh")
    for eixo, ang in zip(np.eye(3), girar):
        if ang:
            malha.apply_transform(trimesh.transformations.rotation_matrix(np.radians(ang), eixo))
    malha.apply_translation(-malha.bounds.mean(axis=0))
    malha.apply_scale(tamanho / max(malha.extents[0], malha.extents[1]))
    return malha


def _dist(occ, dx):
    """Distância com sinal: negativa dentro, positiva fora (mm)."""
    return (ndimage.distance_transform_edt(~occ) - ndimage.distance_transform_edt(occ)) * dx


def _suave_uniao(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def peca_inteira(malha, tamanho, profundidade, recuo, curva, furos, dx=0.25):
    from skimage.measure import marching_cubes
    import fast_simplification
    lado = tamanho + 6
    n = int(round(lado / dx))
    x0 = y0 = -lado / 2
    tri = malha.vertices[malha.faces].astype(np.float64)
    z, cont = _camadas(tri, x0, y0, dx, n, n)
    frente = malha.bounds[1, 2]
    plano = max(frente - profundidade, malha.bounds[0, 2])
    zs = np.arange(plano - 2 * dx, frente + 3 * dx, dx)
    occ = _ocupacao(z, cont, zs)
    occ[:, :, zs < plano] = False
    occ = ndimage.binary_closing(occ, iterations=1)

    d_modelo = ndimage.gaussian_filter(np.clip(_dist(occ, dx), -4, 4), 1.3)
    d_plano = np.broadcast_to((plano - zs)[None, None, :], d_modelo.shape)
    # miolo de suporte: tudo o que é visto de frente, preenchido até as costas,
    # recuado da superfície e arredondado
    alcance = np.maximum.accumulate(occ[:, :, ::-1], axis=2)[:, :, ::-1]
    alcance &= (zs >= plano)[None, None, :]
    d_miolo = ndimage.gaussian_filter(np.clip(_dist(alcance, dx), -20, 20), curva / dx / 2) + recuo
    d = _suave_uniao(d_modelo, d_miolo, curva)
    d = np.maximum(d, d_plano)
    X = (np.arange(n) + 0.5) * dx + x0
    for cx, cy, r in furos:
        dist_xy = np.hypot(X[None, :] - cx, X[:, None] - cy) - r
        d = np.maximum(d, -dist_xy[:, :, None])
    d = np.pad(d, 2, constant_values=10.0)
    v, f, _, _ = marching_cubes(d, 1e-3, spacing=(dx, dx, dx))
    verts = np.column_stack([v[:, 1] + x0 - 2 * dx, v[:, 0] + y0 - 2 * dx, v[:, 2] + zs[0] - 2 * dx - plano])
    verts, faces = fast_simplification.simplify(verts.astype(np.float32), f[:, ::-1], target_reduction=0.6)
    tm = trimesh.Trimesh(verts, faces, process=False)
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
    ap.add_argument("--altura", type=float, default=5.0, help="só no modo medalha")
    ap.add_argument("--compressao", type=float, default=0.6, help="só no modo medalha")
    ap.add_argument("--furo", type=float, nargs=2)
    a = ap.parse_args()

    malha = carregar(a.modelo, a.girar, a.tamanho)
    furos = [(a.furo[0], a.furo[1], 1.8)] if a.furo else []
    if a.modo == "inteiro":
        tm = peca_inteira(malha, a.tamanho, a.profundidade, a.recuo, a.curva, furos)
    else:
        p = Peca(os.path.basename(a.saida), largura=a.tamanho + 4, altura=a.tamanho + 4, dx=0.15)
        tri = malha.vertices[malha.faces].astype(np.float64)
        z, cont = _camadas(tri, p.X[0, 0] - p.dx / 2, p.Y[0, 0] - p.dx / 2, p.dx, p.X.shape[1], p.X.shape[0])
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
