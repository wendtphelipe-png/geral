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

import numpy as np

import arranjador
import bateria
import efeitos
import ia
import motor
import padrao

PUBLICO = motor.AQUI / "public"
EXPORTADOS = motor.PASTA_DADOS.parent / "exportados"
TIPOS = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
         ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml"}

abertos = {}          # id -> motor.Projeto
trabalhos = {}        # id -> {"etapa": str, "erro": str|None, "pronto": bool}
trava_abertos = threading.Lock()
PASTA_ESTRUTURAS = motor.PASTA_DADOS.parent / "estruturas"
PASTA_PADROES = motor.PASTA_DADOS.parent / "padroes"
analises = {}         # id -> {"etapa", "erro", "resultado"}


def lista_estruturas():
    cat = arranjador.catalogo()
    salvas = []
    if PASTA_ESTRUTURAS.is_dir():
        for f in sorted(PASTA_ESTRUTURAS.glob("*.json")):
            e = motor.ler_json(f)
            if e:
                e["id"], e["salva"] = f.stem, True
                salvas.append(e)
    return {"modos": cat["modos"], "estruturas": cat["estruturas"] + salvas,
            "estilos": [{"id": i, "nome": e["nome"], "bpm": e["bpm"], "padrao": e["padrao"]} for i, e in bateria.estilos().items()]}


def validar_estrutura(e):
    if not isinstance(e, dict) or not isinstance(e.get("passos"), list) or not e["passos"]:
        raise ValueError("estrutura sem passos")
    modos = {m["id"] for m in arranjador.catalogo()["modos"]}
    passos = []
    for p in e["passos"][:60]:
        if p.get("modo") not in modos:
            raise ValueError(f"modo desconhecido: {p.get('modo')}")
        passo = {"modo": p["modo"], "oitos": "auto" if p.get("oitos") == "auto" else int(numero(p.get("oitos", 1), 1, 32, 1))}
        if p.get("estilo") in bateria.estilos():
            passo["estilo"] = p["estilo"]
        if p.get("peso"):
            passo["peso"] = round(numero(p["peso"], 0.1, 200, 1), 2)
        passos.append(passo)
    return {"nome": str(e.get("nome") or "Minha estrutura")[:60], "desc": str(e.get("desc") or "")[:400],
            "paradas": e.get("paradas") if e.get("paradas") in arranjador.PARADAS_POR_MINUTO else "normal",
            "passos": passos, **({"origem": str(e["origem"])[:80]} if e.get("origem") else {})}


