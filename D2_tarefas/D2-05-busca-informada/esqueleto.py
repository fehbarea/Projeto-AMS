"""Laboratório 05 — A estrela e a comparação: o que a heurística economiza.

O esqueleto acrescenta as linhas da busca gulosa e do A* à tabela do
lab-04, com DUAS heurísticas já prontas e comentadas para a formulação
apontada: uma admissível e uma inadmissível. O comentário de cada uma diz
POR QUE ela é (ou não é) admissível — e esse argumento é o que a rubrica
avalia, tanto quanto o código.

    python esqueleto.py

Caminho padrão: receba as duas heurísticas prontas, rode, complete a tabela
do lab-04 e escreva o parágrafo da dominância — qual heurística domina a
outra, e por quê (slide 31: entre duas admissíveis, domina a que estima
mais alto em todo estado; a dominada expande mais, nunca menos). A rubrica
trata esse argumento como EQUIVALENTE a projetar uma heurística — a
análise de admissibilidade é o que o critério mede, e ela se faz em
português.

Desafio: a heurística é sua — projete por relaxamento (slide 32: remova
uma restrição, resolva o problema mais fácil, declare qual restrição
removeu) e preencha as funções marcadas com TODO. Trocar de caminho é
livre, nos dois sentidos e sem justificar.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# A mesma constante do lab-04 — a sua formulação, uma linha para trocar.
FORMULACAO = "problemas.problema_ams:MAIOR"
LIMITE = 32

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

from busca import busca_gulosa, a_estrela  # noqa: E402


def carregar_formulacao(especificacao: str):
    """O mesmo carregador do lab-04: "arquivo.py:NOME" ou "modulo:NOME"."""
    caminho, marcador, atributo = especificacao.rpartition(":")
    if marcador and atributo.isidentifier() and ".py" in caminho:
        spec = importlib.util.spec_from_file_location(Path(caminho).stem,
                                                      caminho)
        modulo = importlib.util.module_from_spec(spec)
        sys.modules.setdefault(Path(caminho).stem, modulo)
        spec.loader.exec_module(modulo)  # type: ignore[union-attr]
    else:
        modulo = importlib.import_module(especificacao.partition(":")[0])
        atributo = especificacao.partition(":")[2] or "MAIOR"
    return getattr(modulo, atributo)


# --------------------------------------------------------------------------
# As duas heurísticas — prontas no caminho padrão, suas no desafio
# --------------------------------------------------------------------------

def heuristica_admissivel(estado) -> float:
    """A estimativa que NUNCA superestima o custo restante (slide 26).

    Padrão: esta função delega à `heuristica_admissivel` do problema
    apontado — os três do catálogo trazem a delas, comentada. Abra o
    módulo do catálogo e LEIA o comentário: o argumento de admissibilidade
    de lá é o modelo do parágrafo que você vai escrever.

    Desafio (TODO): a sua heurística, projetada por relaxamento. Escreva
    aqui, no comentário, qual restrição removeu e por que o custo da
    versão relaxada nunca passa do real — tudo o que era possível no
    problema original continua possível no relaxado.
    """
    problema = _problema()
    if hasattr(problema, "heuristica_admissivel"):
        return problema.heuristica_admissivel(estado)
    raise NotImplementedError(
        "TODO (desafio): projete a sua heurística admissível por "
        "relaxamento — remova uma restrição, declare qual no comentário")


def heuristica_inadmissivel(estado) -> float:
    """A estimativa que superestima — e o que ela custa (slide 33).

    Padrão: delega à `heuristica_inadmissivel` do problema apontado. O
    comentário de cada uma do catálogo explica POR QUE superestima — e as
    linhas da tabela vão mostrar o efeito: caminho mais caro que o ótimo,
    apesar de expandir pouquíssimo. Rápida e errada.

    Desafio (TODO): uma heurística "tentadora" do SEU domínio que
    superestime — o pessimismo é o que quebra a garantia do A*; mostrá-lo
    com número é metade do laboratório.
    """
    problema = _problema()
    if hasattr(problema, "heuristica_inadmissivel"):
        return problema.heuristica_inadmissivel(estado)
    raise NotImplementedError(
        "TODO (desafio): escreva a sua heurística inadmissível — a que "
        "superestima e mostra o que a garantia vale")


_problema_cacheado = None


def _problema():
    global _problema_cacheado
    if _problema_cacheado is None:
        _problema_cacheado = carregar_formulacao(FORMULACAO)
    return _problema_cacheado


# --------------------------------------------------------------------------
# A tabela completa — a do lab-04, mais as quatro linhas informadas
# --------------------------------------------------------------------------

CABECALHO = (
    "| Busca | Custo | Ações | Nós expandidos | Nós gerados | Prof. máx. | Segundos |\n"
    "|---|---:|---:|---:|---:|---:|---:|\n"
)


def _linha(nome: str, resultado) -> str:
    return (
        f"| {nome} | {round(resultado.custo, 4)} | {len(resultado.caminho)} "
        f"| {resultado.nos_expandidos} | {resultado.nos_gerados} "
        f"| {resultado.profundidade_maxima} | {resultado.segundos:.6f} |\n"
    )


def tabela_informada(problema) -> str:
    """Gulosa e A* com as duas heurísticas — as linhas que faltavam."""
    textos = []
    textos.append(_linha("gulosa[admissivel]",
                         busca_gulosa(problema, heuristica_admissivel)))
    textos.append(_linha("a_estrela[admissivel]",
                         a_estrela(problema, heuristica_admissivel)))
    textos.append(_linha("gulosa[inadmissivel]",
                         busca_gulosa(problema, heuristica_inadmissivel)))
    textos.append(_linha("a_estrela[inadmissivel]",
                         a_estrela(problema, heuristica_inadmissivel)))
    return "".join(textos)


if __name__ == "__main__":
    problema = _problema()
    print(f"Formulação: {FORMULACAO}\n")
    print(CABECALHO + tabela_informada(problema))
    print("""Como ler (slide 36):
  - A estrela expandindo MAIS que o custo uniforme do lab-04? Heurística fraca.
  - A estrela com custo PIOR que o custo uniforme? A heurística superestima.
  - Antes de qualquer outra verificação: h vale zero em todo estado objetivo?
  - O item que vale nota: o parágrafo da dominância, comparando as duas
    colunas de expandidos — a evidência são os números, a explicação é sua.
""")
