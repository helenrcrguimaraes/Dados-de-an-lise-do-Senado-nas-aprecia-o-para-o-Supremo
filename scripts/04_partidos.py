"""
04_partidos.py — Análise da dimensão partidária e construção do índice
de dispersão partidária usado em 07_associacoes_dispersao.py.

Gera:
    - Tabelas 16 a 19 (frequências por pessoa em cada posição-chave)
    - Quadro 7 (partidos por indicação)
    - Arquivo com índice de dispersão (usado em outros scripts)

Entrada: dados/partidos_posicoes.csv
Saídas:  outputs/tabela_16_presidente_republica.csv
         outputs/tabela_17_presidente_senado.csv
         outputs/tabela_18_presidente_ccj.csv
         outputs/tabela_19_relatores.csv
         outputs/quadro_07_partidos.csv
         outputs/indice_dispersao.csv

Notas sobre o dado de entrada:
    - A filiação de Itamar Franco à época da indicação de Maurício Corrêa
      é registrada como "Sem Partido" (deixou o PRN em 1992, antes da
      indicação em 1994).
    - PMDB e MDB aparecem unificados como "PMDB" no banco.
    - PFL, DEM e União Brasil são mantidos como rótulos distintos, refletindo
      a denominação do partido na época de cada indicação.
    - Na indicação de Nunes Marques, Rodrigo Pacheco atuou como relator
      ad hoc (Eduardo Braga foi designado inicialmente). O dado registra
      apenas o relator efetivo (Rodrigo Pacheco, DEM).
"""

import pandas as pd
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent))
from utilidades_00 import indice_dispersao_partidaria  # noqa: E402


# -----------------------------------------------------------------------------
# 0. Caminhos e criação do diretório de saída
# -----------------------------------------------------------------------------
DIR_BASE = Path(__file__).parent.parent
DIR_OUT = DIR_BASE / "outputs"
DIR_OUT.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# 1. Leitura
# -----------------------------------------------------------------------------
df = pd.read_csv(DIR_BASE / "dados" / "partidos_posicoes.csv")

# -----------------------------------------------------------------------------
# 2. Quadro 7 — apresentação dos partidos por indicação
# -----------------------------------------------------------------------------
quadro7 = df[["indicado", "pres_brasil_partido", "pres_senado_partido",
              "pres_ccj_partido", "relator_partido"]].copy()
quadro7.columns = ["Indicado(a)", "Pres. da República", "Pres. do Senado",
                   "Pres. da CCJ", "Relator"]
quadro7.to_csv(DIR_OUT / "quadro_07_partidos.csv", index=False)

# -----------------------------------------------------------------------------
# 3. Tabelas 16 a 19 — frequências por pessoa
# -----------------------------------------------------------------------------
def freq(col, arquivo, titulo):
    n = len(df)
    vc = df[col].value_counts().reset_index()
    vc.columns = [titulo, "Indicações"]
    vc["%"] = (vc["Indicações"] / n * 100).round(1)
    vc.to_csv(DIR_OUT / arquivo, index=False)
    return vc

t16 = freq("pres_brasil_pessoa", "tabela_16_presidente_republica.csv",
           "Presidente da República")
t17 = freq("pres_senado_pessoa", "tabela_17_presidente_senado.csv",
           "Presidente do Senado")
t18 = freq("pres_ccj_pessoa", "tabela_18_presidente_ccj.csv",
           "Presidente da CCJ")
t19 = freq("relator_pessoa", "tabela_19_relatores.csv", "Relator")

# -----------------------------------------------------------------------------
# 4. Índice de dispersão partidária
# -----------------------------------------------------------------------------
df["disp"] = df.apply(indice_dispersao_partidaria, axis=1)
df[["indicado", "disp"]].to_csv(DIR_OUT / "indice_dispersao.csv", index=False)

# Distribuição do índice
dist_disp = df["disp"].value_counts().sort_index().reset_index()
dist_disp.columns = ["Dispersão (nº de partidos distintos)", "Indicações"]

# -----------------------------------------------------------------------------
# 5. Relatório no console — valores calculados sobre a base atual
# -----------------------------------------------------------------------------
print("=" * 70)
print("BLOCO 4 — PARTIDOS POLÍTICOS")
print("=" * 70)
print(f"\nn = {len(df)}")
print(f"\nTabela 16 — Presidentes da República:\n{t16.to_string(index=False)}")
print(f"\nTabela 17 — Presidentes do Senado:\n{t17.to_string(index=False)}")
print(f"\nTabela 18 — Presidentes da CCJ:\n{t18.to_string(index=False)}")
print(f"\nTabela 19 — Relatores:\n{t19.to_string(index=False)}")
print(f"\nDistribuição do índice de dispersão:\n{dist_disp.to_string(index=False)}")

# -----------------------------------------------------------------------------
# 6. Síntese para conferência com o texto da seção 3.4
# -----------------------------------------------------------------------------
# Valores calculados dinamicamente sobre a base atual. Use-os para atualizar
# o texto da tese sempre que a base for alterada.
n = len(df)
pt = (df["pres_brasil_partido"] == "PT").sum()
pmdb_sen = (df["pres_senado_partido"] == "PMDB").sum()
pmdb_pfl_ccj = df["pres_ccj_partido"].isin(["PMDB", "PFL"]).sum()
relatores_distintos = df["relator_pessoa"].nunique()

print(f"\n--- Síntese para a seção 3.4 ---")
print(f"PT como presidente da República: {pt}/{n} = {pt/n*100:.1f}%")
print(f"PMDB como presidente do Senado:  {pmdb_sen}/{n} = {pmdb_sen/n*100:.1f}%")
print(f"PMDB ou PFL como presidente da CCJ: {pmdb_pfl_ccj}/{n} = "
      f"{pmdb_pfl_ccj/n*100:.1f}%")
print(f"Relatores distintos: {relatores_distintos}")
