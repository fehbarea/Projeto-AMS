# Análise — gabarito do caminho padrão (AMS)

> **Gabarito do projeto padrão, para conferir.** É o `analise-modelo.md`
> do `D2-08` preenchido para o AMS: o item 5 da N2, em uma página. Cada
> afirmação cita um número ou um caso do `relatorio-de-desempenho-AMS.pdf`;
> é essa amarração que separa o adequado do excelente. Uma análise sua que
> chegue às mesmas conclusões precisa citar os **seus** números.

## O que torna o problema difícil

A observabilidade parcial não é rótulo no AMS: a linha de base liberou os
tornos C07 e C08, que falharam depois, porque a leitura deles era boa (60
e 61 °C, 3,0 e 3,1 mm/s). A informação que decide, uma falha intermitente
que ainda não apareceu nos sensores, não está na percepção do instante.
Nenhum limiar sobre a leitura pega esses dois casos, e eles são os únicos
erros da linha de base que colocam alguém em risco.

A estocasticidade aparece no par C07 e C10: dois tornos com leituras
quase iguais, um falhou e o outro não. Por isso o estado interno, que
responde pela família e não pela máquina, erra para os dois lados: chega
tarde em C07 e C08 e sobra em C10.

A discretização em limiares custa os atípicos. C11 e C22 passaram dos
7,0 mm/s por 0,4 e 0,1 e receberam parada onde bastava inspecionar, e o
registro de C11 dizia que o compressor tinha 3 meses de uso. A regra tinha
a idade na mão e não a usou.

Na busca, a dificuldade é a ordem: todo caminho de liberação tem as mesmas
14 ações, e o que separa 128 de 172 minutos é resolver cada pendência
antes de conferir o item seguinte. A heurística do catálogo ignora as
pendências futuras e por isso economiza só 25% de expansões sobre o custo
uniforme.

## Que tipo de agente o problema realmente exige

Reativo simples não basta, e há número para isso: sem a condição de estado
interno, o agente acerta 23 de 30 e libera 4 máquinas que falharam; com
ela, 25 de 30 e libera 2 (C18 e C19 são as recuperadas). O AMS precisa ser
**baseado em modelo**, com estado interno por família e política de
esquecimento de 7 dias.

A escolha obriga o projeto a avaliar os casos na ordem cronológica e a
declarar a janela. E dispensa, por enquanto, busca e planejamento na
decisão de risco: cada ordem pede uma decisão, não uma sequência de ações.
A busca fica na fatia em que a ordem muda o custo, a auditoria de
liberação.

O que o problema pede de verdade vai além: a assimetria entre liberar uma
máquina que vai falhar e parar uma que não ia é a marca de um agente
**baseado em utilidade**. A linha de base trata os dois erros como iguais
na métrica primária, e só a secundária das falhas liberadas mostra a
diferença.

## O que isto muda no projeto

O agente erra onde falta informação, não onde falta regra. Um agente com
modelo de linguagem que enxergue os mesmos campos erraria C07 e C08 do
mesmo jeito. O que a D10 precisa trazer é **dado novo**: o histórico da
máquina específica, e não só da família, e a idade da máquina entrando na
decisão (resolveria C11). A linha de base é competitiva nos extremos
(acerta 15 dos 16 casos "seguir" e os 7 "parar") e fraca no meio: acerta
só 3 dos 7 "inspecionar". O agente de D10 precisa empatar nos extremos a
custo quase zero, porque perder ali seria regressão, e ganhar no meio.
Saber disso agora é o que a linha de base vale.

---

**Erro previsível.** Repetir a tabela das sete dimensões sem caso nem
número; concluir que "um LLM resolveria" sem dizer que informação nova ele
teria; tratar 0,83 como fracasso em vez de referência.

**O que transferir para o seu domínio.** Cada propriedade do ambiente
amarrada a um erro observado; a escolha do tipo de agente justificada pela
diferença medida entre a versão com e sem estado interno; e o fecho dizendo
qual **dado** falta, não qual tecnologia usar.
