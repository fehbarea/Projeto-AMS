"""Laboratório 02 — a descida à mão. SOLUÇÃO COMENTADA (arquivo do professor).

Nunca entra no pacote do aluno: o empacotador falha se `solucao.py` viajar
(`ferramentas/empacotar.py`, regra do B02 da D2). O esqueleto é este arquivo
com as duas derivadas em branco.

A conta das duas linhas (slide 9 do D3-E2):

    erro = (w * x + b) - y        # o resíduo de cada ponto
    L    = mean(erro ** 2)        # a perda quadrática

    dL/dw = 2 * mean(erro * x)    # regra da cadeia: d erro/dw = x
    dL/db = 2 * mean(erro)        # regra da cadeia: d erro/db = 1

Os dois erros clássicos que o slide 10 prevê — esquecer o fator 2 ou trocar
o sinal — aparecem do mesmo jeito: a perda SOBE em vez de cair. O diagnóstico
do NOTA_PROFESSOR vale: imprimir `dw` no primeiro passo e perguntar se o
sinal faz sentido (w maior que o verdadeiro → erro positivo → dw positivo →
a descida DIMINUI w).

Comportamento medido com os dados deste laboratório (semente dos dados 7,
início da descida semente 42, 200 passos — o gabarito de `anotacoes.md`):

    taxa 0.001  → a perda cai de 2,85e5 para 2,25e4 e AINDA ESTÁ CAINDO no
                  passo 200; w para em 215,0 (longe do 300) — baixa demais.
    taxa 0.1    → perda 2,85e5 → 0,752; estabiliza por volta do passo 60;
                  w=300,008 e b=4,912 (os que geraram: 300 e 5) — adequada.
    taxa 1.5    → a perda sobe sem parar e vira `inf` no passo 161; os pesos
                  passam de ±1e190 — alta demais, diverge (slide 12). Com
                  `--passos 350` o `inf` vira `nan` no passo 326: é o "vira
                  'não é número'" do slide 12 e do slide 13 por inteiro.

Por que `nan` não chega dentro dos 200 passos: com aritmética float64 e a
taxa 0,1 convergindo no MESMO conjunto, o erro cresce no máximo ~29 vezes
por passo, e os 200 passos do slide não bastam para atravessar as ~300
ordens de grandeza até o estouro. A divergência VISÍVEL (perda subindo sem
parar e virando `inf`) acontece no passo 161; o `nan` chega no 326. A
divergência entre o texto do slide 12 e o comportamento float64 está
registrada no R03 (seção de premissas).
"""

import argparse

import numpy as np

N = 100
SEMENTE_DOS_DADOS = 7
SIGMA = 2.0
W_VERDADEIRO = 300.0
B_VERDADEIRO = 5.0
SIGMA_DO_RUIDO = 1.0


def gerar_dados():
    """Os mesmos dados do esqueleto — idênticos byte a byte (semente 7)."""
    rng = np.random.default_rng(SEMENTE_DOS_DADOS)
    x = rng.normal(0.0, SIGMA, size=N)
    y = W_VERDADEIRO * x + B_VERDADEIRO + rng.normal(0.0, SIGMA_DO_RUIDO, size=N)
    return x, y


def descida(x, y, taxa=0.1, passos=200, semente=42):
    """O laço do slide 9, completo.

    A semente do INÍCIO (42) está fixada de propósito, como no slide: sem
    ela, dois alunos com o mesmo código obteriam pesos iniciais diferentes
    e ninguém confere o do outro.
    """
    rng = np.random.default_rng(semente)
    w, b = rng.normal(size=2)
    perdas = []
    for _ in range(passos):
        erro = (w * x + b) - y            # resíduo
        dw = 2 * np.mean(erro * x)        # derivada em w — TAREFA 1
        db = 2 * np.mean(erro)            # derivada em b — TAREFA 2
        w, b = w - taxa * dw, b - taxa * db
        with np.errstate(over="ignore", invalid="ignore"):
            perdas.append(float(np.mean(erro ** 2)))
    return w, b, perdas


def main():
    parser = argparse.ArgumentParser(
        description="Descida de gradiente à mão (slide 9 do D3-E2) — solução.")
    parser.add_argument("--taxa", type=float, default=0.1)
    parser.add_argument("--passos", type=int, default=200)
    argumentos = parser.parse_args()

    x, y = gerar_dados()
    # o estouro é o resultado esperado na taxa alta — sem alarme na tela
    with np.errstate(over="ignore", invalid="ignore"):
        w, b, perdas = descida(x, y, taxa=argumentos.taxa,
                               passos=argumentos.passos)

    print(f"dados: {N} pontos · pesos que geraram: w={W_VERDADEIRO} "
          f"b={B_VERDADEIRO} (semente dos dados {SEMENTE_DOS_DADOS})")
    print(f"descida: taxa {argumentos.taxa} · {argumentos.passos} passos · "
          f"semente 42")
    for passo, perda in enumerate(perdas, start=1):
        if passo == argumentos.passos:
            print(f"passo {passo:4d} perda {perda:.6g} w {float(w):.6g} "
                  f"b {float(b):.6g}")
        else:
            print(f"passo {passo:4d} perda {perda:.6g}")


if __name__ == "__main__":
    main()
