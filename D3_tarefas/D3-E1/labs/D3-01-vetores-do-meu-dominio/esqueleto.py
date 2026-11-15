"""Laboratório 01 — os vetores do meu domínio.

O esqueleto já carrega os vetores e já imprime a ordenação; o que falta é a
CONTA: as duas medidas de comparação (slides 16 e 17) e a ordenação de todos
os pares por cosseno. São as TAREFAS 1, 2 e 3, poucas linhas cada uma.

Como usar:
    1. complete as TAREFAS 1, 2 e 3;
    2. rode:  python esqueleto.py
    3. troque a linha NORMALIZAR para True e rode de novo — a comparação
       "com e sem normalizar" (slide 18) é ESTA linha, e não código novo;
    4. escolha DOIS pares que surpreenderam e anote-os em
       `pares-surpreendentes.md` — eles voltam na D7 (slide 19);
    5. quando estiver pronto:  python -m pytest teste.py -q

O conjunto padrão é o de manutenção (`dados/manutencao`). Se o seu domínio
não estiver no pacote, use a reserva: mude a linha CONJUNTO para
"dados/generico" (o arquivo de frases e o de vetores trocam juntos).
Nenhuma rede é chamada: os vetores já vêm calculados (ver FONTE.md).
"""

from itertools import combinations
from pathlib import Path

import numpy as np

# --- configuração (são estas linhas, e não código novo) ----------------------
CONJUNTO = "dados/manutencao"  # a reserva do pacote: "dados/generico"
NORMALIZAR = True             # a comparação com/sem normalização é AQUI (slide 13)
QUANTOS = 30                   # quantos pares imprimir em cada extremo


def carregar(base: str):
    """Lê o par `<base>-frases.txt` + `<base>-vetores.npy`, alinhados por
    índice: a frase i tem o vetor i (ver FONTE.md do pacote). Procura a
    partir da pasta corrente e, se não achar, da pasta do laboratório."""
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
    """Aplica a escolha da linha NORMALIZAR — o resto do código não muda.

    Sem normalizar, o comprimento do vetor (frase longa) participa da
    comparação; normalizado, sobra só a direção (slide 13).
    """
    if not NORMALIZAR:
        return matriz
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    return matriz / normas


# =============================================================================
# TAREFA 1 — a similaridade de cosseno (slide 16): o produto escalar dividido
# pelo produto das duas normas. Duas linhas com np.dot e np.linalg.norm.
def similaridade_cosseno(a, b):
    produto = np.dot(a, b)
    normas = np.linalg.norm(a) * np.linalg.norm(b)
    return float(produto / normas)


# TAREFA 2 — a distância euclidiana (slide 17): a norma da diferença. Uma linha.
def distancia_euclidiana(a, b):
    return float(np.linalg.norm(a - b))


# TAREFA 3 — a ordenação do slide 18: para TODO par de índices (i, j) com
# i < j, calcule a similaridade de cosseno e devolva a lista de pares
# [((i, j), valor), ...] ordenada da similaridade MAIS ALTA para a MAIS BAIXA.
# (o módulo `itertools` já está importado lá em cima)
def pares_ordenados(matriz):
    pares = [((i, j), similaridade_cosseno(matriz[i], matriz[j]))
                 for i, j in combinations(range(len(matriz)), 2)]
    pares.sort(key=lambda item: item[1], reverse=True)
    return pares
# =============================================================================


def resumo(texto: str, n: int = 44) -> str:
    return texto if len(texto) <= n else texto[: n - 1] + "…"


if __name__ == "__main__":
    frases, matriz = carregar(CONJUNTO)
    prontos = preparar(matriz)
    pares = pares_ordenados(prontos)
    if pares is None:
        raise SystemExit(
            "As TAREFAS 1, 2 e 3 ainda estão em branco — procure a marca "
            "TAREFA no esqueleto.py e complete as três funções.")

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
