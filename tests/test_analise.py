"""Testes das agregações usadas na exploração."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from ams.analise import (
    acuracia_regra_desgaste,
    correlacao_torque_rotacao,
    falhas_sem_modo,
    frequencia_de_modos,
    melhor_limiar_desgaste,
    taxa_falha_geral,
    taxa_falha_por_tipo,
)
from ams.dados import carregar


def quadro_de_teste(csv_valido: Path) -> pd.DataFrame:
    return carregar(csv_valido, validar_com_pydantic=False).quadro


def test_taxa_falha_geral(csv_valido: Path) -> None:
    # o CSV do conftest tem 1 falha em 3 linhas
    assert taxa_falha_geral(quadro_de_teste(csv_valido)) == pytest.approx(1 / 3)


def test_taxa_falha_por_tipo_tem_as_tres_categorias(csv_valido: Path) -> None:
    serie = taxa_falha_por_tipo(quadro_de_teste(csv_valido))
    assert set(serie.index) == {"L", "M"}
    assert (serie >= 0).all() and (serie <= 100).all()


def test_frequencia_de_modos_cobre_os_cinco(csv_valido: Path) -> None:
    serie = frequencia_de_modos(quadro_de_teste(csv_valido))
    assert list(serie.index) == ["twf", "hdf", "pwf", "osf", "rnf"]
    assert serie["osf"] == 1  # a linha de falha do conftest é OSF


def test_falhas_sem_modo_identifica_discordancia(csv_valido: Path) -> None:
    quadro = quadro_de_teste(csv_valido)
    # nenhuma no CSV base; criamos uma na mão para o teste da lição de dados
    quadro.loc[quadro.index[-1], "falha"] = True
    sem_modo = falhas_sem_modo(quadro)
    assert len(sem_modo) == 1
    assert sem_modo.iloc[0]["udi"] == 3


def test_acuracia_da_regra_extrema(csv_valido: Path) -> None:
    quadro = quadro_de_teste(csv_valido)
    # limiar além do máximo: prevê 'nunca falha' ⇒ acerta 2 de 3
    assert acuracia_regra_desgaste(quadro, limiar=1_000) == pytest.approx(2 / 3)


def test_melhor_limiar_retorna_par_consistente(csv_valido: Path) -> None:
    limiar, acuracia = melhor_limiar_desgaste(quadro_de_teste(csv_valido))
    assert 0 <= limiar <= 300
    assert acuracia >= acuracia_regra_desgaste(quadro_de_teste(csv_valido), limiar=1_000)


def test_correlacao_torque_rotacao_negativa_no_dataset_oficial() -> None:
    """No dataset oficial (10.000 linhas) a correlação é fortemente negativa.

    Roda só se data/raw existir na máquina (o CI/limpo pula — a relação
    física é testada indiretamente nos outros testes).
    """
    from ams.dados import RAIZ_DO_PACOTE

    if not (RAIZ_DO_PACOTE / "data" / "raw" / "ai4i2020.csv").exists():

        pytest.skip("dataset completo não baixado nesta máquina")
    quadro = carregar(validar_com_pydantic=False).quadro
    assert correlacao_torque_rotacao(quadro) < -0.5
