"""Lyria (Google, pela API do Gemini): gera música para o Audio Remix.

- grooves de estilo para os "blocos de outro estilo", no BPM e no tom da música,
  com o tempo acertado depois (para encaixar exato nos oitos);
- trechos pedidos por texto para uma camada;
- músicas inteiras do zero.

A chave fica só no PC: em audio-remix/dados/chave-google.txt (fora do Git) ou na
variável de ambiente GEMINI_API_KEY. Tudo o que é gerado fica guardado em
dados/ia-cache/, para não pagar duas vezes pelo mesmo pedido.
"""
import hashlib
import json
import os
from pathlib import Path

import librosa
import numpy as np

AQUI = Path(__file__).resolve().parent
DADOS = AQUI.parent / "dados"
ARQ_CHAVE = DADOS / "chave-google.txt"
CACHE = DADOS / "ia-cache"
SR = 44100
_modelos = None


def chave():
    for nome in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
        if os.environ.get(nome):
            return os.environ[nome].strip()
    if ARQ_CHAVE.exists():
        return ARQ_CHAVE.read_text(encoding="utf-8").strip() or None
    return None


def salvar_chave(valor):
    DADOS.mkdir(parents=True, exist_ok=True)
    ARQ_CHAVE.write_text(valor.strip(), encoding="utf-8")
    global _modelos
    _modelos = None


def cliente():
    k = chave()
    if not k:
        raise RuntimeError("a chave do Google ainda não foi colada (botão IA, no alto do editor)")
    try:
        from google import genai
    except ImportError:
        raise RuntimeError("falta instalar a biblioteca do Google: rode PREPARAR-ANALISADOR.bat de novo")
    return genai.Client(api_key=k)


def modelos():
    """Modelos Lyria disponíveis para esta chave (os nomes mudam com as versões, então perguntamos ao Google)."""
    global _modelos
    if _modelos is None:
        nomes = []
        for m in cliente().models.list():
            nome = (m.name or "").split("/")[-1]
            if "lyria" in nome and "realtime" not in nome:
                nomes.append(nome)
        _modelos = sorted(nomes)
    return _modelos


def escolher(tipo):
    """'clip' (trechos de 30 s) ou 'musica' (músicas inteiras)."""
    nomes = modelos()
    if not nomes:
        raise RuntimeError("esta chave não tem acesso a nenhum modelo Lyria")
    if tipo == "clip":
        ordem = [n for n in nomes if "clip" in n] + [n for n in nomes if "clip" not in n]
    else:
        ordem = sorted([n for n in nomes if "clip" not in n], reverse=True) + [n for n in nomes if "clip" in n]
    return ordem


def testar():
    nomes = modelos()
    return {"ok": bool(nomes), "modelos": nomes}


def gerar(prompt, tipo="clip"):
    """Gera áudio. Devolve (caminho do arquivo em cache, texto que o modelo devolveu, modelo usado)."""
    from google.genai import types
    CACHE.mkdir(parents=True, exist_ok=True)
    erro_final = None
    for modelo in escolher(tipo):
        h = hashlib.md5(f"{modelo}|{prompt}".encode()).hexdigest()[:16]
        for ext in ("mp3", "wav"):
            pronto = CACHE / f"{h}.{ext}"
            if pronto.exists():
                info = json.loads((CACHE / f"{h}.json").read_text(encoding="utf-8")) if (CACHE / f"{h}.json").exists() else {}
                return pronto, info.get("texto", ""), modelo
        try:
            resposta = cliente().models.generate_content(
                model=modelo, contents=prompt,
                config=types.GenerateContentConfig(response_modalities=["AUDIO", "TEXT"]))
        except Exception as erro:
            erro_final = erro
            continue
        texto, audio, mime = [], None, ""
        for cand in resposta.candidates or []:
            for parte in (cand.content.parts if cand.content else []) or []:
                if parte.text:
                    texto.append(parte.text)
                elif parte.inline_data and parte.inline_data.data:
                    audio, mime = parte.inline_data.data, parte.inline_data.mime_type or ""
        if not audio:
            erro_final = RuntimeError("o modelo não devolveu áudio" + (f": {' '.join(texto)[:200]}" if texto else ""))
            continue
        ext = "wav" if "wav" in mime else "mp3"
        destino = CACHE / f"{h}.{ext}"
        destino.write_bytes(audio)
        (CACHE / f"{h}.json").write_text(json.dumps({"prompt": prompt, "modelo": modelo, "texto": " ".join(texto)},
                                                    ensure_ascii=False), encoding="utf-8")
        return destino, " ".join(texto), modelo
    raise RuntimeError(f"o Lyria não gerou o áudio: {erro_final}")


