"""Testes da configuração (.env) e do log estruturado."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from ams.config import Configuracao, ErroConfig, carregar_config
from ams.log import FormatadorJson, configurar_log


def test_config_padrao_sem_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # sem .env e sem variáveis: tudo em padrão (chave vazia é permitida)
    for nome in ("GEMINI_API_KEY", "GEMINI_MODEL", "AMS_LOG_LEVEL", "AMS_MODO_OFFLINE"):
        monkeypatch.delenv(nome, raising=False)
    config = carregar_config(tmp_path / ".env-inexistente")
    assert config.gemini_api_key == ""
    assert config.gemini_model == "gemini-3.5-flash-lite"
    assert config.modo_offline is False


def test_config_le_arquivo_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for nome in ("GEMINI_API_KEY", "GEMINI_MODEL", "AMS_LOG_LEVEL", "AMS_MODO_OFFLINE"):
        monkeypatch.delenv(nome, raising=False)
    env = tmp_path / ".env"
    env.write_text(
        "GEMINI_API_KEY=AIzaSyA-teste-teste-teste-teste-teste11\n"
        "GEMINI_MODEL=gemini-3.7-flash\n"
        "AMS_LOG_LEVEL=debug\n"
        "AMS_MODO_OFFLINE=1\n",
        encoding="utf-8",
    )
    config = carregar_config(env)
    assert config.gemini_model == "gemini-3.7-flash"
    assert config.log_level == "DEBUG"  # normalizado para maiúsculas
    assert config.modo_offline is True


@pytest.mark.parametrize(
    ("valor", "trecho_do_erro"),
    [
        ("AIzaSyA-teste-teste teste-teste-teste11", "espaço"),
        ("GEMINI_API_KEY=AIzaSyA-teste-teste-teste-teste", "="),
        ("AIza...sua-chave-aqui...", "exemplo"),
        ("AIzaSyA-curta", "curta demais"),
    ],
)
def test_config_rejeita_erro_de_colagem(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valor: str, trecho_do_erro: str
) -> None:
    """O validador pega erro de COLAGEM — não o formato do fornecedor."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text(f"GEMINI_API_KEY={valor}\n", encoding="utf-8")
    with pytest.raises(ErroConfig, match=trecho_do_erro):
        carregar_config(env)


def test_config_rejeita_chave_entre_aspas() -> None:
    """Aspas vindas da variável de ambiente.

    Num .env o python-dotenv já tira as aspas sozinho; quem chega aqui com
    aspas é quem exportou a variável no terminal com elas.
    """
    with pytest.raises(ValueError, match="aspas"):
        Configuracao(gemini_api_key='"AIzaSyA-teste-teste-teste-teste-teste11"')


@pytest.mark.parametrize(
    "valor",
    [
        "AIzaSyA-teste-teste-teste-teste-teste11",   # o formato antigo
        "AQ.Ab-teste-teste-teste-teste-teste-teste8",  # o formato novo, com ponto
    ],
)
def test_config_aceita_os_dois_formatos_de_chave(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, valor: str
) -> None:
    """O Google mudou o formato da chave no meio do semestre.

    Uma regra presa ao prefixo 'AIza' recusava chave boa; esta prova existe
    para que ninguém volte a prender o validador ao formato do fornecedor.
    """
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    env = tmp_path / ".env"
    env.write_text(f"GEMINI_API_KEY={valor}\n", encoding="utf-8")
    assert carregar_config(env).gemini_api_key == valor


def test_config_rejeita_nivel_invalido(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AMS_LOG_LEVEL", raising=False)
    env = tmp_path / ".env"
    env.write_text("AMS_LOG_LEVEL=VERBOSE\n", encoding="utf-8")
    with pytest.raises(ErroConfig, match="AMS_LOG_LEVEL"):
        carregar_config(env)


def test_log_estruturado_produz_json_com_campos_extras() -> None:
    configurar_log(nivel="INFO", forcar=True)  # garante handlers limpos para o teste
    registro = logging.LogRecord(
        name="ams", level=logging.INFO, pathname=__file__, lineno=1,
        msg="ordem avaliada", args=(), exc_info=None,
    )
    registro.latencia_ms = 240
    registro.tokens_saida = 131
    linha = FormatadorJson().format(registro)
    documento = json.loads(linha)  # precisa ser JSON válido de primeira
    assert documento["mensagem"] == "ordem avaliada"
    assert documento["latencia_ms"] == 240
    assert documento["tokens_saida"] == 131
    assert "horario" in documento


def test_log_em_arquivo_jsonl(tmp_path: Path) -> None:
    caminho = tmp_path / "logs" / "ams.jsonl"
    log = configurar_log(nivel="INFO", caminho_arquivo=caminho, forcar=True)
    log.info("evento de teste", extra={"ordem_id": "OS-1"})
    linhas = caminho.read_text(encoding="utf-8").strip().splitlines()
    assert len(linhas) == 1
    documento = json.loads(linhas[0])
    assert documento["ordem_id"] == "OS-1"
