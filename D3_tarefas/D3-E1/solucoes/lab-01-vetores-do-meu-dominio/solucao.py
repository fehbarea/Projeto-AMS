"""Laboratório 01 — os vetores do meu domínio. SOLUÇÃO COMENTADA (professor).

Nunca entra no pacote do aluno (o empacotador falha se `solucao.py` viajar).
É o esqueleto com as três TAREFAS resolvidas e o porquê de cada linha.

TAREFA 1 — cosseno (slide 16): produto escalar ÷ (norma de a · norma de b).
    Mede a DIREÇÃO: 1 = mesma direção, 0 = sem relação linear, negativo =
    direções opostas. O tamanho dos vetores sai da conta — é exatamente o
    que o slide 13 pede ao normalizar, e o slide 15 aponta como o defeito
    do produto escalar cru.

TAREFA 2 — euclidiana (slide 17): a norma da diferença.
    Mede a POSIÇÃO. Sobre vetores normalizados, as duas medidas produzem a
    MESMA ordenação — o teste do laboratório prova isso. Sem normalizar,
    não: a euclidiana passa a ser dominada pelo comprimento de cada vetor,
    e frases longas parecem "mais" que frases curtas (slide 13).

TAREFA 3 — a ordenação: todas as combinações (i, j) com i < j, ordenadas
    por cosseno decrescente. São 19.900 pares com 200 frases — roda em
    menos de um segundo.

O gabarito da interpretação está no GABARITO-DE-PARES.md da disciplina
(arquivo do professor, ao lado dos vetores originais em fonte/dados/): os
pares plantados de negação saem com cosseno alto (média 0,7316), os de
palavras opostas ficam quase colados (0,9518 — o "próximo sem razão") e os
de jargão ficam mal representados. É o slide 20 do D3-E1, medido.
"""

from itertools import combinations
from pathlib import Path

import numpy as np

CONJUNTO = "dados/manutencao"
NORMALIZAR = False
QUANTOS = 10


def carregar(base: str):
    """Mesma busca do esqueleto: pasta corrente, depois a do laboratório."""
    caminho_frases = caminho_vetores = None
    for raiz in (Path(), Path(__file__).resolve().parent):
        if (raiz / f"{base}-frases.txt").is_file() \
                and (raiz / f"{base}-vetores.npy").is_file():
            caminho_frases = raiz / f"{base}-frases.txt"
            caminho_vetores = raiz / f"{base}-vetores.npy"
            break
    if caminho_frases is None:
        raise SystemExit(
            f"Não encontrei {base}-frases.txt ou {base}-vetores.npy nem na "
            "pasta corrente nem na pasta do laboratório. Extraia o pacote "
            "inteiro (a pasta dados/ viaja junto) ou ajuste a linha "
            "CONJUNTO no topo do esqueleto.")
    frases = [linha.strip() for linha in
              caminho_frases.read_text(encoding="utf-8").splitlines()
              if linha.strip()]
    matriz = np.load(caminho_vetores)
    if len(frases) != len(matriz):
        raise SystemExit(
            f"{len(frases)} frases contra {len(matriz)} vetores — os dois "
            "arquivos estão desalinhados; não reordene um sem o outro.")
    return frases, matriz


def preparar(matriz: np.ndarray) -> np.ndarray:
    if not NORMALIZAR:
        return matriz
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    return matriz / normas


def similaridade_cosseno(a, b):
    produto = np.dot(a, b)
    normas = np.linalg.norm(a) * np.linalg.norm(b)
    if normas == 0:
        raise ValueError("vetor de norma zero: a similaridade não se define")
    return float(produto / normas)


def distancia_euclidiana(a, b):
    return float(np.linalg.norm(a - b))


def pares_ordenados(matriz):
    pares = [((i, j), similaridade_cosseno(matriz[i], matriz[j]))
             for i, j in combinations(range(len(matriz)), 2)]
    pares.sort(key=lambda item: item[1], reverse=True)
    return pares


def resumo(texto: str, n: int = 44) -> str:
    return texto if len(texto) <= n else texto[: n - 1] + "…"


if __name__ == "__main__":
    frases, matriz = carregar(CONJUNTO)
    prontos = preparar(matriz)
    pares = pares_ordenados(prontos)

    print(f"conjunto: {CONJUNTO} · {len(frases)} frases · "
          f"{matriz.shape[1]} dimensões")
    print(f"normalizar: {NORMALIZAR}  (troque a linha NORMALIZAR e rode de "
          f"novo — a comparação do slide 18 é esta linha)")
    print()

    pares = [(par, float(valor)) for par, valor in pares]
    extremos = [("mais parecidos (por cosseno):", pares[:QUANTOS]),
                ("mais distantes (por cosseno):", pares[-QUANTOS:][::-1])]
    for titulo, fatia in extremos:
        print(titulo)
        for posicao, ((i, j), valor) in enumerate(fatia, start=1):
            euclidiana = distancia_euclidiana(prontos[i], prontos[j])
            distancia = f"{float(euclidiana):.4f}" if euclidiana is not None else "—"
            print(f"  {posicao:2d}. cos {valor:.4f}  eucl {distancia}  "
                  f"({i:3d}, {j:3d}) "
                  f"\"{resumo(frases[i])}\" / \"{resumo(frases[j])}\"")
        print()

    print("agora: escolha DOIS pares que surpreenderam — um PRÓXIMO sem razão "
          "aparente e um DISTANTE que deveria estar junto (slide 19) — e "
          "anote-os em pares-surpreendentes.md. Eles voltam na D7.")
