"""Testes do Laboratório 04 — a prova de que a tabela está certa.

Como usar (da pasta do laboratório):
    python -m pytest teste.py -q

Três famílias de teste:

  1. GABARITO — as quatro buscas sobre as três instâncias MAIOR do
     catálogo têm que reproduzir os números de `comum/MEDICOES.md`
     (custo, ações, expandidos, gerados, profundidade máxima). São
     determinísticos: se divergirem, algo mudou no motor ou no catálogo —
     pare e reporte, não "conserte" a tabela.
  2. A SUA FORMULAÇÃO (a constante `FORMULACAO` do `esqueleto.py`) — as
     quatro buscas encontram objetivo, e o custo uniforme nunca perde da
     largura em custo (slide 22: esse resultado é defeito de formulação —
     custo negativo ou transição que não é função).
  3. DESAFIO — se `USAR_IMPLEMENTACAO_PROPRIA` estiver em True, as suas
     duas buscas têm que bater com o motor nos três subproblemas do
     catálogo E na formulação apontada: mesmo custo, mesmo número de
     ações. No caminho padrão estes testes são pulados, sem penalidade.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

_AQUI = Path(__file__).resolve().parent


def _pasta_do_comum() -> Path:
    for pasta in (_AQUI, *_AQUI.parents):
        if (pasta / "comum" / "busca.py").is_file():
            return pasta / "comum"
    raise FileNotFoundError(
        "comum/busca.py não encontrado — extraia o pacote inteiro: a pasta "
        "comum/ viaja junto do laboratório.")


_pasta = str(_pasta_do_comum())
if _pasta not in sys.path:
    sys.path.insert(0, _pasta)

from busca import (  # noqa: E402
    aprofundamento_iterativo,
    busca_em_largura,
    comparar,
    custo_uniforme,
    profundidade_limitada,
)
from problemas import conformidade, consultas, diagnostico  # noqa: E402

_spec_esqueleto = importlib.util.spec_from_file_location(
    "esqueleto", _AQUI / "esqueleto.py")
esqueleto = importlib.util.module_from_spec(_spec_esqueleto)
sys.modules["esqueleto"] = esqueleto
_spec_esqueleto.loader.exec_module(esqueleto)  # type: ignore[union-attr]

LIMITE = esqueleto.LIMITE

# O gabarito de `comum/MEDICOES.md` (30/08/2026), instâncias MAIOR:
# problema -> busca -> (custo, ações, expandidos, gerados, prof. máx.)
GABARITO = {
    "diagnostico": {
        "largura": (20.0, 5, 2786, 6744, 5),
        "custo_uniforme": (20.0, 5, 550, 1954, 6),
        "profundidade_limitada": (20.0, 5, 6, 5, 5),
        "aprofundamento_iterativo": (20.0, 5, 1192, 3749, 5),
    },
    "consultas": {
        "largura": (20.0, 1, 11, 140, 2),
        "custo_uniforme": (17.1, 6, 1488, 2450, 7),
        "profundidade_limitada": (17.6, 7, 8, 28, 7),
        "aprofundamento_iterativo": (20.0, 1, 12, 10, 1),
    },
    "conformidade": {
        "largura": (44.0, 14, 20729, 20736, 14),
        "custo_uniforme": (30.0, 14, 20723, 20736, 14),
        "profundidade_limitada": (44.0, 14, 15, 14, 14),
        "aprofundamento_iterativo": (44.0, 14, 27231, 134798, 14),
    },
}
NOMES_DE_BUSCA = {
    "largura": "largura",
    "custo_uniforme": "custo_uniforme",
    "profundidade_limitada": f"profundidade_limitada(limite={LIMITE})",
    "aprofundamento_iterativo": f"aprofundamento_iterativo(limite={LIMITE})",
}

MAIORES = {
    "diagnostico": diagnostico.MAIOR,
    "consultas": consultas.MAIOR,
    "conformidade": conformidade.MAIOR,
}


def _medir(problema, busca):
    return busca(problema)


# --- 1. o gabarito ----------------------------------------------------------

@pytest.mark.parametrize("nome_problema", sorted(GABARITO))
def test_gabarito_das_instancias_maior(nome_problema):
    problema = MAIORES[nome_problema]
    medidos = {
        "largura": busca_em_largura(problema),
        "custo_uniforme": custo_uniforme(problema),
        "profundidade_limitada": profundidade_limitada(problema, LIMITE),
        "aprofundamento_iterativo": aprofundamento_iterativo(problema, LIMITE),
    }
    for nome, esperado in GABARITO[nome_problema].items():
        r = medidos[nome]
        obtido = (round(r.custo, 4), len(r.caminho), r.nos_expandidos,
                  r.nos_gerados, r.profundidade_maxima)
        assert obtido == esperado, (
            f"{nome_problema}.{nome}: obtido {obtido}, gabarito {esperado} "
            "(comum/MEDICOES.md). Divergência é defeito no motor ou no "
            "catálogo — reporte, não ajuste a tabela.")


# --- 2. a formulação apontada no esqueleto ----------------------------------

def _problema_da_formulacao():
    return esqueleto.carregar_formulacao(esqueleto.FORMULACAO)


def test_as_quatro_buscas_encontram_o_objetivo_da_formulacao():
    problema = _problema_da_formulacao()
    for busca in (busca_em_largura, custo_uniforme,
                  lambda p: profundidade_limitada(p, LIMITE),
                  lambda p: aprofundamento_iterativo(p, LIMITE)):
        r = busca(problema)
        assert r.encontrou, (
            f"{busca} não encontrou objetivo em {esqueleto.FORMULACAO}. "
            "Rode o teste de sanidade do laboratório 03 sobre a formulação: "
            "objetivo inatingível é formulação vazia.")


def test_custo_uniforme_nunca_perde_da_largura_em_custo():
    problema = _problema_da_formulacao()
    largura = busca_em_largura(problema)
    uniforme = custo_uniforme(problema)
    assert uniforme.custo <= largura.custo + 1e-9, (
        f"custo uniforme devolveu {uniforme.custo} e a largura {largura.custo}. "
        "Resultado impossível com formulação correta (slide 22: é defeito, "
        "não resultado — quase sempre custo negativo ou transição que não "
        "é função).")


def test_nenhum_custo_da_tabela_traz_float_sujo():
    problema = _problema_da_formulacao()
    for linha_dados in comparar(problema, limite_maximo=LIMITE):
        texto = str(linha_dados["custo"])
        assert "999999" not in texto, (
            f"a tabela imprime {texto} — o arredondamento do comparar() "
            "deveria ter livrado o float sujo")


# --- 3. o desafio ------------------------------------------------------------

@pytest.mark.skipif(
    not esqueleto.USAR_IMPLEMENTACAO_PROPRIA,
    reason="caminho padrão: as buscas próprias não foram implementadas "
           "(desafio). Preencha as TODOs do esqueleto.py e troque a "
           "constante para rodar esta família de testes.")
@pytest.mark.parametrize("nome_problema", sorted(MAIORES))
def test_minhas_buscas_batem_com_o_motor(nome_problema):
    problema = MAIORES[nome_problema]
    for minha, do_motor in (
        (esqueleto.minha_busca_em_largura, busca_em_largura),
        (esqueleto.meu_custo_uniforme, custo_uniforme),
    ):
        meu = minha(problema)
        motor = do_motor(problema)
        assert round(meu.custo, 4) == round(motor.custo, 4), (
            f"{nome_problema}: meu custo {meu.custo} ≠ motor {motor.custo}")
        assert len(meu.caminho) == len(motor.caminho), (
            f"{nome_problema}: {len(meu.caminho)} ações contra "
            f"{len(motor.caminho)} do motor — a minha busca não é a mesma")


@pytest.mark.skipif(
    not esqueleto.USAR_IMPLEMENTACAO_PROPRIA,
    reason="desafio não ativado — ver a família acima.")
def test_minhas_buscas_batem_na_formulacao_apontada():
    problema = _problema_da_formulacao()
    for minha, do_motor in (
        (esqueleto.minha_busca_em_largura, busca_em_largura),
        (esqueleto.meu_custo_uniforme, custo_uniforme),
    ):
        meu, motor = minha(problema), do_motor(problema)
        assert meu.encontrou and motor.encontrou
        assert round(meu.custo, 4) == round(motor.custo, 4)
