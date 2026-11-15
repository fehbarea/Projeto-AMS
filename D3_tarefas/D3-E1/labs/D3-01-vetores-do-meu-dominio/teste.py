"""Testes do Laboratório 01 — a prova de que a conta está certa.

Como usar (da pasta do laboratório):
    python -m pytest teste.py -q

O que cada família confere:

  1. O COSENO (TAREFA 1) — valores conhecidos: o exemplo do slide 14,
     vetores iguais, vetores perpendiculares;
  2. A EUCLIDIANA (TAREFA 2) — a norma da diferença, com o mesmo exemplo;
  3. A ORDENAÇÃO (TAREFA 3) — sobre uma matriz pequena de ordem conhecida,
     do mais parecido ao menos parecido;
  4. O CONJUNTO DO PACOTE — os arquivos de vetores carregam alinhados
     (frases e vetores na mesma quantidade — FONTE.md).

A quinta verificação está escondida na 3: sobre vetores NORMALIZADOS, a
ordenação por cosseno e a ordenação por euclidiana (ao contrário) têm de
ser a mesma — é o detalhe do slide 17 que explica por que sistemas de
busca normalizam tudo na entrada.

Se os testes falham citando `...` (Ellipsis), as TAREFAS ainda estão em
branco — esse é o estado de partida.
"""

from __future__ import annotations

import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

_AQUI = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location("esqueleto", _AQUI / "esqueleto.py")
esqueleto = importlib.util.module_from_spec(_spec)
sys.modules["esqueleto"] = esqueleto
_spec.loader.exec_module(esqueleto)  # type: ignore[union-attr]

# Os dois vetores do slide 14 do D3-E1.
A_DO_SLIDE = np.array([2.0, 1.0, 0.0])
B_DO_SLIDE = np.array([1.0, 3.0, 1.0])
COSENO_DO_SLIDE = 5.0 / (math.sqrt(5.0) * math.sqrt(11.0))   # ≈ 0,6742

# Matriz pequena com ordenação conhecida (TAREFA 3): cossenos
# (1,2)=0,96 · (0,2)=0,80 · (0,1)=0,60 · (1,3)=−0,60 · (2,3)=−0,80 · (0,3)=−1
MATRIZ_PEQUENA = np.array([[1.0, 0.0],
                           [0.6, 0.8],
                           [0.8, 0.6],
                           [-1.0, 0.0]])


# --- 1. o cosseno ------------------------------------------------------------

def test_o_cosseno_reproduz_o_exemplo_do_slide():
    valor = esqueleto.similaridade_cosseno(A_DO_SLIDE, B_DO_SLIDE)
    assert valor is not None, "a TAREFA 1 ainda está em branco"
    assert abs(valor - COSENO_DO_SLIDE) < 1e-9, (
        f"deu {valor:.6f}; o esperado é {COSENO_DO_SLIDE:.6f} "
        "(produto escalar dividido pelas duas normas)")


def test_vetores_iguais_tem_cosseno_1_e_perpendiculares_tem_0():
    assert abs(esqueleto.similaridade_cosseno(A_DO_SLIDE, A_DO_SLIDE) - 1.0) < 1e-9
    assert abs(esqueleto.similaridade_cosseno(
        np.array([1.0, 0.0]), np.array([0.0, 3.0]))) < 1e-9


# --- 2. a euclidiana -----------------------------------------------------------

def test_a_euclidiana_e_a_norma_da_diferenca():
    valor = esqueleto.distancia_euclidiana(A_DO_SLIDE, B_DO_SLIDE)
    assert valor is not None, "a TAREFA 2 ainda está em branco"
    assert abs(valor - math.sqrt(6.0)) < 1e-9, (
        f"deu {valor:.6f}; o esperado é {math.sqrt(6.0):.6f}")
    assert esqueleto.distancia_euclidiana(A_DO_SLIDE, A_DO_SLIDE) == 0.0


# --- 3. a ordenação --------------------------------------------------------------

def test_a_ordenacao_por_cosseno_e_do_mais_parecido_ao_menos():
    pares = esqueleto.pares_ordenados(MATRIZ_PEQUENA)
    assert pares is not None, "a TAREFA 3 ainda está em branco"
    esperado = [(1, 2), (0, 2), (0, 1), (1, 3), (2, 3), (0, 3)]
    obtido = [tuple(par) for par, _ in pares]
    assert obtido == esperado, (
        f"a ordem veio {obtido}; a esperada é {esperado} — a ordenação tem "
        "de ir da similaridade MAIS ALTA para a MAIS BAIXA")
    valores = [valor for _, valor in pares]
    assert valores == sorted(valores, reverse=True)


def test_sobre_vetores_normalizados_cosseno_e_euclidiana_ordem_igual():
    rng = np.random.default_rng(7)
    matriz = rng.normal(size=(6, 5))
    unitarios = matriz / np.linalg.norm(matriz, axis=1, keepdims=True)
    por_cosseno = [tuple(par) for par, _ in esqueleto.pares_ordenados(unitarios)]
    por_euclidiana = sorted(
        (tuple(par) for par, _ in esqueleto.pares_ordenados(unitarios)),
        key=lambda par: esqueleto.distancia_euclidiana(
            unitarios[par[0]], unitarios[par[1]]))
    assert por_cosseno == por_euclidiana, (
        "sobre vetores normalizados as duas ordenações devem coincidir "
        "(slide 17)")


# --- 4. o conjunto do pacote -------------------------------------------------------

def test_os_arquivos_do_pacote_carregam_alinhados():
    frases, matriz = esqueleto.carregar(esqueleto.CONJUNTO)
    assert len(frases) == len(matriz) == 200
    assert matriz.shape[1] == 384
