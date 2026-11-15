# agent-spec.md — gabarito do caminho padrão (AMS)

> **Gabarito do projeto padrão, para conferir.** É o `agent-spec-modelo.md`
> do `D2-01` preenchido para o AMS, seção por seção, na mesma ordem. Cada
> seção tem a resposta, o **erro previsível** (o que o professor procura) e
> **o que transferir para o seu domínio**. Você pode discordar de qualquer
> linha, desde que diga por quê.

**Domínio:** AMS · Assistente de Manutenção Segura (manutenção industrial)
**Autor(a):** gabarito da coordenação

---

## 1. PEAS

**Quando se preenche:** no Laboratório 01. Refinado na Atividade Orientada.

**Performance:** acerto da recomendação — ordens de serviço em que a
recomendação do AMS coincide com a decisão correta rotulada, divididas
pelo total de ordens do conjunto. Conjunto: os 30 casos rotulados da
reserva (`D2-06`). Sucesso: 27 de 30 ou mais (0,90), **com nenhuma máquina
que falhou depois liberada para operar**. Esse segundo termo é o que
impede a trapaça óbvia: recomendar sempre "seguir operando" acerta mais da
metade e deixa passar todas as falhas.

**Environment:** a planta industrial com tornos, prensas, compressores e
robôs; o painel de sensores de cada máquina (temperatura, vibração, horas
desde a última manutenção); as ordens de serviço abertas; o histórico de
falhas da frota; as normas NR-10, NR-12 e NR-35; o técnico de manutenção,
com pouco tempo entre uma ordem e outra; o supervisor de segurança, que
audita depois. Ruído: leitura de sensor defasada, descrição da ordem
escrita às pressas.

**Actuators:** recomendar uma das três decisões (seguir operando,
inspecionar antes de operar, parar para manutenção) com justificativa;
indicar as normas aplicáveis; marcar se a intervenção exige bloqueio e
etiquetagem; registrar a recomendação na ordem de serviço; escalar ao
supervisor de segurança; pedir uma confirmação ao técnico.

**Sensors:** a leitura atual dos sensores da máquina; o tipo e a idade da
máquina; a descrição da intervenção na ordem; os desfechos que o ambiente
revela depois (a máquina falhou ou não). O que **não** chega ao AMS: o
estado interno da peça, o histórico da máquina específica antes da
implantação, a condição da equipe no dia.

