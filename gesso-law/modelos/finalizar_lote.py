"""Finaliza um lote de peças para a resina: escala máxima para a Elegoo Mars 5,
pino de encaixe em D nas costas e arquivos com 2 peças por mesa.

Uso:
  python finalizar_lote.py pasta_entrada pasta_saida peca1 peca2 [peca3 ...]
  (as peças vão em pares, na ordem dada: 1+2, 3+4, ...)

Entrada: <pasta_entrada>/<peca>.stl, costas em z = 0 e frente para +z.
Saída:   <pasta_saida>/<peca>.stl (peça final com pino) e <pasta_saida>/mesa_<a>_<b>.stl.

Todas as peças do lote recebem a MESMA escala (a maior que faz todos os pares
caberem na mesa), para a coleção ficar uniforme e os moldes padronizados.
"""
import os
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold, Mesh

# Elegoo Mars 5: área útil 143,43 x 89,6 mm (altura 150 mm)
MESA_X, MESA_Y = 143.4, 89.6
MARGEM = 4.0          # sobra para a base dos suportes (raft) em volta
VAO = 6.0             # espaço entre as duas peças

# Pino de encaixe em D (padrão de todas as coleções)
PINO_RAIO = 5.0       # 10 mm de diâmetro
PINO_CORTE = 3.0      # lado reto do D, a 3 mm do centro (virado para o topo da peça)
PINO_ALTURA = 4.0
PINO_ENTRA = 0.6      # quanto o pino entra na peça, para ficar soldado nela


def pino_d():
    circ = CrossSection.circle(PINO_RAIO, 96)
    corte = CrossSection.square((2 * PINO_RAIO + 2, 2 * PINO_RAIO + 2)).translate((-PINO_RAIO - 1, PINO_CORTE))
    d = circ - corte
    # ponta levemente afunilada (chanfro) para entrar sem forçar
    corpo = Manifold.extrude(d, PINO_ALTURA - 0.6)
    ponta = Manifold.extrude(d, 0.6, scale_top=(0.88, 0.88)).translate((0, 0, PINO_ALTURA - 0.6))
    p = corpo + ponta
    # vira para baixo: do z = +PINO_ENTRA até z = -PINO_ALTURA
    return p.mirror((0, 0, 1)).translate((0, 0, PINO_ENTRA))


def para_manifold(tm):
    return Manifold(Mesh(vert_properties=np.asarray(tm.vertices, np.float32),
                         tri_verts=np.asarray(tm.faces, np.uint32)))


def para_trimesh(m):
    mm = m.to_mesh()
    return trimesh.Trimesh(np.asarray(mm.vert_properties)[:, :3], np.asarray(mm.tri_verts), process=False)


def lugar_do_pino(tm):
    """Ponto das costas mais perto do centro onde o D inteiro cabe com folga."""
    secao = tm.section(plane_origin=[0, 0, 0.4], plane_normal=[0, 0, 1])
    poli, para3d = secao.to_2D()
    area = max(poli.polygons_full, key=lambda p: p.area)
    folga = area.buffer(-(PINO_RAIO + 1.5))
    if folga.is_empty:
        raise SystemExit("costas pequenas demais para o pino")
    alvo = area.centroid
    from shapely.ops import nearest_points
    p = nearest_points(folga, alvo)[0] if not folga.contains(alvo) else alvo
    xyz = trimesh.transform_points([[p.x, p.y, 0]], para3d)[0]
    return xyz[0], xyz[1]


def caber(a, b):
    """Maior escala para o par (a, b) na mesa; testa as peças em pé ou deitadas."""
    W, H = MESA_X - 2 * MARGEM, MESA_Y - 2 * MARGEM
    melhor = (0, None)
    for ra in (0, 90):
        for rb in (0, 90):
            wa, ha = (a[0], a[1]) if ra == 0 else (a[1], a[0])
            wb, hb = (b[0], b[1]) if rb == 0 else (b[1], b[0])
            s = min((W - VAO) / (wa + wb), H / max(ha, hb))
            if s > melhor[0]:
                melhor = (s, (ra, rb))
    return melhor


def main():
    ent, sai, nomes = sys.argv[1], sys.argv[2], sys.argv[3:]
    os.makedirs(sai, exist_ok=True)
    pecas = {n: trimesh.load(os.path.join(ent, n + ".stl")) for n in nomes}
    pares = [nomes[i:i + 2] for i in range(0, len(nomes), 2)]
    escalas = [caber(pecas[a].extents, pecas[b].extents) for a, b in pares]
    s = min(e[0] for e in escalas)
    print(f"escala do lote: {s:.3f}x")
    finais = {}
    for n, tm in pecas.items():
        tm = tm.copy()
        tm.apply_scale(s)
        b = tm.bounds
        tm.apply_translation([-(b[0, 0] + b[1, 0]) / 2, -(b[0, 1] + b[1, 1]) / 2, -b[0, 2]])
        cx, cy = lugar_do_pino(tm)
        final = para_manifold(tm) + pino_d().translate((cx, cy, 0))
        f = para_trimesh(final)
        f.export(os.path.join(sai, n + ".stl"))
        finais[n] = f
        e = tm.extents
        print(f"{n}: {e[0]:.1f} x {e[1]:.1f} x {e[2]:.1f} mm (+ pino de {PINO_ALTURA:.0f} mm) | "
              f"fechada={f.is_watertight} | gesso ~{tm.volume / 1000 * 1.3:.0f} g")
    for (a, b), (_, (ra, rb)) in zip(pares, escalas):
        ma, mb = finais[a].copy(), finais[b].copy()
        for m, r in ((ma, ra), (mb, rb)):
            if r:
                m.apply_transform(trimesh.transformations.rotation_matrix(np.radians(r), [0, 0, 1]))
            m.apply_translation(-m.bounds[0])
        mb.apply_translation([ma.extents[0] + VAO, 0, 0])
        mesa = trimesh.util.concatenate([ma, mb])
        mesa.apply_translation([-mesa.bounds.mean(axis=0)[0], -mesa.bounds.mean(axis=0)[1], 0])
        mesa.export(os.path.join(sai, f"mesa_{a}_{b}.stl"))
        e = mesa.extents
        print(f"mesa {a} + {b}: {e[0]:.1f} x {e[1]:.1f} mm (mesa da Mars 5: {MESA_X} x {MESA_Y})")


if __name__ == "__main__":
    main()
