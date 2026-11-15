from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class EtapaAMS:
    nome: str
    categoria: str        # 'RISCO', 'NORMA', 'DECISAO_LOTO', 'PARECER'
    custo_base: float     # Latência ou esforço computacional em ms
    resultado_fixo: str   # O que o ambiente revelará/aplicará (oráculo)



CASO_PEQUENO: tuple[EtapaAMS, ...] = (
    EtapaAMS("EstimarRiscoAI4I", "RISCO", 1.0, "Baixo"),
    EtapaAMS("IdentificarNormas", "NORMA", 30.0, "NR-12"),
    EtapaAMS("RecomendarBloqueio", "DECISAO_LOTO", 5.0, "BloqueioRecomendado"),
    EtapaAMS("DispensarBloqueio", "DECISAO_LOTO", 5.0, "BloqueioDispensado"),
    EtapaAMS("GerarParecerJustificado", "PARECER", 15.0, "ParecerGerado"),
)


CASO_MAIOR: tuple[EtapaAMS, ...] = (
    EtapaAMS("EstimarRiscoAI4I", "RISCO", 1.0, "Alto"),
    EtapaAMS("IdentificarNormas", "NORMA", 45.0, "NR-10, NR-12, NR-35"),
    EtapaAMS("RecomendarBloqueio", "DECISAO_LOTO", 5.0, "BloqueioRecomendado"),
    EtapaAMS("DispensarBloqueio", "DECISAO_LOTO", 5.0, "BloqueioDispensado"),
    EtapaAMS("GerarParecerJustificado", "PARECER", 20.0, "ParecerGerado"),
)


class TriagemAMS:

    def __init__(self, etapas: tuple[EtapaAMS, ...]):
        self.etapas = etapas
        self._por_nome = {e.nome: e for e in etapas}
        self.estado_inicial: tuple[tuple[str, ...], tuple[str, ...]] = ((), ())

    def acoes(self, estado: tuple[tuple[str, ...], tuple[str, ...]]) -> list[str]:
        feitas, _ = estado
        categorias_feitas = {self._por_nome[f].categoria for f in feitas}
        
        ativas = []
        for etapa in self.etapas:
            if etapa.nome in feitas:
                continue
            
            if etapa.categoria in ("RISCO", "NORMA"):
                ativas.append(etapa.nome)
            elif etapa.categoria == "DECISAO_LOTO":
                if "RISCO" in categorias_feitas and "NORMA" in categorias_feitas:
                    ativas.append(etapa.nome)
            elif etapa.categoria == "PARECER":
                if "DECISAO_LOTO" in categorias_feitas:
                    ativas.append(etapa.nome)
                    
        return ativas

    def transicao(
        self, estado: tuple[tuple[str, ...], tuple[str, ...]], acao: str
    ) -> tuple[tuple[str, ...], tuple[str, ...]]:
        feitas, valores = estado
        etapa = self._por_nome[acao]
        
        novas_feitas = tuple(sorted((*feitas, acao)))
        novos_valores = tuple(sorted((*valores, etapa.resultado_fixo)))
        
        return novas_feitas, novos_valores

    def objetivo(self, estado: tuple[tuple[str, ...], tuple[str, ...]]) -> bool:
        feitas, _ = estado
        categorias_feitas = {self._por_nome[f].categoria for f in feitas}
        return {"RISCO", "NORMA", "DECISAO_LOTO", "PARECER"}.issubset(categorias_feitas)

    def custo(
        self,
        estado: tuple[tuple[str, ...], tuple[str, ...]],
        acao: str,
        estado_seguinte: tuple[tuple[str, ...], tuple[str, ...]],
    ) -> float:
        feitas, _ = estado
        etapa = self._por_nome[acao]
        
        risco_atual = "Pendente"
        for f in feitas:
            if self._por_nome[f].categoria == "RISCO":
                risco_atual = self._por_nome[f].resultado_fixo
                
        if etapa.categoria == "DECISAO_LOTO":
            if acao == "RecomendarBloqueio" and risco_atual == "Baixo":
                return 250.0  # Penalidade alta: paralisou máquina sem necessidade
            if acao == "DispensarBloqueio" and risco_atual in ("Alto", "Médio"):
                return 1000.0 # Penalidade severa: liberou equipamento sob risco iminente
        
        return etapa.custo_base


PEQUENA = TriagemAMS(CASO_PEQUENO)
MAIOR = TriagemAMS(CASO_MAIOR)