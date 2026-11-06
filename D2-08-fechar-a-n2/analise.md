# Análise — modelo de uma página

<!--
Item 5 da N2 — a única escrita genuinamente nova, e o tema é fixo:
quais propriedades do ambiente tornam o problema difícil, e que tipo de
agente o problema realmente exige. Um parágrafo por pergunta abaixo; a
meta é UMA página. O que separa o adequado do excelente é a EVIDÊNCIA:
citar o número que apareceu, o caso que errou, a linha da tabela — algo
que só quem rodou saberia. Responda NOS COLCHETES.
-->

## O que torna o problema difícil

[Duas ou três propriedades do ambiente (da caracterização do lab-02), cada
uma amarrada a um comportamento observado: onde a linha de base errou e por quê
(a lista do `medir.py`), onde a busca gastou nós, o que a heurística
precisava saber e não sabia. Exemplo da forma: "a observabilidade parcial
não é rótulo aqui: a linha de base perdeu os casos C07 e C08 porque a falha
intermitente não aparece nas leituras — a informação que decide não está
na percepção do instante."]

[Observabilidade parcial é responsável pelos erros nos casos C20, C23 e C26, pois as leituras dos sensores não revelam a instabilidade anteriores, a baseline usou uma regra matemática de histórico, mas falhou por rigidez, exigindo duas falhas e ignorando ocorrências únicas graves que poderiam ser o suficiente. Isso deixa claro que algo tão simples não seria capaz de dar uma parecer assertivo, o agente deve ter informações qualitativas e quantitativas.  
O agente tem valores continuos, a natureza contínua do dados do sensores quebra a lógica fixa no caso C28, que foi classificado indevidamente como manutencao_padrao, o que é um falso negativo grave no cenário, porque o sensor leu 49.9, batendo na trave do limiar de 50.0 para bloqueio.
Já o erro do C29 é correlacionado com a observabilidade parcial e a natureza contínua, já que o máquina falhou há 18 dias, estourando a janela de 15 dias, isso demonstra uma vunerabilidade, dado que o valor poderia ser 16, por ter passado 1 segundo da meia noite, nesse cenário o agente determinístico teria falhado também, pois faria sentido essa ultima falha ser levada em consideração para o parecer.
Isso leva ao Estocástico, demostrando que o agente precisa de uma IA para conseguir avaliar o contexto global antes de emitir um parecer, além de guardar algumas informações das antigas execuções, demosntrando a sua observabilidade parcial.]

## Que tipo de agente o problema realmente exige

[Dado o parágrafo anterior: reativo simples basta? Precisa de estado
interno (e de quanto histórico)? Precisa de objetivos e busca? O que a
escolha OBRIGA o projeto a ter — e o que ela DISPENSA. Se você apagou a
segunda condição da linha de base porque o seu ambiente é totalmente
observável, este é o lugar da justificativa — a escolha do tipo é parte do
que a rubrica avalia.]

[Com os problemas apresentados no tópico anterior fica evidente os problemas de um reativo simples aplicado a esse contexto, pois evidencia o aprendizado do E2 "sem histórico, não percebe tendência nem repetição", o que ficou evidente no C29. Diante disso, o mínimo necessário para esse agente é o Agente Baseado em Modelo, pois é preciso um agente capaz de interpretar a nuance e a semântica das descrições textuais das ordens de serviço, manter estados internos e precisa balancear as decisões tomadas com o custo acarretados, Dado isso, uma LLM se mostra necessária, para avaliar o que já foi executado, entendo o parecer dado, o risco, os dados dos sensores, qual foi o último problema apresentado e correlacionar isso com o chamado atual, assim identicando padrões e tomando decisões baseadas não só em limiares e pesos, mas no contexto inserido.
Os outros tipos de agentes mais "caros" se tornam desnecesário para o caso, pois o baseado em objetivo planejaria passos que não são necessários aqui, o de utilidade traria uma complexidade muito alta, pois os existem limiares documentados dos sensores e falhas, o que o agente precisa é apenas cruzar essas informações junto com a descrição e o histórico. Por fim, o agente com aprendizado poderia ser implementado, porém não é previsto um retorno do usuário para esse domínio e poderia esbarrar em risco relacionados as limiares dos sensores que não devem ser alterados.
]

## O que isto muda no projeto (fecho, três ou quatro linhas)

[A consequência de projeto da análise: o que a D10 precisa trazer para o
seu agente com modelo funcionar melhor que a linha de base — novo sensor,
novo dado, verificador externo? Onde a linha de base é competitiva, e por
quê isso é informação valiosa e não fracasso.]

[Para o D10, o agente precisará receber as descrições em texto livre dos chamados na máquina, e não apenas o número de falhas, o dataset público *AI4I 2020 Predictive Maintenance Dataset* e todo o histórico do que já foi executado, porém, a linha de base pode ser usada para certos casos, pois com 83,3% de acerto a um custo computacional e latência próximos de zero, ela pode atuar como um filtro inicial.]
