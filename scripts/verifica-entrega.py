"""Verificação de entrega — o Contrato de Saída da D1, item por item.

Rode na RAIZ do seu repositório, antes de entregar a N2:

    python verifica-entrega.py

(o script roda de qualquer lugar; ele examina a pasta em que você está)

O que ele faz: confere PRESENÇA e FORMA dos artefatos do Contrato de Saída —
estrutura de pastas, Git, .env fora do versionamento, requirements, README,
dominio.md, dataset, notebook, funções tipadas, testes e o cliente_llm.py.

O que ele NÃO faz: avaliar qualidade ou dar nota. "Tudo verde" significa "o
contrato está cumprido", não "nota máxima" — julgar a análise e o código é
trabalho do professor, com a rubrica da N2.

Itens CRÍTICOS: o contrato não está cumprido sem eles (código de saída 1).
Itens RECOMENDADOS: a entrega passa, mas enfraquece na rubrica.

Este script usa apenas a biblioteca padrão — funciona antes de instalar
qualquer pacote. Os itens que executam código (pytest, cliente do modelo) usam o Python
da .venv do projeto, se existir; sem .venv eles falham com instrução.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# Emojis e acentos precisam sobreviver ao console do Windows mesmo quando a
# saída é redirecionada para arquivo (o PowerShell às vezes usa cp1252 aí).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = Path.cwd() if len(sys.argv) < 2 else Path(sys.argv[1]).resolve()

PASTAS_IGNORADAS = {".venv", "venv", ".git", "__pycache__", "node_modules", ".pytest_cache",
                    ".ruff_cache", "build", "dist"}
EXTENSOES_DE_DADOS = {".csv", ".parquet", ".json", ".xlsx", ".txt", ".tsv", ".feather"}
# O provedor emite chave em DOIS formatos, e este verificador precisa achar os
# dois — chave que ele não acusa é chave que vai para o repositório do aluno:
#
#   1. o antigo, "AIza" + exatamente 35 caracteres de [0-9A-Za-z_-] — COM
#      hífen, que é caractere normal do alfabeto do provedor. Medido pela D12
#      em 13/09/2026: com o padrão anterior (30+, sem hífen), 37,4% de 100.000
#      chaves sintéticas no formato real escapavam;
#   2. o novo, "AQ." seguido de 25 ou mais caracteres, que o Google passou a
#      emitir e que apareceu na turma em 17/09/2026. Aqui NÃO se fixa o que vem
#      depois do ponto: o formato do fornecedor já mudou uma vez.
#
# As chaves DIDÁTICAS do curso não são separáveis pelo formato (a fictícia dos
# testes tem os mesmos 35 caracteres), então a exclusão delas é pelo CONTEÚDO:
# casamento que contém "teste" não é acusado — é a convenção das chaves de
# prova do curso (ver tests/test_config_e_log.py).
PADRAO_DE_CHAVE = re.compile(r"AIza[0-9A-Za-z_-]{35}|AQ\.[0-9A-Za-z_-]{25,}")
MARCA_DE_CHAVE_DIDATICA = "teste"
# A seção do agente não precisa ser a ÚLTIMA do notebook (o 01-eda tem
# "Antes de entregar" depois dela): procura-se a EXPRESSÃO, em qualquer
# posição, no notebook e no dominio.md.
ROTULO_SECAO_AGENTE = "o que meu agente precisaria saber para decidir isso"


@dataclass
class Item:
    """Um item verificado.

    critico: sem ele, o Contrato de Saída não está cumprido (exit 1).
    recomendado: a entrega passa, mas fica fraca na rubrica.
    """

    nome: str
    ok: bool
    detalhe: str
    instrucao: str = ""
    critico: bool = True


@dataclass
class Relatorio:
    """Acumula os itens e contabiliza os críticos."""

    itens: list[Item] = field(default_factory=list)

    def adicionar(self, item: Item) -> None:
        self.itens.append(item)
        simbolo = "✅" if item.ok else "❌"
        tipo = "crítico    " if item.critico else "recomendado"
        indice = len(self.itens)
        print(f" [{indice:>2}] {tipo}  {item.nome:<44} {simbolo} {item.detalhe}")
        if not item.ok and item.instrucao:
            print(f"      → o que fazer: {item.instrucao}")

    @property
    def criticos_falhos(self) -> int:
        return sum(1 for i in self.itens if i.critico and not i.ok)

    @property
    def recomendados_falhos(self) -> int:
        return sum(1 for i in self.itens if not i.critico and not i.ok)

    @property
    def aprovados(self) -> int:
        return sum(1 for i in self.itens if i.ok)


# ---------------------------------------------------------------------------
# Utilitários


def _arquivos_python(pasta: Path) -> list[Path]:
    """Lista os .py do projeto, fora das pastas ignoradas."""
    if not pasta.exists():
        return []
    achados = []
    for caminho in pasta.rglob("*.py"):
        if any(parte in PASTAS_IGNORADAS for parte in caminho.parts):
            continue
        achados.append(caminho)
    return achados


def _python_da_venv() -> Path | None:
    """Devolve o interpretador da .venv do projeto, se existir."""
    candidatos = [RAIZ / ".venv" / "Scripts" / "python.exe", RAIZ / ".venv" / "bin" / "python"]
    return next((c for c in candidatos if c.exists()), None)


def _rodar(
    args: list[str], timeout: int, env_extra: dict[str, str] | None = None
) -> tuple[int, str]:
    """Roda um comando e devolve (código de saída, saída combinada).

    Exceções viram código -1 com a mensagem — quem chama decide o que dizer.
    """
    ambiente = os.environ.copy()
    if env_extra:
        ambiente.update(env_extra)
    try:
        concluido = subprocess.run(
            args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            cwd=RAIZ,
            env=ambiente,
        )
        saida = (concluido.stdout or "") + (concluido.stderr or "")
        return concluido.returncode, saida.strip()
    except subprocess.TimeoutExpired:
        return -1, f"(não terminou em {timeout} s)"
    except OSError as erro:
        return -1, str(erro)


def _git_ls_files() -> list[str]:
    """Lista os arquivos rastreados pelo Git (vazio se não for repositório)."""
    codigo, saida = _rodar(["git", "ls-files"], timeout=30)
    if codigo != 0:
        return []
    return [linha.strip() for linha in saida.splitlines() if linha.strip()]


def _textos_rastreados(rastreados: list[str]) -> list[tuple[str, str]]:
    """Lê os arquivos texto rastreados (até 1 MB cada) para varrer segredos."""
    textos = []
    for nome in rastreados:
        if Path(nome).suffix.lower() not in {".py", ".md", ".txt", ".toml", ".cfg", ".ini",
                                             ".yml", ".yaml", ".json", ".sh", ".ps1", ".env"}:
            continue
        caminho = RAIZ / nome
        try:
            if caminho.stat().st_size > 1_000_000:
                continue
            textos.append((nome, caminho.read_text(encoding="utf-8", errors="replace")))
        except OSError:
            continue
    return textos


def _mascarar(chave: str) -> str:
    """Mostra só o começo e o fim de uma chave — nunca o valor inteiro."""
    return f"{chave[:10]}...{chave[-4:]}" if len(chave) > 16 else "(curta demais)"


def _contar_registros_csv(caminho: Path) -> int | None:
    """Conta as linhas de dados de um CSV (None se não der para ler)."""
    import csv

    try:
        with caminho.open(encoding="utf-8", errors="replace", newline="") as arquivo:
            leitor = csv.reader(arquivo)
            return max(sum(1 for _ in leitor) - 1, 0)
    except OSError:
        return None


# ---------------------------------------------------------------------------
# Verificações — estrutura


def verificar_parece_projeto() -> bool:
    """Confere que a pasta atual parece um projeto Python antes de prosseguir."""
    marcadores = [RAIZ / "src", RAIZ / "tests", RAIZ / "notebooks", RAIZ / ".git",
                  RAIZ / "requirements.txt", RAIZ / "pyproject.toml", RAIZ / "dominio.md"]
    return any(m.exists() for m in marcadores)


def verificar_estrutura() -> list[Item]:
    """Confere as pastas exigidas pela estrutura padrão do curso."""
    itens = []

    pacotes = [p for p in RAIZ.glob("src/*/") if list(p.glob("*.py"))]
    itens.append(Item(
        "Pasta src/ com um pacote dentro",
        bool(pacotes),
        f"encontrei {', '.join(p.name for p in pacotes)}"
        if pacotes else "src/ não existe ou está vazia",
        "crie src/<nome-do-seu-projeto>/ e mova seu código para lá "
        "(é o item 5 da N2 e a linha 6 do Contrato de Saída)",
    ))

    testes = list(RAIZ.glob("tests/test_*.py")) + list(RAIZ.glob("test_*.py"))
    itens.append(Item(
        "Pasta tests/ com testes",
        bool(testes),
        f"{len(testes)} arquivo(s) de teste" if testes else "nenhum test_*.py encontrado",
        "crie tests/test_alguma_coisa.py — a N2 exige no mínimo 3 testes passando",
    ))

    notebooks = list(RAIZ.glob("notebooks/*.ipynb"))
    itens.append(Item(
        "Pasta notebooks/ com .ipynb",
        bool(notebooks),
        f"{len(notebooks)} notebook(s)" if notebooks else "notebooks/ não existe",
        "crie notebooks/01-eda.ipynb — é a linha 5 do Contrato de Saída "
        "(D3, D5 e D7 abrem este arquivo)",
    ))

    dados = next((nome for nome in ("dados", "data") if (RAIZ / nome).exists()
                  and any((RAIZ / nome).glob("*"))), None)
    itens.append(Item(
        "Pasta de dados (dados/ ou data/)",
        dados is not None,
        f"{dados}/" if dados else "nem dados/ nem data/ com arquivos",
        "o dataset bruto do seu domínio vive aí (linha 4 do Contrato de Saída)",
    ))

    itens.append(Item(
        "Pasta scripts/",
        (RAIZ / "scripts").exists(),
        "existe" if (RAIZ / "scripts").exists() else "não existe",
        "recomendada (a estrutura padrão do curso tem scripts/); sem ela, "
        "o script de download de dados precisa morar em outro lugar óbvio",
        critico=False,
    ))
    return itens


def verificar_git(rastreados: list[str]) -> list[Item]:
    """Confere repositório Git, .env fora do versionamento e sem chaves vazando."""
    itens = []
    eh_git = (RAIZ / ".git").exists()
    itens.append(Item(
        "É um repositório Git",
        eh_git,
        "com histórico" if eh_git else "não encontrei .git aqui",
        "rode git init e faça o primeiro commit — 15 meses de projeto vivem de histórico",
    ))
    if not eh_git:
        return itens

    env_rastreado = any(nome == ".env" or nome.endswith("/.env") for nome in rastreados)
    itens.append(Item(
        ".env fora do versionamento",
        not env_rastreado,
        ".env não está no Git" if not env_rastreado else ".env ESTÁ sendo versionado",
        "rode: git rm --cached .env  (depois confira que .env está no .gitignore e commite)",
    ))

    gitignore = RAIZ / ".gitignore"
    menciona_env = gitignore.exists() and ".env" in gitignore.read_text(encoding="utf-8",
                                                                        errors="replace")
    itens.append(Item(
        ".gitignore cobre .env (e .venv/)",
        menciona_env,
        ".gitignore menciona .env" if menciona_env else ".gitignore não menciona .env",
        "acrescente ao .gitignore as linhas: .env, .venv/, __pycache__/",
        critico=False,
    ))

    vazamentos = []
    for nome, texto in _textos_rastreados(rastreados):
        for achado in PADRAO_DE_CHAVE.finditer(texto):
            if MARCA_DE_CHAVE_DIDATICA in achado.group().lower():
                continue  # chave didática do curso — ver PADRAO_DE_CHAVE
            linha = texto.count("\n", 0, achado.start()) + 1
            vazamentos.append(f"{nome}:{linha} ({_mascarar(achado.group())})")
    itens.append(Item(
        "Nenhuma chave do Gemini nos arquivos versionados",
        not vazamentos,
        "nada encontrado" if not vazamentos else f"ENCONTREI em: {'; '.join(vazamentos)}",
        "remova a chave do arquivo, gere outra em aistudio.google.com/apikey "
        "(a antiga está comprometida) e use o .env, que fica fora do Git",
    ))
    return itens


def verificar_env_example() -> Item:
    """Confere que existe .env.example com a chave vazia (nunca preenchida)."""
    exemplo = RAIZ / ".env.example"
    if not exemplo.exists():
        if (RAIZ / ".env").exists():
            # o .env.example pode ter sido renomeado para .env pelo próprio
            # aluno — isso é legítimo; o item vira recomendação, não bloqueio.
            return Item(
                ".env.example presente",
                True,
                "não existe (o .env.example foi renomeado para .env)",
                "quando puder, recrie o .env.example com a linha GEMINI_API_KEY= "
                "(vazia) — quem clona seu repositório precisa saber quais "
                "variáveis o projeto espera",
                critico=False,
            )
        return Item(
            ".env.example presente",
            False,
            "arquivo não existe na raiz",
            "crie o .env.example com a linha GEMINI_API_KEY= (vazia) — quem clona seu "
            "repositório precisa saber quais variáveis o projeto espera",
        )
    texto = exemplo.read_text(encoding="utf-8", errors="replace")
    chave = re.search(r"^GEMINI_API_KEY=(.*)$", texto, re.MULTILINE)
    if chave is None:
        return Item(
            ".env.example presente",
            True,
            "existe (sem a linha GEMINI_API_KEY=)",
            "acrescente a linha GEMINI_API_KEY= (vazia) para documentar a variável do curso",
            critico=False,
        )
    if chave.group(1).strip():
        return Item(
            ".env.example presente",
            False,
            "existe, mas GEMINI_API_KEY está PREENCHIDA",
            "uma chave no .env.example vai para o Git — remova o valor, deixe GEMINI_API_KEY= "
            "vazia e gere uma chave nova em aistudio.google.com/apikey",
        )
    return Item(".env.example presente", True, "existe, com GEMINI_API_KEY= vazia")


def verificar_dependencias() -> Item:
    """Confere requirements.txt ou pyproject.toml, e se as versões estão fixadas."""
    requirements = RAIZ / "requirements.txt"
    pyproject = RAIZ / "pyproject.toml"
    if requirements.exists():
        texto = requirements.read_text(encoding="utf-8", errors="replace")
        fixadas = [linha for linha in texto.splitlines()
                   if "==" in linha or "~=" in linha or ".*" in linha]
        soltas = [linha for linha in texto.splitlines()
                  if linha.strip() and not linha.startswith("#") and not linha.startswith("-")
                  and linha not in fixadas]
        if soltas:
            return Item(
                "requirements.txt com versões fixadas",
                False,
                f"requirements.txt existe, mas {len(soltas)} pacote(s) sem versão",
                "a linha 2 do Contrato de Saída pede versões fixadas — troque "
                "'pandas' por 'pandas==2.2.*' (rode pip freeze para ver o que você usa)",
                critico=False,
            )
        return Item("requirements.txt ou pyproject.toml", True,
                    f"requirements.txt com {len(fixadas)} pacote(s) fixado(s)")
    if pyproject.exists():
        return Item("requirements.txt ou pyproject.toml", True, "pyproject.toml encontrado")
    return Item(
        "requirements.txt ou pyproject.toml",
        False,
        "nenhum dos dois existe na raiz",
        "gere com pip freeze > requirements.txt (com a venv ativa) — sem isto, "
        "ninguém consegue reproduzir seu ambiente",
    )


def verificar_readme() -> Item:
    """Confere que o README existe e explica instalar/executar."""
    readme = RAIZ / "README.md"
    if not readme.exists():
        return Item(
            "README.md",
            False,
            "não existe na raiz",
            "crie o README.md com: o que é o projeto, como instalar, como executar "
            "(item 8 da N2 — três comandos que funcionam)",
        )
    texto = readme.read_text(encoding="utf-8", errors="replace").lower()
    fala_de_instalar = any(p in texto for p in ("instal", "pip install", "setup"))
    fala_de_executar = any(p in texto for p in ("execut", "rodar", "como usar", "python "))
    if fala_de_instalar and fala_de_executar:
        return Item("README.md", True, "explica como instalar e como executar")
    return Item(
        "README.md",
        True,
        "existe, mas não encontrei como instalar/executar",
        "acrescente duas seções: 'Como instalar' e 'Como executar', com comandos "
        "que você mesmo testou num clone novo",
        critico=False,
    )


def verificar_dominio() -> Item:
    """Confere dominio.md na raiz (ou em docs/, com aviso)."""
    caminho = RAIZ / "dominio.md"
    if not caminho.exists():
        achados = [p for p in RAIZ.rglob("dominio.md")
                   if not any(parte in PASTAS_IGNORADAS for parte in p.parts)]
        if achados:
            return Item(
                "dominio.md na raiz",
                True,
                f"encontrei em {achados[0].relative_to(RAIZ)} (a D2 procura na raiz)",
                "mova para a raiz — a próxima disciplina abre este arquivo pelo caminho padrão",
                critico=False,
            )
        return Item(
            "dominio.md na raiz",
            False,
            "não encontrei em lugar nenhum",
            "é a linha 3 do Contrato de Saída: problema, decisão a automatizar e fonte "
            "de dados, numa página — a D2 transforma isto no agent-spec.md no primeiro dia",
        )
    palavras = len(caminho.read_text(encoding="utf-8", errors="replace").split())
    if palavras < 300:
        return Item(
            "dominio.md na raiz",
            True,
            f"existe, mas está curto ({palavras} palavras; a AO1 pediu 400–600)",
            "desenvolva: problema, decisão a automatizar, fonte de dados — "
            "é a matéria-prima do agent-spec.md da D2",
            critico=False,
        )
    return Item("dominio.md na raiz", True, f"existe ({palavras} palavras)")


def verificar_dataset() -> list[Item]:
    """Confere dataset bruto: presença, tamanho e script de download."""
    itens = []
    pasta_dados = next((RAIZ / nome for nome in ("dados", "data")
                        if (RAIZ / nome).exists()), None)
    arquivos = []
    if pasta_dados is not None and pasta_dados.is_dir():
        arquivos = [p for p in pasta_dados.iterdir() if p.suffix.lower() in EXTENSOES_DE_DADOS]
        arquivos += [p for sub in pasta_dados.iterdir() if sub.is_dir()
                     for p in sub.iterdir() if p.suffix.lower() in EXTENSOES_DE_DADOS]
    pasta_scripts = RAIZ / "scripts"
    tem_script = pasta_scripts.exists() and any(
        "baixar" in p.name.lower() for p in pasta_scripts.glob("*.py"))

    if arquivos:
        caminho = arquivos[0]
        registros = (_contar_registros_csv(caminho)
                     if caminho.suffix.lower() == ".csv" else None)
        if registros is not None and registros < 500 and not tem_script:
            itens.append(Item(
                "Dataset bruto (≥ 500 registros)",
                False,
                f"{caminho.name}: {registros} registros, sem script de download",
                "a linha 4 do Contrato de Saída pede ≥ 500 registros (ou ≥ 50 documentos) "
                "versionados OU um script que baixe o completo — hoje não há nenhum dos dois",
            ))
        elif registros is not None and registros < 500:
            itens.append(Item(
                "Dataset bruto (≥ 500 registros)",
                True,
                f"{caminho.name}: {registros} registros locais + script de download "
                "(o contrato aceita a dupla)",
            ))
        else:
            detalhe = caminho.name
            if registros is not None:
                detalhe += f" ({registros} registros)"
            itens.append(Item("Dataset bruto (≥ 500 registros)", True, detalhe))
    elif tem_script:
        itens.append(Item("Dataset bruto (≥ 500 registros)", True,
                          "via scripts/ com download (confira o resultado rodando o script)"))
    else:
        itens.append(Item(
            "Dataset bruto (≥ 500 registros)",
            False,
            "nenhum arquivo de dados em dados/ (ou data/) e nenhum script de download",
            "versione o arquivo bruto na pasta de dados OU entregue o script que o baixa "
            "(linha 4 do Contrato de Saída — D5 treina sobre isto)",
        ))
    return itens


def verificar_notebook() -> list[Item]:
    """Confere a seção do agente ("O que meu agente precisaria saber...").

    O NÚMERO de perguntas não é verificado aqui de propósito: um contador de
    títulos numerados erra nos dois sentidos (títulos que fogem do padrão
    viram pergunta invisível — viu-se com "### Pergunta 1 (exemplo resolvido)"
    não casando), e é o professor quem julga se são perguntas com resposta em
    número. O que a máquina confere é a PRESENÇA da expressão da seção do
    agente — em qualquer posição do notebook (não precisa ser a última; o
    01-eda tem "Antes de entregar" depois dela).
    """
    notebooks = sorted(RAIZ.glob("notebooks/*.ipynb"))
    if not notebooks:
        return [Item(
            "Seção 'O que meu agente precisaria saber para decidir isso?'",
            False,
            "nenhum .ipynb em notebooks/",
            "crie notebooks/01-eda.ipynb (linha 5 do Contrato de Saída) com as "
            "perguntas da AO1 + as perguntas 6 a 8 do D1-16, e a seção do agente — "
            "que vira o agent-spec.md da D2 (item 4 da N2)",
        )]

    caminho = notebooks[0]
    for preferido in ["01-eda.ipynb", "eda"]:
        achado = next((n for n in notebooks if preferido in n.name), None)
        if achado:
            caminho = achado
            break
    try:
        conteudo = json.loads(caminho.read_text(encoding="utf-8"))
        markdown = "\n".join("".join(c.get("source", [])) for c in conteudo.get("cells", [])
                             if c.get("cell_type") == "markdown")
    except (json.JSONDecodeError, OSError) as erro:
        return [Item(
            "Seção 'O que meu agente precisaria saber para decidir isso?'",
            False,
            f"não consegui ler {caminho.name}: {erro}",
            "abra o notebook no Jupyter, salve e rode esta verificação de novo",
        )]

    tem_secao = ROTULO_SECAO_AGENTE in markdown.lower()
    if not tem_secao and (RAIZ / "dominio.md").exists():
        texto_dom = (RAIZ / "dominio.md").read_text(encoding="utf-8", errors="replace").lower()
        tem_secao = ROTULO_SECAO_AGENTE in texto_dom
    return [Item(
        "Seção 'O que meu agente precisaria saber para decidir isso?'",
        tem_secao,
        ("presente no notebook" if ROTULO_SECAO_AGENTE in markdown.lower()
         else "presente no dominio.md") if tem_secao else "não encontrei a expressão",
        "acrescente a seção do agente (item 4 da N2): o que falta saber para decidir — "
        "é o primeiro rascunho do agent-spec.md que a D2 abre no primeiro dia",
    )]


def _funcoes_tipadas(arquivos: list[Path]) -> list[str]:
    """Nomes das funções com retorno anotado e ao menos um parâmetro anotado."""
    achadas = []
    for caminho in arquivos:
        try:
            arvore = ast.parse(caminho.read_text(encoding="utf-8", errors="replace"))
        except (SyntaxError, OSError):
            continue
        for no in ast.walk(arvore):
            if not isinstance(no, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            if no.name.startswith("_") and no.name != "__init__":
                continue
            anota_retorno = no.returns is not None
            anota_param = any(a.annotation is not None for a in no.args.args
                              + no.args.kwonlyargs if a.arg != "self")
            if anota_retorno and anota_param:
                achadas.append(f"{caminho.stem}.{no.name}")
    return achadas


def verificar_codigo() -> list[Item]:
    """Confere ≥ 3 funções tipadas em src/ e o uso de Pydantic (linha 7)."""
    arquivos = _arquivos_python(RAIZ / "src")
    if not arquivos:
        arquivos = [p for p in _arquivos_python(RAIZ) if p.parent == RAIZ]

    tipadas = _funcoes_tipadas(arquivos)
    itens = [Item(
        "src/ com ≥ 3 funções tipadas",
        len(tipadas) >= 3,
        f"{len(tipadas)} função(ões) com tipo em {len(arquivos)} arquivo(s)",
        "a N2 exige ≥ 3 funções com anotações de tipo e docstring — "
        "anote parâmetros e retorno (def f(x: str) -> int)",
    )]

    texto_src = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in arquivos)
    tem_modelo = "BaseModel" in texto_src or "create_model" in texto_src
    itens.append(Item(
        "Modelo Pydantic no src/",
        tem_modelo,
        "encontrei uso de BaseModel" if tem_modelo else "não encontrei BaseModel em src/",
        "linha 7 do Contrato de Saída: uma classe herdando de pydantic.BaseModel "
        "valida dados externos — é a peça que valida a resposta do LLM",
    ))
    return itens


def verificar_testes() -> Item:
    """Roda o pytest do projeto e confere ≥ 3 testes aprovados."""
    python = _python_da_venv() or (sys.executable if sys.prefix != sys.base_prefix else None)
    if python is None:
        return Item(
            "≥ 3 testes passando (pytest)",
            False,
            "não encontrei .venv nem estou rodando dentro de uma",
            "crie/ative a venv e instale os requisitos antes desta checagem "
            "(python -m venv .venv; ative; pip install -r requirements.txt)",
        )
    # Sem -q: com o dobro de "quiet" (aqui + addopts do pyproject) o pytest 9
    # deixa de imprimir a linha final "N passed" que esta checagem lê.
    codigo, saida = _rodar([str(python), "-m", "pytest", "--tb=no"], timeout=300)
    if codigo == -1 and "não terminou" in saida:
        return Item(
            "≥ 3 testes passando (pytest)",
            False,
            saida,
            "testes que não terminam em 5 min geralmente esperam rede — "
            "confira se não falta o modo offline (AMS_MODO_OFFLINE=1)",
        )
    aprovados = re.search(r"(\d+) passed", saida)
    falhos = re.search(r"(\d+) failed", saida)
    if aprovados and int(aprovados.group(1)) >= 3 and codigo == 0:
        return Item("≥ 3 testes passando (pytest)", True,
                    f"{aprovados.group(1)} aprovados")
    if aprovados and int(aprovados.group(1)) >= 3 and (falhos or codigo != 0):
        return Item(
            "≥ 3 testes passando (pytest)",
            False,
            f"{aprovados.group(1)} aprovados, mas {falhos.group(1) if falhos else 'houve'} "
            f"falha(s) — a entrega exige a suíte verde",
            "rode pytest -q você mesmo e corrija as falhas antes de entregar",
        )
    return Item(
        "≥ 3 testes passando (pytest)",
        False,
        (saida[-200:] if saida else "o pytest não rodou"),
        "a N2 exige ≥ 3 testes verificando comportamento real, e todos passando",
    )


def verificar_cliente() -> list[Item]:
    """Confere cliente_llm.py: existe, compila e roda em modo offline."""
    candidatos = [p for p in RAIZ.rglob("cliente_llm.py")
                  if not any(parte in PASTAS_IGNORADAS for parte in p.parts)]
    if not candidatos:
        return [Item(
            "cliente_llm.py presente",
            False,
            "nenhum arquivo com esse nome no projeto",
            "é o entregável do laboratório 06 (E4) e o item 7 da N2 — sem ele, "
            "a D2 não tem o que abrir no primeiro laboratório",
        ), Item(
            "cliente_llm.py roda em modo offline",
            False,
            "sem o arquivo não há o que rodar",
            "mesmo item acima",
        )]

    caminho = candidatos[0]
    try:
        compile(caminho.read_text(encoding="utf-8", errors="replace"), str(caminho), "exec")
        compila = True
    except (SyntaxError, OSError) as erro:
        compila = False
        erro_compilacao = str(erro)

    itens = [Item(
        "cliente_llm.py presente",
        compila,
        f"{caminho.relative_to(RAIZ)}" if compila
        else f"{caminho.relative_to(RAIZ)} não compila: {erro_compilacao}",
        "corrija o erro de sintaxe — abra o arquivo e rode python "
        f"{caminho.relative_to(RAIZ)} você mesmo",
    )]

    python = _python_da_venv() or (sys.executable if sys.prefix != sys.base_prefix else None)
    if python is None:
        itens.append(Item(
            "cliente_llm.py roda em modo offline",
            False,
            "não encontrei .venv para executar o cliente",
            "crie/ative a venv e instale os requirements; depois rode esta verificação de novo",
        ))
        return itens

    # O modo offline do curso (laboratório 06): AMS_MODO_OFFLINE=1 faz o cliente
    # ler das fixtures. A chave entra VAZIA: esta verificação nunca gasta cota.
    ambiente = {"AMS_MODO_OFFLINE": "1", "GEMINI_API_KEY": ""}
    relativo = caminho.relative_to(RAIZ)
    if caminho.parent == RAIZ:
        comando = [str(python), str(relativo)]
    elif caminho.parent.parent == RAIZ / "src":
        comando = [str(python), "-m", f"{caminho.parent.name}.cliente_llm"]
    else:
        comando = [str(python), str(caminho)]
    codigo, saida = _rodar(comando, timeout=240, env_extra=ambiente)
    if codigo == 0:
        itens.append(Item(
            "cliente_llm.py roda em modo offline",
            True,
            f"executou e terminou bem ({' '.join(comando[1:])})",
        ))
    else:
        itens.append(Item(
            "cliente_llm.py roda em modo offline",
            False,
            f"terminou com código {codigo}: {saida[-200:] if saida else 'sem saída'}",
            "rode você mesmo, com AMS_MODO_OFFLINE=1 no .env, e leia a mensagem "
            "— os erros comuns (dataset ausente, chave vazia sem modo offline) "
            "têm explicação no laboratório 06",
        ))
    return itens


# ---------------------------------------------------------------------------
# Principal


def principal() -> int:
    print("=" * 68)
    print(" D1 · verificação de entrega — o Contrato de Saída, item por item")
    print(" Especialização em Desenvolvimento de Agentes Inteligentes · UTFPR")
    print(f" Repositório examinado: {RAIZ}")
    print("-" * 68)

    if not verificar_parece_projeto():
        print()
        print(" ❌ Esta pasta não parece um repositório Python do curso.")
        print("    Não encontrei src/, tests/, notebooks/, requirements.txt,")
        print("    pyproject.toml, dominio.md nem .git aqui.")
        print("    → o que fazer: abra um terminal NA RAIZ do seu repositório")
        print("      (a pasta que você clona do Git) e rode este script de lá,")
        print("      ou passe o caminho: python verifica-entrega.py C:\\caminho\\repo")
        print("=" * 68)
        return 1

    relatorio = Relatorio()
    for item in verificar_estrutura():
        relatorio.adicionar(item)
    rastreados = _git_ls_files()
    for item in verificar_git(rastreados):
        relatorio.adicionar(item)
    relatorio.adicionar(verificar_env_example())
    relatorio.adicionar(verificar_dependencias())
    relatorio.adicionar(verificar_readme())
    relatorio.adicionar(verificar_dominio())
    for item in verificar_dataset():
        relatorio.adicionar(item)
    for item in verificar_notebook():
        relatorio.adicionar(item)
    for item in verificar_codigo():
        relatorio.adicionar(item)
    relatorio.adicionar(verificar_testes())
    for item in verificar_cliente():
        relatorio.adicionar(item)

    total = len(relatorio.itens)
    print("-" * 68)
    print(f" {relatorio.aprovados} de {total} itens passaram "
          f"({relatorio.criticos_falhos} crítico(s) e {relatorio.recomendados_falhos} "
          f"recomendado(s) falhando).")
    if relatorio.criticos_falhos:
        print(" ⚠️  Há item CRÍTICO falhando: o Contrato de Saída NÃO está cumprido.")
        print("    Siga os '→ o que fazer' acima antes de entregar a N2.")
    else:
        print(" ✅ Todos os itens críticos passaram: o contrato está cumprido.")
        if relatorio.recomendados_falhos:
            print(f"    ({relatorio.recomendados_falhos} item(ns) recomendado(s) falharam —")
            print("     a entrega passa, mas enfraquece na rubrica da N2.)")
    print()
    print(" Lembrete: este script confere presença e forma. Qualidade da análise,")
    print(" do código e da integração com o modelo são critérios da rubrica da N2,")
    print(" avaliados pelo professor — 'tudo verde' não é sinônimo de nota máxima.")
    print("=" * 68)
    return 1 if relatorio.criticos_falhos else 0


if __name__ == "__main__":
    sys.exit(principal())
