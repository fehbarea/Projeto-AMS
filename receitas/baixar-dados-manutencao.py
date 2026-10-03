"""Receita de dados do domínio MANUTENÇÃO INDUSTRIAL — UCI 447 ou UCI 179.

Domínio: manutenção industrial · Atenção: NÃO é o AI4I 2020 (dataset do
exemplo AMS da disciplina, proibido no AO1). Dois conjuntos à escolha:

    hidraulico  — "Condition monitoring of hydraulic systems" (UCI 447):
        2.205 ciclos; o zip tem 76,6 MB com perfis de sensor (séries de até
        6.000 amostras por ciclo) que a receita lê DIRETO do zip e resume
        na média por ciclo → dataset.csv com 22 colunas (5 alvos de
        condição + 17 médias de sensor). Nada é descompactado no disco.
    secom  — "SECOM" (UCI 179): 1.567 passagens de fábrica × 590 medidas
        anônimas de sensor + rótulo de falha → dataset.csv (1567 × 592;
        o rótulo da fonte vem -1/+1 e a receita converte para 1 = falhou,
        0 = passou).

Licença dos dois: confira o cartão de cada dataset no UCI.

O que a receita produz (o contrato das disciplinas seguintes):
    dados/dataset.csv    — a tabela do seu domínio, carregável pelo Pandas
    dados/FONTE.md       — URL, data, licença, hash e contagem de linhas

Requer: pandas (já está no requirements do curso).

Uso (a partir da raiz do seu repositório):
    python baixar-dados.py                        # hidráulico por padrão
    python baixar-dados.py --conjunto secom       # troca o conjunto
    python baixar-dados.py --forcar               # refaz do zero
"""

from __future__ import annotations

import argparse
import hashlib
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

URLS = {
    "hidraulico": ("https://archive.ics.uci.edu/static/public/447/"
                   "condition+monitoring+of+hydraulic+systems.zip"),
    "secom": ("https://archive.ics.uci.edu/static/public/179/secom.zip"),
}
LICENCA = "confira o cartão do dataset no UCI"
MAX_MB = 200.0           # teto de disco acordado no MAPA-DE-DATASETS
MAX_LINHAS = 50_000      # teto de memória (amostra sistemática se passar)
PISO_AO1_LINHAS = 500
BLOCO = 64 * 1024

# UCI 447: arquivo de perfil de sensor no zip → prefixo da coluna (média)
SENSORES_HIDRAULICO = {
    "PS1.txt": "pressao1", "PS2.txt": "pressao2", "PS3.txt": "pressao3",
    "PS4.txt": "pressao4", "PS5.txt": "pressao5", "PS6.txt": "pressao6",
    "EPS1.txt": "pressao_motor", "FS1.txt": "vazao1", "FS2.txt": "vazao2",
    "TS1.txt": "temperatura1", "TS2.txt": "temperatura2",
    "TS3.txt": "temperatura3", "TS4.txt": "temperatura4",
    "CE.txt": "potencia", "CP.txt": "eficiencia",
    "SE.txt": "fator_viscosidade", "VS1.txt": "vibracao",
}
ALVOS_HIDRAULICO = ["cooler_condicao", "valvula_condicao",
                    "vazamento_bomba", "acumulador_bar", "ciclo_estavel"]


class LimiteExcedido(RuntimeError):
    """A fonte passou do limite de disco acordado — recusar, não truncar."""


def baixar_com_limite(url: str, destino: Path, max_mb: float) -> int:
    """Baixa em blocos, abortando (e apagando) se passar do teto."""
    teto = int(max_mb * 1024 * 1024)
    bytes_baixados = 0
    with urllib.request.urlopen(url, timeout=180) as resposta, \
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


def tabela_hidraulico(zip_local: Path) -> "object":  # pandas DataFrame
    import pandas as pd
    with zipfile.ZipFile(zip_local) as z:
        perfil = pd.read_csv(z.open("profile.txt"), sep="\t", header=None)
        perfil.columns = ALVOS_HIDRAULICO
        tabela = perfil
        for nome, prefixo in SENSORES_HIDRAULICO.items():
            serie = pd.read_csv(z.open(nome), sep="\t", header=None)
            tabela[f"{prefixo}_media"] = serie.mean(axis=1)
    return tabela


def tabela_secom(zip_local: Path):
    import pandas as pd
    with zipfile.ZipFile(zip_local) as z:
        atributos = pd.read_csv(z.open("secom.data"), sep=r"\s+", header=None)
        rotulos = pd.read_csv(z.open("secom_labels.data"), sep=r"\s+",
                              header=None, names=["falha", "data"])
    atributos.columns = [f"sensor_{i}" for i in range(atributos.shape[1])]
    rotulos["falha"] = (rotulos["falha"] == 1).astype(int)  # fonte usa -1/+1
    return pd.concat([atributos, rotulos], axis=1)


def main() -> int:
    p = argparse.ArgumentParser(
        description="Dados do domínio manutenção (UCI 447 hidráulico ou 179 SECOM).")
    p.add_argument("--conjunto", choices=sorted(URLS), default="hidraulico",
                   help="qual candidato do mapa usar (padrão: hidraulico)")
    p.add_argument("--forcar", action="store_true",
                   help="refaz mesmo se dados/dataset.csv já existir")
    argumentos = p.parse_args()

    csv_final = PASTA_DADOS / "dataset.csv"
    fonte_md = PASTA_DADOS / "FONTE.md"
    if csv_final.is_file() and not argumentos.forcar:
        print(f"{csv_final} já existe — nada a fazer (use --forcar para refazer).")
        return 0

    import pandas as pd  # dentro do main: a receita só importa se for rodar

    url_zip = URLS[argumentos.conjunto]
    PASTA_DADOS.mkdir(exist_ok=True)
    zip_local = PASTA_DADOS / "fonte.zip"
    print(f"Baixando {argumentos.conjunto} (limite {MAX_MB:g} MB): {url_zip}")
    try:
        bytes_zip = baixar_com_limite(url_zip, zip_local, MAX_MB)
    except LimiteExcedido as erro:
        print(f"RECUSADO: {erro}")
        return 1
    hash_zip = sha256_do(zip_local)

    tabela = (tabela_hidraulico(zip_local) if argumentos.conjunto == "hidraulico"
              else tabela_secom(zip_local))

    brutas = len(tabela)
    amostra = ""
    if brutas > MAX_LINHAS:
        passo = brutas // MAX_LINHAS
        tabela = tabela.iloc[::passo].head(MAX_LINHAS)
        amostra = (f" → {len(tabela)} mantidas (amostra sistemática, "
                   f"1 a cada {passo})")
    if len(tabela) < PISO_AO1_LINHAS:
        print(f"ERRO: {len(tabela)} linhas — abaixo do piso de "
              f"{PISO_AO1_LINHAS} do AO1.")
        return 1
    tabela.to_csv(csv_final, index=False)

    detalhe = ("média por ciclo de 17 perfis de sensor + 5 alvos de condição "
               "(UCI 447)" if argumentos.conjunto == "hidraulico"
               else "590 medidas de sensor + rótulo de falha e data (UCI 179)")
    fonte_md.write_text(
        f"# FONTE — dataset do domínio manutenção industrial\n\n"
        f"- **URL:** {url_zip}\n"
        f"- **Conjunto:** {argumentos.conjunto} — {detalhe}\n"
        f"- **Data do download:** "
        f"{datetime.now(timezone.utc).date().isoformat()}\n"
        f"- **Licença:** {LICENCA}\n"
        f"- **Bytes do zip:** {bytes_zip} · **SHA-256:** {hash_zip}\n"
        f"- **Registros:** {brutas} linhas × {len(tabela.columns)} colunas"
        f"{amostra}\n"
        f"- **Limites:** download ≤ {MAX_MB:g} MB · linhas ≤ "
        f"{MAX_LINHAS:,}\n",
        encoding="utf-8")
    zip_local.unlink(missing_ok=True)
    print(f"Pronto: {csv_final} ({len(tabela)} linhas) + {fonte_md}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
