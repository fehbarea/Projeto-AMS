"""Teste do Laboratório 03 — saber se o relatório está fechado.

Como usar (da pasta do laboratório, depois de rodar o medidas.py e
PREENCHER as decisões):
    python teste.py                     # confere relatorio-dado.md
    python teste.py outro-relatorio.md  # ou confere outro arquivo
    python -m pytest teste.py -q        # a mesma conferência pelo pytest

O critério do slide 28, um a um:

  1. as medidas saíram (a tabela existe — rode o medidas.py primeiro);
  2. cada variável COM extremos marcados tem a decisão escrita;
  3. cada variável COM faltantes tem um mecanismo marcado e o porquê;
  4. as quatro perguntas do slide 29 respondidas, com o número;
  5. a comparação com a análise da D1 escrita.

Uma resposta vazia, ou só de underscores, não conta como escrita.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path


def _conteudo_real(texto: str) -> str:
    limpo = re.sub(r"[_.\-]+", " ", texto)
    return limpo.strip()


def _respostas_em(bloco: str) -> list[str]:
    """O texto que segue cada marcador `R:` — na mesma linha ou nas linhas
    seguintes, até a linha em branco. Vazio se não foi escrito."""
    respostas, capturando, atual = [], False, []
    for linha in bloco.splitlines():
        tira = linha.strip()
        if tira == "R:" or tira.startswith("R: "):
            if capturando:
                respostas.append(" ".join(atual))
            capturando, atual = True, []
            mesma_linha = tira[2:].strip()
            if mesma_linha:
                atual.append(mesma_linha)
        elif capturando:
            if tira:
                atual.append(tira)
            else:
                respostas.append(" ".join(atual))
                capturando = False
    if capturando:
        respostas.append(" ".join(atual))
    return respostas


def verificar(caminho: str | Path = "relatorio-dado.md") -> list[str]:
    """Devolve a lista de problemas; lista vazia = relatório fechado."""
    arquivo = Path(caminho)
    if not arquivo.is_file():
        return [
            f"Não existe {arquivo} — rode primeiro: python medidas.py "
            "(com o seu conjunto, ou com exemplo/dataset-exemplo.csv para "
            "experimentar), preencha as decisões e rode este teste de novo."
        ]
    texto = arquivo.read_text(encoding="utf-8")
    problemas = []

    if "| variável |" not in texto or "## Medidas por variável" not in texto:
        problemas.append(
            "a tabela de medidas não está no arquivo — o relatório precisa "
            "vir do medidas.py; rode python medidas.py e preencha por cima")

    secoes = re.split(r"\n### ", texto)
    for secao in secoes[1:]:
        titulo = secao.splitlines()[0]
        corpo = re.split(r"\n## ", secao)[0]   # só o bloco desta seção
        respostas = _respostas_em(corpo)
        preenchidas = [_conteudo_real(r) for r in respostas
                       if _conteudo_real(r)]
        if titulo.startswith("Extremos de") and not preenchidas:
            problemas.append(
                f"{titulo}: a decisão sobre os extremos está em branco — "
                "o critério é CADA extremo marcado com decisão escrita")
        if titulo.startswith("Faltantes de"):
            if not re.search(r"- \[[xX]\]", corpo):
                problemas.append(
                    f"{titulo}: nenhum mecanismo marcado — marque UM dos "
                    "três do slide 26 com um x dentro do colchete")
            if not preenchidas:
                problemas.append(
                    f"{titulo}: o porquê do mecanismo está em branco")

    inicio = texto.find("**1.")
    respostas_finais = _respostas_em(texto[inicio:]) if inicio >= 0 else []
    if len(respostas_finais) < 5 or not all(
            _conteudo_real(r) for r in respostas_finais):
        problemas.append(
            "as quatro perguntas do slide 29 e a comparação com a D1 "
            "precisam das cinco respostas escritas (com o número que "
            "sustenta cada uma)")
    return problemas


def test_relatorio_fechado():
    """A mesma conferência pelo pytest — sem argumento, confere
    relatorio-dado.md na pasta corrente."""
    problemas = verificar()
    assert not problemas, "pendências: " + " | ".join(problemas)


if __name__ == "__main__":
    alvo = sys.argv[1] if len(sys.argv) > 1 else "relatorio-dado.md"
    problemas = verificar(alvo)
    if problemas:
        print(f"{alvo} ainda não está fechado — {len(problemas)} pendência(s):")
        for problema in problemas:
            print(f"  - {problema}")
        raise SystemExit(1)
    print(f"{alvo}: critério do slide 28 cumprido — extremos com decisão "
          "escrita, faltantes com mecanismo nomeado, perguntas respondidas.")
