# Relatório de desempenho da linha de base — gabarito do caminho padrão (AMS)

> **Gabarito do projeto padrão, para conferir.** É o
> `relatorio-de-desempenho-modelo.md` do `D2-08` preenchido para o AMS,
> com as saídas reais dos comandos. Ele cobre os labs 04, 05 e 06 e os
> itens 3 e 4 da N2. Todos os números abaixo são determinísticos, exceto
> a coluna de segundos, que muda de máquina para máquina.

**Projeto:** AMS · Assistente de Manutenção Segura

## 1. A métrica primária

Acerto da recomendação: casos em que a decisão do agente é igual à coluna
`acao_correta`, divididos pelo total de casos. Duas secundárias
acompanham, conforme a seção 4 do `agent-spec.md`: **falhas liberadas**
(casos com `falhou_depois = 1` em que o agente recomendou seguir operando,
sobre os casos que falharam) e **paradas desnecessárias** (paradas
recomendadas em casos cujo rótulo não era parar, sobre o total de paradas
recomendadas).

## 2. O valor

A linha de base é o `esqueleto.py` do `D2-06` **sem alteração**: no
caminho padrão, as regras de fábrica já são as do AMS. Saída de
`python medir.py`:

```
Métrica primária: acerto da decisão (casos com decisão igual à rotulada, sobre o total)
Valor: 25/30 = 0.8333
Conjunto: casos-de-reserva.csv — 30 casos rotulados
  {'seguir_operando': 16, 'parar_para_manutencao': 7,
   'inspecionar_antes_de_operar': 7}
```

(A última linha sai inteira no terminal; aqui foi quebrada para caber na página.)

Secundárias, contadas sobre a mesma saída: **2 falhas liberadas de 11**
(C07, C08) e **2 paradas desnecessárias de 9** (C11, C22), ou 22%.

Para dar escala ao 0,83, a mesma medição com três outras políticas:

| Política | Acerto | Falhas liberadas | Paradas desnecessárias |
|---|---:|---:|---:|
| Sempre seguir operando | 16/30 = 0,53 | 11 de 11 | 0 de 0 |
| Sempre parar | 7/30 = 0,23 | 0 de 11 | 23 de 30 |
| Só a condição reativa (sem estado interno) | 23/30 = 0,77 | 4 de 11 | 2 de 9 |
| **Linha de base (reativa + estado interno)** | **25/30 = 0,83** | **2 de 11** | **2 de 9** |

A linha "só reativa" é o que se obtém apagando a segunda condição de
`decidir()`. A diferença entre ela e a linha de base (C18 e C19, duas
falhas a menos liberadas) é o que o estado interno compra.

## 3. O conjunto

`casos-de-reserva.csv`, do `D2-06`: 30 casos de manutenção industrial,
em ordem cronológica, com 16 casos "seguir operando", 7 "inspecionar" e 7
"parar"; 11 das 30 máquinas falharam depois. O conjunto foi montado pela
coordenação para fim didático e tem casos fáceis, difíceis e dois
atípicos. **Usei o conjunto de reserva do `D2-06`**: no projeto padrão ele
é o conjunto de avaliação, porque o *AI4I 2020* da D1 não traz a decisão
correta rotulada.

## 4. Onde o agente erra

```
Onde erra (o rótulo que o agente não deu):
  caso C07: decidiu seguir_operando, correto era inspecionar_antes_de_operar
  caso C08: decidiu seguir_operando, correto era inspecionar_antes_de_operar
  caso C10: decidiu inspecionar_antes_de_operar, correto era seguir_operando
  caso C11: decidiu parar_para_manutencao, correto era inspecionar_antes_de_operar
  caso C22: decidiu parar_para_manutencao, correto era inspecionar_antes_de_operar
```

**O padrão.** Os cinco erros não são aleatórios; são três padrões. C07 e
C08 são a falha intermitente: dois tornos com leitura boa (60 e 61 °C, 3,0
e 3,1 mm/s) que falharam depois. A regra reativa não vê nada de errado, e
o estado interno só acende depois de duas falhas da família, ou seja,
tarde. C10 é o excesso de cautela: outro torno, leitura igualmente boa,
recebe inspeção porque a família acabou de falhar; o estado não distingue
máquina dentro da família. C11 e C22 são os atípicos no limiar: um
compressor de 3 meses com 7,4 mm/s e um robô com 7,1 mm/s, logo acima dos
7,0 que disparam a parada, onde bastava inspecionar.

