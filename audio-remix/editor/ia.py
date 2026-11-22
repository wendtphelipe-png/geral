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


_cliente = None
_cliente_chave = None


def cliente():
    """Um cliente só, guardado. (Criar um cliente por chamada fazia a conexão fechar antes da resposta:
    "Cannot send a request, as the client has been closed".)"""
    global _cliente, _cliente_chave
    k = chave()
    if not k:
        raise RuntimeError("a chave do Google ainda não foi colada (botão IA, no alto do editor)")
    if _cliente is None or _cliente_chave != k:
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            raise RuntimeError("falta instalar a biblioteca do Google: rode PREPARAR-ANALISADOR.bat de novo")
        # Os modelos Lyria só existem na API v1beta; a biblioteca 3.x usa a v1 por padrão,
        # onde a lista volta sem nenhum Lyria e a geração dá "404 not found".
        _cliente = genai.Client(api_key=k, http_options=types.HttpOptions(api_version="v1beta"))
        _cliente_chave = k
    return _cliente


def modelos():
    """Modelos Lyria disponíveis para esta chave (os nomes mudam com as versões, então perguntamos ao Google)."""
    global _modelos
    if _modelos is None:
        nomes = []
        c = cliente()
        for m in c.models.list():
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
            c = cliente()
            resposta = c.models.generate_content(
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
    pronto = _encaixar_beat_this(arquivo, y, bpm, batidas)
    if pronto is not None:
        return pronto
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
    return _montar_batidas(y[:, inicio:], bpm, batidas)


def _encaixar_beat_this(arquivo, y, bpm, batidas):
    """Encaixe pelo Beat This! (o mesmo detector da contagem). Com o detector simples, o bloco
    do Lyria saía 160 ms atrasado em relação à batida (um terço de tempo a 130 BPM): a bateria
    de estilo soava atravessada em cima da música. None se o Beat This! não estiver instalado."""
    import motor
    achado = motor.batidas_beat_this(arquivo)
    if achado is None or len(achado[0]) < 8:
        return None
    marcas, compassos = achado
    # cada intervalo é levado ao nível do BPM pedido antes da mediana: o Lyria às vezes faz em
    # meio tempo e o detector alterna os níveis (no krump, 65 e 130 misturados davam 139 BPM
    # na média e o bloco era esticado errado)
    # (a mediana só diz o nível; a medida fina é a reta por todas as batidas, numeradas no nível
    # pedido, porque o detector mede em degraus de 20 ms)
    alvo = 60.0 / bpm
    intervalos = np.diff(marcas)
    passo = float(np.median([d * 2.0 ** round(np.log2(alvo / d)) for d in intervalos if d > 0]))
    numero = np.concatenate([[0], np.cumsum([max(1, int(round(d / passo))) for d in intervalos])])
    bpm_real = 60.0 / float(np.polyfit(numero, marcas, 1)[0])
    taxa = bpm / bpm_real
    if abs(taxa - 1) > 0.001:
        y = np.stack([librosa.effects.time_stretch(c, rate=taxa) for c in y])
    # começa no 1 de um compasso, depois de pular a entrada; 5 ms antes, para não cortar o ataque
    fortes = [t for t in (compassos if len(compassos) else marcas) if t >= 0.3] or [float(marcas[0])]
    inicio = max(0, int((fortes[0] / taxa - 0.005) * SR))
    return _montar_batidas(y[:, inicio:], bpm, batidas)


def _montar_batidas(corpo, bpm, batidas):
    """Exatamente `batidas` batidas, repetindo compassos inteiros se o trecho for curto."""
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
