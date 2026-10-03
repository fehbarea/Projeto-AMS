"""Fixtures compartilhadas pelos testes do AMS.

Nenhum teste toca a rede ou depende do download: o CSV de teste é criado
em disco temporário pelo próprio conftest, com a mesma estrutura do
dataset oficial (colunas em inglês e BOM, como no arquivo do UCI).
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

import pytest

# Uma linha válida canônica, na forma das colunas originais do CSV do UCI
LINHA_VALIDA = {
    "UDI": "1",
    "Product ID": "M14860",
    "Type": "M",
    "Air temperature [K]": "298.1",
    "Process temperature [K]": "308.6",
    "Rotational speed [rpm]": "1551",
    "Torque [Nm]": "42.8",
    "Tool wear [min]": "0",
    "Machine failure": "0",
    "TWF": "0",
    "HDF": "0",
    "PWF": "0",
    "OSF": "0",
    "RNF": "0",
}

COLUNAS_ORIGINAIS = list(LINHA_VALIDA)


def gerar_csv(linhas: list[dict[str, str]], caminho: Path) -> Path:
    """Grava um CSV de teste com as colunas originais do dataset e BOM UTF-8."""
    buffer = io.StringIO()
    escritor = csv.DictWriter(buffer, fieldnames=COLUNAS_ORIGINAIS)
    escritor.writeheader()
    escritor.writerows(linhas)
    # utf-8-sig grava com BOM, imitando o arquivo oficial do UCI
    caminho.write_text(buffer.getvalue(), encoding="utf-8-sig")
    return caminho


@pytest.fixture
def leitura_valida() -> dict[str, object]:
    """Dicionário com os campos de uma LeituraSensor válida."""
    return {
        "udi": 1,
        "product_id": "M14860",
        "tipo": "M",
        "temperatura_ar": 298.1,
        "temperatura_processo": 308.6,
        "rotacao": 1551,
        "torque": 42.8,
        "desgaste": 0,
        "falha": False,
        "twf": False,
        "hdf": False,
        "pwf": False,
        "osf": False,
        "rnf": False,
    }


@pytest.fixture
def csv_valido(tmp_path: Path) -> Path:
    """CSV temporário com 3 linhas válidas, incluindo uma com falha."""
    falha = dict(LINHA_VALIDA)
    falha.update({"UDI": "2", "Machine failure": "1", "OSF": "1", "Tool wear [min]": "220"})
    outra = dict(LINHA_VALIDA)
    outra.update({"UDI": "3", "Type": "L", "Product ID": "L47181"})
    return gerar_csv([LINHA_VALIDA, falha, outra], tmp_path / "ai4i2020.csv")
