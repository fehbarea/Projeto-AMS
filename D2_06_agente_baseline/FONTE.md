# FONTE — procedência do conjunto de reserva

**Arquivo:** `casos-de-reserva.csv` — 30 casos de manutenção industrial,
rotulados com o desfecho (a ação correta) e com o que aconteceu depois
(`falhou_depois`).

## Origem

**Dados inventados pela coordenação do curso**, para fim didático, em
30/08/2026. Não há fonte externa: nenhuma linha veio de base pública nem
de dado real de empresa. Os valores foram calibrados para que o conjunto
tenha casos fáceis, casos difíceis e dois atípicos (slide 24 do D2-E4) —
e para que a linha de base do esqueleto acerte 25 dos 30, com os cinco erros
concentrados em padrões sistemáticos, que é a matéria-prima da análise
escrita.

## Por que inventado

A rede de proteção do laboratório (slide 29 do D2-E4): quem não tiver o
conjunto de dados próprio pronto faz o laboratório inteiro e entrega a N2
sobre este conjunto, sem perda de nota — desde que a análise escrita diga
que usou a reserva. Um conjunto inventado é preferível a um conjunto
real sem desfecho: **sem desfecho rotulado não há métrica a calcular**.

## O que cada coluna significa

| Coluna | Significado |
|---|---|
| `id_caso` | Identificador do caso (C01 a C30) |
| `data` | Data da leitura — a ordem cronológica importa: o estado interno do agente se acumula caso a caso |
| `tipo_maquina` | Família da máquina (TORNO, PRENSA, COMPRESSOR, ROBOT) |
| `idade_meses` | Idade da máquina, em meses |
| `temperatura_c` | Temperatura de operação, °C |
| `vibracao_mm_s` | Vibração medida, mm/s |
| `horas_desde_manutencao` | Horas de operação desde a última manutenção |
| `acao_correta` | O RÓTULO: a decisão correta (`seguir_operando`, `inspecionar_antes_de_operar`, `parar_para_manutencao`) |
| `falhou_depois` | 1 se a máquina falhou depois da leitura, 0 se não — é o desfecho que o ambiente revela ao agente, e o que alimenta o estado interno |

## Licença e reúso

Sem restrição — dados de autoria da coordenação do curso (CEDAGI/UTFPR),
criados para a disciplina D2. As disciplinas D5, D7 e D10 devem reusar o
MESMO conjunto (slide 31 do D2-E4): guarde o arquivo junto do projeto.
