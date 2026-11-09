#!/bin/sh
# Kit de Natal 2026: 8 peças para pendurar, com argola externa reforçada.
# Modelos de origem (Printables): baixe e salve como *_fig.stl (uma peça por arquivo).
R=../relevo3d.py
B="--tamanho 52 --ajuste altura --argola 5 1.6 6"
python3 $R noel_fig.stl noel --girar -90 0 0 $B --profundidade 16
python3 $R boneco_fig.stl boneco --girar -90 0 0 $B --profundidade 16
python3 $R rena_fig.stl rena --girar -90 0 0 $B --profundidade 16 --minimo 3
python3 $R pinguim_fig.stl pinguim --girar -90 0 0 $B --profundidade 26
python3 $R biscoito_fig.stl biscoito --girar -90 0 0 $B --profundidade 16
python3 $R anjo_fig.stl anjo --girar -90 0 0 $B --profundidade 34
python3 $R grinch_fig.stl grinch --girar 0 0 0 $B --profundidade 16 --minimo 3
python3 $R gato_fig.stl gato --girar -90 0 0 $B --profundidade 16
