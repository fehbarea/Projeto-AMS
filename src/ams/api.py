"""API local do AMS — janela de exploração do E4-B4 (FastAPI).

Transforma o cliente do modelo em serviço: Pydantic na entrada e na saída, /docs
automático, TestClient nos testes. Prepara o deploy da D4.

Rodar:
    uvicorn ams.api:app --reload
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from ams.config import carregar_config
from ams.llm import ErroLlm, avaliar_risco
from ams.modelos import AvaliacaoRisco, OrdemServico

app = FastAPI(
    title="AMS — Assistente de Manutenção Segura",
    description="Avalia risco de falha e normas aplicáveis de uma ordem de serviço (D1).",
    version="0.1.0",
)

CONFIG = carregar_config()


@app.get("/saude")
def saude() -> dict[str, str]:
    """Endpoint de verificação: a API está de pé e em que modo está."""
    return {"status": "ok", "modo": "offline" if CONFIG.modo_offline else "online"}


@app.post("/avaliar", response_model=AvaliacaoRisco)
def avaliar(ordem: OrdemServico) -> AvaliacaoRisco:
    """Recebe uma ordem de serviço e devolve o parecer validado.

    Falhas da camada de modelo (cota, esquema, rede) viram 503: o problema
    é do fornecedor, não do cliente que chamou — e a resposta diz o que
    fazer, no mesmo padrão do resto do curso.
    """
    try:
        return avaliar_risco(ordem, CONFIG)
    except ErroLlm as erro:
        raise HTTPException(
            status_code=503,
            detail=f"camada de modelo indisponível: {erro}",
        ) from erro
