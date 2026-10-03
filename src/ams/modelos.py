"""Modelos Pydantic do domínio do AMS.

Um LLM devolve texto; o sistema precisa de objetos validados. Estes modelos
são o contrato entre as partes: o dataset vira `LeituraSensor`, a requisição
do usuário vira `OrdemServico` e a resposta do Gemini deve caber em
`AvaliacaoRisco` — ou ela não é aceita.

Este mesmo mecanismo reaparece no curso inteiro: tool calling (D8), saída
estruturada (D9) e ferramentas de agente (D10).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

# Faixas físicas das leituras: mais largas que o dataset (295–305 K etc.)
# para aceitar variação real, mas estreitas o bastante para rejeitar
# impossíveis (0 K, torque negativo, rotação negativa).
FAIXAS = {
    "temperatura_ar": (250.0, 330.0),
    "temperatura_processo": (250.0, 340.0),
    "rotacao": (500.0, 5000.0),
    "torque": (0.0, 200.0),
    "desgaste": (0, 400),
}


class TipoProduto(StrEnum):
    """Tipo de produto na planta: L (baixa), M (média) e H (alta qualidade)."""

    L = "L"
    M = "M"
    H = "H"


class NivelRisco(StrEnum):
    """Nível de risco de falha estimado para a máquina."""

    BAIXO = "baixo"
    MEDIO = "medio"
    ALTO = "alto"


class LeituraSensor(BaseModel):
    """Uma leitura dos sensores de uma máquina (uma linha do dataset AI4I 2020).

    Os validadores rejeitam valores fisicamente impossíveis com mensagens em
    português — é melhor recusar um dado absurdo na porta do que descobrir
    o estrago no meio da análise.
    """

    udi: int = Field(gt=0, description="identificador único da leitura")
    product_id: str = Field(min_length=2, description="código da máquina, ex.: M14860")
    tipo: TipoProduto
    temperatura_ar: float = Field(description="temperatura do ar [K]")
    temperatura_processo: float = Field(description="temperatura do processo [K]")
    rotacao: int = Field(description="velocidade de rotação [rpm]")
    torque: float = Field(description="torque [Nm]")
    desgaste: int = Field(ge=0, description="desgaste da ferramenta [min]")
    falha: bool = Field(description="indicador de falha da máquina")
    twf: bool = Field(description="falha por desgaste da ferramenta")
    hdf: bool = Field(description="falha por dissipação de calor")
    pwf: bool = Field(description="falha de potência")
    osf: bool = Field(description="falha por sobrecarga")
    rnf: bool = Field(description="falha aleatória")

    @field_validator("product_id")
    @classmethod
    def validar_product_id(cls, valor: str) -> str:
        codigo = valor.strip().upper()
        if not codigo or len(codigo) < 2:
            raise ValueError("Product ID vazio ou curto demais — informe o código da máquina.")
        return codigo

    @field_validator("temperatura_ar")
    @classmethod
    def validar_temperatura_ar(cls, valor: float) -> float:
        minimo, maximo = FAIXAS["temperatura_ar"]
        if not minimo <= valor <= maximo:
            raise ValueError(
                f"temperatura do ar de {valor} K está fora da faixa plausível "
                f"({minimo:.0f}–{maximo:.0f} K) — confira a unidade e o sensor."
            )
        return valor

    @field_validator("temperatura_processo")
    @classmethod
    def validar_temperatura_processo(cls, valor: float) -> float:
        minimo, maximo = FAIXAS["temperatura_processo"]
        if not minimo <= valor <= maximo:
            raise ValueError(
                f"temperatura de processo de {valor} K está fora da faixa plausível "
                f"({minimo:.0f}–{maximo:.0f} K) — confira a unidade e o sensor."
            )
        return valor

    @field_validator("rotacao")
    @classmethod
    def validar_rotacao(cls, valor: int) -> int:
        minimo, maximo = FAIXAS["rotacao"]
        if not minimo <= valor <= maximo:
            raise ValueError(
                f"rotação de {valor} rpm está fora da faixa plausível "
                f"({minimo:.0f}–{maximo:.0f} rpm)."
            )
        return valor

    @field_validator("torque")
    @classmethod
    def validar_torque(cls, valor: float) -> float:
        minimo, maximo = FAIXAS["torque"]
        if not minimo <= valor <= maximo:
            raise ValueError(
                f"torque de {valor} Nm está fora da faixa plausível "
                f"({minimo:.0f}–{maximo:.0f} Nm) — torque negativo é impossível."
            )
        return valor

    @field_validator("desgaste")
    @classmethod
    def validar_desgaste(cls, valor: int) -> int:
        minimo, maximo = FAIXAS["desgaste"]
        if not minimo <= valor <= maximo:
            raise ValueError(
                f"desgaste de {valor} min está fora da faixa plausível ({minimo}–{maximo} min)."
            )
        return valor

    @model_validator(mode="after")
    def validar_coerencia(self) -> LeituraSensor:
        """Regras que dependem de mais de um campo.

        Neste dataset, a temperatura de processo é sempre maior que a do ar
        (a máquina gera calor); o contrário indica leitura trocada.
        """
        if self.temperatura_processo <= self.temperatura_ar:
            raise ValueError(
                f"temperatura de processo ({self.temperatura_processo} K) deveria ser maior "
                f"que a do ar ({self.temperatura_ar} K) — leituras possivelmente trocadas."
            )
        return self


class OrdemServico(BaseModel):
    """Uma ordem de serviço a avaliar: máquina, leitura atual e descrição.

    É a unidade de trabalho do agente: o E4 processa 20 delas.
    """

    identificador: str = Field(description="número da ordem, ex.: OS-2026-0001")
    maquina: str = Field(description="Product ID da máquina")
    leitura: LeituraSensor
    descricao: str = Field(description="descrição livre da intervenção planejada")

    @field_validator("identificador")
    @classmethod
    def validar_identificador(cls, valor: str) -> str:
        identificador = valor.strip()
        if len(identificador) < 3:
            raise ValueError(
                "identificador da ordem de serviço curto demais — use o padrão OS-AAAA-NNNN."
            )
        return identificador

    @field_validator("descricao")
    @classmethod
    def validar_descricao(cls, valor: str) -> str:
        descricao = valor.strip()
        if len(descricao) < 10:
            raise ValueError(
                "descrição da intervenção curta demais — o avaliador de risco "
                "precisa saber o que será feito (mínimo 10 caracteres)."
            )
        return descricao


class AvaliacaoRisco(BaseModel):
    """Parecer de risco esperado como resposta do Gemini.

    Este é o modelo que o modelo de linguagem deve preencher. A resposta
    só é aceita se validar aqui — texto solto não vira decisão.
    """

    nivel_risco: NivelRisco
    justificativa: str = Field(max_length=300)
    normas_aplicaveis: list[str] = Field(default_factory=list)
    requer_bloqueio: bool
    confianca: float = Field(ge=0.0, le=1.0)

    @field_validator("justificativa")
    @classmethod
    def validar_justificativa(cls, valor: str) -> str:
        justificativa = valor.strip()
        if len(justificativa) < 10:
            raise ValueError(
                "justificativa curta demais — o técnico precisa entender o porquê "
                "do nível de risco (mínimo 10 caracteres)."
            )
        return justificativa

    @field_validator("normas_aplicaveis")
    @classmethod
    def validar_normas(cls, valor: list[str]) -> list[str]:
        normas = [norma.strip().upper() for norma in valor if norma.strip()]
        if not normas:
            raise ValueError(
                "liste ao menos uma norma aplicável (ex.: NR-12) ou 'NENHUMA' "
                "se nenhuma se aplicar."
            )
        return normas
