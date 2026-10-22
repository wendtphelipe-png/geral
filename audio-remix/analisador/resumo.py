"""Junta as análises de vários mixes e tira os padrões: duração total, tamanho dos
trechos (em oitos), tipos de transição, BPMs e músicas identificadas.

Uso:  python resumo.py <pasta-das-analises> [--lista dados/audios/lista.json]
"""
import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np


def faixa(valores, casas=1):
    v = np.array(valores, dtype=float)
    if not len(v):
        return "-"
    q1, med, q3 = np.percentile(v, [25, 50, 75])
    return f"mediana {med:.{casas}f} (metade entre {q1:.{casas}f} e {q3:.{casas}f}; de {v.min():.{casas}f} a {v.max():.{casas}f})"


def mmss(s):
    return f"{int(s // 60)}:{int(s % 60):02d}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("pasta")
    p.add_argument("--lista", default=None)
    a = p.parse_args()
    pasta = Path(a.pasta)
    # Só os arquivos de análise de mix (ignora resumo.json, lista-videos.json etc.)
    analises = [d for d in (json.loads(f.read_text(encoding="utf-8")) for f in sorted(pasta.glob("*.json")))
                if isinstance(d, dict) and "trechos" in d]
    if not analises:
        print("Nenhuma análise encontrada.")
        return
    lista = {}
    if a.lista and Path(a.lista).exists():
        lista = {x["id"]: x for x in json.loads(Path(a.lista).read_text(encoding="utf-8"))}

    duracoes = [r["duracao"] for r in analises]
    trechos = [t for r in analises for t in r["trechos"]]
    transicoes = [x for r in analises for x in r["transicoes"]]
    etiquetas = Counter(e for x in transicoes for e in x["etiquetas"])
    musicas = Counter(f"{t['musica']['artista']} – {t['musica']['titulo']}" for t in trechos if t.get("musica"))
    saltos_bpm = [abs(x["bpm_depois"] - x["bpm_antes"]) for x in transicoes]

    md = ["# Resumo dos mixes analisados", "",
          f"Mixes: {len(analises)}", "",
          "## Duração total", f"- {faixa([d / 60 for d in duracoes], 2)} minutos", "",
          "## Trechos",
          f"- Trechos por mix: {faixa([len(r['trechos']) for r in analises], 0)}",
          f"- Duração de cada trecho: {faixa([t['duracao'] for t in trechos])} segundos",
          f"- Tamanho em oitos: {faixa([t['oitos'] for t in trechos])}",
          f"- BPM dos trechos: {faixa([t['bpm'] for t in trechos])}",
          f"- Trechos com voz: {sum(1 for t in trechos if t.get('tem_voz'))} de {sum(1 for t in trechos if 'tem_voz' in t)}",
          "", "## Transições",
          f"- Transições por minuto: {faixa([len(r['transicoes']) / (r['duracao'] / 60) for r in analises], 2)}",
          f"- Mudança de BPM numa transição: {faixa(saltos_bpm)}",
          f"- Paradas (stops) por minuto: {faixa([len(r.get('paradas', [])) / (r['duracao'] / 60) for r in analises], 1)}",
          f"- Duração das paradas: {faixa([x['duracao'] for r in analises for x in r.get('paradas', [])], 2)} segundos", ""]
    md += [f"- {e}: {n} ({100 * n / max(len(transicoes), 1):.0f}%)" for e, n in etiquetas.most_common()]
    md += ["", "## Músicas identificadas (vezes em que aparecem)", ""]
    md += [f"- {m}: {n}" for m, n in musicas.most_common()] or ["- nenhuma"]
    md += ["", "## Por mix", "", "| Mix | Duração | Trechos | Transições | BPM mediano |", "|---|---|---|---|---|"]
    for r in analises:
        md.append(f"| {r['arquivo']} | {mmss(r['duracao'])} | {len(r['trechos'])} | {len(r['transicoes'])} | {r['bpm_medio']} |")

    (pasta / "RESUMO.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (pasta / "resumo.json").write_text(json.dumps({
        "mixes": len(analises),
        "duracoes": duracoes,
        "duracao_trecho": [t["duracao"] for t in trechos],
        "oitos_trecho": [t["oitos"] for t in trechos],
        "etiquetas": dict(etiquetas),
        "musicas": dict(musicas),
        "videos": list(lista.values()),
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
