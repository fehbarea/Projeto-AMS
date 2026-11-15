"""GABARITO — Laboratório 04, o mapa do meu domínio (a janela do E2).

Este arquivo é a solução das duas TAREFAS do esqueleto e o gabarito do
professor; NÃO vai dentro do pacote do aluno. Os números abaixo foram
medidos no conjunto `manutencao` (200 vetores de 384 dimensões, MiniLM
multilíngue, crus — ver dados/FONTE.md), normalizados, com a semente
20260901 no método de vizinhança.

Os três pares exemplares do passo 4 (escolhidos como vizinhos no mapa
t-SNE; o cosseno é medido no espaço ORIGINAL, e não depende da semente):

  - (35, 36)  cos +0.9780  CONFIRMA — "Aperte os parafusos do mancal em
    ordem cruzada" / "Afrouxe os parafusos do mancal em ordem cruzada"
    (a ordem de aperto invertida; o modelo sabe que fala da mesma coisa);
  - (30, 31)  cos +0.9426  CONFIRMA — "Abra a válvula de alívio…" /
    "Feche a válvula de alívio…" (mesma cena, comandos opostos);
  - (60, 77)  cos +0.1228  NÃO CONFIRMA — "O contato do contator K3
    apresentou soldagem" / "As correntes da esteira transportadora
    recebem…" (colados no mapa, assuntos distantes: o caso de engano do
    critério do slide 52).

O que mais o professor pode mostrar, tudo medido nestes conjuntos:

  - Determinismo (slide 54): mesma semente reproduz o mapa exatamente;
    a semente 42 no lugar de 20260901 desloca os pontos em média ~7
    unidades — figuras diferentes, mesmos dados. Mostrar ao vivo com
    --semente 42.
  - A transformação fixa (slide 53, pergunta 4): projetar os 200 vetores
    um a um com posicionar_novo reproduz o mapa de componentes principais
    até a precisão numérica — é por isso que PCA entra num sistema em
    funcionamento e a vizinhança serve à inspeção.
  - A escolha do slide 55: normalizar muda a ESTRUTURA do mapa — a
    correlação das distâncias par a par entre o mapa com e sem
    normalização é ≈0.665 no PCA e ≈0.353 na vizinhança (medido; não é
    ruído, e não é o mesmo mapa). Nos vetores deste pacote, porém, o
    comprimento NÃO domina a primeira componente (Spearman(norma, PC1)
    ≈ −0.07 sem normalizar; o sinal do comprimento aparece na PC2,
    ≈ +0.26). O mecanismo que as NOTAS do slide 55 descrevem ("o
    comprimento domina a primeira direção") não se manifesta nestes
    vetores; a afirmação que se verifica é a do CORPO do slide: a escolha
    muda a figura e precisa estar registrada. (achado registrado no R05.)
  - Frequência do engano (slide 52, "em geral, pelo menos um não
    confirma"): olhando o vizinho mais próximo no mapa t-SNE de cada um
    dos 200 pontos, ≈2.5% têm cosseno original < 0.30 com normalização
    (≈6.5% sem) — em um conjunto de 200, sempre há casos para a
    discussão. No mapa de COMPONENTES PRINCIPAIS a vizinhança engana
    MUITO mais (≈47% dos vizinhos visuais têm cosseno < 0.30): distância
    global preservada não faz pontos colados serem semelhantes.

Tempos de referência: componentes principais ≈0.02 s; vizinhança
(t-SNE, 200×384, 1000 iterações) ≈5 s nesta máquina.
"""

import argparse
from pathlib import Path

import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    raise SystemExit(
        "Este laboratório desenha mapas e precisa do matplotlib e do "
        "scikit-learn — eles fazem parte do stack da disciplina, mas não "
        "estão instalados neste ambiente.")

try:
    from sklearn.manifold import TSNE
except ImportError:
    raise SystemExit(
        "Este laboratório desenha mapas e precisa do matplotlib e do "
        "scikit-learn — eles fazem parte do stack da disciplina, mas não "
        "estão instalados neste ambiente.")

_AQUI = Path(__file__).resolve().parent

SEMENTE_PADRAO = 20260901
PERPLEXIDADE = 30

CONJUNTOS_DO_PACOTE = {"manutencao": "dados/manutencao", "generico": "dados/generico"}


