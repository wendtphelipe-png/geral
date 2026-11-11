"""Cria um mix de competição sozinho, a partir da análise da música.

Segue os padrões tirados das apresentações da Brotherhood na IDL (DESCOBERTAS.md):
- uma música âncora, picotada em blocos de 2 a 4 oitos, sempre cortando na batida;
- abertura sem grave e depois a "queda" com tudo;
- o refrão (a parte mais forte e repetida) volta várias vezes;
- respiros de 1 oito sem grave ou sem bateria;
- um trecho em meio tempo;
- paradas curtas (cerca de 2,6 por minuto), principalmente no tempo 8 antes de um corte;
- eco "jogado" na voz antes de um respiro;
- final na voz, com reverb e fade.

Cada bloco sai com um "papel" (o motivo de estar ali), que a tela mostra.
"""
import random

FAIXAS = ["voz", "bateria", "baixo", "outros"]


def _bloco(u, papel, **extra):
    b = {"u": u["id"], "faixas": {f: 1.0 for f in FAIXAS}, "vel": 1, "papel": papel}
    b.update(extra)
    return b


def _medidas(u):
    onda = u.get("onda") or {}
    media = {f: (sum(onda.get(f, [0])) / max(1, len(onda.get(f, [0])))) for f in FAIXAS}
    return {"forca": sum(media.values()), "voz": media["voz"], "grave": media["baixo"]}


def secoes(oitos):
    """Junta oitos seguidos com a mesma parte (A, B, C...)."""
    lista = []
    for u in oitos:
        p = u.get("parte") or "?"
        if lista and lista[-1]["parte"] == p:
            lista[-1]["oitos"].append(u)
        else:
            lista.append({"parte": p, "oitos": [u]})
    return lista


def achar_refrao(lista, medidas):
    """A parte que mais se repete e tem mais energia (e voz) costuma ser o refrão."""
    por_parte = {}
    for s in lista:
        d = por_parte.setdefault(s["parte"], {"vezes": 0, "forca": [], "voz": []})
        d["vezes"] += 1
        for u in s["oitos"]:
            d["forca"].append(medidas[u["id"]]["forca"])
            d["voz"].append(medidas[u["id"]]["voz"])
    def nota(p):
        d = por_parte[p]
        forca = sum(d["forca"]) / len(d["forca"])
        voz = sum(d["voz"]) / len(d["voz"])
        return min(d["vezes"], 4) * forca * (0.6 + voz)
    return max(por_parte, key=nota) if por_parte else None


