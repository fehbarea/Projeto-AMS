"""Testes do Laboratório 03 — a prova de que a formulação está de pé.

Como usar (da pasta do laboratório):
    python -m pytest teste.py -q

O que é testado:
  1. a SOLUÇÃO passa nas seis verificações do teste de sanidade;
  2. os TRÊS subproblemas do catálogo (instâncias pequenas e maiores)
     passam nas seis — o teste de sanidade não pode acusar defeito em
     formulação que se sabe boa;
  3. cada um dos seis defeitos clássicos de formulação ACENDE a verificação
     correspondente — um teste de sanidade que nunca acusa não testa nada;
  4. o carregador `arquivo.py:ATRIBUTO` acha o problema certo.
"""

from __future__ import annotations

import importlib.util
import random
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

_especificacao = importlib.util.spec_from_file_location(
    "verificar-formulacao", _AQUI / "verificar-formulacao.py")
vf = importlib.util.module_from_spec(_especificacao)
sys.modules["verificar-formulacao"] = vf
_especificacao.loader.exec_module(vf)  # type: ignore[union-attr]

from problemas import conformidade, consultas, diagnostico  # noqa: E402


def _carregar_solucao():
    """A SOLUÇÃO não viaja no pacote do aluno (regra do empacotador) — o
    teste dela só roda na árvore de trabalho, onde o arquivo existe."""
    caminho = _AQUI / "solucao.py"
    if not caminho.is_file():
        pytest.skip("solucao.py não está aqui — teste de solução roda na "
                    "árvore de trabalho, não no pacote")
    spec = importlib.util.spec_from_file_location("solucao", caminho)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["solucao"] = modulo
    spec.loader.exec_module(modulo)  # type: ignore[union-attr]
    return modulo


def _seis_verdes(problema) -> None:
    relatos = vf.verificar(problema)
    vermelhas = [a for a in relatos if not a.ok and not a.aviso]
    amarelas = [a for a in relatos if a.aviso]
    assert not vermelhas, [a.mensagem for a in vermelhas]
    assert not amarelas, [a.mensagem for a in amarelas]
    assert len(relatos) == 6


def test_solucao_passa_nas_seis_verificacoes():
    _seis_verdes(_carregar_solucao().PEDIDOS)


def test_os_tres_do_catalogo_passam_nas_seis():
    for modulo in (diagnostico, consultas, conformidade):
        _seis_verdes(modulo.PEQUENA)
        _seis_verdes(modulo.MAIOR)


# --- os seis defeitos, um por verificação ---------------------------------


class _GuardaCaminho:
    """O erro do slide 47: o estado é a trilha, ordenada ou não... aqui não."""

    def __init__(self) -> None:
        self.estado_inicial = ()

    def acoes(self, s):
        return [a for a in ("p", "q", "r") if a not in s]

    def transicao(self, s, a):
        return s + (a,)          # sem ordenar: dois caminhos, estados distintos

    def objetivo(self, s):
        return {"p", "q"} <= set(s)

    def custo(self, s, a, t):
        return 1.0


class _CustoNegativo:
    def __init__(self) -> None:
        self.estado_inicial = 0

    def acoes(self, s):
        return ["andar"] if s < 3 else []

    def transicao(self, s, a):
        return s + 1

    def objetivo(self, s):
        return s >= 3

    def custo(self, s, a, t):
        return -2.0


class _TransicaoNaoFuncao:
    def __init__(self) -> None:
        self.estado_inicial = 0

    def acoes(self, s):
        return ["moeda"]

    def transicao(self, s, a):
        return s + 1 if random.random() < 0.9 else s + 5

    def objetivo(self, s):
        return s >= 5

    def custo(self, s, a, t):
        return 1.0


class _AcoesInstaveis:
    def __init__(self) -> None:
        self.estado_inicial = 0

    def acoes(self, s):
        return random.sample(["p", "q", "r"], 3)

    def transicao(self, s, a):
        return s + 1

    def objetivo(self, s):
        return s >= 3

    def custo(self, s, a, t):
        return 1.0


