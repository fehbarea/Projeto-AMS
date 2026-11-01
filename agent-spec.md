# agent-spec.md — modelo do meu agente

<!--
Este arquivo é para preencher, não para ler e devolver. As perguntas de cada
seção estão em comentário como este: elas não aparecem na pré-visualização,
aparecem no editor. Responda ABAIXO de cada seção, apagando nada delas.

As seções que ainda não foram vistas em aula ficam de pé, com a linha
"quando se preenche" dizendo o encontro em que isso acontece. O documento
cresce a cada laboratório — o de hoje é o primeiro.

Preencha com exemplos concretos do SEU domínio. Uma linha que funcionaria
para qualquer empresa é uma linha genérica — o exemplo do seu segmento
(agente-spec-exemplo.pdf, no mesmo pacote) mostra o contraste.
-->

**Domínio:**  AMS · Assistente de Manutenção Segura
**Autor(a):** Felipe Alves Barea· **Última revisão:** 10/10/2026

---

## 1. PEAS

<!-- Perguntas que guiam o preenchimento:
  - Performance: o que conta como sucesso, em uma fórmula? Sobre o quê se
    conta, sobre qual conjunto, quanto é sucesso? Qual termo impede a
    trapaça mais óbvia (fechar rápido sem resolver)?
  - Environment: onde o agente opera? O que existe lá — sistemas, pessoas,
    documentos, ruído? Cite elementos concretos.
  - Actuators: o que o agente pode FAZER? Inclua comunicar e escalar:
    informar a decisão é uma ação, e passar adiante também é.
  - Sensors: o que o agente consegue PERCEBER? Só o que ele enxerga existe
    para ele.
  Um PEAS que menciona tecnologia de solução (banco vetorial, nome de modelo)
  está descrevendo a solução — o PEAS descreve o problema.
-->
**Quando se preenche:** no Laboratório 01, hoje. Refinado na Atividade Orientada.

**Performance:**

A proporção de chamados de manutenção em que a recomendação do agente corresponde exatamente à decisão ideal do especialista humano, dividida pelo total de incidentes avaliados. O sucesso é atingido com a média de acertos acima de 85% e uma taxa de erro de 0% para classifição de risco alto ou erronemanete recomendar bloqueio. Termo contra a trapaça: o agente não pode recomendar o bloqueio em 100% dos casos para zerar o risco e elevar o sucesso, pois isso travaria a produção indevidamente.

**Environment:**

Chamados de ordem de serviço, máquinas que precisam de intervenção, equipe de manutenção e supervisor.

**Actuators:**

Classificar o risco de falha da máquina, recomendar as normas aplicáceis, recomendar bloqueio e etiquetagem, emitir parecer curto, justificadop e auditável.

**Sensors:**

Descrição da intervenção, leitura dos sensores, dados da máquina, dataset público *AI4I 2020 Predictive Maintenance Dataset*, Normas NR-10, NR-12 e NR-35.

---

## 2. O ambiente em sete dimensões

<!--
Perguntas que guiam o preenchimento (uma por dimensão):
  - Observabilidade: existe algo que muda a decisão e o agente não mede?
  - Número de agentes: existe alguém cujas ações mudam o seu resultado?
    Um humano que reage ao agente conta.
  - Determinismo: a mesma ação no mesmo estado dá sempre o mesmo efeito?
  - Episódico ou sequencial: a decisão de agora afeta as decisões seguintes?87c xg
  - Estático ou dinâmico: o ambiente muda enquanto o agente delibera?
  - Discreto ou contínuo: estados e ações são contáveis?
  - Conhecido ou desconhecido: o agente sabe de antemão as regras? (Trata do
    que ele SABE, não do que ele VÊ.)
  Cada classificação vem com uma frase de justificativa — a etiqueta sozinha
  não vale nada.
-->
**Quando se preenche:**

