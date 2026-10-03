"""Configuração do AMS lida do arquivo .env.

A regra do curso: nenhuma chave no código e nenhuma chave no Git. Tudo que
é secreto ou varia por máquina vive no `.env` (copiado do `.env.example`),
e este módulo é o único lugar que o lê.

Uso:
    from ams.config import carregar_config

    configuracao = carregar_config()   # procura .env na raiz do projeto
    print(configuracao.gemini_model)
"""

from __future__ import annotations

import re
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator

RAIZ_DO_PACOTE = Path(__file__).resolve().parent.parent.parent

# A checagem daqui NÃO valida a chave de verdade — só uma chamada à API faz
# isso. Ela pega os erros de colagem: espaço no meio, aspas em volta, a linha
# inteira do .env colada dentro do valor, ou o texto de exemplo no lugar da
# chave.
#
# E ela de propósito NÃO exige um prefixo. O Google já usou "AIza..." e passou
# a emitir chaves em outro formato; uma regra presa ao formato do fornecedor
# recusa chave boa no dia em que ele muda — foi o que aconteceu com a turma. O
# que não muda é o que a colagem estraga.
TAMANHO_MINIMO_DA_CHAVE = 30
# O texto de exemplo que aparece no .env.example e nos guias, para o caso de
# alguém salvar o arquivo sem trocar o valor.
PADRAO_DE_PLACEHOLDER = re.compile(r"\.\.\.|[<>]|sua[ _-]?chave", re.IGNORECASE)


class ErroConfig(ValueError):
    """Erro de configuração com mensagem pronta para o usuário."""


class Configuracao(BaseModel):
    """Configuração validada do AMS.

    A chave é opcional (o modo offline e os testes vivem sem ela), mas se
    estiver preenchida precisa ter cara de chave do Gemini.
    """

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    log_level: str = Field(default="INFO")
    modo_offline: bool = False

    @field_validator("gemini_api_key")
    @classmethod
    def validar_chave(cls, valor: str) -> str:
        chave = valor.strip()
        if not chave:
            return chave

        onde = "Abra o .env, na linha GEMINI_API_KEY,"
        gere = ("Se precisar de uma chave nova, gere em "
                "https://aistudio.google.com/apikey e cole o valor inteiro.")

        if chave[0] in "\"'" or chave[-1] in "\"'":
            raise ValueError(
                f"GEMINI_API_KEY está entre aspas. {onde} e tire as aspas: "
                f"no .env o valor vai solto, sem aspas e sem espaço. {gere}"
            )
        if any(c.isspace() for c in chave):
            raise ValueError(
                f"GEMINI_API_KEY tem espaço no meio do valor. {onde} e cole a "
                f"chave de novo, de uma vez só, sem quebrar a linha. {gere}"
            )
        if "=" in chave:
            raise ValueError(
                f"GEMINI_API_KEY tem '=' dentro do valor — provavelmente a linha "
                f"inteira foi colada dentro dela. {onde} deixe só a chave depois "
                f"do primeiro '='. {gere}"
            )
        if PADRAO_DE_PLACEHOLDER.search(chave):
            raise ValueError(
                f"GEMINI_API_KEY ainda está com o texto de exemplo, não com uma "
                f"chave. {onde} e substitua o valor inteiro pela sua chave. {gere}"
            )
        if len(chave) < TAMANHO_MINIMO_DA_CHAVE:
            raise ValueError(
                f"GEMINI_API_KEY tem só {len(chave)} caracteres — curta demais "
                f"para uma chave (a cópia provavelmente veio cortada). {onde} e "
                f"cole o valor inteiro. {gere}"
            )
        return chave

    @field_validator("gemini_model")
    @classmethod
    def validar_modelo(cls, valor: str) -> str:
        modelo = valor.strip()
        if not modelo:
            raise ValueError(
                "GEMINI_MODEL vazio no .env — indique um modelo (ex.: gemini-3.5-flash-lite). "
                "Os modelos ativos ficam visíveis em aistudio.google.com."
            )
        return modelo

    @field_validator("log_level")
    @classmethod
    def validar_nivel(cls, valor: str) -> str:
        nivel = valor.strip().upper()
        validos = {"DEBUG", "INFO", "WARNING", "ERROR"}
        if nivel not in validos:
            raise ValueError(
                f"AMS_LOG_LEVEL inválido: '{valor}'. Use um destes: {sorted(validos)}."
            )
        return nivel


def carregar_config(caminho_env: Path | None = None) -> Configuracao:
    """Lê o .env e devolve uma configuração validada.

    Args:
        caminho_env: caminho do .env. Se omitido, procura na raiz do projeto.

    Returns:
        Configuracao preenchida com os valores do arquivo (e das variáveis
        de ambiente, que o load_dotenv não sobrescreve).

    Raises:
        ErroConfig: se algum valor viola as regras, com a instrução em
            português do que corrigir no .env.
    """
    if caminho_env is None:
        caminho_env = RAIZ_DO_PACOTE / ".env"
    load_dotenv(caminho_env)

    try:
        return Configuracao(
            gemini_api_key=_variavel("GEMINI_API_KEY", ""),
            gemini_model=_variavel("GEMINI_MODEL", "gemini-3.5-flash-lite"),
            log_level=_variavel("AMS_LOG_LEVEL", "INFO"),
            modo_offline=_variavel("AMS_MODO_OFFLINE", "0") in {"1", "true", "sim"},
        )
    except ValueError as erro:
        raise ErroConfig(f"Problema no {caminho_env.name}: {erro}") from erro


def _variavel(nome: str, padrao: str) -> str:
    """Lê uma variável de ambiente como string, tratando vazio como ausente."""
    import os

    valor = os.environ.get(nome, padrao)
    return valor if valor.strip() else padrao
