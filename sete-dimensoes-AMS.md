# Sete dimensões — gabarito do caminho padrão (AMS)

> **Gabarito do projeto padrão, para conferir.** É a seção "As respostas
> do meu domínio" do `sete-dimensoes-perguntas.md` (`D2-02`) preenchida
> para o AMS, com a evidência de cada classificação e a resposta
> alternativa que também é aceitável. Onde a evidência é um caso da
> reserva (C07, C10), ele está no `casos-de-reserva.csv` do `D2-06`.

## As respostas do meu domínio

**Domínio:** AMS · Assistente de Manutenção Segura

| Dimensão | Minha classificação | Justificativa (uma frase) |
|---|---|---|
| Observabilidade | parcial | A falha intermitente e o histórico da máquina específica mudam a decisão correta e não estão na leitura do instante |
| Número de agentes | único | O técnico decide depois do AMS, mas não compete com ele nem muda de conduta para explorá-lo |
| Determinismo | estocástico | O mesmo tipo de leitura, no mesmo torno, termina em falha num caso e não no outro |
| Episódico ou sequencial | sequencial | Parar para manutenção zera as horas da máquina e muda as leituras seguintes |
| Estático ou dinâmico | semidinâmico | A máquina não muda nos segundos da deliberação, mas a recomendação que chega depois de o técnico começar não vale nada |
| Discreto ou contínuo | contínuo (discretizado) | Temperatura e vibração variam sem degraus; a decisão foi discretizada em três níveis |
| Conhecido ou desconhecido | parcialmente conhecido | As normas estão escritas; a física de falha de cada máquina o agente não sabe de antemão |

## A evidência de cada linha

- **Observabilidade.** O teste da dimensão: existe algo que muda a decisão
  correta e o agente não mede? No AMS, sim. Os casos C07 e C08 da reserva
  têm leitura boa (60 °C, 3,0 mm/s) e a máquina falhou depois. A análise
  exploratória da D1 já avisava: o *AI4I* é anônimo quanto à máquina, e a
  taxa global esconde máquinas cronicamente piores.
- **Número de agentes.** Aceitável também "único, com humano no circuito".
  Viraria multiagente se o técnico passasse a reagir ao AMS (ignorar
  recomendações depois de muitos alarmes falsos, por exemplo). Esse risco
  existe e é tratado na D12, não aqui.
- **Determinismo.** C07 (torno, 60 °C, 3,0 mm/s) falhou; C10 (torno,
  61 °C, 3,3 mm/s) não falhou. O próprio *AI4I* inclui uma falha aleatória
  (RNF, cerca de 0,1% dos registros), sem causa nos sensores. E, quando o
  AMS chamar o modelo de linguagem, haverá uma ação estocástica no meio.
- **Episódico ou sequencial.** Aceitável também "episódico", **desde que
  com a consequência escrita**: tratar cada ordem como independente
  dispensa avaliar trajetória, mas proíbe o estado interno da frota. O
  gabarito escolhe sequencial porque a linha de base usa esse estado, e o
  `carregar_casos` ordena os casos por data por isso.
- **Estático ou dinâmico.** Dinâmico seria exagero: nada muda enquanto o
  agente decide. Estático ignora o prazo real, que é o técnico começar.
- **Discreto ou contínuo.** A discretização é decisão declarada: três
  níveis de decisão e dois limiares na linha de base (vibração acima de
  7,0 mm/s ou temperatura acima de 78 °C → parar). Os casos C11 e C22
  mostram o custo dela: 7,4 e 7,1 mm/s passam do limiar por pouco, e o
  agente para onde bastava inspecionar.
- **Conhecido ou desconhecido.** Trata do que o agente **sabe**, não do
  que ele vê. As regras das NRs são conhecidas e estão escritas. A relação
  entre leitura e falha o agente não conhece e terá de aprender dos dados
  (D5).

**Nota para o professor.** O *AI4I 2020* é sintético, e a documentação
dele publica as regras que geraram as falhas (por exemplo, falha por
dissipação de calor quando a diferença entre temperatura do ar e do
processo fica abaixo de 8,6 K com rotação abaixo de 1 380 rpm). Aluno que
descobrir isso pode argumentar "conhecido". A resposta: as regras são
conhecidas pelos autores do dataset, não pelo agente, e numa planta real
não haveria documento assim. O argumento é bom e vale discutir em aula.

## O que a tabela de consequências obriga no meu projeto

**Se aplicam:**

| Classificação | O que obriga no AMS |
|---|---|
| Parcialmente observável | Estado interno: as falhas por família numa janela de 7 dias (`EstadoDaFrota`), com a janela como política de esquecimento declarada |
| Estocástico | Valor esperado: o custo da falha liberada pesa mais que o da parada desnecessária (secundárias da seção 4 do agent-spec); tempo máximo e nova tentativa na chamada ao modelo |
| Sequencial | Avaliar na ordem cronológica, nunca embaralhar os 30 casos: o estado depende da ordem |
| Semidinâmico | Prazo de resposta: até 10 segundos por ordem (seção 5 do agent-spec) |
| Contínuo | Discretização declarada: três níveis e os dois limiares, com o custo mostrado em C11 e C22 |
| Parcialmente conhecido | Fase de exploração para a física de falha: é a D5, que tenta bater a regra de limiar com aprendizado |

**Não se aplica:**

| Classificação | O que o AMS não precisa ter |
|---|---|
| Multiagente | Protocolo de comunicação e previsão do outro, até a D11 |

## Erro previsível

"Totalmente observável, porque os sensores medem tudo" (o erro que a D1
já tinha desmontado). "Determinístico, porque a mesma leitura dá a mesma
recomendação": determinismo trata do **efeito da ação no ambiente**, e não
da regra do agente. E a etiqueta sem a frase.

## O que transferir para o seu domínio

Para cada classificação, um caso concreto como evidência, e a
consequência escrita. Quando a resposta honesta for "depende", escreva de
quê: é caracterização melhor, não pior.
