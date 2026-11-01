# Catálogo de ações — modelo para preencher

<!--
Este arquivo é para preencher: uma linha por ação que o SEU agente vai
poder executar. As perguntas de cada coluna estão aqui em comentário.

As quatro perguntas que decidem se uma linha está boa:
  - Ação de ESCRITA também? As que alteram o mundo são as que exigem
    cuidado — e são justamente as que mais ficam de fora.
  - COMUNICAR é ação? Avisar, escalar, transferir, pedir confirmação:
    entram com entrada, saída e risco como as outras.
  - "É reversível?" pergunta se o efeito pode ser DESFEITO sem custo
    maior que o da própria ação.
  - O risco diz risco DE QUÊ — "baixo" não é descrição; "paga duas vezes
    uma nota que já estava paga" é.

Este catálogo é, literalmente, a lista de ferramentas que você vai
implementar em D10. Cada linha vira uma função com contrato.
-->

| Ação | Entrada | Saída | É reversível? | Risco se errar |
|---|---|---|---|---|
| Ler os dados dos sensores do equipamento | Identificador do equipamento | Temperatura, rotação, torque e desgaste de ferramenta atuais | Sim — só lê. | Erro de leitura leva a uma decisão de risco errada e possível falha da maquina. |
| Consultar o histórico de falhas | Identificador do equipamento | Número de falhas recentes na janela de tempo| Sim — só lê. | Consulta desatualizada ou com janela errada liberta indevidamente uma máquina instável. |
| Decisão de normas regulamentares aplicáveis | Identificador do equipamento | Norma aplicável | Parcialmente - Decisão de norma errada pode atrapalhar a manutenção |  Risco alto - Norma errada acareta em atraso de manutenção, risco humano e reexecução da ordem |
| Ler a ordem de serviço | Identificador do chamado | Descrição do serviço a fazer | Sim - só lê | Leitura de chamado errado pode acarretar em rexecuções, priorização errada |
| Redigir o nível de risco de falha| Descrição do serviço a fazer, Dados dos sensores, histórico e normas aplicáveis | Avaliação do nível de risco | Parcialmente - Pode acarretar em erro humano e falha da máquina ou, apenas, na reavaliação. | Risco alto - Desgaste na confiança no sistema, pode causar vies na decisão humana e falha da máquina. |
| Registrar necessidade de bloqueio de LOTO | Dados dos sensores, histórico, nível de risco | Ordem de travamento para máquina| Parcialmente - Pode acarretar em erro humano, parada desnecessária da máquina, falha da máquina ou, apenas, na reavaliação. | Risco alto - Interromper operações desnecessariamente causando parada de produção ou não ativar o bloqueio quando necessário arrisca vidas. |
| Resposta com recomendações |  Avaliação do nível de risco, ordem de travamento para máquina, Norma aplicável | Chamado Respondido com recomendaçõe | Sim - Responde o chamado novamente | Não responder leva a demora na manutenção


**Quem executa cada ação:** As leituras e resposta com recomendaçõe são realiadas pelo agente sozinho, porém a decisão de loto, normas aplicáveis e risco são avaliadas por humanos antes de intervenção no mundo real.

**O que o agente JAMAIS executa sozinho:** Bloqueio da máquina, pois é de alto risco para a produção.
