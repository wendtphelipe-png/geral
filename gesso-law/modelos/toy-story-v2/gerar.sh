#!/bin/sh
# Gera os 6 bustos a partir dos modelos "Toy Story Series" (Model Magic, Printables, domínio público).
# Antes: baixe os .stl e separe a figura da base redonda (a peça maior do arquivo), salvando como *_fig.stl.
# O Alien usa o maior dos 3 aliens do arquivo.
R=../relevo3d.py
python3 $R woody_fig.stl woody --girar -90 0 0 --busto 0.40 --tamanho 60 --profundidade 32 \
    --ombro -12 --largura 36 --olho -7.7 6.4 2.0 --olho 0.8 6.4 2.0
python3 $R buzz_fig.stl buzz --girar -90 0 0 --busto 0.28 --tamanho 60 --ajuste altura --profundidade 28 \
    --ombro -10 --largura 58 --lateral --olho -4.75 15.75 1.6 --olho 4.0 15.75 1.6
python3 $R jessie_fig.stl jessie --girar -90 0 0 --busto 0.42 --tamanho 60 --profundidade 30 \
    --ombro -10 --largura 40 --massa 2 -6 12 6 3
python3 $R rex_fig.stl rex --girar -90 90 0 --busto 0.40 --tamanho 58 --ajuste altura --profundidade 30 \
    --remover -11 1 -31 -15 -21
python3 $R alien_fig.stl alien --girar -70 -20 0 --busto 0.62 --tamanho 62 --profundidade 30 --arco 3
python3 $R batata_fig.stl batata --girar -90 0 0 --busto 0.85 --tamanho 62 --profundidade 30 \
    --manter -2.5 -5 18.8 22 --manter -6 20 13 8 --manter -23 1 5.8 8.6 --manter 14.3 5.5 6 7.5
