"""Receita de dados do domínio CRÉDITO — baixa, converte e registra.

Domínio: crédito ou fraude · Dataset: UCI "Default of Credit Card Clients"
(ID 350) — 30.000 registros × 24 colunas, licença CC BY 4.0 (confira o cartão
do dataset no UCI). Limite respeitado: 5,5 MB de download, bem abaixo do teto
de 200 MB, e 30.000 linhas na memória, abaixo do teto de 50.000.

O que a receita produz (o contrato das disciplinas seguintes):
    dados/dataset.csv    — a tabela do seu domínio, carregável pelo Pandas
    dados/FONTE.md       — URL, data, licença, hash e contagem de linhas

Requer: pandas e xlrd (leitor do formato .xls antigo):
    pip install pandas xlrd

Uso (a partir da raiz do seu repositório):
    python baixar-dados.py             # baixa e converte se ainda não existir
    python baixar-dados.py --forcar    # refaz do zero
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# Emojis e acentos precisam sobreviver ao console do Windows mesmo quando a
# saída é redirecionada para arquivo (o PowerShell às vezes usa cp1252 aí).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent  # a receita vive na RAIZ do repositório
if RAIZ.name in ("receitas", "scripts"):  # rodando de dentro do pacote D1-00
    RAIZ = RAIZ.parent                    # o dados/ sobe para a raiz do projeto
PASTA_DADOS = RAIZ / "dados"

URL_ZIP = ("https://archive.ics.uci.edu/static/public/350/"
           "default+of+credit+card+clients.zip")
LICENCA = "CC BY 4.0 (confira o cartão do dataset no UCI)"
MAX_MB = 200.0           # teto de disco acordado no MAPA-DE-DATASETS
MAX_LINHAS = 50_000      # teto de memória (amostra sistemática se passar)
BLOCO = 64 * 1024


class LimiteExcedido(RuntimeError):
    """A fonte passou do limite de disco acordado — recusar, não truncar."""


def baixar_com_limite(url: str, destino: Path, max_mb: float) -> int:
    """Baixa em blocos, abortando (e apagando) se passar do teto."""
    teto = int(max_mb * 1024 * 1024)
    bytes_baixados = 0
    with urllib.request.urlopen(url, timeout=60) as resposta, \
            open(destino, "wb") as saida:
        while bloco := resposta.read(BLOCO):
            bytes_baixados += len(bloco)
            if bytes_baixados > teto:
                saida.close()
                destino.unlink(missing_ok=True)
                raise LimiteExcedido(
                    f"o download passou de {max_mb:g} MB sem acabar — recusado"
                )
            saida.write(bloco)
    return bytes_baixados


def sha256_do(caminho: Path) -> str:
    digesto = hashlib.sha256()
    with open(caminho, "rb") as fh:
        while bloco := fh.read(BLOCO):
            digesto.update(bloco)
    return digesto.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description="Dados do domínio crédito (UCI 350).")
    p.add_argument("--forcar", action="store_true",
                   help="refaz mesmo se dados/dataset.csv já existir")
    argumentos = p.parse_args()

    csv_final = PASTA_DADOS / "dataset.csv"
    fonte_md = PASTA_DADOS / "FONTE.md"
    if csv_final.is_file() and not argumentos.forcar:
        print(f"{csv_final} já existe — nada a fazer (use --forcar para refazer).")
        return 0

    import pandas as pd  # dentro do main: a receita só importa se for rodar

    PASTA_DADOS.mkdir(exist_ok=True)
    zip_local = PASTA_DADOS / "fonte.zip"
    print(f"Baixando (limite {MAX_MB:g} MB): {URL_ZIP}")
    bytes_zip = baixar_com_limite(URL_ZIP, zip_local, MAX_MB)
    hash_zip = sha256_do(zip_local)

    with zipfile.ZipFile(zip_local) as z:
        nome_xls = z.namelist()[0]
        z.extract(nome_xls, PASTA_DADOS)
    xls = PASTA_DADOS / nome_xls

    print("Convertendo .xls → .csv (pandas + xlrd)...")
    df = pd.read_excel(xls, skiprows=1)
    df.to_csv(csv_final, index=False)

    if len(df) < 500:
        print(f"ERRO: {len(df)} linhas — abaixo do piso de 500 do AO1.")
        return 1

    fonte_md.write_text(
        f"# FONTE — dataset do domínio crédito\n\n"
        f"- **URL:** {URL_ZIP}\n"
        f"- **Data do download:** "
        f"{datetime.now(timezone.utc).date().isoformat()}\n"
        f"- **Licença:** {LICENCA}\n"
        f"- **Bytes do zip:** {bytes_zip} · **SHA-256:** {hash_zip}\n"
        f"- **Registros:** {len(df)} linhas × {len(df.columns)} colunas\n"
        f"- **Limites:** download ≤ {MAX_MB:g} MB · linhas ≤ {MAX_LINHAS:,} "
        f"(nenhum teto foi atingido — dados completos)\n",
        encoding="utf-8",
    )
    xls.unlink(missing_ok=True)
    zip_local.unlink(missing_ok=True)
    print(f"Pronto: {csv_final} ({len(df)} linhas) + {fonte_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
