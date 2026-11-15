# Catálogo de ações — gabarito do caminho padrão (AMS)

> **Gabarito do projeto padrão, para conferir.** É o
> `catalogo-de-acoes-modelo.md` do `D2-07` preenchido para o AMS. Vai para
> a seção 6 do `agent-spec.md` e é, literalmente, a lista de ferramentas
> que a D10 implementa.

| Ação | Entrada | Saída | É reversível? | Risco se errar |
|---|---|---|---|---|
| Consultar a leitura atual da máquina | Identificador da máquina | Temperatura, vibração, horas desde a última manutenção, hora da leitura | Sim — só lê | Leitura defasada: o agente decide sobre o estado de horas atrás e libera uma máquina que já esquentou |
| Consultar o histórico de falhas da família | Família da máquina e janela em dias | Número de falhas observadas na janela | Sim — só lê | Janela curta perde a falha intermitente (C07, C08); janela longa põe a família inteira em inspeção sem motivo (C10) |
| Consultar as normas aplicáveis à intervenção | Descrição da intervenção | NRs aplicáveis, com o trecho que justifica | Sim — só lê | Norma omitida: o técnico entra sem o bloqueio que a NR-10 ou a NR-12 exige |
| Registrar a recomendação na ordem de serviço | Ordem, decisão e justificativa | Registro com data e autor "AMS" | Parcialmente — corrige-se com novo registro, mas o original fica, e deve ficar, para auditoria | Recomendação errada gravada orienta o técnico e contamina a auditoria do supervisor |
| Marcar a exigência de bloqueio e etiquetagem | Ordem e normas aplicáveis | Campo "exige bloqueio" preenchido no checklist | Parcialmente — o campo se corrige; a intervenção começada sem bloqueio, não | Marcar "não exige" por engano expõe o técnico a energia perigosa: risco à vida |
| Recomendar a parada da máquina ao técnico | Máquina, motivo e leitura que justifica | Aviso ao técnico, com a justificativa | Não — a produção perdida na parada não volta | Parada desnecessária custa produção (C11, C22) e gasta a confiança do técnico nos próximos avisos |
| Pedir confirmação ao técnico | Pergunta objetiva, com as opções | Resposta do técnico | Sim | Pergunta demais atrasa a ordem e ensina o técnico a responder sem ler |
| Escalar ao supervisor de segurança | Ordem, motivo e o que já foi verificado | Chamado aberto para o supervisor | Sim — o chamado se cancela | Escalar demais cansa o supervisor; escalar de menos deixa a auditoria sem os casos que importam |

**Quem executa cada ação:** as três consultas, o agente sozinho. Registrar
a recomendação, o agente sozinho, porque o registro é auditável e não
muda a máquina. Marcar o bloqueio: o agente pode marcar "exige" sozinho;
marcar "não exige" só com confirmação do técnico. Recomendar parada,
pedir confirmação e escalar: o agente sozinho, porque são comunicações e a
decisão continua com o humano. Aplicar ou retirar o bloqueio físico e
liberar a máquina para operar: só o humano, e por isso essas ações nem
entram no catálogo.

**O que o agente JAMAIS executa sozinho:** dispensar o bloqueio e
etiquetagem de uma intervenção em que NR-10 ou NR-12 se aplica, e liberar
uma máquina para voltar a operar.

## Os comentários, linha a linha

- **Três ações de leitura, duas de escrita, três de comunicação.** As de
  escrita e as de comunicação são as que mais ficam de fora em catálogo de
  primeira viagem, e são as que alteram o mundo.
- **"Marcar a exigência de bloqueio" é a ação de maior risco do
  catálogo**, embora pareça burocrática: é um campo de formulário. O risco
  não está no tamanho da ação, está no que a pessoa faz em seguida
  confiando nela.
- **A reversibilidade da parada é "não"** mesmo que a máquina volte a
  operar depois: o que se pergunta é se o efeito pode ser desfeito sem
  custo maior que o da própria ação, e a hora parada não volta.
- **Cada risco cita um caso da reserva quando existe.** C07, C08, C10,
  C11 e C22 são os erros da linha de base do lab-06, e cada um é o risco
  de uma ação deste catálogo acontecendo de verdade.

## Erro previsível

Catálogo só com consultas; coluna de reversibilidade em branco; risco
escrito como "baixo" ou "médio" em vez de risco **de quê**, **para quem**.
E "decidir o nível de risco" listado como ação: decidir é o que o agente
faz por dentro; as ações são o que ele faz no mundo.

## O que transferir para o seu domínio

Procure a ação que parece inofensiva e na qual alguém vai confiar sem
conferir: costuma ser a de maior risco. E separe o que o agente faz
sozinho, o que faz com confirmação e o que fica só com o humano.