def iniciar_analise(aid, origem):
    analises[aid] = {"etapa": "começando", "erro": None, "resultado": None}

    def avisar(etapa):
        analises[aid]["etapa"] = etapa
        print(f"[análise {aid}] {etapa}", flush=True)

    def rodar():
        try:
            analises[aid]["resultado"] = padrao.rodar(PASTA_PADROES / aid, origem, avisar)
            avisar("pronto")
        except Exception as erro:
            traceback.print_exc()
            analises[aid]["erro"] = str(erro)

    threading.Thread(target=rodar, daemon=True).start()


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

    def do_DELETE(self):
        self.atender("DELETE")

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

        if partes[:2] == ["api", "ia"]:
            if metodo == "GET":
                return self.enviar({"configurada": bool(ia.chave())})
            if metodo == "POST" and partes[2:] == ["chave"]:
                valor = (self.corpo_json().get("chave") or "").strip()
                if len(valor) < 20:
                    return self.erro(400, "essa chave parece incompleta")
                ia.salvar_chave(valor)
            if metodo == "POST" and partes[2:] in (["chave"], ["testar"]):
                try:
                    return self.enviar(ia.testar())
                except Exception as erro:
                    return self.erro(400, f"o Google recusou: {str(erro)[:300]}")

        if partes[:2] == ["api", "estruturas"]:
            if metodo == "GET":
                return self.enviar(lista_estruturas())
            if metodo == "POST":
                e = validar_estrutura(self.corpo_json())
                PASTA_ESTRUTURAS.mkdir(parents=True, exist_ok=True)
                eid = re.sub(r"[^\w\-]+", "-", e["nome"].lower()).strip("-")[:40] or "estrutura"
                eid = f"{eid}-{motor.time.strftime('%m%d%H%M%S')}"
                motor.gravar_json(PASTA_ESTRUTURAS / f"{eid}.json", e)
                return self.enviar({"ok": True, "id": eid})
            if metodo == "DELETE" and len(partes) == 3 and re.fullmatch(r"[\w\-]+", partes[2]):
                (PASTA_ESTRUTURAS / f"{partes[2]}.json").unlink(missing_ok=True)
                return self.enviar({"ok": True})

        if partes[:2] == ["api", "padroes"]:
            if metodo == "POST" and len(partes) == 2:
                aid = motor.novo_id("analise")
                destino = PASTA_PADROES / aid
                destino.mkdir(parents=True)
                if self.headers.get("Content-Type", "").startswith("application/json"):
                    link = (self.corpo_json().get("link") or "").strip()
                    if not link.startswith("http"):
                        return self.erro(400, "link inválido")
                    iniciar_analise(aid, {"link": link})
                else:
                    nome = urllib.parse.unquote(self.headers.get("X-Nome", "mix"))
                    arquivo = destino / ("enviado" + Path(nome).suffix.lower())
                    self.receber_arquivo(arquivo, int(self.headers.get("Content-Length") or 0))
                    iniciar_analise(aid, {"arquivo": str(arquivo), "nome": nome})
                return self.enviar({"id": aid})
            if metodo == "GET" and len(partes) == 3:
                a = analises.get(partes[2])
                if not a:
                    salvo = motor.ler_json(PASTA_PADROES / partes[2] / "resultado.json") if re.fullmatch(r"[\w\-]+", partes[2]) else None
                    if not salvo:
                        raise KeyError(partes[2])
                    a = {"etapa": "pronto", "erro": None, "resultado": salvo}
                return self.enviar(a)

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
                             "mixer": meta.get("mixer") or mixer_padrao(),
                             "camadas": meta.get("camadas") or [],
                             "importados": motor.listar_importados(p),
                             "duracao_mix": round(proj.duracao(meta["timeline"], meta.get("camadas")), 2)})
            return self.enviar(info)

        if metodo == "PUT" and acao == "timeline":
            dados = self.corpo_json()
            proj = abrir(pid)
            timeline = validar_timeline(dados.get("timeline"), proj)
            meta = motor.ler_json(p / "projeto.json")
            meta["timeline"] = timeline
            if isinstance(dados.get("camadas"), list):
                meta["camadas"] = validar_camadas(dados["camadas"], proj, efetivo=False)
            if isinstance(dados.get("mixer"), dict):
                meta["mixer"] = validar_mixer(dados["mixer"])
            if "alvo" in dados:
                meta["alvo"] = max(10, min(900, float(dados["alvo"])))
            motor.gravar_json(p / "projeto.json", meta)
            return self.enviar({"ok": True, "duracao_mix": round(proj.duracao(timeline, meta.get("camadas")), 2)})

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
            dados = self.corpo_json()
            timeline = validar_timeline(dados.get("timeline"), proj)
            audio, inicios = proj.montar(timeline, validar_camadas(dados.get("camadas") or [], proj),
                                         clique=bool(dados.get("clique")))
            return self.enviar(motor.para_wav(audio), "audio/wav", extra={"X-Inicios": json.dumps(inicios)})

        if metodo == "POST" and acao == "gerar":
            dados = self.corpo_json()
            analise = motor.ler_json(p / "analise.json")
            meta = motor.ler_json(p / "projeto.json")
            alvo = numero(dados.get("alvo", meta.get("alvo", 165)), 20, 900, 165)
            if dados.get("estrutura"):
                estrutura = validar_estrutura(dados["estrutura"])
            else:
                todas = lista_estruturas()["estruturas"]
                estrutura = next((e for e in todas if e.get("id") == dados.get("estrutura_id")), todas[0])
            timeline, estilos, roteiro = arranjador.criar_mix(analise, alvo=alvo, semente=int(numero(dados.get("semente", 1), 0, 1e9, 1)),
                                                              estrutura=estrutura)
            bpm = analise.get("bpm") or 120
            if dados.get("usar_ia") and estilos:
                tom = motor.tom_do_projeto(p)
                for c in estilos:
                    try:
                        arquivo, _, modelo = ia.gerar(ia.prompt_estilo(c["estilo"], bpm, tom), "clip")
                        info = motor.salvar_importado(p, ia.encaixar(arquivo, bpm, c["batidas"]), f"{c['nome']} (Lyria)")
                        c["importado"] = info
                        roteiro.append(f"{c['nome']}: criada pelo Lyria ({modelo}) no BPM {round(bpm)} e tom {tom} da música.")
                    except Exception as erro:
                        traceback.print_exc()
                        roteiro.append(f"{c['nome']}: o Lyria falhou ({str(erro)[:120]}); usei a bateria sintetizada.")
            camadas = [{"id": f"auto{n}", "nome": c["nome"] + (" (Lyria)" if c.get("importado") else ""), "ganho": 0.9,
                        "mudo": False, "solo": False, "auto": True,
                        "clipes": [{"id": f"ka{n}", "nome": c["nome"], "pos": c["pos"], "ini": 0, "dur": c["dur"], "ganho": 1,
                                    "fonte": {"tipo": "importado", "id": c["importado"]["id"]} if c.get("importado") else
                                    {"tipo": "estilo", "estilo": c["estilo"], "bpm": bpm, "batidas": c["batidas"]}}]}
                       for n, c in enumerate(estilos)]
            # volume da bateria de estilo igual ao da bateria original naqueles oitos
            proj = abrir(pid)
            for c, cam in zip(estilos, camadas):
                try:
                    ref = [proj.faixas["bateria"][:, proj.unidades[u]["ini"]:proj.unidades[u]["fim"]] for u in c["unidades"]]
                    alvo_rms = float(np.sqrt(np.mean(np.concatenate(ref, axis=1) ** 2))) if ref else 0.1
                    camada_audio = proj.fonte_clipe(cam["clipes"][0]["fonte"])
                    rms = float(np.sqrt(np.mean(camada_audio ** 2))) or 1.0
                    cam["clipes"][0]["ganho"] = round(max(0.15, min(2.0, alvo_rms / rms)), 3)
                    cam["ganho"] = 1.0
                except Exception:
                    traceback.print_exc()
            novos = [c["importado"] for c in estilos if c.get("importado")]
            return self.enviar({"timeline": validar_timeline(timeline, abrir(pid)), "camadas": camadas, "roteiro": roteiro,
                                "importados": novos})

        if metodo == "POST" and acao == "ia-trecho":
            dados = self.corpo_json()
            analise = motor.ler_json(p / "analise.json")
            bpm = analise.get("bpm") or 120
            batidas = int(numero(dados.get("batidas"), 1, 256, 8))
            pedido = str(dados.get("prompt") or "").strip()[:500]
            if not pedido:
                return self.erro(400, "escreva o que a IA deve criar")
            tom = motor.tom_do_projeto(p)
            texto_ia = (f"{pedido}. {round(bpm)} BPM, steady tempo, key of {tom}, made to layer on top of a song in a "
                        f"street dance competition mix, loopable" + ("" if "voz" in pedido.lower() or "vocal" in pedido.lower() else ", no vocals"))
            arquivo, _, modelo = ia.gerar(texto_ia, "clip")
            info = motor.salvar_importado(p, ia.encaixar(arquivo, bpm, batidas), "IA: " + pedido[:40])
            return self.enviar({"importado": info, "modelo": modelo})

        if metodo == "POST" and acao == "importar":
            nome = urllib.parse.unquote(self.headers.get("X-Nome", "audio"))
            n = int(self.headers.get("Content-Length") or 0)
            temporario = p / ("enviado-" + re.sub(r"[^\w.]", "", Path(nome).name)[-60:])
            self.receber_arquivo(temporario, n)
            return self.enviar(motor.importar_audio(p, temporario, nome))

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
            arquivo = motor.exportar(proj, timeline, validar_camadas(dados.get("camadas") or [], proj),
                                     dados.get("formato", "mp3"),
                                     EXPORTADOS / f"{nome} - mix {motor.time.strftime('%Y%m%d-%H%M')}")
            return self.enviar({"ok": True, "arquivo": str(arquivo)})

        raise KeyError(caminho)

    def receber_arquivo(self, caminho, n):
        with open(caminho, "wb") as f:
            restante = n
            while restante > 0:
                pedaco = self.rfile.read(min(1 << 20, restante))
                if not pedaco:
                    break
                f.write(pedaco)
                restante -= len(pedaco)

    def criar(self, q):
        tipo = self.headers.get("Content-Type", "")
        if tipo.startswith("application/json"):
            dados = self.corpo_json()
            if dados.get("ia"):
                pid = motor.novo_id("ia")
                (motor.PASTA_DADOS / pid).mkdir(parents=True)
                iniciar_trabalho(pid, {"ia": str(dados["ia"]).strip()[:1500]})
                return self.enviar({"id": pid})
            link = (dados.get("link") or "").strip()
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
            self.receber_arquivo(arquivo, n)
            iniciar_trabalho(pid, {"arquivo": str(arquivo), "nome": nome})
        return self.enviar({"id": pid})


