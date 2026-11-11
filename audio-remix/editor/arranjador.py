"""Cria um mix de competição sozinho, seguindo uma ESTRUTURA.

Uma estrutura é uma sequência de passos ("modos"), por exemplo:
  abertura_sem_grave -> queda -> corpo(auto) -> respiro_sem_grave -> ... -> final_voz
As estruturas prontas e o catálogo de modos ficam em biblioteca/estruturas.json.
As estruturas salvas pelo usuário (montadas à mão ou aprendidas ao analisar um
mix) ficam em dados/estruturas/.

Os padrões vêm das apresentações da Brotherhood na IDL (DESCOBERTAS.md): cortes na
batida a cada 2 a 4 oitos, refrão recorrente, respiros, meio tempo, paradas
(~2,6 por minuto), eco jogado antes de um respiro, final marcante.
"""
import json
import random
from pathlib import Path

FAIXAS = ["voz", "bateria", "baixo", "outros"]
BIBLIOTECA = Path(__file__).resolve().parent.parent / "biblioteca" / "estruturas.json"
PARADAS_POR_MINUTO = {"poucas": 0.5, "normal": 1.2, "densas": 4.0}


def catalogo():
    return json.loads(BIBLIOTECA.read_text(encoding="utf-8"))


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
        return min(d["vezes"], 4) * (sum(d["forca"]) / len(d["forca"])) * (0.6 + sum(d["voz"]) / len(d["voz"]))
    return max(por_parte, key=nota) if por_parte else None


