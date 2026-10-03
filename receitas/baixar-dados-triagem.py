"""Receita de dados do domínio TRIAGEM DE ATENDIMENTO — Customer Support Tickets.

Domínio: triagem de atendimento (FAQs e reclamações) · Dataset: "Customer
Support Ticket Dataset" (suraj520/customer-support-ticket-dataset no Kaggle)
— 29.807 chamados × 17 colunas (tipo, assunto, descrição, prioridade,
canal, satisfação...). Licença: CC0 — domínio público.

O texto livre (`Ticket Description`) é o que faz deste um domínio de
linguagem: ele alimenta a busca com RAG na disciplina de Engenharia de
Prompt e IA Generativa.

O Kaggle exige uma conta gratuita com token de API (kaggle.com/settings →
seção API → "Create New Token" — começa com KGAT_). Guarde-o no .env da
raiz do projeto, junto da chave do Gemini:
    KAGGLE_TOKEN=KGAT_...
A receita procura o token nesta ordem: (1) o .env da raiz, (2) a variável
de ambiente KAGGLE_TOKEN, (3) o ~/.kaggle/kaggle.json (formato antigo,
username + key).
Sem token? Baixe o zip à mão na página do dataset, salve como
dados/fonte.zip e rode de novo — a conversão é a mesma.

O que a receita produz (o contrato das disciplinas seguintes):
    dados/dataset.csv    — a tabela do seu domínio, carregável pelo Pandas
    dados/FONTE.md       — URL, data, licença, hash e contagem de linhas

Requer: pandas (já está no requirements do curso).

Uso (a partir da raiz do seu repositório):
    python baixar-dados.py             # baixa e converte se ainda não existir
    python baixar-dados.py --forcar    # refaz do zero
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent  # a receita vive na RAIZ do repositório
if RAIZ.name in ("receitas", "scripts"):  # rodando de dentro do pacote D1-00
    RAIZ = RAIZ.parent                    # o dados/ sobe para a raiz do projeto
PASTA_DADOS = RAIZ / "dados"

REF = "suraj520/customer-support-ticket-dataset"
URL_PAGINA = "https://www.kaggle.com/datasets/" + REF
URL_DOWNLOAD = "https://www.kaggle.com/api/v1/datasets/download/" + REF
MEMBRO = "customer_support_tickets.csv"
LICENCA = "CC0: Public Domain"
MAX_MB = 200.0           # teto de disco acordado no MAPA-DE-DATASETS
MAX_LINHAS = 50_000      # teto de memória (amostra sistemática se passar)
PISO_AO1_LINHAS = 500
BLOCO = 64 * 1024


class LimiteExcedido(RuntimeError):
    """A fonte passou do limite de disco acordado — recusar, não truncar."""


def ler_do_env(nome: str) -> str:
    """Lê NOME=valor do .env da raiz — o lar dos segredos do curso."""
    arquivo = RAIZ / ".env"
    if not arquivo.is_file():
        return ""
    for linha in arquivo.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if linha.startswith(nome + "="):
            return linha.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def autorizacao_kaggle() -> str | None:
    """Token novo: do .env da raiz, do ambiente, ou do kaggle.json antigo."""
    token = os.environ.get("KAGGLE_TOKEN", "").strip() or ler_do_env("KAGGLE_TOKEN")
    if token:
        return "Bearer " + token
    arquivo = Path.home() / ".kaggle" / "kaggle.json"
    if arquivo.is_file():
        conta = json.loads(arquivo.read_text(encoding="utf-8"))
        chave = conta.get("key", "")
        if chave.startswith("KGAT_"):
            return "Bearer " + chave
        par = f"{conta.get('username', '')}:{chave}".encode("utf-8")
        return "Basic " + base64.b64encode(par).decode("ascii")
    return None


def baixar_com_limite(url: str, destino: Path, max_mb: float,
                      autorizacao: str | None) -> int:
    """Baixa em blocos, abortando (e apagando) se passar do teto."""
    teto = int(max_mb * 1024 * 1024)
    pedido = urllib.request.Request(
        url, headers={"Authorization": autorizacao} if autorizacao else {})
    bytes_baixados = 0
    with urllib.request.urlopen(pedido, timeout=120) as resposta, \
            open(destino, "wb") as saida:
        while bloco := resposta.read(BLOCO):
            bytes_baixados += len(bloco)
            if bytes_baixados > teto:
                saida.close()
                destino.unlink(missing_ok=True)
                raise LimiteExcedido(
                    f"o download passou de {max_mb:g} MB sem acabar — recusado")
            saida.write(bloco)
    return bytes_baixados


def sha256_do(caminho: Path) -> str:
    digesto = hashlib.sha256()
    with open(caminho, "rb") as fh:
        while bloco := fh.read(BLOCO):
            digesto.update(bloco)
    return digesto.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(description="Dados do domínio triagem (tickets).")
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
    bytes_zip = 0
    if zip_local.is_file():
        bytes_zip = zip_local.stat().st_size
        print(f"Usando o zip que já está em {zip_local} (baixado à mão).")
    else:
        autorizacao = autorizacao_kaggle()
        if autorizacao is None:
            print("SEM TOKEN do Kaggle. Duas saídas:")
            print(f"  1. crie o token gratuito em kaggle.com/settings (seção API)")
            print("     e defina a variável de ambiente KAGGLE_TOKEN, ou")
            print(f"  2. baixe o zip à mão em {URL_PAGINA} e salve como {zip_local}.")
            print("Depois rode esta receita de novo.")
            return 1
        print(f"Baixando (limite {MAX_MB:g} MB): {URL_PAGINA}")
        try:
            bytes_zip = baixar_com_limite(URL_DOWNLOAD, zip_local, MAX_MB,
                                          autorizacao)
        except urllib.error.HTTPError as erro:
            zip_local.unlink(missing_ok=True)
            if erro.code in (401, 403):
                print(f"RECUSADO: HTTP {erro.code} — o token foi rejeitado. "
                      "Gere outro em kaggle.com/settings → API.")
            else:
                print(f"ERRO: HTTP {erro.code} no download do Kaggle.")
            return 1
        except LimiteExcedido as erro:
            print(f"RECUSADO: {erro}")
            return 1
    hash_zip = sha256_do(zip_local)

    with zipfile.ZipFile(zip_local) as z:
        nomes = z.namelist()
        nome_csv = MEMBRO if MEMBRO in nomes else (
            nomes[0] if len(nomes) == 1 else None)
        if nome_csv is None:
            print(f"RECUSADO: esperava '{MEMBRO}' no zip; achei {nomes}. "
                  "Apague dados/fonte.zip e rode de novo.")
            return 1
        with z.open(nome_csv) as fh:
            df = pd.read_csv(fh)

    brutas = len(df)
    amostra = ""
    if brutas > MAX_LINHAS:
        passo = brutas // MAX_LINHAS
        df = df.iloc[::passo].head(MAX_LINHAS)  # linha 0 e uma a cada passo
        amostra = (f" → {len(df)} mantidas (amostra sistemática, "
                   f"1 a cada {passo})")
    if len(df) < PISO_AO1_LINHAS:
        print(f"ERRO: {len(df)} linhas — abaixo do piso de "
              f"{PISO_AO1_LINHAS} do AO1.")
        return 1
    df.to_csv(csv_final, index=False)

    fonte_md.write_text(
        f"# FONTE — dataset do domínio triagem de atendimento\n\n"
        f"- **URL:** {URL_PAGINA}\n"
        f"- **Data do download:** "
        f"{datetime.now(timezone.utc).date().isoformat()}\n"
        f"- **Licença:** {LICENCA}\n"
        f"- **Bytes do zip:** {bytes_zip} · **SHA-256:** {hash_zip}\n"
        f"- **Registros:** {brutas} linhas × {len(df.columns)} colunas"
        f"{amostra}\n"
        f"- **Limites:** download ≤ {MAX_MB:g} MB · linhas ≤ "
        f"{MAX_LINHAS:,}\n",
        encoding="utf-8")
    zip_local.unlink(missing_ok=True)
    print(f"Pronto: {csv_final} ({len(df)} linhas) + {fonte_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
