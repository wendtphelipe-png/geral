"""Kit da própria música: golpes de bateria e notas de baixo recortados das faixas separadas.

O estilo novo é tocado com os sons da própria música (o mesmo bumbo, a mesma caixa, o mesmo
timbre de baixo), por isso se mistura com ela de forma orgânica. O que a música não tem (por
exemplo, palma ou chimbal aberto) vem da bateria sintetizada da biblioteca.

- bateria: cada golpe é classificado pelo timbre (bumbo grave, caixa no meio, chimbal agudo) e
  ficam os mais limpos (fortes e sem outro golpe logo antes ou logo depois);
- baixo: notas estáveis (mesma altura por pelo menos ~0,12 s), guardadas pela nota MIDI.

Resultado guardado em <projeto>/kit.npz (uma vez por música).
"""
from pathlib import Path

import numpy as np

import motor

SR = motor.SR
VERSAO = 2
POR_PECA = 4          # golpes guardados de cada peça (alternados, para não soar "metralhadora")
DUR_PECA = {"bumbo": 0.35, "caixa": 0.32, "chimbal": 0.12}


def _bandas(trecho, sr):
    espec = np.abs(np.fft.rfft(trecho * np.hanning(len(trecho)))) ** 2
    freqs = np.fft.rfftfreq(len(trecho), 1 / sr)
    total = espec.sum() + 1e-12
    grave = espec[freqs < 150].sum() / total
    medio = espec[(freqs >= 150) & (freqs < 4000)].sum() / total
    agudo = espec[freqs >= 4000].sum() / total
    centro = float((freqs * espec).sum() / total)
    return grave, medio, agudo, centro


def _golpes(bateria):
    """{peca: [(2, n) float32, ...]} com os golpes mais limpos de cada peça."""
    import librosa
    mono = bateria.mean(axis=0)
    env = librosa.onset.onset_strength(y=mono, sr=SR, hop_length=256)
    quadros = librosa.onset.onset_detect(onset_envelope=env, sr=SR, hop_length=256, backtrack=True, units="samples")
    quadros = np.asarray(quadros, int)
    candidatos = {"bumbo": [], "caixa": [], "chimbal": []}
    for k, ini in enumerate(quadros):
        prox = quadros[k + 1] if k + 1 < len(quadros) else len(mono)
        ant = quadros[k - 1] if k > 0 else -SR
        janela = mono[ini:ini + int(0.06 * SR)]
        if len(janela) < int(0.03 * SR):
            continue
        grave, medio, agudo, centro = _bandas(janela, SR)
        pico = float(np.abs(janela).max())
        if grave > 0.45:
            peca = "bumbo"
        elif agudo > 0.45 and centro > 5000:
            peca = "chimbal"
        elif medio > 0.35:
            peca = "caixa"
        else:
            continue
        dur = int(DUR_PECA[peca] * SR)
        # limpo = sem golpe logo depois (o recorte não pega o próximo) e sem cauda forte antes
        livre_depois = (prox - ini) / dur
        antes = mono[max(0, ini - int(0.03 * SR)):ini]
        ruido_antes = float(np.sqrt(np.mean(antes ** 2))) if len(antes) else 0.0
        nota = pico * min(1.0, livre_depois) / (1.0 + 8 * ruido_antes / (pico + 1e-9))
        candidatos[peca].append((nota, ini, dur))
    saida = {}
    for peca, lista in candidatos.items():
        lista.sort(reverse=True)
        golpes = []
        for _, ini, dur in lista[:POR_PECA]:
            g = bateria[:, ini:ini + dur].astype(np.float32).copy()
            caida = min(len(g[0]), int(0.03 * SR))
            g[:, -caida:] *= np.linspace(1, 0, caida, dtype=np.float32)
            g[:, :32] *= np.linspace(0, 1, 32, dtype=np.float32)
            golpes.append(g / (np.abs(g).max() + 1e-9))
        if golpes:
            saida[peca] = golpes
    return saida


