"""Confere se tudo o que o analisador precisa está instalado. Sai com código 1 se faltar o essencial."""
import importlib
import shutil
import sys

ok = True
print(f"Python {sys.version.split()[0]}")
for modulo, essencial in [("yt_dlp", True), ("librosa", True), ("numpy", True), ("scipy", True),
                          ("soundfile", True), ("matplotlib", False), ("shazamio", False),
                          ("torch", False), ("audio_separator", False)]:
    try:
        m = importlib.import_module(modulo)
        extra = ""
        if modulo == "torch":
            extra = f" | placa de vídeo: {m.cuda.get_device_name(0) if m.cuda.is_available() else 'NÃO (vai usar o processador)'}"
        print(f"  OK     {modulo} {getattr(m, '__version__', '')}{extra}")
    except Exception as erro:
        print(f"  FALTA  {modulo}{' (essencial)' if essencial else ' (opcional)'}: {str(erro)[:100]}")
        ok = ok and not essencial
for programa in ["ffmpeg", "deno"]:
    print(f"  {'OK   ' if shutil.which(programa) else 'FALTA'}  {programa}")
    ok = ok and (programa != "ffmpeg" or bool(shutil.which(programa)))
print("\nTUDO PRONTO para analisar." if ok else "\nFalta algo essencial. Mande uma foto desta janela para o Claude.")
sys.exit(0 if ok else 1)
