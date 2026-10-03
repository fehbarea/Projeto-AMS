"""Testes de carregamento e validação do dataset."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from conftest import LINHA_VALIDA, gerar_csv

from ams.dados import ErroDados, caminho_dataset, carregar, preparar


def test_carrega_csv_valido(csv_valido: Path) -> None:
    dataset = carregar(csv_valido)
    assert len(dataset.quadro) == 3
    # colunas renomeadas para português
    assert "temperatura_ar" in dataset.quadro.columns
    assert "falha" in dataset.quadro.columns
    # flags viram bool
    assert dataset.quadro["falha"].dtype == bool
    assert dataset.quadro["osf"].dtype == bool
    assert bool(dataset.quadro.loc[1, "falha"]) is True


def test_carrega_com_bom_utf8(csv_valido: Path) -> None:
    """O CSV oficial vem com BOM — a leitura não pode vazar '\\ufeff' no nome."""
    dataset = carregar(csv_valido)
    assert not any(coluna.startswith("﻿") for coluna in dataset.quadro.columns)


def test_rejeita_csv_com_coluna_faltando(tmp_path: Path) -> None:
    linhas = [dict(LINHA_VALIDA)]
    caminho = gerar_csv(linhas, tmp_path / "ai4i2020.csv")
    quadro = pd.read_csv(caminho, encoding="utf-8-sig").drop(columns=["RNF"])
    quadro.to_csv(caminho, index=False)
    with pytest.raises(ErroDados, match="colunas ausentes"):
        carregar(caminho)


def test_rejeita_linha_fora_da_faixa(tmp_path: Path) -> None:
    impossivel = dict(LINHA_VALIDA)
    impossivel["Torque [Nm]"] = "-50"  # torque negativo
    caminho = gerar_csv([LINHA_VALIDA, impossivel], tmp_path / "ai4i2020.csv")
    with pytest.raises(ErroDados, match="linha 3"):
        carregar(caminho)


def test_fallback_para_amostra(tmp_path: Path, csv_valido: Path) -> None:
    """Sem data/raw, o caminho resolvido deve ser a amostra versionada."""
    (tmp_path / "data" / "amostra").mkdir(parents=True)
    destino = tmp_path / "data" / "amostra" / "ai4i2020.csv"
    destino.write_bytes(csv_valido.read_bytes())
    resolvido = caminho_dataset(tmp_path)
    assert resolvido == destino


def test_erro_claro_sem_nenhum_dado(tmp_path: Path) -> None:
    with pytest.raises(ErroDados, match="baixar-dados"):
        caminho_dataset(tmp_path)


def test_preparar_acrescenta_colunas_derivadas(csv_valido: Path) -> None:
    dataset = carregar(csv_valido, validar_com_pydantic=False)
    derivado = preparar(dataset.quadro)
    assert {"delta_temperatura", "potencia_kw", "algum_modo"} <= set(derivado.columns)
    linha = derivado.iloc[0]
    assert linha["delta_temperatura"] == pytest.approx(308.6 - 298.1)
    # potência esperada para a linha canônica: 42,8 Nm × 1551 rpm
    esperada_kw = 42.8 * (1551 * 2 * 3.141592653589793 / 60) / 1000
    assert linha["potencia_kw"] == pytest.approx(esperada_kw, rel=1e-6)
    assert bool(linha["algum_modo"]) is False


def test_validacao_pydantic_rapida_o_suficiente(csv_valido: Path) -> None:
    """A validação completa de 10 mil linhas precisa custar poucos segundos.

    Usa o CSV de 3 linhas replicado para medir por linha (tolerância ampla
    para máquinas lentas de CI).
    """
    import time

    quadro = pd.read_csv(csv_valido, encoding="utf-8-sig")
    grande = pd.concat([quadro] * 334, ignore_index=True)  # ~1000 linhas
    caminho = csv_valido.with_name("grande.csv")
    grande.to_csv(caminho, index=False, encoding="utf-8-sig")

    inicio = time.perf_counter()
    carregar(caminho)
    decorrido = time.perf_counter() - inicio
    # 1.000 linhas em menos de ~3 s ⇒ 10.000 em menos de ~30 s no pior caso;
    # na prática fica em ~1 s para o dataset inteiro.
    assert decorrido < 3.0, f"validação lenta demais: {decorrido:.2f} s para 1.000 linhas"
