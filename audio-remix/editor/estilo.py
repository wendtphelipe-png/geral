"""Trocar o estilo de um trecho: opções de groove do estilo, separadas por instrumento.

O Lyria não obedece ao "só bateria e baixo" do pedido e devolve um groove completo (com
teclados e efeitos), que brigava com a música: o resultado não soava orgânico. Por isso cada
opção é separada em bateria, baixo e outros (o mesmo separador das músicas), e a tela deixa
escolher quais instrumentos do estilo entram. Cada instrumento sai no volume da faixa
original correspondente naqueles oitos.

Com o Lyria saem até 3 opções diferentes (variações do pedido), para comparar e escolher.
A bateria sintetizada da biblioteca é uma opção só, e só de bateria.
"""
import tempfile
import traceback
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf

import bateria
import ia
import motor

INSTRUMENTOS = ["bateria", "baixo", "outros"]
# o que muda entre as opções do Lyria (a primeira é o pedido base)
VARIACOES = ["", " Variation: busier drums with extra percussion and shakers.",
             " Variation: minimal and stripped back, deep and steady groove."]
DEMUCS = {"bateria": ["drums"], "baixo": ["bass"], "outros": ["other", "vocals"]}


def ganho_como_faixa(proj, unidades, fonte, faixa):
    """Ganho para o instrumento do estilo soar no volume da faixa original naqueles oitos."""
    try:
        ref = [proj.faixas[faixa][:, proj.unidades[u]["ini"]:proj.unidades[u]["fim"]] for u in unidades]
        alvo = float(np.sqrt(np.mean(np.concatenate(ref, axis=1) ** 2))) if ref else 0.1
        rms = float(np.sqrt(np.mean(proj.fonte_clipe(fonte) ** 2))) or 1.0
        return round(max(0.15, min(2.0, alvo / max(rms, 1e-6))), 3)
    except Exception:
        traceback.print_exc()
        return 1.0


SR_TOM = 22050


def _perfil(y, sr):
    """Quanto de cada uma das 12 notas há no som (normalizado)."""
    import librosa
    c = librosa.feature.chroma_cqt(y=librosa.resample(y, orig_sr=sr, target_sr=SR_TOM), sr=SR_TOM, hop_length=512).mean(axis=1)
    return c / (np.linalg.norm(c) + 1e-9)


def perfil_do_trecho(proj, unidades):
    """Notas do baixo e dos outros instrumentos da música nos oitos selecionados (o tom que vale ali)."""
    partes = [(proj.faixas["baixo"] + proj.faixas["outros"])[:, proj.unidades[u]["ini"]:proj.unidades[u]["fim"]].mean(axis=0)
              for u in unidades]
    return _perfil(np.concatenate(partes), motor.SR)


def transposicao(alvo, partes):
    """Semitons (-6 a +5) que levam o baixo e os outros do groove para as notas do trecho.
    O Lyria ignora o tom pedido: em Ladies' Choice (ré) os baixos vieram em dó, lá# e fá."""
    som = 2 * partes["baixo"].mean(axis=0) + partes["outros"].mean(axis=0)  # o baixo pesa mais: é ele que desafina
    if float(np.abs(som).max()) < 1e-4:
        return 0
    c = _perfil(som, motor.SR)
    notas = {k: float(alvo @ np.roll(c, k)) for k in range(-6, 6)}
    melhor = max(notas, key=notas.get)
    return melhor if notas[melhor] - notas[0] > 0.01 else 0


def transpor(som, semitons):
    import librosa
    if not semitons or float(np.abs(som).max()) < 1e-4:
        return som
    return np.stack([librosa.effects.pitch_shift(c, sr=motor.SR, n_steps=semitons) for c in som]).astype(np.float32)


