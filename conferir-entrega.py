"""conferir-entrega.py — o que falta na N2, com o comando de cada falta.

Rode na raiz do SEU repositório (ou aponte a raiz no primeiro argumento):

    python conferir-entrega.py
    python conferir-entrega.py caminho/do/repositorio

Procura os cinco itens da entrega final, roda os seus testes e imprime,
para cada item, ✅ ou ❌ com O QUE FAZER — não só o que falta. Sai com
código 0 quando está tudo de pé.

O que é conferido, item a item (conforme o enunciado da N2):

  1. `agent-spec.md` com as sete seções;
  2. `baseline.py` que EXECUTA — de preferência em `src/<projeto>/`;
  3. relatório de desempenho sobre ≥ 30 casos (métrica, valor, conjunto);
  4. a tabela comparativa de busca, com as seis linhas do enunciado;
  5. a análise escrita de uma página.

E o pytest do repositório inteiro, ao final. Este verificador não exige
rede e não precisa de chave nenhuma.
"""

from __future__ import annotations

import argparse
import py_compile
import re
import subprocess
import sys
from pathlib import Path

# Emojis e acentos precisam sobreviver ao console do Windows mesmo quando a
# saída é redirecionada para arquivo (o PowerShell às vezes usa cp1252 aí).
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IGNORAR = {".venv", "venv", "__pycache__", ".git", ".pytest_cache",
           ".ruff_cache", "node_modules", ".idea", ".vscode"}

NOMES_DE_BUSCA = ["largura", "custo_uniforme", "profundidade_limitada",
                  "aprofundamento_iterativo", "gulosa", "a_estrela"]


def _procurar(raiz: Path, nome: str) -> list[Path]:
    """Procura um arquivo por nome, sem descer nas pastas de ruído."""
    achados: list[Path] = []
    if not raiz.is_dir():
        return achados
    pilha = [raiz]
    while pilha and len(achados) < 20:
        atual = pilha.pop()
        try:
            entradas = sorted(atual.iterdir())
        except OSError:
            continue
        for entrada in entradas:
            if entrada.name in IGNORAR or entrada.name.startswith("."):
                continue
            if entrada.is_dir():
                pilha.append(entrada)
            elif entrada.name.lower() == nome:
                achados.append(entrada)
    return achados


def _procurar_md(raiz: Path) -> list[Path]:
    """Os .md do repositório — EXCETO os deste pacote: os modelos que aqui
    vieram (relatorio-de-desempenho-modelo.md, analise-modelo.md) são
    gabaritos para preencher, e contá-los como entrega seria responder
    ❌ com ✅."""
    pacote = Path(__file__).resolve().parent
    achados: list[Path] = []
    pilha = [raiz]
    while pilha and len(achados) < 200:
        atual = pilha.pop()
        try:
            entradas = sorted(atual.iterdir())
        except OSError:
            continue
        for entrada in entradas:
            if entrada.name in IGNORAR or entrada.name.startswith("."):
                continue
            if entrada.is_dir():
                pilha.append(entrada)
            elif entrada.suffix == ".md" and                     entrada.resolve().parent != pacote:
                achados.append(entrada)
    return achados


# --------------------------------------------------------------------------
# As cinco verificações — cada uma devolve (ok, mensagem)
# --------------------------------------------------------------------------

def verificar_agent_spec(raiz: Path) -> tuple[bool, str]:
    achados = _procurar(raiz, "agent-spec.md")
    if not achados:
        return False, (
            "falta o `agent-spec.md` — as sete seções do seu agente. "
            "O que fazer: o modelo está no pacote D2-01 (pasta do "
            "laboratório 01); copie o modelo para a raiz do repositório "
            "como agent-spec.md e preencha as seções que faltam.")
    corpo = achados[0].read_text(encoding="utf-8", errors="replace")
    secoes = sum(1 for secao in ("PEAS", "dimens", "Tipo", "Medida",
                                 "Restri", "Catálogo", "Formula")
                 if secao.lower() in corpo.lower())
    if secoes < 5:
        return False, (
            f"o `agent-spec.md` ({achados[0].relative_to(raiz)}) tem "
            f"{secoes} das 7 seções. O que fazer: complete as seções "
            "faltando no modelo do D2-01 — a AO1 pede as sete.")
    return True, f"`agent-spec.md` com {secoes} das 7 seções " \
                 f"({achados[0].relative_to(raiz)})"


