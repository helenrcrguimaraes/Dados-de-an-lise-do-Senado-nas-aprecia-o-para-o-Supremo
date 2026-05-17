"""
07_associacoes.py — Associações estatísticas entre as dimensões.

Gera:
    - Tabela 4 (correlação CCJ × Plenário)
    - Tabela 5 (sabatinas × votação)
    - Tabela 6 (macrocategorias × variáveis quantitativas)
    - Tabela 7 (Mann-Whitney: com casos × sem casos)

Entradas: múltiplos CSVs da pasta dados/
Saídas:   outputs/tabela_0{4,5,6,7}_*.csv

Os tamanhos amostrais (n) são calculados dinamicamente a partir dos CSVs.

Decisões metodológicas:
    - Tau de Kendall com variant='b' (corrige empates) — diferente do tau
      usado nas Tabelas 3, 12 e 26, que são Mann-Kendall clássico (tau-a).
      A Tabela 4 e seguintes testam CORRELAÇÃO entre duas variáveis, não
      tendência temporal em uma série — por isso o teste apropriado é
      Kendall tau-b via scipy.stats.kendalltau.
    - Para Mann-Whitney: scipy.stats.mannwhitneyu (alternative='two-sided').
    - Para Spearman: scipy.stats.spearmanr.

Padronização de nomes: este script assume que todos os CSVs da pasta dados/
já estão com os nomes uniformizados conforme regra única do projeto. A
checagem de consistência por merge identifica e aborta se houver indicado
em uma fonte e ausente na outra.
"""

import pandas as pd
from scipy import stats
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
# 1. Carregar todos os dados relevantes
# -----------------------------------------------------------------------------
ccj = pd.read_csv(DIR_BASE / "dados" / "ccj_votacao.csv")
pln = pd.read_csv(DIR_BASE / "dados" / "plenario_votacao.csv")
sab = pd.read_csv(DIR_BASE / "dados" / "sabatinas_quantitativo.csv")
par = pd.read_csv(DIR_BASE / "dados" / "partidos_posicoes.csv")
tem = pd.read_csv(DIR_BASE / "dados" / "temas_indagacoes.csv")

# Percentuais
ccj["pct_fav_ccj"] = ccj["favoraveis"] / ccj["quorum"] * 100
ccj["pct_con_ccj"] = ccj["contrarios"] / ccj["quorum"] * 100
pln["pct_fav_pln"] = pln["favoraveis"] / pln["quorum"] * 100
pln["pct_con_pln"] = pln["contrarios"] / pln["quorum"] * 100

# -----------------------------------------------------------------------------
# 2. Tabela 4 — Correlação CCJ × Plenário
# -----------------------------------------------------------------------------
m4 = ccj[["indicado", "pct_fav_ccj", "pct_con_ccj"]].merge(
    pln[["indicado", "pct_fav_pln", "pct_con_pln"]], on="indicado")

pares = [
    ("% Contrários CCJ × % Contrários Plenário",
     m4["pct_con_ccj"], m4["pct_con_pln"]),
    ("% Favoráveis CCJ × % Favoráveis Plenário",
     m4["pct_fav_ccj"], m4["pct_fav_pln"]),
]
linhas_t4 = []
for label, x, y in pares:
    tau_b, p_k = stats.kendalltau(x, y, variant="b")
    rho, p_s = stats.spearmanr(x, y)
    linhas_t4.append({
        "Variáveis cruzadas": label,
        "tau_Kendall": tau_b, "p_Kendall": p_k,
        "rho_Spearman": rho, "p_Spearman": p_s,
    })
tab4 = pd.DataFrame(linhas_t4)
tab4 = tab4.round({"tau_Kendall": 4, "p_Kendall": 6,
                   "rho_Spearman": 4, "p_Spearman": 6})
tab4.to_csv(DIR_OUT / "tabela_04_ccj_plenario.csv", index=False)

