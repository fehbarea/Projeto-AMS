"""Agregações que respondem as perguntas da exploração de dados.

Cada função responde UMA pergunta e devolve um dado pronto para virar
gráfico ou frase de conclusão. O notebook de EDA é o consumidor destas
funções — assim a análise fica testável fora do notebook.

Regra da disciplina: nenhum gráfico sem uma pergunta escrita em cima e
uma conclusão embaixo.
"""

from __future__ import annotations

import pandas as pd


def taxa_falha_geral(quadro: pd.DataFrame) -> float:
    """Fração de registros com falha de máquina (0 a 1)."""
    return float(quadro["falha"].mean())


def taxa_falha_por_tipo(quadro: pd.DataFrame) -> pd.Series:
    """Taxa de falha por tipo de produto (L/M/H), em percentual."""
    return (quadro.groupby("tipo", observed=True)["falha"].mean() * 100.0).rename("taxa_falha_pct")


def distribuicao_desgaste(quadro: pd.DataFrame) -> pd.Series:
    """Estatísticas de desgaste separadas por máquina que falhou ou não."""
    return quadro.groupby("falha")["desgaste"].describe()


def frequencia_de_modos(quadro: pd.DataFrame) -> pd.Series:
    """Quantas ocorrências de cada um dos cinco modos de falha."""
    modos = ["twf", "hdf", "pwf", "osf", "rnf"]
    return quadro[modos].sum().rename("ocorrencias")


def falhas_sem_modo(quadro: pd.DataFrame) -> pd.DataFrame:
    """Registros com falha indicada e nenhum modo marcado.

    No dataset oficial existem 27 casos — a lição de qualidade de dados
    da pergunta 6 do notebook: o indicador geral e os modos discordam.
    """
    modos = ["twf", "hdf", "pwf", "osf", "rnf"]
    return quadro[quadro["falha"] & ~quadro[modos].any(axis=1)]


def acuracia_regra_desgaste(quadro: pd.DataFrame, limiar: int) -> float:
    """Acurácia da regra simples 'falha se desgaste > limiar'.

    É o baseline de referência: qualquer modelo treinado depois (D5)
    precisa bater isso para justificar a existência.
    """
    previsao = quadro["desgaste"] > limiar
    return float((previsao == quadro["falha"]).mean())


def melhor_limiar_desgaste(quadro: pd.DataFrame) -> tuple[int, float]:
    """Varre os limiares possíveis e devolve o melhor (limiar, acurácia)."""
    melhor = (0, -1.0)
    for limiar in range(0, 301, 5):
        acuracia = acuracia_regra_desgaste(quadro, limiar)
        if acuracia > melhor[1]:
            melhor = (limiar, acuracia)
    return melhor


def correlacao_torque_rotacao(quadro: pd.DataFrame) -> float:
    """Correlação de Pearson entre torque e rotação.

    Fisicamente negativa: potência aproximadamente constante significa
    que mais rotação exige menos torque.
    """
    return float(quadro["torque"].corr(quadro["rotacao"]))
