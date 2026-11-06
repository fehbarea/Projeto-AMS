"""A sua heurística, projetada por relaxamento — esqueleto do desafio da N2.

O que este módulo faz ao rodar (do jeito que está, ele demonstra no
subproblema de diagnóstico do catálogo — aponte MEU_PROBLEMA para o SEU
módulo do lab-03):

    python esqueleto-heuristica.py

As três verificações da projeção, executadas aqui:
  (a) h vale ZERO em todo estado objetivo;
  (b) o A* com a sua heurística devolve o MESMO CUSTO do custo uniforme
      (é a admissibilidade garantindo a otimalidade);
  (c) o A* com a sua heurística expande MENOS nós que o custo uniforme
      (é a economia que justifica a heurística).

O TODO é a heurística — e a justificativa de admissibilidade escrita no
comentário dela é o que a rubrica avalia na faixa Excelente.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

# TODO 0: aponte para o SEU módulo de formulação (o do lab-03) —
# "arquivo.py:NOME" ou "problemas.diagnostico:MAIOR" (o catálogo, para
# demonstrar antes de apontar o seu).
MEU_PROBLEMA = "problemas.diagnostico:MAIOR"

_AQUI = Path(__file__).resolve().parent


def pasta_do_comum() -> Path:
    """Localiza comum/busca.py: aqui ao lado, subindo as pastas, ou dentro
    de qualquer pasta irmã (os laboratórios extraídos levam a sua cópia)."""
    for pasta in (_AQUI, *_AQUI.parents):
        direto = pasta / "comum" / "busca.py"
        if direto.is_file():
            return pasta / "comum"
        try:
            for candidato in pasta.glob("*/comum/busca.py"):
                return candidato.parent
        except OSError:
            continue
    raise FileNotFoundError(
        "comum/busca.py não encontrado a partir de " f"{_AQUI}. Rode este "
        "esqueleto no repositório que tem os laboratórios extraídos "
        "(D2-04 ou D2-05 trazem a pasta comum/).")


_pasta = str(pasta_do_comum())
if _pasta not in sys.path:
    sys.path.insert(0, _pasta)

from busca import a_estrela, custo_uniforme  # noqa: E402


def carregar_problema(especificacao: str):
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


def heuristica(estado) -> float:
    """TODO: a SUA heurística, projetada por relaxamento.

    O método (slide 32 do E3): remova UMA restrição do problema, resolva o
    problema mais fácil — o custo dessa solução é a estimativa, e ela
    nunca superestima, porque tudo o que era possível no original continua
    possível no relaxado.

    ESCREVA AQUI, no comentário, a justificativa completa:
      1. qual restrição foi removida;
      2. por que, sem ela, o custo ótimo do problema relaxado é o valor
         que a função devolve;
      3. por que, com a restrição de volta, o custo real nunca fica
         abaixo da estimativa.
    """
    problema = _problema()
    if hasattr(problema, "heuristica_admissivel"):
        return problema.heuristica_admissivel(estado)
    raise NotImplementedError(
        "TODO: projete a sua heurística por relaxamento e escreva a "
        "justificativa de admissibilidade no comentário")


_problema_cacheado = None


def _problema():
    global _problema_cacheado
    if _problema_cacheado is None:
        _problema_cacheado = carregar_problema(MEU_PROBLEMA)
    return _problema_cacheado


if __name__ == "__main__":
    problema = _problema()
    uniforme = custo_uniforme(problema)
    informada = a_estrela(problema, heuristica)

    print(f"Formulação: {MEU_PROBLEMA}\n")
    print(f"(a) objetivo alcançado: {'sim' if informada.encontrou else 'NÃO'}")
    print(f"(b) custo do A* com a sua heurística: {round(informada.custo, 4)}"
          f" · custo uniforme: {round(uniforme.custo, 4)}")
    print(f"(c) nós expandidos — A estrela: {informada.nos_expandidos}"
          f" · custo uniforme: {uniforme.nos_expandidos}")

    verde = (informada.encontrou
             and round(informada.custo, 4) == round(uniforme.custo, 4)
             and informada.nos_expandidos < uniforme.nos_expandidos)
    if verde:
        print("\nAs três verificações verdes — falta o parágrafo da "
              "dominância no relatório (o modelo está no "
              "solucao-heuristica.py).")
    else:
        print("\nAlguma verificação vermelha — o slide 36 do E3 tem o "
              "diagnóstico: estimativa fraca (remova uma restrição menor) "
              "ou superestimando (reveja a justificativa).")
    raise SystemExit(0 if verde else 1)