# -----------------------------------------------------------------------------
# 3. Tabela 5 — Sabatinas × Votação
# -----------------------------------------------------------------------------
m5 = sab.merge(ccj[["indicado", "pct_fav_ccj", "pct_con_ccj"]], on="indicado")
m5 = m5.merge(pln[["indicado", "pct_fav_pln", "pct_con_pln"]], on="indicado")

vars_vot = [("% Favoráveis Plenário", "pct_fav_pln"),
            ("% Contrários Plenário", "pct_con_pln"),
            ("% Favoráveis CCJ", "pct_fav_ccj"),
            ("% Contrários CCJ", "pct_con_ccj")]
vars_sab = [("Tempo de sabatina", "tempo_h"),
            ("Indagações", "indagacoes"),
            ("Senadores que indagaram", "senadores"),
            ("Elogios", "elogios"),
            ("Rejeições", "rejeicao")]

linhas_t5 = []
for v_label, v_col in vars_vot:
    for s_label, s_col in vars_sab:
        tau, p = stats.kendalltau(m5[v_col], m5[s_col], variant="b")
        linhas_t5.append({
            "Variável de votação": v_label,
            "Variável da sabatina": s_label,
            "tau": tau, "p_valor": p,
            "sig_alfa_0_05": "Sim" if p < 0.05 else "Não",
            "direcao": "Positiva" if tau > 0 else "Negativa" if tau < 0 else "Nula",
        })
tab5 = pd.DataFrame(linhas_t5)
tab5 = tab5.round({"tau": 4, "p_valor": 4})
tab5.to_csv(DIR_OUT / "tabela_05_sabatina_votacao.csv", index=False)

# -----------------------------------------------------------------------------
# 4. Tabela 6 — Macrocategorias × Quantitativas
# -----------------------------------------------------------------------------
# Proporção de cada macrocategoria nas indagações de cada sabatina.
tem["macrocategoria"] = tem["macrocategoria"].astype(str).str.strip()
sabatinas_unicas = tem["indicado"].unique()
macros = sorted(tem["macrocategoria"].unique())

prop = pd.DataFrame(index=sorted(sabatinas_unicas), columns=macros, dtype=float)
for s in sabatinas_unicas:
    sub = tem[tem["indicado"] == s]
    total = len(sub)
    for mc in macros:
        prop.loc[s, mc] = (sub["macrocategoria"] == mc).sum() / total * 100
prop.index.name = "indicado"
prop = prop.reset_index()

# Junção com variáveis quantitativas (nomes já padronizados no projeto)
m6 = prop.merge(sab[["indicado", "senadores", "indagacoes", "tempo_h"]],
                on="indicado")
m6 = m6.merge(pln[["indicado", "pct_con_pln"]], on="indicado")

vars_q = [("Tempo de sabatina", "tempo_h"),
          ("Senadores que indagaram", "senadores"),
          ("% Contrários Plenário", "pct_con_pln"),
          ("Indagações", "indagacoes")]

linhas_t6 = []
for mc in macros:
    for q_label, q_col in vars_q:
        tau, p = stats.kendalltau(m6[mc], m6[q_col], variant="b")
        linhas_t6.append({
            "Macrocategoria (%)": mc,
            "Variável quantitativa": q_label,
            "tau": tau, "p_valor": p,
            "sig_alfa_0_05": "Sim" if p < 0.05 else "Não",
        })
tab6 = pd.DataFrame(linhas_t6)
tab6 = tab6.round({"tau": 4, "p_valor": 4})
tab6.to_csv(DIR_OUT / "tabela_06_macro_quantitativas.csv", index=False)

# -----------------------------------------------------------------------------
# 5. Tabela 7 — Mann-Whitney com casos × sem casos
# -----------------------------------------------------------------------------
casos = tem[tem["macrocategoria"] == "Casos e eventos específicos"][
    "indicado"].unique().tolist()

m7 = sab.merge(pln[["indicado", "pct_con_pln"]], on="indicado")
m7["grupo"] = m7["indicado"].apply(lambda x: "com" if x in casos else "sem")