def verificar_baseline(raiz: Path) -> tuple[bool, str, str | None]:
    achados = _procurar(raiz, "baseline.py")
    if not achados:
        return (
            False,
            "falta o `baseline.py` — o agente de linha de base. O que "
            "fazer: preencha os TODOs do esqueleto do pacote D2-06 e copie "
            "as funções para `src/<projeto>/baseline.py` (o caminho que a "
            "entrega cobra).",
            None,
        )
    caminho = achados[0]
    try:
        py_compile.compile(str(caminho), doraise=True)
    except py_compile.PyCompileError as erro:
        return (
            False,
            f"`baseline.py` não compila ({caminho.relative_to(raiz)}): "
            f"{erro}. O que fazer: abra o arquivo e leia o erro de "
            "sintaxe apontado.",
            None,
        )
    de_onde_chamar = None
    partes = caminho.parts
    if "src" in partes:
        indice = partes.index("src")
        if indice + 1 < len(partes):
            pacote = partes[indice + 1]
            de_onde_chamar = f"python -m {pacote}.baseline"
    return True, (f"`baseline.py` encontrado e compilando "
                  f"({caminho.relative_to(raiz)})"), de_onde_chamar


def verificar_relatorio(raiz: Path) -> tuple[bool, str]:
    for caminho in _procurar_md(raiz):
        if "relatorio-de-desempenho" in caminho.name.lower():
            corpo = caminho.read_text(encoding="utf-8", errors="replace")
            tem_valor = re.search(r"\d+\s*/\s*30|\d+\.\d+", corpo)
            tem_conjunto = "conjunto" in corpo.lower()
            if tem_valor and tem_conjunto:
                return True, (f"relatório de desempenho preenchido "
                              f"({caminho.relative_to(raiz)})")
            return False, (
                f"o relatório ({caminho.relative_to(raiz)}) está sem o "
                "valor medido ou sem o conjunto. O que fazer: rode "
                "`python medir.py` na pasta do D2-06, cole a saída e "
                "declare o conjunto — se usou a reserva, declare também.")
    return False, (
        "falta o relatório de desempenho (item 3). O que fazer: copie o "
        "`relatorio-de-desempenho-modelo.md` DESTE pacote para a raiz do "
        "repositório como `relatorio-de-desempenho.md` e preencha com a "
        "saída do `medir.py`.")


def verificar_tabela_de_busca(raiz: Path) -> tuple[bool, str]:
    melhor = (0, None)
    for caminho in _procurar_md(raiz):
        linhas = caminho.read_text(encoding="utf-8",
                                   errors="replace").splitlines()
        em_tabela = [linha for linha in linhas
                     if linha.startswith("|") and any(
                         nome in linha for nome in NOMES_DE_BUSCA)]
        if len(em_tabela) > melhor[0]:
            melhor = (len(em_tabela), caminho)
    quantidade, caminho = melhor
    if quantidade >= 6:
        return True, (f"tabela de busca com {quantidade} linhas "
                      f"({caminho.relative_to(raiz)})")
    if quantidade:
        return False, (
            f"a tabela de busca ({caminho.relative_to(raiz)}) tem "
            f"{quantidade} linha(s) — o enunciado pede seis (as 4 não "
            "informadas + gulosa e A estrela). O que fazer: rode os "
            "esqueletos dos pacotes D2-04 e D2-05 e cole as duas tabelas "
            "juntas no relatório.")
    return False, (
        "falta a tabela comparativa de busca (item 4). O que fazer: no "
        "esqueleto do D2-04, aponte FORMULACAO para o seu subproblema, "
        "rode `python esqueleto.py` e cole a tabela no relatório; o D2-05 "
        "acrescenta as linhas da heurística.")


