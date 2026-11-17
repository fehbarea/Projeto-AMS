# O meu dado, com rigor — relatório do Laboratório 03

Conjunto: `C:\pos-agentes\Projeto-AMS\data\casos\60_casos.csv` · 60 linhas · 9 variáveis

Medidas geradas pelo `medidas.py`: desvio padrão amostral (ddof=1),
quartis por interpolação linear, extremos pela regra da amplitude
interquartil — fora de 1,5 × a caixa (slide 24). As medidas são do
programa; as decisões são SUAS. Preencha todos os blocos `R:` e
confira com `python teste.py`.

## Medidas por variável

| variável | tipo | n | faltantes | média | mediana | desvio | Q1 | Q3 | AIQ | mín | máx |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| id_caso | categórica (60 valores; moda: C35) | 60 | 0 | — | — | — | — | — | — | — | — |
| data | categórica (30 valores; moda: 2026-03-05) | 60 | 0 | — | — | — | — | — | — | — | — |
| tipo_maquina | categórica (4 valores; moda: TORNO) | 60 | 0 | — | — | — | — | — | — | — | — |
| idade_meses | numérica | 60 | 0 | 49.6500 | 47.0000 | 29.2568 | 31.5000 | 62.5000 | 31.0000 | 3.0000 | 216.0000 |
| temperatura_c | numérica | 60 | 0 | 67.1867 | 64.2500 | 7.5034 | 61.0000 | 73.2500 | 12.2500 | 58.0000 | 83.5000 |
| vibracao_mm_s | numérica | 60 | 0 | 4.4400 | 3.9500 | 1.8106 | 3.1750 | 5.5500 | 2.3750 | 2.0000 | 8.4000 |
| horas_desde_manutencao | numérica | 60 | 0 | 116.7500 | 100.0000 | 48.2928 | 83.7500 | 150.0000 | 66.2500 | 40.0000 | 219.0000 |
| acao_correta | categórica (3 valores; moda: seguir_operando) | 60 | 0 | — | — | — | — | — | — | — | — |
| falhou_depois | numérica | 60 | 0 | 0.4000 | 0.0000 | 0.4940 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |

## Extremos marcados (fora de 1,5 × a caixa — slide 24)

### Extremos de `idade_meses` — 2 valor(es), limites [-15.0000; 109.0000]

| linha | valor |
|---:|---:|
| 12 | 216.0000 |
| 42 | 120.0000 |

Decisão sobre ESTES extremos — manter ou remover, caso a caso,
com o motivo (slide 25: quem remove sem dizer, mente por omissão):

R: Esses valores não podem ser retirados ou normalizados, pois a idade é um dado importante a respeito da máquina.


## Faltantes (os três mecanismos do slide 26)

Nenhuma variável tem valores faltantes.

## As quatro perguntas do slide 29

**1. Média e mediana se separam em alguma variável? Em qual?**

R: Sim.
- horas_desde_manutencao: média 116.75, mediana 100.00  
- temperatura_c: média 67.19, mediana 64.25  
- vibracao_mm_s: média 4.44, mediana 3.95
- idade_meses: média 49.65, mediana 47.00

**2. Quantos extremos foram marcados, e quantos você decidiu manter?**

R: Foram marcados 2 extremos na variável idade_meses, decidi manter ambos, pois são consistentes.

**3. Algum faltante parece do terceiro mecanismo?**

R: Não.

**4. O que a análise da D1 não tinha visto?**

R:

## Comparação com a análise exploratória da D1

O que mudou de lá para cá — o que a análise de lá não tinha visto,
e o que estas decisões escritas mudam no conjunto que a D5 vai usar:

R:
