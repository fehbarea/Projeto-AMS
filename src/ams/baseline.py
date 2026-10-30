from __future__ import annotations

import csv
from datetime import date as _date
from pathlib import Path

# --------------------------------------------------------------------------
# Configuração — a troca do dataset é UMA LINHA aqui (slide 29).
# --------------------------------------------------------------------------
CAMINHO_DOS_CASOS = r"C:\pos-agentes\Projeto-AMS\data\meus_casos.csv"
# Troque pelo SEU conjunto quando estiver pronto:
# CAMINHO_DOS_CASOS = "dados/meus_casos.csv"

# --------------------------------------------------------------------------
# Os limiares das regras — TODO: troque pelos do SEU domínio.
# (Os valores abaixo são os do domínio de exemplo: máquinas industriais.)
# --------------------------------------------------------------------------
LIMITE_TENSAO = 50.0
LIMITE_PRESSAO = 10.0    
FALHAS_PARA_PARECER = 2 
JANELA_DIAS = 15
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
                (registro["tipo_equipamento"], self._ultima_data))


# --------------------------------------------------------------------------
# A decisão — o coração do agente, em oito linhas (slide 22)
# --------------------------------------------------------------------------

def decidir(registro: dict, estado: EstadoDaFrota) -> str:

    if registro["tensao_v"] > LIMITE_TENSAO or registro["pressao_bar"] > LIMITE_PRESSAO:
        return "bloqueio_loto"
        
    if estado.falhas_recentes(registro["tipo_equipamento"]) >= FALHAS_PARA_PARECER:
        return "exigir_parecer"
        
    return "manutencao_padrao"


def carregar_casos(caminho: str | Path) -> list[dict]:
    """Lê o CSV de casos rotulados, em ordem cronológica — a ordem importa,
    porque o estado interno se acumula caso a caso. encoding utf-8-sig:
    tolera o BOM que o Excel costuma gravar."""
    with Path(caminho).open(encoding="utf-8-sig", newline="") as arquivo:
        casos = list(csv.DictReader(arquivo,delimiter="," ))
    casos.sort(key=lambda registro: registro["data"])
    for registro in casos:
        registro["tensao_v"] = float(registro["tensao_v"])
        registro["pressao_bar"] = float(registro["pressao_bar"])
        registro["falhou_depois"] = int(registro["falhou_depois"])
    return casos


if __name__ == "__main__":
    from medir import medir_e_imprimir

    medir_e_imprimir(CAMINHO_DOS_CASOS, decidir, EstadoDaFrota)
