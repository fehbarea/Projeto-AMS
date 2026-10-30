"""medir.py — a medição da linha de base sobre os casos rotulados.

Roda o agente (a função `decidir` e o estado do `esqueleto.py`) sobre o
conjunto de casos, caso a caso, na ordem cronológica, e imprime as três
informações que o slide 28 cobra que o aluno traga:

  1. A MÉTRICA — qual é (a primária do `agent-spec.md`);
  2. O VALOR — quanto deu;
  3. O CONJUNTO — sobre quais casos, quantos são e como se distribuem.

E acrescenta a leitura mais valiosa (slide 30): ONDE o agente erra — a
lista dos casos com decisão diferente do rótulo, que é a matéria-prima da
análise escrita da entrega final.

Uso:  python medir.py            (usa o CAMINHO_DOS_CASOS do esqueleto)
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import esqueleto


def medir(caminho: str | Path, decidir=None, classe_estado=None) -> dict:
    """Roda o agente sobre os casos e devolve o resultado da medição.

    O agente decide caso a caso, em ordem cronológica; depois de cada
    decisão, o ambiente revela o desfecho e o estado interno se atualiza —
    é o ciclo percepção → decisão → ação → observação do agente
    baseado em modelo. O caminho vem por parâmetro (a troca do conjunto é
    uma linha, slide 29); sem parâmetro, o configurado no esqueleto.
    """
    decidir = decidir or esqueleto.decidir
    classe_estado = classe_estado or esqueleto.EstadoDaFrota
    casos = esqueleto.carregar_casos(caminho)
    estado = classe_estado()
    acertos = 0
    erros: list[dict] = []
    for registro in casos:
        decisao = decidir(registro, estado)
        correta = registro["acao_correta"]
        if decisao == correta:
            acertos += 1
        else:
            erros.append({"id_caso": registro["id_caso"],
                          "decidiu": decisao, "correta": correta})
        estado.registrar_desfecho(registro)
    total = len(casos)
    rotulos = Counter(registro["acao_correta"] for registro in casos)
    return {
        "caminho": str(caminho),
        "total": total,
        "acertos": acertos,
        "valor": acertos / total if total else 0.0,
        "distribuicao": dict(rotulos),
        "erros": erros,
    }


def imprimir(resultado: dict, nome_da_metrica: str) -> None:
    """As três informações do slide 28, e a lista de onde erra (slide 30)."""
    print(f"Métrica primária: {nome_da_metrica}")
    print(f"Valor: {resultado['acertos']}/{resultado['total']} = "
          f"{round(resultado['valor'], 4)}")
    print(f"Conjunto: {resultado['caminho']} — {resultado['total']} casos "
          f"rotulados {resultado['distribuicao']}")
    if resultado["erros"]:
        print("Onde erra (o rótulo que o agente não deu):")
        for erro in resultado["erros"]:
            print(f"  caso {erro['id_caso']}: decidiu "
                  f"{erro['decidiu']}, correto era {erro['correta']}")
    else:
        print("Onde erra: em nenhum dos casos — cuidado com um conjunto só "
              "de casos fáceis (slide 24: número bonito e inútil).")


def medir_e_imprimir(caminho: str | Path, decidir, classe_estado) -> None:
    resultado = medir(caminho, decidir, classe_estado)
    imprimir(resultado, "acerto da decisão "
                        "(casos com decisão igual à rotulada, sobre o total)")


if __name__ == "__main__":
    medir_e_imprimir(esqueleto.CAMINHO_DOS_CASOS,
                     esqueleto.decidir, esqueleto.EstadoDaFrota)
