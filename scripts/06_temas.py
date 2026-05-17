"""
06_temas.py — Distribuição temática das indagações classificadas.

Gera:
    - Tabela 1 (frequência por macrocategoria)
    - Tabela 2 (frequência por categoria com presença em sabatinas)
    - Verificação de consistência: contagem por sabatina no banco de temas
      vs total declarado na Tabela 22 (sabatinas_quantitativo.csv).

Entrada: dados/temas_indagacoes.csv
         dados/sabatinas_quantitativo.csv  (para a verificação)
Saídas:  outputs/tabela_01_macrocategorias.csv
         outputs/tabela_02_categorias.csv
         outputs/verificacao_temas_vs_indagacoes.csv

Notas:
    - O n de indagações classificadas é calculado dinamicamente.
    - Os nomes dos indicados nos dois CSVs devem estar padronizados
      conforme regra única do projeto (ver Bloco 4 / README). O script
      faz checagem cruzada e aborta se houver indicado em uma fonte e
      ausente na outra.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import textwrap
from pathlib import Path
from docx import Document
from docx.shared import Pt


# -----------------------------------------------------------------------------
# 0. Caminhos e criação do diretório de saída
# -----------------------------------------------------------------------------
DIR_BASE = Path(__file__).parent.parent
DIR_OUT = DIR_BASE / "outputs"
DIR_OUT.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Leitura
# -----------------------------------------------------------------------------
df = pd.read_csv(DIR_BASE / "dados" / "temas_indagacoes.csv")

# Padronização mínima (apenas strip; não altera grafias)
df["macrocategoria"] = df["macrocategoria"].astype(str).str.strip()
df["categoria"] = df["categoria"].astype(str).str.strip()
df["indicado"] = df["indicado"].astype(str).str.strip()

n = len(df)

# -----------------------------------------------------------------------------
# 2. Tabela 1 — macrocategorias
# -----------------------------------------------------------------------------
vc_macro = df["macrocategoria"].value_counts().reset_index()
vc_macro.columns = ["Macrocategoria", "Frequência"]
vc_macro["%"] = (vc_macro["Frequência"] / n * 100).round(1)
vc_macro.to_csv(DIR_OUT / "tabela_01_macrocategorias.csv", index=False)

# -----------------------------------------------------------------------------
# 3. Tabela 2 — categorias com presença em sabatinas
# -----------------------------------------------------------------------------
cats = df["categoria"].value_counts().reset_index()
cats.columns = ["Categoria", "Frequência"]
cats["%"] = (cats["Frequência"] / n * 100).round(1)
cats["Presença em sabatinas"] = cats["Categoria"].apply(
    lambda c: df[df["categoria"] == c]["indicado"].nunique()
)
n_sabs = df["indicado"].nunique()
cats["Presença em sabatinas"] = (
    cats["Presença em sabatinas"].astype(str) + f"/{n_sabs}"
)
cats.insert(0, "Posição", range(1, len(cats) + 1))
cats.to_csv(DIR_OUT / "tabela_02_categorias.csv", index=False)

# -- Exportação da Tabela 2 para .docx (Times New Roman 11, sem espaçamento) ---
def exportar_tabela_02_docx(df_cats, n_total, caminho):
    doc = Document()

    # Estilo padrão: Times New Roman 11, sem espaçamento
    estilo = doc.styles["Normal"]
    estilo.font.name = "Times New Roman"
    estilo.font.size = Pt(11)
    pf = estilo.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0

    # Título da tabela
    titulo = doc.add_paragraph()
    n_fmt = f"{n_total:,}".replace(",", ".")
    run = titulo.add_run(
        f"Tabela 2 — Distribuição das indagações por categoria temática, "
        f"ordenadas por frequência (n = {n_fmt})"
    )
    run.bold = True
    run.font.name = "Times New Roman"
    run.font.size = Pt(11)

    # Tabela (cabeçalho + linhas)
    cabecalhos = ["Posição", "Categoria", "Frequência", "%",
                  "Presença em sabatinas"]
    tabela = doc.add_table(rows=1 + len(df_cats), cols=len(cabecalhos))
    tabela.style = "Table Grid"

    for i, h in enumerate(cabecalhos):
        celula = tabela.rows[0].cells[i]
        celula.text = ""
        p = celula.paragraphs[0]
        r = p.add_run(h)
        r.bold = True
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0

    for idx, linha in df_cats.iterrows():
        cels = tabela.rows[idx + 1].cells
        valores = [str(linha["Posição"]), str(linha["Categoria"]),
                   str(linha["Frequência"]), str(linha["%"]),
                   str(linha["Presença em sabatinas"])]
        for i, v in enumerate(valores):
            cels[i].text = ""
            p = cels[i].paragraphs[0]
            r = p.add_run(v)
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0

    doc.save(caminho)


exportar_tabela_02_docx(cats, n, DIR_OUT / "tabela_02_categorias.docx")

# -- Heatmap: distribuição percentual das macrocategorias por indicado --------
def gerar_heatmap_macrocategorias(df_temas, ordem_indicados, caminho_png):
    """
    Cada linha (indicado) soma ~100%: percentual de suas próprias indagações
    em cada macrocategoria. Cores em escala azul; células com 0 ficam em branco.
    """
    # Cross-tab e ordenação
    ct = pd.crosstab(df_temas["indicado"], df_temas["macrocategoria"])
    ordem_macros = (
        df_temas["macrocategoria"].value_counts().index.tolist()
    )
    ct = ct.reindex(index=ordem_indicados, columns=ordem_macros, fill_value=0)
    ct_pct = ct.div(ct.sum(axis=1), axis=0) * 100

    # Anotações: mostrar "X%" em células > 0, vazio em zeros
    annot = ct_pct.apply(
        lambda col: col.map(lambda v: f"{v:.0f}%" if v > 0 else "")
    )

    # Quebra os rótulos longos das colunas em 2-3 linhas
    rotulos_x = [textwrap.fill(c, width=22) for c in ct_pct.columns]

    fig, ax = plt.subplots(figsize=(14, 10))
    sns.heatmap(
        ct_pct, annot=annot, fmt="", cmap="Blues",
        vmin=0, vmax=ct_pct.values.max(),
        cbar_kws={"label": "Percentual das indagações", "shrink": 0.7},
        linewidths=0.5, linecolor="white",
        annot_kws={"size": 9, "color": "black"},
        ax=ax,
    )

    ax.set_xticklabels(rotulos_x, rotation=0, ha="center", fontsize=9)
    ax.set_yticklabels(ct_pct.index, rotation=0, fontsize=10)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.xaxis.tick_top()
    ax.xaxis.set_label_position("top")

    plt.tight_layout()
    plt.savefig(caminho_png, dpi=200, bbox_inches="tight")
    plt.close(fig)


# Carrega ordem cronológica dos indicados a partir de sabatinas_quantitativo.csv
ordem_cronologica = (
    pd.read_csv(DIR_BASE / "dados" / "sabatinas_quantitativo.csv")["indicado"]
    .tolist()
)
gerar_heatmap_macrocategorias(
    df, ordem_cronologica,
    DIR_OUT / "heatmap_macrocategorias_por_indicado.png",
)

# -----------------------------------------------------------------------------
# 4. Verificação: banco de temas vs Tabela 22 (sabatinas_quantitativo.csv)
# -----------------------------------------------------------------------------
sab = pd.read_csv(DIR_BASE / "dados" / "sabatinas_quantitativo.csv")
sab["indicado"] = sab["indicado"].astype(str).str.strip()

# Confere que os conjuntos de indicados estão alinhados (após padronização)
set_temas = set(df["indicado"].unique())
set_sab = set(sab["indicado"].unique())
so_em_temas = set_temas - set_sab
so_em_sab = set_sab - set_temas
if so_em_temas or so_em_sab:
    raise ValueError(
        "Inconsistência de nomes entre os dois CSVs:\n"
        f"  Só em temas:  {sorted(so_em_temas)}\n"
        f"  Só em sabs:   {sorted(so_em_sab)}\n"
        "Padronize os nomes antes de prosseguir."
    )

count_banco = df["indicado"].value_counts().rename("banco_classificado")
count_decl = sab.set_index("indicado")["indagacoes"].rename("tabela_22")
comp = pd.concat([count_decl, count_banco], axis=1).fillna(0).astype(int)
comp["diferenca"] = comp["banco_classificado"] - comp["tabela_22"]
comp = comp.sort_index()
comp.to_csv(DIR_OUT / "verificacao_temas_vs_indagacoes.csv")

div = comp[comp["diferenca"] != 0]

# -----------------------------------------------------------------------------
# 5. Relatório no console
# -----------------------------------------------------------------------------
print("=" * 70)
print("BLOCO 6 — TEMAS DAS INDAGAÇÕES")
print("=" * 70)
print(f"\nTotal de indagações classificadas: {n}")
print(f"Sabatinas únicas: {n_sabs}")
print(f"Macrocategorias: {df['macrocategoria'].nunique()}")
print(f"Categorias: {df['categoria'].nunique()}")

print(f"\nTabela 1 — Macrocategorias:\n{vc_macro.to_string(index=False)}")

print(f"\nTabela 2 — Categorias temáticas, ordenadas por frequência (n = {n}):")
print(cats.to_string(index=False))

total_t22 = int(comp["tabela_22"].sum())
total_banco = int(comp["banco_classificado"].sum())
print(f"\n--- Verificação: banco de temas vs Tabela 22 ---")
print(f"Total declarado (Tabela 22): {total_t22}")
print(f"Total classificado (banco):  {total_banco}")
print(f"Diferença global:            {total_banco - total_t22}")

if div.empty:
    print("\nNenhuma divergência por indicado.")
else:
    menores = div[div["diferenca"] < 0]
    maiores = div[div["diferenca"] > 0]
    if not menores.empty:
        print(f"\nSabatinas com banco MENOR que a Tabela 22 "
              f"(indagações não classificáveis):")
        print(menores.to_string())
    if not maiores.empty:
        print(f"\nSabatinas com banco MAIOR que a Tabela 22 (inverso — checar):")
        print(maiores.to_string())
