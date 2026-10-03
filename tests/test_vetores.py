"""Testes das funções vetoriais (norma, cosseno, vizinhos)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.spatial.distance import cosine as cosseno_scipy

from ams.vetores import norma, similaridade_cosseno, vizinhos_mais_proximos


def test_norma_do_vetor_3_4() -> None:
    assert norma(np.array([3.0, 4.0])) == pytest.approx(5.0)


def test_norma_de_vetor_zero() -> None:
    assert norma(np.zeros(4)) == 0.0


def test_cosseno_de_vetores_iguais_e_um() -> None:
    v = np.array([1.0, 2.0, 3.0])
    assert similaridade_cosseno(v, v) == pytest.approx(1.0)


def test_cosseno_de_vetores_ortogonais_e_zero() -> None:
    u = np.array([1.0, 0.0])
    v = np.array([0.0, 5.0])
    assert similaridade_cosseno(u, v) == pytest.approx(0.0, abs=1e-12)


def test_cosseno_de_vetores_opostos_e_menos_um() -> None:
    u = np.array([2.0, 1.0])
    v = np.array([-4.0, -2.0])
    assert similaridade_cosseno(u, v) == pytest.approx(-1.0)


def test_cosseno_bate_com_scipy_a_1e9() -> None:
    rng = np.random.default_rng(7)
    for _ in range(20):
        u = rng.normal(size=8)
        v = rng.normal(size=8)
        # scipy devolve a DISTÂNCIA (1 − cosseno); nosso valor é a similaridade
        esperado = 1.0 - cosseno_scipy(u, v)
        assert similaridade_cosseno(u, v) == pytest.approx(esperado, abs=1e-9)


def test_cosseno_rejeita_vetor_zero() -> None:
    with pytest.raises(ValueError, match="vetor zero"):
        similaridade_cosseno(np.zeros(3), np.array([1.0, 2.0, 3.0]))


def test_cosseno_rejeita_comprimentos_diferentes() -> None:
    with pytest.raises(ValueError, match="comprimentos diferentes"):
        similaridade_cosseno(np.array([1.0, 2.0]), np.array([1.0, 2.0, 3.0]))


def test_vizinhos_ordenados_da_maior_para_menor_similaridade() -> None:
    rng = np.random.default_rng(42)
    matriz = rng.normal(size=(50, 6))
    alvo = matriz[10].copy()  # o próprio deve ser o vizinho nº 1 (cosseno 1)
    indices, similaridades = vizinhos_mais_proximos(alvo, matriz, quantidade=5)
    assert indices[0] == 10
    assert similaridades[0] == pytest.approx(1.0)
    # ordenação decrescente
    assert all(similaridades[i] >= similaridades[i + 1] for i in range(len(similaridades) - 1))


def test_vizinhos_encontra_duplicado() -> None:
    rng = np.random.default_rng(3)
    matriz = rng.normal(size=(30, 4))
    matriz[17] = matriz[5] * 2.0  # mesma direção ⇒ cosseno 1 com o 5
    indices, similaridades = vizinhos_mais_proximos(matriz[5], matriz, quantidade=3)
    assert set(indices[:2]) == {5, 17}
    assert abs(similaridades[1] - 1.0) < 1e-12


def test_vizinhos_rejeita_matriz_incompativel() -> None:
    matriz = np.ones((5, 3))
    alvo = np.ones(4)
    with pytest.raises(ValueError, match="incompat"):
        vizinhos_mais_proximos(alvo, matriz, quantidade=2)
