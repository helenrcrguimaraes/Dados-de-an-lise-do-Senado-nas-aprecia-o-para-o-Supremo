# Análise quantitativa das sabatinas do Senado Federal para o Supremo Tribunal Federal

Pacote de dados, scripts e instruções para reproduzir a análise quantitativa
da apreciação do Senado Federal sobre indicados ao Supremo Tribunal Federal.
Cobre: votação na Comissão de Constituição, Justiça e Cidadania (CCJ),
votação no Plenário, tempo de tramitação, composição partidária das
posições-chave, variáveis quantitativas das sabatinas, distribuição temática
das indagações e testes de associação entre essas dimensões.

## Estrutura

```
analise_sabatinas_stf/
├── README.md
├── requirements.txt
├── dados/                     ← entradas
│   ├── ccj_votacao.csv
│   ├── plenario_votacao.csv
│   ├── tramitacao_tempos.csv
│   ├── partidos_posicoes.csv
│   ├── sabatinas_quantitativo.csv
│   └── temas_indagacoes.csv
├── scripts/                   ← análises
│   ├── utilidades_00.py
│   ├── 01_ccj.py
│   ├── 02_plenario.py
│   ├── 03_tramitacao.py
│   ├── 04_partidos.py
│   ├── 05_sabatinas_quantitativo.py
│   ├── 06_temas.py
│   ├── 07_associacoes.py
│   └── 08_dispersao_associacoes.py
└── outputs/                   ← vazio; populado pela execução dos scripts
```

## Requisitos

- Python 3.12 ou superior.
- Bibliotecas listadas em `requirements.txt`.

Instalação das dependências:

```
pip install -r requirements.txt
```

## Execução

Todos os scripts são independentes e podem ser executados em qualquer ordem.

Para executar todos os blocos:

```
cd scripts
python 01_ccj.py
python 02_plenario.py
python 03_tramitacao.py
python 04_partidos.py
python 05_sabatinas_quantitativo.py
python 06_temas.py
python 07_associacoes.py
python 08_dispersao_associacoes.py
```

Os scripts gravam tabelas, gráficos e documentos auxiliares na pasta
`outputs/` (criada automaticamente se não existir).

## Decisões metodológicas

### Testes estatísticos

- **Tendência temporal:** Mann-Kendall clássico (Mann, 1945), implementado
  via `pymannkendall.original_test`. A estatística τ reportada é o τ-a de
  Kendall (sem correção para empates).
- **Detecção de ponto de mudança:** teste de Pettitt (Pettitt, 1979) com
  p-valor pela aproximação assintótica `p ≈ 2 · exp(−6 K² / (n³ + n²))`.
  Conservador para n pequeno. Aplicado apenas às variáveis com tendência
  significativa no Mann-Kendall (α = 0,05), seleção determinada em tempo
  de execução.
- **Critério de outlier:** regra de Tukey (Q1 − 1,5·IQR; Q3 + 1,5·IQR),
  reportada integralmente; a exclusão de pontos atípicos é decisão
  metodológica explícita controlada pela constante `INDICADOS_EXCLUIDOS`
  nos scripts em que se aplica.
- **Correlação bivariada:** τ-b de Kendall (com correção para empates) via
  `scipy.stats.kendalltau(variant='b')`, complementado pelo ρ de Spearman
  via `scipy.stats.spearmanr`. Distinto do τ-a usado nos testes de
  tendência.
- **Comparação de grupos:** teste de Mann-Whitney U via
  `scipy.stats.mannwhitneyu(alternative='two-sided')`.
- **Estatística descritiva:** desvio-padrão amostral, com divisor n − 1
  (`ddof = 1`).

### Escopo da amostra

A série completa de indicados ao Supremo Tribunal Federal cobertos pelo
projeto vai de Paulo Brossard (1989) até a indicação mais recente. Cada
CSV cobre o subconjunto efetivamente documentado para sua dimensão:

- `tramitacao_tempos.csv` (n = 29): inclui todos desde Brossard.
- `plenario_votacao.csv` (n = 28): inicia em Sepúlveda Pertence, pois os
  dados anteriores não estão consolidados.
- `partidos_posicoes.csv` (n = 29): inclui todos desde Brossard.
- `ccj_votacao.csv` (n = 21): inicia em Ellen Gracie, primeira sabatina
  pública para o STF.
- `sabatinas_quantitativo.csv` (n = 20): inicia em Ellen Gracie e omite
  Ricardo Lewandowski (2006), cujos dados não foram disponibilizados pela
  fonte.
- `temas_indagacoes.csv` (n = 1.210 indagações, em 20 sabatinas):
  classificação temática das indagações registradas, mesma cobertura de
  `sabatinas_quantitativo.csv`.

## Estrutura dos arquivos de entrada

### `ccj_votacao.csv`, `plenario_votacao.csv`

Uma linha por indicado, em ordem cronológica das votações.

| Coluna       | Tipo  | Descrição                                  |
|--------------|-------|--------------------------------------------|
| indicado     | texto | Nome do(a) indicado(a)                     |
| favoraveis   | int   | Votos favoráveis                           |
| contrarios   | int   | Votos contrários                           |
| abstencoes   | int   | Abstenções                                 |
| ausencias    | int   | Ausências                                  |
| quorum       | int   | Número de membros aptos a votar            |

CCJ: quórum variável (23 até Teori Zavascki; 27 a partir da Resolução do
Senado Federal nº 11/2013). Plenário: quórum fixo de 81 senadores.

### `tramitacao_tempos.csv`

| Coluna             | Tipo | Descrição                                |
|--------------------|------|------------------------------------------|
| indicado           | texto| Nome do(a) indicado(a)                   |
| tempo_total        | int  | Dias entre indicação e nomeação          |
| tempo_distribuicao | int  | Dias entre indicação e distribuição ao relator |

