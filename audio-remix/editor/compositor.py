"""Motor de estilos do PC: toca um padrão de bateria e de baixo de um estilo em cima da música.

Grátis e local. Junta três coisas:
- os padrões (biblioteca/padroes.json, ou compostos pelo Claude pela cota da assinatura);
- a harmonia da música tempo a tempo (harmonia.py): o baixo do padrão é escrito em funções
  (tônica, quinta, oitava, nota da música...) e vira as notas certas de cada tempo, então fica
  afinado por construção;
- o kit da própria música (kit.py): o mesmo bumbo, a mesma caixa, o mesmo timbre de baixo.

A grade de tempo vem das batidas reais da música dentro da seleção (não de um metrônomo ideal),
e o "1" do padrão cai no "1" de cada oito.
"""
import json
import random
from functools import lru_cache
from pathlib import Path

import numpy as np

import bateria
import harmonia
import motor

SR = motor.SR
BIBLIOTECA = Path(__file__).resolve().parent.parent / "biblioteca" / "padroes.json"
PECAS = ["bumbo", "caixa", "palma", "chimbal", "chimbal_aberto", "shaker", "ha", "impacto", "tambor", "log_drum"]
FUNCOES = ["T", "5", "8", "3", "b7", "6", "N", "A"]
FORCA = {"X": 1.0, "x": 0.8, "o": 0.45}
NIVEL = {"bumbo": 1.0, "caixa": 0.85, "palma": 0.7, "chimbal": 0.45, "chimbal_aberto": 0.4, "shaker": 0.3,
         "ha": 0.6, "impacto": 0.9, "tambor": 0.7, "log_drum": 0.6}
DO_KIT = {"bumbo": "bumbo", "caixa": "caixa", "chimbal": "chimbal"}  # peças que vêm da própria música


@lru_cache(maxsize=1)
def biblioteca():
    return json.loads(BIBLIOTECA.read_text(encoding="utf-8"))["estilos"]


def validar(padrao):
    """Confere um padrão (da biblioteca ou do Claude). Devolve o padrão limpo ou levanta ValueError."""
    if not isinstance(padrao, dict):
        raise ValueError("padrão inválido")
    bat = {}
    for peca, desenho in (padrao.get("bateria") or {}).items():
        if peca in PECAS and isinstance(desenho, str) and len(desenho) in (16, 32) and set(desenho) <= set(".xXo"):
            bat[peca] = desenho
    notas = []
    for item in padrao.get("baixo") or []:
        if not (isinstance(item, (list, tuple)) and len(item) == 4):
            continue
        passo, funcao, dur, forca = item
        if isinstance(passo, (int, float)) and 0 <= passo < 32 and funcao in FUNCOES and isinstance(dur, (int, float)) \
                and 1 <= dur <= 32 and isinstance(forca, (int, float)):
            notas.append([int(passo), funcao, int(dur), float(min(1.0, max(0.1, forca)))])
    if not bat and not notas:
        raise ValueError("o padrão não tem bateria nem baixo")
    return {"nome": str(padrao.get("nome") or "Padrão")[:60], "bateria": bat, "baixo": sorted(notas)}


def padroes_do_estilo(estilo):
    """Lista de padrões completos (bateria + baixo) da biblioteca: a variação k da bateria com a k do baixo."""
    e = biblioteca()[estilo]
    lista = []
    for k, bat in enumerate(e["bateria"]):
        baixo = e["baixo"][k % len(e["baixo"])]
        lista.append(validar({"nome": f"{bat['nome']} + {baixo['nome'].lower()}",
                              "bateria": {p: d for p, d in bat.items() if p != "nome"}, "baixo": baixo["notas"]}))
    return lista


# ---------------------------------------------------------------- tempo

def grade(proj, blocos):
    """Batidas da seleção na linha do tempo: [(t relativo ao começo da seleção, duração, índice da batida
    na música, posição no oito 0-7)]. `blocos`: [{u, de, ate, vel}] na ordem da linha do tempo."""
    batidas = np.array(proj.analise["batidas"])
    d = proj.analise.get("deslocamento", 0)
    passo_medio = float(np.median(np.diff(batidas)))
    saida, acumulado = [], 0.0
    for b in blocos:
        u = proj.unidades[b["u"]]
        tam = (u["fim"] - u["ini"]) / SR
        s0 = u["ini"] / SR + tam * float(b.get("de", 0))
        s1 = u["ini"] / SR + tam * float(b.get("ate", 1))
        vel = float(b.get("vel", 1)) or 1.0
        for i in np.nonzero((batidas >= s0 - 0.02) & (batidas < s1 - 0.02))[0]:
            t = batidas[i]
            prox = batidas[i + 1] if i + 1 < len(batidas) else t + passo_medio
            saida.append((acumulado + max(0.0, t - s0) / vel, (prox - t) / vel, int(i), int((i - d) % 8)))
        acumulado += (s1 - s0) / vel
    return saida, acumulado


# ---------------------------------------------------------------- notas do baixo

def nota(harm, funcao, i, pos):
    """Nota MIDI de uma função do padrão no tempo i (pos = posição no oito)."""
    t = harmonia.tonica(harm, i)
    escala = set(harm.get("escala") or range(12))
    tipo = harmonia.acorde(harm, i)
    if funcao == "A":  # meio tom abaixo da tônica do próximo meio compasso: passagem de propósito
        proximo = i + (1 if pos % 2 else 2)
        alvo = harmonia.tonica(harm, proximo)
        return alvo - 1
    if funcao == "N":
        b = harm["batidas"][i]["baixo"] if 0 <= i < len(harm["batidas"]) else None
        m = b if b is not None else t
    else:
        m = t + {"T": 0, "5": 7, "8": 12, "3": 4 if tipo == "maj" else 3, "b7": 10, "6": 9}[funcao]
        if m % 12 not in escala:  # fora da escala da música: nota segura
            m = t + 7 if (t + 7) % 12 in escala and funcao in ("b7", "6") else t
    centro = harm.get("registro", 38)
    while m < centro - 9:
        m += 12
    while m > centro + 17:
        m -= 12
    return m


def _baixo_sintetizado(m, dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 440.0 * 2 ** ((m - 69) / 12)
    s = np.sin(2 * np.pi * f * t) + 0.35 * np.sin(4 * np.pi * f * t) + 0.12 * np.sin(6 * np.pi * f * t)
    env = np.minimum(1, t / 0.006) * np.exp(-t * 2.2)
    s = (s * env / 1.5).astype(np.float32)
    return np.stack([s, s])


class Amostras:
    """Notas de baixo do kit da música; notas que faltam saem da gravação mais próxima transposta
    (no máximo 4 semitons) ou, sem nenhuma por perto, de um baixo sintetizado."""

    def __init__(self, kit, semente):
        self.notas = kit.get("notas") or {}
        self.golpes = kit.get("golpes") or {}
        self.cache = {}
        self.vez = {}
        self.sorteio = random.Random(semente)

    def baixo(self, m):
        if m not in self.cache:
            if m in self.notas:
                self.cache[m] = self.notas[m]
            else:
                perto = min(self.notas, key=lambda k: abs(k - m), default=None)
                if perto is not None and abs(perto - m) <= 4:
                    import librosa
                    origem = self.notas[perto][0]
                    self.cache[m] = [np.stack([librosa.effects.pitch_shift(c, sr=SR, n_steps=m - perto) for c in origem]).astype(np.float32)]
                else:
                    self.cache[m] = [_baixo_sintetizado(m, 1.2)]
        lista = self.cache[m]
        k = self.vez.get(("b", m), 0)
        self.vez[("b", m)] = k + 1
        return lista[k % len(lista)]

    def golpe(self, peca):
        lista = self.golpes.get(DO_KIT.get(peca, ""), [])
        if lista:
            k = self.vez.get(peca, 0)
            self.vez[peca] = k + 1
            return lista[k % len(lista)]
        chave = ("sint", peca)
        if chave not in self.cache:
            s = bateria.som(peca)
            self.cache[chave] = np.stack([s, s])
        return self.cache[chave]


# ---------------------------------------------------------------- tocar

def tocar(proj, harm, kit, blocos, estilo, padrao, semente=1):
    """{"bateria": (2, n), "baixo": (2, n)} do padrão na seleção, já no tempo e no tom da música."""
    batidas, total = grade(proj, blocos)
    n = int(round(total * SR))
    swing = float(bateria.estilos()[estilo].get("swing", 0.5))
    sorteio = random.Random(semente)
    sons = Amostras(kit, semente)

    passos = []  # (tempo, passo no padrão de 32, batida, posição no oito, duração do passo)
    for t, d, i, pos in batidas:
        for k in range(4):
            atraso = (swing - 0.5) * 2 * (d / 4) if k % 2 else 0.0
            passos.append((t + k * d / 4 + atraso, (pos * 4 + k) % 32, i, pos, d / 4))

    saida_bat = np.zeros((2, n + SR), np.float32)
    for peca, desenho in padrao["bateria"].items():
        for tempo, p, _, _, _ in passos:
            letra = desenho[p % len(desenho)]
            if letra == ".":
                continue
            golpe = sons.golpe(peca)
            forca = FORCA[letra] * NIVEL[peca] * (1 + sorteio.uniform(-0.06, 0.06))
            ini = int((tempo + sorteio.uniform(-0.003, 0.003)) * SR)
            if ini < 0 or ini >= n:
                continue
            fim = min(ini + golpe.shape[1], saida_bat.shape[1])
            saida_bat[:, ini:fim] += golpe[:, :fim - ini] * forca

    # baixo: as notas do padrão (passos 0-15 repetem nos dois compassos)
    por_passo = {}
    for passo, funcao, dur, forca in padrao["baixo"]:
        for p in ((passo, passo + 16) if passo < 16 and all(x[0] < 16 for x in padrao["baixo"]) else (passo,)):
            por_passo[p] = (funcao, dur, forca)
    eventos = []
    for tempo, p, i, pos, dpasso in passos:
        if p in por_passo:
            funcao, dur, forca = por_passo[p]
            eventos.append([tempo, nota(harm, funcao, i, pos), dur * dpasso, forca])
    saida_bai = np.zeros((2, n + SR), np.float32)
    for k, (tempo, m, dur, forca) in enumerate(eventos):
        if k + 1 < len(eventos):
            dur = min(dur, eventos[k + 1][0] - tempo)  # baixo monofônico: a nota acaba quando a próxima começa
        amostra = sons.baixo(m)
        tam = min(amostra.shape[1], int(dur * SR) + int(0.012 * SR))
        if tam <= 0:
            continue
        trecho = amostra[:, :tam].copy()
        caida = min(tam // 3, int(0.012 * SR))
        if caida:
            trecho[:, -caida:] *= np.linspace(1, 0, caida, dtype=np.float32)
        ini = int(tempo * SR)
        if ini < 0 or ini >= n:
            continue
        fim = min(ini + tam, saida_bai.shape[1])
        saida_bai[:, ini:fim] += trecho[:, :fim - ini] * forca * (1 + sorteio.uniform(-0.05, 0.05))

    saida = {}
    for nome, som in (("bateria", saida_bat[:, :n]), ("baixo", saida_bai[:, :n])):
        pico = float(np.abs(som).max())
        if pico > 1e-4:
            saida[nome] = (som * (0.9 / pico)).astype(np.float32)
    return saida
