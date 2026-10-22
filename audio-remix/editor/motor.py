"""Motor do editor por oitos.

Um projeto guarda a música original separada em faixas (voz, bateria, baixo,
outros) e uma linha do tempo de "blocos". Cada bloco aponta para uma unidade
da música original (um oito, ou a introdução/final) e diz quais faixas tocam,
com que volume e em que velocidade. Nada do áudio original é alterado.

Ao ouvir, só os blocos que mudaram são recalculados; o resto vem do cache.
"""
import hashlib
import json
import shutil
import subprocess
import sys
import threading
import time
import traceback
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "analisador"))

SR = 44100
SR_ANALISE = 22050
HOP = 512
EMENDA = int(0.012 * SR)  # 12 ms de cruzamento entre blocos (evita estalos)
FAIXAS = ["voz", "bateria", "baixo", "outros"]
NOMES_DEMUCS = {"voz": "vocals", "bateria": "drums", "baixo": "bass", "outros": "other"}
VELOCIDADES = {1: "normal", 0.5: "meio tempo", 2: "tempo dobrado"}

PASTA_DADOS = AQUI.parent / "dados" / "projetos"


def agora():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def ler_json(caminho, padrao=None):
    try:
        return json.loads(Path(caminho).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao


def gravar_json(caminho, dados):
    tmp = Path(str(caminho) + ".tmp")
    tmp.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp.replace(caminho)


# ---------------------------------------------------------------- preparação

def novo_id(nome):
    base = "".join(c if c.isalnum() else "-" for c in nome.lower())[:40].strip("-") or "musica"
    return f"{time.strftime('%Y%m%d-%H%M%S')}-{base}"


def preparar(projeto_id, origem, avisar):
    """Baixa/converte, separa as faixas e analisa. `origem` = {'link': ...} ou {'arquivo': caminho}."""
    pasta = PASTA_DADOS / projeto_id
    pasta.mkdir(parents=True, exist_ok=True)
    fonte = pasta / "fonte.wav"

    if "link" in origem:
        avisar("baixando o áudio")
        import yt_dlp
        opcoes = {"format": "bestaudio/best", "outtmpl": str(pasta / "baixado.%(ext)s"), "noplaylist": True,
                  "quiet": True, "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}]}
        titulo = None
        for navegador in [None, "chrome", "edge", "firefox"]:
            if navegador:
                opcoes["cookiesfrombrowser"] = (navegador,)
            try:
                with yt_dlp.YoutubeDL(opcoes) as ydl:
                    info = ydl.extract_info(origem["link"], download=True)
                titulo = info.get("title")
                break
            except Exception as erro:
                ultimo = erro
        if titulo is None:
            raise RuntimeError(f"não consegui baixar: {ultimo}")
        converter(pasta / "baixado.wav", fonte)
        (pasta / "baixado.wav").unlink(missing_ok=True)
    else:
        avisar("convertendo o arquivo")
        titulo = Path(origem["nome"]).stem
        converter(Path(origem["arquivo"]), fonte)
        Path(origem["arquivo"]).unlink(missing_ok=True)

    meta = ler_json(pasta / "projeto.json", {})
    meta["titulo"] = titulo
    gravar_json(pasta / "projeto.json", meta)

    avisar("separando voz, bateria, baixo e outros (alguns minutos)")
    separar_faixas(pasta, fonte)

    avisar("encontrando as batidas e os oitos")
    analisar_projeto(pasta)

    meta = ler_json(pasta / "projeto.json", {})
    analise = ler_json(pasta / "analise.json")
    meta.update({"timeline": timeline_inicial(analise), "alvo": 165, "criado": agora()})
    gravar_json(pasta / "projeto.json", meta)


def converter(entrada, saida):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(entrada), "-ac", "2", "-ar", str(SR), str(saida)],
                   check=True)


def separar_faixas(pasta, fonte):
    destino = pasta / "faixas"
    destino.mkdir(exist_ok=True)
    stems = None
    try:
        from analisar import separar
        stems = separar(fonte, pasta / "separacao", PASTA_DADOS.parent / "modelos")
    except Exception:
        traceback.print_exc()
    if stems:
        for nome, demucs in NOMES_DEMUCS.items():
            converter(stems[demucs], destino / f"{nome}.wav")
        shutil.rmtree(pasta / "separacao", ignore_errors=True)
        return
    # Sem o separador: divisão simples (percussão / grave / resto). Serve para testar, não para produzir.
    y, _ = librosa.load(str(fonte), sr=SR, mono=False)
    y = np.atleast_2d(y)
    harm = np.stack([librosa.effects.harmonic(c) for c in y])
    perc = y - harm
    espectro = [librosa.stft(c) for c in harm]
    freqs = librosa.fft_frequencies(sr=SR)
    grave = np.stack([librosa.istft(np.where(freqs[:, None] < 160, s, 0), length=y.shape[1]) for s in espectro])
    for nome, sinal in [("bateria", perc), ("baixo", grave), ("outros", harm - grave), ("voz", np.zeros_like(y))]:
        sf.write(destino / f"{nome}.wav", sinal.T, SR)
    meta = ler_json(pasta / "projeto.json", {})
    meta["separacao_simples"] = True
    gravar_json(pasta / "projeto.json", meta)


