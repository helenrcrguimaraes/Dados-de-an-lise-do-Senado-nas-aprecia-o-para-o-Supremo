"""
03_tramitacao.py — Análise do tempo de tramitação das indicações.

Gera:
    - Tabela 13 (tempos por indicado, dados brutos)
    - Tabela 14 (descritivas, amostra completa)
    - Tabela 15 (descritivas, amostra sem indicados excluídos)
    - Linhas da Tabela 3 referentes à Tramitação (Mann-Kendall, completa e sem
      excluídos)
    - Resumo do critério de Tukey por variável
    - Lista completa de outliers identificados por Tukey
    - Quadro 6 (incidentes processuais) — apenas se o CSV de incidentes
      estiver disponível em dados/incidentes_procedimentais.csv

Entradas: dados/tramitacao_tempos.csv (obrigatório)
          dados/incidentes_procedimentais.csv (opcional)

Decisão metodológica — análise de sensibilidade:
    Apresenta-se a análise sobre a amostra completa (n total) e sobre uma
    subamostra que exclui os indicados listados em INDICADOS_EXCLUIDOS, para
    permitir avaliação do impacto de pontos atípicos sobre os resultados.

    A configuração padrão exclui André Mendonça, único caso atípico em ambas
    as variáveis de tramitação pelo critério de Tukey. Para alterar a regra
    de exclusão, basta editar a lista INDICADOS_EXCLUIDOS abaixo.

    O critério de Tukey é reportado integralmente, com Q1, Q3, IQR, limites
    inferior e superior, e a lista completa de outliers identificados por
    variável — independentemente de quais foram efetivamente excluídos.

Referência:
    TUKEY, J. W. Exploratory data analysis. Reading: Addison-Wesley, 1977.
"""

import pandas as pd
import numpy as np
import pymannkendall as mk
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from utilidades_00 import describe  # noqa: E402


# =============================================================================
# CONFIGURAÇÃO METODOLÓGICA
# =============================================================================
# Indicados a serem excluídos da subamostra para análise de sensibilidade.
# Justificativa documentada no docstring do módulo.
INDICADOS_EXCLUIDOS = ["André Mendonça"]


# -----------------------------------------------------------------------------
# 0. Caminhos e criação do diretório de saída
# -----------------------------------------------------------------------------
DIR_BASE = Path(__file__).parent.parent
DIR_OUT = DIR_BASE / "outputs"
DIR_OUT.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Leitura
# -----------------------------------------------------------------------------
df = pd.read_csv(DIR_BASE / "dados" / "tramitacao_tempos.csv")

# Verifica se os nomes em INDICADOS_EXCLUIDOS realmente existem na base
nomes_invalidos = [n for n in INDICADOS_EXCLUIDOS if n not in df["indicado"].values]
if nomes_invalidos:
    raise ValueError(
        "Os seguintes nomes em INDICADOS_EXCLUIDOS não constam na base: "
        f"{nomes_invalidos}"
    )

variaveis_tramitacao = [
    ("tempo_total", "Tempo total"),
    ("tempo_distribuicao", "Tempo até distribuição"),
]

# -----------------------------------------------------------------------------
# 2. Critério de Tukey — resumo por variável e lista completa de outliers
# -----------------------------------------------------------------------------
# Critério: outlier é qualquer observação fora de [Q1 − 1,5·IQR, Q3 + 1,5·IQR].
# Referência: Tukey (1977).
resumo_tukey = []
outliers_tukey = []
for col, label in variaveis_tramitacao:
    q1 = float(np.percentile(df[col], 25))
    q3 = float(np.percentile(df[col], 75))
    iqr = q3 - q1
    lim_inf = q1 - 1.5 * iqr
    lim_sup = q3 + 1.5 * iqr
    resumo_tukey.append({
        "Variável": label,
        "n": len(df),
        "Q1": q1, "Q3": q3, "IQR": iqr,
        "Limite inferior (Q1 − 1,5·IQR)": lim_inf,
        "Limite superior (Q3 + 1,5·IQR)": lim_sup,
    })
    mask = (df[col] > lim_sup) | (df[col] < lim_inf)
    for _, row in df[mask].iterrows():
        outliers_tukey.append({
            "Variável": label,
            "Indicado": row["indicado"],
            "Valor": row[col],
            "Tipo": "Superior" if row[col] > lim_sup else "Inferior",
        })

resumo_tukey_df = pd.DataFrame(resumo_tukey)
resumo_tukey_df = resumo_tukey_df.round({
    "Q1": 2, "Q3": 2, "IQR": 2,
    "Limite inferior (Q1 − 1,5·IQR)": 3,
    "Limite superior (Q3 + 1,5·IQR)": 3,
})
resumo_tukey_df.to_csv(DIR_OUT / "criterio_tukey_resumo.csv", index=False)

outliers_tukey_df = pd.DataFrame(outliers_tukey)
outliers_tukey_df.to_csv(DIR_OUT / "criterio_tukey_outliers.csv", index=False)

# -----------------------------------------------------------------------------
# 3. Amostras: completa e sem excluídos
# -----------------------------------------------------------------------------
df_sem_excluidos = (
    df[~df["indicado"].isin(INDICADOS_EXCLUIDOS)]
    .reset_index(drop=True)
)

# -----------------------------------------------------------------------------
# 4. Tabela 13 — dados brutos
# -----------------------------------------------------------------------------
df.to_csv(DIR_OUT / "tabela_13_tramitacao_tempos.csv", index=False)

