"""Carregamento, validação e preparação do dataset de manutenção.

Regras deste módulo:

1. Nunca depende de download: se `data/raw/` não tem o arquivo, cai
   automaticamente em `data/amostra/` (200 linhas versionadas).
2. Sempre valida antes de devolver: um DataFrame com colunas faltando ou
   valores fora da faixa física é bug de dados, não de análise.
3. Diz de onde veio: a função devolve também a fonte usada, porque a
   proveniência dos dados é parte da análise.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from pydantic import ValidationError

from ams.modelos import LeituraSensor

RAIZ_DO_PACOTE = Path(__file__).resolve().parent.parent.parent

COLUNAS = {
    "UDI": "udi",
    "Product ID": "product_id",
    "Type": "tipo",
    "Air temperature [K]": "temperatura_ar",
    "Process temperature [K]": "temperatura_processo",
    "Rotational speed [rpm]": "rotacao",
    "Torque [Nm]": "torque",
    "Tool wear [min]": "desgaste",
    "Machine failure": "falha",
    "TWF": "twf",
    "HDF": "hdf",
    "PWF": "pwf",
    "OSF": "osf",
    "RNF": "rnf",
}
DTYPES = {
    "udi": "int64",
    "product_id": "string",
    "tipo": "string",
    "temperatura_ar": "float64",
    "temperatura_processo": "float64",
    "rotacao": "int64",
    "torque": "float64",
    "desgaste": "int64",
}


class ErroDados(ValueError):
    """Erro de estrutura ou conteúdo do dataset, com resumo em português."""


@dataclass(frozen=True)
class Dataset:
    """DataFrame validado + a origem dele."""

    quadro: pd.DataFrame
    fonte: str  # "data/raw (10.000 linhas)" | "data/amostra (200 linhas)"
    caminho: Path


def caminho_dataset(raiz: Path | None = None) -> Path:
    """Decide qual CSV usar: o completo em data/raw, ou a amostra versionada.

    Raises:
        ErroDados: se nenhum dos dois existir (rode scripts/baixar-dados.py).
    """
    base = raiz or RAIZ_DO_PACOTE
    bruto = base / "data" / "raw" / "ai4i2020.csv"
    amostra = base / "data" / "amostra" / "ai4i2020.csv"
    if bruto.exists():
        return bruto
    if amostra.exists():
        return amostra
    raise ErroDados(
        "nenhum dataset encontrado: rode `python scripts/baixar-dados.py` "
        "para baixar (com fallback offline)."
    )


def carregar(caminho: Path | None = None, validar_com_pydantic: bool = True) -> Dataset:
    """Carrega o dataset de manutenção como DataFrame tipado e validado.

    Args:
        caminho: CSV a ler; se omitido, resolve sozinho (raw → amostra).
        validar_com_pydantic: valida cada linha contra `LeituraSensor`.
            Custo: ~1 s para 10.000 linhas. Desligue só em exploração
            interativa, nunca em código de produção.

    Returns:
        Dataset com o DataFrame (colunas renomeadas para português, dtypes
        corretos, flags como bool) e a fonte usada.

    Raises:
        ErroDados: colunas erradas, valores fora de faixa ou tipos
            impossíveis — a mensagem diz a primeira ocorrência.
    """
    caminho = caminho or caminho_dataset()
    # utf-8-sig: o CSV oficial vem com BOM UTF-8; sem isso a primeira coluna
    # apareceria como '\ufeffUDI' e o renome abaixo falharia.
    quadro = pd.read_csv(caminho, encoding="utf-8-sig")

    faltando = [coluna for coluna in COLUNAS if coluna not in quadro.columns]
    if faltando:
        raise ErroDados(
            f"colunas ausentes no CSV ({', '.join(faltando)}). "
            f"Arquivo: {caminho}. Rode scripts/baixar-dados.py --forcar."
        )

    quadro = quadro.rename(columns=COLUNAS)

    # flags 0/1 → bool (dataset original usa inteiros)
    for coluna in ("falha", "twf", "hdf", "pwf", "osf", "rnf"):
        quadro[coluna] = quadro[coluna].astype(bool)

    try:
        quadro = quadro.astype(DTYPES)
    except (ValueError, TypeError) as erro:
        raise ErroDados(f"valor não numérico onde número era esperado: {erro}") from erro

    if validar_com_pydantic:
        _validar_com_modelos(quadro, caminho)

    quadro["tipo"] = quadro["tipo"].astype("category")
    fonte = f"{caminho.parent.name}/{caminho.name} ({len(quadro)} linhas)"
    return Dataset(quadro=quadro, fonte=fonte, caminho=caminho)


def _validar_com_modelos(quadro: pd.DataFrame, caminho: Path) -> None:
    """Valida todas as linhas contra o modelo Pydantic do domínio.

    Na primeira linha inválida, levanta ErroDados com a mensagem em
    português do validador — a política é falhar rápido e explicar.
    """
    registros = quadro.drop(columns=["tipo"]).to_dict("records")
    try:
        # TypeAdapter-free: construímos direto, em lote, para velocidade
        for indice, registro in enumerate(registros):
            registro["tipo"] = quadro["tipo"].iloc[indice]
            LeituraSensor(**registro)
    except ValidationError as erro:
        primeiro = erro.errors()[0]
        linha = indice + 2  # +2: header + base 1
        campo = primeiro["loc"][0]
        mensagem = primeiro["msg"]
        raise ErroDados(
            f"linha {linha} do CSV rejeitada pelo validador (campo '{campo}': "
            f"{mensagem}). Arquivo: {caminho}. Confira a fonte dos dados."
        ) from erro


def preparar(quadro: pd.DataFrame) -> pd.DataFrame:
    """Acrescenta as colunas derivadas usadas na análise e pelos modos de falha.

    Colunas criadas:
        delta_temperatura: processo − ar [K] (limiar de HDF é 8,6 K)
        potencia_kw: torque × rotação convertida em potência [kW]
        algum_modo: pelo menos um dos cinco modos de falha marcado
    """
    derivado = quadro.copy()
    derivado["delta_temperatura"] = derivado["temperatura_processo"] - derivado["temperatura_ar"]
    # potência [W] = torque [Nm] × ω [rad/s]; rpm → rad/s multiplicando 2π/60
    omega = derivado["rotacao"] * (2.0 * 3.141592653589793 / 60.0)
    derivado["potencia_kw"] = derivado["torque"] * omega / 1000.0
    derivado["algum_modo"] = (
        derivado[["twf", "hdf", "pwf", "osf", "rnf"]].any(axis=1)
    )
    return derivado