# ---------------------------------------------------------------- análise

def batidas_regulares(tempos, duracao):
    """Preenche batidas perdidas (buracos maiores que 1,5 batida) e estende a grade
    até o começo e o fim da música (o detector costuma ignorar as primeiras batidas)."""
    if len(tempos) < 4:
        return np.asarray(tempos)
    passo = float(np.median(np.diff(tempos)))
    saida = [tempos[0]]
    for t in tempos[1:]:
        while t - saida[-1] > 1.5 * passo:
            saida.append(saida[-1] + passo)
        saida.append(t)
    while saida[0] - passo >= 0:
        saida.insert(0, saida[0] - passo)
    while saida[-1] + passo <= duracao:
        saida.append(saida[-1] + passo)
    return np.array(saida)


def achar_o_um(oenv, batidas, ritmo):
    """Escolhe qual batida (0 a 7) é o "1" da contagem.

    Junta duas pistas: o bumbo mais forte e as mudanças de harmonia/timbre,
    que quase sempre acontecem no começo de um oito.
    """
    if len(batidas) < 16:
        return 0
    quadros = np.minimum(librosa.time_to_frames(batidas, sr=SR_ANALISE, hop_length=HOP), len(oenv) - 1)
    forca = oenv[quadros]
    mistura_harm = librosa.effects.harmonic(ritmo)
    chroma = librosa.feature.chroma_stft(y=mistura_harm, sr=SR_ANALISE, hop_length=HOP)
    mfcc = librosa.feature.mfcc(y=ritmo, sr=SR_ANALISE, hop_length=HOP, n_mfcc=13)
    feat = np.vstack([chroma, mfcc[1:] / 50])
    sinc = librosa.util.sync(feat, quadros, aggregate=np.mean)  # uma coluna por batida
    sinc = sinc / (np.linalg.norm(sinc, axis=0, keepdims=True) + 1e-9)
    mudanca = np.zeros(len(batidas))
    for i in range(4, min(len(batidas), sinc.shape[1]) - 4):
        antes, depois = sinc[:, i - 4:i].mean(axis=1), sinc[:, i:i + 4].mean(axis=1)
        mudanca[i] = 1 - float(antes @ depois / (np.linalg.norm(antes) * np.linalg.norm(depois) + 1e-9))

    def nota(v):
        medias = np.array([v[i::8].mean() for i in range(8)])
        return (medias - medias.mean()) / (medias.std() + 1e-9)

    return int(np.argmax(nota(mudanca) + 0.5 * nota(forca)))


def analisar_projeto(pasta, deslocamento=None):
    faixas = pasta / "faixas"
    if deslocamento is None:
        bateria, _ = librosa.load(str(faixas / "bateria.wav"), sr=SR_ANALISE, mono=True)
        baixo, _ = librosa.load(str(faixas / "baixo.wav"), sr=SR_ANALISE, mono=True)
        oenv = librosa.onset.onset_strength(y=bateria + 0.5 * baixo, sr=SR_ANALISE, hop_length=HOP)
        tempo, quadros = librosa.beat.beat_track(onset_envelope=oenv, sr=SR_ANALISE, hop_length=HOP)
        batidas = batidas_regulares(librosa.frames_to_time(quadros, sr=SR_ANALISE, hop_length=HOP),
                                    len(bateria) / SR_ANALISE)
        deslocamento = achar_o_um(oenv, batidas, bateria + baixo)
    else:
        antiga = ler_json(pasta / "analise.json")
        batidas = np.array(antiga["batidas"])

    duracao = sf.info(str(faixas / "voz.wav")).duration
    amostras = [int(round(t * SR)) for t in batidas]
    unidades = []
    inicio_oitos = amostras[deslocamento] if len(amostras) > deslocamento else 0
    if inicio_oitos > int(0.05 * SR):
        unidades.append({"id": "intro", "tipo": "intro", "rotulo": "Início", "ini": 0, "fim": inicio_oitos})
    n = 0
    i = deslocamento
    while i + 8 < len(amostras):
        n += 1
        unidades.append({"id": f"o{n}", "tipo": "oito", "rotulo": str(n), "ini": amostras[i], "fim": amostras[i + 8]})
        i += 8
    fim_oitos = amostras[i] if i < len(amostras) else inicio_oitos
    total = int(duracao * SR)
    if total - fim_oitos > int(0.05 * SR):
        unidades.append({"id": "final", "tipo": "final", "rotulo": "Final", "ini": fim_oitos, "fim": total})

    descrever_unidades(faixas, unidades)
    # BPM pela reta que melhor passa pelas batidas (mais preciso que a mediana dos intervalos)
    bpm = 60.0 / float(np.polyfit(np.arange(len(batidas)), batidas, 1)[0]) if len(batidas) > 2 else 0
    gravar_json(pasta / "analise.json", {
        "bpm": round(bpm, 1), "duracao": round(duracao, 2), "deslocamento": deslocamento,
        "batidas": [round(float(t), 4) for t in batidas], "unidades": unidades,
        "versao": hashlib.md5(f"{deslocamento}-{len(batidas)}-{duracao}".encode()).hexdigest()[:8],
    })


