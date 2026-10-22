"""Raio-x de mixes de competição.

Para cada áudio: separa as faixas (voz, bateria, baixo, outros), mede o BPM ao
longo do tempo, encontra os trechos e as transições, classifica cada transição
e tenta identificar a música original de cada trecho.

Uso:  python analisar.py <pasta-ou-arquivo> --saida <pasta-das-analises>
      [--sem-separar] [--sem-identificar] [--estrutura <pasta-dos-stems>]
"""
import argparse
import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy.ndimage import median_filter
from scipy.signal import find_peaks

SR = 22050
HOP = 512
BLOCO = 0.25  # segundos por bloco na busca de trechos
EXTENSOES = {".wav", ".mp3", ".m4a", ".opus", ".webm", ".flac", ".ogg"}

NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
PERFIL_MAIOR = np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
PERFIL_MENOR = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])


def log(msg):
    print(msg, flush=True)


# ---------- separação em faixas ----------

def separar(caminho, pasta_stems):
    """Separa com Demucs (htdemucs) via audio-separator. Devolve {nome: caminho} ou None."""
    destino = pasta_stems / caminho.stem
    nomes = {"drums": "Drums", "bass": "Bass", "vocals": "Vocals", "other": "Other"}

    def achar():
        achados = {}
        for chave, rotulo in nomes.items():
            lista = sorted(destino.glob(f"*({rotulo})*.wav"))
            if lista:
                achados[chave] = lista[0]
        return achados if len(achados) == 4 else None

    pronto = achar()
    if pronto:
        return pronto
    try:
        from audio_separator.separator import Separator
    except ImportError:
        log("  (audio-separator não instalado: seguindo sem separar)")
        return None
    destino.mkdir(parents=True, exist_ok=True)
    try:
        sep = Separator(output_dir=str(destino), model_file_dir=str(pasta_stems.parent / "modelos"))
        sep.load_model(model_filename="htdemucs.yaml")
        sep.separate(str(caminho))
    except Exception as erro:  # a análise continua mesmo sem as faixas
        log(f"  (falha ao separar: {erro})")
        return None
    return achar()


# ---------- medidas ----------

def carregar(caminho):
    y, _ = librosa.load(str(caminho), sr=SR, mono=True)
    return y


def envelope_ataques(y):
    # Só a parte percussiva: reduz a influência da plateia e da voz.
    perc = librosa.effects.percussive(y, margin=2.0)
    return librosa.onset.onset_strength(y=perc, sr=SR, hop_length=HOP, aggregate=np.median)


def dobrar_bpm(bpm, minimo=70.0, maximo=160.0):
    """Leva o BPM para a faixa útil de dança (resolve o 'dobro' e a 'metade')."""
    bpm = np.asarray(bpm, dtype=float).copy()
    for _ in range(4):
        bpm = np.where(bpm < minimo, bpm * 2, bpm)
        bpm = np.where(bpm > maximo, bpm / 2, bpm)
    return bpm


def curva_bpm(oenv):
    local = librosa.feature.tempo(onset_envelope=oenv, sr=SR, hop_length=HOP, aggregate=None, ac_size=6.0)
    local = dobrar_bpm(local)
    janela = int(4.0 * SR / HOP) | 1
    return median_filter(local, size=janela, mode="nearest")


def batidas(oenv, bpm_curva):
    try:
        _, quadros = librosa.beat.beat_track(onset_envelope=oenv, sr=SR, hop_length=HOP, bpm=bpm_curva)
    except Exception:
        _, quadros = librosa.beat.beat_track(onset_envelope=oenv, sr=SR, hop_length=HOP,
                                             start_bpm=float(np.median(bpm_curva)))
    return librosa.frames_to_time(quadros, sr=SR, hop_length=HOP)


