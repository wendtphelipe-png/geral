"""Harmonia da música, tempo a tempo: a nota que o baixo toca e o acorde.

É a base do motor de estilos do PC: o baixo de um estilo novo usa as notas que o baixo da
própria música toca em cada tempo, então fica afinado por construção. (O baixo do Lyria
tocava outra linha: só 20% a 63% das notas cabiam no acorde da música.)

Resultado guardado em <projeto>/harmonia.json (calculado uma vez por música, ~15 s).
"""
from pathlib import Path

import numpy as np

import motor

SR_NOTA = 11025
HOP = 256
VERSAO = 4


def _acordes(chroma):
    """Acorde de cada coluna de chroma (12, n): (raiz 0-11, 'maj'|'min', confiança)."""
    modelos = []
    for raiz in range(12):
        for tipo, terca in (("maj", 4), ("min", 3)):
            v = np.zeros(12)
            v[[raiz, (raiz + terca) % 12, (raiz + 7) % 12]] = [1.0, 0.8, 0.9]
            modelos.append((raiz, tipo, v / np.linalg.norm(v)))
    c = chroma / (np.linalg.norm(chroma, axis=0, keepdims=True) + 1e-9)
    notas = np.array([m[2] for m in modelos]) @ c  # (24, n)
    melhor = notas.argmax(axis=0)
    return [(modelos[k][0], modelos[k][1], float(notas[k, i])) for i, k in enumerate(melhor)]


def _tom(chroma):
    """(nota central 0-11, menor?) pelos perfis de Krumhansl sobre a soma do chroma da música."""
    maior = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
    menor = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])
    total = chroma.sum(axis=1)
    notas = [(float(np.corrcoef(total, np.roll(p, k))[0, 1]), k, m) for m, p in ((False, maior), (True, menor)) for k in range(12)]
    _, k, m = max(notas)
    return k, m


