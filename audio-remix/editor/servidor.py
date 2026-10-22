"""Servidor do editor por oitos. Abre em http://127.0.0.1:3060

Uso: python servidor.py [--porta 3060]
"""
import argparse
import json
import re
import threading
import traceback
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import motor

PUBLICO = motor.AQUI / "public"
EXPORTADOS = motor.PASTA_DADOS.parent / "exportados"
TIPOS = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml"}

abertos = {}          # id -> motor.Projeto
trabalhos = {}        # id -> {"etapa": str, "erro": str|None, "pronto": bool}
trava_abertos = threading.Lock()


def pasta(pid):
    if not re.fullmatch(r"[\w\-]+", pid or ""):
        raise KeyError(pid)
    p = motor.PASTA_DADOS / pid
    if not p.is_dir():
        raise KeyError(pid)
    return p


def abrir(pid):
    with trava_abertos:
        if pid not in abertos:
            # Mantém só um projeto na memória (as faixas ocupam algumas centenas de MB).
            abertos.clear()
            abertos[pid] = motor.Projeto(pasta(pid))
        return abertos[pid]


def iniciar_trabalho(pid, origem):
    trabalhos[pid] = {"etapa": "começando", "erro": None, "pronto": False}

    def avisar(etapa):
        trabalhos[pid]["etapa"] = etapa
        print(f"[{pid}] {etapa}", flush=True)

    def rodar():
        try:
            motor.preparar(pid, origem, avisar)
            trabalhos[pid]["pronto"] = True
            avisar("pronto")
        except Exception as erro:
            traceback.print_exc()
            trabalhos[pid]["erro"] = str(erro)

    threading.Thread(target=rodar, daemon=True).start()


def resumo_projeto(pid):
    p = pasta(pid)
    meta = motor.ler_json(p / "projeto.json", {})
    analise = motor.ler_json(p / "analise.json")
    t = trabalhos.get(pid)
    if analise and "timeline" in meta:
        estado = "pronto"
    elif t and t["erro"]:
        estado = "erro"
    elif t:
        estado = "preparando"
    else:
        estado = "incompleto"  # o servidor foi fechado no meio da preparação
    return {"id": pid, "titulo": meta.get("titulo") or pid, "estado": estado,
            "etapa": t["etapa"] if t else None, "erro": t["erro"] if t else None,
            "criado": meta.get("criado"), "separacao_simples": meta.get("separacao_simples", False)}


