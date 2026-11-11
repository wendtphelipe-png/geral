"""Analisar um padrão de mixagem.

Recebe um mix pronto (link ou arquivo) e descobre:
- quais músicas foram usadas e em que trechos (Shazam, gratuito e não oficial);
- como cada música é na original (baixa a original e compara BPM e tom);
- o que foi feito em cada trecho (sem grave, sem bateria, só voz, meio tempo,
  troca de música, paradas);
- uma ESTRUTURA reutilizável (a mesma usada pelo "Criar mix automático"),
  que pode ser salva na biblioteca e aplicada a outras músicas.
"""
import json
import statistics
import sys
import time
import traceback
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "analisador"))

NOTAS = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def baixar(link, pasta, avisar):
    import yt_dlp
    opcoes = {"format": "bestaudio/best", "outtmpl": str(pasta / "mix.%(ext)s"), "noplaylist": True, "quiet": True,
              "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}]}
    ultimo = None
    for navegador in [None, "chrome", "edge", "firefox"]:
        if navegador:
            opcoes["cookiesfrombrowser"] = (navegador,)
        try:
            with yt_dlp.YoutubeDL(opcoes) as ydl:
                info = ydl.extract_info(link, download=True)
            return pasta / "mix.wav", info.get("title") or "mix"
        except Exception as erro:
            ultimo = erro
    raise RuntimeError(f"não consegui baixar o link: {ultimo}")


def medir_original(busca, pasta):
    """Baixa a primeira versão encontrada no YouTube e mede BPM e tom (primeiros 2 minutos)."""
    import librosa
    import yt_dlp
    from analisar import dobrar_bpm, tom
    destino = pasta / "original.%(ext)s"
    opcoes = {"format": "bestaudio/best", "outtmpl": str(destino), "noplaylist": True, "quiet": True,
              "max_downloads": 1, "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}]}
    with yt_dlp.YoutubeDL(opcoes) as ydl:
        info = ydl.extract_info(f"ytsearch1:{busca}", download=True)
    entrada = (info.get("entries") or [info])[0]
    y, sr = librosa.load(str(pasta / "original.wav"), sr=22050, mono=True, duration=120)
    bpm, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_cqt(y=librosa.effects.harmonic(y), sr=sr)
    return {"bpm": round(float(dobrar_bpm([float(np.atleast_1d(bpm)[0])])[0]), 1), "tom": tom(chroma.mean(axis=1)),
            "titulo_video": entrada.get("title"), "link": entrada.get("webpage_url")}


def semitons(tom_a, tom_b):
    """Diferença em semitons entre dois tons (ignora maior/menor), de -5 a +6."""
    try:
        a, b = NOTAS.index(tom_a.rstrip("m")), NOTAS.index(tom_b.rstrip("m"))
    except ValueError:
        return None
    d = (b - a) % 12
    return d - 12 if d > 6 else d


INGLES = {"vocals": "voz", "drums": "bateria", "bass": "baixo", "other": "outros"}


def classificar(trechos):
    """O que foi feito em cada trecho, comparando as faixas separadas com a mediana do mix."""
    for t in trechos:  # o analisador usa os nomes do separador (em inglês)
        if t.get("faixas"):
            t["faixas"] = {INGLES.get(k, k): v for k, v in t["faixas"].items()}
    tem_faixas = all("faixas" in t for t in trechos)
    med = {f: statistics.median(t["faixas"][f] for t in trechos) if tem_faixas else 0 for f in ("voz", "bateria", "baixo", "outros")}
    bpm_med = statistics.median(t["bpm"] for t in trechos)
    vol_med = statistics.median(t["volume_db"] for t in trechos)
    for t in trechos:
        tipo = "normal"
        f = t.get("faixas")
        if f:
            if f["voz"] > 0.5 and f["bateria"] < 0.15:
                tipo = "so_voz"
            elif f["bateria"] < 0.4 * med["bateria"]:
                tipo = "sem_bateria"
            elif f["baixo"] < 0.4 * med["baixo"]:
                tipo = "sem_grave"
        if tipo == "normal" and t["bpm"] < 0.62 * bpm_med:
            tipo = "meio_tempo"
        elif tipo == "normal" and t["bpm"] > 1.6 * bpm_med:
            tipo = "tempo_dobrado"
        t["tipo"] = tipo
        t["queda_volume"] = t["volume_db"] < vol_med - 6
    return bpm_med


def analisar_mix(arquivo, pasta, avisar, nome=None, comparar=True):
    from analisar import analisar as raio_x
    import bateria
    avisar("separando as faixas e medindo o mix (alguns minutos)")
    r = raio_x(Path(arquivo), pasta / "faixas", separar_faixas=True, identificar=True,
               pasta_modelos=AQUI.parent / "dados" / "modelos")
    trechos = r["trechos"]
    if not trechos:
        raise RuntimeError("não encontrei trechos no áudio")
    bpm_med = classificar(trechos)

    # músicas usadas, em ordem
    def chave(t):
        m = t.get("musica")
        return f"{m['artista']} – {m['titulo']}" if m else None
    musicas = []
    for t in trechos:
        k = chave(t)
        if musicas and musicas[-1]["nome"] == k:
            musicas[-1]["fim"] = t["fim"]; musicas[-1]["trechos"].append(t)
        else:
            musicas.append({"nome": k, "inicio": t["inicio"], "fim": t["fim"], "trechos": [t]})
    contagem = {}
    for m in musicas:
        if m["nome"]:
            contagem[m["nome"]] = contagem.get(m["nome"], 0) + (m["fim"] - m["inicio"])
    ancora = max(contagem, key=contagem.get) if contagem else None
    lista_musicas = []
    for m in musicas:
        bpm = statistics.median(t["bpm"] for t in m["trechos"])
        tons = [t["tom"] for t in m["trechos"]]
        lista_musicas.append({"nome": m["nome"] or "não identificada", "inicio": m["inicio"], "fim": m["fim"],
                              "bpm": round(bpm, 1), "tom": max(set(tons), key=tons.count)})

    # compara com as originais (até 3 músicas diferentes)
    originais = {}
    if comparar:
        for nome_musica in list(dict.fromkeys(m["nome"] for m in lista_musicas if m["nome"] != "não identificada"))[:3]:
            avisar(f"comparando com a original: {nome_musica}")
            sub = pasta / f"original-{len(originais) + 1}"
            sub.mkdir(exist_ok=True)
            try:
                originais[nome_musica] = medir_original(nome_musica.replace("–", ""), sub)
            except Exception as erro:
                originais[nome_musica] = {"erro": str(erro)[:150]}

    # ---- relatório
    rel = []
    dur = r["duracao"]
    rel.append(f"Duração: {int(dur // 60)}:{int(dur % 60):02d}. {len(trechos)} trechos, BPM mediano {round(bpm_med)}.")
    if ancora:
        rel.append(f"Música principal: {ancora} ({round(100 * contagem[ancora] / dur)}% do mix).")
    outras = [m for m in lista_musicas if m["nome"] not in (ancora, "não identificada")]
    for m in outras:
        rel.append(f"Outra música de {mmss(m['inicio'])} a {mmss(m['fim'])}: {m['nome']} (BPM {round(m['bpm'])}).")
    for nome_musica, o in originais.items():
        if "erro" in o:
            rel.append(f"Não consegui baixar a original de {nome_musica} para comparar.")
            continue
        no_mix = [m for m in lista_musicas if m["nome"] == nome_musica]
        bpm_mix = statistics.median(m["bpm"] for m in no_mix)
        tom_mix = no_mix[0]["tom"]
        razao = bpm_mix / o["bpm"] if o["bpm"] else 1
        if 0.45 < razao < 0.55 or 1.9 < razao < 2.1:
            vel = "em meio tempo" if razao < 1 else "em tempo dobrado"
            rel.append(f"{nome_musica}: original a {round(o['bpm'])} BPM, no mix {vel}.")
        elif abs(razao - 1) > 0.025:
            rel.append(f"{nome_musica}: original a {round(o['bpm'])} BPM, no mix a {round(bpm_mix)} BPM "
                       f"({'acelerada' if razao > 1 else 'desacelerada'} {abs(round((razao - 1) * 100, 1))}%).")
        else:
            rel.append(f"{nome_musica}: mesmo andamento da original (cerca de {round(o['bpm'])} BPM).")
        st = semitons(o["tom"], tom_mix)
        if st:
            rel.append(f"{nome_musica}: tom mudou {abs(st)} semitom(ns) {'acima' if st > 0 else 'abaixo'} ({o['tom']} → {tom_mix}). "
                       "Medida aproximada.")
    nomes_tipo = {"so_voz": "só a voz", "sem_bateria": "sem bateria", "sem_grave": "sem grave",
                  "meio_tempo": "em meio tempo", "tempo_dobrado": "em tempo dobrado"}
    for t in trechos:
        if t["tipo"] in nomes_tipo:
            rel.append(f"{mmss(t['inicio'])}–{mmss(t['fim'])}: {nomes_tipo[t['tipo']]}.")
    cortes = sum(1 for x in r["transicoes"] if "corte" in x["etiquetas"])
    por_min = len(r["transicoes"]) / (dur / 60)
    paradas_min = len(r.get("paradas", [])) / (dur / 60)
    rel.append(f"Mudanças: {round(por_min, 1)} por minuto, {round(100 * cortes / max(1, len(r['transicoes'])))}% cortes secos. "
               f"Paradas: {round(paradas_min, 1)} por minuto.")

    # ---- estrutura reutilizável
    passos = []
    picotado = por_min > 6

    def junta(modo, oitos, **extra):
        if passos and passos[-1]["modo"] == modo and modo in ("corpo", "picotado") and passos[-1].get("estilo") == extra.get("estilo"):
            passos[-1]["peso"] = round(passos[-1].get("peso", 0) + oitos, 1)
            return
        passo = {"modo": modo, **extra}
        if modo in ("corpo", "picotado"):
            passo.update(oitos="auto", peso=round(oitos, 1))
        else:
            passo["oitos"] = max(1, round(oitos))
        passos.append(passo)

    for i, t in enumerate(trechos):
        oitos = max(1.0, t["oitos"])
        musica = chave(t)
        primeiro, ultimo = i == 0, i == len(trechos) - 1
        if primeiro and t["oitos"] < 1.2 and t["volume_db"] < statistics.median(x["volume_db"] for x in trechos) - 6:
            continue  # entrada no palco / plateia antes da música
        if not passos:
            modo = {"so_voz": "abertura_so_voz", "sem_grave": "abertura_sem_grave", "sem_bateria": "abertura_sem_grave"}.get(t["tipo"], "abertura_original")
            junta(modo, oitos)
            continue
        if ultimo:
            f = t.get("faixas") or {}
            modo = "final_fade" if t["queda_volume"] else "final_voz" if f.get("voz", 0) > 0.4 or t["tipo"] in ("so_voz", "sem_grave") else "final_hit"
            junta(modo, min(oitos, 2))
            continue
        if musica and ancora and musica != ancora:
            junta("estilo", oitos, estilo=bateria.sugerir_estilo(t["bpm"]))
        elif t["tipo"] == "so_voz":
            junta("so_voz", oitos)
        elif t["tipo"] == "sem_bateria":
            junta("respiro_sem_bateria", oitos)
        elif t["tipo"] == "sem_grave":
            junta("respiro_sem_grave", oitos)
        elif t["tipo"] == "meio_tempo":
            junta("meio_tempo", oitos / 2)  # no mix ele já dura o dobro
        elif t["tipo"] == "tempo_dobrado":
            junta("tempo_dobrado", oitos * 2)
        else:
            junta("picotado" if picotado else "corpo", oitos)
    if not passos or not passos[-1]["modo"].startswith("final"):
        passos.append({"modo": "final_hit", "oitos": 1})
    if any(p["modo"] == "estilo" for p in passos):
        rel.append("Os trechos de outra música viraram 'blocos de outro estilo' na estrutura; o estilo foi sugerido pelo BPM "
                   "e pode ser trocado no montador.")
    densidade = "densas" if paradas_min > 4.5 else "poucas" if paradas_min < 1.6 else "normal"
    titulo = nome or (ancora or "mix analisado")
    estrutura = {"nome": f"Padrão de {titulo}"[:60], "desc": "Aprendido ao analisar um mix: " + "; ".join(rel[:2]),
                 "paradas": densidade, "passos": passos, "origem": titulo}
    return {"relatorio": rel, "musicas": lista_musicas, "originais": originais, "estrutura": estrutura,
            "duracao": dur, "quando": time.strftime("%Y-%m-%d %H:%M")}


def mmss(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"


def rodar(pasta, origem, avisar):
    """Trabalho completo (em segundo plano no servidor). origem = {'link'} ou {'arquivo', 'nome'}."""
    pasta.mkdir(parents=True, exist_ok=True)
    if "link" in origem:
        avisar("baixando o áudio do link")
        arquivo, nome = baixar(origem["link"], pasta, avisar)
    else:
        import subprocess
        arquivo = pasta / "mix.wav"
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", origem["arquivo"], "-ac", "2", "-ar", "44100", str(arquivo)], check=True)
        Path(origem["arquivo"]).unlink(missing_ok=True)
        nome = Path(origem["nome"]).stem
    try:
        resultado = analisar_mix(arquivo, pasta, avisar, nome=nome)
    except Exception:
        traceback.print_exc()
        raise
    (pasta / "resultado.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=1), encoding="utf-8")
    return resultado
