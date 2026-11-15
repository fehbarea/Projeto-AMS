"""Motor de busca compartilhado da D2 — lab-03 a lab-06.

Para que serve
--------------
Os laboratórios de busca da disciplina (formular como busca, busca não
informada, busca informada) rodam sobre este módulo. Ele conhece ALGORITMOS;
não conhece problema nenhum. Um problema é qualquer classe que cumpra o
protocolo `Problema` — o catálogo em `problemas/` traz três prontos.

Convenções que os laboratórios medem (não troque sem avisar a coordenação):

  - `nos_expandidos` conta cada nó RETIRADO DA FRONTEIRA — incluindo a
    retirada do nó objetivo e as retiradas de nós repetidos, descartados
    pelo conjunto de explorados. É a definição literal usada nos enunciados.
  - `nos_gerados` conta cada `No` CRIADO, inclusive repetidos.
  - Todas as buscas são busca em GRAFO: um conjunto de explorados impede
    reexpandir estados. O teste de objetivo acontece na retirada da
    fronteira (necessário para custo uniforme e A* serem ótimos).
  - Empates na fronteira de prioridade resolvem-se por ordem de criação
    (o contador do heap), para o resultado ser determinístico.

Depende só da biblioteca padrão e roda em Python 3.10.
"""

from __future__ import annotations

import heapq
import itertools
import time
from collections import deque
from dataclasses import dataclass
from typing import Callable, Hashable, Protocol

Estado = Hashable
Acao = Hashable
Heuristica = Callable[[Estado], float]


class Problema(Protocol):
    """O contrato de um problema de busca.

    Os estados precisam ser hashable (entram num conjunto de explorados);
    as ações, na prática, são strings com nome legível — o catálogo em
    `problemas/` segue esse padrão.
    """

    estado_inicial: Estado

    def acoes(self, estado: Estado) -> list[Acao]:
        """As ações disponíveis num estado, numa ordem estável."""
        ...

    def transicao(self, estado: Estado, acao: Acao) -> Estado:
        """O estado que resulta de aplicar `acao` em `estado`."""
        ...

    def objetivo(self, estado: Estado) -> bool:
        """O estado resolve o problema?"""
        ...

    def custo(self, estado: Estado, acao: Acao, estado_seguinte: Estado) -> float:
        """O custo de aplicar `acao` — tempo, dinheiro, esforço, latência."""
        ...


@dataclass
class No:
    """Um nó da árvore de busca: um estado mais a trilha que levou a ele."""

    estado: Estado
    pai: No | None
    acao: Acao | None
    custo: float            # custo acumulado desde a raiz (o "g" de A*)
    profundidade: int       # ações desde a raiz

    def caminho(self) -> list[Acao]:
        """Reconstrói a lista de ações da raiz até este nó."""
        passos: list[Acao] = []
        atual: No | None = self
        while atual is not None and atual.acao is not None:
            passos.append(atual.acao)
            atual = atual.pai
        passos.reverse()
        return passos


@dataclass
class Resultado:
    """O que toda busca devolve — os números que o laboratório mede.

    `cortou` só tem significado quando `encontrou` é False e para as buscas
    com limite: True significa que a busca parou no limite sem esgotar o
    espaço (pode haver solução mais funda); False significa que o espaço
    foi esgotado (solução não existe). O `profundidade_limitada` e o
    `aprofundamento_iterativo` é que a preenchem.
    """

    caminho: list[Acao]         # as ações da raiz ao objetivo (vazio se não achou)
    custo: float                # custo total do caminho (0.0 se não achou)
    nos_expandidos: int         # retiradas da fronteira (convenção no topo)
    nos_gerados: int            # nós criados, inclusive repetidos
    profundidade_maxima: int    # maior profundidade entre os nós GERADOS
    segundos: float
    encontrou: bool
    cortou: bool = False


def _raiz(problema: Problema) -> No:
    return No(problema.estado_inicial, None, None, 0.0, 0)


def _sem_sucesso(expandidos: int, gerados: int, prof_max: int, inicio: float, cortou: bool = False) -> Resultado:
    return Resultado(
        caminho=[], custo=0.0, nos_expandidos=expandidos, nos_gerados=gerados,
        profundidade_maxima=prof_max, segundos=time.perf_counter() - inicio,
        encontrou=False, cortou=cortou,
    )


def _achou(no: No, expandidos: int, gerados: int, prof_max: int, inicio: float) -> Resultado:
    return Resultado(
        caminho=no.caminho(), custo=no.custo, nos_expandidos=expandidos,
        nos_gerados=gerados, profundidade_maxima=prof_max,
        segundos=time.perf_counter() - inicio, encontrou=True,
    )


def _custo_do_filho(problema: Problema, no: No, acao: Acao) -> tuple[Estado, float]:
    estado_seguinte = problema.transicao(no.estado, acao)
    return estado_seguinte, no.custo + problema.custo(no.estado, acao, estado_seguinte)


