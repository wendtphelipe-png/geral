"""Motor de peças em relevo para moldes de gesso (Gesso Law).

Toda peça é um "mapa de alturas": para cada ponto (x, y) existe uma única
altura z. Isso garante, por construção, que a peça não tem contrassaída
(nada prende o gesso no molde) e que as costas são planas.

Unidades em milímetros. x para a direita, y para cima.
"""
import numpy as np
from matplotlib.path import Path
from scipy import ndimage
from scipy.interpolate import splprep, splev

# Padrão único de todas as peças da coleção
BASE = 5.0       # espessura da placa de base
SAIDA = 5.0      # inclinação das paredes: sobe 5 mm a cada 1 mm (cerca de 11 graus de saída)
ARRED = 1.5      # arredondamento da quina de cima da base
FURO_R = 1.8     # furo para fita: 3,6 mm de diâmetro


def suave_min(a, b, k):
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def curva(pontos, fechada=True, n=240):
    """Curva suave que passa pelos pontos de controle."""
    p = np.array(pontos, float)
    if fechada:
        p = np.vstack([p, p[:1]])
    tck, _ = splprep([p[:, 0], p[:, 1]], s=0, per=1 if fechada else 0, k=3 if len(p) > 3 else len(p) - 1)
    x, y = splev(np.linspace(0, 1, n), tck)
    return np.column_stack([x, y])


def simetrica(meia):
    """Recebe a metade direita (de cima para baixo, x >= 0) e devolve o contorno inteiro."""
    meia = list(meia)
    esquerda = [(-x, y) for x, y in reversed(meia) if x > 1e-9]
    return meia + esquerda