def mixer_padrao():
    return {f: {"ganho": 1.0, "mudo": False, "solo": False} for f in motor.FAIXAS}


def validar_mixer(mixer):
    saida = mixer_padrao()
    for f in motor.FAIXAS:
        m = mixer.get(f) or {}
        saida[f] = {"ganho": max(0.0, min(2.0, float(m.get("ganho", 1)))),
                    "mudo": bool(m.get("mudo")), "solo": bool(m.get("solo"))}
    return saida


def numero(v, minimo, maximo, padrao):
    try:
        return max(minimo, min(maximo, float(v)))
    except (TypeError, ValueError):
        return padrao


def validar_fx(fx):
    """Efeitos: {"eco": 0..1, "reverb": 0..1, "tamanho": 0..1, "filtro": nome, "batidas_eco": n, "distante": bool}."""
    if not isinstance(fx, dict):
        return None
    saida = {}
    for k in ("eco", "reverb", "tamanho"):
        if fx.get(k):
            saida[k] = round(numero(fx[k], 0, 1, 0), 3)
    if fx.get("batidas_eco"):
        saida["batidas_eco"] = round(numero(fx["batidas_eco"], 0.125, 4, 0.75), 3)
    if fx.get("filtro") in efeitos.FILTROS:
        saida["filtro"] = fx["filtro"]
    if fx.get("distante"):
        saida["distante"] = True
    return saida or None