def analisar(pasta):
    """{versao, batidas: [{t, baixo (MIDI) ou None, forca, raiz, tipo, conf}]} — uma entrada por batida."""
    import librosa
    pasta = Path(pasta)
    guardado = motor.ler_json(pasta / "harmonia.json")
    analise = motor.ler_json(pasta / "analise.json")
    if guardado and guardado.get("versao") == VERSAO and guardado.get("contagem") == analise.get("versao"):
        return guardado
    batidas = np.array(analise["batidas"])
    baixo, _ = librosa.load(str(pasta / "faixas" / "baixo.wav"), sr=SR_NOTA, mono=True)
    f0, tem_nota, _ = librosa.pyin(baixo, fmin=librosa.note_to_hz("B0"), fmax=librosa.note_to_hz("C4"),
                                   sr=SR_NOTA, frame_length=1024, hop_length=HOP)
    tempos_f0 = librosa.times_like(f0, sr=SR_NOTA, hop_length=HOP)
    midi = np.where(tem_nota, librosa.hz_to_midi(np.nan_to_num(f0, nan=1.0)), np.nan)

    # acorde a partir do baixo + outros (harmonia), uma coluna por batida
    outros, _ = librosa.load(str(pasta / "faixas" / "outros.wav"), sr=SR_NOTA, mono=True)
    n = min(len(outros), len(baixo))
    chroma = librosa.feature.chroma_cqt(y=outros[:n] + baixo[:n], sr=SR_NOTA, hop_length=512)
    quadros = np.clip(librosa.time_to_frames(batidas, sr=SR_NOTA, hop_length=512), 0, chroma.shape[1] - 1)
    por_batida = librosa.util.sync(chroma, np.append(quadros, chroma.shape[1] - 1), aggregate=np.median)
    # meio compasso de contexto suaviza acordes de uma batida só (passagens)
    suave = np.stack([np.convolve(linha, np.ones(2) / 2, mode="same") for linha in por_batida])
    acordes = _acordes(suave[:, :len(batidas)])

    energia = librosa.feature.rms(y=baixo, frame_length=1024, hop_length=HOP)[0]
    lista = []
    for i, t in enumerate(batidas):
        fim = batidas[i + 1] if i + 1 < len(batidas) else t + float(np.median(np.diff(batidas)))
        m = (tempos_f0 >= t) & (tempos_f0 < fim)
        notas = midi[m][~np.isnan(midi[m])]
        nota = int(np.round(np.median(notas))) if len(notas) >= max(3, 0.3 * m.sum()) else None
        raiz, tipo, conf = acordes[i] if i < len(acordes) else (None, None, 0.0)
        lista.append({"t": round(float(t), 4), "baixo": nota, "forca": round(float(energia[m].mean()) if m.any() else 0.0, 5),
                      "raiz": raiz, "tipo": tipo, "conf": round(conf, 3)})
    # tônica de cada meio compasso (2 tempos, contados a partir do 1): o acorde que soa ali, com
    # preferência para a nota que o baixo toca no tempo forte. Num baixo caminhante (Ladies' Choice:
    # ré, fá#, sol, si...) a nota de cada tempo é passagem, não tônica: quinta e oitava em cima
    # dela desafinariam.
    # o tom da música: acordes do tom ganham preferência; notas de passagem fora do tom (o sol# entre
    # sol e lá do baixo caminhante) não puxam a tônica
    centro_tom, menor = _tom(suave)
    escala = {(centro_tom + g) % 12 for g in (0, 2, 4, 5, 7, 9, 11)} if not menor else \
             {(centro_tom + g) % 12 for g in (0, 2, 3, 5, 7, 8, 10)}
    maior_rel = centro_tom if not menor else (centro_tom + 3) % 12
    do_tom = {((maior_rel + g) % 12, t) for g, t in ((0, "maj"), (2, "min"), (4, "min"), (5, "maj"), (7, "maj"), (9, "min"))}
    d = analise.get("deslocamento", 0)
    for ini in range(-((-d) % 2), len(lista), 2):
        grupo = [k for k in (ini, ini + 1) if 0 <= k < len(lista)]
        c = sum(suave[:, k] for k in grupo if k < suave.shape[1])
        if np.ndim(c) == 0:
            continue
        c = c / (np.linalg.norm(c) + 1e-9)
        forte = lista[grupo[0]]["baixo"]
        melhor, nota_melhor = None, -1.0
        for raiz in range(12):
            for tipo, terca in (("maj", 4), ("min", 3)):
                v = np.zeros(12)
                v[[raiz, (raiz + terca) % 12, (raiz + 7) % 12]] = [1.0, 0.8, 0.9]
                nota = float(c @ (v / np.linalg.norm(v)))
                if (raiz, tipo) in do_tom:
                    nota += 0.1
                elif tipo == "maj" and raiz in escala:
                    nota += 0.04  # dominante secundária (ex.: si maior em ré)
                if forte is not None and forte % 12 == raiz and raiz in escala:
                    nota += 0.08
                if nota > nota_melhor:
                    melhor, nota_melhor = (raiz, tipo), nota
        for k in grupo:
            lista[k]["tonica"], lista[k]["acorde"] = melhor[0], melhor[1]

    tocadas = [b["baixo"] for b in lista if b["baixo"] is not None]
    saida = {"versao": VERSAO, "contagem": analise.get("versao"), "batidas": lista,
             "registro": int(np.median(tocadas)) if tocadas else 38,
             "tom": [int(centro_tom), bool(menor)], "escala": sorted(int(x) for x in escala)}
    motor.gravar_json(pasta / "harmonia.json", saida)
    return saida


def tonica(harm, i):
    """Tônica (MIDI) do meio compasso do tempo i, na região grave em que o baixo da música toca."""
    b = harm["batidas"][max(0, min(i, len(harm["batidas"]) - 1))]
    pc = b.get("tonica", b.get("raiz"))
    if pc is None:
        return raiz_em(harm, i)
    centro = harm.get("registro", 38)
    return min((pc + 12 * o for o in range(1, 5)), key=lambda m: abs(m - centro))


def acorde(harm, i):
    b = harm["batidas"][max(0, min(i, len(harm["batidas"]) - 1))]
    return b.get("acorde", b.get("tipo") or "maj")


def raiz_em(harm, i):
    """Nota-base (MIDI) do tempo i: a do baixo da música; sem baixo, a última tocada; sem nada, a raiz do acorde."""
    b = harm["batidas"]
    for k in range(i, max(-1, i - 8), -1):
        if 0 <= k < len(b) and b[k]["baixo"] is not None:
            return b[k]["baixo"]
    raiz = b[i]["raiz"] if 0 <= i < len(b) and b[i]["raiz"] is not None else 2
    return 36 + int(raiz)  # dó 2 a si 2