# -----------------------------------------------------------------------------
# 5. Tabela 14 — descritivas (amostra completa)
# -----------------------------------------------------------------------------
desc_completa = {
    "Tempo total (dias)": describe(df["tempo_total"]),
    "Tempo até distribuição (dias)": describe(df["tempo_distribuicao"]),
}
tab14 = pd.DataFrame(desc_completa).T
tab14.index.name = "Variável"
tab14 = tab14.round({"media": 2, "mediana": 2, "dp": 2, "min": 2, "max": 2})
tab14.to_csv(DIR_OUT / "tabela_14_tramitacao_descritivas_completa.csv")

# -----------------------------------------------------------------------------
# 6. Tabela 15 — descritivas (amostra sem excluídos)
# -----------------------------------------------------------------------------
desc_sem = {
    "Tempo total (dias)": describe(df_sem_excluidos["tempo_total"]),
    "Tempo até distribuição (dias)": describe(df_sem_excluidos["tempo_distribuicao"]),
}
tab15 = pd.DataFrame(desc_sem).T
tab15.index.name = "Variável"
tab15 = tab15.round({"media": 2, "mediana": 2, "dp": 2, "min": 2, "max": 2})
tab15.to_csv(DIR_OUT / "tabela_15_tramitacao_descritivas_sem_excluidos.csv")

# -----------------------------------------------------------------------------
# 7. Tabela 3 — Mann-Kendall (duas amostras)
# -----------------------------------------------------------------------------
linhas_mk = []
for label_amostra, d in [
    (f"Completa (n={len(df)})", df),
    (f"Sem excluídos (n={len(df_sem_excluidos)})", df_sem_excluidos),
]:
    for col, nome in variaveis_tramitacao:
        r = mk.original_test(d[col].values)
        linhas_mk.append({
            "Variável": nome,
            "Amostra": label_amostra,
            "n": len(d),
            "tau": r.Tau,
            "p_valor": r.p,
            "S": int(r.s),
            "Z": r.z,
            "sig_alfa_0_05": "Sim" if r.p < 0.05 else "Não",
            "tendencia": r.trend,
        })
tab3 = pd.DataFrame(linhas_mk)
tab3 = tab3.round({"tau": 4, "p_valor": 4, "Z": 4})
tab3.to_csv(DIR_OUT / "tabela_03_tramitacao_mann_kendall.csv", index=False)

# -----------------------------------------------------------------------------
# 8. Quadro 6 — Incidentes processuais (condicional)
# -----------------------------------------------------------------------------
caminho_incidentes = DIR_BASE / "dados" / "incidentes_procedimentais.csv"
quadro6_processado = False
contagens = None
tudo_sim = None
if caminho_incidentes.exists():
    df_inc = pd.read_csv(caminho_incidentes)
    df_inc.to_csv(DIR_OUT / "quadro_06_incidentes.csv", index=False)

    # Indicações com os quatro incidentes simultâneos
    tudo_sim = df_inc[
        (df_inc["sem_pauta"] == "Sim") &
        (df_inc["adiada"] == "Sim") &
        (df_inc["vista"] == "Sim") &
        (df_inc["interstic"] == "Sim")
    ]

    # Contagens — total dinâmico
    total_inc = len(df_inc)
    contagens = pd.DataFrame({
        "Incidente": ["Sem pauta prévia", "Sabatina adiada/suspensa",
                      "Vista coletiva", "Dispensa do interstício"],
        "Sim": [(df_inc["sem_pauta"] == "Sim").sum(),
                (df_inc["adiada"] == "Sim").sum(),
                (df_inc["vista"] == "Sim").sum(),
                (df_inc["interstic"] == "Sim").sum()],
        "Não": [(df_inc["sem_pauta"] == "Não").sum(),
                (df_inc["adiada"] == "Não").sum(),
                (df_inc["vista"] == "Não").sum(),
                (df_inc["interstic"] == "Não").sum()],
    })
    contagens["Sem dado"] = total_inc - contagens["Sim"] - contagens["Não"]
    contagens.to_csv(DIR_OUT / "incidentes_contagens.csv", index=False)
    quadro6_processado = True

# -----------------------------------------------------------------------------
# 9. Relatório no console
# -----------------------------------------------------------------------------
print("=" * 70)
print("BLOCO 3 — TRAMITAÇÃO")
print("=" * 70)
print(f"\nAmostra completa: n = {len(df)}")
print(f"Indicados excluídos (configuração do script): {INDICADOS_EXCLUIDOS}")
print(f"Amostra sem excluídos: n = {len(df_sem_excluidos)}")

print(f"\nCritério de Tukey — resumo por variável:\n"
      f"{resumo_tukey_df.to_string(index=False)}")
print(f"\nOutliers identificados pelo critério de Tukey:\n"
      f"{outliers_tukey_df.to_string(index=False)}")

print(f"\nTabela 14 — descritivas, amostra completa (n={len(df)}):\n"
      f"{tab14.to_string()}")
print(f"\nTabela 15 — descritivas, sem excluídos (n={len(df_sem_excluidos)}):\n"
      f"{tab15.to_string()}")
print(f"\nTabela 3 — Mann-Kendall:\n{tab3.to_string(index=False)}")

if quadro6_processado:
    print(f"\nIncidentes processuais (contagens, n={len(df_inc)}):\n"
          f"{contagens.to_string(index=False)}")
    print(f"\nIndicações com os 4 incidentes simultâneos: "
          f"{tudo_sim['indicado'].tolist()}")
else:
    print(f"\nAviso: {caminho_incidentes.name} não encontrado em dados/.")
    print("Quadro 6 e contagens de incidentes não foram processados.")

print("\nArquivos salvos em outputs/")
