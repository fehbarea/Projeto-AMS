"""Verificação de ambiente do AMS — Disciplina 1.

Diagnóstico do ambiente do aluno: Python, ambiente virtual, pacotes,
chave do Gemini, conectividade e itens de sistema. Cada verificação
imprime uma linha com ✅ ou ❌ e, quando falha, a instrução exata do
que fazer para resolver.

Feito para ser compreendido por quem nunca abriu um terminal: os nomes
estão em português e cada problema vem com o passo seguinte escrito.

Uso:
    python scripts/verifica-ambiente.py

Código de saída: 0 se todos os itens essenciais passaram; 1 caso
contrário (útil para o professor checar várias máquinas de uma vez).

Este script usa apenas a biblioteca padrão, para funcionar antes da
instalação dos pacotes do projeto.
"""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

# Emojis e acentos precisam sobreviver ao console do Windows mesmo quando a
# saída é redirecionada para arquivo (o PowerShell às vezes usa cp1252 aí).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path(__file__).resolve().parent.parent

# Pacotes exigidos pelo requirements.txt: (nome de import, nome no PyPI).
PACOTES = [
    ("pydantic", "pydantic"),
    ("numpy", "numpy"),
    ("pandas", "pandas"),
    ("scipy", "scipy"),
    ("pyarrow", "pyarrow"),
    ("matplotlib", "matplotlib"),
    ("seaborn", "seaborn"),
    ("sklearn", "scikit-learn"),
    ("polars", "polars"),
    ("duckdb", "duckdb"),
    ("httpx", "httpx"),
    ("dotenv", "python-dotenv"),
    ("fastapi", "fastapi"),
    ("uvicorn", "uvicorn"),
    ("pytest", "pytest"),
]

CHAVE_GEMINI = "GEMINI_API_KEY"
# Validado com chave real em 25/08/2026: HTTP 200, ~1,3 s, ~124 tokens.
# gemini-2.5-flash e gemini-2.0-flash retornam 404 (desligados).
# O .env do aluno sempre sobrepõe este valor.
MODELO_PADRAO = "gemini-3.5-flash-lite"
HOST_GEMINI = "generativelanguage.googleapis.com"
URL_GEMINI = f"https://{HOST_GEMINI}/v1beta/models"


@dataclass
class Resultado:
    """Resultado de uma verificação individual.

    essencial: se falhar, o aluno não consegue acompanhar a disciplina.
    aviso: falha que não impede a aula, mas precisa ser relatada.
    """

    nome: str
    ok: bool
    detalhe: str
    instrucao: str = ""
    essencial: bool = True
    aviso: str = ""


@dataclass
class Relatorio:
    """Acumula os resultados e contabiliza o essencial."""

    resultados: list[Resultado] = field(default_factory=list)

    def adicionar(self, resultado: Resultado) -> None:
        self.resultados.append(resultado)
        simbolo = "✅" if resultado.ok else ("⚠️ " if resultado.aviso else "❌")
        indice = len(self.resultados)
        print(f" [{indice:>2}] {resultado.nome:<38} {simbolo} {resultado.detalhe}")
        if not resultado.ok and resultado.instrucao:
            print(f"      → o que fazer: {resultado.instrucao}")

    @property
    def essenciais_falhos(self) -> int:
        return sum(1 for r in self.resultados if r.essencial and not r.ok and not r.aviso)

    @property
    def aprovados(self) -> int:
        return sum(1 for r in self.resultados if r.ok or r.aviso)


def verificar_python() -> Resultado:
    """Confere se o Python em uso é 3.12 ou superior."""
    if sys.version_info >= (3, 12):  # noqa: UP036 — roda também em Python antigo, é o diagnóstico
        versao = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        return Resultado("Python 3.12 ou superior", True, versao)
    return Resultado(
        "Python 3.12 ou superior",
        False,
        f"encontrei {sys.version_info.major}.{sys.version_info.minor}",
        "instale o Python 3.12+ em https://www.python.org/downloads/ "
        "(na instalação, marque a opção 'Add python.exe to PATH') e rode este script de novo",
    )