def carregar(nome: str):
    """Resolve o conjunto e lê o par `<base>-frases.txt` +
    `<base>-vetores.npy`, alinhados por índice (ver FONTE.md). Aceita o
    nome curto de um conjunto do pacote (`manutencao`, `generico`) ou um
    caminho base próprio — o domínio de cada um entra por aqui, sem
    rede."""
    base = CONJUNTOS_DO_PACOTE.get(nome, nome)
    caminho_frases = caminho_vetores = None
    for raiz in (Path(), _AQUI):
        if (raiz / f"{base}-frases.txt").is_file() \
                and (raiz / f"{base}-vetores.npy").is_file():
            caminho_frases = raiz / f"{base}-frases.txt"
            caminho_vetores = raiz / f"{base}-vetores.npy"
            break
    if caminho_frases is None:
        conhecidos = " e ".join(sorted(CONJUNTOS_DO_PACOTE))
        raise SystemExit(
            f"Não encontrei {base}-frases.txt e {base}-vetores.npy nem na "
            f"pasta corrente nem na pasta do laboratório. Os conjuntos do "
            f"pacote são {conhecidos}; para o SEU domínio, aponte o caminho "
            "base dos seus dois arquivos (eles viajam sempre juntos).")
    frases = [linha.strip() for linha in
              caminho_frases.read_text(encoding="utf-8").splitlines()
              if linha.strip()]
    matriz = np.load(caminho_vetores).astype(np.float64)
    if len(frases) != len(matriz):
        raise SystemExit(
            f"{len(frases)} frases contra {len(matriz)} vetores — os dois "
            "arquivos estão desalinhados; não reordene um sem o outro.")
    return frases, matriz


def preparar(matriz: np.ndarray, normalizar: bool) -> np.ndarray:
    """Aplica a ESCOLHA do slide 55: sem normalizar, o comprimento do
    vetor participa da redução; normalizado, sobra só a direção. A
    escolha vai registrada na figura e no pares-conferidos.md."""
    if not normalizar:
        return matriz
    normas = np.linalg.norm(matriz, axis=1, keepdims=True)
    return matriz / normas


def reduzir_pca(matriz: np.ndarray):
    """Componentes principais (slide 51): gira o espaço e mantém as
    direções de maior variação. Preserva a estrutura GLOBAL, é rápida e
    DETERMINÍSTICA — e é uma transformação FIXA: o modelo devolvido
    (`centro` e `componentes`) projeta um vetor novo sem refazer o mapa,
    que é a resposta da pergunta 4 do slide 53."""
    centro = matriz.mean(axis=0)
    x = matriz - centro
    _, _, vt = np.linalg.svd(x, full_matrices=False)
    componentes = vt[:2].T
    return x @ componentes, {"centro": centro, "componentes": componentes}


def reduzir_vizinhanca(matriz: np.ndarray, semente: int) -> np.ndarray:
    """O método de vizinhança (slide 51): tenta manter juntos os pontos
    que já eram vizinhos, produzindo grupos visualmente claros — mas a
    distância ENTRE grupos no mapa não significa quase nada, e a posição
    de um ponto novo não existe sem refazer o mapa inteiro (slide 53).
    A semente é obrigatória e declarada: duas execuções com sementes
    diferentes dão figuras diferentes (slide 54)."""
    return TSNE(n_components=2, init="pca", random_state=semente,
                perplexity=PERPLEXIDADE).fit_transform(matriz)


