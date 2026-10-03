"""Testes do cliente LLM (llm.py) — sem rede: fixtures gravadas e monkeypatch.

O que se prova aqui:
- montagem do corpo (systemInstruction, schema, temperatura 0);
- extração defensiva do texto (filtro, candidates ausentes, cercas de código);
- política de erros: chave ausente, 429/5xx com Retry-After, esquema com UMA
  retentativa, 404 com mensagem do GEMINI_MODEL;
- modo offline: replay das fixtures reais, incluindo os dois casos didáticos;
- lote assíncrono: erros isolados por ordem.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import httpx
import pytest

from ams.config import Configuracao
from ams.llm import (
    ErroLlm,
    _espera_exponencial,
    _tirar_cercas,
    avaliar_lote,
    avaliar_risco,
    avaliar_risco_async,
    extrair_texto,
    montar_corpo,
)
from ams.modelos import OrdemServico

LEITURA_VALIDA: dict[str, object] = {
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


def ordem_padrao() -> OrdemServico:
    return OrdemServico(
        identificador="OS-2026-0001",
        maquina="M14860",
        leitura=LEITURA_VALIDA,  # type: ignore[arg-type]
        descricao="Troca do insert de corte do eixo 3 e regulagem da folga.",
    )


def config_online() -> Configuracao:
    return Configuracao(gemini_api_key="AIza" + "x" * 34)


def usar_transporte(monkeypatch: pytest.MonkeyPatch,
                    respostas: list[httpx.Response]) -> None:
    """Faz o `httpx.Client` do llm.py devolver as respostas fixas, em ordem."""
    fila = list(respostas)

    def atender(requisicao: httpx.Request) -> httpx.Response:
        resposta = fila.pop(0)
        resposta.request = requisicao
        return resposta

    cliente = httpx.Client(transport=httpx.MockTransport(atender))
    monkeypatch.setattr(httpx, "Client", lambda **kw: cliente)


def resposta_429(retry_after: str | None = None) -> httpx.Response:
    cabecalhos = {"Retry-After": retry_after} if retry_after else {}
    return httpx.Response(
        429, headers=cabecalhos,
        json={"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}})


def resposta_ok(texto: str | None = None,
                tokens: tuple[int, int] = (100, 50)) -> httpx.Response:
    if texto is None:
        texto = ('{"nivel_risco": "medio", "justificativa": '
                 '"Desgaste dentro do previsto para o tipo M.", '
                 '"normas_aplicaveis": ["NR-12"], '
                 '"requer_bloqueio": false, "confianca": 0.9}')
    return httpx.Response(200, json={
        "candidates": [{"content": {"parts": [{"text": texto}]},
                        "finishReason": "STOP"}],
        "usageMetadata": {"promptTokenCount": tokens[0],
                          "candidatesTokenCount": tokens[1]},
    })


FORA_DO_ESQUEMA = (
    '{"nivel_risco": "critico", "justificativa": "texto suficientemente '
    'longo aqui.", "normas_aplicaveis": ["NR-12"], "requer_bloqueio": '
    'false, "confianca": 0.5}'
)


# --- montagem e extração (puro, sem I/O) ---


def test_montar_corpo_leva_o_schema_e_temperatura_zero() -> None:
    corpo = json.loads(montar_corpo(ordem_padrao()))
    geracao = corpo["generationConfig"]
    assert geracao["temperature"] == 0
    assert geracao["responseMimeType"] == "application/json"
    assert geracao["responseSchema"]["properties"]["nivel_risco"]["enum"] == [
        "baixo", "medio", "alto"]
    assert corpo["systemInstruction"]["parts"][0]["text"].startswith(
        "Você é o avaliador de risco")
    texto_usuario = corpo["contents"][0]["parts"][0]["text"]
    assert "OS-2026-0001" in texto_usuario and "M14860" in texto_usuario


def test_extrair_texto_aceita_resposta_normal() -> None:
    resposta = {"candidates": [{"content": {"parts": [
        {"text": '{"nivel_risco": "alto"}'}]}, "finishReason": "STOP"}]}
    assert extrair_texto(resposta) == '{"nivel_risco": "alto"}'


def test_extrair_texto_denuncia_filtro_e_resposta_vazia() -> None:
    with pytest.raises(ErroLlm, match="bloqueada"):
        extrair_texto({"promptFeedback": {"blockReason": "SAFETY"}})
    with pytest.raises(ErroLlm, match="sem candidates"):
        extrair_texto({})
    with pytest.raises(ErroLlm, match="interrompida"):
        extrair_texto({"candidates": [{"finishReason": "RECITATION"}]})


def test_tirar_cercas_resolve_a_mania_do_modelo() -> None:
    sujo = '```json\n{"nivel_risco": "medio"}\n```'
    assert _tirar_cercas(sujo) == '{"nivel_risco": "medio"}'
    assert _tirar_cercas('{"a": 1}') == '{"a": 1}'


def test_espera_exponencial_respeita_retry_after_e_o_teto() -> None:
    assert _espera_exponencial(1, retry_after=45.0) == 45.0  # servidor manda mais
    for _ in range(20):
        assert _espera_exponencial(10, None) <= 30.0  # teto com jitter
    assert _espera_exponencial(1, None) >= 2.0  # base mínima 2**1


# --- política de erros (transporte falso) ---


def test_chave_ausente_falha_imediato_com_instrucao() -> None:
    config = Configuracao()  # sem chave
    with pytest.raises(ErroLlm, match="aistudio.google.com"):
        avaliar_risco(ordem_padrao(), config)


def test_429_e_503_tres_tentativas_e_mensagem_de_cota(
        monkeypatch: pytest.MonkeyPatch) -> None:
    dormidas: list[float] = []
    monkeypatch.setattr("ams.llm.time.sleep", dormidas.append)
    usar_transporte(monkeypatch, [resposta_429("0"), httpx.Response(503, json={}),
                                  resposta_429()])
    with pytest.raises(ErroLlm, match="cota|falhou"):
        avaliar_risco(ordem_padrao(), config_online())
    assert len(dormidas) == 2  # dormiu entre as tentativas, não na última


def test_modelo_404_aponta_o_gemini_model(monkeypatch: pytest.MonkeyPatch) -> None:
    usar_transporte(monkeypatch, [httpx.Response(404, json={"error": {}})])
    with pytest.raises(ErroLlm, match="GEMINI_MODEL"):
        avaliar_risco(ordem_padrao(), config_online())


def test_erro_de_esquema_ganha_uma_segunda_chance(
        monkeypatch: pytest.MonkeyPatch) -> None:
    corpos: list[bytes] = []

    def capturar(requisicao: httpx.Request) -> httpx.Response:
        corpos.append(requisicao.content)
        return resposta_ok(FORA_DO_ESQUEMA if len(corpos) == 1 else None)

    cliente = httpx.Client(transport=httpx.MockTransport(capturar))
    monkeypatch.setattr(httpx, "Client", lambda **kw: cliente)
    parecer = avaliar_risco(ordem_padrao(), config_online())
    assert parecer.nivel_risco == "medio"
    segunda = json.loads(corpos[1])
    assert "violou o esquema" in segunda["contents"][0]["parts"][1]["text"]


def test_erro_de_esquema_duas_vezes_sobe_erro(
        monkeypatch: pytest.MonkeyPatch) -> None:
    usar_transporte(monkeypatch, [resposta_ok(FORA_DO_ESQUEMA),
                                  resposta_ok(FORA_DO_ESQUEMA)])
    with pytest.raises(ErroLlm, match="duas vezes"):
        avaliar_risco(ordem_padrao(), config_online())


# --- modo offline: as fixtures REAIS de data/fixtures ---


@pytest.fixture
def ordens_das_fixtures() -> list[OrdemServico]:
    """As 25 ordens que geraram as fixtures (mesma semente, mesmos ids)."""
    from ams import dados
    from ams.cliente_llm import gerar_ordens

    raiz = Path(__file__).resolve().parents[1]
    dataset = dados.carregar(raiz / "data" / "amostra" / "ai4i2020.csv",
                             validar_com_pydantic=False)
    return gerar_ordens(dataset.quadro, 25)


def test_replay_offline_devolve_parecer_valido(ordens_das_fixtures) -> None:
    config = Configuracao(modo_offline=True)
    parecer = avaliar_risco(ordens_das_fixtures[0], config)
    assert parecer.nivel_risco in {"baixo", "medio", "alto"}
    assert 0.0 <= parecer.confianca <= 1.0


def test_fixture_de_429_reproduz_o_erro_de_cota(ordens_das_fixtures) -> None:
    config = Configuracao(modo_offline=True)
    with pytest.raises(ErroLlm, match="429"):
        avaliar_risco(ordens_das_fixtures[18], config)  # OS-2026-0019


def test_fixture_de_erro_de_esquema_reproduz_a_rejeicao(
        ordens_das_fixtures) -> None:
    config = Configuracao(modo_offline=True)
    with pytest.raises(ErroLlm, match="esquema"):
        avaliar_risco(ordens_das_fixtures[19], config)  # OS-2026-0020


def test_fixtures_tem_pelo_menos_25_respostas() -> None:
    raiz = Path(__file__).resolve().parents[1]
    arquivos = list((raiz / "data" / "fixtures").glob("*.json"))
    assert len(arquivos) >= 25


# --- lote assíncrono ---


def test_lote_isola_erros_por_ordem(monkeypatch: pytest.MonkeyPatch) -> None:
    primeira = ordem_padrao()
    segunda = ordem_padrao()
    segunda.identificador = "OS-2026-0002"
    config = Configuracao(modo_offline=True)

    async def falso_async(ordem, config_, cliente, semaforo):
        if ordem.identificador.endswith("0001"):
            return avaliar_risco(ordem, config_)
        raise ErroLlm("chamada falhou após 3 tentativas (cota esgotada)")

    monkeypatch.setattr("ams.llm.avaliar_risco_async", falso_async)
    pareceres = asyncio.run(avaliar_lote([primeira, segunda], config))
    assert len(pareceres) == 1


def test_avaliar_risco_async_sem_chave_falha_claro() -> None:
    config = Configuracao()  # sem chave e sem offline
    semaforo = asyncio.Semaphore(1)

    async def caso() -> None:
        async with httpx.AsyncClient() as cliente:
            with pytest.raises(ErroLlm, match="aistudio.google.com"):
                await avaliar_risco_async(ordem_padrao(), config, cliente, semaforo)

    asyncio.run(caso())
