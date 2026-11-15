"""Subproblema 2 do catálogo: a sequência de consultas para responder uma pergunta.

A formulação vem do plano da D2, seção 9 (catálogo de subproblemas):
Estado: o que já se sabe. Ação: consultar uma fonte. Custo: latência da
consulta. Objetivo: ter todos os dados que a resposta exige.

O sabor do caso: uma fonte costuma entregar VÁRIOS fatos de uma vez. O
caminho ótimo pode ser uma fonte cara que fecha tudo, ou duas baratas que
juntas fecham — e é exatamente esse tipo de escolha que a busca compara.
Uma consulta repetida (todos os fatos já sabidos) é permitida, custa a
latência inteira e não muda o estado: a busca em grafo a descarta.

Os dados são inventados e moram nas constantes do módulo — troque pelos do
seu domínio (lab-03) sem tocar na classe.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Fonte:
    """Uma fonte que pode ser consultada, e o que ela entrega."""

    nome: str
    latencia: float              # custo da consulta (segundos)
    fornece: tuple[str, ...]     # os fatos que a consulta devolve


# A pergunta: "quantos dias de férias ainda tenho, já considerando a venda
# do saldo que pedi?" — quatro fatos, cinco fontes.
FATOS_PEQUENOS: frozenset[str] = frozenset({
    "saldo de dias do funcionário",
    "regra de venda do acordo coletivo",
    "janela mínima exigida pela política",
    "aprovações pendentes do gestor",
})
FONTES_PEQUENAS: tuple[Fonte, ...] = (
    Fonte("RH Digital — meu saldo", 1.2, ("saldo de dias do funcionário",)),
    Fonte("intranet — política de férias", 2.0, ("janela mínima exigida pela política",)),
    Fonte("PDF do acordo coletivo", 6.0, ("regra de venda do acordo coletivo",
                                          "janela mínima exigida pela política")),
    Fonte("sistema do gestor", 3.5, ("aprovações pendentes do gestor",)),
    Fonte("atendimento humano do RH", 15.0, ("saldo de dias do funcionário",
                                             "regra de venda do acordo coletivo",
                                             "janela mínima exigida pela política",
                                             "aprovações pendentes do gestor")),
)

# A pergunta maior: "o pedido do cliente pode ser faturado hoje?" — oito
# fatos, e nenhuma fonte cobre tudo sozinha.
FATOS_MAIORES: frozenset[str] = frozenset({
    "saldo de crédito do cliente",
    "status do cadastro fiscal",
    "preço vigente da tabela",
    "estoque disponível do item",
    "prazo de entrega da transportadora",
    "limite de faturamento sem aprovação",
    "pedidos em aberto do cliente",
    "regra de desconto do canal",
})
FONTES_MAIORES: tuple[Fonte, ...] = (
    Fonte("ERP — ficha do cliente", 0.8, ("saldo de crédito do cliente",
                                          "pedidos em aberto do cliente")),
    Fonte("serviço de cadastro", 1.1, ("status do cadastro fiscal",)),
    Fonte("tabela de preços do dia", 0.9, ("preço vigente da tabela",)),
    Fonte("WMS — saldo do depósito", 1.3, ("estoque disponível do item",)),
    Fonte("portal da transportadora", 4.0, ("prazo de entrega da transportadora",)),
    Fonte("política de crédito em PDF", 7.0, ("limite de faturamento sem aprovação",)),
    Fonte("regras do canal no wiki", 2.5, ("regra de desconto do canal",)),
    Fonte("ERP — consulta completa do cliente", 6.5, ("saldo de crédito do cliente",
                                                      "status do cadastro fiscal",
                                                      "pedidos em aberto do cliente")),
    Fonte("pacote de integração do parceiro", 12.0, ("preço vigente da tabela",
                                                     "estoque disponível do item",
                                                     "regra de desconto do canal")),
    Fonte("atendimento humano comercial", 20.0, ("saldo de crédito do cliente",
                                                 "status do cadastro fiscal",
                                                 "preço vigente da tabela",
                                                 "estoque disponível do item",
                                                 "prazo de entrega da transportadora",
                                                 "limite de faturamento sem aprovação",
                                                 "pedidos em aberto do cliente",
                                                 "regra de desconto do canal")),
    Fonte("dashboards de operação", 3.0, ("estoque disponível do item",
                                          "pedidos em aberto do cliente")),
    Fonte("robô de email do comercial", 9.0, ("limite de faturamento sem aprovação",
                                              "regra de desconto do canal")),
    Fonte("legado COBOL via fila", 8.5, ("saldo de crédito do cliente",
                                         "preço vigente da tabela")),
    Fonte("consulta do jurídico", 14.0, ("status do cadastro fiscal",
                                         "limite de faturamento sem aprovação")),
)


class Consultas:
    """O problema de busca: que fontes consultar, em que ordem.

    O estado é o conjunto de fatos já sabidos, como tupla ordenada —
    estados com os mesmos fatos são o mesmo hash, não importa a ordem
    das consultas.
    """

    def __init__(self, fatos_necessarios: frozenset[str], fontes: tuple[Fonte, ...]):
        self.fatos_necessarios = fatos_necessarios
        self.fontes = fontes
        self._por_nome = {f.nome: f for f in fontes}
        self.estado_inicial: tuple[str, ...] = ()

    def acoes(self, estado: tuple[str, ...]) -> list[str]:
        return [f.nome for f in self.fontes]

    def transicao(self, estado: tuple[str, ...], acao: str) -> tuple[str, ...]:
        # o estado é um CONJUNTO de fatos: consultar fonte que só repete o
        # que já se sabe devolve o MESMO estado — sem o set(), cada consulta
        # redundante criaria um estado novo com o fato duplicado.
        return tuple(sorted(set(estado) | set(self._por_nome[acao].fornece)))

    def objetivo(self, estado: tuple[str, ...]) -> bool:
        return self.fatos_necessarios.issubset(estado)

    def custo(self, estado: tuple[str, ...], acao: str, estado_seguinte: tuple[str, ...]) -> float:
        return self._por_nome[acao].latencia

    def heuristica_admissivel(self, estado: tuple[str, ...]) -> float:
        """A latência da consulta mais barata que ainda entrega um fato faltante.

        Admissível: enquanto faltar fato, é obrigatório consultar PELO MENOS
        uma fonte que ajude — e nenhuma consulta custa menos do que a menor
        latência útil. Ignora quantas consultas ainda virão depois dessa.
        """
        sabidos = set(estado)
        faltantes = self.fatos_necessarios - sabidos
        if not faltantes:
            return 0.0
        uteis = [f.latencia for f in self.fontes
                 if set(f.fornece) & faltantes]
        return min(uteis)

    def heuristica_inadmissivel(self, estado: tuple[str, ...]) -> float:
        """Pior caso por fato: cada fato que falta vai custar a consulta mais lenta.

        NÃO é admissível, e é tentadora por isso: "cada dado que falta é uma
        consulta, e consulta pode demorar o máximo" é o cálculo pessimista
        que se escreve de primeira. Ela ignora que uma consulta única entrega
        vários fatos — e por isso faz a fonte cara que resolve tudo parecer
        o caminho mais promissor: o A* com ela mergulha na consulta lenta e
        devolve caminho mais caro que o ótimo (o lab-05 mede o dano).
        """
        sabidos = set(estado)
        faltantes = len(self.fatos_necessarios - sabidos)
        pior_latencia = max(f.latencia for f in self.fontes)
        return float(faltantes * pior_latencia)


PEQUENA = Consultas(FATOS_PEQUENOS, FONTES_PEQUENAS)
MAIOR = Consultas(FATOS_MAIORES, FONTES_MAIORES)