def busca_em_largura(problema: Problema) -> Resultado:
    """Busca em largura: fronteira em fila (primeiro a entrar, primeiro a sair).

    Ótima em número de ações; só ótima em custo quando os custos são uniformes.
    """
    inicio = time.perf_counter()
    fronteira: deque[No] = deque([_raiz(problema)])
    explorados: set[Estado] = set()
    gerados = prof_max = expandidos = 0
    while fronteira:
        no = fronteira.popleft()
        expandidos += 1
        if no.estado in explorados:
            continue
        if problema.objetivo(no.estado):
            return _achou(no, expandidos, gerados, prof_max, inicio)
        explorados.add(no.estado)
        for acao in problema.acoes(no.estado):
            estado_seguinte, custo_total = _custo_do_filho(problema, no, acao)
            filho = No(estado_seguinte, no, acao, custo_total, no.profundidade + 1)
            gerados += 1
            prof_max = max(prof_max, filho.profundidade)
            fronteira.append(filho)
    return _sem_sucesso(expandidos, gerados, prof_max, inicio)


def custo_uniforme(problema: Problema) -> Resultado:
    """Busca de custo uniforme: fronteira em heap por custo acumulado (g).

    Ótima em custo, com ou sem heurística. É a linha de base do lab-05:
    o que A* economiza contra ela é o valor da heurística.
    """
    inicio = time.perf_counter()
    ordem = itertools.count()
    raiz = _raiz(problema)
    fronteira: list[tuple[float, int, No]] = [(raiz.custo, next(ordem), raiz)]
    gerados = prof_max = 0
    expandidos = 0
    explorados: set[Estado] = set()
    while fronteira:
        _, _, no = heapq.heappop(fronteira)
        expandidos += 1  # toda retirada conta, mesmo a de um repetido abaixo
        if no.estado in explorados:
            continue
        if problema.objetivo(no.estado):
            return _achou(no, expandidos, gerados, prof_max, inicio)
        explorados.add(no.estado)
        for acao in problema.acoes(no.estado):
            estado_seguinte, custo_total = _custo_do_filho(problema, no, acao)
            filho = No(estado_seguinte, no, acao, custo_total, no.profundidade + 1)
            gerados += 1
            prof_max = max(prof_max, filho.profundidade)
            heapq.heappush(fronteira, (filho.custo, next(ordem), filho))
    return _sem_sucesso(expandidos, gerados, prof_max, inicio)


def _profundidade_limitada_rec(
    problema: Problema, no: No, limite: int, explorados: set[Estado],
    contagem: dict[str, int],
) -> tuple[No | None, bool]:
    """Uma rodada de profundidade limitada. Devolve (nó objetivo, cortou).

    `cortou` diz se a rodada parou em algum nó que ainda tinha ações —
    é o que distingue "o limite cortou a busca" de "o espaço acabou".
    Busca em GRAFO: o conjunto `explorados` (da rodada) evita reexpandir
    estado que já saiu da fronteira nesta rodada.
    """
    contagem["expandidos"] += 1
    explorados.add(no.estado)
    if problema.objetivo(no.estado):
        return no, False
    if no.profundidade == limite:
        # Cortou de verdade só se havia TERRITÓRIO NOVO atrás das ações —
        # ação cujo resultado já foi explorado não é o limite segurando
        # ninguém, é espaço acabado.
        return None, any(
            problema.transicao(no.estado, acao) not in explorados
            for acao in problema.acoes(no.estado)
        )
    cortou = False
    for acao in problema.acoes(no.estado):
        estado_seguinte = problema.transicao(no.estado, acao)
        filho = No(estado_seguinte, no, acao,
                   no.custo + problema.custo(no.estado, acao, estado_seguinte),
                   no.profundidade + 1)
        contagem["gerados"] += 1
        contagem["prof_max"] = max(contagem["prof_max"], filho.profundidade)
        if filho.estado in explorados:
            continue
        achado, cortou_filho = _profundidade_limitada_rec(
            problema, filho, limite, explorados, contagem)
        if achado is not None:
            return achado, cortou_filho
        cortou = cortou or cortou_filho
    return None, cortou


def profundidade_limitada(problema: Problema, limite: int) -> Resultado:
    """Busca em profundidade com limite, em grafo (conjunto de explorados).

    `Resultado.cortou` distingue os dois insucessos: True = parou no limite e
    pode haver solução mais funda; False = o espaço foi esgotado e a solução
    não existe.
    """
    inicio = time.perf_counter()
    contagem = {"expandidos": 0, "gerados": 0, "prof_max": 0}
    explorados: set[Estado] = set()
    achado, cortou = _profundidade_limitada_rec(
        problema, _raiz(problema), limite, explorados, contagem)
    if achado is not None:
        return _achou(achado, contagem["expandidos"], contagem["gerados"],
                      contagem["prof_max"], inicio)
    return _sem_sucesso(contagem["expandidos"], contagem["gerados"],
                        contagem["prof_max"], inicio, cortou)


