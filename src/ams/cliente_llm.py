"""O cliente do modelo — lê ordem → chama modelo → valida → registra → repete.

Não é um agente (a D2 reserva a palavra): é o encanamento — HTTP, validação
com Pydantic, retry e log estruturado, em lote. O esqueleto é curto porque as
peças já existem (config, modelos, dados, llm, log); este script as monta.

CLI:
    python -m ams.cliente_llm             # 20 ordens (roteiro do E4)
    python -m ams.cliente_llm --n 5      # lupa: poucas ordens, mesmo caminho
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

from ams import dados
from ams.config import ErroConfig, carregar_config
from ams.llm import ErroLlm, avaliar_lote
from ams.log import configurar_log
from ams.modelos import LeituraSensor, OrdemServico

# Emojis e acentos precisam sobreviver ao console do Windows mesmo quando a
# saída é redirecionada para arquivo (o PowerShell às vezes usa cp1252 aí).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DESCRICOES = [
    "Troca do insert de corte do eixo 3 e regulagem da folga.",
    "Inspeção elétrica do painel de comando com reaperto de bornes.",
    "Substituição do rolamento do mancal dianteiro e alinhamento.",
]

RAIZ_DO_PACOTE = Path(__file__).resolve().parent.parent.parent


def gerar_ordens(quadro, quantidade: int) -> list[OrdemServico]:
    """Cria N ordens de serviço a partir das primeiras linhas do dataset.

    Cada linha vira uma `LeituraSensor` e uma `OrdemServico`, com uma das
    três descrições de intervenção em rotação — o suficiente para o modelo
    ter contexto real variando os sensores.
    """
    ordens: list[OrdemServico] = []
    for indice, (_, linha) in enumerate(quadro.head(quantidade).iterrows()):
        leitura = LeituraSensor(
            udi=int(linha["udi"]),
            product_id=str(linha["product_id"]),
            tipo=str(linha["tipo"]),
            temperatura_ar=float(linha["temperatura_ar"]),
            temperatura_processo=float(linha["temperatura_processo"]),
            rotacao=int(linha["rotacao"]),
            torque=float(linha["torque"]),
            desgaste=int(linha["desgaste"]),
            falha=bool(linha["falha"]),
            twf=bool(linha["twf"]),
            hdf=bool(linha["hdf"]),
            pwf=bool(linha["pwf"]),
            osf=bool(linha["osf"]),
            rnf=bool(linha["rnf"]),
        )
        ordens.append(
            OrdemServico(
                identificador=f"OS-2026-{indice + 1:04d}",
                maquina=str(linha["product_id"]),
                leitura=leitura,
                descricao=DESCRICOES[indice % len(DESCRICOES)],
            )
        )
    return ordens


def principal() -> int:
    """Fluxo do E4-B3: dados → ordens → lote concorrente → tabela no console."""
    argumentos = _argumentos()
    try:
        config = carregar_config()
    except ErroConfig as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        print("O que fazer: confira o .env na raiz do projeto "
              "(copie do .env.example e preencha a chave).")
        return 1

    configurar_log(config.log_level,
                         caminho_arquivo=RAIZ_DO_PACOTE / "data" / "logs" / "ams.jsonl")

    try:
        dataset = dados.carregar(validar_com_pydantic=False)
        ordens = gerar_ordens(dataset.quadro, argumentos.n)
        modo = "📄 OFFLINE (fixtures)" if config.modo_offline else "🟢 ONLINE"
        print(f"⚙️  AMS — avaliador de risco de ordens de manutenção")
        print(f"   ordens: {len(ordens)} · dado: {dataset.fonte}")
        print(f"   modo: {modo} · modelo: {config.gemini_model}\n")

        inicio = time.perf_counter()
        pares = asyncio.run(
            avaliar_lote(ordens, config, com_ordens=True))
        duracao = time.perf_counter() - inicio

        print(_tabela(pares))
        ok = sum(1 for _, parecer in pares if parecer is not None)
        bloqueios = sum(1 for _, p in pares if p is not None and p.requer_bloqueio)
        print(f"\n✅ {ok}/{len(pares)} avaliadas · "
              f"🔒 {bloqueios} bloqueio(s) recomendado(s) · "
              f"{duracao:.1f} s · {len(pares) / duracao:.1f} ordens/s")
        print("📄 detalhe estruturado, linha a linha (JSON): data/logs/ams.jsonl")
        return 0
    except (ErroLlm, dados.ErroDados) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        print("O que fazer: se for cota (429), aguarde a janela ou use "
              "AMS_MODO_OFFLINE=1 no .env; se for o dataset, rode "
              "scripts/baixar-dados.py. Log completo em data/logs/ams.jsonl.")
        return 1


# valor já vem com ícone + palavra acentuada; a coluna Risco tem 8 de largura:
# ícone (2) + espaço (1) + palavra acentuada (5) fecha a conta.
ICONES_RISCO = {"baixo": "🟢 baixo", "medio": "🟡 médio", "alto": "🔴 alto"}
LARGURAS = [14, 9, 8, 8, 5, 12, 26]  # Ordem·Máquina·Risco·Bloqueio·Conf.·Normas·Justificativa


def _largura(texto: str) -> int:
    """Largura visível no terminal: emoji ocupa 2 colunas, o resto 1."""
    return sum(2 if ord(caractere) > 0x2600 else 1 for caractere in texto)


def _cortar(texto: str, largura: int) -> str:
    """Encolhe o texto para caber na coluna, sem quebrar palavra no meio."""
    texto = " ".join(texto.split())
    if _largura(texto) <= largura:
        return texto
    while _largura(texto + "…") > largura:
        texto = texto[:-1]
    return texto + "…"


def _linha_da_tabela(celulas: list[str]) -> str:
    celulas = [_cortar(celula, largura) for celula, largura in zip(celulas, LARGURAS)]
    celulas = [celula + " " * (largura - _largura(celula))
               for celula, largura in zip(celulas, LARGURAS)]
    return "│ " + " │ ".join(celulas) + " │"


def _tabela(pares: list) -> str:
    """A tabela final do console: um ícone por decisão, sem JSON à vista."""
    topo = "┌" + "┬".join("─" * (largura + 2) for largura in LARGURAS) + "┐"
    meio = "├" + "┼".join("─" * (largura + 2) for largura in LARGURAS) + "┤"
    base = "└" + "┴".join("─" * (largura + 2) for largura in LARGURAS) + "┘"
    linhas = [
        topo,
        _linha_da_tabela(["Ordem", "Máquina", "Risco", "Bloqueio", "Conf.",
                          "Normas", "Justificativa"]),
        meio,
    ]
    for ordem, parecer in pares:
        if parecer is None:
            linhas.append(_linha_da_tabela(
                [ordem.identificador, ordem.maquina, "—", "—", "—", "—",
                 "✖ falhou (ver data/logs/ams.jsonl)"]))
            continue
        risco = ICONES_RISCO.get(str(parecer.nivel_risco), f"• {parecer.nivel_risco}")
        bloqueio = "🔒 sim" if parecer.requer_bloqueio else "🔓 não"
        normas = ", ".join(parecer.normas_aplicaveis) if parecer.normas_aplicaveis else "—"
        linhas.append(_linha_da_tabela([
            ordem.identificador, ordem.maquina, risco, bloqueio,
            f"{parecer.confianca:.0%}", normas, parecer.justificativa,
        ]))
    linhas.append(base)
    return "\n".join(linhas)


def _argumentos() -> argparse.Namespace:
    leitor = argparse.ArgumentParser(
        prog="ams.cliente_llm",
        description="Cliente do modelo no AMS: avalia ordens em lote.",
    )
    leitor.add_argument("--n", type=int, default=20,
                        help="quantidade de ordens a processar (padrão: 20)")
    return leitor.parse_args()


if __name__ == "__main__":
    sys.exit(principal())