def verificar_analise(raiz: Path) -> tuple[bool, str]:
    for caminho in _procurar_md(raiz):
        if caminho.name.lower().startswith("analise"):
            corpo = caminho.read_text(encoding="utf-8", errors="replace")
            if len(corpo) >= 600:
                return True, (f"análise escrita encontrada "
                              f"({caminho.relative_to(raiz)})")
            return False, (
                f"a análise ({caminho.relative_to(raiz)}) está muito "
                "curta para a página pedida. O que fazer: preencha o "
                "`analise-modelo.md` DESTE pacote — duas perguntas: o que "
                "torna o problema difícil, e que tipo de agente ele exige.")
    return False, (
        "falta a análise escrita (item 5). O que fazer: copie o "
        "`analise-modelo.md` DESTE pacote para a raiz como `analise.md` "
        "e escreva a página — é a única escrita nova da entrega.")


def rodar_pytest(raiz: Path) -> tuple[bool, str]:
    try:
        resultado = subprocess.run(
            [sys.executable, "-m", "pytest", "-q"], cwd=str(raiz),
            capture_output=True, text=True, timeout=180,
            encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return False, ("o pytest não terminou em 3 minutos — confira se "
                       "algum teste chama a rede ou dorme.")
    ultima = (resultado.stdout + resultado.stderr).strip().splitlines()
    resumo = ultima[-1] if ultima else "(sem saída)"
    if resultado.returncode == 0 and "no tests ran" not in resumo:
        return True, f"pytest: {resumo}"
    if "no tests ran" in resumo:
        return False, ("nenhum teste foi encontrado no repositório. O que "
                       "fazer: os 10 testes do baseline estão no teste.py "
                       "do pacote D2-06 — copie para `tests/` e adapte aos "
                       "seus limiares.")
    return False, (f"pytest com falhas: {resumo}. O que fazer: rode "
                   "`python -m pytest -q` e leia o primeiro FAIL — "
                   "costuma ser o limiar de uma regra do baseline.")


def main(argv: list[str] | None = None) -> int:
    leitor = argparse.ArgumentParser(
        description="Confere os cinco itens da N2 e diz o que fazer.")
    leitor.add_argument("raiz", nargs="?", default=None,
                        help="raiz do repositório (padrão: a pasta que "
                             "contém este pacote)")
    argumentos = leitor.parse_args(argv)
    if argumentos.raiz:
        raiz = Path(argumentos.raiz).resolve()
    else:
        # este script mora dentro do pacote extraído no repositório —
        # a raiz do repositório é o pai da pasta do pacote
        raiz = Path(__file__).resolve().parent.parent
    if not raiz.is_dir():
        print(f"ERRO: raiz não encontrada: {raiz}", file=sys.stderr)
        return 1

    print(f"Conferindo a entrega final em {raiz}\n")
    ok_geral = True

    ok, mensagem = verificar_agent_spec(raiz)
    ok_geral = ok_geral and ok
    print(f"  1. agent-spec.md          {'✅' if ok else '❌'}  {mensagem}")

    ok, mensagem, comando = verificar_baseline(raiz)
    ok_geral = ok_geral and ok
    print(f"  2. baseline.py            {'✅' if ok else '❌'}  {mensagem}")
    if comando:
        print(f"     o baseline mora em um pacote: chame com `{comando}`")

    ok, mensagem = verificar_relatorio(raiz)
    ok_geral = ok_geral and ok
    print(f"  3. relatório de desempenho {'✅' if ok else '❌'}  {mensagem}")

    ok, mensagem = verificar_tabela_de_busca(raiz)
    ok_geral = ok_geral and ok
    print(f"  4. tabela de busca        {'✅' if ok else '❌'}  {mensagem}")

    ok, mensagem = verificar_analise(raiz)
    ok_geral = ok_geral and ok
    print(f"  5. análise escrita        {'✅' if ok else '❌'}  {mensagem}")

    ok, mensagem = rodar_pytest(raiz)
    ok_geral = ok_geral and ok
    print(f"  6. pytest do repositório  {'✅' if ok else '❌'}  {mensagem}")

    if ok_geral:
        print("\nCinco itens de pé e testes verdes.")
        print("Entregue pelo Moodle até a véspera da primeira sexta "
              "da D3, às 23h59.")
        print("A data exata desta turma está na tarefa do Moodle.")
        return 0
    print("\nHá ❌ acima — cada mensagem traz o comando que resolve. "
          "Conserte e rode de novo.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