def verificar_venv() -> Resultado:
    """Confere se o script está rodando dentro do ambiente virtual do projeto."""
    ativa = sys.prefix != sys.base_prefix
    if ativa:
        return Resultado("Ambiente virtual ativo", True, sys.prefix)
    if (RAIZ / ".venv").exists():
        return Resultado(
            "Ambiente virtual ativo",
            False,
            "o Python em uso é o global, mas existe uma .venv no projeto",
            "ative a venv antes de continuar — no PowerShell: .\\.venv\\Scripts\\Activate.ps1 "
            "| no Linux/macOS: source .venv/bin/activate",
        )
    return Resultado(
        "Ambiente virtual ativo",
        False,
        "não existe ambiente virtual (.venv) neste projeto",
        "rode o script de configuração — no PowerShell: powershell -ExecutionPolicy Bypass "
        "-File scripts\\setup-windows.ps1 | no Linux/macOS: bash scripts/setup-unix.sh",
    )


def verificar_pacote(nome_import: str, nome_pypi: str) -> Resultado:
    """Confere se um pacote do requirements.txt está instalado e importável.

    Importar pode falhar por dois motivos MUITO diferentes: o pacote não está
    instalado, ou está instalado mas não carrega (típico de caminho de pasta
    longo demais para o Windows carregar as DLLs do pacote). A instrução muda
    completamente de um caso para o outro.
    """
    try:
        importlib.import_module(nome_import)
    except ImportError:
        try:
            importlib.metadata.version(nome_pypi)
            return Resultado(
                f"Pacote '{nome_pypi}'",
                False,
                "instalado, mas NÃO CARREGA (erro de DLL/caminho)",
                "provável limite de caminho do Windows: mova o projeto para uma pasta "
                "curta (ex.: C:\\CEDAGI\\D1), apague a pasta .venv e rode o setup de novo",
            )
        except importlib.metadata.PackageNotFoundError:
            return Resultado(
                f"Pacote '{nome_pypi}'",
                False,
                "não instalado",
                "com a venv ativa, rode: python -m pip install -r requirements.txt",
            )
    try:
        versao = importlib.metadata.version(nome_pypi)
    except importlib.metadata.PackageNotFoundError:
        versao = "instalado (versão desconhecida)"
    return Resultado(f"Pacote '{nome_pypi}'", True, versao)


def verificar_ruff() -> Resultado:
    """Confere se o ruff (ferramenta de linha de comando) está disponível.

    Procura primeiro junto ao interpretador em uso (a venv), depois no PATH:
    quando este diagnóstico roda sem a venv ativada no PATH — como o próprio
    setup faz — o which sozinho daria falso negativo.
    """
    locais = [Path(sys.prefix) / "Scripts" / "ruff.exe", Path(sys.prefix) / "bin" / "ruff"]
    caminho = next((str(local) for local in locais if local.exists()), None) or shutil.which("ruff")
    if caminho:
        return Resultado("Ferramenta 'ruff'", True, caminho)
    return Resultado(
        "Ferramenta 'ruff'",
        False,
        "comando não encontrado",
        "com a venv ativa, rode: python -m pip install -r requirements.txt",
    )


def ler_env(caminho: Path) -> dict[str, str]:
    """Lê um arquivo .env simples (CHAVE=valor), sem depender de pacotes extras.

    Ignora comentários (#) e linhas vazias; aceita valores entre aspas.
    """
    valores: dict[str, str] = {}
    if not caminho.exists():
        return valores
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, valor = linha.split("=", 1)
        valor = valor.strip().strip("'\"")
        valores[chave.strip()] = valor
    return valores


def verificar_env(valores: dict[str, str]) -> Resultado:
    """Confere se o .env existe e tem a chave do Gemini preenchida."""
    if not (RAIZ / ".env").exists():
        return Resultado(
            f".env com {CHAVE_GEMINI}",
            False,
            "arquivo .env não existe na raiz do projeto",
            "copie o modelo com: copy .env.example .env (Windows) ou cp .env.example .env "
            "(Linux/macOS), gere a chave em https://aistudio.google.com/apikey e cole o valor",
        )
    chave = valores.get(CHAVE_GEMINI, "").strip()
    if chave:
        return Resultado(f".env com {CHAVE_GEMINI}", True, f"preenchida ({len(chave)} caracteres)")
    return Resultado(
        f".env com {CHAVE_GEMINI}",
        False,
        "arquivo existe, mas a chave está vazia",
        "gere a chave em https://aistudio.google.com/apikey e cole o valor no .env",
    )


