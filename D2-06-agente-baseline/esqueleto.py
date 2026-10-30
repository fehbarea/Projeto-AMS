"""Laboratório 06 — o agente de linha de base do seu domínio.

O agente mais simples que resolve uma fatia do problema, SEM modelo de
linguagem: percepção (o registro), decisão (regras explícitas), ação (a
recomendação) e medida (a métrica primária do `agent-spec.md`, sobre 30
casos). O número que sai daqui é a linha de base contra a qual o agente de
D10 vai ser comparado — sem ela, "melhorou" é opinião.

Estrutura do slide 22 do D2-E4: uma função `decidir(registro, estado)` com
duas condições — a primeira REATIVA (só a percepção do instante) e a
segunda consultando ESTADO INTERNO (o que o agente já observou do mundo).
Quem caracterizou o ambiente como totalmente observável pode APAGAR a
segunda condição e ficar com um reativo simples — e registra a escolha na
análise, porque o tipo de agente é parte do que a rubrica avalia.

Como usar:
    1. adapte as regras (os TODOs) e os limiares ao SEU domínio;
    2. aponte CAMINHO_DOS_CASOS para o seu conjunto de 30 casos rotulados
       (ou deixe no conjunto de reserva — ver COMO-USAR-A-RESERVA.pdf);
    3. rode:  python medir.py
    4. quando o baseline estiver pronto, copie as funções para
       `src/<projeto>/baseline.py` — é o caminho que a entrega final cobra.

Este módulo roda de fábrica sobre o conjunto de reserva que viaja no
pacote: medida funcionando antes da primeira adaptação.
"""

from __future__ import annotations

import csv
from datetime import date as _date
from pathlib import Path

# --------------------------------------------------------------------------
# Configuração — a troca do dataset é UMA LINHA aqui (slide 29).
# --------------------------------------------------------------------------
CAMINHO_DOS_CASOS = "casos-de-reserva.csv"
# Troque pelo SEU conjunto quando estiver pronto:
# CAMINHO_DOS_CASOS = "dados/meus_casos.csv"

# --------------------------------------------------------------------------
# Os limiares das regras — TODO: troque pelos do SEU domínio.
# (Os valores abaixo são os do domínio de exemplo: máquinas industriais.)
# --------------------------------------------------------------------------
LIMITE_VIBRACAO = 7.0          # mm/s — acima disso, para
LIMITE_TEMPERATURA = 78.0      # °C   — acima disso, para
FALHAS_PARA_INSPECAO = 2       # falhas observadas da família → inspecionar
JANELA_DIAS = 7                # "recentes" = dentro desta janela

# --------------------------------------------------------------------------
# Estado interno — a memória do que o agente JÁ OBSERVOU do ambiente.
# O agente não sabe o futuro: ele acumula os desfechos que o ambiente
# revelou até agora. E "até agora" tem política de esquecimento — decidir
# por quanto tempo guardar é parte da decisão de estado interno (slide 24
# do E2). Sem a janela, duas falhas antigas deixariam a família inteira em
# inspeção para sempre. Quem apagar a segunda condição de decidir() pode
# apagar esta classe junto.
# --------------------------------------------------------------------------


class EstadoDaFrota:
    """O que o agente já observou: falhas por família, dentro da janela."""

    def __init__(self, janela_dias: int = JANELA_DIAS) -> None:
        self._janela = janela_dias
        self._falhas: list[tuple[str, _date]] = []
        self._ultima_data: _date | None = None

    def falhas_recentes(self, familia: str) -> int:
        """Quantas falhas desta família o agente viu, dentro da janela."""
        if self._ultima_data is None:
            return 0
        limite = self._ultima_data.toordinal() - self._janela
        return sum(
            1 for familia_vista, dia in self._falhas
            if familia_vista == familia and dia.toordinal() >= limite)

    def registrar_desfecho(self, registro: dict) -> None:
        """O ambiente revela o desfecho do caso — a percepção do próximo
        ciclo é maior do que a do anterior (parcialmente observável). Sem
        desfecho observado, não há o que registrar."""
        self._ultima_data = _date.fromisoformat(registro["data"])
        if int(registro.get("falhou_depois", 0)) == 1:
            self._falhas.append(
                (registro["tipo_maquina"], self._ultima_data))


# --------------------------------------------------------------------------
# A decisão — o coração do agente, em oito linhas (slide 22)
# --------------------------------------------------------------------------

def decidir(registro: dict, estado: EstadoDaFrota) -> str:
    """Uma rodada: percepção entra, ação sai.

    TODO 1: a condição reativa — limiares sobre o REGISTRO atual.
    TODO 2: a condição com estado interno — ou APAGUE-A, se o seu ambiente
    é totalmente observável, e registre a escolha na análise.
    A ordem importa: a primeira que casar decide.
    """
    if registro["vibracao_mm_s"] > LIMITE_VIBRACAO or \
            registro["temperatura_c"] > LIMITE_TEMPERATURA:
        return "parar_para_manutencao"
    if estado.falhas_recentes(registro["tipo_maquina"]) >= FALHAS_PARA_INSPECAO:
        return "inspecionar_antes_de_operar"
    return "seguir_operando"


def carregar_casos(caminho: str | Path) -> list[dict]:
    """Lê o CSV de casos rotulados, em ordem cronológica — a ordem importa,
    porque o estado interno se acumula caso a caso. encoding utf-8-sig:
    tolera o BOM que o Excel costuma gravar."""
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        casos = list(csv.DictReader(arquivo))
    casos.sort(key=lambda registro: registro["data"])
    for registro in casos:
        registro["idade_meses"] = int(registro["idade_meses"])
        registro["temperatura_c"] = float(registro["temperatura_c"])
        registro["vibracao_mm_s"] = float(registro["vibracao_mm_s"])
        registro["horas_desde_manutencao"] = float(
            registro["horas_desde_manutencao"])
        registro["falhou_depois"] = int(registro["falhou_depois"])
    return casos


if __name__ == "__main__":
    from medir import medir_e_imprimir

    medir_e_imprimir(CAMINHO_DOS_CASOS, decidir, EstadoDaFrota)
