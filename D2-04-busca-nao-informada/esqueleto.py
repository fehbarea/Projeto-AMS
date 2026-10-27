"""Laboratório 04 — as quatro buscas não informadas, medidas.

Este esqueleto JÁ RODA: ele aponta para uma formulação do catálogo, roda as
quatro buscas não informadas e imprime a tabela em Markdown, pronta para
colar na entrega. O trabalho do caminho padrão é trocar a constante
`FORMULACAO` para a SUA formulação do laboratório 03, executar, e ler a
tabela — medir, não afirmar.

    python esqueleto.py

No desafio, a fronteira e o conjunto de explorados são seus: preencha as
duas funções marcadas com TODO (sem abrir `comum/busca.py` — o protocolo do
slide 46 basta), troque `USAR_IMPLEMENTACAO_PROPRIA` para True e compare as
suas linhas com as do motor. Trocar de caminho é livre, nos dois sentidos.

A tabela sai com o custo e os segundos arredondados — 17.1, nunca
17.099999999999998.
"""

from __future__ import annotations

import importlib.util
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# --------------------------------------------------------------------------
# Configuração — é aqui que se troca. Nada de caminho embutido no meio do
# código: uma constante, uma linha.
# --------------------------------------------------------------------------
FORMULACAO = "problemas.problema-ams:MAIOR"
# Substitua pelo SEU módulo do laboratório 03, no formato "arquivo.py:NOME".
# O exemplo aponta para o subproblema de diagnóstico do catálogo, instância
# maior — os números dela estão no MEDICOES.md do motor (material do
# professor) e no teste.py deste pacote.

LIMITE = 32                     # o limite das duas buscas com limite

USAR_IMPLEMENTACAO_PROPRIA = False   # desafio: True depois dos TODOs


# --------------------------------------------------------------------------
# O motor e a sua formulação
# --------------------------------------------------------------------------

_AQUI = Path(__file__).resolve().parent


def pasta_do_comum() -> Path:
    for pasta in (_AQUI, *_AQUI.parents):
        if (pasta / "comum" / "busca.py").is_file():
            return pasta / "comum"
    raise FileNotFoundError(
        "comum/busca.py não encontrado — extraia o pacote inteiro: a pasta "
        "comum/ viaja junto do laboratório.")


_pasta = str(pasta_do_comum())
if _pasta not in sys.path:
    sys.path.insert(0, _pasta)

from busca import (  # noqa: E402
    aprofundamento_iterativo,
    busca_em_largura,
    custo_uniforme,
    profundidade_limitada,
)


def carregar_formulacao(especificacao: str):
    """Carrega "arquivo.py:NOME" (o seu módulo) ou "modulo.sub:NOME" (o
    catálogo). Uma constante no topo, uma linha para trocar."""
    caminho, marcador, atributo = especificacao.rpartition(":")
    if marcador and atributo.isidentifier() and ".py" in caminho:
        spec = importlib.util.spec_from_file_location(
            Path(caminho).stem, caminho)
        modulo = importlib.util.module_from_spec(spec)
        sys.modules.setdefault(Path(caminho).stem, modulo)
        spec.loader.exec_module(modulo)  # type: ignore[union-attr]
    else:
        modulo = importlib.import_module(
            especificacao.partition(":")[0])
        atributo = especificacao.partition(":")[2] or "MAIOR"
    return getattr(modulo, atributo)


# --------------------------------------------------------------------------
# Desafio — a sua fronteira e o seu conjunto de explorados
# --------------------------------------------------------------------------

@dataclass
class Resultado:
    """O que a sua busca devolve — os mesmos campos do `Resultado` do motor
    (slide 13). É o que a tabela imprime."""

    caminho: list            # as ações da raiz ao objetivo
    custo: float             # custo total do caminho
    nos_expandidos: int      # retiradas da fronteira, repetidos inclusive
    nos_gerados: int         # nós criados, repetidos inclusive
    profundidade_maxima: int
    segundos: float
    encontrou: bool


