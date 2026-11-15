# FONTE — procedência dos 60 casos do AMS

**Arquivo:** `casos-ams-60.csv` — 60 casos de manutenção industrial, no
mesmo formato da reserva da D2 (`casos-de-reserva.csv`, pacote `D2-06`).

| Casos | Origem |
|---|---|
| C01 a C30 | A reserva da D2, **cópia sem alteração** |
| C31 a C60 | A ampliação da AO1 da D3, **dados inventados pela coordenação do curso** para o gabarito do caminho padrão |

## Por que inventados

A AO1 da D3 pede ampliar o conjunto de 30 para pelo menos 60 casos
rotulados. No projeto padrão, os 30 primeiros são a reserva da D2, que
também é inventada: o *AI4I 2020* da D1 traz o desfecho (falhou ou não),
mas não a decisão correta rotulada, e sem decisão rotulada não há acerto a
calcular. Nenhuma linha veio de base pública nem de dado real de empresa.

## Como a ampliação foi calibrada

Os 30 casos novos repetem os padrões da reserva, e mais nada:

- casos fáceis nas quatro famílias (TORNO, PRENSA, COMPRESSOR, ROBOT);
- falhas intermitentes com leitura boa (C39, C51), como C07 e C08;
- excesso de cautela da família depois de duas falhas (C45, C50), como C10;
- máquinas no limiar de vibração: quatro atípicos em que bastava inspecionar
  (C32, C37, C42, C47), como C11 e C22, e duas falhas reais logo acima do
  limiar (C35, C49), que são o contraponto.

Com isso a variante B (faixa de atenção) ganha em alguns casos e perde em
outros, e a comparação da AO1 termina onde a AO1 avisa que a maioria vai
terminar: **"não sei ainda"**. O calibre foi escolhido para isso de
propósito, e está declarado aqui para ninguém ler o resultado como
descoberta.

## Colunas

As mesmas da reserva: `id_caso`, `data` (a ordem cronológica importa: o
estado interno se acumula caso a caso), `tipo_maquina`, `idade_meses`,
`temperatura_c`, `vibracao_mm_s`, `horas_desde_manutencao`, `acao_correta`
(o rótulo) e `falhou_depois` (o desfecho que o ambiente revela).

## Licença e reúso

Sem restrição: dados de autoria da coordenação do curso (CEDAGI/UTFPR). Os
mesmos 60 casos, em `casos-linha-de-base.jsonl`, são o artefato que o
Contrato de Saída da D3 promete às disciplinas seguintes.
