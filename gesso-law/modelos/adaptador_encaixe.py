# Adaptador para colar nas costas das peças já impressas (Toy Story): disco fino com o pino em D.
import sys; sys.path.insert(0,'/home/user/geral/gesso-law/modelos')
from finalizar_lote import pino_d, para_trimesh
from manifold3d import Manifold
ESP=2.0; RAIO=14.0
disco=Manifold.cylinder(ESP, RAIO, RAIO, 128)          # z de 0 a 2 (lado de colar em cima)
# riscos na face de colagem para a cola agarrar melhor
for i in range(-3,4):
    disco=disco-Manifold.cube((2*RAIO+2,0.8,0.5)).translate((-RAIO-1,i*3.5-0.4,ESP-0.4))
p=disco+pino_d()
t=para_trimesh(p); t.export(sys.argv[1]); print(t.extents, t.is_watertight)
