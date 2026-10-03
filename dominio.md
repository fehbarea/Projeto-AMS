# dominio.md — AMS · Assistente de Manutenção Segura

> Este arquivo descreve o domínio do projeto em uma página, respondendo seis
> perguntas: o problema, a decisão a automatizar, o usuário, a fonte de dados,
> por que um agente é solução e como saber se está funcionando. Ele chega
> **preenchido com o domínio padrão do pacote** — manutenção industrial, com o
> dataset *AI4I 2020* — e é a página que a disciplina seguinte abre no primeiro
> dia. **Leia-o e entenda cada resposta**: o trabalho das próximas disciplinas
> parte daqui, e você vai precisar explicar cada linha.
> Se você escolheu outro dataset, **substitua as respostas pelas do seu
> domínio**, mantendo as seis perguntas — o `COMO-TROCAR-O-DATASET.pdf` deste
> pacote orienta a troca, e cada resposta vira a sua.

## 1. Qual é o problema?

Em uma planta industrial, máquinas de produção são monitoradas por sensores de
temperatura, rotação, torque e desgaste de ferramenta. Quando uma máquina precisa de
intervenção (preventiva ou corretiva), a equipe de manutenção recebe uma **ordem de
serviço** descrevendo o serviço a fazer. O problema: decidir **se a máquina pode
falhar em breve** — o que muda a prioridade e o procedimento — exige cruzar leituras
de sensores com histórico de falhas, e isso hoje é feito por inspeção e experiência,
sob pressão de tempo.

## 2. Qual decisão será automatizada?

Dada uma ordem de serviço (máquina + leitura atual de sensores + descrição da
intervenção), o sistema decide:

1. o **nível de risco de falha** da máquina (baixo / médio / alto);
2. as **normas regulamentares aplicáveis** à intervenção (NR-10 se houver instalação
   elétrica, NR-12 para máquinas e equipamentos, NR-35 para trabalho em altura);
3. se a intervenção **exige bloqueio e etiquetagem** (LOTO) antes de começar.

A decisão final continua sendo do técnico — o sistema é apoio, não substituto.
O nível de autonomia cresce ao longo do curso (é o que as disciplinas vão acrescentar).

## 3. Quem é o usuário?

Técnico de manutenção industrial com pouco tempo entre uma ordem e outra: precisa de
uma resposta curta, justificada e auditável, não de um painel. O supervisor de
segurança é o usuário secundário: audita as recomendações depois.

## 4. De onde vêm os dados?

- **Sensores e falhas:** dataset público *AI4I 2020 Predictive Maintenance Dataset*
  (UCI, ID 601) — 10.000 registros, 14 colunas, licença CC BY 4.0. Baixado por
  `scripts/baixar-dados.py` com cascata de fallback; proveniência registrada.
- **Normas (corpus documental):** NR-10, NR-12 e NR-35 em PDF do portal gov.br.
  Na D1 apenas baixamos e confirmamos que o corpus existe; a leitura e a busca
  entram nas disciplinas de dados (D7) e RAG (D9).

## 5. Por que um agente é uma boa solução (ou não)?

É um bom caso porque a decisão combina **predição numérica** (risco a partir de
sensores — ML tabular), **conhecimento documental** (normas — recuperação) e
**linguagem natural** (descrição da intervenção — LLM), com justificativa em
português. Um sistema puramente estatístico não lê a descrição; um LLM puro não
estima risco numérico confiável. A composição das partes é o trabalho do agente.
A ressalva honesta: com 10.000 registros públicos, o componente preditivo é
demonstrativo — em planta real, seria treinado no histórico da própria fábrica.

## 6. Como vou saber se está funcionando?

O AMS será avaliado ao longo do curso por etapas: na D1, o critério é a fundação
(dados carregam, validam, e a resposta do modelo vem como objeto `AvaliacaoRisco`
validado — não texto solto). Da D3 em diante, ganha protocolo estatístico; na D7,
um conjunto de avaliação com casos reais; na D12, auditoria completa (o sistema
audita a si mesmo: risco, LGPD, robustez a injeção de prompt).
