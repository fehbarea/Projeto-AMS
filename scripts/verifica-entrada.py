"""Verifica o estado de entrada da D3 — o que esta disciplina assume pronto.

Para que serve
--------------
Este pacote é o projeto padrão (AMS) no estado em que a D3 COMEÇA: o estado
que a D2 deixou. Este programa é a prova. Ele roda a suíte do projeto, importa
cada módulo que o Contrato de Entrada da D3 promete, confere os artefatos,
e imprime item a item o que passou e o que falta.

Como rodar (na raiz do pacote extraído):

    PowerShell / Prompt de Comando:  python scripts\verifica-entrada.py
    Git Bash:                        python scripts/verifica-entrada.py

A suíte roda com o Python do AMBIENTE ATIVO — ative o venv do projeto antes
(ou chame o python do venv direto). Sem o venv, o programa termina com o
código 2 e diz o que fez falta.

Códigos de saída (o padrão dos conferidores do curso):
    0  tudo verde — o estado é o que a D3 assume;
    1  há item vermelho — o pacote existe, mas não está no estado prometido;
    2  não pôde examinar — estrutura ausente ou pytest indisponível.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Emojis e acentos precisam sobreviver ao console do Windows mesmo quando a
# saída é redirecionada para arquivo (o PowerShell às vezes usa cp1252 aí).
for _canal in (sys.stdout, sys.stderr):
    if hasattr(_canal, "reconfigure"):
        _canal.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parents[1]

ITENS: list[tuple[str, bool, str]] = []


def conferir(nome: str, ok: bool, detalhe: str = "") -> bool:
    ITENS.append((nome, ok, detalhe))
    return ok


def modulo_importavel(nome: str) -> tuple[bool, str]:
    import importlib

    try:
        importlib.import_module(nome)
        return True, ""
    except Exception as erro:  # noqa: BLE001 - o item é "importa ou não"
        return False, f"{type(erro).__name__}: {erro}"


def main() -> int:
    if not (RAIZ / "src" / "ams").is_dir():
        print("❌ não encontrei src/ams na raiz do pacote — extraia o zip inteiro.")
        return 2

    # -- 1. A suíte do projeto ------------------------------------------------
    modulo_pytest_ok, _ = modulo_importavel("pytest")
    if not modulo_pytest_ok:
        print("❌ o pytest não está no ambiente ativo — ative o venv do projeto")
        print("   (crie com: python -m venv .venv ; e instale com:")
        print("   python -m pip install -r requirements.txt) e rode de novo.")
        return 2
    ams_ok, ams_erro = modulo_importavel("ams")
    if not ams_ok:
        print("❌ o pacote do projeto não está instalado no ambiente ativo")
        print(f"   ({ams_erro}).")
        print("   Instale-o no modo editável e rode de novo:")
        print("       python -m pip install -e .")
        return 2
    import subprocess

    feito = subprocess.run(
        [sys.executable, "-m", "pytest", "tests", "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    resumo = "passou" if feito.returncode == 0 else "FALHOU"
    conferir("a suíte do projeto roda (pytest tests)", feito.returncode == 0,
             f"pytest terminou em {feito.returncode} ({resumo})")

    # -- 2. O repositório da D1 (a base) -------------------------------------
    conferir("src/ams com o módulo do projeto instalável",
             (RAIZ / "src" / "ams" / "config.py").is_file()
             and (RAIZ / "pyproject.toml").is_file())
    conferir("requirements.txt com versões fixadas",
             (RAIZ / "requirements.txt").is_file())
    conferir("notebooks/01-eda.ipynb — a análise exploratória",
             (RAIZ / "notebooks" / "01-eda.ipynb").is_file())
    conferir("data/ com o dataset do domínio (amostra + fixtures)",
             (RAIZ / "data" / "amostra").is_dir())
    conferir("dominio.md — o problema, a decisão e a fonte de dados",
             (RAIZ / "dominio.md").is_file())

    # -- 3. O contrato de entrada da D3, item a item -------------------------
    para_importar = {
        "ams.config": "configuração Pydantic (carregar_config, Configuracao, ErroConfig)",
        "ams.dados": "carga de dados do domínio",
        "ams.baseline": "o agente de linha de base da D2",
        "ams.llm": "o cliente do modelo, com respostas gravadas",
        "ams.log": "o log estruturado",
    }
    for modulo, papel in para_importar.items():
        ok, erro = modulo_importavel(modulo)
        conferir(f"import {modulo} — {papel}", ok, erro)

    try:
        from ams import baseline  # noqa: PLC0415 - conferência é o propósito

        tem_decidir = callable(getattr(baseline, "decidir", None))
        tem_estado = hasattr(baseline, "EstadoDaFrota")
        tem_casos = callable(getattr(baseline, "carregar_casos", None))
        conferir("baseline.decidir + EstadoDaFrota + carregar_casos disponíveis",
                 tem_decidir and tem_estado and tem_casos)
    except Exception:  # noqa: BLE001 - o item de import já registrou o erro
        conferir("baseline.decidir + EstadoDaFrota + carregar_casos disponíveis", False)

    from ams import config as _config  # noqa: PLC0415 - conferência é o propósito

    conferir("ams.config expõe carregar_config, Configuracao e ErroConfig",
             all(hasattr(_config, n) for n in ("carregar_config", "Configuracao", "ErroConfig")))

    conferir("agent-spec-AMS.md — a especificação com a medida de desempenho",
             (RAIZ / "agent-spec-AMS.md").is_file())
    conferir("relatorio-de-desempenho-AMS.md — o desempenho medido (≥ 30 casos)",
             (RAIZ / "relatorio-de-desempenho-AMS.md").is_file())
    conferir("analise-AMS.md — a análise do que o problema exige",
             (RAIZ / "analise-AMS.md").is_file())
    conferir("sete-dimensoes-AMS.md e catalogo-de-acoes-AMS.md — o ambiente e as ações",
             (RAIZ / "sete-dimensoes-AMS.md").is_file()
             and (RAIZ / "catalogo-de-acoes-AMS.md").is_file())

    # -- 4. Nenhuma credencial no pacote (regra de curso) ---------------------
    conferir("nenhum .env na raiz (só o .env.example)",
             not (RAIZ / ".env").exists())
    exemplo = RAIZ / ".env.example"
    # A regra de curso proíbe SEGREDO em pacote — não proíbe padrão de
    # configuração (o .env.example legítimo traz GEMINI_MODEL e o nível de log
    # preenchidos). O que se vigia: variável de segredo com valor.
    marcas_de_segredo = ("KEY", "TOKEN", "PASSWORD", "SECRET", "SENHA")
    if exemplo.is_file():
        com_segredo = [
            linha.split("=", 1)[0].strip()
            for linha in exemplo.read_text(encoding="utf-8").splitlines()
            if "=" in linha and not linha.lstrip().startswith("#")
            and linha.split("=", 1)[1].strip() != ""
            and any(m in linha.split("=", 1)[0].upper() for m in marcas_de_segredo)
        ]
        conferir(".env.example sem segredo nenhum", not com_segredo,
                 "variáveis de segredo com valor: " + ", ".join(com_segredo)
                 if com_segredo else "")
    else:
        conferir(".env.example presente", False, ".env.example ausente")

    # -- o veredito ------------------------------------------------------------
    print()
    falhas = 0
    for nome, ok, detalhe in ITENS:
        marca = "✅" if ok else "❌"
        if not ok:
            falhas += 1
        linha = f"{marca} {nome}"
        if detalhe and not ok:
            linha += f" — {detalhe}"
        print(linha)
    print()
    if falhas == 0:
        print("Estado de entrada da D3 VERIFICADO: é o que a disciplina assume.")
        return 0
    print(f"{falhas} item(ns) vermelho(s) — o pacote não está no estado prometido.")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as erro:  # noqa: BLE001 - o conferidor nunca morre sem dizer
        print(f"❌ não pôde examinar o pacote: {type(erro).__name__}: {erro}")
        sys.exit(2)