def descrever_unidades(faixas, unidades):
    """Para cada unidade: desenho da onda de cada faixa e a 'parte' da música (A, B, C...)."""
    sinais = {nome: librosa.load(str(faixas / f"{nome}.wav"), sr=SR_ANALISE, mono=True)[0] for nome in FAIXAS}
    mistura = sum(sinais.values())
    chroma = librosa.feature.chroma_stft(y=mistura, sr=SR_ANALISE, hop_length=HOP)
    mfcc = librosa.feature.mfcc(y=mistura, sr=SR_ANALISE, hop_length=HOP, n_mfcc=13)
    fator = SR_ANALISE / SR
    vetores = []
    for u in unidades:
        a, b = int(u["ini"] * fator), max(int(u["fim"] * fator), int(u["ini"] * fator) + 1)
        u["onda"] = {}
        energias = []
        for nome, s in sinais.items():
            trecho = s[a:b]
            partes = np.array_split(np.abs(trecho), 96) if len(trecho) >= 96 else [np.abs(trecho)]
            u["onda"][nome] = [round(float(p.max()) if len(p) else 0.0, 3) for p in partes]
            energias.append(float(np.sqrt(np.mean(trecho ** 2))) if len(trecho) else 0.0)
        total = sum(energias) + 1e-9
        u["energia"] = {nome: round(e / total, 3) for nome, e in zip(FAIXAS, energias)}
        qa, qb = a // HOP, max(b // HOP, a // HOP + 1)
        vetores.append(np.concatenate([chroma[:, qa:qb].mean(axis=1), mfcc[1:, qa:qb].mean(axis=1) / 50,
                                       np.array(energias) / total]))
    # normaliza a onda pelo máximo da música inteira, por faixa
    for nome in FAIXAS:
        maximo = max((max(u["onda"][nome]) for u in unidades), default=1) or 1
        for u in unidades:
            u["onda"][nome] = [round(v / maximo, 3) for v in u["onda"][nome]]
    oitos = [i for i, u in enumerate(unidades) if u["tipo"] == "oito"]
    if len(oitos) >= 4:
        from scipy.cluster.hierarchy import fcluster, linkage
        dados = np.array([vetores[i] for i in oitos])
        dados = dados - dados.mean(axis=0)
        dados = dados / (np.abs(dados).max() + 1e-9)  # mesma escala para tudo (não infla detalhes sem importância)
        grupos = fcluster(linkage(dados, method="average", metric="cosine"), t=0.5, criterion="distance")
        letras, ordem = {}, iter("ABCDEFGHIJKLMNOP")
        for i, g in zip(oitos, grupos):
            if g not in letras:
                letras[g] = next(ordem, "?")
            unidades[i]["parte"] = letras[g]


def timeline_inicial(analise):
    return [novo_bloco(u["id"]) for u in analise["unidades"]]


def novo_bloco(uid):
    return {"u": uid, "faixas": {f: 1.0 for f in FAIXAS}, "vel": 1}


# ---------------------------------------------------------------- renderização

def aplicar_fades(audio, fi, fo):
    """Fade de entrada/saída (segundos) com curva suave (cosseno)."""
    n = audio.shape[1]
    for segundos, entrada in ((fi, True), (fo, False)):
        k = min(n, int(float(segundos or 0) * SR))
        if k > 1:
            curva = (0.5 - 0.5 * np.cos(np.linspace(0, np.pi, k))).astype(np.float32)
            if entrada:
                audio[:, :k] *= curva
            else:
                audio[:, n - k:] *= curva[::-1]
    return audio


