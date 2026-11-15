"""Testes do Laboratório 04 — o que o mapa promete, conferido.

Como usar (da pasta do laboratório):
    python -m pytest teste.py -q

O que cada família confere:

  1. A CONFERÊNCIA — o seu cosseno é o do slide 16 e os números dos pares
     exemplares batem com a medida no espaço original (par que confirma e
     par que NÃO confirma — o critério do slide 52 precisa dos dois);
  2. A TRANSFORMAÇÃO FIXA — projetar o conjunto inteiro, vetor a vetor,
     reproduz o mapa de componentes principais (a resposta da pergunta 4
     do slide 53: PCA posiciona ponto novo; a vizinhança, não);
  3. O DETERMINISMO — a vizinhança com a MESMA semente reproduz o mapa
     (e por isso a semente vai declarada na figura) e muda com outra
     semente (slide 54);
  4. A ESCOLHA DO SLIDE 55 — normalizar ou não muda o mapa, medida pela
     correlação das distâncias entre os dois mapas;
  5. O FECHAMENTO — pares-conferidos.md com os três pares conferidos, as
     quatro respostas do slide 53 e o caso em que o mapa enganou.

Se os testes falham citando `...` (Ellipsis), as TAREFAS ainda estão em
branco — esse é o estado de partida.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

_AQUI = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location("esqueleto", _AQUI / "esqueleto.py")
esqueleto = importlib.util.module_from_spec(_spec)
sys.modules["esqueleto"] = esqueleto
_spec.loader.exec_module(esqueleto)  # type: ignore[union-attr]

# Os pares exemplares desta máquina e semente: (35, 36) são vizinhos no
# mapa e o cosseno original CONFIRMA; (60, 77) são vizinhos no mapa e o
# cosseno original NÃO confirma — o caso de engano do critério do slide 52.
PAR_CONFIRMA = (35, 36)
COS_CONFIRMA = 0.9780
PAR_ENGANO = (60, 77)
COS_ENGANO = 0.1228

_FRASES, MATRIZ = esqueleto.carregar("manutencao")
CRUDA = esqueleto.preparar(MATRIZ, normalizar=False)
NORMALIZADA = esqueleto.preparar(MATRIZ, normalizar=True)


# --- 1. a conferência ----------------------------------------------------------

def test_o_cosseno_e_o_do_slide_16():
    assert esqueleto.similaridade_cosseno(NORMALIZADA[7], NORMALIZADA[7]) is not None, \
        "a TAREFA 1 ainda está em branco"
    assert abs(float(esqueleto.similaridade_cosseno(NORMALIZADA[7],
                                                    NORMALIZADA[7])) - 1.0) < 1e-9
    ortogonal = np.array([1.0, 0.0, 0.0])
    assert abs(float(esqueleto.similaridade_cosseno(ortogonal,
                                                    np.array([0.0, 2.0, 0.0])))) < 1e-9


def test_os_pares_exemplares_batem_com_o_espaco_original():
    obtido_confirma = float(esqueleto.similaridade_cosseno(
        NORMALIZADA[PAR_CONFIRMA[0]], NORMALIZADA[PAR_CONFIRMA[1]]))
    obtido_engano = float(esqueleto.similaridade_cosseno(
        NORMALIZADA[PAR_ENGANO[0]], NORMALIZADA[PAR_ENGANO[1]]))
    assert abs(obtido_confirma - COS_CONFIRMA) < 2e-4, (
        f"o par {PAR_CONFIRMA} deu {obtido_confirma:.4f}; o esperado é "
        f"{COS_CONFIRMA:.4f} — a conferência precisa medir no espaço ORIGINAL")
    assert abs(obtido_engano - COS_ENGANO) < 2e-4, (
        f"o par {PAR_ENGANO} deu {obtido_engano:.4f}; o esperado é "
        f"{COS_ENGANO:.4f} (o caso em que o mapa engana)")


def test_a_conferencia_devolve_os_dois_vereditos():
    resultados = dict(esqueleto.conferir_pares(
        [PAR_CONFIRMA, PAR_ENGANO], NORMALIZADA))
    assert resultados[PAR_CONFIRMA] >= 0.5
    assert resultados[PAR_ENGANO] < 0.5


# --- 2. a transformação fixa ------------------------------------------------------

def test_posicionar_novo_reproduz_o_mapa():
    pontos, modelo = esqueleto.reduzir_pca(NORMALIZADA)
    assert esqueleto.posicionar_novo(NORMALIZADA[7], modelo) is not None, \
        "a TAREFA 2 ainda está em branco"
    reprojetado = np.array([esqueleto.posicionar_novo(vetor, modelo)
                            for vetor in NORMALIZADA])
    assert np.allclose(reprojetado, pontos), (
        "posicionar_novo não reproduz o mapa — a projeção do ponto novo "
        "é (vetor − centro) @ componentes (a transformação é FIXA, slide 53)")


# --- 3. o determinismo ------------------------------------------------------------

def test_a_vizinhanca_reproduz_com_a_mesma_semente():
    primeira = esqueleto.reduzir_vizinhanca(NORMALIZADA, esqueleto.SEMENTE_PADRAO)
    segunda = esqueleto.reduzir_vizinhanca(NORMALIZADA, esqueleto.SEMENTE_PADRAO)
    assert np.allclose(primeira, segunda), (
        "a mesma semente deu mapas diferentes — sem isso a figura declarada "
        "não pode ser reproduzida (slide 54)")


def test_a_vizinhanca_muda_com_outra_semente():
    primeira = esqueleto.reduzir_vizinhanca(NORMALIZADA, esqueleto.SEMENTE_PADRAO)
    outra = esqueleto.reduzir_vizinhanca(NORMALIZADA, 42)
    assert float(np.abs(primeira - outra).mean()) > 1.0, (
        "sementes diferentes devolveram mapas iguais — o slide 54 afirma o "
        "contrato: duas execuções PODEM dar figuras diferentes")


# --- 4. a escolha do slide 55 -------------------------------------------------------

def _correlacao_de_distancias(a, b):
    indice = np.triu_indices(len(a), k=1)
    da = np.linalg.norm(a[indice[0]] - a[indice[1]], axis=1)
    db = np.linalg.norm(b[indice[0]] - b[indice[1]], axis=1)
    return float(np.corrcoef(da, db)[0, 1])


def test_normalizar_ou_nao_muda_o_mapa():
    mapa_crudo, _ = esqueleto.reduzir_pca(CRUDA)
    mapa_normalizado, _ = esqueleto.reduzir_pca(NORMALIZADA)
    correlacao = _correlacao_de_distancias(mapa_crudo, mapa_normalizado)
    assert 0.55 <= correlacao <= 0.75, (
        f"a correlação das distâncias entre os dois mapas deu {correlacao:.3f}; "
        "a medida nestes conjuntos é ≈0,66: a escolha do slide 55 muda o mapa "
        "de verdade — e por isso ela vai registrada na figura")


# --- 5. o fechamento ----------------------------------------------------------------

def _pendencias():
    """O que falta para o critério do slide 52, sobre o arquivo de conferência."""
    caminho = Path("pares-conferidos.md")
    if not caminho.is_file():
        return ["pendências: pares-conferidos.md não existe — rode primeiro "
                "python esqueleto.py (e depois com --pares), responda e rode "
                "este teste de novo."]
    corpo = caminho.read_text(encoding="utf-8")
    linhas = corpo.splitlines()
    na_tabela = [linha for linha in linhas if linha.startswith("| (")]
    pendencias = []
    if len(na_tabela) < 3:
        pendencias.append(
            f"pendências: a tabela do passo 4 tem {len(na_tabela)} par(es) "
            "conferido(s); o slide 52 pede TRÊS — rode com --pares.")
    marcados = 0
    for posicao, linha in enumerate(linhas):
        alvo = linha.strip()
        seguinte = linhas[posicao + 1].strip() if posicao + 1 < len(linhas) else ""
        if alvo.startswith("R:") and (alvo[2:].strip() or seguinte):
            marcados += 1
    if marcados < 5:
        pendencias.append(
            f"pendências: faltam respostas ({marcados} de 5 — as quatro "
            "perguntas do slide 53 e o caso em que o mapa enganou).")
    return pendencias


def test_o_arquivo_de_conferencia_esta_fechado():
    pendencias = _pendencias()
    assert not pendencias, "\n".join(pendencias)


if __name__ == "__main__":
    pendencias = _pendencias()
    if pendencias:
        print("pares-conferidos.md ainda não está fechado:")
        for pendencia in pendencias:
            print(f"  - {pendencia}")
        raise SystemExit(1)
    print("pares-conferidos.md fechado: três pares conferidos, as quatro "
          "perguntas e o caso de engano registrados.")
