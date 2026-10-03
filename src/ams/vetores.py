"""Álgebra linear com NumPy: norma, similaridade de cosseno e vizinhos.

Por que implementar à mão o que a biblioteca já tem: porque a similaridade
de cosseno é o coração de todo sistema de recuperação (RAG) — é assim que
um sistema acha o documento certo para uma pergunta. Ver a fórmula vira
código uma vez elimina a magia para sempre. (A D3 dá a base teórica e a
D7 usa isso em escala.)
"""

from __future__ import annotations

import numpy as np


def norma(vetor: np.ndarray) -> float:
    """Comprimento (norma euclidiana) de um vetor.

    Args:
        vetor: vetor 1-D de números.

    Returns:
        A norma como float.

    Examples:
        >>> norma(np.array([3.0, 4.0]))
        5.0
    """
    return float(np.sqrt(np.dot(vetor, vetor)))


def similaridade_cosseno(u: np.ndarray, v: np.ndarray) -> float:
    """Similaridade de cosseno entre dois vetores: 1 = mesma direção, 0 = ortogonais.

    O produto escalar mede alinhamento, mas cresce com o tamanho dos
    vetores; dividir pelas normas isola a direção — que é o que interessa
    quando comparamos perfis de sensores (ou embeddings).

    Args:
        u: vetor 1-D.
        v: vetor 1-D do mesmo comprimento.

    Returns:
        Similaridade no intervalo [-1, 1].

    Raises:
        ValueError: se os vetores têm comprimentos diferentes ou um deles
            é o vetor zero (direção indefinida).
    """
    if u.shape != v.shape:
        raise ValueError(
            f"vetores de comprimentos diferentes ({u.shape[0]} e {v.shape[0]}) não têm cosseno."
        )
    norma_u, norma_v = norma(u), norma(v)
    if norma_u == 0.0 or norma_v == 0.0:
        raise ValueError("vetor zero não tem direção — similaridade de cosseno indefinida.")
    return float(np.dot(u, v) / (norma_u * norma_v))


def vizinhos_mais_proximos(
    alvo: np.ndarray, matriz: np.ndarray, quantidade: int = 5
) -> tuple[np.ndarray, np.ndarray]:
    """Devolve os índices e similaridades dos vizinhos mais parecidos com o alvo.

    "Parecidos" aqui = maior similaridade de cosseno com o vetor alvo.

    Args:
        alvo: vetor 1-D de referência.
        matriz: matriz (n_amostras, n_dimensões) com os candidatos.
        quantidade: quantos vizinhos devolver.

    Returns:
        Tupla (índices, similaridades), ambos 1-D, ordenados da maior
        similaridade para a menor.

    Raises:
        ValueError: se dimensões não casam ou quantidade for inválido.
    """
    if matriz.ndim != 2 or matriz.shape[1] != alvo.shape[0]:
        raise ValueError(
            f"matriz {matriz.shape} e alvo {alvo.shape} incompatíveis — "
            "o número de colunas deve ser igual ao comprimento do alvo."
        )
    if not 1 <= quantidade <= matriz.shape[0]:
        raise ValueError(
            f"quantidade deve estar entre 1 e {matriz.shape[0]} (recebi {quantidade})."
        )

    # Normalizamos uma vez só e usamos o produto escalar matricial: cada linha
    # do resultado é o cosseno do alvo com aquele candidato. Com 10.000
    # candidatos isso é milhares de vezes mais rápido que um laço em Python.
    alvo_unitario = alvo / norma(alvo)
    normas = np.sqrt((matriz * matriz).sum(axis=1))
    validos = normas > 0
    cossenos = np.zeros(matriz.shape[0])
    cossenos[validos] = (matriz[validos] @ alvo_unitario) / normas[validos]

    ordem = np.argsort(-cossenos)[:quantidade]
    return ordem, cossenos[ordem]
