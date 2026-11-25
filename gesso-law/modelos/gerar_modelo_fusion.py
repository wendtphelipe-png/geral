"""Gera os arquivos-modelo para o Fusion 360 (STEP): contramolde em branco do kit M, limites das 6 vagas,
6 pinos de referência e o pino D avulso. Medidas iguais às da tampa universal (tampa_kit_M.stl).

Coordenadas = posição de IMPRESSÃO e de USO do contramolde (Z para cima, fundo na mesa em Z = 0):
  costas das peças (e o batente onde a tampa assenta) em Z = 41; piso da lâmina de silicone em Z = 37;
  parede-guia até Z = 45. Vagas 1-2-3 na fileira da frente (Y negativo), da esquerda para a direita;
  4-5-6 na fileira de trás. Canto chanfrado: frente-direita. Peças de frente para baixo, cabeça para -Y.
Uso: python gerar_modelo_fusion.py pasta_saida
"""
import os
import sys

import cadquery as cq
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import molde_kit as mk  # noqa: E402

SIL_NOVO = 4.0                 # silicone nos moldes feitos no Fusion (pedido do Phelipe: 4 mm)
H = mk.FUNDO + mk.PECA_E + SIL_NOVO   # 41: plano das costas das peças / batente
EXT = mk.DEGRAU + mk.FOLGA + mk.PAREDE


def poligono(d):
    """Contorno da lâmina afastado d mm, já na posição de uso (chanfro na frente-direita)."""
    ax, ay, c = mk.AX + d, mk.AY + d, mk._chanfro(d)
    return [(-ax, ay), (ax, ay), (ax, -(ay - c)), (ax - c, -ay), (-ax, -ay)]


def prisma(d, z0, z1):
    return cq.Workplane("XY").workplane(offset=z0).polyline(poligono(d)).close().extrude(z1 - z0)


def contramolde_branco():
    corpo = prisma(EXT, 0, H)
    corpo = corpo.cut(prisma(0, H - SIL_NOVO, H + 1))                       # lâmina de silicone
    parede = prisma(EXT, H, H + mk.GUIA).cut(prisma(mk.DEGRAU + mk.FOLGA, H - 1, H + mk.GUIA + 1))
    return corpo.union(parede)


def perfil_d(wp, plano_reto_para_y_negativo=True):
    r, c = mk.PINO_RAIO if hasattr(mk, "PINO_RAIO") else 5.0, 3.0
    s = -1 if plano_reto_para_y_negativo else 1
    x = float(np.sqrt(r * r - c * c))
    return wp.moveTo(x, s * c).threePointArc((0, -s * r), (-x, s * c)).close()


def pino(cx, cy, z_costas, para_cima=True):
    """Pino D: entra 0,6 mm na peça, sai 3,4 mm (os últimos 0,6 mm chanfrados)."""
    if para_cima:   # posição de uso: peça de frente para baixo, pino para +Z, lado reto para -Y
        wp = cq.Workplane("XY").workplane(offset=z_costas - 0.6).center(cx, cy)
        corpo = perfil_d(wp, True).extrude(3.4)
        ponta = perfil_d(cq.Workplane("XY").workplane(offset=z_costas + 2.8).center(cx, cy), True).extrude(0.6, taper=45)
    else:           # peça de frente para cima (como se desenha), pino para -Z, lado reto para +Y
        wp = cq.Workplane("XY").workplane(offset=z_costas - 2.8).center(cx, cy)
        corpo = perfil_d(wp, False).extrude(3.4)
        ponta = perfil_d(cq.Workplane("XY", origin=(0, 0, z_costas - 2.8)).center(cx, cy), False).extrude(-0.6, taper=45)
    return corpo.union(ponta)


def main(sai):
    os.makedirs(sai, exist_ok=True)
    cm = contramolde_branco()
    vagas = [(cx, -cy) for cx, cy in mk.centros()]          # numeração igual à gravada na tampa
    asm = cq.Assembly(name="kit_M_modelo")
    asm.add(cm, name="contramolde_em_branco", color=cq.Color(0.67, 0.78, 0.92))
    for k, (cx, cy) in enumerate(vagas, 1):
        lim = cq.Workplane("XY").workplane(offset=H - mk.PECA_E).center(cx, cy).rect(mk.PECA_L, mk.PECA_A).extrude(mk.PECA_E)
        asm.add(lim, name=f"vaga_{k}_limite_64x82x35", color=cq.Color(1.0, 0.82, 0.25, 0.25))
        asm.add(pino(cx, cy, H, True), name=f"vaga_{k}_pino_referencia", color=cq.Color(1.0, 0.31, 0.6))
    asm.save(os.path.join(sai, "kit_M_modelo.step"))
    cq.exporters.export(cm, os.path.join(sai, "contramolde_M_em_branco.step"))
    cq.exporters.export(cm, os.path.join(sai, "contramolde_M_em_branco.stl"), tolerance=0.05)
    pa = pino(0, 0, 0, False)
    cq.exporters.export(pa, os.path.join(sai, "pino_D.step"))
    cq.exporters.export(pa, os.path.join(sai, "pino_D.stl"), tolerance=0.02)
    bb = cm.val().BoundingBox()
    print(f"contramolde em branco: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm, volume {cm.val().Volume() / 1000:.0f} cm3")
    print("vagas:", [(round(x, 1), round(y, 1)) for x, y in vagas])


if __name__ == "__main__":
    main(sys.argv[1])