def aprofundamento_iterativo(problema: Problema, limite_maximo: int) -> Resultado:
    """Profundidade limitada com limite crescente, de 0 a `limite_maximo`.

    Acumula as contagens de todas as rodadas — é o preço do aprofundamento,
    e o lab-04 o compara com a busca em largura. O conjunto de explorados
    recomeça vazio a cada rodada (é dela que vem a profundidade). Se uma
    rodada esgota o espaço sem cortar no limite, a solução não existe e as
    rodadas param.
    """
    inicio = time.perf_counter()
    expandidos = gerados = prof_max = 0
    cortou_alguma = False
    for limite in range(limite_maximo + 1):
        contagem = {"expandidos": 0, "gerados": 0, "prof_max": 0}
        explorados: set[Estado] = set()
        achado, cortou = _profundidade_limitada_rec(
            problema, _raiz(problema), limite, explorados, contagem)
        expandidos += contagem["expandidos"]
        gerados += contagem["gerados"]
        prof_max = max(prof_max, contagem["prof_max"])
        if achado is not None:
            return _achou(achado, expandidos, gerados, prof_max, inicio)
        cortou_alguma = cortou_alguma or cortou
        if not cortou:
            break  # o espaço esgotou sem cortar: mais limite não encontra nada
    return _sem_sucesso(expandidos, gerados, prof_max, inicio, cortou_alguma)


def _busca_com_heap(problema: Problema, prioridade: Callable[[No, float], float]) -> Resultado:
    """Gulosa e A* juntas: mesma estrutura, muda a chave do heap.

    `prioridade(no, h)` devolve a chave de ordenação: só `h` na gulosa,
    `g + h` no A*. A fronteira mantém duplicatas (lazy deletion): o estado
    repetido sai na hora da retirada, pelo conjunto de explorados.
    """
    inicio = time.perf_counter()
    ordem = itertools.count()
    raiz = _raiz(problema)
    fronteira: list[tuple[float, int, No]] = [(prioridade(raiz, 0.0), next(ordem), raiz)]
    gerados = prof_max = 0
    expandidos = 0
    explorados: set[Estado] = set()
    while fronteira:
        _, _, no = heapq.heappop(fronteira)
        expandidos += 1
        if no.estado in explorados:
            continue
        if problema.objetivo(no.estado):
            return _achou(no, expandidos, gerados, prof_max, inicio)
        explorados.add(no.estado)
        for acao in problema.acoes(no.estado):
            estado_seguinte, custo_total = _custo_do_filho(problema, no, acao)
            filho = No(estado_seguinte, no, acao, custo_total, no.profundidade + 1)
            gerados += 1
            prof_max = max(prof_max, filho.profundidade)
            chave = prioridade(filho, custo_total)
            heapq.heappush(fronteira, (chave, next(ordem), filho))
    return _sem_sucesso(expandidos, gerados, prof_max, inicio)


def busca_gulosa(problema: Problema, heuristica: Heuristica) -> Resultado:
    """Busca gulosa: fronteira ordenada só por h(estado).

    Rápida, mas não ótima: ignora o que já foi gasto. O lab-05 mostra com
    número o que isso custa.
    """
    return _busca_com_heap(problema, lambda no, _: heuristica(no.estado))


def a_estrela(problema: Problema, heuristica: Heuristica) -> Resultado:
    """A*: fronteira ordenada por g + h.

    Com heurística admissível, ótimo em custo — e expande menos nós que o
    custo uniforme, que é o efeito que o lab-05 mede.
    """
    return _busca_com_heap(problema, lambda no, g: g + heuristica(no.estado))


def comparar(
    problema: Problema,
    heuristicas: dict[str, Heuristica] | None = None,
    limite_maximo: int = 32,
) -> list[dict]:
    """Roda as buscas aplicáveis no mesmo problema e devolve a tabela comparativa.

    Cada linha é um dicionário pronto para virar linha de tabela Markdown
    (`MEDICOES.md` do motor; a tabela que o aluno entrega no lab-05 tem a
    mesma forma). As quatro buscas não informadas rodam sempre; para cada
    heurística do dicionário rodam a gulosa e o A* — passe a admissível e a
    inadmissível para ter o contraste que o lab-05 explora.
    """
    linhas: list[dict] = []

    def registrar(nome: str, resultado: Resultado) -> None:
        linhas.append({
            "busca": nome,
            "encontrou": resultado.encontrou,
            "cortou": resultado.cortou,
            # arredondado como os segundos: a linha vira tabela, e o custo
            # exato de somas de floats sai como 17.099999999999998
            "custo": round(resultado.custo, 4),
            "acoes": len(resultado.caminho),
            "nos_expandidos": resultado.nos_expandidos,
            "nos_gerados": resultado.nos_gerados,
            "profundidade_maxima": resultado.profundidade_maxima,
            "segundos": round(resultado.segundos, 4),
        })

    registrar("largura", busca_em_largura(problema))
    registrar("custo_uniforme", custo_uniforme(problema))
    registrar(f"profundidade_limitada(limite={limite_maximo})",
              profundidade_limitada(problema, limite_maximo))
    registrar(f"aprofundamento_iterativo(limite={limite_maximo})",
              aprofundamento_iterativo(problema, limite_maximo))
    for nome, heuristica in (heuristicas or {}).items():
        registrar(f"gulosa[{nome}]", busca_gulosa(problema, heuristica))
        registrar(f"a_estrela[{nome}]", a_estrela(problema, heuristica))
    return linhas
