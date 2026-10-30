# Conferência automática das páginas da fábrica de livros de colorir.
#
# Mede o que dá para medir sem "olhar" o desenho: sombra e cinza no desenho
# original, se ele foi cortado na borda, se há manchas pretas, quantas áreas
# para pintar existem e quantas são pequenas demais para a idade.
# O que depende de olhar (mão deformada, personagem parecido com o de outra
# empresa, cena sem sentido) fica com o MKT REVISOR.
import numpy as np
from scipy import ndimage as ndi

from acabamento import MM, carregar_cinza, largura_do_traco, limiar_otsu

# Área mínima de cada espaço para pintar (mm²) e espessura do traço (mm),
# por faixa de idade. Criança pequena precisa de áreas grandes e traço grosso.
IDADES = {
# max_pequenas: parte da área pintável que pode estar em espaços pequenos.
# Olhos e bochechas são pequenos mas ocupam pouco; desenho cheio de detalhe
# miúdo (o defeito comum da IA) tem boa parte da página em espaços pequenos.
    '2-4': {'area_min_mm2': 100, 'traco_mm': 2.0, 'max_pequenas': 0.05, 'max_areas': 40},
    '5-8': {'area_min_mm2': 36, 'traco_mm': 1.3, 'max_pequenas': 0.10, 'max_areas': 120},
    '9-12': {'area_min_mm2': 12, 'traco_mm': 0.8, 'max_pequenas': 0.25, 'max_areas': 400},
}


def regra_da_idade(idade):
    return IDADES.get(idade, IDADES['5-8'])


def cinza_no_original(cinza):
    """Parte do desenho que está em cinza médio fora da beirada do traço
    (sombra, degradê, preenchimento). Em livro de colorir deve ser ~0."""
    tinta = cinza < limiar_otsu(cinza)
    beirada = ndi.binary_dilation(tinta, iterations=2) & ~ndi.binary_erosion(tinta, iterations=2)
    meio_tom = (cinza > 0.25) & (cinza < 0.85) & ~beirada
    return float(meio_tom.mean())


def areas_para_pintar(final_tinta, area_min_px):
    """Espaços brancos fechados (cada um é uma área que a criança pinta),
    sem contar o fundo que encosta na borda da página. Devolve o total, quantos
    são pequenos demais e que parte da área pintável eles somam."""
    rotulos, n = ndi.label(~final_tinta)
    if not n:
        return 0, 0, 0.0
    areas = ndi.sum(np.ones_like(rotulos), rotulos, index=np.arange(1, n + 1))
    borda = set(np.unique(np.concatenate([rotulos[0], rotulos[-1], rotulos[:, 0], rotulos[:, -1]])))
    internas = [a for i, a in enumerate(areas, start=1) if i not in borda]
    pequenas = [a for a in internas if a < area_min_px]
    fracao = float(sum(pequenas) / sum(internas)) if internas else 0.0
    return len(internas), len(pequenas), fracao


def conferir(original, final, idade='5-8', medidas=None):
    """Devolve um relatório com as medidas, uma nota de 0 a 100 e os motivos
    de reprovação automática (lista vazia = passou)."""
    regra = regra_da_idade(idade)
    cinza = carregar_cinza(original) if isinstance(original, str) else original
    pagina = carregar_cinza(final) if isinstance(final, str) else final
    tinta = pagina < 0.5

    cinza_pct = cinza_no_original(cinza)
    tinta_pct = float(tinta.mean())
    traco_mm = largura_do_traco(tinta) / MM
    dist = ndi.distance_transform_edt(tinta)
    mancha_mm = float(dist.max() * 2 / MM) if tinta.any() else 0.0
    total, pequenas, fracao_pequenas = areas_para_pintar(tinta, regra['area_min_mm2'] * MM * MM)
    cortado = bool(medidas and medidas.get('cortado_na_borda'))

    motivos = []
    if cinza_pct > 0.02:
        motivos.append(f'sombra ou cinza no desenho ({cinza_pct:.1%})')
    if cortado:
        motivos.append('desenho cortado na borda da imagem original')
    if tinta_pct < 0.02:
        motivos.append('quase sem desenho')
    if tinta_pct > 0.35:
        motivos.append(f'preto demais na página ({tinta_pct:.0%})')
    if mancha_mm > regra['traco_mm'] * 4:
        motivos.append(f'mancha preta de {mancha_mm:.1f} mm')
    if total < 6:
        motivos.append(f'poucas áreas para pintar ({total})')
    if total > regra['max_areas']:
        motivos.append(f'detalhe demais para {idade} anos ({total} áreas)')
    if fracao_pequenas > regra['max_pequenas']:
        motivos.append(f'{fracao_pequenas:.0%} da área para pintar está em espaços pequenos demais para {idade} anos')

    nota = 100.0
    nota -= min(cinza_pct * 1000, 40)
    nota -= 30 if cortado else 0
    nota -= min(max(mancha_mm - regra['traco_mm'] * 2, 0) * 3, 20)
    if total:
        nota -= min(fracao_pequenas * 150, 30)
        nota -= min(max(total - regra['max_areas'], 0) * 0.2, 20)
    else:
        nota -= 50
    return {
        'idade': idade,
        'cinza_pct': round(cinza_pct, 4),
        'tinta_pct': round(tinta_pct, 4),
        'traco_mm': round(traco_mm, 2),
        'maior_mancha_mm': round(mancha_mm, 1),
        'areas_para_pintar': total,
        'areas_pequenas': pequenas,
        'area_em_pequenas_pct': round(fracao_pequenas, 3),
        'nota': round(max(nota, 0), 1),
        'motivos': motivos,
        'passou': not motivos,
    }