def tom(chroma_medio):
    melhor, nome = -2.0, "?"
    for i in range(12):
        for perfil, modo in ((PERFIL_MAIOR, ""), (PERFIL_MENOR, "m")):
            r = np.corrcoef(chroma_medio, np.roll(perfil, i))[0, 1]
            if r > melhor:
                melhor, nome = r, NOTAS[i] + modo
    return nome


def em_blocos(matriz, quadros_por_bloco):
    n = matriz.shape[1] // quadros_por_bloco
    m = matriz[:, : n * quadros_por_bloco]
    return m.reshape(matriz.shape[0], n, quadros_por_bloco).mean(axis=2)


def novidade(feat, meia):
    """Curva de 'mudança' (kernel em tabuleiro sobre a matriz de semelhança)."""
    f = feat / (np.linalg.norm(feat, axis=0, keepdims=True) + 1e-9)
    s = f.T @ f
    n = s.shape[0]
    eixo = np.arange(-meia, meia) + 0.5
    gauss = np.exp(-0.5 * (eixo / (meia / 2)) ** 2)
    kernel = np.outer(gauss, gauss) * np.outer(np.sign(eixo), np.sign(eixo))
    pad = np.pad(s, meia, mode="edge")
    curva = np.array([np.sum(pad[i: i + 2 * meia, i: i + 2 * meia] * kernel) for i in range(n)])
    curva = np.maximum(curva, 0)
    return curva / (curva.max() + 1e-9)


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-6))


# ---------- análise de um áudio ----------

def analisar(caminho, pasta_stems, separar_faixas=True, identificar=True):
    log(f"\n== {caminho.name}")
    y = carregar(caminho)
    duracao = len(y) / SR

    stems = separar(caminho, pasta_stems) if separar_faixas else None
    faixas = {}
    if stems:
        for nome, arq in stems.items():
            faixas[nome] = carregar(arq)
        base_ritmo = faixas["drums"] + faixas["bass"]
    else:
        base_ritmo = y

    log("  medindo BPM e batidas")
    oenv = envelope_ataques(base_ritmo)
    bpm_c = curva_bpm(oenv)
    tempos_batida = batidas(oenv, bpm_c)

    log("  procurando trechos e transições")
    qpb = int(round(BLOCO * SR / HOP))
    mfcc = librosa.feature.mfcc(y=y, sr=SR, hop_length=HOP, n_mfcc=20)[1:]
    chroma = librosa.feature.chroma_cqt(y=librosa.effects.harmonic(y), sr=SR, hop_length=HOP)
    rms = librosa.feature.rms(y=y, hop_length=HOP)[0]
    centro = librosa.feature.spectral_centroid(y=y, sr=SR, hop_length=HOP)[0]
    espectro = np.abs(librosa.stft(y, hop_length=HOP))
    freqs = librosa.fft_frequencies(sr=SR)
    grave = espectro[freqs < 150].sum(axis=0) / (espectro.sum(axis=0) + 1e-9)

    mfcc_n = (mfcc - mfcc.mean(axis=1, keepdims=True)) / (mfcc.std(axis=1, keepdims=True) + 1e-9)
    bpm_feat = (bpm_c - bpm_c.mean()) / (bpm_c.std() + 1e-9)
    feat = np.vstack([em_blocos(mfcc_n, qpb), em_blocos(chroma, qpb) * 2,
                      em_blocos(bpm_feat[None, :], qpb) * 2])
    nov = novidade(feat, meia=int(4 / BLOCO))
    picos, _ = find_peaks(nov, distance=int(6 / BLOCO), height=np.median(nov) + 0.8 * nov.std(),
                          prominence=0.1)
    fronteiras = [float(p * BLOCO) for p in picos if 3 < p * BLOCO < duracao - 3]
    fronteiras = [encaixar(t, tempos_batida) for t in fronteiras]

    def quadro(t):
        return int(np.clip(t * SR / HOP, 0, len(rms) - 1))

    def media(arr, a, b):
        i, j = quadro(a), max(quadro(b), quadro(a) + 1)
        return float(np.mean(arr[i:j]))

    transicoes = [classificar(t, rms, centro, mfcc_n, bpm_c, quadro, media) for t in fronteiras]
    paradas = achar_paradas(rms, tempos_batida)

    limites = [0.0] + fronteiras + [duracao]
    trechos = []
    for i in range(len(limites) - 1):
        a, b = limites[i], limites[i + 1]
        bt = tempos_batida[(tempos_batida >= a) & (tempos_batida < b)]
        bpm = float(60 / np.median(np.diff(bt))) if len(bt) > 4 else float(np.median(bpm_c[quadro(a):quadro(b)]))
        bpm = float(dobrar_bpm([bpm])[0])
        n_bat = len(bt)
        t = {
            "n": i + 1,
            "inicio": round(a, 2),
            "fim": round(b, 2),
            "duracao": round(b - a, 2),
            "bpm": round(bpm, 1),
            "batidas": n_bat,
            "oitos": round(n_bat / 8, 1),
            "tom": tom(chroma[:, quadro(a):quadro(b)].mean(axis=1)),
            "volume_db": round(float(db(media(rms, a, b))), 1),
            "grave": round(media(grave, a, b), 3),
            "brilho_hz": round(media(centro, a, b)),
        }
        if faixas:
            ia, ib = int(a * SR), int(b * SR)
            energia = {k: float(np.sqrt(np.mean(v[ia:ib] ** 2)) + 1e-9) for k, v in faixas.items()}
            total = sum(energia.values())
            t["faixas"] = {k: round(v / total, 3) for k, v in energia.items()}
            t["tem_voz"] = energia["vocals"] / total > 0.18
            t["tem_bateria"] = energia["drums"] / total > 0.15
        trechos.append(t)

    if identificar:
        log("  identificando as músicas originais")
        identificar_trechos(caminho, trechos)

    return {
        "arquivo": caminho.name,
        "duracao": round(duracao, 2),
        "bpm_medio": round(float(np.median(bpm_c)), 1),
        "separado": bool(faixas),
        "trechos": trechos,
        "transicoes": transicoes,
        "paradas": paradas,
        "curva_bpm": [[round(float(t), 1), round(float(b), 1)]
                      for t, b in zip(librosa.frames_to_time(np.arange(0, len(bpm_c), int(SR / HOP)), sr=SR, hop_length=HOP),
                                      bpm_c[:: int(SR / HOP)])],
        "batidas": [round(float(t), 3) for t in tempos_batida],
    }


