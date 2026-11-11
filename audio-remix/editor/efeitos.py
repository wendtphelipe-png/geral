"""Efeitos do editor: eco, reverb, filtros (abafado, rádio) e paradas.

Os efeitos de eco e reverb geram uma "cauda" que continua soando depois do
fim do trecho (como num mix de verdade). Por isso `aplicar` devolve duas
partes: o som seco (mesmo tamanho da entrada) e o som molhado (mais longo).
"""
import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
FILTROS = ("abafado", "radio", "grave")

_respostas = {}


def resposta_reverb(tamanho):
    """Resposta de sala sintética (ruído com decaimento), estéreo, sempre a mesma para o mesmo tamanho."""
    tamanho = round(float(tamanho), 2)
    if tamanho not in _respostas:
        dur = 0.5 + 2.5 * tamanho
        n = int(dur * SR)
        t = np.arange(n) / SR
        gerador = np.random.default_rng(42)
        ruido = gerador.standard_normal((2, n)).astype(np.float32)
        ruido *= np.exp(-6.9 * t / dur).astype(np.float32)  # cai 60 dB até o fim
        ruido[:, : int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR), dtype=np.float32)  # pré-atraso suave
        ruido = sosfilt(butter(2, 6000, "lowpass", fs=SR, output="sos"), ruido, axis=1).astype(np.float32)
        ruido /= np.sqrt((ruido ** 2).sum(axis=1, keepdims=True)) + 1e-9
        _respostas[tamanho] = ruido
    return _respostas[tamanho]


def filtrar(audio, tipo):
    if tipo == "abafado":  # como ouvir de outra sala
        return sosfilt(butter(4, 900, "lowpass", fs=SR, output="sos"), audio, axis=1).astype(np.float32)
    if tipo == "radio":  # rádio / telefone
        y = sosfilt(butter(4, [400, 2800], "bandpass", fs=SR, output="sos"), audio, axis=1)
        return (np.tanh(y * 2.2) / 1.6).astype(np.float32)
    if tipo == "grave":  # só os graves
        return sosfilt(butter(4, 180, "lowpass", fs=SR, output="sos"), audio, axis=1).astype(np.float32)
    return audio


def aplicar(audio, fx, tempo):
    """audio (2, n). fx = {"eco": 0..1, "reverb": 0..1, "filtro": nome, "tamanho": 0..1, "batidas_eco": 0.75}.
    tempo = duração de uma batida em segundos. Devolve (seco (2, n), molhado (2, n + cauda))."""
    if not fx:
        return audio, np.zeros((2, 0), np.float32)
    seco = filtrar(audio, fx.get("filtro"))
    molhado = np.zeros((2, 0), np.float32)

    def somar(a, b):
        if a.shape[1] < b.shape[1]:
            a = np.pad(a, ((0, 0), (0, b.shape[1] - a.shape[1])))
        a[:, : b.shape[1]] += b
        return a

    eco = float(fx.get("eco") or 0)
    if eco > 0:
        atraso = max(1, int(float(fx.get("batidas_eco", 0.75)) * tempo * SR))
        retorno = 0.35 + 0.3 * eco  # quanto cada repetição devolve
        repeticoes = int(min(10, max(2, np.log(0.01) / np.log(retorno))))
        cauda = np.zeros((2, seco.shape[1] + atraso * repeticoes), np.float32)
        # o eco escuta uma versão um pouco abafada (soa mais natural)
        fonte = sosfilt(butter(1, 4500, "lowpass", fs=SR, output="sos"), seco, axis=1).astype(np.float32)
        for k in range(1, repeticoes + 1):
            ini = atraso * k
            g = eco * (retorno ** (k - 1))
            # ping-pong: alterna os lados do estéreo
            lado = np.array([[1.0], [0.55]] if k % 2 else [[0.55], [1.0]], np.float32)
            cauda[:, ini:ini + fonte.shape[1]] += fonte * g * lado
        molhado = somar(molhado, cauda)

    reverb = float(fx.get("reverb") or 0)
    if reverb > 0:
        ir = resposta_reverb(fx.get("tamanho", 0.6))
        sala = np.stack([fftconvolve(seco[c], ir[c]) for c in range(2)]).astype(np.float32)
        molhado = somar(molhado, sala * (reverb * 0.9))

    seco_final = seco * (1 - 0.35 * max(eco, reverb)) if fx.get("distante") else seco
    return seco_final.astype(np.float32), molhado.astype(np.float32)


def silenciar(audio, trechos, tempo, inicio_batida=0.0):
    """Paradas: zera o som nos trechos [(batida, duração em batidas), ...] (batidas contadas do início do áudio)."""
    if not trechos:
        return audio
    rampa = int(0.004 * SR)
    for batida, dur in trechos:
        a = int((float(batida) - inicio_batida) * tempo * SR)
        b = a + int(float(dur) * tempo * SR)
        a, b = max(0, a), min(audio.shape[1], b)
        if b - a <= 2 * rampa:
            continue
        envelope = np.ones(b - a, np.float32)
        envelope[:rampa] = np.linspace(1, 0, rampa)
        envelope[rampa:-rampa] = 0
        envelope[-rampa:] = np.linspace(0, 1, rampa)
        audio[:, a:b] *= envelope
    return audio
