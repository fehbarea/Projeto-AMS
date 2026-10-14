"""Testes de comportamento do motor de busca e do catálogo de problemas.

Não são testes de cobertura: cada um prova uma propriedade que os
laboratórios e a entrega final afirmam para a turma. Se algum falhar, o
número que o aluno vai medir está errado — conserte o motor ou o catálogo,
nunca a tabela que o aluno vai preencher.

Execução (da pasta da disciplina):
    python -m pytest fonte/laboratorios/comum -q
"""

import sys
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from busca import (  # noqa: E402
    a_estrela,
    aprofundamento_iterativo,
    busca_em_largura,
    busca_gulosa,
    custo_uniforme,
    profundidade_limitada,
)
from problemas import conformidade, consultas, diagnostico  # noqa: E402

PEQUENAS = [diagnostico.PEQUENA, consultas.PEQUENA, conformidade.PEQUENA]
MAIORES = [diagnostico.MAIOR, consultas.MAIOR, conformidade.MAIOR]


def _uniformes() -> list:
    """As três instâncias pequenas com todos os custos iguais a 1.0.

    Com custos uniformes, caminho mais curto e caminho mais barato são o
    mesmo caminho — é o terreno onde a busca em largura é ótima e onde o
    aprofundamento iterativo tem que concordar com ela.
    """
    return [
        diagnostico.Diagnostico(
            tuple(replace(v, tempo=1.0) for v in diagnostico.CASO_PEQUENO)),
        consultas.Consultas(
            consultas.FATOS_PEQUENOS,
            tuple(replace(f, latencia=1.0) for f in consultas.FONTES_PEQUENAS)),
        conformidade.Conformidade(
            tuple(replace(i, esforco=1.0) for i in conformidade.ITENS_PEQUENOS),
            {nome: 1.0 for nome in conformidade.PENDENCIAS_PEQUENAS},
            fator_retrabalho=1.0),
    ]


def test_largura_e_otima_quando_os_custos_sao_uniformes():
    """(1) Com custos uniformes, a largura devolve caminho de custo ótimo.

    A prova de custo ótimo é o custo uniforme — que é ótimo por construção
    — devolvendo o MESMO custo. E, sendo 1.0 por ação, o custo tem que
    bater com o número de ações.
    """
    for problema in _uniformes():
        largura = busca_em_largura(problema)
        uniforme = custo_uniforme(problema)
        assert largura.encontrou
        assert largura.custo == uniforme.custo
        assert largura.custo == float(len(largura.caminho))


def test_custo_uniforme_e_a_estrela_admissivel_devolvem_o_mesmo_custo():
    """(2) A* com heurística admissível é ótimo: mesmo custo do custo uniforme.

    Os caminhos podem diferir (há empates); o custo, nunca.
    """
    for problema in PEQUENAS + MAIORES:
        uniforme = custo_uniforme(problema)
        informada = a_estrela(problema, problema.heuristica_admissivel)
        assert uniforme.encontrou and informada.encontrou
        assert informada.custo == uniforme.custo


def test_a_estrela_expande_menos_que_o_custo_uniforme_na_instancia_maior():
    """(3) A heurística admissível economiza nós — o efeito que o lab-05 mede.

    Se deixar de valer, a heurística ficou fraca demais e o laboratório
    perde o efeito: conserte a heurística, não o teste.
    """
    for problema in MAIORES:
        uniforme = custo_uniforme(problema)
        informada = a_estrela(problema, problema.heuristica_admissivel)
        assert informada.nos_expandidos < uniforme.nos_expandidos


def test_heuristica_inadmissivel_devolve_caminho_mais_caro_em_algum_problema():
    """(4) A inadmissível tem que custar caro em algum lugar — senão o lab-05
    não tem o que mostrar. (Na conformidade ela superestima sem piorar o
    caminho: os objetivos diferem só no re-trabalho; nos outros dois, piora.)
    """
    otimos = {id(p): custo_uniforme(p).custo for p in MAIORES}
    pioras = [
        a_estrela(problema, problema.heuristica_inadmissivel).custo
        > otimos[id(problema)]
        for problema in MAIORES
    ]
    assert any(pioras)


def test_profundidade_limitada_distingue_corte_de_insucesso():
    """(5) 'Não existe solução' e 'cortou no limite' são respostas diferentes.

    - Limite 2 na conformidade pequena: a solução é mais funda, e os nós do
      limite ainda tinham ações → cortou.
    - Limite 2 na consultas pequena: a solução é rasa e é achada.
    - Fato que nenhuma fonte entrega: o espaço esgota sem cortar → não
      existe solução, com qualquer limite.
    """
    cortada = profundidade_limitada(conformidade.PEQUENA, 2)
    assert not cortada.encontrou and cortada.cortou

    achada = profundidade_limitada(consultas.PEQUENA, 2)
    assert achada.encontrou and not achada.cortou

    inatingivel = consultas.Consultas(
        frozenset({"relatório que nenhuma fonte emite"}), consultas.FONTES_PEQUENAS)
    sem_solucao = profundidade_limitada(inatingivel, 5)
    assert not sem_solucao.encontrou and not sem_solucao.cortou
    assert not custo_uniforme(inatingivel).encontrou


class _Portao:
    """Problema mínimo em que o custo só se conhece no estado SEGUINTE.

    Nos três problemas do catálogo, `custo` olha o estado de partida e a
    ação; nenhum olha o estado de chegada. Um problema do aluno pode olhar
    — o protocolo permite —, e é ele quem este problema representa.
    """

    estado_inicial = "porta fechada"

    def acoes(self, estado: str) -> list[str]:
        return ["abrir"] if estado == "porta fechada" else []

    def transicao(self, estado: str, acao: str) -> str:
        return "porta aberta"

    def objetivo(self, estado: str) -> bool:
        return estado == "porta aberta"

    def custo(self, estado: str, acao: str, estado_seguinte: str) -> float:
        return 100.0 if estado_seguinte == "porta aberta" else 1.0


def test_todas_as_buscas_passam_o_estado_seguinte_para_o_custo():
    """(7) `custo` recebe o estado de CHEGADA, não uma cópia do de partida.

    Com custos uniformes — o terreno dos testes 1 e 6 — as duas coisas dão
    o mesmo número, e o erro passa despercebido. Aqui não: o custo real da
    única ação é 100,0, e quem passa o argumento errado devolve 1,0.
    """
    problema = _Portao()
    for busca in (busca_em_largura, custo_uniforme):
        assert busca(problema).custo == 100.0
    for informada in (busca_gulosa, a_estrela):
        assert informada(problema, lambda _: 0.0).custo == 100.0


def test_aprofundamento_iterativo_concorda_com_a_largura_quando_os_custos_sao_uniformes():
    """(6) Com custos uniformes, o aprofundamento iterativo acha a mesma
    solução da busca em largura — mesmo caminho, mesmo custo.
    """
    for problema in _uniformes():
        largura = busca_em_largura(problema)
        iterativo = aprofundamento_iterativo(problema, limite_maximo=20)
        assert iterativo.encontrou
        assert iterativo.caminho == largura.caminho
        assert iterativo.custo == largura.custo
