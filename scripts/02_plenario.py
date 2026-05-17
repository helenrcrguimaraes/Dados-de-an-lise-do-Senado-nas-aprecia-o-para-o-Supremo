"""
02_plenario.py — Análise da votação no Plenário do Senado Federal.

Gera:
    - Tabela 10 (percentuais por indicado)
    - Tabela 11 (estatística descritiva; n reportado dinamicamente)
    - Linhas da Tabela 3 referentes ao Plenário (Mann-Kendall, 4 variáveis)
    - Linhas da Tabela 12 referentes ao Plenário (Pettitt, condicional ao MK)

Entrada: dados/plenario_votacao.csv
Saídas:  outputs/tabela_10_plenario_percentuais.csv
         outputs/tabela_11_plenario_descritivas.csv
         outputs/tabela_03_plenario_mann_kendall.csv
         outputs/tabela_12_plenario_pettitt.csv

Quórum fixo: 81 senadores.
Pettitt aplicado apenas às variáveis com tendência significativa
(α = 0,05) no Mann-Kendall; seleção determinada em tempo de execução.
"""

import pandas as pd
import pymannkendall as mk
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from utilidades_00 import pettitt_test, describe  # noqa: E402


# -----------------------------------------------------------------------------
# 0. Caminhos e criação do diretório de saída
# -----------------------------------------------------------------------------
DIR_BASE = Path(__file__).parent.parent
DIR_OUT = DIR_BASE / "outputs"
DIR_OUT.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Leitura e validação
# -----------------------------------------------------------------------------
df = pd.read_csv(DIR_BASE / "dados" / "plenario_votacao.csv")

soma = (df["favoraveis"] + df["contrarios"]
        + df["abstencoes"] + df["ausencias"])
inconsistentes = df[soma != df["quorum"]]
if not inconsistentes.empty:
    raise ValueError(
        "Soma de absolutos ≠ quórum nas seguintes linhas:\n"
        f"{inconsistentes.to_string(index=False)}"
    )

# -----------------------------------------------------------------------------
# 2. Percentuais (quórum = 81)
# -----------------------------------------------------------------------------
df["pct_fav"] = df["favoraveis"] / df["quorum"] * 100
df["pct_con"] = df["contrarios"] / df["quorum"] * 100
df["pct_abs"] = df["abstencoes"] / df["quorum"] * 100
df["pct_aus"] = df["ausencias"] / df["quorum"] * 100

# -----------------------------------------------------------------------------
# 3. Tabela 10 — Percentuais por indicado
# -----------------------------------------------------------------------------
tab10 = df[["indicado", "pct_fav", "pct_con", "pct_abs", "pct_aus"]].copy()
tab10.columns = ["Indicado(a)", "Favoráveis (%)", "Contrários (%)",
                 "Abstenções (%)", "Ausências (%)"]
tab10 = tab10.round({"Favoráveis (%)": 2, "Contrários (%)": 2,
                     "Abstenções (%)": 2, "Ausências (%)": 2})
tab10.to_csv(DIR_OUT / "tabela_10_plenario_percentuais.csv", index=False)

# -----------------------------------------------------------------------------
# 4. Tabela 11 — Estatística descritiva
# -----------------------------------------------------------------------------
descritivas = {}
for nome, col in [("Favoráveis (%)", "pct_fav"),
                  ("Contrários (%)", "pct_con"),
                  ("Abstenções (%)", "pct_abs"),
                  ("Ausências (%)", "pct_aus")]:
    descritivas[nome] = describe(df[col])

tab11 = pd.DataFrame(descritivas).T
tab11.index.name = "Variável"
tab11 = tab11.round({"media": 2, "mediana": 2, "dp": 2, "min": 2, "max": 2})
tab11.to_csv(DIR_OUT / "tabela_11_plenario_descritivas.csv")

# -----------------------------------------------------------------------------
# 5. Tabela 3 — Mann-Kendall
# -----------------------------------------------------------------------------
variaveis = [("% Favoráveis", "pct_fav"),
             ("% Contrários", "pct_con"),
             ("% Abstenção", "pct_abs"),
             ("% Ausências", "pct_aus")]

resultados_mk = {}
linhas_mk = []
for nome, col in variaveis:
    r = mk.original_test(df[col].values)
    resultados_mk[col] = r
    linhas_mk.append({
        "Variável": nome, "n": len(df),
        "tau": r.Tau, "p_valor": r.p,
        "S": int(r.s), "Z": r.z,
        "sig_alfa_0_05": "Sim" if r.p < 0.05 else "Não",
        "tendencia": r.trend,
    })
tab3 = pd.DataFrame(linhas_mk)
tab3 = tab3.round({"tau": 4, "p_valor": 4, "Z": 4})
tab3.to_csv(DIR_OUT / "tabela_03_plenario_mann_kendall.csv", index=False)

# -----------------------------------------------------------------------------
# 6. Tabela 12 — Pettitt (condicional ao MK)
# -----------------------------------------------------------------------------
linhas_pettitt = []
for nome, col in variaveis:
    if resultados_mk[col].p >= 0.05:
        continue
    y = df[col].values
    res = pettitt_test(y)
    tau_idx = res["tau_idx"]
    antes = df["indicado"].iloc[tau_idx - 1]
    depois = df["indicado"].iloc[tau_idx]
    linhas_pettitt.append({
        "Variável": nome,
        "ponto_mudanca": f"{antes} → {depois}",
        "K": res["K"], "p_valor": res["p_value"],
        "media_antes": y[:tau_idx].mean(),
        "media_depois": y[tau_idx:].mean(),
    })

if linhas_pettitt:
    tab12 = pd.DataFrame(linhas_pettitt)
    tab12 = tab12.round({"p_valor": 4, "media_antes": 2, "media_depois": 2})
else:
    tab12 = pd.DataFrame(columns=["Variável", "ponto_mudanca", "K",
                                  "p_valor", "media_antes", "media_depois"])
tab12.to_csv(DIR_OUT / "tabela_12_plenario_pettitt.csv", index=False)

# -----------------------------------------------------------------------------
# 7. Relatório
# -----------------------------------------------------------------------------
print("=" * 70)
print("BLOCO 2 — PLENÁRIO DO SENADO FEDERAL")
print("=" * 70)
print(f"\nTabela 10 (percentuais) gerada — n = {len(df)}")
print(f"\nTabela 11 (descritivas):\n{tab11.to_string()}")
print(f"\nTabela 3 (Mann-Kendall):\n{tab3.to_string(index=False)}")
if not tab12.empty:
    print(f"\nTabela 12 (Pettitt):\n{tab12.to_string(index=False)}")
else:
    print("\nTabela 12 (Pettitt): nenhuma variável significativa no MK.")
print("\nArquivos salvos em outputs/")