def validar_timeline(timeline, proj):
    if not isinstance(timeline, list):
        raise ValueError("linha do tempo inválida")
    saida = []
    for b in timeline:
        if b.get("u") not in proj.unidades:
            raise ValueError(f"unidade desconhecida: {b.get('u')}")
        faixas = {f: numero((b.get("faixas") or {}).get(f, 1), 0, 2, 1.0) for f in motor.FAIXAS}
        vel = float(b.get("vel", 1))
        bloco = {"u": b["u"], "faixas": faixas, "vel": vel if vel in motor.VELOCIDADES else 1}
        de, ate = numero(b.get("de", 0), 0, 1, 0.0), numero(b.get("ate", 1), 0, 1, 1.0)
        if ate - de < 0.01:
            raise ValueError("corte pequeno demais")
        if de or ate != 1:
            bloco.update(de=round(de, 5), ate=round(ate, 5))
        for k in ("fi", "fo"):
            if b.get(k):
                bloco[k] = round(numero(b[k], 0, 60, 0), 3)
        if isinstance(b.get("fx"), dict):
            fx = {k: validar_fx(v) for k, v in b["fx"].items() if k in motor.FAIXAS + ["tudo"]}
            fx = {k: v for k, v in fx.items() if v}
            if fx:
                bloco["fx"] = fx
        if isinstance(b.get("paradas"), list):
            paradas = [[round(numero(p[0], 0, 64, 0), 3), round(numero(p[1], 0.05, 16, 0.5), 3)]
                       for p in b["paradas"][:32] if isinstance(p, (list, tuple)) and len(p) == 2]
            if paradas:
                bloco["paradas"] = sorted(paradas)
        if b.get("papel"):
            bloco["papel"] = str(b["papel"])[:40]
        env = b.get("env")
        if isinstance(env, list) and 2 <= len(env) <= 64:
            pontos = sorted((numero(x, 0, 1, 0), numero(g, 0, 2, 1)) for x, g in env)
            bloco["env"] = [[round(x, 4), round(g, 4)] for x, g in pontos]
        saida.append(bloco)
    return saida


