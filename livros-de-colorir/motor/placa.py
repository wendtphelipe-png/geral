# Revezamento da placa de vídeo com o Estúdio de dublagem.
#
# O estúdio tem prioridade: se ele estiver processando algum vídeo, ou se a
# placa já estiver com memória ocupada por outro programa, a fábrica espera.
import json
import shutil
import subprocess
import urllib.request

ESTUDIO = 'http://127.0.0.1:3050/api/estado'
MEMORIA_LIVRE_MIN_MB = 6500  # o SDXL com descarregamento usa até ~6 GB


def estudio_ocupado():
    """True se o estúdio estiver processando algo; None se estiver desligado."""
    try:
        with urllib.request.urlopen(ESTUDIO, timeout=3) as r:
            estado = json.load(r)
    except Exception:
        return None
    if estado.get('gpuDono'):
        return True
    return any(i.get('estado') == 'processando' for i in estado.get('fila', []))


def memoria_da_placa():
    """(usada_mb, total_mb) pela nvidia-smi, ou None se não houver placa NVIDIA."""
    if not shutil.which('nvidia-smi'):
        return None
    try:
        saida = subprocess.run(
            ['nvidia-smi', '--query-gpu=memory.used,memory.total', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=10).stdout.strip().splitlines()[0]
        usada, total = (int(x) for x in saida.split(','))
        return usada, total
    except Exception:
        return None


def situacao():
    estudio = estudio_ocupado()
    memoria = memoria_da_placa()
    livre = None if memoria is None else memoria[1] - memoria[0]
    motivo = None
    if estudio:
        motivo = 'o estúdio de dublagem está processando'
    elif livre is not None and livre < MEMORIA_LIVRE_MIN_MB:
        motivo = f'a placa está com só {livre} MB livres'
    elif memoria is None:
        motivo = 'placa NVIDIA não encontrada'
    return {
        'livre': motivo is None,
        'motivo': motivo,
        'estudio': 'desligado' if estudio is None else ('processando' if estudio else 'parado'),
        'memoria_mb': None if memoria is None else {'usada': memoria[0], 'total': memoria[1]},
    }
