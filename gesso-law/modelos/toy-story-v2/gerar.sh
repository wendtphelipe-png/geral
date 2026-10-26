#!/bin/sh
# Gera os 6 bustos a partir dos modelos "Toy Story Series" (Model Magic, Printables, domínio público).
# Antes: baixe os .stl e separe a figura da base redonda (a peça maior do arquivo), salvando como *_fig.stl.
# O Alien usa o maior dos 3 aliens do arquivo.
R=../relevo3d.py
python3 $R woody_fig.stl woody --girar -90 0 0 --busto 0.40 --tamanho 60 --profundidade 32 \
    --ombro -12 --largura 36 --olho -7.6 6.4 1.7 --olho 0.8 6.4 1.7
python3 $R buzz_fig.stl buzz --girar -90 0 0 --busto 0.36 --tamanho 60 --ajuste altura --profundidade 28 \
    --ombro -6 --largura 54 --lateral --placa 0 14 15 16.5 8 --olho -4.75 19.5 1.4 --olho 4.0 19.5 1.4
python3 $R jessie_fig.stl jessie --girar -90 0 0 --busto 0.42 --tamanho 60 --profundidade 30 \
    --ombro -10 --largura 40 --placa 2 -6 10 7 12
python3 $R rex_fig.stl rex --girar -80 40 0 --busto 0.40 --tamanho 58 --ajuste altura --profundidade 30 \
    --ombro -14 --largura 64 --lateral
python3 $R alien_fig.stl alien --girar -70 -20 0 --busto 0.62 --tamanho 60 --ajuste altura --profundidade 30 \
    --ombro -14 --largura 64 --lateral
python3 $R batata_fig.stl batata --girar -90 0 0 --busto 0.85 --tamanho 60 --ajuste altura --profundidade 30 \
    --ombro 0 --largura 42 --lateral