class Peca:
    def __init__(self, nome, largura=64.0, altura=64.0, dx=0.2):
        self.nome = nome
        self.dx = dx
        n, m = int(round(largura / dx)), int(round(altura / dx))
        xs = (np.arange(n) + 0.5) * dx - largura / 2
        ys = (np.arange(m) + 0.5) * dx - altura / 2
        self.X, self.Y = np.meshgrid(xs, ys)
        self.silhueta = np.zeros(self.X.shape, bool)
        self.H = None
        self.tinta = []   # (máscara, cor) para a prévia pintada
        self.furos = []

    # ---------- formas 2D (máscaras) ----------
    def circulo(self, cx, cy, r):
        return (self.X - cx) ** 2 + (self.Y - cy) ** 2 <= r * r

    def elipse(self, cx, cy, rx, ry, ang=0.0):
        a = np.radians(ang)
        x, y = self.X - cx, self.Y - cy
        u = x * np.cos(a) + y * np.sin(a)
        v = -x * np.sin(a) + y * np.cos(a)
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1

    def poligono(self, pontos, suave=True):
        p = curva(pontos) if suave else np.array(pontos, float)
        caminho = Path(p)
        dentro = caminho.contains_points(np.column_stack([self.X.ravel(), self.Y.ravel()]))
        return dentro.reshape(self.X.shape)

    def dist_linha(self, pontos, suave=True, fechada=False):
        """Distância (mm) de cada ponto até uma linha."""
        p = curva(pontos, fechada=fechada, n=120) if (suave and len(pontos) > 2) else np.array(pontos, float)
        d = np.full(self.X.shape, np.inf)
        for (x0, y0), (x1, y1) in zip(p[:-1], p[1:]):
            vx, vy = x1 - x0, y1 - y0
            L = vx * vx + vy * vy or 1e-9
            t = np.clip(((self.X - x0) * vx + (self.Y - y0) * vy) / L, 0, 1)
            d = np.minimum(d, np.hypot(self.X - x0 - t * vx, self.Y - y0 - t * vy))
        return d

    def traco(self, pontos, largura, suave=True):
        return self.dist_linha(pontos, suave) <= largura / 2

    # ---------- distâncias ----------
    def _dentro(self, m):
        return ndimage.distance_transform_edt(m) * self.dx

    def _assinada(self, m):
        return (ndimage.distance_transform_edt(m) - ndimage.distance_transform_edt(~m)) * self.dx

    def _almofada(self, m, h, raio):
        """Perfil arredondado (almofada) que sobe h mm a partir da borda da forma."""
        d = self._dentro(m)
        t = np.clip(d / raio, 0, 1)
        return np.minimum(SAIDA * d, h * np.sqrt(1 - (1 - t) ** 2))

    # ---------- construção ----------
    def contorno(self, mascara):
        """Define a silhueta da peça (pode ser chamada várias vezes: soma)."""
        self.silhueta |= mascara

    def iniciar(self):
        d = self._assinada(self.silhueta)
        self.H = suave_min(SAIDA * d, np.full_like(d, BASE), ARRED)
        self.H0 = self.H.copy()

    def parte(self, m, altura, raio=4.0, cor=None):
        """Volume principal (rosto, chapéu...). Sobrepõe o que estiver embaixo."""
        m = m & self.silhueta
        self.H = np.maximum(self.H, self.H0 + self._almofada(m, altura, raio) * m)
        if cor:
            self.tinta.append((m, cor))
        return m

    def relevo(self, m, altura, raio=0.8, cor=None):
        """Detalhe em relevo somado à superfície (olho, nariz, sobrancelha)."""
        m = m & self.silhueta
        self.H = self.H + self._almofada(m, altura, raio) * m
        if cor:
            self.tinta.append((m, cor))
        return m

    def rebaixo(self, m, fundo, raio=0.6, cor=None):
        """Área rebaixada (boca aberta, narina)."""
        m = m & self.silhueta
        self.H = self.H - self._almofada(m, fundo, raio) * m
        if cor:
            self.tinta.append((m, cor))
        return m

    def sulco(self, pontos, largura=0.9, fundo=0.6, suave=True):
        """Risco em U para separar áreas de pintura."""
        d = self.dist_linha(pontos, suave)
        self.H = self.H - fundo * np.clip(1 - (d / (largura / 2)) ** 2, 0, 1)

    def furo(self, cx, cy, r=FURO_R):
        self.furos.append((cx, cy, r))

    def finalizar(self):
        self.H = ndimage.gaussian_filter(self.H, 1.0)
        for cx, cy, r in self.furos:
            dist = np.hypot(self.X - cx, self.Y - cy) - r
            self.H = np.minimum(self.H, SAIDA * dist)
        return self

    # ---------- saída ----------
    def malha(self, reducao=0.7):
        from skimage.measure import marching_cubes
        import trimesh
        dx = self.dx
        H = np.pad(self.H.astype(np.float32), 2, constant_values=-5.0)
        zs = np.arange(-1.5 * dx, H.max() + 2 * dx, dx, dtype=np.float32)
        F = np.minimum(H[..., None] - zs, zs)
        v, f, _, _ = marching_cubes(F, 1e-3, spacing=(dx, dx, dx))
        x0 = self.X[0, 0] - 2 * dx
        y0 = self.Y[0, 0] - 2 * dx
        verts = np.column_stack([v[:, 1] + x0, v[:, 0] + y0, v[:, 2] + zs[0]])
        faces = f[:, ::-1]
        if reducao:
            import fast_simplification
            verts, faces = fast_simplification.simplify(verts.astype(np.float32), faces, target_reduction=reducao)
        tm = trimesh.Trimesh(verts, faces, process=False)
        if tm.volume < 0:
            tm.invert()
        return tm

    def sombra(self, luz=(-0.45, 0.55, 0.70)):
        gy, gx = np.gradient(self.H, self.dx)
        n = np.dstack([-gx, -gy, np.ones_like(gx)])
        n /= np.linalg.norm(n, axis=2, keepdims=True)
        L = np.array(luz) / np.linalg.norm(luz)
        return np.clip(n @ L, 0, 1)

    def previa(self, pintada=False):
        """Imagem RGB vista de frente (gesso cru ou pintado)."""
        s = self.sombra()
        cor = np.ones(self.H.shape + (3,)) * np.array([0.95, 0.93, 0.89])
        if pintada:
            for m, c in self.tinta:
                cor[m] = np.array(c) / 255.0
        img = cor * (0.35 + 0.75 * s[..., None])
        img = np.clip(img, 0, 1)
        fundo = self.H <= 0.3
        img[fundo] = 1.0
        return (img[::-1] * 255).astype(np.uint8)