### `partidos_posicoes.csv`

Uma linha por indicado com partido e nome ocupando as quatro posições-chave
no momento da indicação:

| Coluna                | Tipo  | Descrição                            |
|-----------------------|-------|--------------------------------------|
| indicado              | texto | Nome do(a) indicado(a)               |
| pres_brasil_pessoa    | texto | Presidente da República              |
| pres_brasil_partido   | texto | Partido do Presidente da República   |
| pres_senado_pessoa    | texto | Presidente do Senado Federal         |
| pres_senado_partido   | texto | Partido do Presidente do Senado      |
| pres_ccj_pessoa       | texto | Presidente da CCJ                    |
| pres_ccj_partido      | texto | Partido do Presidente da CCJ         |
| relator_pessoa        | texto | Relator da indicação                 |
| relator_partido       | texto | Partido do relator                   |
| fonte                 | texto | Fonte documental do registro         |

### `sabatinas_quantitativo.csv`

| Coluna       | Tipo  | Descrição                                  |
|--------------|-------|--------------------------------------------|
| indicado     | texto | Nome do(a) indicado(a)                     |
| senadores    | int   | Senadores que indagaram durante a sabatina |
| indagacoes   | int   | Total de indagações na sabatina            |
| elogios      | int   | Manifestações somente de elogio            |
| rejeicao     | int   | Manifestações de rejeição sem indagação    |
| outras       | int   | Outras manifestações sem indagação         |
| tempo_h      | int   | Duração da sabatina em horas               |

### `temas_indagacoes.csv`

Uma linha por indagação classificada.

| Coluna         | Tipo  | Descrição                                   |
|----------------|-------|---------------------------------------------|
| indicado       | texto | Sabatina em que a indagação foi feita       |
| senador        | texto | Senador que formulou a indagação (NaN se não identificado) |
| tema           | texto | Tema específico da indagação                |
| pagina         | texto | Página de referência na fonte primária      |
| codigo         | float | Código numérico da categoria                |
| macrocategoria | texto | Macrocategoria temática                     |
| categoria      | texto | Categoria temática específica               |

## Saídas geradas pelos scripts

A pasta `outputs/` é distribuída vazia. As tabelas, documentos e
gráficos são gerados pela execução dos scripts e gravados ali. Cada
execução reescreve os arquivos correspondentes.

Principais saídas:

| Bloco | Arquivos principais                                              |
|-------|------------------------------------------------------------------|
| 1     | `tabela_03_ccj_mann_kendall.csv`, `tabela_08_ccj_percentuais.csv`, `tabela_09_ccj_descritivas.csv`, `tabela_12_ccj_pettitt.csv` |
| 2     | `tabela_03_plenario_mann_kendall.csv`, `tabela_10_plenario_percentuais.csv`, `tabela_11_plenario_descritivas.csv`, `tabela_12_plenario_pettitt.csv` |
| 3     | `tabela_13_tramitacao_tempos.csv`, `tabela_14_tramitacao_descritivas_completa.csv`, `tabela_15_tramitacao_descritivas_sem_excluidos.csv`, `tabela_03_tramitacao_mann_kendall.csv`, `criterio_tukey_*.csv` |
| 4     | `quadro_07_partidos.csv`, `tabela_16_*.csv` a `tabela_19_*.csv`, `indice_dispersao.csv` |
| 5     | `tabela_20_*.csv` a `tabela_26_sabatinas_pettitt.csv`            |
| 6     | `tabela_01_macrocategorias.csv`, `tabela_02_categorias.csv` (+ versão `.docx`), `heatmap_macrocategorias_por_indicado.png`, `verificacao_temas_vs_indagacoes.csv` |
| 7     | `tabela_04_ccj_plenario.csv` (+ `.docx`), `tabela_05_sabatina_votacao.csv` (+ `.docx`), `tabela_06_macro_quantitativas.csv` (+ `.docx`), `tabela_07_casos_mann_whitney.csv` (+ `.docx`) |
| 8     | `dispersao_associacoes.csv`                                      |

## Padronização e qualidade dos dados

Os nomes dos indicados foram uniformizados entre os seis CSVs conforme
auditoria cruzada. Convenção adotada:

- Sem acentos quando há prática consagrada na imprensa especializada
  (ex.: "Cezar Peluso", "Luis Roberto Barroso").
- Sem prefixos honoríficos.
- Forma completa para distinguir homônimos (ex.: "Kássio Nunes Marques",
  "Marco Aurélio de Mello").
- Caso específico: o relator da sabatina de Kássio Nunes Marques é
  registrado como "Rodrigo Pacheco" (relator ad hoc que efetivamente
  conduziu a sessão), seguindo decisão metodológica documentada na tese.

A validação de integridade é feita em tempo de execução pelos scripts 01
a 03: a soma `favoraveis + contrarios + abstencoes + ausencias` deve bater
com `quorum` em cada linha; o script aborta com mensagem informativa se
detectar inconsistência.

## Adição de novos indicados

Para incluir uma nova indicação na análise, basta acrescentar uma linha
ao final do CSV correspondente (mantendo a ordem cronológica crescente)
e reexecutar o script. Não é necessário alterar código.

## Referências metodológicas

- MANN, H. B. Nonparametric tests against trend. *Econometrica*, v. 13,
  n. 3, p. 245-259, 1945.
- PETTITT, A. N. A non-parametric approach to the change-point problem.
  *Journal of the Royal Statistical Society. Series C (Applied
  Statistics)*, v. 28, n. 2, p. 126-135, 1979.
- TUKEY, J. W. *Exploratory data analysis*. Reading: Addison-Wesley, 1977.
- BRASIL. Senado Federal. Resolução nº 11, de 2013.