def importar_audio(pasta, arquivo_enviado, nome):
    """Converte qualquer áudio (mp3, wav, m4a...) para a pasta de importados do projeto."""
    destino = Path(pasta) / "importados"
    destino.mkdir(exist_ok=True)
    aid = "a" + hashlib.md5(f"{nome}-{time.time()}".encode()).hexdigest()[:10]
    wav = destino / f"{aid}.wav"
    converter(arquivo_enviado, wav)
    Path(arquivo_enviado).unlink(missing_ok=True)
    y, _ = librosa.load(str(wav), sr=SR_ANALISE, mono=True)
    passo = max(1, int(SR_ANALISE / 20))  # 20 pontos por segundo
    onda = [round(float(np.abs(y[i:i + passo]).max()), 3) for i in range(0, len(y), passo)]
    maximo = max(onda) or 1
    info = {"id": aid, "nome": Path(nome).stem, "dur": round(len(y) / SR_ANALISE, 3),
            "onda": [round(v / maximo, 3) for v in onda]}
    gravar_json(destino / f"{aid}.json", info)
    return info


def listar_importados(pasta):
    return [ler_json(f) for f in sorted((Path(pasta) / "importados").glob("*.json"))]


class Projeto:
    """Projeto aberto na memória: faixas carregadas e cache de pedaços já calculados."""

    def __init__(self, pasta):
        self.pasta = Path(pasta)
        self.analise = ler_json(self.pasta / "analise.json")
        self.unidades = {u["id"]: u for u in self.analise["unidades"]}
        self.faixas = {}
        for nome in FAIXAS:
            self.faixas[nome] = self._ler(self.pasta / "faixas" / f"{nome}.wav")
        self.importados = {}
        self.cache = {}
        self.trava = threading.Lock()

    @staticmethod
    def _ler(caminho):
        dados, sr = sf.read(str(caminho), dtype="float32", always_2d=True)
        if dados.shape[1] == 1:
            dados = np.repeat(dados, 2, axis=1)
        if sr != SR:
            dados = librosa.resample(dados.T, orig_sr=sr, target_sr=SR).T
        return np.ascontiguousarray(dados[:, :2].T)  # (2, n)

    def _guardar(self, chave, valor):
        self.cache[chave] = valor
        if len(self.cache) > 800:
            self.cache.pop(next(iter(self.cache)))
        return valor

    def trecho_unidade(self, uid, de=0.0, ate=1.0):
        """Amostras [a, b) de uma unidade, recortada pelas frações de/ate (0 a 1)."""
        u = self.unidades[uid]
        tam = u["fim"] - u["ini"]
        return u["ini"] + int(round(tam * de)), u["ini"] + int(round(tam * ate))

    def bloco_audio(self, bloco):
        """Áudio de um bloco da trilha principal + EMENDA amostras extras no fim (cruzamento)."""
        chave = hashlib.md5(json.dumps([self.analise["versao"], bloco], sort_keys=True).encode()).hexdigest()
        if chave in self.cache:
            return self.cache[chave]
        a, b = self.trecho_unidade(bloco["u"], bloco.get("de", 0), bloco.get("ate", 1))
        n_total = next(iter(self.faixas.values())).shape[1]
        b_ext = min(b + EMENDA * 4, n_total)
        mistura = np.zeros((2, max(b_ext - a, 1)), dtype=np.float32)
        for nome, ganho in bloco["faixas"].items():
            if ganho:
                mistura += self.faixas[nome][:, a:b_ext] * float(ganho)
        nucleo = b - a
        vel = float(bloco.get("vel", 1))
        if vel != 1:
            mistura = librosa.effects.time_stretch(mistura, rate=vel)
            nucleo = int(round(nucleo / vel))
        if mistura.shape[1] < nucleo + EMENDA:
            mistura = np.pad(mistura, ((0, 0), (0, nucleo + EMENDA - mistura.shape[1])))
        mistura = mistura[:, : nucleo + EMENDA].astype(np.float32)
        if bloco.get("env"):  # curva de volume (fades que atravessam vários blocos)
            xs, gs = zip(*bloco["env"])
            mistura[:, :nucleo] *= np.interp(np.linspace(0, 1, nucleo), xs, gs).astype(np.float32)
            mistura[:, nucleo:] *= float(gs[-1])
        if bloco.get("fi") or bloco.get("fo"):
            corpo = aplicar_fades(mistura[:, :nucleo].copy(), bloco.get("fi"), bloco.get("fo"))
            mistura[:, :nucleo] = corpo
            if bloco.get("fo"):
                mistura[:, nucleo:] = 0  # depois de um fade de saída não sobra som
        return self._guardar(chave, (mistura, nucleo))

    def fonte_clipe(self, fonte):
        """Áudio completo de onde o clipe é recortado."""
        if fonte["tipo"] == "importado":
            aid = fonte["id"]
            if aid not in self.importados:
                self.importados[aid] = self._ler(self.pasta / "importados" / f"{aid}.wav")
            return self.importados[aid]
        a, b = self.trecho_unidade(fonte["u"], fonte.get("de", 0), fonte.get("ate", 1))
        return self.faixas[fonte["faixa"]][:, a:b]

    def clipe_audio(self, clipe):
        chave = hashlib.md5(json.dumps(["clipe", self.analise["versao"], clipe], sort_keys=True).encode()).hexdigest()
        if chave in self.cache:
            return self.cache[chave]
        fonte = self.fonte_clipe(clipe["fonte"])
        a = int(float(clipe.get("ini", 0)) * SR)
        b = a + int(float(clipe["dur"]) * SR)
        audio = fonte[:, a:min(b, fonte.shape[1])].astype(np.float32) * float(clipe.get("ganho", 1))
        audio = aplicar_fades(audio.copy(), clipe.get("fi"), clipe.get("fo"))
        return self._guardar(chave, audio)

    def montar(self, timeline, camadas=None):
        """Trilha principal (blocos em sequência) + camadas (clipes em posições livres).
        Devolve (áudio (2, n), início de cada bloco em segundos)."""
        with self.trava:
            pedacos = [self.bloco_audio(b) for b in timeline]
            clipes = [(c, self.clipe_audio(c)) for cam in (camadas or []) for c in cam.get("clipes", [])
                      if float(cam.get("ganho", 1)) > 0]
        total = sum(n for _, n in pedacos)
        fim_camadas = max((int(float(c["pos"]) * SR) + a.shape[1] for c, a in clipes), default=0)
        saida = np.zeros((2, max(total, fim_camadas) + EMENDA), dtype=np.float32)
        sobe = np.linspace(0, 1, EMENDA, dtype=np.float32)
        desce = sobe[::-1]
        pos, inicios = 0, []
        for i, (audio, nucleo) in enumerate(pedacos):
            inicios.append(round(pos / SR, 4))
            pedaco = audio.copy()
            if i > 0:
                pedaco[:, :EMENDA] *= sobe
            pedaco[:, nucleo:nucleo + EMENDA] *= desce
            saida[:, pos:pos + nucleo + EMENDA] += pedaco
            pos += nucleo
        ganho_camada = {id(c): float(cam.get("ganho", 1)) for cam in (camadas or []) for c in cam.get("clipes", [])}
        for c, audio in clipes:
            ini = int(float(c["pos"]) * SR)
            saida[:, ini:ini + audio.shape[1]] += audio * ganho_camada[id(c)]
        saida = saida[:, :max(total, fim_camadas, 1)]
        pico = float(np.abs(saida).max()) if saida.size else 0
        if pico > 0.98:  # protege contra distorção
            saida *= 0.98 / pico
        return saida, inicios

    def duracao(self, timeline, camadas=None):
        principal = sum((lambda a, b: (b - a))(*self.trecho_unidade(b["u"], b.get("de", 0), b.get("ate", 1)))
                        / float(b.get("vel", 1)) for b in timeline) / SR
        fim = max((float(c["pos"]) + float(c["dur"]) for cam in (camadas or []) for c in cam.get("clipes", [])),
                  default=0)
        return max(principal, fim)

    def unidade_original(self, uid):
        u = self.unidades[uid]
        return sum(f[:, u["ini"]:u["fim"]] for f in self.faixas.values())


def para_wav(audio):
    import io
    buf = io.BytesIO()
    sf.write(buf, audio.T, SR, format="WAV", subtype="PCM_16")
    return buf.getvalue()


def exportar(projeto, timeline, camadas, formato, destino):
    audio, _ = projeto.montar(timeline, camadas)
    # nivela o volume: pico em -1 dB
    pico = float(np.abs(audio).max()) or 1
    audio = audio * (0.89 / pico)
    wav = destino.with_suffix(".wav")
    sf.write(wav, audio.T, SR, subtype="PCM_24")
    if formato == "mp3":
        mp3 = destino.with_suffix(".mp3")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav), "-b:a", "320k", str(mp3)], check=True)
        wav.unlink()
        return mp3
    return wav
