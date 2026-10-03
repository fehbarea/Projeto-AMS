"""Testes dos modelos Pydantic do domínio."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ams.modelos import AvaliacaoRisco, LeituraSensor, NivelRisco, OrdemServico


def test_leitura_valida_aceita(leitura_valida: dict) -> None:
    leitura = LeituraSensor(**leitura_valida)
    assert leitura.tipo == "M"
    assert leitura.temperatura_processo > leitura.temperatura_ar


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("temperatura_ar", 0.0),  # zero absoluto é impossível em planta
        ("temperatura_processo", 999.0),
        ("rotacao", -100),
        ("torque", -5.0),  # torque negativo é fisicamente impossível aqui
        ("desgaste", 10_000),
    ],
)
def test_rejeita_valores_fora_da_faixa(leitura_valida: dict, campo: str, valor: object) -> None:
    with pytest.raises(ValidationError) as erro:
        LeituraSensor(**{**leitura_valida, campo: valor})
    # a mensagem de erro precisa estar em português para o técnico entender
    assert "fora da faixa" in str(erro.value) or "impossível" in str(erro.value)


def test_rejeita_processo_menor_que_ar(leitura_valida: dict) -> None:
    leitura_valida["temperatura_ar"] = 308.6
    leitura_valida["temperatura_processo"] = 300.0
    with pytest.raises(ValidationError, match="trocadas"):
        LeituraSensor(**leitura_valida)


def test_rejeita_tipo_desconhecido(leitura_valida: dict) -> None:
    with pytest.raises(ValidationError):
        LeituraSensor(**{**leitura_valida, "tipo": "X"})


def test_ordem_servico_valida(leitura_valida: dict) -> None:
    ordem = OrdemServico(
        identificador="OS-2026-0001",
        maquina="M14860",
        leitura=LeituraSensor(**leitura_valida),
        descricao="Substituição da ferramenta de corte do eixo 3",
    )
    assert ordem.identificador == "OS-2026-0001"
    assert ordem.leitura.torque == pytest.approx(42.8)


@pytest.mark.parametrize(
    ("descricao", "espera_erro"),
    [
        ("Revisão geral do cabeçote e troca do rolamento", False),
        ("curta", True),  # descrição com menos de 10 caracteres
        ("   ", True),
    ],
)
def test_valida_descricao_da_ordem(leitura_valida: dict, descricao: str, espera_erro: bool) -> None:
    kwargs = {
        "identificador": "OS-2026-0002",
        "maquina": "M14860",
        "leitura": LeituraSensor(**leitura_valida),
        "descricao": descricao,
    }
    if espera_erro:
        with pytest.raises(ValidationError):
            OrdemServico(**kwargs)
    else:
        OrdemServico(**kwargs)


def test_avaliacao_risco_valida() -> None:
    parecer = AvaliacaoRisco(
        nivel_risco="medio",
        justificativa="Desgaste da ferramenta avançado com torque elevado.",
        normas_aplicaveis=["NR-12"],
        requer_bloqueio=True,
        confianca=0.82,
    )
    assert parecer.nivel_risco is NivelRisco.MEDIO
    assert parecer.requer_bloqueio is True


def test_avaliacao_rejeita_confianca_fora_de_0_a_1() -> None:
    with pytest.raises(ValidationError):
        AvaliacaoRisco(
            nivel_risco="alto",
            justificativa="Risco elevado por sobrecarga detectada.",
            normas_aplicaveis=["NR-12"],
            requer_bloqueio=True,
            confianca=1.5,
        )


def test_avaliacao_rejeita_justificativa_demais_longas() -> None:
    with pytest.raises(ValidationError):
        AvaliacaoRisco(
            nivel_risco="alto",
            justificativa="x" * 301,
            normas_aplicaveis=["NR-12"],
            requer_bloqueio=False,
            confianca=0.5,
        )


def test_avaliacao_rejeita_lista_vazia_de_normas() -> None:
    with pytest.raises(ValidationError):
        AvaliacaoRisco(
            nivel_risco="baixo",
            justificativa="Operação de rotina sem indício de risco.",
            normas_aplicaveis=[],
            requer_bloqueio=False,
            confianca=0.9,
        )