| Dimensão | Minha classificação | Justificativa (uma frase) |
|---|---|---|
| Observabilidade | Parcial | Falta de histórico de defeitos e manutenções anteriores |
| Número de agentes | único | O agente decide sem a influências externa |
| Determinismo | Estocástico | Utiliza IA variando o resultado |
| Episódico ou sequencial | Episódico | O resultado do chamdo atual não afeta o próximo |
| Estático ou dinâmico | Semidinâmico | O estado não altera, mas a demora no parecer pode causar delay na manutenção e falha na máquina |
| Discreto ou contínuo | Contínuo | Os valores dos sensores variam de forma contínua |
| Conhecido ou desconhecido | Conhecido | As regras estão documentadas em arquivos |

---

## 3. Tipo de agente pretendido

<!--
Perguntas que guiam o preenchimento:
  - O tipo mais simples que resolve: reativo simples, baseado em modelo,
    baseado em objetivos, baseado em utilidade, ou um deles com aprendizagem?
  - A caracterização do ambiente (seção 2) é que decide — parcialmente
    observável elimina o reativo simples.
  - Justifique com a dimensão do ambiente que obriga a escolha.
-->
**Quando se preenche:**

O agente baseado em modelo é o mais simples que resolve o problema do AMS, pois ele é parcialmnte observável quanto ao histórico de manutenções, pois, o agente não recebe o histórico completo da máquina em cada chamado, ele precisa de uma memória para acumular ocorrências e julgar a frequência de falhas.

---

## 4. Medida de desempenho

<!--
Perguntas que guiam o preenchimento:
  - A fórmula do campo Performance, agora em definição operacional: como se
    calcula, passo a passo, sem ambiguidade?
  - Métrica primária e duas secundárias. As secundárias pegam o que a
    primária deixa passar (custo, latência, reabertura).
  - O conjunto de casos: de onde vêm, quantos são, de que período.
  - O limiar de sucesso e o valor de hoje.
-->
**Quando se preenche:**

*Primária:* Número de chamados em que a recomendação final do agente é igual ao rótulo esperado pelo especialista humano, dividido pelo total de casos analisados no último semestre, deve ser maior que 85%.

*Segundária:* Tempo para retorno do chamado após abertura não superior a 5 minutos.

*Segundária:* Máquinas que falham antes de manutenção por erro na avaliação dos sensores e, consequentemente, classicação de risco como baixo, dividido pelo total de casos analisados no último semestre, deve ser menor que 1%.
---

## 5. Restrições

<!--
Perguntas que guiam o preenchimento:
  - Latência aceitável: a partir de quantos segundos a resposta perde valor?
  - Custo aceitável: quanto pode custar cada resolução?
  - O que o agente jamais pode fazer: a ação irreversível que ele não executa
    sozinho. Esta linha vira política em D12.
  - A troca que você aceita: quanto de qualidade por quanto de custo?
    Um exemplo numérico vale mais que a fórmula.
-->

**Quando se preenche:** na Atividade Orientada.

*Latência:* Limite de 5 minutos para resposta com parecer, a demora na resposta dos chamados com risco alto de falha pode afetar a produção.
*Custo:* até R$ 0,80 por chamado.
*O que o agente jamais faz sozinho:* O agente jamais pode acionar e confirmar o bloqueio (LOTO) diretamente no maquinário físico ou no sistema de chão de fábrica.
*Troca aceita*: Redução de 5 pontos percentuais no desempenho primário por agravar o parecer, desde que mantenha 0% de erro em falsas necesidade de bloqueio e reduza o custo por chamado em 40%.

---

## 6. Catálogo de ações

<!--
Perguntas que guiam o preenchimento:
  - Para cada ação: nome, entrada, saída, é reversível?, qual o risco se
    errar? As quatro colunas são obrigatórias — "baixo" não é descrição de
    risco.
  - Ações de leitura E de escrita: as que alteram o mundo são as que exigem
    cuidado, e são justamente as que mais ficam de fora.
  - Este catálogo é, literalmente, a lista de ferramentas que você vai
    implementar em D10.
-->
**Quando se preenche:**

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

---

## 7. Formulação por busca

<!--
Perguntas que guiam o preenchimento:
  - Qual fatia do problema é um espaço de estados? (Nem toda fatia é — e
    reconhecer a que não é vale tanto quanto formular a que é.)
  - Os cinco componentes: estado inicial, ações, modelo de transição, teste
    de objetivo, custo de caminho. Comece pelo teste de objetivo.
  - O estado descreve a SITUAÇÃO, não a história de como se chegou nela.