class _ObjetivoInatingivel:
    def __init__(self) -> None:
        self.estado_inicial = 0

    def acoes(self, s):
        return ["andar"] if s < 2 else []

    def transicao(self, s, a):
        return s + 1

    def objetivo(self, s):
        return s >= 99

    def custo(self, s, a, t):
        return 1.0


class _EstadoNaoHashable:
    def __init__(self) -> None:
        self.estado_inicial = []

    def acoes(self, s):
        return ["p", "q"]

    def transicao(self, s, a):
        return s + [a]

    def objetivo(self, s):
        return len(s) >= 2

    def custo(self, s, a, t):
        return 1.0


def _relato(problema, numero: int):
    return vf.verificar(problema)[numero - 1]


def test_verificacao_6_acusa_o_estado_que_guarda_caminho():
    relato = _relato(_GuardaCaminho(), 6)
    assert relato.aviso, "o estado-trilha tem que acender o aviso da 6"
    assert "situação" in relato.mensagem


def test_verificacao_4_acusa_o_custo_negativo():
    relato = _relato(_CustoNegativo(), 4)
    assert not relato.ok and not relato.aviso
    assert "otimalidade" in relato.mensagem


def test_verificacao_2_acusa_a_transicao_que_nao_e_funcao():
    random.seed(1)
    relato = _relato(_TransicaoNaoFuncao(), 2)
    assert not relato.ok and not relato.aviso
    assert "determinística" in relato.mensagem


def test_verificacao_3_acusa_as_acoes_instaveis():
    random.seed(7)
    relato = _relato(_AcoesInstaveis(), 3)
    assert not relato.ok and not relato.aviso
    assert "ordem estável" in relato.mensagem


def test_verificacao_5_acusa_o_objetivo_inatingivel():
    relato = _relato(_ObjetivoInatingivel(), 5)
    assert not relato.ok and not relato.aviso
    assert "vazia" in relato.mensagem


def test_verificacao_1_acusa_o_estado_sem_hash():
    relato = _relato(_EstadoNaoHashable(), 1)
    assert not relato.ok and not relato.aviso
    assert "tuple/frozenset" in relato.mensagem


# --- o carregador ----------------------------------------------------------

def test_carregador_acha_por_arquivo_e_atributo():
    # o carregador re-executa o arquivo: é OUTRA instância, do mesmo tipo
    _carregar_solucao()
    problema = vf.carregar_problema(str(_AQUI / "solucao.py") + ":PEDIDOS")
    assert type(problema).__name__ == "DiagnosticoPedidos"
    _seis_verdes(problema)


def test_carregador_acha_o_unico_candidato(tmp_path):
    modulo = tmp_path / "unico.py"
    modulo.write_text(
        "class SoTemUm:\n"
        "    estado_inicial = 0\n"
        "    def acoes(self, s):\n        return []\n"
        "    def transicao(self, s, a):\n        return s\n"
        "    def objetivo(self, s):\n        return True\n"
        "    def custo(self, s, a, t):\n        return 0.0\n",
        encoding="utf-8")
    problema = vf.carregar_problema(str(modulo))
    assert (isinstance(problema, type) and problema.__name__ == "SoTemUm")
    relatos = vf.verificar(problema())
    assert all(r.ok for r in relatos)


def test_carregador_recusa_ambiguidade_com_mensagem(tmp_path):
    modulo = tmp_path / "dois.py"
    modulo.write_text(
        "class Base:\n"
        "    estado_inicial = 0\n"
        "    def acoes(self, s):\n        return []\n"
        "    def transicao(self, s, a):\n        return s\n"
        "    def objetivo(self, s):\n        return True\n"
        "    def custo(self, s, a, t):\n        return 0.0\n"
        "UM = Base()\n"
        "OUTRO = Base()\n",
        encoding="utf-8")
    try:
        vf.carregar_problema(str(modulo))
    except ValueError as erro:
        assert "aponte o atributo" in str(erro)
    else:
        raise AssertionError("dois candidatos sem atributo devia falhar")
