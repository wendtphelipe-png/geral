"""Baixa o áudio de vídeos ou playlists do YouTube (e outros sites) para análise.

Uso:  python baixar.py <link> [<link> ...] --pasta <destino> [--navegador chrome]

Tenta primeiro sem login. Se o YouTube pedir login ("confirme que não é um robô"),
tenta de novo usando os cookies do navegador (Chrome, Edge ou Firefox).
"""
import argparse
import json
import sys
from pathlib import Path

import yt_dlp


def opcoes(pasta, navegador=None, prefixo="00"):
    o = {
        "format": "bestaudio/best",
        "outtmpl": str(pasta / f"{prefixo} - %(title).80B [%(id)s].%(ext)s"),
        "noplaylist": True,
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "wav"}],
        "postprocessor_args": {"extractaudio": ["-ar", "44100"]},
    }
    if navegador:
        o["cookiesfrombrowser"] = (navegador,)
    return o


def listar(link, navegador=None):
    """Lista os vídeos de uma playlist (ou o vídeo único) sem baixar."""
    o = {"extract_flat": "in_playlist", "quiet": True}
    if navegador:
        o["cookiesfrombrowser"] = (navegador,)
    with yt_dlp.YoutubeDL(o) as ydl:
        info = ydl.extract_info(link, download=False)
    entradas = info.get("entries") if info.get("_type") == "playlist" else [info]
    return [{"id": e.get("id"), "titulo": e.get("title"), "duracao": e.get("duration"),
             "canal": e.get("channel") or e.get("uploader"),
             "link": e.get("url") if str(e.get("url", "")).startswith("http") else f"https://www.youtube.com/watch?v={e.get('id')}",
             "posicao": pos} for pos, e in enumerate(entradas or [], 1) if e and e.get("id")]


def tentar(acao, navegadores):
    ultimo = None
    for nav in navegadores:
        try:
            return acao(nav)
        except Exception as erro:
            ultimo = erro
            print(f"   {'sem login' if nav is None else 'cookies do ' + nav}: {str(erro)[:160]}", flush=True)
    raise RuntimeError(ultimo)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("links", nargs="+")
    p.add_argument("--pasta", default="dados/audios")
    p.add_argument("--navegador", default="auto", help="chrome, edge, firefox, nenhum ou auto")
    a = p.parse_args()
    pasta = Path(a.pasta)
    pasta.mkdir(parents=True, exist_ok=True)

    navegadores = [None, "chrome", "edge", "firefox"] if a.navegador == "auto" else \
        [None] if a.navegador == "nenhum" else [a.navegador]

    lista = []
    for link in a.links:
        print(f"\n>> {link}", flush=True)
        try:
            videos = tentar(lambda nav: listar(link, nav), navegadores)
        except RuntimeError:
            videos = []
        if not videos and "list=" in link:
            print("   A playlist não abriu (o link pode estar incompleto). Usando só o vídeo.", flush=True)
            so_video = link.split("&list=")[0]
            try:
                videos = tentar(lambda nav: listar(so_video, nav), navegadores)
            except RuntimeError:
                videos = []
        print(f"   {len(videos)} vídeo(s) encontrado(s)", flush=True)
        for v in videos:
            if list(pasta.glob(f"*[[]{v['id']}[]].wav")):
                print(f"   já baixado: {v['titulo']}", flush=True)
            else:
                print(f"   baixando: {v['titulo']}", flush=True)
                try:
                    tentar(lambda nav: yt_dlp.YoutubeDL(opcoes(pasta, nav, f"{v['posicao']:02d}")).download([v["link"]]) or True, navegadores)
                except RuntimeError:
                    print("   NÃO consegui baixar este vídeo.", flush=True)
                    continue
            lista.append(v)

    destino = pasta / "lista.json"
    antigos = json.loads(destino.read_text(encoding="utf-8")) if destino.exists() else []
    vistos = {x["id"] for x in lista}
    destino.write_text(json.dumps([x for x in antigos if x["id"] not in vistos] + lista,
                                  ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n{len(lista)} vídeo(s) prontos. Áudios em {pasta}", flush=True)
    return 0 if lista else 2


if __name__ == "__main__":
    sys.exit(main())