def _separar(pasta, audio, nome):
    """Separa um groove (2, n) em bateria, baixo e outros. Devolve {instrumento: (2, n)} ou None."""
    from analisar import separar
    with tempfile.TemporaryDirectory(prefix="estilo-", dir=pasta) as tmp:
        tmp = Path(tmp)
        entrada = tmp / f"{nome}.wav"
        sf.write(entrada, audio.T, motor.SR)
        stems = separar(entrada, tmp / "stems", motor.PASTA_DADOS.parent / "modelos")
        if not stems:
            return None
        n = audio.shape[1]
        saida = {}
        for inst, nomes in DEMUCS.items():
            soma = np.zeros((2, n), np.float32)
            for d in nomes:
                if d in stems:
                    s = motor.Projeto._ler(stems[d])[:, :n]
                    soma[:, :s.shape[1]] += s
            saida[inst] = soma
        return saida


def opcoes(pasta, proj, estilo, unidades, dur, usar_lyria, quantas):
    """Devolve (lista de opções, aviso). Cada opção: {n, nome, modelo, faixas: {inst: {fonte, ganho, importado}}}."""
    bpm = proj.analise.get("bpm") or 120
    batidas = max(1, int(round(dur / (60.0 / bpm))))
    nome_estilo = bateria.estilos()[estilo]["nome"]
    if not usar_lyria:
        fonte = {"tipo": "estilo", "estilo": estilo, "bpm": bpm, "batidas": batidas}
        return [{"n": 1, "nome": f"{nome_estilo} (sintetizada)", "modelo": None,
                 "faixas": {"bateria": {"fonte": fonte, "ganho": ganho_como_faixa(proj, unidades, fonte, "bateria"),
                                        "importado": None}}}], ""
    tom = motor.tom_do_projeto(pasta)
    base = ia.prompt_estilo(estilo, bpm, tom)
    quantas = max(1, min(len(VARIACOES), int(quantas)))

    def gerar(k):
        try:
            arquivo, _, modelo = ia.gerar(base + VARIACOES[k], "clip")
            return k, ia.encaixar(arquivo, bpm, batidas), modelo, None
        except Exception as erro:
            traceback.print_exc()
            return k, None, None, str(erro)[:160]

    with ThreadPoolExecutor(max_workers=quantas) as fila:  # o Lyria responde em paralelo
        gerados = list(fila.map(gerar, range(quantas)))

    alvo = perfil_do_trecho(proj, unidades)
    lista, erros = [], []
    for k, audio, modelo, erro in gerados:
        if audio is None:
            erros.append(erro)
            continue
        partes = _separar(pasta, audio, f"{estilo}-{k + 1}")
        if partes is None:  # sem o separador: o groove inteiro vira "outros", para não perder a opção
            partes = {"bateria": np.zeros_like(audio), "baixo": np.zeros_like(audio), "outros": audio}
        # o Lyria ignora o tom pedido: baixo e outros vão para as notas do trecho (a bateria não tem tom)
        semitons = transposicao(alvo, partes)
        for inst in ("baixo", "outros"):
            partes[inst] = transpor(partes[inst], semitons)
        faixas = {}
        for inst in INSTRUMENTOS:
            som = partes[inst]
            if float(np.abs(som).max()) < 1e-4:
                continue  # o Lyria não pôs esse instrumento nesta opção
            info = motor.salvar_importado(pasta, som, f"{nome_estilo} {k + 1} · {inst}")
            fonte = {"tipo": "importado", "id": info["id"]}
            faixas[inst] = {"fonte": fonte, "importado": info, "ganho": ganho_como_faixa(proj, unidades, fonte, inst)}
        lista.append({"n": k + 1, "nome": f"{nome_estilo} · opção {k + 1}", "modelo": modelo, "faixas": faixas,
                      "semitons": semitons})
    aviso = ""
    if erros and lista:
        aviso = f"{len(erros)} opção(ões) do Lyria falharam ({erros[0]})"
    elif erros:
        raise RuntimeError(f"o Lyria não conseguiu criar o groove: {erros[0]}")
    return lista, aviso