-->
**Quando se preenche:**



class TriagemAMS:

    def __init__(self, etapas: tuple[EtapaAMS, ...]):
        self.etapas = etapas
        self._por_nome = {e.nome: e for e in etapas}
        self.estado_inicial: tuple[tuple[str, ...], tuple[str, ...]] = ((), ())

    def acoes(self, estado: tuple[tuple[str, ...], tuple[str, ...]]) -> list[str]:
        feitas, _ = estado
        categorias_feitas = {self._por_nome[f].categoria for f in feitas}
        
        ativas = []
        for etapa in self.etapas:
            if etapa.nome in feitas:
                continue
            
            if etapa.categoria in ("RISCO", "NORMA"):
                ativas.append(etapa.nome)
            elif etapa.categoria == "DECISAO_LOTO":
                if "RISCO" in categorias_feitas and "NORMA" in categorias_feitas:
                    ativas.append(etapa.nome)
            elif etapa.categoria == "PARECER":
                if "DECISAO_LOTO" in categorias_feitas:
                    ativas.append(etapa.nome)
                    
        return ativas

    def transicao(
        self, estado: tuple[tuple[str, ...], tuple[str, ...]], acao: str
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        feitas, valores = estado
        etapa = self._por_nome[acao]
        
        novas_feitas = tuple(sorted((*feitas, acao)))
        novos_valores = tuple(sorted((*valores, etapa.resultado_fixo)))
        
        return novas_feitas, novos_valores

    def objetivo(self, estado: tuple[tuple[str, ...], tuple[str, ...]]) -> bool:
        feitas, _ = estado
        categorias_feitas = {self._por_nome[f].categoria for f in feitas}
        return {"RISCO", "NORMA", "DECISAO_LOTO", "PARECER"}.issubset(categorias_feitas)

    def custo(
        self,
        estado: tuple[tuple[str, ...], tuple[str, ...]],
        acao: str,
        estado_seguinte: tuple[tuple[str, ...], tuple[str, ...]],
    ) -> float:
        feitas, _ = estado
        etapa = self._por_nome[acao]
        
        risco_atual = "Pendente"
        for f in feitas:
            if self._por_nome[f].categoria == "RISCO":
                risco_atual = self._por_nome[f].resultado_fixo
                
        if etapa.categoria == "DECISAO_LOTO":
            if acao == "RecomendarBloqueio" and risco_atual == "Baixo":
                return 250.0 
            if acao == "DispensarBloqueio" and risco_atual in ("Alto", "Médio"):
                return 1000.0
        
        return etapa.custo_base
    
    def heuristica_admissivel(
        self, estado: tuple[tuple[str, ...], tuple[str, ...]]
    ) -> float:

        feitas, _ = estado
        categorias_feitas = {self._por_nome[f].categoria for f in feitas}
        essenciais = {"RISCO", "NORMA", "DECISAO_LOTO", "PARECER"}
        faltam = essenciais - categorias_feitas
        
        if not faltam:
            return 0.0
            
        custo_otimista = 0.0
        for cat in faltam:
            etapas_cat = [e for e in self.etapas if e.categoria == cat]
            if etapas_cat:
                custo_otimista += min(e.custo_base for e in etapas_cat)
                
        return custo_otimista

    def heuristica_inadmissivel(
        self, estado: tuple[tuple[str, ...], tuple[str, ...]]
    ) -> float:

        feitas, _ = estado
        categorias_feitas = {self._por_nome[f].categoria for f in feitas}
        essenciais = {"RISCO", "NORMA", "DECISAO_LOTO", "PARECER"}
        faltam = essenciais - categorias_feitas

        ja_feito = sum(self._por_nome[feita].custo_base for feita in feitas)
        nao_feito = sum(self._por_nome[etapa.nome].custo_base for etapa in self.etapas if etapa.categoria in faltam)
        complementares = 0.0
        
        for etapa in self.etapas:
            if etapa.categoria == "COMPLEMENTAR" and etapa.nome not in feitas:
                complementares += etapa.custo_base *2
            
        return (3.0 * nao_feito - 2.0 * ja_feito) + complementares 