def criar_mix(analise, alvo=165, semente=1, meio_tempo=True):
    """Devolve (linha do tempo, roteiro em texto)."""
    sorteio = random.Random(semente)
    bpm = float(analise.get("bpm") or 120)
    batida = 60.0 / bpm
    unidades = analise["unidades"]
    oitos = [u for u in unidades if u["tipo"] == "oito"]
    if not oitos:
        return [_bloco(u, "Original") for u in unidades], ["A música é curta demais para montar um mix."]
    dur = {u["id"]: (u["fim"] - u["ini"]) / 44100 for u in unidades}
    medidas = {u["id"]: _medidas(u) for u in oitos}
    lista = secoes(oitos)
    refrao = achar_refrao(lista, medidas)
    tem_voz = sum(m["voz"] for m in medidas.values()) / len(medidas) > 0.08
    nome_parte = lambda p: "Refrão" if p == refrao else f"Parte {p}"

    # oitos do refrão, do mais forte para o mais fraco
    oitos_refrao = [u for s in lista if s["parte"] == refrao for u in s["oitos"]] or oitos
    mais_fortes = sorted(oitos_refrao, key=lambda u: -medidas[u["id"]]["forca"])

    linha, roteiro = [], []

    # 1. Abertura: um oito marcante (com voz), sem grave e sem bateria, com um pouco de reverb
    abertura = max(oitos_refrao[: max(2, len(oitos_refrao) // 2)], key=lambda u: medidas[u["id"]]["voz"])
    linha.append(_bloco(abertura, "Abertura sem grave",
                        faixas={"voz": 1.0, "bateria": 0.0, "baixo": 0.0, "outros": 1.0} if tem_voz else
                        {"voz": 1.0, "bateria": 0.0, "baixo": 0.0, "outros": 0.8},
                        fx={"tudo": {"reverb": 0.3}}, paradas=[[7, 1.0]]))
    roteiro.append("Abertura: 1 oito do refrão sem grave e sem bateria, com reverb, e uma parada no tempo 8 antes da queda.")

    # 2. Corpo: percorre a música na ordem, pegando 2 a 4 oitos de cada seção, o refrão pode voltar
    oito_dur = 8 * batida
    reserva_final = oito_dur
    corpo_alvo = alvo - dur[abertura["id"]] - reserva_final
    usados_por_parte = {}
    segmentos = []
    tempo = 0.0
    ordem = list(range(len(lista)))
    volta = 0
    while tempo < corpo_alvo - oito_dur / 2 and volta < 4:
        for k in ordem:
            s = lista[k]
            vezes = usados_por_parte.get(s["parte"], 0)
            limite = 3 if s["parte"] == refrao else 2
            if vezes >= limite:
                continue
            tam = sorteio.choices([2, 3, 4], weights=[3, 4, 3])[0]
            tam = min(tam, len(s["oitos"]))
            restante = corpo_alvo - tempo
            tam = max(1, min(tam, round(restante / oito_dur)))
            if tam <= 0:
                break
            # na segunda vez de uma parte, pega outro pedaço dela (se der)
            inicio = 0 if vezes == 0 or len(s["oitos"]) <= tam else sorteio.randrange(0, len(s["oitos"]) - tam + 1)
            pedaco = s["oitos"][inicio:inicio + tam]
            segmentos.append({"parte": s["parte"], "oitos": pedaco})
            usados_por_parte[s["parte"]] = vezes + 1
            tempo += sum(dur[u["id"]] for u in pedaco)
            if tempo >= corpo_alvo - oito_dur / 2:
                break
        volta += 1
        usados_por_parte = {p: max(0, v - 1) for p, v in usados_por_parte.items()}  # libera para mais uma volta

    # o primeiro bloco do corpo é a "queda": começa num pedaço forte
    if segmentos and segmentos[0]["parte"] != refrao:
        segmentos.insert(0, {"parte": refrao, "oitos": [mais_fortes[0]]})

    blocos_corpo = []
    for n, seg in enumerate(segmentos):
        for j, u in enumerate(seg["oitos"]):
            papel = "Queda (tudo entra)" if n == 0 and j == 0 else nome_parte(seg["parte"])
            b = _bloco(u, papel)
            if j == len(seg["oitos"]) - 1 and n < len(segmentos) - 1 and sorteio.random() < 0.65:
                b["paradas"] = [[7, 0.5]]  # parada no 8, logo antes do corte
            blocos_corpo.append(b)

    # 3. Respiros: perto de 40% e 72% do corpo
    total = len(blocos_corpo)
    respiros = []
    for fracao, tipo in ((0.4, sorteio.choice(["grave", "bateria"])), (0.72, None)):
        if total < 6:
            break
        i = max(1, min(total - 2, int(total * fracao)))
        tipo = tipo or ("bateria" if respiros and respiros[0][1] == "grave" else "grave")
        b = blocos_corpo[i]
        if tipo == "grave":
            b["faixas"]["baixo"] = 0.0
            b["papel"] = "Respiro sem grave"
        else:
            b["faixas"]["bateria"] = 0.0
            b["faixas"]["baixo"] = 0.3
            b["papel"] = "Respiro sem bateria"
        b.pop("paradas", None)
        anterior = blocos_corpo[i - 1]
        if tem_voz:  # eco "jogado" na voz, que vaza para dentro do respiro
            anterior.setdefault("fx", {})["voz"] = {"eco": 0.55}
            anterior["paradas"] = [[7, 0.5]]
        respiros.append((i, tipo))

    # 4. Meio tempo: 1 oito do refrão em câmera lenta, perto de 55% (vale por 2 oitos de tempo)
    if meio_tempo and total >= 8:
        i = int(total * 0.56)
        if all(i != r[0] for r in respiros):
            b = blocos_corpo[i]
            b["vel"] = 0.5
            b["papel"] = "Meio tempo"
            b.pop("paradas", None)
            # para não passar da duração, tira o bloco seguinte (o meio tempo dura o dobro)
            if i + 1 < len(blocos_corpo) - 1:
                blocos_corpo.pop(i + 1)

    # 5. Paradas extras no tempo 5 até chegar a cerca de 2,6 por minuto
    def contar():
        return sum(len(b.get("paradas", [])) for b in linha + blocos_corpo)
    dur_total = sum(dur[b["u"]] / b["vel"] for b in linha + blocos_corpo) + oito_dur
    meta = round(2.6 * dur_total / 60)
    candidatos = [b for b in blocos_corpo if b["vel"] == 1 and "Respiro" not in b["papel"] and not b.get("paradas")]
    sorteio.shuffle(candidatos)
    for b in candidatos:
        if contar() >= meta:
            break
        b["paradas"] = [[4, 0.5]]
    linha.extend(blocos_corpo)
    roteiro.append(f"Corpo: {len(segmentos)} trechos de 2 a 4 oitos na ordem da música, cortando sempre na batida; "
                   f"o refrão aparece {sum(1 for s in segmentos if s['parte'] == refrao)} vezes.")
    roteiro.append(f"Paradas: {contar()} no total (meta de cerca de 2,6 por minuto), a maioria no tempo 8 antes de um corte.")

    # 6. Final na voz: refrão só com voz (ou só com a melodia), reverb e fade de saída
    ultimo = mais_fortes[min(1, len(mais_fortes) - 1)]
    faixas_fim = {"voz": 1.0, "bateria": 0.0, "baixo": 0.0, "outros": 0.25} if tem_voz else \
        {"voz": 0.0, "bateria": 0.0, "baixo": 0.3, "outros": 1.0}
    linha.append(_bloco(ultimo, "Final na voz" if tem_voz else "Final suave", faixas=faixas_fim,
                        fx={"tudo": {"reverb": 0.55}},
                        env=[[0, 1], [0.5, 1], [0.75, 0.7], [1, 0]]))
    roteiro.append("Final: 1 oito do refrão quase só com a voz, com reverb e fade de saída (pose final).")

    for n, b in enumerate(linha, 1):
        if b["papel"].startswith("Respiro"):
            roteiro.insert(-1, f"{b['papel']} no bloco {n}" + (", com eco jogado na voz antes." if tem_voz else "."))
        elif b["papel"] == "Meio tempo":
            roteiro.insert(-1, f"Meio tempo no bloco {n}: 1 oito em câmera lenta (dura o dobro).")
    duracao = sum(dur[b["u"]] / b["vel"] for b in linha)
    roteiro.insert(0, f"Mix de {int(duracao // 60)}:{int(duracao % 60):02d} (alvo {int(alvo // 60)}:{int(alvo % 60):02d}), "
                      f"{len(linha)} blocos, refrão = parte {refrao}.")
    return linha, roteiro
