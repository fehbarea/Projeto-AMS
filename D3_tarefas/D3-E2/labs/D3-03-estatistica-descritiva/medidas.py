"""Laboratório 03 — o meu dado, com rigor.

Aqui não há código para completar: o seu trabalho é RODAR sobre o SEU
conjunto de dados (o mesmo da D1) e ESCREVER as decisões dentro do
relatório que este programa gera. As medidas saem prontas; as decisões
são suas — é o critério do slide 28 do D3-E2.

Como usar:
    python medidas.py                          # acha o conjunto sozinho
    python medidas.py caminho/do/dataset.csv   # ou aponte o arquivo
    python medidas.py exemplo/dataset-exemplo.csv   # para experimentar

A busca automática procura `dados/dataset.csv` e `data/dataset.csv` (as
duas grafias que a D1 aceita) na pasta corrente e na pasta acima do
laboratório — onde o conjunto mora quando o pacote é extraído na raiz do
repositório. Se não achar, a mensagem diz o que fazer; não há rastro de
exceção.

O relatório sai em `relatorio-dado.md` (na pasta corrente). Se ele já
existir, suas decisões escritas são PRESERVADAS: a nova rodada vai para
`relatorio-dado-novo.md` para comparação. Ao terminar de preencher:

    python teste.py
"""

import argparse
import csv
from pathlib import Path

import numpy as np

# valores que contam como faltante (além da célula vazia)
FALTANTES = {"", "na", "n/a", "nan", "null", "none", "-"}


def achar_conjunto(argumento: str | None) -> Path:
    """Resolve o conjunto: argumento explícito vence; senão, as duas
    grafias da D1 nas pastas prováveis."""
    if argumento:
        caminho = Path(argumento)
        if caminho.is_file():
            return caminho
        raise SystemExit(
            f"Não encontrei o arquivo {argumento} — confira o caminho "
            "(rodei a partir da pasta corrente).")
    raizes = [Path.cwd(), Path(__file__).resolve().parent.parent]
    candidatos = []
    for raiz in raizes:
        candidatos += [raiz / "dados" / "dataset.csv",
                       raiz / "data" / "dataset.csv"]
    for raiz in raizes:
        for pasta in ("dados", "data"):
            if (raiz / pasta).is_dir():
                candidatos += sorted((raiz / pasta).glob("*.csv"))
    for candidato in candidatos:
        if candidato.is_file():
            return candidato
    procurados = "\n".join(f"  - {c}" for c in candidatos)
    raise SystemExit(
        "Não encontrei o seu conjunto de dados. Procurei:\n"
        f"{procurados}\n\n"
        "O que fazer:\n"
        "  - rode de novo apontando o arquivo: "
        "python medidas.py caminho/do/seu-dataset.csv\n"
        "  - ou, para experimentar sem o seu conjunto: "
        "python medidas.py exemplo/dataset-exemplo.csv")


def eh_faltante(valor: str) -> bool:
    return valor.strip().lower() in FALTANTES


def ler_csv(caminho: Path):
    """Devolve (colunas, linhas) com linhas curtas completadas por vazio."""
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        colunas = next(leitor, [])
        linhas = [linha + [""] * (len(colunas) - len(linha))
                  for linha in leitor]
    if not colunas or not linhas:
        raise SystemExit(
            f"{caminho} não tem cabeçalho ou não tem linhas de dados — "
            "não há o que medir.")
    return colunas, linhas


def resumir_variavel(nome: str, valores: list[str], total: int) -> dict:
    """Medidas de uma variável: numéricas recebem centro, dispersão e
    extremos pela regra da amplitude interquartil (slide 24)."""
    faltaram = [i for i, valor in enumerate(valores, start=1)
                if eh_faltante(valor)]
    presentes = [valor for valor in valores if not eh_faltante(valor)]
    resumo = {"nome": nome, "total": total, "faltantes": len(faltaram)}
    try:
        numeros = np.array([float(valor.replace(",", ".")) for valor in presentes])
    except ValueError:
        resumo.update(tipo="categórica", categorias=len(set(presentes)),
                      moda=max(set(presentes), key=presentes.count)
                      if presentes else "—")
        return resumo
    resumo.update(tipo="numérica", n=len(numeros))
    resumo.update(media=float(np.mean(numeros)),
                  mediana=float(np.median(numeros)),
                  desvio=float(np.std(numeros, ddof=1)),
                  minimo=float(np.min(numeros)), maximo=float(np.max(numeros)))
    q1, q3 = (float(v) for v in np.percentile(numeros, [25, 75]))
    caixa = q3 - q1
    resumo.update(q1=q1, q3=q3, aiq=caixa)
    limite_baixo, limite_alto = q1 - 1.5 * caixa, q3 + 1.5 * caixa
    resumo.update(limite_baixo=limite_baixo, limite_alto=limite_alto)
    resumo["extremos"] = [(i, float(valor.replace(",", ".")))
                          for i, valor in enumerate(valores, start=1)
                          if not eh_faltante(valor)
                          and not limite_baixo <= float(valor.replace(",", "."))
                          <= limite_alto]
    return resumo


def _n(valor: float) -> str:
    return f"{valor:.4f}"