def validar_camadas(camadas, proj, efetivo=True):
    """Camadas extras. `efetivo`: o ganho já vem calculado (mudo/solo) pela tela."""
    saida = []
    for cam in camadas[:32]:
        clipes = []
        for c in (cam.get("clipes") or [])[:400]:
            fonte = c.get("fonte") or {}
            if fonte.get("tipo") == "importado":
                if not re.fullmatch(r"a[0-9a-f]{10}", str(fonte.get("id"))) or \
                        not (proj.pasta / "importados" / f"{fonte['id']}.wav").exists():
                    raise ValueError("arquivo importado não encontrado")
                f = {"tipo": "importado", "id": fonte["id"]}
            elif fonte.get("tipo") == "estilo":
                if fonte.get("estilo") not in bateria.estilos():
                    raise ValueError("estilo desconhecido")
                f = {"tipo": "estilo", "estilo": fonte["estilo"], "bpm": numero(fonte.get("bpm"), 40, 220, 120),
                     "batidas": int(numero(fonte.get("batidas"), 1, 1024, 8))}
            elif fonte.get("tipo") == "faixa":
                if fonte.get("u") not in proj.unidades or fonte.get("faixa") not in motor.FAIXAS:
                    raise ValueError("trecho de faixa inválido")
                f = {"tipo": "faixa", "u": fonte["u"], "faixa": fonte["faixa"],
                     "de": numero(fonte.get("de", 0), 0, 1, 0), "ate": numero(fonte.get("ate", 1), 0, 1, 1)}
            else:
                raise ValueError("clipe sem origem")
            clipe = {"id": str(c.get("id", ""))[:20], "fonte": f, "pos": round(numero(c.get("pos"), 0, 3600, 0), 4),
                     "ini": round(numero(c.get("ini"), 0, 3600, 0), 4), "dur": round(numero(c.get("dur"), 0.01, 3600, 1), 4),
                     "ganho": numero(c.get("ganho", 1), 0, 2, 1), "nome": str(c.get("nome", ""))[:80]}
            for k in ("fi", "fo"):
                if c.get(k):
                    clipe[k] = round(numero(c[k], 0, 60, 0), 3)
            fx = validar_fx(c.get("fx"))
            if fx:
                clipe["fx"] = fx
            clipes.append(clipe)
        item = {"id": str(cam.get("id", ""))[:20], "nome": str(cam.get("nome", "Camada"))[:40],
                "ganho": numero(cam.get("ganho", 1), 0, 2, 1), "clipes": clipes}
        if cam.get("auto"):
            item["auto"] = True
        if not efetivo:
            item.update(mudo=bool(cam.get("mudo")), solo=bool(cam.get("solo")))
        saida.append(item)
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