class Pedido(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, formato, *args):
        pass

    # ---- respostas
    def enviar(self, corpo, tipo="application/json; charset=utf-8", codigo=200, extra=None):
        if isinstance(corpo, (dict, list)):
            corpo = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
        elif isinstance(corpo, str):
            corpo = corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corpo)

    def erro(self, codigo, mensagem):
        self.enviar({"erro": mensagem}, codigo=codigo)

    def corpo_json(self):
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    # ---- rotas
    def atender(self, metodo):
        try:
            self.rotear(metodo)
        except KeyError:
            self.erro(404, "não encontrado")
        except ValueError as erro:
            self.erro(400, str(erro))
        except Exception as erro:
            traceback.print_exc()
            self.erro(500, str(erro))

    def do_GET(self):
        self.atender("GET")

    def do_POST(self):
        self.atender("POST")

    def do_PUT(self):
        self.atender("PUT")

    def rotear(self, metodo):
        url = urllib.parse.urlparse(self.path)
        caminho = url.path
        q = dict(urllib.parse.parse_qsl(url.query))
        partes = [urllib.parse.unquote(x) for x in caminho.strip("/").split("/")]

        if metodo == "GET" and not caminho.startswith("/api/"):
            arquivo = (PUBLICO / ("index.html" if caminho == "/" else caminho.lstrip("/"))).resolve()
            if PUBLICO not in arquivo.parents or not arquivo.is_file():
                raise KeyError(caminho)
            return self.enviar(arquivo.read_bytes(), TIPOS.get(arquivo.suffix, "application/octet-stream"))

        if partes[:2] == ["api", "projetos"] and len(partes) == 2:
            if metodo == "GET":
                motor.PASTA_DADOS.mkdir(parents=True, exist_ok=True)
                ids = sorted((p.name for p in motor.PASTA_DADOS.iterdir() if p.is_dir()), reverse=True)
                return self.enviar([resumo_projeto(i) for i in ids])
            if metodo == "POST":
                return self.criar(q)

        pid = partes[2] if len(partes) > 2 else None
        acao = partes[3] if len(partes) > 3 else None
        p = pasta(pid)

        if metodo == "GET" and acao is None:
            info = resumo_projeto(pid)
            if info["estado"] == "pronto":
                meta = motor.ler_json(p / "projeto.json")
                analise = motor.ler_json(p / "analise.json")
                proj = abrir(pid)
                info.update({"analise": {k: analise[k] for k in ("bpm", "duracao", "deslocamento", "unidades", "versao")},
                             "timeline": meta["timeline"], "alvo": meta.get("alvo", 165),
                             "duracao_mix": round(proj.duracao(meta["timeline"]), 2)})
            return self.enviar(info)

        if metodo == "PUT" and acao == "timeline":
            dados = self.corpo_json()
            proj = abrir(pid)
            timeline = validar_timeline(dados.get("timeline"), proj)
            meta = motor.ler_json(p / "projeto.json")
            meta["timeline"] = timeline
            if "alvo" in dados:
                meta["alvo"] = max(10, min(900, float(dados["alvo"])))
            motor.gravar_json(p / "projeto.json", meta)
            return self.enviar({"ok": True, "duracao_mix": round(proj.duracao(timeline), 2)})

        if metodo == "POST" and acao == "contagem":
            dados = self.corpo_json()
            desloc = int(dados.get("deslocamento", 0)) % 8
            motor.analisar_projeto(p, deslocamento=desloc)
            meta = motor.ler_json(p / "projeto.json")
            meta["timeline"] = motor.timeline_inicial(motor.ler_json(p / "analise.json"))
            motor.gravar_json(p / "projeto.json", meta)
            with trava_abertos:
                abertos.pop(pid, None)
            return self.enviar({"ok": True})

        if metodo == "POST" and acao == "audio":
            # Corpo: {"timeline": [...]} — devolve o WAV da mistura e o início de cada bloco no cabeçalho.
            proj = abrir(pid)
            timeline = validar_timeline(self.corpo_json().get("timeline"), proj)
            audio, inicios = proj.montar(timeline)
            return self.enviar(motor.para_wav(audio), "audio/wav", extra={"X-Inicios": json.dumps(inicios)})

        if metodo == "GET" and acao == "unidade":
            proj = abrir(pid)
            uid = partes[4] if len(partes) > 4 else ""
            if uid not in proj.unidades:
                raise KeyError(uid)
            return self.enviar(motor.para_wav(proj.unidade_original(uid)), "audio/wav")

        if metodo == "POST" and acao == "exportar":
            dados = self.corpo_json()
            proj = abrir(pid)
            timeline = validar_timeline(dados.get("timeline"), proj)
            meta = motor.ler_json(p / "projeto.json")
            EXPORTADOS.mkdir(parents=True, exist_ok=True)
            nome = re.sub(r'[\\/:*?"<>|]+', "", meta.get("titulo") or pid)[:60].strip() or pid
            arquivo = motor.exportar(proj, timeline, dados.get("formato", "mp3"),
                                     EXPORTADOS / f"{nome} - mix {motor.time.strftime('%Y%m%d-%H%M')}")
            return self.enviar({"ok": True, "arquivo": str(arquivo)})

        raise KeyError(caminho)

    def criar(self, q):
        tipo = self.headers.get("Content-Type", "")
        if tipo.startswith("application/json"):
            link = (self.corpo_json().get("link") or "").strip()
            if not link.startswith("http"):
                return self.erro(400, "link inválido")
            pid = motor.novo_id("youtube")
            (motor.PASTA_DADOS / pid).mkdir(parents=True)
            iniciar_trabalho(pid, {"link": link})
        else:
            nome = urllib.parse.unquote(self.headers.get("X-Nome", "musica"))
            n = int(self.headers.get("Content-Length") or 0)
            pid = motor.novo_id(Path(nome).stem)
            destino = motor.PASTA_DADOS / pid
            destino.mkdir(parents=True)
            arquivo = destino / ("enviado" + Path(nome).suffix.lower())
            with open(arquivo, "wb") as f:
                restante = n
                while restante > 0:
                    pedaco = self.rfile.read(min(1 << 20, restante))
                    if not pedaco:
                        break
                    f.write(pedaco)
                    restante -= len(pedaco)
            iniciar_trabalho(pid, {"arquivo": str(arquivo), "nome": nome})
        return self.enviar({"id": pid})


def validar_timeline(timeline, proj):
    if not isinstance(timeline, list):
        raise ValueError("linha do tempo inválida")
    saida = []
    for b in timeline:
        if b.get("u") not in proj.unidades:
            raise ValueError(f"unidade desconhecida: {b.get('u')}")
        faixas = {f: max(0.0, min(2.0, float((b.get("faixas") or {}).get(f, 1)))) for f in motor.FAIXAS}
        vel = float(b.get("vel", 1))
        saida.append({"u": b["u"], "faixas": faixas, "vel": vel if vel in motor.VELOCIDADES else 1})
    return saida


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=3060)
    p.add_argument("--sem-navegador", action="store_true")
    a = p.parse_args()
    motor.PASTA_DADOS.mkdir(parents=True, exist_ok=True)
    url = f"http://127.0.0.1:{a.porta}"
    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", a.porta), Pedido)
    except OSError:
        print(f"O editor já está aberto em {url}", flush=True)
        if not a.sem_navegador:
            webbrowser.open(url)
        return
    print(f"Editor do Audio Remix em {url}  (feche esta janela para desligar)", flush=True)
    if not a.sem_navegador:
        webbrowser.open(url)
    servidor.serve_forever()


if __name__ == "__main__":
    main()
