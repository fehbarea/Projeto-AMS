# Fonte dos dados — AI4I 2020 Predictive Maintenance Dataset

- **URL oficial:** https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip
  (UCI Machine Learning Repository, ID 601 — https://archive.ics.uci.edu/dataset/601)
- **Data do download:** agosto/2026 (o `scripts/baixar-dados.py` refaz o download
  e registra a data do dia; esta amostra é o fallback offline do curso)
- **Licença:** CC BY 4.0 — https://creativecommons.org/licenses/by/4.0/
- **Arquivo local:** `data/amostra/ai4i2020.csv` — 200 registros versionados,
  14 colunas. O dataset completo tem 10.000 e chega em `data/raw/` pelo
  `scripts/baixar-dados.py`; a entrega da AO1 e da N2 pede o completo
  (piso de 500 registros).
- **Citação recomendada:**
  Matzka, S. (2020). *AI4I 2020 Predictive Maintenance Dataset* [Data set].
  UCI Machine Learning Repository, ID 601.

## Colunas (dicionário resumido)

| Coluna | Significado |
|---|---|
| `UDI` | identificador do registro |
| `Product ID`, `Type` | produto (letra inicial = qualidade L/M/H) e tipo L/M/H |
| `Air temperature [K]`, `Process temperature [K]` | temperaturas de ar e processo |
| `Rotational speed [rpm]`, `Torque [Nm]` | rotação e torque do fuso |
| `Tool wear [min]` | minutos de desgaste da ferramenta |
| `Machine failure` | rótulo geral (0/1) |
| `TWF`, `HDF`, `PWF`, `OSF`, `RNF` | os cinco modos de falha (0/1) |
