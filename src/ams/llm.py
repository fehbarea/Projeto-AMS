"""Cliente do Gemini Flash — REST puro com httpx, sem SDK (brief B01, §4.4).

Este é o embrião da camada de LLM que será reescrita na D8. Tudo aqui é
escrito à mão de propósito: a lição da disciplina é a mecânica HTTP.

Política de erros (a mesma em `avaliar_risco` e `avaliar_risco_async`):

- 429/5xx: até 3 tentativas com espera exponencial + Retry-After;
- timeout 30 s explícito, erro claro;
- chave ausente: falha imediata com a instrução do AI Studio;
- modelo 404: mensagem própria apontando o GEMINI_MODEL do .env;
- JSON fora do esquema: UMA nova tentativa anexando o erro de validação;
- modo offline (AMS_MODO_OFFLINE=1): as fixtures de `data/fixtures/` entram
  no lugar da rede — passando pelos mesmos tratamentos, inclusive os dois
  casos didáticos (erro de esquema e 429).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import random
import re
import time
from pathlib import Path

import httpx
from pydantic import ValidationError

from ams.config import Configuracao
from ams.log import obter_logger
from ams.modelos import AvaliacaoRisco, OrdemServico

log = obter_logger()

URL_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

RAIZ_DO_PACOTE = Path(__file__).resolve().parent.parent.parent
PASTA_FIXTURES = RAIZ_DO_PACOTE / "data" / "fixtures"

TIMEOUT_S = 30.0
MAX_TENTATIVAS = 3

# Custo de referência (US$ por 1M tokens) da camada PAGA equivalente — a
# camada gratuita não cobra, mas o número ensina o que a conta faria na
# produção. A D7/D9 voltam aqui com orçamento de verdade.
PRECO_ENTRADA_POR_1M = 0.10
PRECO_SAIDA_POR_1M = 0.40

# ESCRITO À MÃO, de propósito: o model_json_schema() do Pydantic emite
# $defs/anyOf/title, que o Gemini REJEITA. A D8 automatizará esta conversão;
# na D1, escrever à mão é o que ensina o formato.
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "nivel_risco": {"type": "STRING", "enum": ["baixo", "medio", "alto"]},
        "justificativa": {"type": "STRING"},
        "normas_aplicaveis": {"type": "ARRAY", "items": {"type": "STRING"}},
        "requer_bloqueio": {"type": "BOOLEAN"},
        "confianca": {"type": "NUMBER"},
    },
    "required": [
        "nivel_risco", "justificativa", "normas_aplicaveis",
        "requer_bloqueio", "confianca",
    ],
}

INSTRUCAO_SISTEMA = (
    "Você é o avaliador de risco do AMS. Dada uma ordem de manutenção com "
    "leituras de sensores, responda APENAS com JSON no esquema pedido. "
    "Nível de risco julga a chance de falha da máquina; normas seguem a "
    "intervenção descrita (NR-10 elétrica, NR-12 máquinas, NR-35 altura)."
)


class ErroLlm(RuntimeError):
    """Falha da camada de modelo, com mensagem pronta para o usuário."""


def montar_corpo(ordem: OrdemServico, correcao: str | None = None) -> bytes:
    """Monta o corpo JSON da chamada (systemInstruction + contents + generationConfig).

    A entrada do usuário é o resumo da ordem: identificador, máquina,
    leituras-chave e a descrição da intervenção. Se `correcao` vem preenchida,
    é a segunda tentativa após erro de esquema: a resposta rejeitada e o erro
    de validação são anexados para o modelo corrigir a si mesmo.
    """
    leitura = ordem.leitura
    texto = (
        f"Ordem {ordem.identificador} — máquina {ordem.maquina}.\n"
        f"Sensores: temperatura do ar {leitura.temperatura_ar} K, temperatura do "
        f"processo {leitura.temperatura_processo} K, rotação {leitura.rotacao} rpm, "
        f"torque {leitura.torque} Nm, desgaste da ferramenta {leitura.desgaste} min, "
        f"tipo de produto {leitura.tipo}.\n"
        f"Intervenção planejada: {ordem.descricao}"
    )
    partes: list[dict[str, object]] = [{"text": texto}]
    if correcao is not None:
        partes.append({"text": correcao})
    corpo = {
        "systemInstruction": {"parts": [{"text": INSTRUCAO_SISTEMA}]},
        "contents": [{"role": "user", "parts": partes}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }
    return json.dumps(corpo, ensure_ascii=False).encode("utf-8")


def extrair_texto(resposta_json: dict) -> str:
    """Extrai `candidates[0].content.parts[0].text` — a string que CONTÉM o JSON.

    Navegação toda com `.get()`: uma resposta bloqueada pelo filtro de
    segurança não tem `candidates`, e o erro precisa dizer isso — não
    `KeyError: 'candidates'` no meio da aula.
    """
    if resposta_json.get("promptFeedback", {}).get("blockReason"):
        motivo = resposta_json["promptFeedback"]["blockReason"]
        raise ErroLlm(
            f"resposta bloqueada pelo filtro de segurança do provedor "
            f"({motivo}) — reescreva a descrição da intervenção."
        )
    candidatos = resposta_json.get("candidates") or []
    if not candidatos:
        raise ErroLlm(
            "resposta sem candidates — o provedor não devolveu texto "
            "(verifique o corpo completo no log)."
        )
    motivo_final = candidatos[0].get("finishReason", "STOP")
    if motivo_final not in {"STOP", "MAX_TOKENS"}:
        raise ErroLlm(
            f"geração interrompida pelo provedor (finishReason: {motivo_final})."
        )
    partes = (candidatos[0].get("content") or {}).get("parts") or []
    if not partes or "text" not in partes[0]:
        raise ErroLlm(
            "resposta sem parte de texto — o modelo devolveu estrutura "
            "inesperada (verifique o corpo completo no log)."
        )
    return partes[0]["text"]


def _espera_exponencial(tentativa: int, retry_after: float | None) -> float:
    """Quanto esperar antes da próxima tentativa, em segundos.

    Base 2**tentativa com jitter, teto de 30 s. `Retry-After` do servidor,
    quando presente, ganha se for maior — o servidor sabe da própria fila.
    """
    base = min(2 ** tentativa + random.uniform(0, 1), 30.0)
    return max(base, retry_after or 0.0)


def _tirar_cercas(texto: str) -> str:
    """Remove as cercas ```json que modelos adoram pôr mesmo quando proibidas."""
    limpo = texto.strip()
    casou = re.search(r"```(?:json)?\s*(.*?)\s*```", limpo, flags=re.DOTALL)
    if casou:
        limpo = casou.group(1)
    return limpo


def _resumo_erro_validacao(erro: ValidationError) -> str:
    """Uma linha por campo com o problema — é isto que vai anexado à 2ª tentativa."""
    linhas = [
        f"- {e['loc'][0]}: {e['msg']}" for e in erro.errors()
    ]
    return "Sua resposta anterior violou o esquema:\n" + "\n".join(linhas)


def _contadores(resposta_json: dict) -> tuple[int, int]:
    """Tokens de entrada/saída do usageMetadata (0 quando ausente)."""
    uso = resposta_json.get("usageMetadata") or {}
    return int(uso.get("promptTokenCount", 0)), int(uso.get("candidatesTokenCount", 0))


def _registrar(ordem: OrdemServico, latencia_ms: int, tokens_in: int,
               tokens_out: int, tentativas: int, origem: str) -> None:
    custo = (
        tokens_in / 1e6 * PRECO_ENTRADA_POR_1M
        + tokens_out / 1e6 * PRECO_SAIDA_POR_1M
    )
    log.info(
        "ordem avaliada",
        extra={
            "ordem_id": ordem.identificador,
            "origem": origem,
            "latencia_ms": latencia_ms,
            "tokens_entrada": tokens_in,
            "tokens_saida": tokens_out,
            "custo_usd": round(custo, 6),
            "tentativas": tentativas,
        },
    )


# --- modo offline (§4.5): as fixtures salvam a aula quando a cota estoura ---


def _caminho_fixture(ordem: OrdemServico, pasta: Path = PASTA_FIXTURES) -> Path:
    """Caminho determinístico da resposta gravada: sha1 do identificador."""
    digesto = hashlib.sha1(ordem.identificador.encode("utf-8")).hexdigest()[:16]
    return pasta / f"{digesto}.json"


def _modo_offline(config: Configuracao) -> bool:
    """True se AMS_MODO_OFFLINE=1 — o cliente lê fixtures em vez da rede."""
    return config.modo_offline


def _carregar_fixture(ordem: OrdemServico) -> dict:
    """Lê a fixture da ordem: {"status_code", "headers", "corpo"}.

    As fixtures (>= 25 ordens) incluem um caso de ERRO DE ESQUEMA e um de
    429 — no modo offline os tratamentos funcionam sem rede, porque a
    resposta gravada entra exatamente onde a resposta HTTP entraria.
    """
    caminho = _caminho_fixture(ordem)
    if not caminho.exists():
        raise ErroLlm(
            f"modo offline sem fixture para a ordem {ordem.identificador} "
            f"({caminho.name}). Rode `python scripts/gravar-fixtures.py` "
            "com uma chave válida, ou desligue AMS_MODO_OFFLINE no .env."
        )
    return json.loads(caminho.read_text(encoding="utf-8"))


def _validar_ou_corrigir(
    texto: str, segunda_tentativa: bool
) -> tuple[AvaliacaoRisco | None, str | None]:
    """Valida o texto do modelo; devolve o parecer ou a correção para anexar.

    Uma única retentativa: se a resposta viola o esquema de novo, o erro
    sobe — insistir contra um modelo decidido a errar só queima cota.
    """
    try:
        return AvaliacaoRisco.model_validate_json(_tirar_cercas(texto)), None
    except ValidationError as erro:
        if segunda_tentativa:
            raise ErroLlm(
                "o modelo devolveu JSON fora do esquema duas vezes "
                f"(último erro: {erro.errors()[0]['loc'][0]}). "
                "Trate como falha da chamada — registre e siga."
            ) from erro
        return None, _resumo_erro_validacao(erro)


def avaliar_risco(ordem: OrdemServico, config: Configuracao) -> AvaliacaoRisco:
    """Chamada síncrona: valida, trata 429/5xx com retry, mede latência e tokens."""
    if _modo_offline(config):
        return _avaliar_offline(ordem)

    if not config.gemini_api_key:
        raise ErroLlm(
            "GEMINI_API_KEY ausente no .env — gere a chave gratuita em "
            "https://aistudio.google.com/apikey e cole o valor, ou use o "
            "modo offline (AMS_MODO_OFFLINE=1)."
        )

    url = f"{URL_BASE}/{config.gemini_model}:generateContent"
    cabecalhos = {"x-goog-api-key": config.gemini_api_key}
    correcao: str | None = None
    inicio = time.perf_counter()

    with httpx.Client(timeout=TIMEOUT_S) as cliente:
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            resposta = cliente.post(url, content=montar_corpo(ordem, correcao),
                                    headers=cabecalhos)
            if resposta.status_code == 200:
                corpo = resposta.json()
                texto = extrair_texto(corpo)
                parecer, correcao_nova = _validar_ou_corrigir(texto, correcao is not None)
                if parecer is not None:
                    t_in, t_out = _contadores(corpo)
                    _registrar(ordem, int((time.perf_counter() - inicio) * 1000),
                               t_in, t_out, tentativa, "online")
                    return parecer
                correcao = correcao_nova
                continue
            if resposta.status_code == 404:
                raise ErroLlm(
                    f"Modelo {config.gemini_model} não disponível para esta "
                    "chave. Verifique aistudio.google.com e ajuste "
                    "GEMINI_MODEL no .env."
                )
            if resposta.status_code in (429, 500, 502, 503):
                if tentativa == MAX_TENTATIVAS:
                    break
                espera = _espera_exponencial(tentativa,
                                             _retry_after_de(resposta.headers))
                log.warning("tentativa %d falhou (%s); esperando %.1fs",
                            tentativa, resposta.status_code, espera)
                time.sleep(espera)
                continue
            break  # outros códigos: não há política de retry

    raise ErroLlm(
        f"chamada ao modelo falhou após {MAX_TENTATIVAS} tentativas "
        "(cota esgotada ou provedor fora do ar). Se for 429, aguarde a "
        "janela de cota ou use AMS_MODO_OFFLINE=1."
    )


def _avaliar_offline(ordem: OrdemServico) -> AvaliacaoRisco:
    """Replay da fixture: mesma extração, mesma validação, mesmos tratamentos."""
    fixture = _carregar_fixture(ordem)
    inicio = time.perf_counter()
    status = fixture.get("status_code", 200)
    if status == 200:
        corpo = fixture["corpo"]
        parecer, _ = _validar_ou_corrigir(extrair_texto(corpo), segunda_tentativa=True)
        t_in, t_out = _contadores(corpo)
        _registrar(ordem, int((time.perf_counter() - inicio) * 1000),
                   t_in, t_out, 1, "offline")
        return parecer
    if status == 404:
        raise ErroLlm(
            "fixture com modelo indisponível — ajuste GEMINI_MODEL e "
            "regrave as fixtures (scripts/gravar-fixtures.py)."
        )
    raise ErroLlm(
        f"fixture com HTTP {status} (cota esgotada no momento da gravação). "
        "É o caso didático do laboratório: o tratamento de 429 é o mesmo "
        "da chamada real."
    )


def _retry_after_de(cabecalhos) -> float | None:
    """Lê o cabeçalho Retry-After em segundos, se o servidor o enviou."""
    valor = cabecalhos.get("Retry-After")
    if valor is None:
        return None
    try:
        return float(valor)
    except ValueError:
        return None


async def avaliar_risco_async(ordem: OrdemServico, config: Configuracao,
                              cliente: httpx.AsyncClient,
                              semaforo: asyncio.Semaphore) -> AvaliacaoRisco:
    """Versão assíncrona com AsyncClient — mesma política de erros do síncrono.

    O semáforo limita a concorrência: disparar 20 chamadas simultâneas
    contra a camada gratuita é o caminho curto para o 429 da turma inteira.
    """
    if _modo_offline(config):
        return _avaliar_offline(ordem)

    if not config.gemini_api_key:
        raise ErroLlm(
            "GEMINI_API_KEY ausente no .env — gere a chave gratuita em "
            "https://aistudio.google.com/apikey, ou use o modo offline."
        )

    url = f"{URL_BASE}/{config.gemini_model}:generateContent"
    correcao: str | None = None
    inicio = time.perf_counter()

    async with semaforo:
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            resposta = await cliente.post(
                url, content=montar_corpo(ordem, correcao),
                headers={"x-goog-api-key": config.gemini_api_key},
            )
            if resposta.status_code == 200:
                corpo = resposta.json()
                parecer, correcao_nova = _validar_ou_corrigir(
                    extrair_texto(corpo), correcao is not None)
                if parecer is not None:
                    t_in, t_out = _contadores(corpo)
                    _registrar(ordem, int((time.perf_counter() - inicio) * 1000),
                               t_in, t_out, tentativa, "online")
                    return parecer
                correcao = correcao_nova
                continue
            if resposta.status_code == 404:
                raise ErroLlm(
                    f"Modelo {config.gemini_model} não disponível para esta "
                    "chave. Verifique aistudio.google.com e ajuste "
                    "GEMINI_MODEL no .env."
                )
            if resposta.status_code in (429, 500, 502, 503):
                if tentativa == MAX_TENTATIVAS:
                    break
                espera = _espera_exponencial(tentativa,
                                             _retry_after_de(resposta.headers))
                log.warning("tentativa %d falhou (%s); esperando %.1fs",
                            tentativa, resposta.status_code, espera)
                await asyncio.sleep(espera)
                continue
            break

    raise ErroLlm(
        f"chamada ao modelo falhou após {MAX_TENTATIVAS} tentativas "
        "(cota esgotada ou provedor fora do ar). Se for 429, aguarde a "
        "janela de cota ou use AMS_MODO_OFFLINE=1."
    )


async def avaliar_lote(ordens: list[OrdemServico], config: Configuracao,
                       concorrencia: int = 5,
                       com_ordens: bool = False) -> list | list[tuple]:
    """Processa um lote com asyncio.gather + semáforo.

    Erros isolados por chamada: uma ordem que falha não derruba o lote — o
    relatório final diz X ok, Y por esquema, Z por cota/rede.

    Com `com_ordens=True` devolve pares `(ordem, parecer | None)` na ordem
    de entrada — falha vira `None` —, que é o formato que o cliente usa
    para montar a tabela final. O padrão continua devolvendo só pareceres.
    """
    semaforo = asyncio.Semaphore(concorrencia)
    async with httpx.AsyncClient(timeout=TIMEOUT_S) as cliente:
        tarefas = [avaliar_risco_async(o, config, cliente, semaforo) for o in ordens]
        resultados = await asyncio.gather(*tarefas, return_exceptions=True)

    pareceres, esquema, cota = [], 0, 0
    for r in resultados:
        if isinstance(r, AvaliacaoRisco):
            pareceres.append(r)
        elif isinstance(r, ErroLlm) and "esquema" in str(r):
            esquema += 1
        else:
            cota += 1
    log.info(
        "lote concluído",
        extra={"total": len(ordens), "ok": len(pareceres),
               "erro_esquema": esquema, "erro_cota_ou_rede": cota},
    )
    if com_ordens:
        return [
            (ordem, r if isinstance(r, AvaliacaoRisco) else None)
            for ordem, r in zip(ordens, resultados)
        ]
    return pareceres