**Erro previsível.** Performance escrita como intenção ("prever falhas
com precisão", "aumentar a segurança"). E o PEAS que descreve a solução:
"modelo de ML", "RAG sobre as NRs", "Gemini" são tecnologia, não problema.

**O que transferir para o seu domínio.** A medida tem dois termos: o que
conta como acerto e o que proíbe o jeito barato de acertar. Escalar e
registrar são atuadores; o técnico e o supervisor fazem parte do ambiente.

---

## 2. O ambiente em sete dimensões

**Quando se preenche:** no Laboratório 02, no encontro 2.

| Dimensão | Classificação | Justificativa |
|---|---|---|
| Observabilidade | Parcialmente observável | A falha intermitente e o histórico da máquina específica não aparecem na leitura do instante |
| Número de agentes | Agente único | O técnico decide depois do AMS, mas não compete com ele nem muda de conduta para explorá-lo |
| Determinismo | Estocástico | Duas leituras quase iguais do mesmo torno (C07 e C10 da reserva) têm desfechos opostos |
| Episódico ou sequencial | Sequencial | Parar para manutenção zera as horas da máquina e muda as leituras seguintes; o estado do agente se acumula caso a caso |
| Estático ou dinâmico | Semidinâmico | A máquina não muda nos segundos da deliberação, mas a resposta que chega depois de o técnico começar não vale nada |
| Discreto ou contínuo | Contínuo na percepção, discreto na ação | Temperatura e vibração variam sem degraus; a decisão tem três valores |
| Conhecido ou desconhecido | Parcialmente conhecido | As normas estão escritas; a física de falha de cada máquina o agente não sabe de antemão |

O detalhamento, com as consequências de projeto, está em
`sete-dimensoes-AMS.pdf`.

---

## 3. Tipo de agente pretendido

**Quando se preenche:** no encontro 2, manhã.

**Baseado em modelo** (reativo com estado interno). A observabilidade
parcial elimina o reativo simples: a falha intermitente não aparece na
leitura, então o agente precisa guardar o que já observou da frota. No
AMS, o estado interno é a contagem de falhas por família de máquina numa
janela de 7 dias (`EstadoDaFrota`, no `D2-06`).

O lab-06 confirma com número: a versão só reativa acerta 23 de 30 e libera
4 máquinas que falharam; com a condição de estado interno, 25 de 30 e
libera 2.

Não é, por enquanto, baseado em utilidade, embora o problema peça isso: o
custo de liberar uma máquina que vai falhar é muito maior que o de uma
parada desnecessária, e só um agente que compara custos esperados trata a
assimetria direito (é para onde D3 e D5 levam). A fatia de busca da seção
7 é baseada em objetivos, mas é uma fatia, não o agente inteiro.

**Erro previsível.** Escolher "baseado em utilidade" ou "com aprendizagem"
por soar mais sofisticado, sem dizer qual dimensão do ambiente obriga. O
critério é o tipo **mais simples** que resolve.

**O que transferir para o seu domínio.** Uma dimensão justifica a escolha
(aqui, observabilidade), e o estado interno precisa de política de
esquecimento: guardar o quê, por quanto tempo.

---

## 4. Medida de desempenho

**Quando se preenche:** fórmula no Laboratório 01; definição operacional
completa na Atividade Orientada.

**Primária — acerto da recomendação.** Como se calcula: para cada um dos
30 casos, compara-se a decisão do agente com a coluna `acao_correta`;
conta-se quantas coincidem e divide-se por 30. Conjunto: os 30 casos
rotulados da reserva do `D2-06`, de março, com 16 casos "seguir", 7
"inspecionar" e 7 "parar". Sucesso: 0,90 ou mais.

**Secundária 1 — falhas liberadas.** Casos em que a máquina falhou depois
(`falhou_depois = 1`) e o agente recomendou seguir operando, sobre os 11
casos que falharam. Meta: 0 de 11. É o termo contra a trapaça, e pega o
que a primária deixa passar: a primária conta todo erro igual, e este é o
erro que machuca gente.

**Secundária 2 — paradas desnecessárias.** Recomendações de parada em
casos cujo rótulo não era parar, sobre o total de paradas recomendadas.
Meta: até 20%. Impede o jeito barato de zerar a secundária 1, que é parar
tudo.

**Valor de hoje.** Na Atividade Orientada ainda não há agente, e o valor
de referência é o da política que não faz nada, calculável numa planilha:
**recomendar sempre "seguir operando"** acerta 16 de 30 (0,53) e libera
as 11 falhas. Parar tudo acerta 7 de 30 (0,23) com 23 paradas
desnecessárias. Os dois extremos mostram por que uma métrica só não basta.
No encontro 4, a linha de base do lab-06 passa a ser o valor de hoje:
**25 de 30 (0,83), 2 falhas liberadas de 11, 2 paradas desnecessárias de
9 (22%)**. Atualizar esta linha é o "o que mudou" que o item 1 da N2 pede.

**Por que não o AI4I.** O *AI4I 2020* da D1 tem o desfecho (falhou ou
não), mas não tem a decisão correta rotulada; sem a decisão rotulada não
há acerto a calcular. Na D1 ele serviu à análise exploratória: a falha é
rara, perto de 3,4%, e "nunca falha" acerta cerca de 96,6%. É o mesmo
aviso da secundária 1, em outra escala.

**Erro previsível.** Medida sem conjunto ("acurácia do modelo"), ou sem
valor de hoje. E a acurácia sozinha, sem o termo das falhas liberadas.

**O que transferir para o seu domínio.** As três perguntas (sobre o quê,
sobre qual conjunto, quanto é sucesso), mais a política trivial como
primeiro valor de hoje: ela sempre se calcula, mesmo antes de existir
agente.

---

## 5. Restrições

**Quando se preenche:** na Atividade Orientada.

Os números abaixo são **decisões de projeto**, não medições.

- **Latência:** até 10 segundos por ordem. O técnico lê a recomendação
  entre uma ordem e outra; depois de 30 segundos ele começa sem ler, e a
  recomendação perde o valor.
- **Custo:** zero na camada gratuita, que é a regra do curso. Se o projeto
  migrar para plano pago, teto de R$ 0,05 por ordem.
- **O que o agente jamais faz sozinho:** declarar que uma intervenção
  dispensa bloqueio e etiquetagem quando NR-10 ou NR-12 se aplica (na
  dúvida, o AMS marca "exige bloqueio"); liberar uma máquina para voltar a
  operar; fechar ou alterar a ordem de serviço sem o técnico. Estas linhas
  viram política na D12.
- **Troca aceita:** até 3 paradas desnecessárias a mais, em 30 ordens,
  para evitar 1 falha liberada. Exemplo: um agente com 27 de 30 acertos,
  nenhuma falha liberada e 4 paradas desnecessárias vale mais que um com
  28 de 30 e uma falha liberada. Uma parada desnecessária custa cerca de
  uma hora de máquina parada; uma falha em operação custa um turno e expõe
  quem está perto da máquina.

**Erro previsível.** "Resposta rápida" e "baixo custo" sem número. E a
troca escrita como fórmula abstrata, sem o exemplo.

**O que transferir para o seu domínio.** A linha do "jamais" é a ação
irreversível de risco alto; a troca se escreve comparando dois agentes
concretos.

---

## 6. Catálogo de ações

**Quando se preenche:** na Atividade Orientada.

A tabela completa, com os comentários, está em `catalogo-de-acoes-AMS.pdf`.
Resumo das oito ações:

| Ação | Tipo |
|---|---|
| Consultar a leitura atual da máquina | leitura |
| Consultar o histórico de falhas da família | leitura |
| Consultar as normas aplicáveis à intervenção | leitura |
| Registrar a recomendação na ordem de serviço | escrita |
| Marcar a exigência de bloqueio e etiquetagem | escrita |
| Recomendar a parada da máquina ao técnico | comunicação |
| Pedir confirmação ao técnico | comunicação |
| Escalar ao supervisor de segurança | comunicação |

---

## 7. Formulação por busca

**Quando se preenche:** no Laboratório 03, no encontro 2.

A fatia do problema que é busca: **em que ordem conferir os itens de
liberação de uma ordem de serviço**, antes de o técnico começar. É o
subproblema 3 do catálogo (roteiro de conformidade) com os dados do AMS:
nove itens de conferência, cinco pendências possíveis. O código está em
`ams_conformidade.py`, e passa nas seis verificações do
`verificar-formulacao.py`.

| Componente | No AMS |
|---|---|
| Estado inicial | Nenhum item conferido, nenhuma pendência aberta |
| Ações | Conferir um item ainda não conferido, ou resolver uma pendência aberta |
| Transição | Conferir soma o item aos conferidos e abre as pendências dele (conferir o diagrama elétrico, por exemplo, abre "atualizar o diagrama"); resolver tira a pendência das abertas |
| Teste de objetivo | Os nove itens conferidos e nenhuma pendência aberta: só assim a ordem é liberada |
| Custo | Minutos de trabalho; conferir um item com pendência em aberto custa o dobro, porque a permissão de trabalho tem de ser revista |

O estado é o par (itens conferidos, pendências abertas), como conjuntos:
duas ordens diferentes de conferência que chegam à mesma situação são o
mesmo estado.

O que **não** é busca no AMS: a recomendação de risco é regra (é a linha
de base do lab-06), e a sequência física do bloqueio (desenergizar,
bloquear, testar ausência de tensão) tem ordem imposta pela norma. Ordem
imposta é procedimento, não busca. Os itens desta formulação são
conferências (documento, inspeção, validade), cuja ordem é livre, e é por
isso que a ordem muda o custo.

**Erro previsível.** Formular a recomendação de risco como busca (não há
sequência de ações, é uma decisão por caso). E o estado que guarda a lista
na ordem em que os itens foram conferidos, que o teste 6 do verificador
acusa.

**O que transferir para o seu domínio.** Procure a fatia em que a **ordem
muda o custo**; reconhecer o que não é busca vale tanto quanto formular o
que é.
