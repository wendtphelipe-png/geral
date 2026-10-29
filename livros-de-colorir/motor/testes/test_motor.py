# Testes do acabamento, da conferência e da montagem (não precisam da placa).
# Rodar de dentro da pasta do motor: python -m unittest discover testes
import json
import os
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import acabamento  # noqa: E402
import conferir  # noqa: E402
import fabrica  # noqa: E402
from montar import montar  # noqa: E402


def desenho_falso(com_mancha=False, com_sombra=False, com_sujeira=False, linha=3):
    """Imita uma saída do modelo: círculos e um retângulo em traço fino,
    fundo levemente acinzentado e, opcionalmente, defeitos."""
    img = Image.new('L', (768, 1088), 245)
    d = ImageDraw.Draw(img)
    d.ellipse((150, 200, 620, 670), outline=10, width=linha)
    d.ellipse((260, 320, 380, 440), outline=10, width=linha)
    d.ellipse((400, 320, 520, 440), outline=10, width=linha)
    d.rectangle((200, 720, 570, 950), outline=10, width=linha)
    d.line((200, 835, 570, 835), fill=10, width=linha)
    d.line((385, 720, 385, 950), fill=10, width=linha)
    if com_mancha:
        d.ellipse((300, 480, 470, 600), fill=10)
    if com_sombra:
        d.rectangle((212, 732, 372, 822), fill=140)
        d.rectangle((398, 848, 558, 938), fill=140)
    arr = np.asarray(img, dtype=np.float32)
    arr += np.random.default_rng(1).normal(0, 4, arr.shape)
    if com_sujeira:
        for x, y in [(100, 100), (700, 1000), (50, 600)]:
            arr[y:y + 2, x:x + 2] = 0
    return np.clip(arr, 0, 255) / 255.0


class TestAcabamento(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def acabar(self, cinza, **kw):
        saida = os.path.join(self.tmp, 'final.png')
        medidas = acabamento.acabar(cinza, saida, **kw)
        return saida, medidas

    def test_pagina_a4_300dpi_so_preto_e_branco(self):
        saida, medidas = self.acabar(desenho_falso())
        img = Image.open(saida)
        self.assertEqual(img.size, (2480, 3508))
        self.assertEqual(round(img.info['dpi'][0]), 300)
        arr = np.asarray(img)
        # Fora a beirada suavizada do traço, só preto ou branco
        meio = ((arr > 40) & (arr < 215)).mean()
        self.assertLess(meio, 0.01)

    def test_traco_fica_na_espessura_pedida(self):
        for alvo in (0.8, 1.3, 2.0):
            _, medidas = self.acabar(desenho_falso(linha=2), traco_mm=alvo)
            self.assertAlmostEqual(medidas['traco_final_mm'], alvo, delta=alvo * 0.3)

    def test_respeita_a_margem(self):
        saida, _ = self.acabar(desenho_falso(), margem_mm=15)
        arr = np.asarray(Image.open(saida)) < 128
        m = acabamento.mm_para_px(15) - 2
        self.assertFalse(arr[:m].any() or arr[-m:].any() or arr[:, :m].any() or arr[:, -m:].any())

    def test_mancha_preta_vira_contorno(self):
        _, medidas = self.acabar(desenho_falso(com_mancha=True), traco_mm=1.3)
        self.assertGreaterEqual(medidas['manchas_esvaziadas'], 1)

    def test_sujeira_some(self):
        saida, _ = self.acabar(desenho_falso(com_sujeira=True))
        arr = np.asarray(Image.open(saida)) < 128
        from scipy import ndimage as ndi
        _, n = ndi.label(arr, structure=np.ones((3, 3)))
        # Desenho falso: 4 contornos ligados (o retângulo com a cruz é um só)
        self.assertLessEqual(n, 4)


class TestConferencia(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def conferir(self, cinza, idade='5-8'):
        saida = os.path.join(self.tmp, 'final.png')
        medidas = acabamento.acabar(cinza, saida, traco_mm=conferir.regra_da_idade(idade)['traco_mm'])
        return conferir.conferir(cinza, saida, idade, medidas)

    def test_desenho_limpo_passa(self):
        r = self.conferir(desenho_falso())
        self.assertTrue(r['passou'], r['motivos'])
        self.assertGreaterEqual(r['areas_para_pintar'], 6)

    def test_sombra_reprova(self):
        r = self.conferir(desenho_falso(com_sombra=True))
        self.assertFalse(r['passou'])
        self.assertTrue(any('cinza' in m for m in r['motivos']))

    def test_desenho_cortado_reprova(self):
        cinza = desenho_falso()
        cinza[:, :5] = 0.03  # traço encostando na borda da imagem
        r = self.conferir(cinza)
        self.assertTrue(any('cortado' in m for m in r['motivos']))


class TestFabrica(unittest.TestCase):
    def test_acabar_conferir_montar(self):
        pasta = tempfile.mkdtemp()
        roteiro = {
            'codigo': 'teste', 'titulo': 'Teste', 'idade': '5-8',
            'paginas': [{'n': 1, 'cena': 'a', 'prompt': 'a'}, {'n': 2, 'cena': 'b', 'prompt': 'b'}],
        }
        caminho = os.path.join(pasta, 'roteiro.json')
        with open(caminho, 'w', encoding='utf-8') as f:
            json.dump(roteiro, f)
        for n in (1, 2):
            p = os.path.join(pasta, 'paginas', f'{n:02d}')
            os.makedirs(p)
            Image.fromarray((desenho_falso() * 255).astype(np.uint8)).save(os.path.join(p, 'v1.png'))
            Image.fromarray((desenho_falso(com_sombra=True) * 255).astype(np.uint8)).save(os.path.join(p, 'v2.png'))

        class Args:
            paginas = None
            variacoes = None
            nao_esperar = True
        args = Args()
        args.roteiro = caminho
        fabrica.cmd_acabar(args)
        fabrica.cmd_conferir(args)
        with open(os.path.join(pasta, 'conferencia-automatica.json'), encoding='utf-8') as f:
            rel = json.load(f)
        self.assertEqual([p['sugestao'] for p in rel['paginas']], ['v1', 'v1'])
        with open(os.path.join(pasta, 'escolhas.json'), 'w') as f:
            json.dump({'1': 'v1', '2': 'v1'}, f)
        fabrica.cmd_montar(args)
        pdf = os.path.join(pasta, 'final', 'miolo.pdf')
        self.assertTrue(os.path.getsize(pdf) > 1000)

    def test_montar_conta_paginas(self):
        pasta = tempfile.mkdtemp()
        png = os.path.join(pasta, 'p.png')
        Image.new('L', (2480, 3508), 255).save(png)
        total = montar([png, png, png], os.path.join(pasta, 'm.pdf'))
        # pertence + verso, e cada desenho com verso em branco
        self.assertEqual(total, 2 + 3 * 2)


if __name__ == '__main__':
    unittest.main()
