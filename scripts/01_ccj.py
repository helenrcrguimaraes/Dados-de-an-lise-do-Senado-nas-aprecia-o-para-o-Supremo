"""
01_ccj.py — Análise da votação na CCJ (Comissão de Constituição, Justiça
e Cidadania) do Senado Federal.

Gera:
    - Tabela 8 (percentuais por indicado)
    - Tabela 9 (estatística descritiva; n reportado dinamicamente)
    - Linhas da Tabela 3 referentes à CCJ (Mann-Kendall, 4 variáveis)
    - Linhas da Tabela 12 referentes à CCJ (Pettitt, condicional ao MK)

Entrada: dados/ccj_votacao.csv  (absolutos por indicado)
Saídas:  outputs/tabela_08_ccj_percentuais.csv
         outputs/tabela_09_ccj_descritivas.csv
         outputs/tabela_03_ccj_mann_kendall.csv
         outputs/tabela_12_ccj_pettitt.csv

Decisões metodológicas:
    - Mann-Kendall clássico (pymannkendall.original_test), com referência a
      Mann (1945). A coluna reportada é τ (= tau-a de Kendall, não corrige
      empates) e NÃO τ-b.
    - DP amostral (ddof = 1).
    - Série em ordem cronológica (ordem em que aparece na planilha de entrada
      coincide com ano da indicação).
    - Pettitt aplicado apenas às variáveis com tendência significativa no
      Mann-Kendall (α = 0,05); seleção determinada em tempo de execução.
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
# 1. Leitura dos dados
# -----------------------------------------------------------------------------
df = pd.read_csv(DIR_BASE / "dados" / "ccj_votacao.csv")

# Validação de integridade: soma dos absolutos deve bater com o quórum.
# Usamos raise (não assert), porque assert é removido com python -O.
soma = (df["favoraveis"] + df["contrarios"]
        + df["abstencoes"] + df["ausencias"])
inconsistentes = df[soma != df["quorum"]]
if not inconsistentes.empty:
    raise ValueError(
        "Soma de absolutos ≠ quórum nas seguintes linhas:\n"
        f"{inconsistentes.to_string(index=False)}"
    )

# -----------------------------------------------------------------------------
# 2. Cálculo dos percentuais (sobre o quórum)
# -----------------------------------------------------------------------------
# Quórum varia: 23 até Teori Zavascki; 27 daí em diante (RSF 11/2013).
df["pct_fav"] = df["favoraveis"] / df["quorum"] * 100
df["pct_con"] = df["contrarios"] / df["quorum"] * 100
df["pct_abs"] = df["abstencoes"] / df["quorum"] * 100
df["pct_aus"] = df["ausencias"] / df["quorum"] * 100

# -----------------------------------------------------------------------------
# 3. Tabela 8 — Percentuais por indicado (2 casas decimais)
# -----------------------------------------------------------------------------
tab8 = df[["indicado", "pct_fav", "pct_con", "pct_abs", "pct_aus"]].copy()
tab8.columns = ["Indicado(a)", "Favoráveis (%)", "Contrários (%)",
                "Abstenções (%)", "Ausências (%)"]
tab8 = tab8.round({"Favoráveis (%)": 2, "Contrários (%)": 2,
                   "Abstenções (%)": 2, "Ausências (%)": 2})
tab8.to_csv(DIR_OUT / "tabela_08_ccj_percentuais.csv", index=False)

# -----------------------------------------------------------------------------
# 4. Tabela 9 — Estatística descritiva (n dinâmico)
# -----------------------------------------------------------------------------
descritivas = {}
for nome, col in [("Favoráveis (%)", "pct_fav"),
                  ("Contrários (%)", "pct_con"),
                  ("Abstenções (%)", "pct_abs"),
                  ("Ausências (%)", "pct_aus")]:
    descritivas[nome] = describe(df[col])

tab9 = pd.DataFrame(descritivas).T
tab9.index.name = "Variável"
tab9 = tab9.round({"media": 2, "mediana": 2, "dp": 2, "min": 2, "max": 2})
tab9.to_csv(DIR_OUT / "tabela_09_ccj_descritivas.csv")

# -----------------------------------------------------------------------------
# 5. Tabela 3 — Mann-Kendall (linhas da CCJ)
# -----------------------------------------------------------------------------
# Teste de Mann (1945) para tendência monotônica em série temporal.
# Implementação: pymannkendall.original_test
#   S = soma dos sinais de (y_j - y_i) para todos os pares i < j
#   Var(S) = [n(n-1)(2n+5)] / 18   (com correção para empates)
#   Z = (S-1)/sqrt(Var(S)) se S>0; (S+1)/sqrt(Var(S)) se S<0; 0 se S=0
#   tau = S / [n(n-1)/2]
#   p-valor bicaudal: p = 2 * (1 - Phi(|Z|))
variaveis = [("% Favoráveis", "pct_fav"),
             ("% Contrários", "pct_con"),
             ("% Abstenção", "pct_abs"),
             ("% Ausências", "pct_aus")]

resultados_mk = {}  # guardamos para reutilizar na seleção do Pettitt
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
tab3.to_csv(DIR_OUT / "tabela_03_ccj_mann_kendall.csv", index=False)

# -----------------------------------------------------------------------------
# 6. Tabela 12 — Pettitt (linhas da CCJ)
# -----------------------------------------------------------------------------
# Aplicado APENAS às variáveis com tendência significativa (α = 0,05) no
# Mann-Kendall. Seleção determinada em tempo de execução (não hardcoded).
linhas_pettitt = []
for nome, col in variaveis:
    if resultados_mk[col].p >= 0.05:
        continue
    y = df[col].values
    res = pettitt_test(y)
    tau_idx = res["tau_idx"]
    antes = df["indicado"].iloc[tau_idx - 1]
    depois = df["indicado"].iloc[tau_idx]
    m_antes = y[:tau_idx].mean()
    m_depois = y[tau_idx:].mean()
    linhas_pettitt.append({
        "Variável": nome,
        "ponto_mudanca": f"{antes} → {depois}",
        "K": res["K"], "p_valor": res["p_value"],
        "media_antes": m_antes,
        "media_depois": m_depois,
    })

if linhas_pettitt:
    tab12 = pd.DataFrame(linhas_pettitt)
    tab12 = tab12.round({"p_valor": 4, "media_antes": 2, "media_depois": 2})
else:
    tab12 = pd.DataFrame(columns=["Variável", "ponto_mudanca", "K",
                                  "p_valor", "media_antes", "media_depois"])
tab12.to_csv(DIR_OUT / "tabela_12_ccj_pettitt.csv", index=False)

# -----------------------------------------------------------------------------
# 7. Relatório no console
# -----------------------------------------------------------------------------
print("=" * 70)
print("BLOCO 1 — CCJ (Comissão de Constituição, Justiça e Cidadania)")
print("=" * 70)
print(f"\nTabela 8 (percentuais) gerada — n = {len(df)}")
print(f"\nTabela 9 (descritivas):\n{tab9.to_string()}")
print(f"\nTabela 3 (Mann-Kendall):\n{tab3.to_string(index=False)}")
if not tab12.empty:
    print(f"\nTabela 12 (Pettitt):\n{tab12.to_string(index=False)}")
else:
    print("\nTabela 12 (Pettitt): nenhuma variável significativa no MK.")
print("\nArquivos salvos em outputs/")
