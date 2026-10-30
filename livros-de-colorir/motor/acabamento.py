# Acabamento das páginas da fábrica de livros de colorir.
#
# Recebe o desenho que saiu do modelo (cinza, com ruído e traço irregular) e
# devolve a página pronta para imprimir:
#   - só preto e branco (nada de sombra ou cinza);
#   - sem sujeira (pontinhos soltos) nem buraquinhos dentro do traço;
#   - manchas pretas grandes viram contorno (a criança precisa pintar ali);
#   - traço da mesma espessura em todas as páginas do livro;
#   - desenho centralizado na página, com margem, em 300 dpi.
# Só usa numpy, Pillow e scipy, para rodar em qualquer computador.
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

DPI = 300
MM = DPI / 25.4  # pixels por milímetro em 300 dpi


def mm_para_px(mm):
    return int(round(mm * MM))


def carregar_cinza(caminho):
    """Imagem em tons de cinza, de 0 (preto) a 1 (branco)."""
    return np.asarray(Image.open(caminho).convert('L'), dtype=np.float32) / 255.0


def limiar_otsu(cinza):
    """Valor que melhor separa traço e fundo (método de Otsu)."""
    hist, _ = np.histogram(cinza, bins=256, range=(0, 1))
    hist = hist.astype(np.float64)
    total = hist.sum()
    if total == 0:
        return 0.5
    niveis = np.arange(256)
    peso0 = np.cumsum(hist)
    peso1 = total - peso0
    soma0 = np.cumsum(hist * niveis)
    media0 = soma0 / np.maximum(peso0, 1)
    media1 = (soma0[-1] - soma0) / np.maximum(peso1, 1)
    entre = peso0 * peso1 * (media0 - media1) ** 2
    t = int(np.argmax(entre))
    # Desenho de colorir é quase todo branco: o limiar nunca deve passar do
    # meio, senão o cinza claro do fundo vira traço.
    return min((t + 0.5) / 256, 0.6)


def largura_do_traco(tinta):
    """Espessura típica do traço, em pixels (mediana nas cristas do traço)."""
    if not tinta.any():
        return 0.0
    dist = ndi.distance_transform_edt(tinta)
    cristas = tinta & (dist >= ndi.maximum_filter(dist, size=3))
    valores = dist[cristas]
    if valores.size == 0:
        return 0.0
    return float(max(2 * np.median(valores) - 1, 1))


def tirar_sujeira(tinta, area_min_tinta, area_min_buraco):
    """Apaga manchinhas de tinta soltas e tapa furinhos dentro do traço."""
    rotulos, n = ndi.label(tinta, structure=np.ones((3, 3)))
    if n:
        areas = ndi.sum(np.ones_like(rotulos), rotulos, index=np.arange(1, n + 1))
        pequenas = np.zeros(n + 1, dtype=bool)
        pequenas[1:] = areas < area_min_tinta
        tinta = tinta & ~pequenas[rotulos]
    rotulos, n = ndi.label(~tinta)
    if n:
        areas = ndi.sum(np.ones_like(rotulos), rotulos, index=np.arange(1, n + 1))
        furos = np.zeros(n + 1, dtype=bool)
        furos[1:] = areas < area_min_buraco
        tinta = tinta | furos[rotulos]
    return tinta


def esvaziar_manchas(tinta, traco):
    """Mancha preta grande (cabelo, sombra, fundo) vira só o contorno, com a
    espessura do traço, para a criança poder pintar."""
    dist = ndi.distance_transform_edt(tinta)
    nucleo = dist > traco
    rotulos, n = ndi.label(nucleo)
    if not n:
        return tinta, 0
    areas = ndi.sum(np.ones_like(rotulos), rotulos, index=np.arange(1, n + 1))
    grandes = np.zeros(n + 1, dtype=bool)
    grandes[1:] = areas >= (2 * traco) ** 2
    miolo = grandes[rotulos]
    return tinta & ~miolo, int(grandes.sum())