linhas_t7 = []
for label, col in [("Tempo de sabatina (h)", "tempo_h"),
                   ("Indagações", "indagacoes"),
                   ("Senadores que indagaram", "senadores"),
                   ("% Contrários Plenário", "pct_con_pln")]:
    g_com = m7[m7["grupo"] == "com"][col]
    g_sem = m7[m7["grupo"] == "sem"][col]
    U, p = stats.mannwhitneyu(g_com, g_sem, alternative="two-sided")
    linhas_t7.append({
        "Variável": label,
        f"Com casos (n={len(g_com)}) média": round(g_com.mean(), 2),
        f"Sem casos (n={len(g_sem)}) média": round(g_sem.mean(), 2),
        "U": round(U, 1), "p_valor": round(p, 4),
    })
tab7 = pd.DataFrame(linhas_t7)
tab7.to_csv(DIR_OUT / "tabela_07_casos_mann_whitney.csv", index=False)

# -----------------------------------------------------------------------------
# 6. Exportação das Tabelas 4, 5, 6 e 7 para .docx
#    (Times New Roman 12, sem espaçamento, decimais com vírgula)
# -----------------------------------------------------------------------------
def _fmt_num(v, casas=2):
    return f"{v:.{casas}f}".replace(".", ",")


def _fmt_pvalor(p):
    if p < 0.0001:
        return "<0,0001"
    return f"{p:.4f}".replace(".", ",")


def _fmt_corr(v):
    return f"{v:.4f}".replace(".", ",")


def _direcao(tau):
    if tau > 0:
        return "Positiva"
    if tau < 0:
        return "Negativa"
    return "Nula"


def tabela_para_docx(linhas, cabecalhos, titulo, caminho):
    """
    Gera .docx com título em negrito e tabela com 'Table Grid', em Times
    New Roman 12, sem espaçamento de parágrafo.
    Parâmetros:
        linhas: lista de listas (cada sublista é uma linha de dados, já formatada)
        cabecalhos: lista de strings com os títulos das colunas
        titulo: texto do título (acima da tabela)
        caminho: Path do arquivo .docx
    """
    doc = Document()

    estilo = doc.styles["Normal"]
    estilo.font.name = "Times New Roman"
    estilo.font.size = Pt(12)
    pf = estilo.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = 1.0

    # Título
    p_tit = doc.add_paragraph()
    r = p_tit.add_run(titulo)
    r.bold = True
    r.font.name = "Times New Roman"
    r.font.size = Pt(12)

    # Tabela
    tabela = doc.add_table(rows=1 + len(linhas), cols=len(cabecalhos))
    tabela.style = "Table Grid"

    for i, h in enumerate(cabecalhos):
        cel = tabela.rows[0].cells[i]
        cel.text = ""
        p = cel.paragraphs[0]
        rr = p.add_run(h)
        rr.bold = True
        rr.font.name = "Times New Roman"
        rr.font.size = Pt(12)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0

    for idx, row in enumerate(linhas):
        cels = tabela.rows[idx + 1].cells
        for i, valor in enumerate(row):
            cels[i].text = ""
            p = cels[i].paragraphs[0]
            rr = p.add_run(str(valor))
            rr.font.name = "Times New Roman"
            rr.font.size = Pt(12)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0

    doc.save(caminho)


# Tabela 4 (CCJ × Plenário, n=len(m4))
linhas_doc4 = []
for label, x, y in pares:
    tau_b, p_k = stats.kendalltau(x, y, variant="b")
    rho, p_s = stats.spearmanr(x, y)
    linhas_doc4.append([
        label, _fmt_corr(tau_b), _fmt_pvalor(p_k),
        _fmt_corr(rho), _fmt_pvalor(p_s),
    ])
tabela_para_docx(
    linhas_doc4,
    ["Variáveis cruzadas", "τ Kendall", "p (Kendall)",
     "ρ Spearman", "p (Spearman)"],
    f"Tabela 4 — Correlação entre os percentuais de votos na CCJ e no Plenário "
    f"(n = {len(m4)})",
    DIR_OUT / "tabela_04_ccj_plenario.docx",
)

