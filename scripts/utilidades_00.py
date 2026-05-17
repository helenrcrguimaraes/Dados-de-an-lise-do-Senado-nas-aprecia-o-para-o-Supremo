"""
00_utilidades.py — funções auxiliares usadas pelos demais scripts.

Este arquivo centraliza funções que aparecem em mais de um bloco de análise,
para evitar duplicação de código e garantir que todos os blocos usem a mesma
implementação dos testes que exigem código manual (notadamente, o teste de
Pettitt, que não tem implementação disponível em `pymannkendall` nem em
`scipy`).
"""

import numpy as np


def pettitt_test(y):
    """
    Teste de Pettitt (1979) para detecção de ponto de mudança em série temporal.

    Referência:
        Pettitt, A. N. (1979). "A non-parametric approach to the change-point
        problem". Journal of the Royal Statistical Society. Series C (Applied
        Statistics), 28(2), 126-135.

    Fórmula:
        Para uma série y_1, y_2, ..., y_n:
          U_{t,n} = sum_{i=1}^{t} sum_{j=t+1}^{n} sgn(y_i - y_j)
        onde sgn(x) = +1 se x > 0, 0 se x = 0, -1 se x < 0.

        K = max_{1<=t<=n-1} |U_{t,n}|
        Ponto de mudança = argmax_t |U_{t,n}|

        p-valor aproximado bicaudal:
          p ≈ 2 * exp(-6 * K^2 / (n^3 + n^2))

    Parâmetros
    ----------
    y : array-like
        Série temporal ordenada cronologicamente.

    Retorna
    -------
    dict com:
        K        : estatística do teste (int)
        tau_idx  : posição (1-based) do último valor antes da mudança
        p_value  : p-valor aproximado bicaudal
        U        : vetor de U_{t,n} para t = 1..n-1 (útil para diagnóstico)
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    if n < 3:
        raise ValueError("Série muito curta (n < 3) para o teste de Pettitt.")

    U = np.zeros(n - 1)
    for t in range(1, n):
        # U_{t,n} = soma dos sinais de (y_i - y_j) para i <= t e j > t
        antes = y[:t][:, None]
        depois = y[t:][None, :]
        U[t - 1] = np.sum(np.sign(antes - depois))

    K = int(np.max(np.abs(U)))
    tau_idx = int(np.argmax(np.abs(U))) + 1  # 1-based
    p = min(2.0 * np.exp(-6.0 * K ** 2 / (n ** 3 + n ** 2)), 1.0)

    return {"K": K, "tau_idx": tau_idx, "p_value": p, "U": U}


def describe(valores):
    """
    Estatísticas descritivas de uma série: n, média, mediana, desvio-padrão
    amostral (ddof = 1), mínimo e máximo.

    O desvio-padrão é amostral (divisor n-1) por convenção estatística quando
    os dados são tratados como amostra.
    """
    v = np.asarray(valores, dtype=float)
    return {
        "n": len(v),
        "media": v.mean(),
        "mediana": np.median(v),
        "dp": v.std(ddof=1),
        "min": v.min(),
        "max": v.max(),
    }


def indice_dispersao_partidaria(row):
    """
    Número de partidos DISTINTOS ocupando as quatro posições-chave em uma
    dada indicação: Presidência da República, Presidência do Senado,
    Presidência da CCJ, Relator.

    Varia de 1 (todas do mesmo partido) a 4 (quatro partidos distintos).
    """
    partidos = [
        row["pres_brasil_partido"],
        row["pres_senado_partido"],
        row["pres_ccj_partido"],
        row["relator_partido"],
    ]
    return len(set(partidos))
