#!/bin/sh
# Gera os 6 bustos a partir dos modelos "Toy Story Series" (Model Magic, Printables, domínio público).
# Antes: baixe os .stl e separe a figura da base redonda (a peça maior do arquivo), salvando como *_fig.stl.
# O Alien usa o maior dos 3 aliens do arquivo.
R=../relevo3d.py
python3 $R woody_fig.stl woody --girar -90 0 0 --busto 0.34 --tamanho 60 --profundidade 32 \
    --ombro -20 --largura 34
python3 $R buzz_fig.stl buzz --girar -90 0 0 --busto 0.28 --tamanho 60 --ajuste altura --profundidade 28 \
    --ombro -10 --largura 58 --lateral
python3 $R jessie_fig.stl jessie --girar -90 0 0 --busto 0.35 --tamanho 60 --profundidade 38 \
    --manter -1 15 30 11 --manter 0 -1 16 14 --manter 2 -17 10 5 --manter 20 -12 12 8 --fundir 14 -16.5 9 3 2.0
python3 $R rex_fig.stl rex --girar -90 90 0 --busto 0.40 --tamanho 58 --ajuste altura --profundidade 30 \
    --remover -11 1 -31 -15 -21
python3 $R alien_fig.stl alien --girar -70 -20 0 --busto 0.62 --tamanho 62 --profundidade 30 --arco 3
python3 $R batata_fig.stl batata --girar -90 0 0 --busto 0.85 --tamanho 62 --profundidade 28.6 --curva 3.5 \
    --manter -2.3 -7 18.3 22.5 --manter -6 20.5 13 7 --manter -22.5 1.2 6.4 8.6 --manter 14.5 6.5 6 8.4 \
    --remover 15.2 19 -9.5 -1.8 -100 --remover -27 -19.8 -13.5 -7.6 -100 --remover -34 34 -40 -26.5 -100 \
    --massa -17 1.5 2.5 8 2.5 --massa 10 6.5 2.5 7.5 2.5 --altura-final 60