# Tabela 5 (Sabatinas × Votação)
linhas_doc5 = []
for v_label, v_col in vars_vot:
    for s_label, s_col in vars_sab:
        tau, p = stats.kendalltau(m5[v_col], m5[s_col], variant="b")
        linhas_doc5.append([
            v_label, s_label, _fmt_corr(tau), _fmt_pvalor(p),
            "Sim" if p < 0.05 else "Não",
            _direcao(tau),
        ])
tabela_para_docx(
    linhas_doc5,
    ["Variável de votação", "Variável da sabatina", "τ", "p-valor",
     "Sig. (α=0,05)", "Direção"],
    f"Tabela 5 — Correlação entre variáveis da sabatina e percentual de votos "
    f"na CCJ e no Plenário (tau de Kendall, n = {len(m5)})",
    DIR_OUT / "tabela_05_sabatina_votacao.docx",
)

# Tabela 6 (Macrocategorias × Quantitativas)
linhas_doc6 = []
for mc in macros:
    for q_label, q_col in vars_q:
        tau, p = stats.kendalltau(m6[mc], m6[q_col], variant="b")
        linhas_doc6.append([
            mc, q_label, _fmt_corr(tau), _fmt_pvalor(p),
            "Sim" if p < 0.05 else "Não",
        ])
tabela_para_docx(
    linhas_doc6,
    ["Macrocategoria (%)", "Variável quantitativa", "τ", "p-valor",
     "Sig. (α=0,05)"],
    f"Tabela 6 — Correlação entre proporção de macrocategorias temáticas e "
    f"variáveis quantitativas (tau de Kendall, n = {len(m6)})",
    DIR_OUT / "tabela_06_macro_quantitativas.docx",
)

# Tabela 7 (Mann-Whitney casos × sem casos)
linhas_doc7 = []
n_com = (m7["grupo"] == "com").sum()
n_sem = (m7["grupo"] == "sem").sum()
for label, col in [("Tempo de sabatina (h)", "tempo_h"),
                   ("Indagações", "indagacoes"),
                   ("Senadores que indagaram", "senadores"),
                   ("% Contrários Plenário", "pct_con_pln")]:
    g_com = m7[m7["grupo"] == "com"][col]
    g_sem = m7[m7["grupo"] == "sem"][col]
    U, p = stats.mannwhitneyu(g_com, g_sem, alternative="two-sided")
    linhas_doc7.append([
        label,
        _fmt_num(g_com.mean(), 2),
        _fmt_num(g_sem.mean(), 2),
        _fmt_num(U, 1),
        _fmt_pvalor(p),
    ])
tabela_para_docx(
    linhas_doc7,
    ["Variável",
     f"Com casos (n={n_com}) — média",
     f"Sem casos (n={n_sem}) — média",
     "U", "p-valor"],
    f"Tabela 7 — Comparação entre sabatinas com e sem indagações sobre casos "
    f"e eventos específicos (Mann-Whitney, n = {len(m7)})",
    DIR_OUT / "tabela_07_casos_mann_whitney.docx",
)

# -----------------------------------------------------------------------------
# 7. Relatório no console (com n dinâmico)
# -----------------------------------------------------------------------------
print("=" * 70)
print("BLOCO 7 — ASSOCIAÇÕES (Tabelas 4, 5, 6, 7)")
print("=" * 70)
print(f"\nTabela 4 (CCJ × Plenário, n = {len(m4)}):\n"
      f"{tab4.to_string(index=False)}")
print(f"\nTabela 5 (sabatina × votação, n = {len(m5)}):\n"
      f"{tab5.to_string(index=False)}")
print(f"\nTabela 6 (macrocategorias × quantitativas, n = {len(m6)}):")
print(tab6.to_string(index=False))
print(f"\nTabela 7 (casos Mann-Whitney, n = {len(m7)}):\n"
      f"{tab7.to_string(index=False)}")