# =============================================================================
# TAREFA 1 — a medida de conferência (slide 16): a similaridade de cosseno,
# a MESMA que você escreveu no lab-01 — produto escalar dividido pelo
# produto das duas normas. Uma linha, com np.dot e np.linalg.norm.
def similaridade_cosseno(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


# TAREFA 2 — a projeção do vetor novo (pergunta 4 do slide 53): o mapa de
# componentes principais é uma transformação FIXA, então posicionar um
# vetor novo é UMA linha — subtraia o centro e multiplique pelas
# componentes do modelo:
#     (vetor - modelo["centro"]) @ modelo["componentes"]
def posicionar_novo(vetor, modelo):
    return (np.asarray(vetor, dtype=float) - modelo["centro"]) @ modelo["componentes"]
# =============================================================================


def conferir_pares(pares, matriz):
    """A conferência automática do passo 4 do slide 52: para cada par de
    índices escolhido NO MAPA, imprime o cosseno ORIGINAL — a vizinhança
    visual se confirma ou não no espaço de 384 dimensões, e nunca ao
    contrário. Devolve [(par, cosseno), ...]."""
    resultados = []
    for i, j in pares:
        valor = similaridade_cosseno(matriz[i], matriz[j])
        if valor is None:
            resultados.append(((i, j), None))
            print(f"  ({i:3d}, {j:3d}) cos —  (a TAREFA 1 está em branco)")
            continue
        resultados.append(((i, j), float(valor)))
        veredito = "confirma" if float(valor) >= 0.5 else "NÃO confirma"
        print(f"  ({i:3d}, {j:3d}) cos {float(valor):+.4f}  {veredito}")
    return resultados


def _ler_pares(pedacos):
    """Lê ['4,9', '22,77', '150,181'] — ou tudo em um argumento só,
    '4,9 22,77 150,181' — e devolve [(4, 9), (22, 77), (150, 181)]."""
    texto = " ".join(pedacos)
    pares = []
    for pedaco in texto.replace(";", " ").split():
        partes = pedaco.split(",")
        if len(partes) != 2:
            raise SystemExit(
                f"par inválido: {pedaco!r} — o formato é --pares 4,9 22,77 "
                "150,181 (dois índices por par, separados por vírgula).")
        pares.append((int(partes[0]), int(partes[1])))
    return pares


def desenhar(pontos_pca, pontos_tsne, conjunto: str, normalizar: bool,
             semente: int, arquivo: str = "mapa-do-espaco.png"):
    """Os dois mapas lado a lado (passo 3 do slide 52), com os índices
    anotados para o passo 4. A escolha de normalização e a SEMENTE vão
    declaradas na própria figura (slide 54)."""
    figura, eixos = plt.subplots(1, 2, figsize=(14.0, 7.0))
    normalizacao = "normalizado" if normalizar else "sem normalizar"
    for eixo, pontos, titulo in (
            (eixos[0], pontos_pca, "componentes principais (determinístico)"),
            (eixos[1], pontos_tsne,
             f"vizinhança — t-SNE, semente {semente}")):
        eixo.scatter(pontos[:, 0], pontos[:, 1], s=14, alpha=0.75)
        for indice, (x, y) in enumerate(pontos):
            eixo.annotate(str(indice), (x, y), fontsize=5, alpha=0.65)
        eixo.set_title(titulo, fontsize=10)
        eixo.set_xticks(())
        eixo.set_yticks(())
    figura.suptitle(
        f"O mapa do meu domínio — {conjunto} · {normalizacao} (slide 55) · "
        f"duas reduções do mesmo conjunto de {len(pontos_pca)} vetores",
        fontsize=12)
    figura.tight_layout()
    figura.savefig(arquivo, dpi=150)
    plt.close(figura)
    return arquivo


def _pontos_csv(pontos_pca, pontos_tsne, frases, arquivo="mapa-pontos.csv"):
    """As coordenadas com os índices e as frases — para escolher os pares
    do passo 4 sem adivinhar número pequeno na figura."""
    linhas = ["indice,x_pca,y_pca,x_vizinhanca,y_vizinhanca,frase"]
    for indice, frase in enumerate(frases):
        linhas.append(
            f"{indice},{pontos_pca[indice, 0]:.4f},{pontos_pca[indice, 1]:.4f},"
            f"{pontos_tsne[indice, 0]:.4f},{pontos_tsne[indice, 1]:.4f},"
            f"\"{frase}\"")
    Path(arquivo).write_text("\n".join(linhas) + "\n",
                             encoding="utf-8", newline="\n")
    return arquivo


def _documento(conjunto, quantas_dimensoes, normalizar, semente, resultados):
    tudo_confirmou = all(valor >= 0.5 for _, valor in resultados
                         if valor is not None) and bool(resultados)
    linhas = [
        "# O mapa do meu domínio — conferência (Laboratório 04)",
        "",
        f"Conjunto: {conjunto} · {quantas_dimensoes} dimensões antes da redução",
        f"Escolha registrada (slide 55): {'normalizado' if normalizar else 'SEM normalizar'}"
        f" · semente da vizinhança: {semente}",
        "Mapas: mapa-do-espaco.png (componentes principais à esquerda,"
        " vizinhança à direita) · pontos: mapa-pontos.csv",
        "",
        "## Passo 4 — os três pares que você escolheu no mapa (slide 52)",
        "",
    ]
    if resultados:
        linhas.append("| par | cosseno original | a vizinhança visual |")
        linhas.append("|---|---|---|")
        for (i, j), valor in resultados:
            if valor is None:
                linhas.append(f"| ({i}, {j}) | — | (TAREFA 1 em branco) |")
                continue
            veredito = "confirma" if valor >= 0.5 else "NÃO confirma"
            linhas.append(f"| ({i}, {j}) | {valor:+.4f} | {veredito} |")
    else:
        linhas.append(
            "Ainda sem pares: escolha no mapa três pares de pontos "
            "VIZINHOS e rode de novo com, por exemplo,")
        linhas.append("`python esqueleto.py " + conjunto +
                      " --pares 4,9 22,77 150,181`")
    linhas += [
        "",
        "## As quatro perguntas do slide 53",
        "",
        "1. Os dois métodos produzem os mesmos agrupamentos?",
        "R:",
        "",
        "2. Há grupo que só aparece em um deles?",
        "R:",
        "",
        "3. Os vizinhos visuais confirmam no cosseno original?",
        "R:",
        "",
        "4. O que aconteceria com um vetor novo, fora do conjunto?",
        "R:",
        "",
    ]
    if tudo_confirmou and resultados:
        linhas += [
            "Todos os seus pares confirmaram — procure um par entre GRUPOS",
            "diferentes do mapa de vizinhança (colados na figura, de assuntos",
            "distantes) e confira também ele; o slide 52 espera ao menos um",
            "que não confirma. Se de fato todos confirmarem no SEU domínio,",
            "anote isso: é um resultado sobre o seu conjunto, não um erro.",
            "",
        ]
    linhas += [
        "## O caso em que o mapa enganou (critério do slide 52)",
        "",
        "Par e o que a figura sugeria, e o que o cosseno original disse:",
        "",
        "R:",
        "",
    ]
    return "\n".join(linhas)


def _fechamento(pares_lidos, resultados, saida):
    """As pendências do critério do slide 52, no formato dos outros labs."""
    pendencias = []
    if not pares_lidos:
        pendencias.append(
            "os três pares do passo 4 ainda não foram conferidos — rode com "
            "--pares (ex.: --pares 4,9 22,77 150,181)")
    elif len(resultados) < 3:
        pendencias.append(
            f"conferi {len(resultados)} par(es); o slide 52 pede TRÊS")
    corpo = saida.read_text(encoding="utf-8") \
        if saida.is_file() else ""
    # R: seguido de texto na mesma linha OU na linha seguinte conta como
    # respondido; R: seguido de linha vazia, não.
    marcados = 0
    linhas = corpo.splitlines()
    for posicao, linha in enumerate(linhas):
        alvo = linha.strip()
        seguinte = linhas[posicao + 1].strip() if posicao + 1 < len(linhas) else ""
        if alvo.startswith("R:") and (alvo[2:].strip() or seguinte):
            marcados += 1
    esperadas = 4 + (1 if pares_lidos else 0)
    if marcados < esperadas:
        obrigatorias = "as quatro perguntas do slide 53 e o caso em que o mapa enganou"
        if not pares_lidos:
            obrigatorias = "as quatro perguntas do slide 53"
        pendencias.append(
            f"faltam respostas no pares-conferidos.md ({marcados} de "
            f"{esperadas}: {obrigatorias})")
    return pendencias


def main():
    parser = argparse.ArgumentParser(
        description="O mapa do meu domínio (slides 52 e 53 do D3-E2).")
    parser.add_argument("conjunto", nargs="?", default="manutencao",
                        help="manutencao, generico ou o caminho base do SEU domínio")
    parser.add_argument("--semente", type=int, default=SEMENTE_PADRAO,
                        help="a semente do método de vizinhança (declarada na figura)")
    parser.add_argument("--sem-normalizar", action="store_true",
                        help="reduzir sobre os vetores crus (slide 55: a escolha "
                             "muda o mapa e precisa estar registrada)")
    parser.add_argument("--pares", nargs="+", default=[], metavar="I,J",
                        help="três pares escolhidos no mapa, ex.: --pares "
                             "4,9 22,77 150,181")
    parser.add_argument("--novo", type=int, default=None,
                        help="índice de um vetor tratado como NOVO (pergunta 4 do slide 53)")
    parser.add_argument("--saida", default="pares-conferidos.md",
                        help="arquivo de conferência a escrever")
    argumentos = parser.parse_args()

    frases, matriz = carregar(argumentos.conjunto)
    prontos = preparar(matriz, normalizar=not argumentos.sem_normalizar)

    pontos_pca, modelo = reduzir_pca(prontos)
    pontos_tsne = reduzir_vizinhanca(prontos, argumentos.semente)

    figura = desenhar(pontos_pca, pontos_tsne, argumentos.conjunto,
                      normalizar=not argumentos.sem_normalizar,
                      semente=argumentos.semente)
    csv = _pontos_csv(pontos_pca, pontos_tsne, frases)

    normalizacao = "normalizado" if not argumentos.sem_normalizar else "SEM normalizar"
    print("== Laboratório 04 — o mapa do meu domínio")
    print(f"conjunto: {argumentos.conjunto} · {len(frases)} frases · "
          f"{matriz.shape[1]} dimensões · {normalizacao} (slide 55)")
    print(f"métodos: componentes principais (determinístico) · "
          f"vizinhança (t-SNE, semente {argumentos.semente} — declarada na figura)")
    print(f"mapas: {figura} (índices anotados) · pontos: {csv}")
    print()

    pares_lidos = []
    if argumentos.pares:
        pares_lidos = _ler_pares(argumentos.pares)
        fora = [p for par in pares_lidos for p in par if not 0 <= p < len(frases)]
        if fora:
            raise SystemExit(
                f"índice fora do conjunto: {fora} — os índices vão de 0 a "
                f"{len(frases) - 1} (veja {csv}).")
        print("conferência (passo 4 do slide 52) — o cosseno ORIGINAL de "
              "cada par escolhido no mapa:")
        resultados = conferir_pares(pares_lidos, prontos)
        if any(valor is None for _, valor in resultados):
            raise SystemExit(
                "A TAREFA 1 (a sua similaridade de cosseno) está em branco — "
                "procure a TAREFA 1 no esqueleto.py; sem ela a conferência "
                "do slide 52 não roda.")
    else:
        resultados = []
        print("próximo passo: escolha no mapa três pares de pontos VIZINHOS "
              "e confira (o passo 4 do slide 52), por exemplo:")
        print(f"  python esqueleto.py {argumentos.conjunto} "
              "--pares 4,9 22,77 150,181")
    print()

    if argumentos.novo is not None:
        indice = argumentos.novo
        if not 0 <= indice < len(frases):
            raise SystemExit(f"índice --novo fora do conjunto: {indice}")
        ponto = posicionar_novo(prontos[indice], modelo)
        if ponto is None:
            raise SystemExit(
                "A TAREFA 2 (a projeção do vetor novo) está em branco — "
                "procure a TAREFA 2 no esqueleto.py.")
        print(f"o vetor {indice} tratado como NOVO (pergunta 4 do slide 53):")
        print(f"  componentes principais: transformação FIXA — projeta e "
              f"acabou: ({ponto[0]:.3f}, {ponto[1]:.3f})")
        print("  vizinhança: não há posição pronta — para incluí-lo, o mapa "
              "INTEIRO seria refeito")
        print()

    saida = Path(argumentos.saida)
    if saida.name == "pares-conferidos.md" and saida.exists():
        alternativa = saida.with_name("pares-conferidos-novo.md")
        destino, aviso = alternativa, (
            f"{saida} já existe e foi PRESERVADO; a execução nova está em "
            f"{alternativa}.")
    else:
        destino, aviso = saida, ""
    destino.write_text(
        _documento(argumentos.conjunto, matriz.shape[1],
                   normalizar=not argumentos.sem_normalizar,
                   semente=argumentos.semente, resultados=resultados),
        encoding="utf-8", newline="\n")
    if aviso:
        print(aviso)
    print(f"conferência: {destino} — anote nele as quatro respostas do "
          "slide 53 e o caso em que o mapa enganou, e rode "
          "python -m pytest teste.py -q")
    pendencias = _fechamento(pares_lidos, resultados, destino)
    if pendencias:
        print()
        print("pendências do critério do slide 52:")
        for pendencia in pendencias:
            print(f"  - {pendencia}")


if __name__ == "__main__":
    main()
