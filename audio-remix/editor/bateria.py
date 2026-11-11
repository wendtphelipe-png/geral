"""Bateria de estilos: toca o padrão de bateria de cada estilo da biblioteca
(biblioteca/estilos.json) no BPM da música. Sons sintetizados, sem amostras
de terceiros. É a base dos "blocos de outro estilo" do mix automático.
"""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfilt

SR = 44100
BIBLIOTECA = Path(__file__).resolve().parent.parent / "biblioteca" / "estilos.json"


@lru_cache(maxsize=1)
def estilos():
    return {e["id"]: e for e in json.loads(BIBLIOTECA.read_text(encoding="utf-8"))["estilos"]}


def _env(n, ataque, queda):
    t = np.arange(n) / SR
    e = np.exp(-t / queda)
    a = int(ataque * SR)
    if a:
        e[:a] *= np.linspace(0, 1, a)
    return e


def _ruido(n, semente):
    return np.random.default_rng(semente).standard_normal(n)


def _passa(sinal, tipo, freq, ordem=2):
    return sosfilt(butter(ordem, freq, tipo, fs=SR, output="sos"), sinal)


@lru_cache(maxsize=None)
def som(nome):
    """Cada peça da bateria, mono, float32."""
    if nome == "bumbo":
        n = int(0.45 * SR); t = np.arange(n) / SR
        freq = 48 + 110 * np.exp(-t * 28)
        s = np.sin(2 * np.pi * np.cumsum(freq) / SR) * _env(n, 0.001, 0.16)
        s += 0.25 * _passa(_ruido(n, 1), "highpass", 2000) * _env(n, 0, 0.004)
        return (np.tanh(s * 1.6) * 0.9).astype(np.float32)
    if nome == "caixa":
        n = int(0.3 * SR); t = np.arange(n) / SR
        corpo = np.sin(2 * np.pi * 190 * t) * _env(n, 0, 0.05)
        chiado = _passa(_ruido(n, 2), "bandpass", [1500, 8000]) * _env(n, 0, 0.11)
        return (0.5 * corpo + 0.9 * chiado).astype(np.float32)
    if nome == "palma":
        n = int(0.28 * SR)
        r = _passa(_ruido(n, 3), "bandpass", [900, 5000])
        e = np.zeros(n)
        for k, atraso in enumerate((0, 0.009, 0.018)):
            i = int(atraso * SR)
            e[i:] += _env(n - i, 0, 0.012 if k < 2 else 0.09)
        return (r * e * 0.7).astype(np.float32)
    if nome == "chimbal":
        n = int(0.08 * SR)
        return (_passa(_ruido(n, 4), "highpass", 7000, 4) * _env(n, 0, 0.018) * 0.45).astype(np.float32)
    if nome == "chimbal_aberto":
        n = int(0.35 * SR)
        return (_passa(_ruido(n, 5), "highpass", 6500, 4) * _env(n, 0, 0.12) * 0.35).astype(np.float32)
    if nome == "shaker":
        n = int(0.09 * SR)
        return (_passa(_ruido(n, 6), "bandpass", [4000, 11000]) * _env(n, 0.01, 0.025) * 0.3).astype(np.float32)
    if nome == "ha":  # o prato "ha" do ballroom
        n = int(1.2 * SR)
        r = _passa(_ruido(n, 7), "highpass", 3500, 2)
        return (r * _env(n, 0.002, 0.35) * 0.55).astype(np.float32)
    if nome == "impacto":  # boom grave do krump
        n = int(1.0 * SR); t = np.arange(n) / SR
        freq = 38 + 70 * np.exp(-t * 12)
        s = np.sin(2 * np.pi * np.cumsum(freq) / SR) * _env(n, 0.001, 0.4)
        s += 0.4 * _passa(_ruido(n, 8), "lowpass", 1200) * _env(n, 0, 0.12)
        return (np.tanh(s * 2.2) * 0.85).astype(np.float32)
    if nome in ("tambor", "log_drum"):  # tamborzão / log drum do amapiano
        n = int(0.35 * SR); t = np.arange(n) / SR
        base = 95 if nome == "tambor" else 62
        freq = base * (1 + 0.6 * np.exp(-t * 30))
        s = np.sin(2 * np.pi * np.cumsum(freq) / SR) * _env(n, 0.001, 0.12 if nome == "tambor" else 0.22)
        return (np.tanh(s * 1.8) * 0.75).astype(np.float32)
    raise KeyError(nome)


NIVEL = {"bumbo": 1.0, "caixa": 0.8, "palma": 0.8, "chimbal": 0.7, "shaker": 0.6, "ha": 0.7,
         "impacto": 0.9, "tambor": 0.8, "log_drum": 0.85}
PAN = {"chimbal": 0.25, "shaker": -0.3, "palma": 0.1, "tambor": -0.15}


def tocar(estilo, bpm, batidas):
    """Áudio estéreo (2, n) com o padrão do estilo por `batidas` batidas, no BPM dado."""
    e = estilos()[estilo]
    passo = 60.0 / float(bpm) / 4  # 16 passos por compasso de 4 batidas
    swing = float(e.get("swing", 0.5))
    n = int(round(batidas * 4 * passo * SR))
    saida = np.zeros((2, n + SR), np.float32)
    padrao = dict(e["padrao"])
    if estilo == "house" and "chimbal" in padrao:  # house: chimbal aberto no contratempo
        padrao["chimbal_aberto"] = padrao.pop("chimbal")
    passos_total = int(round(batidas * 4))
    for peca, desenho in padrao.items():
        nome = "chimbal_aberto" if peca == "chimbal_aberto" else peca
        if nome not in ("bumbo", "caixa", "palma", "chimbal", "chimbal_aberto", "shaker", "ha", "impacto", "tambor", "log_drum"):
            continue
        amostra = som(nome) * NIVEL.get(peca if peca != "chimbal_aberto" else "chimbal", 0.7)
        p = PAN.get(peca, 0.0)
        lados = np.array([[1 - max(0, p)], [1 + min(0, p)]], np.float32)
        for k in range(passos_total):
            if desenho[k % 16] != "x":
                continue
            t = k * passo + ((swing - 0.5) * 2 * passo if k % 2 else 0)
            i = int(t * SR)
            # leve variação de força deixa menos "robótico"
            forca = 1.0 if k % 4 == 0 else 0.86
            fim = min(i + len(amostra), saida.shape[1])
            saida[:, i:fim] += amostra[: fim - i] * forca * lados
    saida = saida[:, :n]
    pico = float(np.abs(saida).max()) or 1
    return (saida * (0.55 / pico)).astype(np.float32)


def sugerir_estilo(bpm):
    """Estilo cuja faixa de BPM inclui o BPM dado (o mais próximo do ideal)."""
    candidatos = [(abs(e["bpm_ideal"] - bpm), i) for i, e in estilos().items() if e["bpm"][0] - 3 <= bpm <= e["bpm"][1] + 3]
    if not candidatos:
        candidatos = [(abs(e["bpm_ideal"] - bpm), i) for i, e in estilos().items()]
    return min(candidatos)[1]
