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
    centro[2] = v[:, 2].max()  # frente da parte recortada em z = 0
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


def _degrau(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


def esculpir_olhos(d, Xg, Yg, zs, dx, olhos):
    """Íris em "pratinho" côncavo com um ponto de brilho em relevo (a pupila fica para a pintura).

    olhos: lista de (x, y, raio_da_íris) em mm, já na posição para onde o olho olha.
    O rebaixo acompanha a curva do olho (desloca a superfície para dentro).
    """
    dentro = d < 0
    tem = dentro.any(axis=2)
    zf = np.where(tem, zs[len(zs) - 1 - np.argmax(dentro[:, :, ::-1], axis=2)], -1e9)
    prof = np.zeros(Xg.shape, np.float32)
    for cx, cy, r in olhos:
        rr = np.hypot(Xg - cx, Yg - cy)
        # íris: um "pratinho" côncavo (mais fundo no meio), borda bem definida
        t = np.clip(rr / r, 0, 1)
        iris = _degrau((r - rr) / 0.2) * (0.25 + 0.25 * (1 - t * t))
        # pontinho de brilho que fica em relevo dentro da íris
        brilho = _degrau((0.2 * r - np.hypot(Xg - (cx + 0.35 * r), Yg - (cy + 0.35 * r))) / 0.1)
        prof = np.maximum(prof, iris * (1 - brilho))
    perto = _degrau(1 - (zf[:, :, None] - zs[None, None, :]) / 1.5)   # só perto da frente
    return d + prof[:, :, None] * perto


def dar_massa(d, Xg, Yg, zs, dx, regioes):
    """Preenche vãos vistos de frente (pescoço fino, vão entre cabeça e gola) dentro de regiões
    ovais, como massa de modelar alisada. Nunca põe material na frente de uma parte que já existe:
    só sobe o fundo dos vãos estreitos até a altura das bordas em volta.

    regioes: (x, y, raio_x, raio_y, raio) em mm; vãos mais estreitos que 2 x raio são preenchidos.
    """
    dentro = d < 0
    tem = dentro.any(axis=2)
    zf = np.where(tem, zs[len(zs) - 1 - np.argmax(dentro[:, :, ::-1], axis=2)], zs[0])
    for cx, cy, rx, ry, r in regioes:
        oval = np.hypot((Xg - cx) / rx, (Yg - cy) / ry) <= 1
        k = int(round(r / dx))
        disco = np.hypot(*np.mgrid[-k:k + 1, -k:k + 1]) <= k
        hc = ndimage.grey_closing(zf, footprint=disco)
        hc = ndimage.gaussian_filter(hc, 1.0 / dx)
        novo = oval & (hc > zf + 0.3)
        if not novo.any():
            continue
        preencher = novo[:, :, None] & (zs[None, None, :] <= hc[:, :, None])
        d_fill = ndimage.gaussian_filter(_dist(np.pad(preencher, 3), dx), 1.0)[3:-3, 3:-3, 3:-3]
        d = _suave_uniao(d, d_fill, 1.0)
    return d


def fundir(d, Xg, Yg, dx, regioes):
    """Une partes vizinhas (orelha e cabeça, aba do chapéu e testa) com uma curva arredondada,
    como uma solda alisada, só dentro de regiões ovais.

    regioes: (x, y, raio_x, raio_y, raio_da_curva) em mm.
    """
    for cx, cy, rx, ry, r in regioes:
        oval = np.hypot((Xg - cx) / rx, (Yg - cy) / ry) <= 1
        peso = ndimage.gaussian_filter(oval.astype(np.float32), 1.0 / dx)[:, :, None]
        m = int(np.ceil(r / dx)) + 3
        inchado = np.pad(d < r, m, constant_values=False)
        d_fech = ndimage.gaussian_filter(_dist(inchado, dx) + r, 1.0)[m:-m, m:-m, m:-m]
        d = np.minimum(d, peso * d_fech + (1 - peso) * d)
    return d


def peca_inteira(malha, tamanho, profundidade, recuo, curva, furos, corte_y=-1e9, arco=0.0, minimo=2.0, ombro=None, largura=40.0, lateral=False, fundo_vaos=3.0, placas=(), olhos=(), manter_ovais=(), massa=(), remover=(), fundir_reg=(), dx=0.2):
    from skimage.measure import marching_cubes
    import fast_simplification
    lado = tamanho + 6
    n = int(round(lado / dx))
    x0 = y0 = -lado / 2
    tri = malha.vertices[malha.faces].astype(np.float64)
    z, sen, cont = _camadas(tri, x0, y0, dx, n, n)
    X = (np.arange(n) + 0.5) * dx + x0
    # recorte do busto: base em arco (mais baixa no meio, sobe nas laterais)
    fundo = corte_y + arco * (X[None, :] / (tamanho / 2)) ** 2
    manter = X[:, None] >= fundo
    if ombro is not None:
        # abaixo da linha dos ombros, só o que está dentro de um contorno oval (corta braços soltos)
        oval = (X[None, :] / (largura / 2)) ** 2 + ((X[:, None] - ombro) / max(ombro - corte_y, 1)) ** 2 <= 1
        manter &= (X[:, None] >= ombro) | oval
        if lateral:
            manter &= np.abs(X[None, :]) <= largura / 2
    if manter_ovais:
        # recorte livre: fica só o que estiver dentro de algum dos ovais
        manter = np.zeros_like(manter)
        for cx, cy, rx, ry in manter_ovais:
            manter |= ((X[None, :] - cx) / rx) ** 2 + ((X[:, None] - cy) / ry) ** 2 <= 1
    # a frente é o ponto mais à frente DENTRO do recorte (um braço cortado fora não conta)
    zz = np.where(np.isfinite(z), z, -np.inf).max(axis=2)
    frente = zz[manter & (cont > 0)].max()
    # com remoção, a frente final fica mais funda: reserva espaço até o z mais fundo das caixas
    fundo_rem = min((r[4] for r in remover), default=frente)
    plano = max(min(frente, fundo_rem) - profundidade, malha.bounds[0, 2])
    zs = np.arange(plano - 2 * dx, frente + 3 * dx, dx, dtype=np.float64)
    frac = _ocupacao(z, sen, cont, zs, dx)
    del z, sen, zz
    if remover:
        # retira partes que ficam na frente (ex.: um braço) e mede a frente de novo
        for bx0, bx1, by0, by1, bz in remover:
            caixa = ((X[None, :] >= bx0) & (X[None, :] <= bx1) & (X[:, None] >= by0) & (X[:, None] <= by1))
            # z positivo-ou-zero relativo: apaga o que está à frente de bz; com bz < -500, apaga o que
            # está atrás de (bz + 1000) (ex.: -1029 apaga atrás de z = -29)
            if bz < -500:
                frac[caixa[:, :, None] & (zs < bz + 1000)[None, None, :]] = 0
            else:
                frac[caixa[:, :, None] & (zs > bz)[None, None, :]] = 0
        ocupado = (frac > 0.5) & manter[:, :, None]
        frente = zs[np.nonzero(ocupado.any(axis=(0, 1)))[0].max()]
        plano = frente - profundidade
    frac[:, :, zs < plano] = 0
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
    Yg, Xg = np.meshgrid(X, X, indexing="ij")
    for cx, cy, rx, ry, esp in placas:
        # placa de reforço oval atrás de uma região (dá massa a cabeças estreitas)
        q = np.hypot((Xg - cx) / rx, (Yg - cy) / ry)
        d_oval = (q - 1) * min(rx, ry)
        d_placa = np.maximum(d_oval[:, :, None], (zs - (plano + esp))[None, None, :])
        d_placa = ndimage.gaussian_filter(d_placa, 1.5 / dx / 2)
        d = _suave_uniao(d, d_placa, 1.5)
    if massa:
        d = dar_massa(d, Xg, Yg, zs, dx, massa)
    if fundir_reg:
        d = fundir(d, Xg, Yg, dx, fundir_reg)
    if olhos:
        d = esculpir_olhos(d, Xg, Yg, zs, dx, olhos)
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
    ap.add_argument("--altura-final", type=float, help="amplia/reduz a peça pronta para esta altura (mm)")
    ap.add_argument("--olho", type=float, nargs=3, action="append", default=[],
                    help="x y raio da íris (mm); repita para cada olho")
    ap.add_argument("--manter", type=float, nargs=4, action="append", default=[],
                    help="x y raio_x raio_y (mm): recorte livre, fica só o que está dentro dos ovais")
    ap.add_argument("--massa", type=float, nargs=5, action="append", default=[],
                    help="x y raio_x raio_y raio (mm): preenche reentrâncias dentro do oval")
    ap.add_argument("--fundir", type=float, nargs=5, action="append", default=[],
                    help="x y raio_x raio_y raio (mm): une partes vizinhas com curva arredondada dentro do oval")
    ap.add_argument("--remover", type=float, nargs=5, action="append", default=[],
                    help="x0 x1 y0 y1 z (mm): apaga o que estiver na caixa e à frente de z (ex.: um braço)")
    ap.add_argument("--placa", type=float, nargs=5, action="append", default=[],
                    help="x y raio_x raio_y espessura (mm): reforço oval atrás de uma região")
    ap.add_argument("--busto", type=float, default=1.0, help="fração de cima do modelo que vira peça (0.3 = 30%%)")
    ap.add_argument("--arco", type=float, default=0.0, help="curva da base do busto (mm)")
    a = ap.parse_args()

    malha, corte_y = carregar(a.modelo, a.girar, a.tamanho, a.busto, a.ajuste)
    furos = [(a.furo[0], a.furo[1], 1.8)] if a.furo else []
    if a.modo == "inteiro":
        tm = peca_inteira(malha, a.tamanho, a.profundidade, a.recuo, a.curva, furos, corte_y, a.arco, a.minimo, a.ombro, a.largura, a.lateral, a.fundo_vaos, a.placa, a.olho, a.manter, a.massa, a.remover, a.fundir)
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
    if a.altura_final:
        tm.apply_scale(a.altura_final / tm.extents[1])
    tm.export(a.saida + ".stl")
    e = tm.extents
    print(f"{a.saida}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm | {len(tm.faces)} triângulos | fechada={tm.is_watertight}")


if __name__ == "__main__":
    main()
