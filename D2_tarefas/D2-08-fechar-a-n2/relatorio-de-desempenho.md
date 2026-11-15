# Relatório de desempenho da linha de base — modelo

<!--
Item 3 da N2. Este relatório tem as quatro informações que o slide 28 do
E4 cobra, mais a leitura de onde erra (slide 30) — a saída do medir.py já
traz quase tudo pronto: rode `python medir.py` na pasta do D2-06 (ou do
seu projeto) e cole no lugar marcado. Responda NOS COLCHETES, apagando
nada das seções.
-->

**Projeto:**  AMS · Assistente de Manutenção Segura · **Data:** Felipe Alves Barea·

## 1. A métrica primária

[Nome da métrica do seu PEAS, com a fórmula ou o procedimento de cálculo —
como se calcula, sem ambiguidade. Ex.: acerto da decisão — casos com
decisão igual à rotulada, sobre o total.]

[Taxa de Acerto da métrica primária é calculada pelo número de chamados em que a recomendação final do agente é exatamente igual à decisão ideal do especialista humano, dividido pelo total de casos analisados no período.]

## 2. O valor

[A saída do `medir.py`, colada: valor, acertos/total. Ex.: 25/30 = 0.8333.]

[Métrica primária: acerto da decisão (casos com decisão igual à rotulada, sobre o total)
Valor: 25/30 = 0.8333
Conjunto: C:\pos-agentes\Projeto-AMS\data\meus_casos.csv — 30 casos rotulados {'manutencao_padrao': 8, 'bloqueio_loto': 15, 'exigir_parecer': 7}
Onde erra (o rótulo que o agente não deu):
  caso C20: decidiu manutencao_padrao, correto era exigir_parecer
  caso C23: decidiu manutencao_padrao, correto era exigir_parecer
  caso C26: decidiu manutencao_padrao, correto era exigir_parecer
  caso C28: decidiu manutencao_padrao, correto era bloqueio_loto
  caso C29: decidiu manutencao_padrao, correto era exigir_parecer]

## 3. O conjunto
[Sobre quais casos: o arquivo, quantos são, de que período, como se
distribuem pelos rótulos. Se usou o conjunto de reserva do `D2-06`,
declare aqui — sem demérito; a exigência é a declaração.]

[A avaliação foi realizada utilizando o conjunto `meus_casos.csv` para o domínio AMS. Os dados cobrem equipamentos variados e incluem cenários de bloqueio imediato (LOTO), exigência de parecer por instabilidade e manutenção padrão.]

## 4. Onde o agente erra

[A lista de erros que o `medir.py` imprime, colada. Depois, dois
parágrafos: o PADRÃO dos erros (todos do mesmo tipo? concentrados em
quais casos?) e a HIPÓTESE do porquê — o que o agente não enxerga quando
erra. Isto é a matéria-prima da análise do item 5.]

[Erros:
  caso C20: decidiu manutencao_padrao, correto era exigir_parecer
  caso C23: decidiu manutencao_padrao, correto era exigir_parecer
  caso C26: decidiu manutencao_padrao, correto era exigir_parecer
  caso C28: decidiu manutencao_padrao, correto era bloqueio_loto
  caso C29: decidiu manutencao_padrao, correto era exigir_parecer

Apesar de acertar uma valor de 83% é importante ressaltar que o modelo deterministo não leva em considerações possíveis descrições que o chamado poderia conter,
Além disso, alguma limitações já ficam evidentes quando os números são exatos, como o C28, que passou como manutencao_padrao, pois está no limiar para exigir loto, 
que nesse cenário é 50 e o valor do teste é 49.9.
Outro limite evidente é o histórico de falha, que aqui está cravado em 15 dias, sendo assim o agende sugere uma manutencao_padrao pos não identificar falhas anteriores a essa data.

Isso se deve a limitações do estado interno engessado. O agente falhou por rigidez, pois o código exige estritamente 2 falhas para ligar o alerta, ignorando que certas falhas únicas anteriores já eram graves o suficiente para exigir atenção. Já no caso C29 a última falha da máquina aconteceu há 18 dias, estourando a janela de 15 dias do estado interno, fazendo o agente limpar o histórico de uma máquina ainda instável.]

## 5. A tabela comparativa de busca (item 4 da N2)

[Cole aqui a tabela completa dos laboratórios 04 e 05 — as 4 linhas não
informadas e as 4 informadas. Exemplo da forma (os números são os SEUS):]

[
| Busca | Custo | Ações | Nós expandidos | Nós gerados | Prof. máx. | Segundos |
|---|---:|---:|---:|---:|---:|---:|
| largura | 71.0 | 4 | 50 | 118 | 5 | 0.000242 |
| custo_uniforme | 70.5 | 4 | 20 | 47 | 6 | 0.000087 |
| profundidade_limitada(limite=32) | 421.5 | 7 | 8 | 7 | 7 | 0.000032 |
| aprofundamento iterativo(limite=32) | 71.0 | 4 | 57 | 77 | 4 | 0.000215 |
| gulosa[admissivel] | 71.0 | 4 | 5 | 16 | 4 | 0.000113 |
| a_estrela[admissivel] | 70.5 | 4 | 7 | 19 | 4 | 0.000075 |
| gulosa[inadmissivel] | 191.0 | 5 | 6 | 16 | 5 | 0.000090 |
| a_estrela[inadmissivel] | 191.0 | 5 | 6 | 16 | 5 | 0.000069 |


Sim, o custo ótimo foi mantido expandindo significativamente menos nós, que caiu de 20 nós expandidos no Custo Uniforme para apenas 7 nós expandidos no A*, economia de 13 
nós, o menor curto possível da minha amostra é 70.5, pois é obrigatório fazer essas categorias: "RISCO", "NORMA", "DECISAO_LOTO", "PARECER".

As seguintes etapas formam o melhor caminho:

EstimarRiscoBaixo (Categoria: RISCO)  
Custo: 0.5  
O agente define o risco atual como "Baixo".  
  
IdentificarNormas (Categoria: NORMA)  
Custo: 45.0  
O agente escolhe o conjunto básico de normas em vez das normas caras que custariam 100.0.  

DispensarBloqueio (Categoria: DECISAO_LOTO)  
Custo: 5.0  
Como o risco definido no passo 1 foi "Baixo", dispensar o bloqueio custa apenas o valor base (5.0). Se o agente tivesse escolhido RecomendarBloqueio aqui, a sua função de custo aplicaria a multa de travamento indevido, atirando o custo desta ação para 250.0.  

GerarParecerJustificado (Categoria: PARECER)  
Custo: 20.0  
O agente escolhe o parecer padrão em vez do detalhado que custaria 40.0.  

*Cálculo final:* 0.5 + 45.0 + 5.0 + 20.0 = 70.5  

A pronfundidade limitada por seguir uma ramo até o fim/limite não se importando com o custo, por isso o custo alto de  421.5, apesar de ter encontrado um caminho
relativamente curto de 8 nós expandidos isso é devido a uma conincidência do meu estado de busca, pois se tivesse encontrado primeiro um caminho mais longo ele teria devolvido como solução, diante disso, esse resultado é devido ao algoritimo ser cego ao custo e a quantidade de nós, se preocupando apenas no caminho dentro do limite.]
