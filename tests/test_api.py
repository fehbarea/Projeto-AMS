"""Testes da API local (api.py) com TestClient — sem rede e sem chave.

O modo offline do CONFIG global decide o comportamento: os testes forçam o
estado por monkeypatch antes de importar/consultar, porque o CONFIG é lido
uma vez na criação do app (como será em produção).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ORDEM_VALIDA = {
    "identificador": "OS-2026-0001",
    "maquina": "M14860",
    "leitura": None,  # preenchido na fixture
    "descricao": "Troca do insert de corte do eixo 3 e regulagem da folga.",
}


@pytest.fixture
def ordem_valida(leitura_valida) -> dict[str, object]:
    return {**ORDEM_VALIDA, "leitura": leitura_valida}


@pytest.fixture
def cliente_offline(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    """App com modo offline ligado — as fixtures reais respondem."""
    from ams import api

    monkeypatch.setattr(api, "CONFIG", type(api.CONFIG)(modo_offline=True))
    return TestClient(api.app)


def test_saude_diz_o_modo(cliente_offline: TestClient) -> None:
    resposta = cliente_offline.get("/saude")
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["status"] == "ok"
    assert corpo["modo"] in {"online", "offline"}


def test_avaliar_devolve_o_parecer_validado(cliente_offline: TestClient,
                                            ordem_valida) -> None:
    # uma ordem que TEM fixture gravada (OS-2026-0001)
    resposta = cliente_offline.post("/avaliar", json=ordem_valida)
    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nivel_risco"] in {"baixo", "medio", "alto"}
    assert 0.0 <= corpo["confianca"] <= 1.0
    assert isinstance(corpo["normas_aplicaveis"], list)


def test_avaliar_rejeita_entrada_fora_do_contrato(cliente_offline: TestClient,
                                                  ordem_valida) -> None:
    quebrada = {**ordem_valida, "identificador": "OS"}  # id curto demais
    resposta = cliente_offline.post("/avaliar", json=quebrada)
    assert resposta.status_code == 422  # o Pydantic da entrada barra antes do LLM


def test_falha_da_camada_de_modelo_vira_503_com_mensagem(
        monkeypatch: pytest.MonkeyPatch, ordem_valida) -> None:
    from ams import api
    from ams.llm import ErroLlm

    def explode(ordem, config):
        raise ErroLlm("chamada ao modelo falhou após 3 tentativas (cota)")

    monkeypatch.setattr(api, "CONFIG", type(api.CONFIG)(modo_offline=True))
    monkeypatch.setattr(api, "avaliar_risco", explode)
    cliente = TestClient(api.app)
    resposta = cliente.post("/avaliar", json=ordem_valida)
    assert resposta.status_code == 503
    assert "cota" in resposta.json()["detail"]


def test_docs_abrem(cliente_offline: TestClient) -> None:
    resposta = cliente_offline.get("/docs")
    assert resposta.status_code == 200


def test_readme_da_api_existe_e_cobre_o_basico() -> None:
    raiz = Path(__file__).resolve().parents[1]
    conteudo = (raiz / "README-API.md").read_text(encoding="utf-8")
    assert "uvicorn" in conteudo
    assert "/saude" in conteudo and "/avaliar" in conteudo
    assert "TestClient" in conteudo or "test_api" in conteudo