def verificar_conectividade() -> Resultado:
    """Confere se o host da API do Gemini responde na rede."""
    url = f"https://{HOST_GEMINI}"
    try:
        requisicao = urllib.request.Request(url, method="HEAD")
        urllib.request.urlopen(requisicao, timeout=10)
    except urllib.error.HTTPError:
        # Qualquer resposta HTTP (mesmo 404/405) prova que o host está alcançável.
        return Resultado("Conectividade com a API do Gemini", True, f"{HOST_GEMINI} respondeu")
    except (urllib.error.URLError, TimeoutError, OSError):
        return Resultado(
            "Conectividade com a API do Gemini",
            False,
            f"não consegui falar com {HOST_GEMINI}",
            "verifique o Wi-Fi/firewall (redes corporativas costumam bloquear) e tente de novo; "
            "se estiver sem internet, o curso tem modo offline — avise o professor antes da aula",
            essencial=False,
        )
    return Resultado("Conectividade com a API do Gemini", True, f"{HOST_GEMINI} respondeu")


def chamada_teste(chave: str, modelo: str) -> tuple[int, str]:
    """Faz uma chamada mínima (1 token de saída) ao Gemini.

    Retorna (código HTTP, corpo da resposta). Qualquer erro de rede vira
    código 0, para o chamador distinguir rede de resposta da API.
    """
    url = f"{URL_GEMINI}/{modelo}:generateContent"
    corpo = json.dumps(
        {
            "contents": [{"role": "user", "parts": [{"text": "Responda apenas: ok"}]}],
            "generationConfig": {"maxOutputTokens": 1, "temperature": 0},
        }
    ).encode("utf-8")
    requisicao = urllib.request.Request(url, data=corpo, method="POST")
    requisicao.add_header("Content-Type", "application/json")
    requisicao.add_header("x-goog-api-key", chave)
    try:
        with urllib.request.urlopen(requisicao, timeout=30) as resposta:
            return resposta.status, resposta.read().decode("utf-8")
    except urllib.error.HTTPError as erro:
        return erro.code, erro.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, ""


def verificar_chamada_gemini(valores: dict[str, str], rede_ok: bool) -> Resultado:
    """Faz uma chamada real de 1 token: valida chave, modelo e mede a latência."""
    nome = "Chamada de teste ao Gemini"
    chave = valores.get(CHAVE_GEMINI, "").strip()
    modelo = valores.get("GEMINI_MODEL", "").strip() or MODELO_PADRAO
    if not chave or not rede_ok:
        return Resultado(
            nome,
            False,
            "não executada (falta chave configurada ou conectividade)",
            "resolva primeiro os itens da chave e da conectividade acima",
            essencial=False,
        )

    inicio = time.perf_counter()
    codigo, corpo = chamada_teste(chave, modelo)
    latencia = int((time.perf_counter() - inicio) * 1000)

    if codigo == 200:
        return Resultado(nome, True, f"modelo {modelo} respondeu em {latencia} ms")
    if codigo in (400, 401, 403):
        return Resultado(
            nome,
            False,
            f"HTTP {codigo}: chave inválida ou sem permissão",
            "gere uma chave nova em https://aistudio.google.com/apikey e atualize o .env",
        )
    if codigo == 404:
        return Resultado(
            nome,
            False,
            f"HTTP 404: o modelo '{modelo}' não está disponível para esta chave",
            "verifique os modelos ativos em aistudio.google.com e ajuste GEMINI_MODEL no .env",
        )
    if codigo == 429:
        return Resultado(
            nome,
            False,
            "HTTP 429: cota gratuita atingida agora (chave e modelo estão corretos)",
            "aguarde a janela de cota (renova a cada minuto/dia) — o curso tem modo offline "
            "para esta situação; nada a corrigir agora",
            essencial=False,
            aviso="cota esgotada no momento",
        )
    if codigo == 0:
        return Resultado(
            nome,
            False,
            "a conexão falhou no meio da chamada",
            "rede instável; rode de novo em alguns minutos e, se persistir, avise o professor",
            essencial=False,
        )
    detalhe = json.loads(corpo or "{}").get("error", {}).get("message", corpo[:120])
    return Resultado(
        nome,
        False,
        f"HTTP {codigo}: {detalhe}",
        "copie esta mensagem e envie ao professor antes da aula",
        essencial=False,
    )