# ------------------------------------------------------------------ encaixar no tempo da música

def encaixar(arquivo, bpm, batidas):
    """Lê o áudio gerado, acerta o andamento para o BPM da música, começa numa batida forte
    e entrega exatamente `batidas` batidas (repetindo, se precisar). Devolve (2, n) a 44,1 kHz."""
    y, _ = librosa.load(str(arquivo), sr=SR, mono=False)
    y = np.atleast_2d(y)
    if y.shape[0] == 1:
        y = np.repeat(y, 2, axis=0)
    mono = y.mean(axis=0)
    oenv = librosa.onset.onset_strength(y=mono, sr=SR)
    tempo, quadros = librosa.beat.beat_track(onset_envelope=oenv, sr=SR)
    detectado = float(np.atleast_1d(tempo)[0]) or bpm
    # o detector às vezes acha o dobro ou a metade
    detectado = min((detectado * f for f in (0.5, 1, 2)), key=lambda x: abs(x - bpm))
    taxa = bpm / detectado
    if abs(taxa - 1) > 0.005:
        y = np.stack([librosa.effects.time_stretch(c, rate=taxa) for c in y])
    # começa numa batida forte, depois de pular a entrada (até 2 s)
    mono = y.mean(axis=0)
    oenv = librosa.onset.onset_strength(y=mono, sr=SR)
    _, quadros = librosa.beat.beat_track(onset_envelope=oenv, sr=SR, bpm=bpm)
    tempos = librosa.frames_to_time(quadros, sr=SR)
    candidatos = [t for t in tempos if t >= 0.5][:8] or [0.0]
    forca = [oenv[min(len(oenv) - 1, librosa.time_to_frames(t, sr=SR))] for t in candidatos]
    inicio = int(candidatos[int(np.argmax(forca))] * SR)
    corpo = y[:, inicio:]
    precisa = int(round(batidas * 60.0 / bpm * SR))
    um_compasso = int(round(4 * 60.0 / bpm * SR))
    utilizavel = max(um_compasso, (corpo.shape[1] // um_compasso) * um_compasso)  # só compassos inteiros
    corpo = corpo[:, :utilizavel]
    saida = np.zeros((2, precisa), np.float32)
    pos, emenda = 0, int(0.01 * SR)
    while pos < precisa:
        pedaco = corpo[:, : precisa - pos].copy()
        if pos > 0 and pedaco.shape[1] > emenda:
            pedaco[:, :emenda] *= np.linspace(0, 1, emenda)
        saida[:, pos:pos + pedaco.shape[1]] += pedaco
        pos += pedaco.shape[1]
    pico = float(np.abs(saida).max()) or 1
    return (saida * (0.6 / pico)).astype(np.float32)


def prompt_estilo(estilo, bpm, tom=None):
    import bateria
    e = bateria.estilos()[estilo]
    partes = [f"Instrumental {e['nome']} groove for a street dance competition routine",
              f"{round(bpm)} BPM, steady tempo, loopable",
              f"groove: {e['groove']}",
              f"instruments: {', '.join(e['instrumentos'])}",
              "strong and clear drums and bass, no vocals, no intro, no fade"]
    if tom:
        partes.append(f"key of {tom.replace('m', ' minor') if tom.endswith('m') else tom + ' major'}")
    return ". ".join(partes) + "."
