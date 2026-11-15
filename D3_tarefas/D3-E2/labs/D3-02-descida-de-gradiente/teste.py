"""Testes do Laboratório 02 — a prova de que a descida desce.

Como usar (da pasta do laboratório):
    python -m pytest teste.py -q

O que cada família confere:

  1. OS DADOS — nascem sempre iguais (semente 7), a partir dos pesos
     conhecidos que o enunciado declara;
  2. A CONVERGÊNCIA — com taxa 0,1 a perda desce e estabiliza e os pesos
     encontrados chegam perto dos que geraram os dados (o critério do
     slide 10);
  3. A PACIÊNCIA — com taxa 0,001 a perda ainda está caindo quando os 200
     passos acabam e os pesos ficam longe (a linha "baixa demais" do
     slide 12);
  4. A DIVERGÊNCIA — com taxa 1,5 a perda sobe sem controle e vira valor
     não numérico (a linha "alta demais" do slide 12); com passos
     suficientes, o `inf` vira `nan` (slide 13).

Se o teste falha com um `TypeError` citando `...` (Ellipsis), as duas
TAREFAS do esqueleto ainda estão em branco — esse é o estado de partida.
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


# --- 1. os dados -------------------------------------------------------------

def test_os_dados_nascem_sempre_iguais():
    x1, y1 = esqueleto.gerar_dados()
    x2, y2 = esqueleto.gerar_dados()
    assert np.array_equal(x1, x2) and np.array_equal(y1, y2), (
        "os dados mudaram entre duas gerações — a semente dos dados não está "
        "fixada (regra do curso: todo número é reproduzível)")


def test_os_dados_nascem_dos_pesos_conhecidos():
    x, y = esqueleto.gerar_dados()
    inclinacao, intersecao = np.polyfit(x, y, 1)
    assert abs(inclinacao - esqueleto.W_VERDADEIRO) < 0.1, (
        f"o ajuste da amostra deu w={inclinacao:.4f}, longe do "
        f"{esqueleto.W_VERDADEIRO} declarado — os dados não condizem com a "
        "história do enunciado")
    assert abs(intersecao - esqueleto.B_VERDADEIRO) < 0.2


# --- 2. a convergência (taxa 0,1) ---------------------------------------------

def test_com_taxa_0_1_a_perda_desce_e_estabiliza():
    x, y = esqueleto.gerar_dados()
    w, b, perdas = esqueleto.descida(x, y, taxa=0.1, passos=200)
    assert len(perdas) == 200
    assert perdas[-1] < perdas[0] / 1000, (
        "a perda não caiu duas ordens de grandeza — confira o sinal e o "
        "fator 2 das derivadas")
    cauda = perdas[-20:]
    assert max(cauda) - min(cauda) < perdas[-1] / 10, (
        "a perda não estabilizou no fim da descida")


def test_com_taxa_0_1_os_pesos_chegam_perto_dos_verdadeiros():
    x, y = esqueleto.gerar_dados()
    w, b, _ = esqueleto.descida(x, y, taxa=0.1, passos=200)
    assert abs(float(w) - esqueleto.W_VERDADEIRO) < 0.05, (
        f"w ficou em {float(w):.4f}; o que gerou os dados é "
        f"{esqueleto.W_VERDADEIRO}")
    assert abs(float(b) - esqueleto.B_VERDADEIRO) < 0.2


# --- 3. a paciência (taxa 0,001) -----------------------------------------------

def test_com_taxa_0_001_nao_estabiliza_em_200_passos():
    x, y = esqueleto.gerar_dados()
    _, _, perdas = esqueleto.descida(x, y, taxa=0.001, passos=200)
    assert all(math.isfinite(p) for p in perdas), (
        "com taxa baixa a perda não pode estourar")
    assert perdas[-1] > 1000, (
        "com taxa 0,001 a perda convergiu nos 200 passos — os dados mudaram? "
        "o sintoma esperado é 'devagar demais'")
    assert perdas[-1] < perdas[99], (
        "com taxa 0,001 a perda deveria AINDA estar caindo no passo 200")


# --- 4. a divergência (taxa 1,5) -------------------------------------------------

def test_com_taxa_1_5_a_perda_diverge_de_forma_visivel():
    x, y = esqueleto.gerar_dados()
    with np.errstate(over="ignore", invalid="ignore"):
        _, _, perdas = esqueleto.descida(x, y, taxa=1.5, passos=200)
    assert perdas[9] > perdas[0] * 100, (
        "com taxa 1,5 a perda deveria disparar já nas primeiras dezenas de "
        "passos — confira se as derivadas não invertem o sinal")
    assert not math.isfinite(perdas[-1]), (
        f"a última perda foi {perdas[-1]!r}; o sintoma do slide 12 é a perda "
        "subir até virar 'inf'/'nan'")


def test_com_passos_suficientes_o_inf_vira_nan():
    x, y = esqueleto.gerar_dados()
    with np.errstate(over="ignore", invalid="ignore"):
        _, _, perdas = esqueleto.descida(x, y, taxa=1.5, passos=350)
    assert any(math.isnan(p) for p in perdas), (
        "o 'vira não é número' do slide 13 não aconteceu nem em 350 passos")
