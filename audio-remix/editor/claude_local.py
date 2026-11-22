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
ESTILOS = ["house", "breaking", "locking", "popping", "hiphop", "waacking", "vogue", "krump", "passinho", "dancehall", "afro"]

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
- {"tipo":"estilo","estilo":"house"|"breaking"|"locking"|"popping"|"hiphop"|"waacking"|"vogue"|"krump"|"passinho"|"dancehall"|"afro"}
  troca o ritmo da seleção: a bateria original fica baixa e a bateria do estilo entra por cima, no BPM da música.
  "passinho" = funk carioca; "afro" = afro/amapiano; "hiphop" = hip-hop dance; "breaking" = b-boy/break.
  Pode vir junto com outras ações (ex.: estilo + paradas). Para estilos fora desta lista (trap, reggaeton...), escolha o
  mais próximo e diga em "frases" que foi uma aproximação; se nenhum servir, explique.

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
        elif t == "estilo" and a.get("estilo") in ESTILOS:
            saida.append({"tipo": "estilo", "estilo": a["estilo"]})
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


def _perguntar(instrucoes, mensagem):
    """Roda o Claude Code sem conversa, sem ferramentas e numa pasta vazia; devolve o JSON da resposta."""
    exe = executavel()
    if not exe:
        raise RuntimeError("o Claude Code não está instalado neste PC")
    with tempfile.TemporaryDirectory(prefix="audio-remix-claude-") as vazia:
        try:
            r = subprocess.run(
                [exe, "-p", "--output-format", "json", "--model", MODELO, "--tools", "",
                 "--strict-mcp-config", "--no-session-persistence", "--system-prompt", instrucoes],
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
    return _json_da_resposta(resultado)


def traduzir(pedido, contexto):
    """Devolve {"acoes": [...], "frases": [...], "explicacao": str}. Erros viram RuntimeError com
    uma mensagem que a tela pode mostrar direto."""
    mensagem = (f"Contexto do editor: {json.dumps(contexto, ensure_ascii=False)}\n\n"
                f"Pedido do usuário sobre os blocos selecionados: {pedido}")
    dados = _perguntar(INSTRUCOES, mensagem)
    frases = [str(f)[:160] for f in (dados.get("frases") or []) if isinstance(f, str)][:6]
    return {"acoes": validar(dados.get("acoes")), "frases": frases, "explicacao": str(dados.get("explicacao") or "")[:300]}


# ---------------------------------------------------------------- o Claude compõe padrões de estilo

INSTRUCOES_COMPOR = """Você é um produtor experiente de trilhas para competições de danças urbanas (breaking, locking, popping, hip-hop, house, waacking, vogue, krump, passinho, dancehall, afro).
Componha UM padrão de bateria e baixo de 2 compassos (32 semicolcheias) no estilo pedido. Ele será tocado por um motor que usa os sons da própria música (bumbo, caixa, chimbal e notas do baixo dela) e coloca cada passo em cima das batidas reais da música.
Responda SOMENTE com JSON, sem texto antes ou depois:
{"nome": "nome curto em português que descreva o groove", "bateria": {"<peça>": "<16 ou 32 caracteres>"}, "baixo": [[passo, "função", duração, força], ...]}

Bateria
- Peças: bumbo, caixa, palma, chimbal, chimbal_aberto, shaker, ha, impacto, tambor, log_drum. Use só as que o estilo pede.
- Cada caractere é uma semicolcheia: X forte, x normal, o fantasma (bem fraco), . silêncio.
- 16 caracteres repetem nos dois compassos; 32 caracteres = os dois compassos (use para variar o segundo, por exemplo uma virada curta no fim).
- Posições: 0 = tempo 1, 4 = tempo 2, 8 = tempo 3, 12 = tempo 4, 16 = tempo 5, 20 = tempo 6, 24 = tempo 7, 28 = tempo 8.

Baixo
- [passo 0-31, função, duração em semicolcheias 1-16, força 0.3-1]. Passos só de 0 a 15 repetem nos dois compassos.
- Funções (o motor converte nas notas certas de cada tempo; NUNCA escreva nomes de notas):
  T tônica do acorde, 5 quinta, 8 oitava acima, 3 terça do acorde, b7 sétima menor, 6 sexta,
  N a nota que o baixo original toca naquele tempo, A aproximação (meio tom abaixo da próxima tônica; curta, no passo logo antes de um tempo forte).
- O baixo é monofônico: uma nota termina quando a próxima começa.

Qualidade (o mais importante)
- Groove autêntico do estilo pedido, com a assinatura dele.
- Bumbo e baixo conversando: o baixo costuma cair junto com o bumbo ou responder a ele.
- Espaço para a música e para a dança: não encha todos os passos; silêncios e acentos fazem o groove.
- A maioria das notas do baixo deve ser T, 5 ou 8 (soam bem em qualquer acorde); use 3, b7, 6 e A com moderação.
- Seja diferente das variações que já existem (o pedido lista os nomes delas)."""


def compor(estilo, info, bpm, progressao, existentes, exemplo, pedido=""):
    """Um padrão novo do estilo, composto pelo Claude (cota da assinatura). Devolve o padrão validado."""
    import compositor
    mensagem = json.dumps({
        "estilo": estilo, "nome": info.get("nome"), "groove": info.get("groove"), "assinatura": info.get("assinatura"),
        "swing": info.get("swing"), "bpm_da_musica": round(bpm), "bpm_tipico_do_estilo": info.get("bpm"),
        "pecas_tipicas": list(info.get("padrao", {}).keys()),
        "progressao_do_trecho": progressao,
        "variacoes_que_ja_existem": existentes,
        "exemplo_do_formato": exemplo,
        "pedido_do_usuario": pedido or "nenhum: crie a variação que você acha que vai soar melhor",
    }, ensure_ascii=False)
    dados = _perguntar(INSTRUCOES_COMPOR, mensagem)
    padrao = compositor.validar(dados)
    padrao["nome"] = "Claude: " + padrao["nome"]
    return padrao