class Montador:
    """Guarda o estado enquanto a estrutura é executada passo a passo."""

    def __init__(self, analise, semente):
        self.sorteio = random.Random(semente)
        self.bpm = float(analise.get("bpm") or 120)
        self.unidades = analise["unidades"]
        self.oitos = [u for u in self.unidades if u["tipo"] == "oito"]
        self.dur = {u["id"]: (u["fim"] - u["ini"]) / 44100 for u in self.unidades}
        self.medidas = {u["id"]: _medidas(u) for u in self.oitos}
        self.lista = secoes(self.oitos)
        self.refrao = achar_refrao(self.lista, self.medidas)
        self.tem_voz = sum(m["voz"] for m in self.medidas.values()) / max(1, len(self.medidas)) > 0.08
        self.oitos_refrao = [u for s in self.lista if s["parte"] == self.refrao for u in s["oitos"]] or self.oitos
        self.fortes = sorted(self.oitos_refrao, key=lambda u: -self.medidas[u["id"]]["forca"])
        self.cursor = 0          # seção atual da música (para "música em ordem")
        # partes fracas (introdução calma, pontes vazias) não entram no meio do corpo
        forca_secao = [sum(self.medidas[u["id"]]["forca"] for u in s["oitos"]) / len(s["oitos"]) for s in self.lista]
        mediana = sorted(forca_secao)[len(forca_secao) // 2] if forca_secao else 0
        self.fraca = [f < 0.6 * mediana for f in forca_secao]
        if all(self.fraca):
            self.fraca = [False] * len(self.lista)
        self.usos = {}           # quantas vezes cada parte já entrou
        self.vez_refrao = 0
        self.linha, self.camadas, self.roteiro = [], [], []
        self.oito_dur = 8 * 60.0 / self.bpm

    # ---- utilidades
    def bloco(self, u, papel, **extra):
        b = {"u": u["id"], "faixas": {f: 1.0 for f in FAIXAS}, "vel": 1, "papel": papel}
        b.update(extra)
        return b

    def nome_parte(self, p):
        return "Refrão" if p == self.refrao else f"Parte {p}"

    def tempo_atual(self):
        return sum(self.dur[b["u"]] / b["vel"] for b in self.linha)

    def continuar_depois(self, u):
        """Depois de usar um oito (por exemplo, o refrão da queda), a música segue da parte seguinte."""
        for k, s in enumerate(self.lista):
            if any(x["id"] == u["id"] for x in s["oitos"]):
                self.cursor = k + 1
                return

    def proximo_refrao(self):
        u = self.oitos_refrao[self.vez_refrao % len(self.oitos_refrao)]
        self.vez_refrao += 1
        return u

    def pegar_em_ordem(self, quantos, tam_min=2, tam_max=4):
        """Trechos da música na ordem original, sempre começando no início de uma frase.

        Uma parte (A, B...) é dividida em frases de 2 ou 4 oitos contadas a partir do começo dela;
        os trechos são frases inteiras, então o corte cai onde a própria música muda."""
        trechos, total, voltas = [], 0, 0
        while total < quantos and voltas < 6:
            if self.cursor >= len(self.lista):
                self.cursor, voltas = 0, voltas + 1
                self.usos = {p: max(0, v - 1) for p, v in self.usos.items()}
                continue
            s = self.lista[self.cursor]
            fraca = self.fraca[self.cursor]
            self.cursor += 1
            if fraca:
                continue
            vezes = self.usos.get(s["parte"], 0)
            if vezes >= (3 if s["parte"] == self.refrao else 2):
                continue
            falta = quantos - total
            frase = tam_max if len(s["oitos"]) >= tam_max else len(s["oitos"])
            if tam_max >= 4 and len(s["oitos"]) >= 4 and self.sorteio.random() < 0.35:
                frase = 2
            frase = max(1, min(frase, falta))
            # nas repetições de uma parte longa, usa outra frase dela (sempre começando numa frase)
            inicios = list(range(0, max(1, len(s["oitos"]) - frase + 1), 2)) or [0]
            inicio = 0 if vezes == 0 else self.sorteio.choice(inicios)
            trechos.append((s["parte"], s["oitos"][inicio:inicio + frase]))
            self.usos[s["parte"]] = vezes + 1
            total += frase
        return trechos

    def camada_estilo(self, estilo, ini, blocos):
        dur = sum(self.dur[b["u"]] / b["vel"] for b in blocos)
        batidas = round(dur / (60.0 / self.bpm))
        self.camadas.append({"nome": f"Bateria {estilo}", "estilo": estilo, "pos": round(ini, 4),
                             "batidas": batidas, "dur": round(dur, 4), "unidades": [b["u"] for b in blocos]})

    # ---- os modos
    def executar(self, passo, n):
        modo = passo["modo"]
        estilo = passo.get("estilo") or "house"
        tv = self.tem_voz
        if modo == "abertura_sem_grave":
            for k in range(n):
                u = max(self.oitos_refrao[: max(2, len(self.oitos_refrao) // 2)], key=lambda x: self.medidas[x["id"]]["voz"]) if k == 0 else self.proximo_refrao()
                b = self.bloco(u, "Abertura sem grave", faixas={"voz": 1.0, "bateria": 0.0, "baixo": 0.0, "outros": 1.0},
                               fx={"tudo": {"reverb": 0.3}})
                if k == n - 1:
                    b["paradas"] = [[7, 0.5]]
                self.linha.append(b)
            self.roteiro.append(f"Abertura: {n} oito(s) do refrão sem grave e sem bateria, com reverb e parada antes da queda.")
        elif modo == "abertura_so_voz":
            for k in range(n):
                u = self.proximo_refrao()
                self.linha.append(self.bloco(u, "Abertura só voz", faixas={"voz": 1.0, "bateria": 0.0, "baixo": 0.0, "outros": 0.15 if tv else 1.0},
                                             fx={"tudo": {"reverb": 0.4}}, paradas=[[7, 0.5]] if k == n - 1 else []))
            self.roteiro.append(f"Abertura: {n} oito(s) só com a voz, com reverb.")
        elif modo == "abertura_original":
            intro = next((u for u in self.unidades if u["tipo"] == "intro" and self.dur[u["id"]] > 1.5), None)
            if intro and self.dur[intro["id"]] < 16:
                self.linha.append(self.bloco(intro, "Começo original"))
            for k in range(n if not intro else max(0, n - 1)):
                self.linha.append(self.bloco(self.oitos[k % len(self.oitos)], "Começo original"))
            self.cursor = 1
            self.roteiro.append("Abertura: o começo original da música.")
        elif modo == "queda":
            # a queda é o começo de uma passagem do refrão, com tudo; depois a música segue dali
            secoes_refrao = [s for s in self.lista if s["parte"] == self.refrao] or self.lista
            sec = max(secoes_refrao, key=lambda s: sum(self.medidas[u["id"]]["forca"] for u in s["oitos"]) / len(s["oitos"]))
            for k in range(n):
                u = sec["oitos"][k % len(sec["oitos"])]
                self.linha.append(self.bloco(u, "Queda (tudo entra)"))
            self.continuar_depois(u)
            self.roteiro.append("Queda: o refrão entra com tudo.")
        elif modo in ("corpo", "picotado"):
            pic = modo == "picotado"
            trechos = self.pegar_em_ordem(n, 1 if pic else 2, 2 if pic else 4)
            for j, (parte, pedaco) in enumerate(trechos):
                for i, u in enumerate(pedaco):
                    b = self.bloco(u, ("Picotado · " if pic else "") + self.nome_parte(parte))
                    if i == len(pedaco) - 1 and self.sorteio.random() < (0.85 if pic else 0.4):
                        b["paradas"] = [[7, 0.5]]
                    self.linha.append(b)
            self.roteiro.append(f"{'Picotado' if pic else 'Música em ordem'}: {sum(len(p) for _, p in trechos)} oitos em "
                                f"{len(trechos)} trechos, cortando na batida.")
        elif modo == "refrao":
            for k in range(n):
                self.linha.append(self.bloco(self.proximo_refrao(), "Refrão"))
            self.roteiro.append(f"Refrão: {n} oito(s).")
        elif modo in ("respiro_sem_grave", "respiro_sem_bateria", "so_voz"):
            if self.linha and tv:  # eco jogado na voz, vazando para dentro do respiro
                ant = self.linha[-1]
                ant.setdefault("fx", {})["voz"] = {"eco": 0.55}
                ant["paradas"] = [[7, 0.5]]
            for k in range(n):
                trechos = self.pegar_em_ordem(1, 1, 1)
                u = trechos[0][1][0] if trechos else self.proximo_refrao()
                if modo == "respiro_sem_grave":
                    b = self.bloco(u, "Respiro sem grave", faixas={"voz": 1.0, "bateria": 1.0, "baixo": 0.0, "outros": 1.0})
                elif modo == "respiro_sem_bateria":
                    b = self.bloco(u, "Respiro sem bateria", faixas={"voz": 1.0, "bateria": 0.0, "baixo": 1.0, "outros": 1.0})
                else:
                    b = self.bloco(self.proximo_refrao(), "Só a voz", faixas={"voz": 1.0, "bateria": 0.0, "baixo": 0.0, "outros": 0.15 if tv else 1.0},
                                   fx={"tudo": {"reverb": 0.35}})
                self.linha.append(b)
            self.roteiro.append({"respiro_sem_grave": "Respiro sem grave", "respiro_sem_bateria": "Respiro sem bateria",
                                 "so_voz": "Só a voz"}[modo] + f": {n} oito(s)" + (", com eco jogado antes." if tv else "."))
        elif modo == "meio_tempo":
            for k in range(n):
                self.linha.append(self.bloco(self.proximo_refrao(), "Meio tempo", vel=0.5))
            self.roteiro.append(f"Meio tempo: {n} oito(s) em câmera lenta (cada um dura o dobro).")
        elif modo == "tempo_dobrado":
            for k in range(n):
                self.linha.append(self.bloco(self.proximo_refrao(), "Tempo dobrado", vel=2))
            self.roteiro.append(f"Tempo dobrado: {n} oito(s) acelerados (cada um dura a metade).")
        elif modo in ("estilo", "final_estilo"):
            ini = self.tempo_atual()
            blocos = []
            for parte, pedaco in self.pegar_em_ordem(n, 2, 4) or [(self.refrao, [self.proximo_refrao()])]:
                for u in pedaco:
                    blocos.append(self.bloco(u, f"Estilo: {estilo}", faixas={"voz": 1.0, "bateria": 0.25, "baixo": 1.0, "outros": 1.0}))
            if modo == "final_estilo" and blocos:
                blocos[-1]["paradas"] = [[7, 1.0]]
                blocos[-1]["fx"] = {"tudo": {"reverb": 0.4}}
                blocos[-1]["papel"] = f"Final: {estilo}"
            self.linha.extend(blocos)
            self.camada_estilo(estilo, ini, blocos)
            self.roteiro.append(f"{'Final' if modo == 'final_estilo' else 'Bloco'} em {estilo}: {len(blocos)} oito(s) da música "
                                f"com a bateria original trocada pela bateria de {estilo}.")
        elif modo == "final_voz":
            for k in range(n):
                u = self.fortes[min(1, len(self.fortes) - 1)] if k == 0 else self.proximo_refrao()
                faixas = {"voz": 1.0, "bateria": 0.0, "baixo": 0.0, "outros": 0.25} if tv else {"voz": 0.0, "bateria": 0.0, "baixo": 0.3, "outros": 1.0}
                b = self.bloco(u, "Final na voz" if tv else "Final suave", faixas=faixas, fx={"tudo": {"reverb": 0.55}})
                if k == n - 1:
                    b["env"] = [[0, 1], [0.5, 1], [0.75, 0.7], [1, 0]]
                self.linha.append(b)
            self.roteiro.append("Final: o refrão quase só na voz, com reverb e fade (pose final).")
        elif modo == "final_hit":
            for k in range(n):
                b = self.bloco(self.fortes[0] if k == n - 1 else self.proximo_refrao(), "Final seco (hit)")
                if k == n - 1:
                    b["paradas"] = [[7, 1.0]]
                    b["fx"] = {"tudo": {"reverb": 0.45}}
                self.linha.append(b)
            self.roteiro.append("Final: o refrão com tudo e um corte seco no tempo 8, deixando só a cauda do reverb.")
        elif modo == "final_fade":
            blocos = [self.bloco(self.proximo_refrao(), "Final com fade") for _ in range(n)]
            for k, b in enumerate(blocos):
                a, z = k / n, (k + 1) / n
                b["env"] = [[0, round(1 - a, 3)], [1, round(1 - z, 3)]]
            self.linha.extend(blocos)
            self.roteiro.append(f"Final: {n} oito(s) sumindo aos poucos.")
        else:
            self.roteiro.append(f"(modo desconhecido ignorado: {modo})")


def criar_mix(analise, alvo=165, semente=1, estrutura=None, meio_tempo=True):
    """Devolve (linha do tempo, camadas de estilo, roteiro em texto)."""
    if estrutura is None:
        estrutura = catalogo()["estruturas"][0]
    m = Montador(analise, semente)
    if not m.oitos:
        return [m.bloco(u, "Original") for u in m.unidades], [], ["A música é curta demais para montar um mix."]
    passos = [p for p in estrutura.get("passos", []) if meio_tempo or p["modo"] != "meio_tempo"]

    # quantos oitos cada passo "auto" recebe para chegar na duração desejada
    def dur_fixa(p):
        n = p.get("oitos", 1)
        if n == "auto":
            return 0
        fator = 2 if p["modo"] == "meio_tempo" else 0.5 if p["modo"] == "tempo_dobrado" else 1
        return int(n) * m.oito_dur * fator
    fixo = sum(dur_fixa(p) for p in passos)
    autos = [p for p in passos if p.get("oitos", 1) == "auto"]
    sobra = max(0.0, float(alvo) - fixo)
    # cada passo "auto" recebe uma parte proporcional ao seu peso (padrões aprendidos guardam o tamanho relativo)
    pesos = [float(p.get("peso", 1)) or 1 for p in autos]
    total_oitos = round(sobra / m.oito_dur)
    por_auto = [max(1, round(total_oitos * w / sum(pesos))) for w in pesos] if autos else []
    if autos:  # acerta o arredondamento no último
        por_auto[-1] = max(1, total_oitos - sum(por_auto[:-1]))

    k = 0
    for p in passos:
        if p.get("oitos", 1) == "auto":
            n = por_auto[k]; k += 1
        else:
            n = max(1, int(p.get("oitos", 1)))
        m.executar(p, n)

    # paradas extras no tempo 5 até chegar na densidade da estrutura
    meta = round(PARADAS_POR_MINUTO.get(estrutura.get("paradas", "normal"), 2.6) * m.tempo_atual() / 60)
    contar = lambda: sum(len(b.get("paradas") or []) for b in m.linha)
    candidatos = [b for b in m.linha[1:-1] if b["vel"] == 1 and not b.get("paradas")
                  and not b["papel"].startswith(("Respiro", "Só a voz", "Abertura", "Final"))]
    m.sorteio.shuffle(candidatos)
    for b in candidatos:
        if contar() >= meta:
            break
        b["paradas"] = [[7, 0.5]] if m.sorteio.random() < 0.7 else [[3, 0.5], [7, 0.5]]
    for b in m.linha:
        if not b.get("paradas"):
            b.pop("paradas", None)

    duracao = m.tempo_atual()
    m.roteiro.insert(0, f"Estrutura \"{estrutura.get('nome', 'personalizada')}\": mix de {int(duracao // 60)}:{int(duracao % 60):02d} "
                        f"(alvo {int(alvo // 60)}:{int(alvo % 60):02d}), {len(m.linha)} blocos, refrão = parte {m.refrao}, "
                        f"{contar()} paradas.")
    return m.linha, m.camadas, m.roteiro
