"""Transforma um modelo 3D (STL, OBJ, GLB) em peça de relevo para molde de gesso.

A técnica é a de "baixo-relevo" usada em medalhas: olha o modelo de frente,
mede a profundidade de cada ponto e comprime essa profundidade (achata o fundo
e preserva os detalhes). O resultado continua sem contrassaída, com costas planas.

Uso:
  python relevo3d.py modelo.glb saida --tamanho 60 --girar 0 0 0 --altura 5 --furo 0 24
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


@njit(cache=True)
def _zbuffer(tri, x0, y0, dx, n, m):
    z = np.full((m, n), -1e9)
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
                if w1 >= 0 and w2 >= 0 and w3 >= 0:
                    zz = w1 * az + w2 * bz + w3 * cz
                    if zz > z[j, i]:
                        z[j, i] = zz
    return z


def carregar(caminho, girar=(0, 0, 0), tamanho=60.0):
    malha = trimesh.load(caminho, force="mesh")
    for eixo, ang in zip(np.eye(3), girar):
        if ang:
            malha.apply_transform(trimesh.transformations.rotation_matrix(np.radians(ang), eixo))
    malha.apply_translation(-malha.bounds.mean(axis=0))
    escala = tamanho / max(malha.extents[0], malha.extents[1])
    malha.apply_scale(escala)
    return malha


def baixo_relevo(Z, dentro, dx, altura, compressao=0.6):
    """Comprime a profundidade mantendo os detalhes (método do gradiente)."""
    gy, gx = np.gradient(np.where(dentro, Z, 0), dx)
    borda = dentro & ~ndimage.binary_erosion(dentro)
    vizinho_fora = ~ndimage.binary_erosion(dentro, iterations=2)
    for g in (gx, gy):
        g[vizinho_fora] = 0
        g[np.abs(g) > 4] = 0           # saltos de profundidade (uma parte na frente da outra)
        a = compressao
        g[:] = np.sign(g) * a * np.log1p(np.abs(g) / a)
    # resolve o laplaciano = divergência, com zero na borda
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
    ap.add_argument("--altura", type=float, default=5.0)
    ap.add_argument("--compressao", type=float, default=0.6)
    ap.add_argument("--furo", type=float, nargs=2)
    a = ap.parse_args()

    malha = carregar(a.modelo, a.girar, a.tamanho)
    p = Peca(os.path.basename(a.saida), largura=a.tamanho + 4, altura=a.tamanho + 4, dx=0.15)
    tri = malha.vertices[malha.faces].astype(np.float64)
    Z = _zbuffer(tri, p.X[0, 0] - p.dx / 2, p.Y[0, 0] - p.dx / 2, p.dx, p.X.shape[1], p.X.shape[0])
    dentro = Z > -1e8
    dentro = ndimage.binary_opening(ndimage.binary_fill_holes(dentro), iterations=2)
    rel = baixo_relevo(Z, dentro, p.dx, a.altura, a.compressao)
    p.contorno(dentro)
    p.iniciar()
    p.H = p.H + rel
    if a.furo:
        p.furo(*a.furo)
    p.finalizar()
    tm = p.malha()
    tm.export(a.saida + ".stl")
    from PIL import Image
    Image.fromarray(p.previa()).save(a.saida + ".png")
    e = tm.extents
    print(f"{a.saida}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm | fechada={tm.is_watertight}")


if __name__ == "__main__":
    main()
