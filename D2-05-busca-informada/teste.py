"""Testes do Laboratório 05 — as três verificações da heurística.

Como usar (da pasta do laboratório):
    python -m pytest teste.py -q

São as verificações do motor de busca (B02) aplicadas às heurísticas:

  (a) a admissível vale ZERO em todo estado objetivo;
  (b) o A* com a admissível devolve o MESMO CUSTO que o custo uniforme
      (é a admissibilidade que garante isso — slide 26);
  (c) o A* com a admissível expande MENOS nós que o custo uniforme na
      instância maior (é a economia que o laboratório mede).

As três rodam sobre cada instância do catálogo com a heurística DELA, e
sobre a formulação apontada no `esqueleto.py` com a heurística DELE — no
desafio, é aí que a SUA heurística é provada. Mais duas famílias: o
gabarito numérico de `comum/MEDICOES.md` e o contraste da inadmissível
(devolve caminho mais caro que o ótimo em pelo menos um problema, e
superestima em algum estado).

Se a (c) falhar para a sua heurística, o slide 36 tem o diagnóstico:
estimativa fraca — volte ao relaxamento e remova uma restrição menor.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_AQUI = Path(__file__).resolve().parent


def _pasta_do_comum() -> Path:
    for pasta in (_AQUI, *_AQUI.parents):
        if (pasta / "comum" / "busca.py").is_file():
            return pasta / "comum"
    raise FileNotFoundError(
        "comum/busca.py não encontrado — extraia o pacote inteiro: a pasta "
        "comum/ viaja junto do laboratório.")


_pasta = str(_pasta_do_comum())
if _pasta not in sys.path:
    sys.path.insert(0, _pasta)

from busca import a_estrela, busca_gulosa, custo_uniforme  # noqa: E402
from problemas import conformidade, consultas, diagnostico  # noqa: E402

_spec = importlib.util.spec_from_file_location("esqueleto", _AQUI / "esqueleto.py")
esqueleto = importlib.util.module_from_spec(_spec)
sys.modules["esqueleto"] = esqueleto
_spec.loader.exec_module(esqueleto)  # type: ignore[union-attr]

CATALOGO = {
    "diagnostico": diagnostico,
    "consultas": consultas,
    "conformidade": conformidade,
}
MAIORES = [m.MAIOR for m in CATALOGO.values()]
PEQUENAS = [m.PEQUENA for m in CATALOGO.values()]

# Gabarito de MEDICOES.md (30/08/2026), instâncias MAIOR:
# (problema, busca) → (custo, ações, expandidos, gerados, prof. máx.)
GABARITO = {
    ("diagnostico", "gulosa[admissivel]"): (20.0, 5, 6, 50, 5),
    ("diagnostico", "a_estrela[admissivel]"): (20.0, 5, 77, 297, 5),
    ("diagnostico", "gulosa[inadmissivel]"): (83.0, 11, 12, 77, 11),
    ("diagnostico", "a_estrela[inadmissivel]"): (77.0, 10, 11, 75, 10),
    ("consultas", "gulosa[admissivel]"): (20.0, 1, 2, 14, 1),
    ("consultas", "a_estrela[admissivel]"): (17.1, 6, 1307, 2338, 6),
    ("consultas", "gulosa[inadmissivel]"): (20.0, 1, 2, 14, 1),
    ("consultas", "a_estrela[inadmissivel]"): (20.0, 1, 2, 14, 1),
    ("conformidade", "gulosa[admissivel]"): (30.0, 14, 15, 60, 14),
    ("conformidade", "a_estrela[admissivel]"): (30.0, 14, 13209, 16560, 14),
    ("conformidade", "gulosa[inadmissivel]"): (30.0, 14, 15, 60, 14),
    ("conformidade", "a_estrela[inadmissivel]"): (30.0, 14, 491, 1084, 14),
}


def _h_admissivel_do(problema):
    """A heurística admissível DAQUELA instância — cada módulo do catálogo
    traz a sua; só quem não traz delega ao esqueleto."""
    if hasattr(problema, "heuristica_admissivel"):
        return problema.heuristica_admissivel
    return esqueleto.heuristica_admissivel


def _h_inadmissivel_do(problema):
    if hasattr(problema, "heuristica_inadmissivel"):
        return problema.heuristica_inadmissivel
    return esqueleto.heuristica_inadmissivel


def _objetivos_alcancaveis(problema, teto: int = 5_000) -> list:
    """Uma amostra dos estados objetivos alcançáveis, para o teste (a)."""
    vistos = {problema.estado_inicial}
    fila = [problema.estado_inicial]
    objetivos = []
    while fila and len(vistos) < teto:
        atual = fila.pop()
        if problema.objetivo(atual):
            objetivos.append(atual)
            if len(objetivos) >= 20:
                break
        for acao in problema.acoes(atual):
            seguinte = problema.transicao(atual, acao)
            if seguinte not in vistos:
                vistos.add(seguinte)
                fila.append(seguinte)
    return objetivos


# --- as três verificações ---------------------------------------------------

def test_a_h_admissivel_valida_zero_em_todo_estado_objetivo():
    for problema in PEQUENAS + MAIORES + [esqueleto._problema()]:
        h = _h_admissivel_do(problema)
        for objetivo in _objetivos_alcancaveis(problema):
            valor = h(objetivo)
            assert abs(valor) < 1e-9, (
                f"h({objetivo!r}) = {valor}, devia ser 0. Toda estimativa "
                "tem de zerar no objetivo — sem isso nem a admissibilidade "
                "sobrevive (slide 25).")


def test_a_estrela_com_a_admissivel_devolve_o_custo_otimo():
    for problema in PEQUENAS + MAIORES + [esqueleto._problema()]:
        uniforme = custo_uniforme(problema)
        informada = a_estrela(problema, _h_admissivel_do(problema))
        assert informada.encontrou and uniforme.encontrou
        assert round(informada.custo, 4) == round(uniforme.custo, 4), (
            "o A* com a heurística admissível devolveu caminho mais caro "
            "que o custo uniforme — a heurística superestima (slide 26: "
            "errar para mais, uma vez que seja, derruba a garantia).")


def test_a_estrela_com_a_admissivel_expande_menos_na_instancia_maior():
    for problema in MAIORES:
        uniforme = custo_uniforme(problema)
        informada = a_estrela(problema, _h_admissivel_do(problema))
        assert informada.nos_expandidos < uniforme.nos_expandidos, (
            f"o A* expandiu {informada.nos_expandidos} contra "
            f"{uniforme.nos_expandidos} do custo uniforme — a heurística "
            "está fraca (slide 36). Volte ao relaxamento e remova uma "
            "restrição menor: a estimativa sobe sem superestimar.")


# --- o gabarito numérico do catálogo ----------------------------------------

def test_gabarito_das_linhas_informadas_nas_instancias_maior():
    for (nome, nome_busca), esperado in GABARITO.items():
        problema = CATALOGO[nome].MAIOR
        # "inadmissivel" CONTÉM "admissivel" — o corte é pelo rótulo inteiro
        admissivel = nome_busca.endswith("[admissivel]")
        h = (_h_admissivel_do(problema) if admissivel
             else _h_inadmissivel_do(problema))
        r = (busca_gulosa(problema, h) if "gulosa" in nome_busca
             else a_estrela(problema, h))
        obtido = (round(r.custo, 4), len(r.caminho), r.nos_expandidos,
                  r.nos_gerados, r.profundidade_maxima)
        assert obtido == esperado, (
            f"{nome}/{nome_busca}: obtido {obtido}, gabarito {esperado} "
            "(comum/MEDICOES.md). Reporte — não ajuste a tabela.")


# --- o contraste da inadmissível --------------------------------------------

def test_a_inadmissivel_custa_caro_em_algum_lugar():
    pioras = []
    for problema in MAIORES:
        otimo = round(custo_uniforme(problema).custo, 4)
        com_ela = round(a_estrela(problema, _h_inadmissivel_do(problema)).custo, 4)
        pioras.append(com_ela > otimo)
    assert any(pioras), (
        "a inadmissível devolveu caminho ótimo em tudo — o contraste que o "
        "laboratório mostra sumiu. Confira as heurísticas do catálogo.")


class _APartirDe:
    """O mesmo problema com outro estado inicial — para medir o custo REAL
    restante de um estado: roda o custo uniforme a partir dele."""

    def __init__(self, problema, estado_inicial):
        self._problema = problema
        self.estado_inicial = estado_inicial

    def acoes(self, estado):
        return self._problema.acoes(estado)

    def transicao(self, estado, acao):
        return self._problema.transicao(estado, acao)

    def objetivo(self, estado):
        return self._problema.objetivo(estado)

    def custo(self, estado, acao, estado_seguinte):
        return self._problema.custo(estado, acao, estado_seguinte)


def _estados_rasos(problema, fundura_maxima: int = 2, teto: int = 8) -> list:
    """Estados do começo da busca, NÃO objetivos — é lá que a inadmissível
    superestima (no objetivo, toda estimativa honesta ou desonesta zera)."""
    vistos = {problema.estado_inicial}
    fila = [(problema.estado_inicial, 0)]
    achados = []
    while fila:
        atual, fundura = fila.pop(0)
        if fundura > fundura_maxima or len(achados) >= teto:
            break
        if not problema.objetivo(atual):
            achados.append(atual)
        for acao in problema.acoes(atual):
            seguinte = problema.transicao(atual, acao)
            if seguinte not in vistos:
                vistos.add(seguinte)
                fila.append((seguinte, fundura + 1))
    return achados


def test_a_inadmissivel_superestima_em_algum_estado():
    exageros = []
    for problema in PEQUENAS:
        h = _h_inadmissivel_do(problema)
        for estado in _estados_rasos(problema):
            real = custo_uniforme(_APartirDe(problema, estado)).custo
            exageros.append(h(estado) > real + 1e-9)
    assert any(exageros), (
        "a inadmissível não superestimou em nenhum estado da amostra — "
        "confira as heurísticas do catálogo.")
