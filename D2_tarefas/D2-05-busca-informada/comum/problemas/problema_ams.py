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
    EtapaAMS("EstimarRiscoBaixo", "RISCO", 0.5, "Baixo"),
    EtapaAMS("IdentificarNormas", "NORMA", 45.0, "NR-10, NR-12, NR-35"),
    EtapaAMS("IdentificarNormasCaras", "NORMA", 100.0, "NR-10, NR-12, NR-35, NR-45, NR-55"),
    EtapaAMS("RecomendarBloqueio", "DECISAO_LOTO", 5.0, "BloqueioRecomendado"),
    EtapaAMS("DispensarBloqueio", "DECISAO_LOTO", 5.0, "BloqueioDispensado"),
    EtapaAMS("GerarParecerJustificado", "PARECER", 20.0, "ParecerGerado"),
    EtapaAMS("GerarParecerJustificadoDetalahado", "PARECER", 40.0, "ParecerGerado"),
    
    EtapaAMS("ConsultarHistoricoOS", "COMPLEMENTAR", 12.0, "SemReincidencia"),
    EtapaAMS("InspecionarVibracaoFisica", "COMPLEMENTAR", 30.0, "VibracaoNormal"),
    EtapaAMS("ChecarManuaisDoFabricante", "COMPLEMENTAR", 25.0, "LeituraConcluida"),
    EtapaAMS("EntrevistarOperadorDaMaquina", "COMPLEMENTAR", 15.0, "RelatoColetado"),
    EtapaAMS("AuditarCalibracaoSensores", "COMPLEMENTAR", 40.0, "SensoresOK"),
    EtapaAMS("MedirTemperaturaBancadaLocal", "COMPLEMENTAR", 10.0, "DentroDoLimite"),
    EtapaAMS("VerificarEstoqueDePecas", "COMPLEMENTAR", 8.0, "PecasDisponiveis"),
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
                return 250.0 
            if acao == "DispensarBloqueio" and risco_atual in ("Alto", "Médio"):
                return 1000.0
        
        return etapa.custo_base
    
    def heuristica_admissivel(
        self, estado: tuple[tuple[str, ...], tuple[str, ...]]
    ) -> float:

        feitas, _ = estado
        categorias_feitas = {self._por_nome[f].categoria for f in feitas}
        essenciais = {"RISCO", "NORMA", "DECISAO_LOTO", "PARECER"}
        faltam = essenciais - categorias_feitas
        
        if not faltam:
            return 0.0
            
        custo_otimista = 0.0
        for cat in faltam:
            etapas_cat = [e for e in self.etapas if e.categoria == cat]
            if etapas_cat:
                custo_otimista += min(e.custo_base for e in etapas_cat)
                
        return custo_otimista

    def heuristica_inadmissivel(
        self, estado: tuple[tuple[str, ...], tuple[str, ...]]
    ) -> float:

        feitas, _ = estado
        categorias_feitas = {self._por_nome[f].categoria for f in feitas}
        essenciais = {"RISCO", "NORMA", "DECISAO_LOTO", "PARECER"}
        faltam = essenciais - categorias_feitas

        ja_feito = sum(self._por_nome[feita].custo_base for feita in feitas)
        nao_feito = sum(self._por_nome[etapa.nome].custo_base for etapa in self.etapas if etapa.categoria in faltam)
        complementares = 0.0
        
        for etapa in self.etapas:
            if etapa.categoria == "COMPLEMENTAR" and etapa.nome not in feitas:
                complementares += etapa.custo_base *2
            
        return (3.0 * nao_feito - 2.0 * ja_feito) + complementares 


PEQUENA = TriagemAMS(CASO_PEQUENO)
MAIOR = TriagemAMS(CASO_MAIOR)