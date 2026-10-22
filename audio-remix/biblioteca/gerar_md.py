"""Gera BIBLIOTECA.md (leitura) a partir de estilos.json (fonte usada pelo app)."""
import json
from pathlib import Path

aqui = Path(__file__).parent
b = json.loads((aqui / "estilos.json").read_text(encoding="utf-8"))
md = ["# Biblioteca de estilos", "", "Gerado de `estilos.json` por `gerar_md.py`. Edite o JSON, não este arquivo.", "",
      b["observacao"], "", "| Estilo | BPM | Referências |", "|---|---|---|"]
md += [f"| [{e['nome']}](#{e['id']}) | {e['bpm'][0]}–{e['bpm'][1]} | {len(e['referencias'])} |" for e in b["estilos"]]
for e in b["estilos"]:
    md += ["", f'<a id="{e["id"]}"></a>', f"## {e['nome']}", "",
           f"- **BPM:** {e['bpm'][0]}–{e['bpm'][1]} (ideal {e['bpm_ideal']}), swing {e['swing']}",
           f"- **Groove:** {e['groove']}",
           f"- **Assinatura:** {e['assinatura']}",
           f"- **Instrumentos:** {', '.join(e['instrumentos'])}",
           f"- **Efeitos típicos:** {', '.join(e['efeitos'])}", "", "Padrão de bateria (16 passos = 1 compasso):", "", "```"]
    md += [f"{k:<9} {v}" for k, v in e["padrao"].items()]
    md += ["```"]
    if e.get("obs_padrao"):
        md += ["", e["obs_padrao"]]
    if e.get("obs"):
        md += ["", f"> {e['obs']}"]
    md += ["", "| Artista | Música | Ano | Tipo | Obs. |", "|---|---|---|---|---|"]
    md += [f"| {r['artista']} | {r['titulo']} | {r['ano'] or ''} | {r['tipo']} | {r.get('obs', '')} |" for r in e["referencias"]]
    if e.get("produtores_para_pesquisar"):
        md += ["", "Para pesquisar: " + "; ".join(e["produtores_para_pesquisar"])]
(aqui / "BIBLIOTECA.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print("ok", sum(len(e["referencias"]) for e in b["estilos"]), "referências")