**A hipótese.** O agente erra onde falta **informação**, não onde falta
regra: a falha intermitente e a identidade da máquina não estão na
leitura, e a idade da máquina está no registro mas nenhuma regra a usa.
Os dois erros que importam para a segurança (C07, C08) são exatamente os
que nenhum limiar sobre a leitura do instante consegue pegar.

## 5. A tabela comparativa de busca (item 4 da N2)

Saída de `python ams_conformidade.py` (a formulação da seção 7 do
`agent-spec.md`). As oito primeiras linhas são as que os esqueletos dos
labs 04 e 05 imprimem; as duas últimas são o gabarito do caminho desafio
do lab-05.

| Busca | Custo | Ações | Nós expandidos | Nós gerados | Prof. máx. | Segundos |
|---|---:|---:|---:|---:|---:|---:|
| largura | 172.0 | 14 | 20729 | 20736 | 14 | 0.0518 |
| custo_uniforme | 128.0 | 14 | 20729 | 20736 | 14 | 0.0818 |
| profundidade_limitada(limite=32) | 172.0 | 14 | 15 | 14 | 14 | 0.0001 |
| aprofundamento_iterativo(limite=32) | 172.0 | 14 | 27231 | 134798 | 14 | 0.3235 |
| gulosa[admissivel] | 128.0 | 14 | 15 | 60 | 14 | 0.0002 |
| a_estrela[admissivel] | 128.0 | 14 | 15521 | 17712 | 14 | 0.081 |
| gulosa[inadmissivel] | 128.0 | 14 | 15 | 60 | 14 | 0.0002 |
| a_estrela[inadmissivel] | 128.0 | 14 | 3691 | 5916 | 14 | 0.0252 |
| gulosa[desafio] | 128.0 | 14 | 15 | 75 | 14 | 0.0004 |
| a_estrela[desafio] | 128.0 | 14 | 3577 | 8704 | 14 | 0.0452 |

**A pergunta do lab-04: alguma busca achou caminho mais barato que a
largura?** Sim. O custo uniforme libera a ordem em 128 minutos; a largura,
em 172. Os dois caminhos têm as mesmas 14 ações: todo caminho até o
objetivo confere os nove itens e resolve as cinco pendências. A diferença
de 44 minutos é só **ordem**. O caminho ótimo confere primeiro os quatro
itens que não abrem pendência e, a cada item que abre uma, resolve na hora,
antes de conferir o próximo. A largura confere os nove itens primeiro e
deixa as cinco pendências para o fim, pagando o dobro em cada item
conferido com pendência aberta. No AMS, largura é ótima em número de ações e nunca em custo.

**A pergunta do lab-05: o A estrela com a heurística admissível manteve o
custo ótimo e expandiu menos que o custo uniforme?** Manteve (128) e
expandiu 15 521 nós contra 20 729, uma economia de 25%. A economia é
modesta porque a heurística do catálogo **ignora as pendências que os
itens ainda não conferidos vão abrir**: no estado inicial ela estima 50
minutos, e o custo real é 128.

**O parágrafo da dominância (caminho padrão).** A heurística inadmissível
é o dobro da admissível em todo estado: estima sempre mais, e por isso o A
estrela com ela expande 4,2 vezes menos (3 691 contra 15 521). Aqui ela
não piorou o custo, que ficou em 128, mas isso é propriedade deste espaço
e não garantia: como todo caminho tem as mesmas 14 ações e só o
re-trabalho diferencia um do outro, superestimar não desviou a busca. No
subproblema de diagnóstico do catálogo, a mesma ideia devolveu custo 77
contra o ótimo 20. Dominância só vale como argumento **entre
admissíveis**; entre uma admissível e uma inadmissível, "expande menos" não
diz nada sobre a qualidade do caminho.

**O parágrafo da dominância (caminho desafio).** A heurística própria
remove a restrição do re-trabalho e soma, ao que a do catálogo já conta,
as pendências que os itens pendentes vão abrir. Continua admissível, já
que toda pendência futura terá de ser resolvida e o re-trabalho só soma, e
domina a do catálogo: estima igual ou mais em todo estado (128 contra 50
no inicial, exata ali). O A estrela com ela expande 3 577 nós, 4,3 vezes
menos que com a do catálogo e 5,8 vezes menos que o custo uniforme, com o
mesmo custo 128. Os 3 577 que sobram vêm do empate: há muitas ordens
ótimas de conferência (qualquer permutação dos quatro itens sem pendência
custa o mesmo), e o A estrela expande o platô inteiro.

