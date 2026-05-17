"""
05_sabatinas_quantitativo.py — Análise quantitativa das sabatinas.

Gera:
    - Tabela 20 (senadores que indagaram por sabatina)
    - Tabela 21 (descritiva de senadores que indagaram)
    - Tabela 22 (total de indagações por sabatina)
    - Tabela 23 (manifestações sem indagação: elogios, rejeição, outras)
    - Tabela 24 (tempo de sabatina por indicado)
    - Tabela 25 (descritiva do tempo de sabatina)
    - Linhas da Tabela 3 referentes às sabatinas (Mann-Kendall, 5 variáveis)
    - Tabela 26 (Pettitt, condicional ao MK)

Entrada: dados/sabatinas_quantitativo.csv
Saídas:  outputs/tabela_20_a_26_*.csv

Observação sobre o universo (n):
    A série de sabatinas começa em Ellen Gracie (2000), primeira sabatina
    pública para o STF, e vai até a indicação mais recente. Ricardo
    Lewandowski (2006) está ausente: limitação efetiva da pesquisa
    documentada no texto da tese (dados não disponibilizados na origem).
    O n é calculado dinamicamente.

Observação sobre a categoria "Outras":
    Manifestações sem indagação e sem caráter de elogio ou rejeição (ex.:
    registro de presença, declaração de preenchimento de requisitos
    constitucionais sem qualificação avaliativa).

Decisão metodológica — Pettitt:
    Aplicado apenas às variáveis com tendência significativa (α = 0,05) no
    Mann-Kendall; seleção determinada em tempo de execução.
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
# 1. Leitura
# -----------------------------------------------------------------------------
df = pd.read_csv(DIR_BASE / "dados" / "sabatinas_quantitativo.csv")

# -----------------------------------------------------------------------------
# 2. Tabela 20 — senadores que indagaram
# -----------------------------------------------------------------------------
tab20 = df[["indicado", "senadores"]].copy()
tab20.columns = ["Indicado(a)", "Senadores que indagaram"]
tab20.to_csv(DIR_OUT / "tabela_20_senadores.csv", index=False)

# -----------------------------------------------------------------------------
# 3. Tabela 21 — descritiva de senadores
# -----------------------------------------------------------------------------
tab21 = pd.DataFrame([describe(df["senadores"])],
                     index=["Senadores que indagaram"])
tab21.index.name = "Variável"
tab21 = tab21.round({"media": 2, "mediana": 2, "dp": 2, "min": 2, "max": 2})
tab21.to_csv(DIR_OUT / "tabela_21_senadores_descritiva.csv")

# -----------------------------------------------------------------------------
# 4. Tabela 22 — total de indagações
# -----------------------------------------------------------------------------
tab22 = df[["indicado", "indagacoes"]].copy()
tab22.columns = ["Indicado(a)", "Total de indagações"]
tab22.to_csv(DIR_OUT / "tabela_22_indagacoes.csv", index=False)

# -----------------------------------------------------------------------------
# 5. Tabela 23 — manifestações sem indagação
# -----------------------------------------------------------------------------
tab23 = df[["indicado", "elogios", "rejeicao", "outras"]].copy()
tab23["total"] = tab23["elogios"] + tab23["rejeicao"] + tab23["outras"]
tab23.columns = ["Indicado(a)", "Elogios", "Rejeição", "Outras", "Total"]
tab23.to_csv(DIR_OUT / "tabela_23_manifestacoes.csv", index=False)

# -----------------------------------------------------------------------------
# 6. Tabela 24 — tempo de sabatina
# -----------------------------------------------------------------------------
tab24 = df[["indicado", "tempo_h"]].copy()
tab24.columns = ["Indicado(a)", "Tempo de sabatina (h)"]
tab24.to_csv(DIR_OUT / "tabela_24_tempo.csv", index=False)

# -----------------------------------------------------------------------------
# 7. Tabela 25 — descritiva do tempo
# -----------------------------------------------------------------------------
tab25 = pd.DataFrame([describe(df["tempo_h"])],
                     index=["Tempo de sabatina (h)"])
tab25.index.name = "Variável"
tab25 = tab25.round({"media": 2, "mediana": 2, "dp": 2, "min": 2, "max": 2})
tab25.to_csv(DIR_OUT / "tabela_25_tempo_descritiva.csv")

# -----------------------------------------------------------------------------
# 8. Tabela 3 — Mann-Kendall (5 variáveis)
# -----------------------------------------------------------------------------
variaveis = [
    ("Senadores que indagaram", "senadores"),
    ("Total de indagações", "indagacoes"),
    ("Tempo de sabatina", "tempo_h"),
    ("Elogios", "elogios"),
    ("Rejeição", "rejeicao"),
]

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
tab3.to_csv(DIR_OUT / "tabela_03_sabatinas_mann_kendall.csv", index=False)

# -----------------------------------------------------------------------------
# 9. Tabela 26 — Pettitt (condicional ao MK)
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
    tab26 = pd.DataFrame(linhas_pettitt)
    tab26 = tab26.round({"p_valor": 4, "media_antes": 2, "media_depois": 2})
else:
    tab26 = pd.DataFrame(columns=["Variável", "ponto_mudanca", "K",
                                  "p_valor", "media_antes", "media_depois"])
tab26.to_csv(DIR_OUT / "tabela_26_sabatinas_pettitt.csv", index=False)

# -----------------------------------------------------------------------------
# 10. Relatório no console
# -----------------------------------------------------------------------------
print("=" * 70)
print("BLOCO 5 — SABATINAS (QUANTITATIVO)")
print("=" * 70)
print(f"\nn = {len(df)}")
print(f"\nTabela 21 (senadores):\n{tab21.to_string()}")
print(f"\nTabela 25 (tempo):\n{tab25.to_string()}")
print(f"\nTabela 3 (Mann-Kendall):\n{tab3.to_string(index=False)}")
if not tab26.empty:
    print(f"\nTabela 26 (Pettitt):\n{tab26.to_string(index=False)}")
else:
    print("\nTabela 26 (Pettitt): nenhuma variável significativa no MK.")

# Síntese dinâmica para o texto da seção 3.5.1
total_indagacoes = df["indagacoes"].sum()
total_elogios = df["elogios"].sum()
total_rejeicao = df["rejeicao"].sum()
total_outras = df["outras"].sum()
total_manifestacoes = total_elogios + total_rejeicao + total_outras
print(f"\n--- Síntese para a seção 3.5.1 ---")
print(f"Total de indagações: {total_indagacoes}")
print(f"Total de elogios: {total_elogios}")
print(f"Total de rejeição: {total_rejeicao}")
print(f"Total de outras: {total_outras}")
print(f"Total de manifestações sem indagação: {total_manifestacoes}")