def gerar_relatorio(resumos: list[dict], caminho: Path, linhas: int) -> str:
    """O relatório preenchível: medidas prontas, decisões para o aluno."""
    partes = [
        "# O meu dado, com rigor — relatório do Laboratório 03",
        "",
        f"Conjunto: `{caminho}` · {linhas} linhas · {len(resumos)} variáveis",
        "",
        "Medidas geradas pelo `medidas.py`: desvio padrão amostral (ddof=1),",
        "quartis por interpolação linear, extremos pela regra da amplitude",
        "interquartil — fora de 1,5 × a caixa (slide 24). As medidas são do",
        "programa; as decisões são SUAS. Preencha todos os blocos `R:` e",
        "confira com `python teste.py`.",
        "",
        "## Medidas por variável",
        "",
        "| variável | tipo | n | faltantes | média | mediana | desvio | Q1 | Q3 | AIQ | mín | máx |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for resumo in resumos:
        if resumo["tipo"] == "categórica":
            partes.append(
                f"| {resumo['nome']} | categórica ({resumo['categorias']} "
                f"valores; moda: {resumo['moda']}) | {resumo['total'] - resumo['faltantes']} "
                f"| {resumo['faltantes']} | — | — | — | — | — | — | — | — |")
        else:
            partes.append(
                f"| {resumo['nome']} | numérica | {resumo['n']} "
                f"| {resumo['faltantes']} | {_n(resumo['media'])} "
                f"| {_n(resumo['mediana'])} | {_n(resumo['desvio'])} "
                f"| {_n(resumo['q1'])} | {_n(resumo['q3'])} "
                f"| {_n(resumo['aiq'])} | {_n(resumo['minimo'])} "
                f"| {_n(resumo['maximo'])} |")

    com_extremos = [r for r in resumos if r.get("extremos")]
    partes += ["", "## Extremos marcados (fora de 1,5 × a caixa — slide 24)", ""]
    if not com_extremos:
        partes += ["Nenhuma variável teve extremos marcados.", ""]
    for resumo in com_extremos:
        partes += [
            f"### Extremos de `{resumo['nome']}` — {len(resumo['extremos'])} "
            f"valor(es), limites [{_n(resumo['limite_baixo'])}; "
            f"{_n(resumo['limite_alto'])}]",
            "",
            "| linha | valor |",
            "|---:|---:|",
        ]
        partes += [f"| {linha} | {_n(valor)} |"
                   for linha, valor in resumo["extremos"]]
        partes += [
            "",
            "Decisão sobre ESTES extremos — manter ou remover, caso a caso,",
            "com o motivo (slide 25: quem remove sem dizer, mente por omissão):",
            "",
            "R:",
            "",
        ]

    com_faltantes = [r for r in resumos if r["faltantes"]]
    partes += ["", "## Faltantes (os três mecanismos do slide 26)", ""]
    if not com_faltantes:
        partes += ["Nenhuma variável tem valores faltantes.", ""]
    for resumo in com_faltantes:
        parcela = 100.0 * resumo["faltantes"] / resumo["total"]
        partes += [
            f"### Faltantes de `{resumo['nome']}` — {resumo['faltantes']} "
            f"({parcela:.1f}% das linhas)",
            "",
            "Mecanismo provável — marque UM com um `x` dentro do colchete:",
            "",
            "- [ ] perdido ao acaso — a falta não depende de nada",
            "- [ ] perdido condicionalmente — depende de outra variável observada",
            "- [ ] perdido por causa do próprio valor — falta porque o valor era o que era",
            "",
            "Por quê:",
            "",
            "R:",
            "",
        ]

    partes += [
        "## As quatro perguntas do slide 29",
        "",
        "**1. Média e mediana se separam em alguma variável? Em qual?**",
        "",
        "R:",
        "",
        "**2. Quantos extremos foram marcados, e quantos você decidiu manter?**",
        "",
        "R:",
        "",
        "**3. Algum faltante parece do terceiro mecanismo?**",
        "",
        "R:",
        "",
        "**4. O que a análise da D1 não tinha visto?**",
        "",
        "R:",
        "",
        "## Comparação com a análise exploratória da D1",
        "",
        "O que mudou de lá para cá — o que a análise de lá não tinha visto,",
        "e o que estas decisões escritas mudam no conjunto que a D5 vai usar:",
        "",
        "R:",
        "",
    ]
    return "\n".join(partes)


def main():
    parser = argparse.ArgumentParser(
        description="Medidas com rigor sobre o SEU conjunto (slide 28 do D3-E2).")
    parser.add_argument("conjunto", nargs="?",
                        help="caminho do CSV (padrão: descobrir em dados/ ou data/)")
    parser.add_argument("--saida", default="relatorio-dado.md",
                        help="arquivo de relatório a escrever")
    argumentos = parser.parse_args()

    caminho = achar_conjunto(argumentos.conjunto)
    colunas, linhas = ler_csv(caminho)
    resumos = [resumir_variavel(nome, [linha[i] for linha in linhas],
                                len(linhas))
               for i, nome in enumerate(colunas)]

    relatorio = gerar_relatorio(resumos, caminho, len(linhas))
    saida = Path(argumentos.saida)
    if saida.name == "relatorio-dado.md" and saida.exists():
        # suas decisões escritas valem mais que uma nova rodada de medidas
        alternativa = saida.with_name("relatorio-dado-novo.md")
        alternativa.write_text(relatorio, encoding="utf-8", newline="\n")
        print(f"{saida} já existe e foi PRESERVADO; as medidas novas estão "
              f"em {alternativa} — compare as duas se quiser.")
        saida_escrita = alternativa
    else:
        saida.write_text(relatorio, encoding="utf-8", newline="\n")
        saida_escrita = saida

    extremos = sum(len(r.get("extremos", [])) for r in resumos)
    faltantes = sum(r["faltantes"] for r in resumos)
    print(f"conjunto: {caminho} · {len(linhas)} linhas · {len(colunas)} colunas")
    print(f"extremos marcados: {extremos} · células faltantes: {faltantes}")
    print(f"relatório: {saida_escrita} — preencha os blocos R: e rode "
          "python teste.py")


if __name__ == "__main__":
    main()
