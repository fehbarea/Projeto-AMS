"""Grava as fixtures de resposta do Gemini para o modo offline (AMS_MODO_OFFLINE=1).

Gera N ordens de serviço do dataset, chama o modelo uma vez por ordem e salva
cada resposta HTTP em `data/fixtures/<sha1-do-id>.json`. As fixtures incluem o
caso de erro de esquema e o caso de 429 (editados a partir de respostas reais,
com o ajuste declarado no corpo do arquivo) — é o que faz os laboratórios de
tratamento de erro funcionarem sem rede e sem cota.

Uso (com a sua chave no .env):
    python scripts/gravar-fixtures.py --n 25
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

from ams import dados
from ams.cliente_llm import gerar_ordens
from ams.config import ErroConfig, carregar_config
from ams.llm import URL_BASE, _caminho_fixture, montar_corpo

RAIZ = Path(__file__).resolve().parents[1]
PASTA_FIXTURES = RAIZ / "data" / "fixtures"


def gravar(ordem, resposta: httpx.Response) -> Path:
    """Salva a resposta no formato que o modo offline reproduz."""
    registro = {
        "ordem_id": ordem.identificador,
        "status_code": resposta.status_code,
        "headers": {"Retry-After": resposta.headers.get("Retry-After")},
        "corpo": resposta.json(),
    }
    caminho = _caminho_fixture(ordem)
    caminho.write_text(json.dumps(registro, ensure_ascii=False, indent=1),
                       encoding="utf-8", newline="\n")
    return caminho


def main() -> int:
    argumentos = _argumentos()
    try:
        config = carregar_config()
    except ErroConfig as erro:
        print(f"ERRO: {erro}")
        return 1
    if not config.gemini_api_key:
        print("ERRO: GEMINI_API_KEY ausente no .env — as fixtures são gravadas "
              "com chamadas reais.")
        return 1

    dataset = dados.carregar(validar_com_pydantic=False)
    ordens = gerar_ordens(dataset.quadro, argumentos.n)
    PASTA_FIXTURES.mkdir(parents=True, exist_ok=True)
    url = f"{URL_BASE}/{config.gemini_model}:generateContent"

    ok = 0
    with httpx.Client(timeout=30.0) as cliente:
        for ordem in ordens:
            resposta = cliente.post(
                url, content=montar_corpo(ordem),
                headers={"x-goog-api-key": config.gemini_api_key},
            )
            if resposta.status_code == 429:
                print(f"  {ordem.identificador}: 429 — esperando 20 s "
                      "(janela de cota) antes de tentar de novo")
                time.sleep(20)
                resposta = cliente.post(
                    url, content=montar_corpo(ordem),
                    headers={"x-goog-api-key": config.gemini_api_key},
                )
            caminho = gravar(ordem, resposta)
            print(f"  {ordem.identificador}: HTTP {resposta.status_code} "
                  f"-> {caminho.name}")
            ok += resposta.status_code == 200

    print(f"\n{ok} de {len(ordens)} respostas HTTP 200 gravadas em {PASTA_FIXTURES}")
    if ok < len(ordens):
        print("Rode de novo só com as que faltaram, ou aumente a espera.")
    return 0


def _argumentos() -> argparse.Namespace:
    leitor = argparse.ArgumentParser(description=__doc__)
    leitor.add_argument("--n", type=int, default=25,
                        help="quantas ordens gravar (padrão: 25)")
    return leitor.parse_args()


if __name__ == "__main__":
    sys.exit(main())
