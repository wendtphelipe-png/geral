# Montagem do miolo do livro em PDF.
#
# Ordem: página "Este livro pertence a", depois cada desenho seguido de um
# verso em branco (a tinta da canetinha não estraga o desenho de trás), e uma
# página final opcional (convite para o site, QR code etc.).
import os

from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

TEXTOS = {
    'pt': 'Este livro pertence a',
    'en': 'This book belongs to',
    'es': 'Este libro pertenece a',
}


def pagina_pertence(c, largura, altura, idioma, imagem=None):
    if imagem and os.path.exists(imagem):
        c.drawImage(ImageReader(imagem), 0, 0, largura, altura)
    c.setFont('Helvetica-Bold', 30)
    c.drawCentredString(largura / 2, altura * 0.62, TEXTOS.get(idioma, TEXTOS['pt']))
    c.setLineWidth(1.5)
    c.line(largura * 0.15, altura * 0.5, largura * 0.85, altura * 0.5)
    c.showPage()


def montar(paginas, saida, largura_mm=210, altura_mm=297, titulo='', autor='',
           idioma='pt', verso_branco=True, pertence=True, pertence_imagem=None, final=None):
    """paginas: lista de PNGs na ordem do livro. Devolve o número de páginas do PDF."""
    largura, altura = largura_mm * mm, altura_mm * mm
    c = canvas.Canvas(saida, pagesize=(largura, altura))
    c.setTitle(titulo)
    c.setAuthor(autor)
    total = 0
    if pertence:
        pagina_pertence(c, largura, altura, idioma, pertence_imagem)
        total += 1
        if verso_branco:
            c.showPage()
            total += 1
    for arquivo in paginas:
        c.drawImage(ImageReader(arquivo), 0, 0, largura, altura)
        c.showPage()
        total += 1
        if verso_branco:
            c.showPage()
            total += 1
    if final and os.path.exists(final):
        c.drawImage(ImageReader(final), 0, 0, largura, altura)
        c.showPage()
        total += 1
    c.save()
    return total
