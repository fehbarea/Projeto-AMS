"""Laboratório 02 — a descida à mão.

O coração deste arquivo é a função `descida`, que é o código do slide 9 do
D3-E2 com DUAS linhas em branco — as duas derivadas. Foi esse código que a
turma acabou de ver; complete as duas linhas e rode. Nada mais precisa ser
escrito: os dados, o laço e a impressão da curva já estão prontos.

Como usar:
    1. complete as TAREFAS 1 e 2 (as duas derivadas, exatamente como no slide 9);
    2. rode:  'python esqueleto.py '           (taxa padrão 0,1)
    3. experimente as taxas do slide 12:
       python esqueleto.py --taxa 0.001
       python esqueleto.py --taxa 1.5
    4. preencha `anotacoes.md` com a última linha de cada taxa e as respostas;
    5. quando estiver pronto:  python -m pytest teste.py -q

Os dados nascem de pesos CONHECIDOS (`W_VERDADEIRO` e `B_VERDADEIRO`, com
semente fixada) — é o que permite conferir se a descida chegou perto do
valor certo (slide 10, passo 4).
"""

import argparse

import numpy as np

# --- os dados sintéticos: pesos conhecidos, semente fixada -------------------
N = 100                    # pontos
SEMENTE_DOS_DADOS = 7      # regra do curso: todo número é reproduzível
SIGMA = 2.0                # dispersão de x
W_VERDADEIRO = 300.0       # o peso w que gerou os dados
B_VERDADEIRO = 5.0         # o peso b que gerou os dados
SIGMA_DO_RUIDO = 1.0       # ruído em torno da reta


def gerar_dados():
    """Gera x e y a partir dos pesos conhecidos — o alvo da descida."""
    rng = np.random.default_rng(SEMENTE_DOS_DADOS)
    x = rng.normal(0.0, SIGMA, size=N)
    y = W_VERDADEIRO * x + B_VERDADEIRO + rng.normal(0.0, SIGMA_DO_RUIDO, size=N)
    return x, y


def descida(x, y, taxa=0.1, passos=200, semente=42):
    """O código do slide 9 do D3-E2, com as duas derivadas em branco.

    As linhas marcadas como "encanamento do laboratório" só registram a
    curva de perda — o slide 10 pede que ela seja guardada. A conta do
    slide é exatamente a da função; as duas TAREFAS são as linhas que
    faltam.
    """
    rng = np.random.default_rng(semente)
    w, b = rng.normal(size=2)
    perdas = []                                   # encanamento do laboratório
    for _ in range(passos):
        erro = (w * x + b) - y            # resíduo
        dw = np.mean(erro * x)           # TAREFA 1 — a derivada em w (slide 9)
        db = np.mean(erro)               # TAREFA 2 — a derivada em b (slide 9)
        w, b = w - taxa * dw, b - taxa * db
        with np.errstate(over="ignore", invalid="ignore"):
            perdas.append(float(np.mean(erro ** 2)))  # encanamento: a curva
    return w, b, perdas              # o slide devolve (w, b); o lab junta a curva


def main():
    parser = argparse.ArgumentParser(
        description="Descida de gradiente à mão (slide 9 do D3-E2).")
    parser.add_argument("--taxa", type=float, default=0.1,
                        help="taxa de aprendizado (experimente 0.001, 0.1 e 1.5)")
    parser.add_argument("--passos", type=int, default=200,
                        help="quantidade de passos (o padrão do slide é 200)")
    argumentos = parser.parse_args()

    x, y = gerar_dados()
    try:
        # o estouro é o resultado esperado na taxa alta — sem alarme na tela
        with np.errstate(over="ignore", invalid="ignore"):
            w, b, perdas = descida(x, y, taxa=argumentos.taxa,
                                   passos=argumentos.passos)
    except TypeError:
        raise SystemExit(
            "A descida ainda tem as duas linhas em branco — procure as "
            "TAREFAS 1 e 2 no esqueleto.py e complete-as antes de rodar.")

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
