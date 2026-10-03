"""Logging estruturado em JSON para o AMS.

Por que JSON e não texto corrido: a partir do momento em que o agente
processa dezenas de ordens de serviço (E4), "dar uma olhada no log" vira
filtrar por campo (latência, tokens, custo) — e isso exige estrutura, não
grep em texto livre. Cada linha de log é um objeto JSON válido.

Uso:
    from ams.log import obter_logger

    log = obter_logger()
    log.info("ordem avaliada", extra={"ordem_id": "OS-1", "latencia_ms": 240})
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime
from pathlib import Path

CAMPOS_FIXOS = {
    "name": "logger",
    "levelname": "nivel",
    "msg": "mensagem",
    "filename": "arquivo",
    "lineno": "linha",
}


class FormatadorJson(logging.Formatter):
    """Converte cada LogRecord em uma linha de JSON.

    Os argumentos passados via `extra={...}` são anexados como campos —
    é assim que latência, tokens e custo entram no registro.
    """

    #: atributos internos do LogRecord que não devem virar campos do JSON
    _internos = set(
        logging.makeLogRecord({}).__dict__.keys()
    ) | {"message", "asctime", "taskName"}

    def format(self, registro: logging.LogRecord) -> str:
        documento: dict[str, object] = {
            "horario": datetime.fromtimestamp(registro.created, tz=UTC).isoformat()
        }
        for atributo, campo in CAMPOS_FIXOS.items():
            documento[campo] = getattr(registro, atributo)
        # campos extras (aqueles que não são atributos padrão do LogRecord)
        for chave, valor in registro.__dict__.items():
            if chave not in self._internos:
                documento[chave] = valor
        if registro.exc_info:
            documento["excecao"] = self.formatException(registro.exc_info)
        return json.dumps(documento, ensure_ascii=False, default=str)


class FormatadorConsole(logging.Formatter):
    """Linha legível para o console — o JSON fica só no arquivo.

    Os eventos conhecidos do AMS ganham ícone e campos em português; os
    demais caem em texto corrido com prefixo por nível. O JSON estruturado
    (o que o E4 consulta com Pandas) continua saindo intacto no arquivo.
    """

    _internos = FormatadorJson._internos

    def format(self, registro: logging.LogRecord) -> str:
        extras = {
            chave: valor
            for chave, valor in registro.__dict__.items()
            if chave not in self._internos
        }
        if registro.msg == "ordem avaliada":
            return (
                f"✅ {extras.get('ordem_id', '?')} avaliada · "
                f"{extras.get('origem', '?')} · "
                f"{extras.get('latencia_ms', 0)} ms · "
                f"tentativa {extras.get('tentativas', 1)}"
            )
        if registro.msg == "lote concluído":
            return (
                f"📦 lote concluído — {extras.get('ok', 0)}/"
                f"{extras.get('total', 0)} ok · "
                f"{extras.get('erro_esquema', 0)} por esquema · "
                f"{extras.get('erro_cota_ou_rede', 0)} por cota/rede"
            )
        icone = {logging.WARNING: "⚠ ", logging.ERROR: "✖ "}.get(
            registro.levelno, "· "
        )
        return f"{icone}{registro.getMessage()}"


def configurar_log(
    nivel: str = "INFO", caminho_arquivo: Path | None = None, forcar: bool = False
) -> logging.Logger:
    """Configura e devolve o logger do AMS (`ams`).

    Args:
        nivel: DEBUG, INFO, WARNING ou ERROR.
        caminho_arquivo: se informado, além do console escreve uma linha
            JSON por evento neste arquivo (formato JSON Lines).
        forcar: reconfigura mesmo que já esteja configurado (útil em testes).

    Returns:
        O logger `ams` com handler de console (e de arquivo, se pedido).
    """
    log = logging.getLogger("ams")
    if log.handlers and not forcar:
        log.setLevel(nivel.upper())
        return log

    log.handlers.clear()
    log.setLevel(nivel.upper())
    log.propagate = False

    console = logging.StreamHandler(stream=sys.stdout)
    console.setFormatter(FormatadorConsole())
    log.addHandler(console)

    if caminho_arquivo is not None:
        caminho_arquivo.parent.mkdir(parents=True, exist_ok=True)
        arquivo = logging.FileHandler(caminho_arquivo, encoding="utf-8")
        arquivo.setFormatter(FormatadorJson())
        log.addHandler(arquivo)

    return log


def obter_logger() -> logging.Logger:
    """Devolve o logger do AMS, configurando-o no nível INFO se preciso."""
    return configurar_log()