def achar_paradas(rms, tempos_batida):
    """Paradas curtas (0,1 a 2 s) em que o som cai muito: os 'stops' e 'freezes' da coreografia."""
    nivel = db(rms)
    referencia = median_filter(nivel, size=int(4 * SR / HOP) | 1, mode="nearest")
    baixo = nivel < referencia - 12
    paradas, i = [], 0
    while i < len(baixo):
        if baixo[i]:
            j = i
            while j < len(baixo) and baixo[j]:
                j += 1
            ini, fim = librosa.frames_to_time([i, j], sr=SR, hop_length=HOP)
            if 0.1 <= fim - ini <= 2.0:
                p = {"tempo": round(float(ini), 2), "duracao": round(float(fim - ini), 2),
                     "queda_db": round(float(np.median(referencia[i:j]) - np.min(nivel[i:j])), 1)}
                if len(tempos_batida) > 8:
                    n = int(np.searchsorted(tempos_batida, ini))
                    p["oito"], p["tempo_do_oito"] = n // 8 + 1, n % 8 + 1
                paradas.append(p)
            i = j
        else:
            i += 1
    return paradas


def encaixar(t, tempos_batida):
    if len(tempos_batida) == 0:
        return round(t, 2)
    i = int(np.argmin(np.abs(tempos_batida - t)))
    return round(float(tempos_batida[i]) if abs(tempos_batida[i] - t) < 0.4 else t, 2)