def verificar_escrita_dados() -> Resultado:
    """Confere permissão de escrita na pasta data/ do projeto."""
    pasta = RAIZ / "data"
    try:
        pasta.mkdir(exist_ok=True)
        teste = pasta / ".verificacao-escrita.tmp"
        teste.write_text("teste", encoding="utf-8")
        teste.unlink()
    except OSError as erro:
        return Resultado(
            "Permissão de escrita em data/",
            False,
            f"não consegui criar/escrever em {pasta}",
            f"feche editores que possam travar a pasta e verifique a mensagem: {erro}",
        )
    return Resultado("Permissão de escrita em data/", True, str(pasta))


def _rodar_comando(args: list[str]) -> str | None:
    """Roda um comando externo e devolve a saída, ou None se ele não existir."""
    try:
        concluido = subprocess.run(
            args, capture_output=True, text=True, encoding="utf-8", timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return (concluido.stdout or "").strip()


def verificar_git() -> Resultado:
    """Confere se o Git está instalado e com identidade configurada."""
    if shutil.which("git") is None:
        return Resultado(
            "Git instalado e configurado",
            False,
            "comando 'git' não encontrado",
            "baixe em https://git-scm.com/download/win e instale (opções padrão servem)",
            essencial=False,
        )
    nome = _rodar_comando(["git", "config", "--global", "user.name"])
    email = _rodar_comando(["git", "config", "--global", "user.email"])
    if nome and email:
        return Resultado("Git instalado e configurado", True, f"{nome} <{email}>")
    return Resultado(
        "Git instalado e configurado",
        False,
        "Git presente, mas sem user.name/user.email (o primeiro commit falharia)",
        "rode: git config --global user.name \"Seu Nome\" e "
        "git config --global user.email \"seu@email.com\"",
        essencial=False,
    )


def verificar_disco() -> Resultado:
    """Confere se há pelo menos 2 GB livres para os dados e a venv."""
    uso = shutil.disk_usage(RAIZ)
    livres_gb = uso.free / 1024**3
    if livres_gb >= 2:
        return Resultado("Espaço em disco (mín. 2 GB)", True, f"{livres_gb:.1f} GB livres")
    return Resultado(
        "Espaço em disco (mín. 2 GB)",
        False,
        f"{livres_gb:.1f} GB livres",
        "libere espaço (a venv com os pacotes ocupa ~2 GB) e rode o setup de novo",
        essencial=False,
    )


def principal() -> int:
    """Executa todas as verificações e imprime o resumo final."""
    print("=" * 68)
    print(" AMS · verificação de ambiente — Disciplina 1")
    print(" Especialização em Desenvolvimento de Agentes Inteligentes · UTFPR")
    print(f" Projeto: {RAIZ}")
    print("-" * 68)

    relatorio = Relatorio()
    relatorio.adicionar(verificar_python())
    relatorio.adicionar(verificar_venv())
    for nome_import, nome_pypi in PACOTES:
        relatorio.adicionar(verificar_pacote(nome_import, nome_pypi))
    relatorio.adicionar(verificar_ruff())

    valores = ler_env(RAIZ / ".env")
    relatorio.adicionar(verificar_env(valores))
    rede = verificar_conectividade()
    relatorio.adicionar(rede)
    relatorio.adicionar(verificar_chamada_gemini(valores, rede.ok))
    relatorio.adicionar(verificar_escrita_dados())
    relatorio.adicionar(verificar_git())
    relatorio.adicionar(verificar_disco())

    total = len(relatorio.resultados)
    aprovados = relatorio.aprovados
    essenciais_falhos = relatorio.essenciais_falhos
    print("-" * 68)
    print(f" {aprovados} de {total} verificações passaram.")
    if essenciais_falhos:
        print(f" ⚠️  {essenciais_falhos} item(ns) CRÍTICO(S) falharam — resolva antes da aula")
        print("   seguindo as instruções marcadas com '→ o que fazer' acima,")
        print("   ou escreva para a coordenação com esta tela anexada.")
    else:
        print(" ✅ Todos os itens críticos passaram. Seu ambiente está pronto!")
    print("=" * 68)
    return 1 if essenciais_falhos else 0


if __name__ == "__main__":
    sys.exit(principal())