def ajustar_traco(tinta, alvo):
    """Engrossa ou afina o traço até a espessura pedida (em pixels)."""
    atual = largura_do_traco(tinta)
    if atual == 0:
        return tinta, atual
    raio = (alvo - atual) / 2
    if raio > 0.5:
        return ndi.distance_transform_edt(~tinta) <= raio, atual
    if raio < -0.5:
        # Afina com cuidado: nunca a ponto de apagar a linha mais fina
        raio = min(-raio, atual / 2 - 1)
        if raio > 0.5:
            return ndi.distance_transform_edt(tinta) > raio, atual
    return tinta, atual


def caixa_do_desenho(tinta, folga):
    linhas = np.where(tinta.any(axis=1))[0]
    colunas = np.where(tinta.any(axis=0))[0]
    if linhas.size == 0:
        return 0, 0, tinta.shape[1], tinta.shape[0]
    a, b = max(linhas[0] - folga, 0), min(linhas[-1] + folga + 1, tinta.shape[0])
    e, d = max(colunas[0] - folga, 0), min(colunas[-1] + folga + 1, tinta.shape[1])
    return e, a, d, b


def cortado_na_borda(tinta, limite=0.03):
    """Desenho cortado: muita tinta encostada numa das bordas. Uma linha de
    horizonte ou de chão que atravessa a página encosta em poucos pontos e
    não conta."""
    return bool(max(tinta[0].mean(), tinta[-1].mean(), tinta[:, 0].mean(), tinta[:, -1].mean()) > limite)


def acabar(entrada, saida, largura_mm=210, altura_mm=297, margem_mm=12,
           traco_mm=1.3, esvaziar=True, sujeira_mm2=0.6):
    """Faz o acabamento de uma página e grava o PNG em 300 dpi.
    Devolve um dicionário com as medidas, usado pela conferência."""
    cinza = carregar_cinza(entrada) if isinstance(entrada, str) else entrada
    pag_l, pag_a = mm_para_px(largura_mm), mm_para_px(altura_mm)
    margem = mm_para_px(margem_mm)
    area_l, area_a = pag_l - 2 * margem, pag_a - 2 * margem

    # Recorta o desenho (com uma folguinha) e calcula a escala que faz ele
    # ocupar a área útil da página.
    tinta0 = cinza < limiar_otsu(cinza)
    e, a, d, b = caixa_do_desenho(tinta0, folga=2)
    recorte = cinza[a:b, e:d]
    escala = min(area_l / recorte.shape[1], area_a / recorte.shape[0])

    # Trabalha no dobro da resolução final: depois reduz pela metade, o que
    # deixa as curvas lisas (sem "escadinha") na impressão.
    fator = 2
    novo_l = max(int(round(recorte.shape[1] * escala * fator)), 1)
    novo_a = max(int(round(recorte.shape[0] * escala * fator)), 1)
    ampliada = np.asarray(
        Image.fromarray((recorte * 255).astype(np.uint8)).resize((novo_l, novo_a), Image.LANCZOS),
        dtype=np.float32) / 255.0
    tinta = ampliada < limiar_otsu(ampliada)

    px_mm2 = (MM * fator) ** 2
    tinta = tirar_sujeira(tinta, area_min_tinta=sujeira_mm2 * px_mm2, area_min_buraco=sujeira_mm2 * px_mm2)
    alvo = traco_mm * MM * fator
    manchas = 0
    if esvaziar:
        tinta, manchas = esvaziar_manchas(tinta, alvo)
    tinta, traco_antes = ajustar_traco(tinta, alvo)

    desenho = Image.fromarray(np.where(tinta, 0, 255).astype(np.uint8))
    desenho = desenho.resize((max(novo_l // fator, 1), max(novo_a // fator, 1)), Image.BOX)
    pagina = Image.new('L', (pag_l, pag_a), 255)
    pagina.paste(desenho, ((pag_l - desenho.width) // 2, (pag_a - desenho.height) // 2))
    if saida:
        pagina.save(saida, dpi=(DPI, DPI))

    final = np.asarray(pagina, dtype=np.float32) / 255.0
    return {
        'arquivo': saida,
        'pixels': [pag_l, pag_a],
        'traco_original_mm': round(traco_antes / (MM * fator), 2),
        'traco_final_mm': round(largura_do_traco(final < 0.5) / MM, 2),
        'manchas_esvaziadas': manchas,
        'cortado_na_borda': cortado_na_borda(tinta0),
    }