def classificar(t, rms, centro, mfcc_n, bpm_c, quadro, media):
    """Etiquetas da transição. São heurísticas: servem de pista, não de verdade."""
    antes = db(media(rms, t - 1.5, t - 0.3))
    depois = db(media(rms, t + 0.3, t + 1.5))
    i0, i1 = quadro(t - 0.5), quadro(t + 0.5)
    vale = float(db(np.min(rms[i0:max(i1, i0 + 1)])))
    etiquetas = []
    if vale < max(antes, depois) - 18:
        etiquetas.append("parada/silêncio")
    # rapidez: a mudança de timbre acontece em menos de meio segundo?
    perto = np.linalg.norm(mfcc_n[:, quadro(t - 0.25)] - mfcc_n[:, quadro(t + 0.25)])
    longe = np.linalg.norm(mfcc_n[:, quadro(t - 3)] - mfcc_n[:, quadro(t + 3)])
    if perto > 0.7 * longe:
        etiquetas.append("corte")
    else:
        etiquetas.append("mistura gradual")
    # efeito de subida (riser / varredura de filtro): o brilho sobe nos 3 s antes
    c = centro[quadro(t - 3):quadro(t)]
    if len(c) > 10 and np.polyfit(np.arange(len(c)), c, 1)[0] * len(c) > 1500:
        etiquetas.append("subida (riser/filtro)")
    b0, b1 = float(np.median(bpm_c[quadro(t - 4):quadro(t)])), float(np.median(bpm_c[quadro(t):quadro(t + 4)]))
    if abs(b1 - b0) > 4:
        etiquetas.append("muda o BPM")
    if abs(depois - antes) > 6:
        etiquetas.append("salto de volume")
    return {"tempo": round(t, 2), "etiquetas": etiquetas, "bpm_antes": round(b0, 1), "bpm_depois": round(b1, 1),
            "volume_antes_db": round(float(antes), 1), "volume_depois_db": round(float(depois), 1)}


# ---------- identificação (Shazam, gratuito e não oficial) ----------

def identificar_trechos(caminho, trechos):
    try:
        from shazamio import Shazam
    except ImportError:
        log("  (shazamio não instalado: sem identificação)")
        return
    y, sr = librosa.load(str(caminho), sr=44100, mono=True)

    async def rodar():
        shazam = Shazam()
        for t in trechos:
            if t["duracao"] < 6:
                continue
            meio = (t["inicio"] + t["fim"]) / 2
            a = max(t["inicio"], meio - 6)
            b = min(t["fim"], a + 12)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, y[int(a * sr):int(b * sr)], sr)
            try:
                fn = getattr(shazam, "recognize", None) or shazam.recognize_song
                r = await fn(tmp.name)
                faixa = r.get("track") if isinstance(r, dict) else None
                if faixa:
                    t["musica"] = {"titulo": faixa.get("title"), "artista": faixa.get("subtitle")}
            except Exception as erro:
                t["musica_erro"] = str(erro)[:120]
            finally:
                Path(tmp.name).unlink(missing_ok=True)
            await asyncio.sleep(1.5)

    asyncio.run(rodar())


# ---------- relatório ----------

