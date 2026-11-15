# O meu dado, com rigor — relatório do Laboratório 03

Conjunto: `exemplo\casos-de-reserva.csv` · 30 linhas · 9 variáveis

Medidas geradas pelo `medidas.py`: desvio padrão amostral (ddof=1),
quartis por interpolação linear, extremos pela regra da amplitude
interquartil — fora de 1,5 × a caixa (slide 24). As medidas são do
programa; as decisões são SUAS. Preencha todos os blocos `R:` e
confira com `python teste.py`.

## Medidas por variável

| variável | tipo | n | faltantes | média | mediana | desvio | Q1 | Q3 | AIQ | mín | máx |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| id_caso | categórica (30 valores; moda: C23) | 30 | 0 | — | — | — | — | — | — | — | — |
| data | categórica (15 valores; moda: 2026-03-16) | 30 | 0 | — | — | — | — | — | — | — | — |
| tipo_maquina | categórica (4 valores; moda: PRENSA) | 30 | 0 | — | — | — | — | — | — | — | — |
| idade_meses | numérica | 30 | 0 | 51.1000 | 47.0000 | 35.5870 | 30.0000 | 63.0000 | 33.0000 | 3.0000 | 216.0000 |
| temperatura_c | numérica | 30 | 0 | 66.7400 | 64.0000 | 7.6391 | 61.0000 | 72.7500 | 11.7500 | 58.0000 | 82.5000 |
| vibracao_mm_s | numérica | 30 | 0 | 4.3600 | 3.9500 | 1.8708 | 3.0250 | 5.3750 | 2.3500 | 2.0000 | 8.4000 |
| horas_desde_manutencao | numérica | 30 | 0 | 115.1667 | 98.0000 | 50.4149 | 81.2500 | 148.7500 | 67.5000 | 40.0000 | 214.0000 |
| acao_correta | categórica (3 valores; moda: seguir_operando) | 30 | 0 | — | — | — | — | — | — | — | — |
| falhou_depois | numérica | 30 | 0 | 0.3667 | 0.0000 | 0.4901 | 0.0000 | 1.0000 | 1.0000 | 0.0000 | 1.0000 |

## Extremos marcados (fora de 1,5 × a caixa — slide 24)

### Extremos de `idade_meses` — 1 valor(es), limites [-19.5000; 112.5000]

| linha | valor |
|---:|---:|
| 12 | 216.0000 |

Decisão sobre ESTES extremos — manter ou remover, caso a caso,
com o motivo (slide 25: quem remove sem dizer, mente por omissão):

R: Manter, é possível uma prensa estar em funcionanamento a 216 meses e relevante para decisões do agente.


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