def _notas_baixo(baixo):
    """{midi: [(2, n) float32, ...]} com notas estáveis do baixo, da mais longa para a mais curta."""
    import librosa
    sr_nota = 11025
    mono = librosa.resample(baixo.mean(axis=0), orig_sr=SR, target_sr=sr_nota)
    hop = 128
    f0, tem, _ = librosa.pyin(mono, fmin=librosa.note_to_hz("B0"), fmax=librosa.note_to_hz("C4"),
                              sr=sr_nota, frame_length=1024, hop_length=hop)
    midi = np.where(tem, np.round(librosa.hz_to_midi(np.nan_to_num(f0, nan=1.0))), -1).astype(int)
    env = librosa.onset.onset_strength(y=mono, sr=sr_nota, hop_length=hop)
    ataques = set(librosa.onset.onset_detect(onset_envelope=env, sr=sr_nota, hop_length=hop, backtrack=True).tolist())
    notas, i = {}, 0
    minimo = int(0.12 * sr_nota / hop)
    while i < len(midi):
        if midi[i] < 0:
            i += 1
            continue
        j = i
        while j + 1 < len(midi) and midi[j + 1] == midi[i]:
            j += 1
        if j - i + 1 >= minimo:
            # começa no ataque mais próximo (até 40 ms antes), para pegar o começo da nota
            ini_q = max((a for a in ataques if i - 14 <= a <= i), default=i)
            a = int(ini_q * hop / sr_nota * SR)
            b = int((j + 1) * hop / sr_nota * SR)
            trecho = baixo[:, a:b].astype(np.float32).copy()
            if trecho.shape[1] > int(0.08 * SR) and np.abs(trecho).max() > 1e-3:
                caida = min(trecho.shape[1] // 3, int(0.02 * SR))
                trecho[:, -caida:] *= np.linspace(1, 0, caida, dtype=np.float32)
                notas.setdefault(int(midi[i]), []).append(trecho / (np.abs(trecho).max() + 1e-9))
        i = j + 1
    # confere cada gravação de novo, só no pedaço recortado: a nota tem de ser exatamente a etiquetada
    # e estável. Sem isso, 21% a 38% das notas tocadas pelo motor saíam diferentes da pretendida
    # (o recorte pegava a nota anterior ou a detecção da música inteira errava a oitava).
    conferidas = {}
    for m, lista in notas.items():
        boas = []
        for trecho in sorted(lista, key=lambda x: -x.shape[1])[:8]:
            y = librosa.resample(trecho.mean(axis=0), orig_sr=SR, target_sr=sr_nota)
            y = y[int(0.02 * sr_nota):int(0.3 * sr_nota)]
            if len(y) < 1024:
                continue
            f, v, _ = librosa.pyin(y, fmin=librosa.note_to_hz("B0"), fmax=librosa.note_to_hz("C4"), sr=sr_nota,
                                   frame_length=1024, hop_length=hop)
            if v.mean() < 0.6:
                continue
            alturas = librosa.hz_to_midi(f[v])
            if int(np.round(np.median(alturas))) == m and float(np.std(alturas)) < 0.35:
                boas.append(trecho)
            if len(boas) == 3:
                break
        if boas:
            conferidas[m] = boas
    return conferidas


def carregar(pasta, proj):
    """{"golpes": {peca: [...]}, "notas": {midi: [...]}}, calculado uma vez e guardado em kit.npz."""
    pasta = Path(pasta)
    arq = pasta / "kit.npz"
    versao_contagem = proj.analise.get("versao")
    if arq.exists():
        try:
            d = np.load(arq, allow_pickle=False)
            if int(d["versao"]) == VERSAO and str(d["contagem"]) == str(versao_contagem):
                kit = {"golpes": {}, "notas": {}}
                for chave in d.files:
                    if chave.startswith("g_"):
                        _, peca, _ = chave.split("_")
                        kit["golpes"].setdefault(peca, []).append(d[chave])
                    elif chave.startswith("n_"):
                        _, m, _ = chave.split("_")
                        kit["notas"].setdefault(int(m), []).append(d[chave])
                return kit
        except Exception:
            pass
    kit = {"golpes": _golpes(proj.faixas["bateria"]), "notas": _notas_baixo(proj.faixas["baixo"])}
    dados = {"versao": np.array(VERSAO), "contagem": np.array(str(versao_contagem))}
    for peca, lista in kit["golpes"].items():
        for k, g in enumerate(lista):
            dados[f"g_{peca}_{k}"] = g
    for m, lista in kit["notas"].items():
        for k, g in enumerate(lista):
            dados[f"n_{m}_{k}"] = g
    np.savez_compressed(arq, **dados)
    return kit
