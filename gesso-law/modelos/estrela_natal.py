"""Peça-teste Gesso Law: estrela de Natal para pendurar e pintar.

Gera estrela_natal.stl (a peça-mestre que vai para a impressora 3D).
Regras de peça boa para gesso aplicadas aqui:
- costas 100% planas (a peça assenta no fundo do molde);
- laterais com ângulo de saída (o topo é menor que a base), sem nenhum "gancho"
  que prenda o gesso no molde;
- borda alta em volta (contorno para a criança pintar dentro);
- relevos baixos e arredondados, sem pontas finas que quebram;
- furo para fita, com reforço em volta.
Para mudar tamanho ou alturas, altere as medidas abaixo (em milímetros).
"""
import math
import sys
from manifold3d import CrossSection, Manifold, JoinType

RAIO_EXTERNO = 42.0   # da ponta da estrela ao centro
RAIO_INTERNO = 20.0
ESPESSURA = 7.0       # placa de base
SAIDA = 0.94          # topo da placa = 94% da base (ângulo de saída)
BORDA_LARG = 2.4
BORDA_ALT = 2.0
ARREDONDA = 3.0       # raio de arredondamento das pontas
FURO_RAIO = 2.2
FURO_Y = 24.0


def estrela(r_ext, r_int, pontas=5):
    pts = []
    for i in range(pontas * 2):
        r = r_ext if i % 2 == 0 else r_int
        a = math.pi / 2 + i * math.pi / pontas
        pts.append((r * math.cos(a), r * math.sin(a)))
    cs = CrossSection([pts])
    # arredonda as pontas: encolhe e expande com junção redonda
    return cs.offset(-ARREDONDA, JoinType.Round).offset(ARREDONDA, JoinType.Round)


def coracao(tam):
    pts = []
    for i in range(120):
        t = 2 * math.pi * i / 120
        x = 16 * math.sin(t) ** 3
        y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((x * tam / 32, y * tam / 32))
    return CrossSection([pts[::-1]])  # sentido anti-horário


def com_saida(cs, altura, escala_topo):
    return Manifold.extrude(cs, altura, scale_top=(escala_topo, escala_topo))


def circulo(r, cx=0, cy=0):
    return CrossSection.circle(r, 64).translate((cx, cy))


contorno = estrela(RAIO_EXTERNO, RAIO_INTERNO)
base = com_saida(contorno, ESPESSURA, SAIDA)

# borda em volta, já dentro do topo inclinado
topo = contorno.scale((SAIDA, SAIDA))
anel = topo - topo.offset(-BORDA_LARG, JoinType.Round)
borda = com_saida(anel, BORDA_ALT, 1.0).translate((0, 0, ESPESSURA))

# coração em relevo baixo no centro
cor = coracao(22).translate((0, -3))
relevo = com_saida(cor, 1.6, 0.92).translate((0, 0, ESPESSURA))

# reforço em volta do furo
reforco = com_saida(circulo(FURO_RAIO + 2.2, 0, FURO_Y), BORDA_ALT, 0.9).translate((0, 0, ESPESSURA))
furo = Manifold.cylinder(40, FURO_RAIO, FURO_RAIO, 48).translate((FURO_Y * 0, FURO_Y, -5))

peca = (base + borda + relevo + reforco) - furo

saida = sys.argv[1] if len(sys.argv) > 1 else "estrela_natal.stl"
malha = peca.to_mesh()
import numpy as np
import trimesh
tm = trimesh.Trimesh(vertices=np.array(malha.vert_properties)[:, :3], faces=np.array(malha.tri_verts), process=False)
tm.export(saida)
b = tm.bounds
print(f"{saida}: {b[1][0]-b[0][0]:.1f} x {b[1][1]-b[0][1]:.1f} x {b[1][2]-b[0][2]:.1f} mm, "
      f"volume {tm.volume/1000:.1f} cm3, fechada={tm.is_watertight}")
