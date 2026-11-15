# O meu dado, com rigor — relatório do Laboratório 03

Conjunto: `exemplo\meus_casos.csv` · 30 linhas · 7 variáveis

Medidas geradas pelo `medidas.py`: desvio padrão amostral (ddof=1),
quartis por interpolação linear, extremos pela regra da amplitude
interquartil — fora de 1,5 × a caixa (slide 24). As medidas são do
programa; as decisões são SUAS. Preencha todos os blocos `R:` e
confira com `python teste.py`.

## Medidas por variável

| variável | tipo | n | faltantes | média | mediana | desvio | Q1 | Q3 | AIQ | mín | máx |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| id_caso | categórica (30 valores; moda: C13) | 30 | 0 | — | — | — | — | — | — | — | — |
| data | categórica (24 valores; moda: 2026-03-03) | 30 | 0 | — | — | — | — | — | — | — | — |
| tipo_equipamento | categórica (5 valores; moda: Esteira) | 30 | 0 | — | — | — | — | — | — | — | — |
| tensao_v | numérica | 30 | 0 | 64.0633 | 24.0000 | 87.8550 | 24.0000 | 43.4250 | 19.4250 | 12.0000 | 380.0000 |
| pressao_bar | numérica | 30 | 0 | 4.0267 | 1.5000 | 5.7072 | 0.0000 | 2.0000 | 2.0000 | 0.0000 | 16.0000 |
| acao_correta | categórica (3 valores; moda: bloqueio_loto) | 30 | 0 | — | — | — | — | — | — | — | — |
| falhou_depois | numérica | 30 | 0 | 0.2333 | 0.0000 | 0.4302 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 1.0000 |

## Extremos marcados (fora de 1,5 × a caixa — slide 24)

### Extremos de `tensao_v` — 7 valor(es), limites [-5.1375; 72.5625]

| linha | valor |
|---:|---:|
| 2 | 127.0000 |
| 5 | 220.0000 |
| 12 | 380.0000 |
| 15 | 110.0000 |
| 22 | 220.0000 |
| 27 | 127.0000 |
| 30 | 220.0000 |

Decisão sobre ESTES extremos — manter ou remover, caso a caso,
com o motivo (slide 25: quem remove sem dizer, mente por omissão):

R:

### Extremos de `pressao_bar` — 7 valor(es), limites [-3.0000; 5.0000]

| linha | valor |
|---:|---:|
| 3 | 15.0000 |
| 6 | 12.0000 |
| 8 | 14.5000 |
| 11 | 14.0000 |
| 18 | 11.0000 |
| 19 | 16.0000 |
| 24 | 15.5000 |

Decisão sobre ESTES extremos — manter ou remover, caso a caso,
com o motivo (slide 25: quem remove sem dizer, mente por omissão):

R:

### Extremos de `falhou_depois` — 7 valor(es), limites [0.0000; 0.0000]

| linha | valor |
|---:|---:|
| 3 | 1.0000 |
| 6 | 1.0000 |
| 8 | 1.0000 |
| 11 | 1.0000 |
| 17 | 1.0000 |
| 21 | 1.0000 |
| 28 | 1.0000 |

Decisão sobre ESTES extremos — manter ou remover, caso a caso,
com o motivo (slide 25: quem remove sem dizer, mente por omissão):

R:


## Faltantes (os três mecanismos do slide 26)

Nenhuma variável tem valores faltantes.

## As quatro perguntas do slide 29

**1. Média e mediana se separam em alguma variável? Em qual?**

R:

**2. Quantos extremos foram marcados, e quantos você decidiu manter?**

R:

**3. Algum faltante parece do terceiro mecanismo?**

R:

**4. O que a análise da D1 não tinha visto?**

R:

## Comparação com a análise exploratória da D1

O que mudou de lá para cá — o que a análise de lá não tinha visto,
e o que estas decisões escritas mudam no conjunto que a D5 vai usar:

R:
