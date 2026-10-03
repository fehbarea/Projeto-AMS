"""Receita de dados do domínio JURÍDICO/DOCUMENTAL — DataJud (CNJ).

Domínio: análise documental jurídica ou tributária · Fonte: API pública do
DataJud (CNJ) — metadados de processos judiciais em formato aberto. NÃO é
preciso criar conta nem chave própria: a chave do DataJud é fixa e pública
(igual para todo mundo — o próprio site a exibe sem login), já vem
preenchida abaixo e não vai no .env; se um dia o CNJ a trocar, ponha
DATAJUD_APIKEY=... no .env da raiz.

O que a receita produz (o contrato das disciplinas seguintes):
    dados/documentos/processo-001.json ... processo-060.json  (o corpus)
    dados/FONTE.md       — URL, data, licença, hash do lote e contagem

Cada documento é um processo (JSON de ~15 KB) com numeroProcesso, classe,
assuntos, movimentos e órgão julgador — só processos de sigilo 0 (público).
Limite do domínio documental respeitado: até 200 documentos (padrão: 60).

Tribunal é o "alias" do CNJ, em minúsculas, sem acento — exemplos:
trf1, trf2, tjpr, tjsp, stj (lista completa no wiki do DataJud).

Requer: apenas a biblioteca padrão do Python (nenhum pip install).

Uso (a partir da raiz do seu repositório):
    python baixar-dados.py                              # 60 processos, TRF1
    python baixar-dados.py --assunto "consumidor"       # muda o termo
    python baixar-dados.py --tribunal tjpr --quantidade 100
    python baixar-dados.py --forcar                     # refaz do zero
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent  # a receita vive na RAIZ do repositório
if RAIZ.name in ("receitas", "scripts"):  # rodando de dentro do pacote D1-00
    RAIZ = RAIZ.parent                    # o dados/ sobe para a raiz do projeto
PASTA_DADOS = RAIZ / "dados"
PASTA_DOCS = PASTA_DADOS / "documentos"

URL_BASE = "https://api-publica.datajud.cnj.jus.br/api_publica_{tribunal}/_search"
CHAVE_PUBLICA_CNJ = ("cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TR"
                     "ENyQk1RdnFKZGRQdw==")  # pública, do wiki do DataJud
MAX_DOCUMENTOS = 200      # teto do domínio documental no MAPA-DE-DATASETS
PISO_AO1_DOCUMENTOS = 50  # piso do AO1 para corpus
TAMANHO_PAGINA = 100      # testado em 28/08/2026: a API aceita até 200
PAGINAS_MAX = 10          # trava contra laço infinito (2.000 documentos)


def limite_do_erro(mensagem: str) -> int:
    print(f"RECUSADO: {mensagem}")
    return 1


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


def coletar(tribunal: str, assunto: str, quantidade: int) -> list[dict]:
    """Percorre o índice do tribunal com paginação search_after."""
    chave = (os.environ.get("DATAJUD_APIKEY", "").strip()
             or ler_do_env("DATAJUD_APIKEY") or CHAVE_PUBLICA_CNJ)
    url = URL_BASE.format(tribunal=tribunal)
    cab = {"Authorization": "APIKey " + chave,
           "Content-Type": "application/json"}
    busca = {
        "size": min(TAMANHO_PAGINA, quantidade),
        "sort": [{"@timestamp": "asc"}],
        "query": {"bool": {"must": [
            {"match": {"assuntos.nome": assunto}},
            {"term": {"nivelSigilo": 0}},
        ]}},
    }
    processos: list[dict] = []
    for _ in range(PAGINAS_MAX):
        req = urllib.request.Request(url, method="POST",
                                     data=json.dumps(busca).encode("utf-8"),
                                     headers=cab)
        try:
            with urllib.request.urlopen(req, timeout=90) as resposta:
                hits = json.load(resposta)["hits"]["hits"]
        except urllib.error.HTTPError as erro:
            dica = ("chave recusada — confira DATAJUD_APIKEY"
                    if erro.code == 401 else
                    f"o tribunal '{tribunal}' pode não existir — aliases no "
                    "wiki do DataJud")
            raise SystemExit(limite_do_erro(
                f"HTTP {erro.code} na API do DataJud ({dica}): "
                f"{erro.read()[:200]}"))
        if not hits:
            break
        for hit in hits:
            processos.append(hit["_source"])
            if len(processos) >= quantidade:
                return processos
        busca["search_after"] = hits[-1]["sort"]  # próxima página
    return processos


def sha256_do(caminho: Path) -> str:
    digesto = hashlib.sha256()
    with open(caminho, "rb") as fh:
        while bloco := fh.read(64 * 1024):
            digesto.update(bloco)
    return digesto.hexdigest()


def main() -> int:
    p = argparse.ArgumentParser(
        description="Corpus de processos do DataJud (domínio jurídico).")
    p.add_argument("--assunto", default="contrato",
                   help="termo buscado em assuntos.nome (padrão: contrato)")
    p.add_argument("--tribunal", default="trf1",
                   help="alias do tribunal no DataJud (padrão: trf1)")
    p.add_argument("--quantidade", type=int, default=60,
                   help=f"quantos processos (≤ {MAX_DOCUMENTOS})")
    p.add_argument("--forcar", action="store_true",
                   help="baixa de novo mesmo se o corpus já existir")
    argumentos = p.parse_args()

    if argumentos.quantidade > MAX_DOCUMENTOS:
        return limite_do_erro(
            f"{argumentos.quantidade} documentos passa do teto do domínio "
            f"documental ({MAX_DOCUMENTOS}) acordado no MAPA-DE-DATASETS")
    if argumentos.quantidade < PISO_AO1_DOCUMENTOS:
        return limite_do_erro(
            f"{argumentos.quantidade} documentos fica abaixo do piso do AO1 "
            f"({PISO_AO1_DOCUMENTOS})")

    ja_tem = PASTA_DOCS.is_dir() and any(PASTA_DOCS.glob("processo-*.json"))
    if ja_tem and not argumentos.forcar:
        print(f"{PASTA_DOCS} já tem corpus — nada a fazer (use --forcar).")
        return 0

    print(f"Consultando o DataJud: tribunal={argumentos.tribunal}, "
          f"assunto='{argumentos.assunto}', {argumentos.quantidade} processos...")
    processos = coletar(argumentos.tribunal, argumentos.assunto,
                        argumentos.quantidade)
    if len(processos) < PISO_AO1_DOCUMENTOS:
        return limite_do_erro(
            f"o tribunal/devolveu só {len(processos)} processos para "
            f"'{argumentos.assunto}' — troque o --assunto ou o --tribunal")

    PASTA_DOCS.mkdir(parents=True, exist_ok=True)
    for indice, processo in enumerate(processos, start=1):
        arquivo = PASTA_DOCS / f"processo-{indice:03d}.json"
        arquivo.write_text(json.dumps(processo, ensure_ascii=False, indent=1),
                           encoding="utf-8")

    hash_lote = hashlib.sha256("".join(
        f"{p['numeroProcesso']};{p.get('dataAjuizamento', '')}\n"
        for p in processos).encode("utf-8")).hexdigest()
    PASTA_DADOS.mkdir(exist_ok=True)
    (PASTA_DADOS / "FONTE.md").write_text(
        f"# FONTE — corpus do domínio jurídico/documental\n\n"
        f"- **URL:** api-publica.datajud.cnj.jus.br "
        f"({argumentos.tribunal}, _search)\n"
        f"- **Filtro:** assuntos.nome ~ '{argumentos.assunto}' · "
        f"nivelSigilo = 0 (apenas públicos)\n"
        f"- **Data do download:** "
        f"{datetime.now(timezone.utc).date().isoformat()}\n"
        f"- **Licença:** dados abertos administrativos do CNJ — confira os "
        f"termos de reuso no wiki do DataJud\n"
        f"- **Documentos:** {len(processos)} processos em "
        f"dados/documentos/ (JSON)\n"
        f"- **SHA-256 do lote** (numero;dataAjuizamento): `{hash_lote}`\n"
        f"- **Limites:** ≤ {MAX_DOCUMENTOS} documentos (nenhum teto "
        f"atingido)\n",
        encoding="utf-8")
    print(f"Pronto: {PASTA_DOCS} com {len(processos)} processos + "
          f"{PASTA_DADOS / 'FONTE.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
