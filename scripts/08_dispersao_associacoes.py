"""
08_dispersao_associacoes.py — Testa associações entre o índice de dispersão
partidária e as variáveis de votação, tramitação e sabatinas. Corresponde
aos três parágrafos de análise da seção 3.7 da tese que começam com
"Os votos favoráveis ou contrários...", "O tempo de tramitação..." e
"As variáveis das sabatinas...".

Entradas: múltiplos CSVs de dados/
Saída:    outputs/dispersao_associacoes.csv

Testes:
    - Tau de Kendall (scipy.stats.kendalltau, variant='b') para correlação
      entre o índice e cada variável.
    - Mann-Whitney U (scipy.stats.mannwhitneyu, alternative='two-sided')
      comparando grupo de baixa dispersão (1 ou 2 partidos distintos) com
      grupo de alta dispersão (3 ou 4 partidos distintos).

Os n são calculados dinamicamente a partir dos merges.
"""

import pandas as pd
from scipy import stats
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from utilidades_00 import indice_dispersao_partidaria  # noqa: E402


# =============================================================================
# CONFIGURAÇÃO METODOLÓGICA
# =============================================================================
# Indicados excluídos na análise de tramitação (análise de sensibilidade
# para outlier). Mantém compatibilidade com o critério adotado no script
# 03_tramitacao.py.
INDICADOS_EXCLUIDOS_TRAMITACAO = ["André Mendonça"]


# -----------------------------------------------------------------------------
# 0. Caminhos e criação do diretório de saída
# -----------------------------------------------------------------------------
DIR_BASE = Path(__file__).parent.parent
DIR_OUT = DIR_BASE / "outputs"
DIR_OUT.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Carregar dados
# -----------------------------------------------------------------------------
par = pd.read_csv(DIR_BASE / "dados" / "partidos_posicoes.csv")
ccj = pd.read_csv(DIR_BASE / "dados" / "ccj_votacao.csv")
pln = pd.read_csv(DIR_BASE / "dados" / "plenario_votacao.csv")
tram = pd.read_csv(DIR_BASE / "dados" / "tramitacao_tempos.csv")
sab = pd.read_csv(DIR_BASE / "dados" / "sabatinas_quantitativo.csv")

# -----------------------------------------------------------------------------
# 2. Índice de dispersão partidária e percentuais
# -----------------------------------------------------------------------------
par["disp"] = par.apply(indice_dispersao_partidaria, axis=1)

ccj["pct_fav_ccj"] = ccj["favoraveis"] / ccj["quorum"] * 100
ccj["pct_con_ccj"] = ccj["contrarios"] / ccj["quorum"] * 100
pln["pct_fav_pln"] = pln["favoraveis"] / pln["quorum"] * 100
pln["pct_con_pln"] = pln["contrarios"] / pln["quorum"] * 100

# -----------------------------------------------------------------------------
# 3. Merges (todos por "indicado", que está padronizado no projeto)
# -----------------------------------------------------------------------------
disp_ccj = par[["indicado", "disp"]].merge(ccj, on="indicado")
disp_pln = par[["indicado", "disp"]].merge(pln, on="indicado")
disp_tram = par[["indicado", "disp"]].merge(tram, on="indicado")
disp_tram_sem = (
    disp_tram[~disp_tram["indicado"].isin(INDICADOS_EXCLUIDOS_TRAMITACAO)]
    .reset_index(drop=True)
)
disp_sab = par[["indicado", "disp"]].merge(sab, on="indicado")

# -----------------------------------------------------------------------------
# 4. Função genérica: Kendall + Mann-Whitney por dicotomização da dispersão
# -----------------------------------------------------------------------------
def testa(df_, col):
    tau, p_k = stats.kendalltau(df_["disp"], df_[col], variant="b")
    g_baixa = df_[df_["disp"] <= 2][col]
    g_alta = df_[df_["disp"] >= 3][col]
    U, p_mw = stats.mannwhitneyu(g_baixa, g_alta, alternative="two-sided")
    return {
        "n": len(df_),
        "tau": round(tau, 4), "p_Kendall": round(p_k, 4),
        "baixa_media": round(g_baixa.mean(), 2), "n_baixa": len(g_baixa),
        "alta_media": round(g_alta.mean(), 2), "n_alta": len(g_alta),
        "U": round(U, 1), "p_MannWhitney": round(p_mw, 4),
    }

# -----------------------------------------------------------------------------
# 5. Aplica a todas as variáveis (labels descritivos, sem n hardcoded)
# -----------------------------------------------------------------------------
linhas = []
for label, d, col in [
    ("% Favoráveis CCJ", disp_ccj, "pct_fav_ccj"),
    ("% Contrários CCJ", disp_ccj, "pct_con_ccj"),
    ("% Favoráveis Plenário", disp_pln, "pct_fav_pln"),
    ("% Contrários Plenário", disp_pln, "pct_con_pln"),
    ("Tempo total (amostra completa)", disp_tram, "tempo_total"),
    ("Tempo até distribuição (amostra completa)",
     disp_tram, "tempo_distribuicao"),
    ("Tempo total (sem excluídos)", disp_tram_sem, "tempo_total"),
    ("Tempo até distribuição (sem excluídos)",
     disp_tram_sem, "tempo_distribuicao"),
    ("Senadores que indagaram", disp_sab, "senadores"),
    ("Indagações", disp_sab, "indagacoes"),
    ("Tempo de sabatina", disp_sab, "tempo_h"),
    ("Elogios", disp_sab, "elogios"),
    ("Rejeição", disp_sab, "rejeicao"),
]:
    r = testa(d, col)
    r["Variável"] = label
    linhas.append(r)

tab_disp = pd.DataFrame(linhas)
colunas = ["Variável", "n", "tau", "p_Kendall", "baixa_media", "n_baixa",
           "alta_media", "n_alta", "U", "p_MannWhitney"]
tab_disp = tab_disp[colunas]
tab_disp.to_csv(DIR_OUT / "dispersao_associacoes.csv", index=False)

# -----------------------------------------------------------------------------
# 6. Relatório no console
# -----------------------------------------------------------------------------
print("=" * 70)
print("BLOCO 8 — ASSOCIAÇÕES COM DISPERSÃO PARTIDÁRIA")
print("=" * 70)
print(f"\nExclusão para tramitação: {INDICADOS_EXCLUIDOS_TRAMITACAO}")
print(f"\n{tab_disp.to_string(index=False)}")
