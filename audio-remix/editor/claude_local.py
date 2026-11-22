"""Claude da assinatura do Phelipe (pelo Claude Code instalado no PC) para entender pedidos livres.

As regras de comandos.js entendem os pedidos comuns de graça e na hora. Quando elas não
entendem, a tela pergunta aqui: o Claude Code roda no modo sem conversa (`claude -p`), com a
conta já logada no PC, e devolve as MESMAS ações que as regras usam. Assim não há cobrança por
API: o uso sai da cota da assinatura. Só funciona no PC em que o Claude Code está instalado e
logado (rode `claude` num terminal uma vez para entrar na conta).

O Claude roda sem nenhuma ferramenta, sem servidores MCP, sem guardar a sessão e numa pasta
vazia: ele só lê o pedido e escreve o JSON. Toda ação que volta é conferida aqui antes de
chegar à tela.
"""
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

MODELO = "sonnet"
ESPERA = 90  # segundos

FAIXAS = ["voz", "bateria", "baixo", "outros"]

INSTRUCOES = """Você é o entendedor de pedidos do Audio Remix, um editor de mixes para competições de danças urbanas.
O usuário seleciona trechos da linha do tempo (blocos; cada bloco é um "oito" da música, 8 tempos) e escreve um pedido em português.
Transforme o pedido em ações do editor. Responda SOMENTE com um objeto JSON, sem texto antes ou depois:
{"acoes": [...], "frases": ["o que foi feito, curto, em português simples"], "explicacao": "só se não der para fazer"}

Ações possíveis (use só estas, com estes campos):
- {"tipo":"faixas","mudancas":{"<faixa>":{"set":0..2} ou {"mult":0..2}}}  volume das faixas voz, bateria, baixo, outros (1 = original, 0 = tirar).
- {"tipo":"fx","alvo":["voz"|"bateria"|"baixo"|"outros"|"tudo"],"fx":{"eco":0..1,"reverb":0..1,"filtro":"abafado"|"radio","distante":true,"batidas_eco":0.25..2}}
- {"tipo":"semFx","alvo":null ou ["voz",...]}  tira efeitos.
- {"tipo":"paradas","tempos":[1..8],"dur":0.25..4}  silêncio curto (hit/stop) nesses tempos da contagem; dur em tempos (0.5 = meio tempo).
- {"tipo":"semParadas"}
- {"tipo":"fade","dir":"in"|"out"} com opcional "seg":segundos ou "tempos":n
- {"tipo":"semFade"}
- {"tipo":"dividir","partes":2|4|8}
- {"tipo":"vel","valor":0.5|1|2}  meio tempo, normal, tempo dobrado.
- {"tipo":"repetir","n":1..16}
- {"tipo":"apagar"}  apaga os blocos selecionados.
- {"tipo":"trazer","faixa":"voz"|"bateria"|"baixo"|"outros"|"tudo","oito":N,"fx":{...},"ganho":0..2}  copia a faixa do oito N da música original para uma camada por cima da seleção.

Dicas de linguagem de dança e de mix:
- "mais pesado", "mais grave", "mais pancada" = baixo e bateria mais altos (mult 1.3 a 1.5).
- "mais limpo", "respiro", "dar um respiro" = tirar o baixo, ou a bateria, conforme o pedido.
- "hit", "acento", "stop", "pausa", "corte seco" = paradas. "nos tempos fortes" = 1 e 5.
- "acapella" ou "só a voz" = voz 1, bateria 0, baixo 0, outros 0 ou 0.15.
- "drop", "queda", "entrar com tudo" = todas as faixas em 1 (bateria e baixo até 1.2), SEM parada no tempo 1:
  o drop precisa bater cheio no 1. Se pedirem impacto, a parada vai no tempo 8.
- Volume: prefira de 1.2 a 1.4 para "mais alto"; acima de 1.5 o mix inteiro é abaixado para não distorcer.
- "sumindo", "terminar suave" = fade out. "entrar suave" = fade in.
- "eco jogado", "voz voando" = eco 0.5 a 0.7 na voz.
Se o pedido pedir algo que estas ações não fazem (mudar o tom, criar som novo, trocar o estilo), devolva "acoes": [] e explique em "explicacao", em uma frase simples. Nunca invente ações ou campos."""


def executavel():
    achado = shutil.which("claude")
    if achado:
        return achado
    for candidato in (Path.home() / ".local" / "bin" / "claude.exe", Path.home() / ".local" / "bin" / "claude"):
        if candidato.exists():
            return str(candidato)
    return None


def _numero(v, minimo, maximo, padrao=None):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return padrao
    return max(minimo, min(maximo, v))


def _fx(fx):
    if not isinstance(fx, dict):
        return {}
    saida = {}
    for k in ("eco", "reverb"):
        if k in fx and _numero(fx[k], 0, 1) is not None:
            saida[k] = round(_numero(fx[k], 0, 1), 3)
    if fx.get("filtro") in ("abafado", "radio"):
        saida["filtro"] = fx["filtro"]
    if fx.get("distante") is True:
        saida["distante"] = True
    if "batidas_eco" in fx and _numero(fx["batidas_eco"], 0.25, 2) is not None:
        saida["batidas_eco"] = _numero(fx["batidas_eco"], 0.25, 2)
    return saida