**A ressalva de contagem.** A profundidade limitada expandiu 15 nós e a
gulosa também, e as duas parecem imbatíveis. Não são. A profundidade
limitada é recursiva e não tem fronteira: nela, "nós expandidos" conta
entradas na recursão, e parte da vantagem aparente é diferença de
contagem (slide 20 do E3). Além disso, ela desceu pela primeira ação da
lista, nunca precisou voltar e devolveu o caminho caro (172). A gulosa acertou o ótimo porque, neste
espaço, escolher sempre o passo que mais reduz a estimativa (conferir
primeiro os itens sem pendência e fechar cada pendência assim que ela
abre, já que pendência aberta pesa na estimativa) coincide com a boa
ordem.
Com outra ordem de itens na lista, os dois números mudam. Expandir pouco
não é mérito se o caminho não é o ótimo, ou se ele saiu ótimo por acaso.

## 6. A linha da D2 na régua de continuidade

A régua de continuidade do projeto padrão pede, a cada disciplina, a linha
que ela deixa. A da D2 é esta, declarada na origem para não precisar de
reconstrução — é a primeira linha da tabela, e é contra ela que todas as
seguintes são lidas.

| Disciplina | Métrica primária | Custo por tarefa | Latência p95 | De onde vem o número |
|---|---|---|---|---|
| **D2 — Fundamentos de Agentes** | **Acerto da recomendação: 25 de 30 = 0,8333**, sobre os 30 casos de sensor; com as duas secundárias ao lado, **2 falhas liberadas de 11** e **2 paradas desnecessárias de 9** | *não gravado na disciplina de origem* | *não gravado na disciplina de origem* | este relatório: a métrica na seção 1, o valor e as secundárias na seção 2, o conjunto na seção 3 |

**Custo e latência.** A linha de base não chama modelo nenhum: não há
tokens a contar, e por isso não há custo por tarefa no formato da régua. A
tabela da seção 5 tem uma coluna de segundos, mas o cabeçalho deste
relatório já avisa que ela **muda de máquina para máquina** — é tempo de
busca em memória, não latência de serviço, e as duas não são a mesma
grandeza. Nenhum dos dois entra estimado: célula sem medida no formato da
régua fica *não gravado*.

**Marca de descontinuidade.** A régua atravessa métricas diferentes. Aqui
é acerto de decisão sobre leitura de sensor; da D9 em diante é o
número-chave do AMS sobre o conjunto de espera. **As duas não se comparam
entre si** — a régua registra a trajetória do projeto, e não uma curva de
progresso. O que esta linha oferece às de baixo não é um número para
superar, e sim a escala: a seção 2 mostra o que as políticas triviais
("sempre parar", "sempre seguir", só reativa) conseguem no mesmo conjunto,
e é isso que diz quanto do 0,8333 é mérito da decisão e quanto é feitio da
amostra.

**Por que a primária é o acerto da recomendação, com as duas ao lado.** Um
agente que nunca manda parar não libera parada desnecessária nenhuma, e um
que manda parar sempre não libera falha nenhuma: cada secundária, sozinha,
premia um extremo inútil. É a mesma razão pela qual, na D5, a acurácia não
serve como primária numa classe rara. Quem copiar esta linha para outro
lugar copia as três células juntas.

## Erro previsível

No relatório: o valor sem o conjunto, ou a reserva usada sem declaração.
Na tabela: ler "a gulosa expandiu 15" como vitória, e o parágrafo de
dominância entre a admissível e a inadmissível sem dizer que a
inadmissível não tem garantia. Os três sinais de defeito do guia de
correção não aparecem aqui: o custo uniforme não é pior que a largura, e
o A estrela admissível não expande mais nem devolve custo pior que o
custo uniforme.

## O que transferir para o seu domínio

A tabela com as políticas triviais (sempre sim, sempre não, só reativa)
dá escala ao número da linha de base e mede o que cada condição compra.
Na busca, a pergunta é sempre a relação entre as linhas, não os números:
os seus serão outros.