def relatorio_md(r):
    linhas = [f"# {r['arquivo']}", "",
              f"Duração: {mmss(r['duracao'])}  |  BPM mediano: {r['bpm_medio']}  |  "
              f"faixas separadas: {'sim' if r['separado'] else 'não'}", "",
              "## Trechos", "",
              "| # | Início | Dur. (s) | Oitos | BPM | Tom | Vol. dB | Voz | Música identificada |",
              "|---|---|---|---|---|---|---|---|---|"]
    for t in r["trechos"]:
        m = t.get("musica")
        musica = f"{m['artista']} – {m['titulo']}" if m else ""
        voz = "" if "tem_voz" not in t else ("sim" if t["tem_voz"] else "não")
        linhas.append(f"| {t['n']} | {mmss(t['inicio'])} | {t['duracao']} | {t['oitos']} | {t['bpm']} | {t['tom']} | "
                      f"{t['volume_db']} | {voz} | {musica} |")
    linhas += ["", "## Transições", "", "| Tempo | Tipo | BPM antes → depois | Volume antes → depois |", "|---|---|---|---|"]
    for x in r["transicoes"]:
        linhas.append(f"| {mmss(x['tempo'])} | {', '.join(x['etiquetas'])} | {x['bpm_antes']} → {x['bpm_depois']} | "
                      f"{x['volume_antes_db']} → {x['volume_depois_db']} |")
    if r.get("paradas"):
        linhas += ["", "## Paradas (stops e freezes)", "", "| Tempo | Duração (s) | Queda (dB) | Oito, tempo |", "|---|---|---|---|"]
        for x in r["paradas"]:
            linhas.append(f"| {mmss(x['tempo'])} | {x['duracao']} | {x['queda_db']} | {x.get('oito', '')}, {x.get('tempo_do_oito', '')} |")
    return "\n".join(linhas) + "\n"


def mmss(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"


def grafico(r, destino):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    c = np.array(r["curva_bpm"])
    fig, ax = plt.subplots(figsize=(14, 3.5))
    ax.plot(c[:, 0], c[:, 1], color="#3FA9F5")
    for x in r["transicoes"]:
        ax.axvline(x["tempo"], color="#FFB224", alpha=0.7)
    for t in r["trechos"]:
        ax.text((t["inicio"] + t["fim"]) / 2, ax.get_ylim()[1], str(t["n"]), ha="center", va="bottom", fontsize=8)
    ax.set_xlabel("segundos")
    ax.set_ylabel("BPM")
    ax.set_title(r["arquivo"].replace("\uff5c", "|"), fontsize=9)
    fig.tight_layout()
    fig.savefig(destino, dpi=110)
    plt.close(fig)


def separador_disponivel():
    try:
        import audio_separator  # noqa: F401
        return True
    except ImportError:
        return False


def main():
    p = argparse.ArgumentParser()
    p.add_argument("entrada")
    p.add_argument("--saida", default="analises")
    p.add_argument("--estrutura", default=None, help="pasta onde ficam as faixas separadas")
    p.add_argument("--sem-separar", action="store_true")
    p.add_argument("--sem-identificar", action="store_true")
    p.add_argument("--refazer", action="store_true", help="analisa de novo mesmo os já analisados")
    a = p.parse_args()

    entrada = Path(a.entrada)
    arquivos = sorted(f for f in entrada.iterdir() if f.suffix.lower() in EXTENSOES) if entrada.is_dir() else [entrada]
    saida = Path(a.saida)
    saida.mkdir(parents=True, exist_ok=True)
    pasta_stems = Path(a.estrutura) if a.estrutura else entrada.parent / "faixas"

    for arq in arquivos:
        destino = saida / (arq.stem + ".json")
        if destino.exists() and not a.refazer:
            antigo = json.loads(destino.read_text(encoding="utf-8"))
            atualizado = "paradas" in antigo  # análises antigas não tinham as paradas
            if atualizado and (antigo.get("separado") or a.sem_separar or not separador_disponivel()):
                log(f"já analisado: {arq.name}")
                continue
            log(f"refazendo (versão nova do analisador ou faixas separadas): {arq.name}")
        inicio = time.time()
        try:
            r = analisar(arq, pasta_stems, not a.sem_separar, not a.sem_identificar)
        except Exception as erro:
            log(f"  ERRO em {arq.name}: {erro}")
            continue
        destino.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8")
        (saida / (arq.stem + ".md")).write_text(relatorio_md(r), encoding="utf-8")
        grafico(r, saida / (arq.stem + ".png"))
        log(f"  pronto em {time.time() - inicio:.0f} s: {len(r['trechos'])} trechos, {len(r['transicoes'])} transições")


if __name__ == "__main__":
    sys.exit(main())