def validar(acoes):
    """Só passam as ações que o editor conhece, com valores dentro dos limites."""
    saida = []
    for a in acoes if isinstance(acoes, list) else []:
        if not isinstance(a, dict):
            continue
        t = a.get("tipo")
        if t == "faixas" and isinstance(a.get("mudancas"), dict):
            m = {}
            for f, v in a["mudancas"].items():
                if f in FAIXAS and isinstance(v, dict):
                    if "set" in v and _numero(v["set"], 0, 2) is not None:
                        m[f] = {"set": round(_numero(v["set"], 0, 2), 3)}
                    elif "mult" in v and _numero(v["mult"], 0, 2) is not None:
                        m[f] = {"mult": round(_numero(v["mult"], 0, 2), 3)}
            if m:
                saida.append({"tipo": "faixas", "mudancas": m})
        elif t == "fx":
            alvo = [x for x in (a.get("alvo") or []) if x in FAIXAS + ["tudo"]] or ["tudo"]
            fx = _fx(a.get("fx"))
            if fx:
                saida.append({"tipo": "fx", "alvo": alvo, "fx": fx})
        elif t == "semFx":
            alvo = [x for x in (a.get("alvo") or []) if x in FAIXAS + ["tudo"]] if a.get("alvo") else None
            saida.append({"tipo": "semFx", "alvo": alvo or None})
        elif t == "paradas":
            tempos = sorted({int(x) for x in (a.get("tempos") or []) if isinstance(x, (int, float)) and 1 <= x <= 8})
            if tempos:
                saida.append({"tipo": "paradas", "tempos": tempos, "dur": _numero(a.get("dur"), 0.25, 4, 0.5)})
        elif t in ("semParadas", "semFade", "apagar"):
            saida.append({"tipo": t})
        elif t == "fade" and a.get("dir") in ("in", "out"):
            f = {"tipo": "fade", "dir": a["dir"]}
            if _numero(a.get("seg"), 0.1, 120) is not None:
                f["seg"] = _numero(a["seg"], 0.1, 120)
            elif _numero(a.get("tempos"), 1, 256) is not None:
                f["tempos"] = _numero(a["tempos"], 1, 256)
            saida.append(f)
        elif t == "dividir" and a.get("partes") in (2, 4, 8):
            saida.append({"tipo": "dividir", "partes": a["partes"]})
        elif t == "vel" and a.get("valor") in (0.5, 1, 2):
            saida.append({"tipo": "vel", "valor": a["valor"]})
        elif t == "repetir":
            saida.append({"tipo": "repetir", "n": int(_numero(a.get("n"), 1, 16, 1))})
        elif t == "trazer" and (a.get("faixa") in FAIXAS + ["tudo"]) and _numero(a.get("oito"), 1, 999) is not None:
            saida.append({"tipo": "trazer", "faixa": a["faixa"], "oito": str(int(_numero(a["oito"], 1, 999))),
                          "fx": _fx(a.get("fx")), "ganho": _numero(a.get("ganho"), 0, 2, 1.0)})
    # "trazer" funciona sozinho na tela (como nas regras)
    trazer = [a for a in saida if a["tipo"] == "trazer"]
    return trazer[:1] if trazer else saida


def _json_da_resposta(texto):
    texto = (texto or "").strip()
    texto = re.sub(r"^```(?:json)?\s*|\s*```$", "", texto)
    inicio, fim = texto.find("{"), texto.rfind("}")
    if inicio < 0 or fim <= inicio:
        raise ValueError("o Claude não respondeu no formato esperado")
    return json.loads(texto[inicio:fim + 1])


def traduzir(pedido, contexto):
    """Devolve {"acoes": [...], "frases": [...], "explicacao": str}. Erros viram RuntimeError com
    uma mensagem que a tela pode mostrar direto."""
    exe = executavel()
    if not exe:
        raise RuntimeError("o Claude Code não está instalado neste PC")
    mensagem = (f"Contexto do editor: {json.dumps(contexto, ensure_ascii=False)}\n\n"
                f"Pedido do usuário sobre os blocos selecionados: {pedido}")
    with tempfile.TemporaryDirectory(prefix="audio-remix-claude-") as vazia:
        try:
            r = subprocess.run(
                [exe, "-p", "--output-format", "json", "--model", MODELO, "--tools", "",
                 "--strict-mcp-config", "--no-session-persistence", "--system-prompt", INSTRUCOES],
                input=mensagem, capture_output=True, text=True, encoding="utf-8", timeout=ESPERA, cwd=vazia)
        except subprocess.TimeoutExpired:
            raise RuntimeError("o Claude demorou demais para responder; tente de novo")
    try:
        saida = json.loads(r.stdout)
    except ValueError:
        raise RuntimeError(f"o Claude Code não respondeu: {(r.stderr or r.stdout or '').strip()[:200]}")
    resultado = str(saida.get("result") or "")
    if saida.get("is_error"):
        if re.search(r"auth|login|OAuth|expired", resultado, re.I):
            raise RuntimeError("o Claude Code deste PC não está logado: abra um terminal, rode \"claude\" e entre na sua conta")
        if re.search(r"limit|quota|usage", resultado, re.I):
            raise RuntimeError("a cota da sua assinatura do Claude acabou por agora; tente mais tarde")
        raise RuntimeError(f"o Claude recusou: {resultado[:200]}")
    dados = _json_da_resposta(resultado)
    frases = [str(f)[:160] for f in (dados.get("frases") or []) if isinstance(f, str)][:6]
    return {"acoes": validar(dados.get("acoes")), "frases": frases, "explicacao": str(dados.get("explicacao") or "")[:300]}