class No:
    """Um nó da árvore de busca: o estado mais a trilha que levou a ele."""

    def __init__(self, estado, pai, acao, custo, profundidade):
        self.estado = estado
        self.pai = pai
        self.acao = acao
        self.custo = custo
        self.profundidade = profundidade

    def caminho(self) -> list:
        passos: list = []
        atual = self
        while atual is not None and atual.acao is not None:
            passos.append(atual.acao)
            atual = atual.pai
        passos.reverse()
        return passos


def minha_busca_em_largura(problema) -> Resultado:
    """TODO (desafio): a busca em largura, a partir do protocolo.

    O que a definição pede (slides 14 e 12): fronteira em FILA
    (`collections.deque`, `popleft()`), conjunto de EXPLORADOS que impede
    reexpandir estado, e teste de objetivo NA RETIRADA da fronteira.
    `No` e `Resultado` acima já dão a estrutura; o laço é seu.
    Sem abrir `comum/busca.py` — quem abre, perde o laboratório e não
    ganha nada, porque a análise escrita é o que vale nota.
    """
    raise NotImplementedError(
        "TODO (desafio): implemente a sua busca em largura e troque "
        "USAR_IMPLEMENTACAO_PROPRIA para True")


def meu_custo_uniforme(problema) -> Resultado:
    """TODO (desafio): o custo uniforme, a partir do protocolo.

    A diferença da largura cabe numa linha: a fronteira é um HEAP ordenado
    pelo custo acumulado (`heapq`, com um contador de desempate — dois nós
    de mesmo custo saem por ordem de criação). O teste de objetivo continua
    na retirada — é dele que vem a otimalidade (slide 15).
    """
    raise NotImplementedError(
        "TODO (desafio): implemente o seu custo uniforme e troque "
        "USAR_IMPLEMENTACAO_PROPRIA para True")


# --------------------------------------------------------------------------
# A tabela
# --------------------------------------------------------------------------

CABECALHO = (
    "| Busca | Custo | Ações | Nós expandidos | Nós gerados | Prof. máx. | Segundos |\n"
    "|---|---:|---:|---:|---:|---:|---:|\n"
)


def linha(nome: str, resultado) -> str:
    return (
        f"| {nome} | {round(resultado.custo, 4)} | {len(resultado.caminho)} "
        f"| {resultado.nos_expandidos} | {resultado.nos_gerados} "
        f"| {resultado.profundidade_maxima} | {resultado.segundos:.6f} |\n"
    )


def tabela(problema) -> str:
    """As quatro buscas sobre o problema, em Markdown pronto para colar."""
    inicio = time.perf_counter()
    textos = [CABECALHO]
    textos.append(linha("largura", busca_em_largura(problema)))
    textos.append(linha("custo_uniforme", custo_uniforme(problema)))
    textos.append(linha(
        f"profundidade_limitada(limite={LIMITE})",
        profundidade_limitada(problema, LIMITE)))
    textos.append(linha(
        f"aprofundamento_iterativo(limite={LIMITE})",
        aprofundamento_iterativo(problema, LIMITE)))
    if USAR_IMPLEMENTACAO_PROPRIA:
        textos.append(linha("minha_largura", minha_busca_em_largura(problema)))
        textos.append(linha("meu_custo_uniforme", meu_custo_uniforme(problema)))
    total = time.perf_counter() - inicio
    textos.append(
        f"\nCusto e segundos arredondados. Forma: `comum.busca.comparar()` "
        f"em {round(total, 4)} s.\n")
    return "".join(textos)


if __name__ == "__main__":
    problema = carregar_formulacao(FORMULACAO)
    print(f"Formulação: {FORMULACAO}\n")
    print(tabela(problema))
    print("Lembre a ressalva de contagem (slide 20): a profundidade limitada "
          "é recursiva e não tem fronteira — nela, `nos_expandidos` conta "
          "entradas na recursão, sem repetidos. Parte da vantagem aparente "
          "dela é diferença de contagem. Registre isso na análise.")
    print(f"\nPróximo passo: cole a tabela na entrega e responda — alguma "
          f"busca achou caminho mais barato que a largura? Em {FORMULACAO.split(':')[0]}"
          ", por quê?")
