"""Teste de sanidade da formulação — o laboratório 03 prometeu este teste.

O que ele checa (slide 48 do D2-E2: "rode o teste de sanidade que vem no
pacote") — as seis verificações, cada uma com o que fazer quando falha:

  1. `estado_inicial` (e os estados alcançados) é HASHABLE — sem isso o
     conjunto de explorados quebra na primeira inserção;
  2. `transicao` é FUNÇÃO: a mesma ação no mesmo estado devolve sempre o
     mesmo estado — chama duas vezes e compara;
  3. `acoes` devolve a mesma lista, na MESMA ORDEM, para o mesmo estado —
     a ordem estável é o que torna as rodadas reproduzíveis;
  4. `custo` é sempre positivo ou zero — custo negativo quebra as
     garantias de otimalidade das buscas;
  5. `objetivo` é alcançável a partir do estado inicial numa busca em
     largura com teto de nós — se não for, a formulação pode estar vazia;
  6. o erro do ESTADO QUE GUARDA O CAMINHO (D2-E2, slide 47): duas
     sequências de ações diferentes que levam à mesma situação precisam
     produzir estados iguais. Detecta por amostra de caminhos curtos e
     AVISA quando encontra situações equivalentes com estados distintos.

A mensagem de erro diz o que fazer, não só o que houve.

Uso (da pasta do laboratório):

    python verificar-formulacao.py                              # o catálogo
    python verificar-formulacao.py meu_problema.py:MEU_PROBLEMA
    python verificar-formulacao.py meu_problema.py              # 1 candidato

Sem argumentos, roda sobre os três subproblemas do catálogo (as instâncias
pequenas e as maiores) — é a prova de que o teste funciona antes de apontá-lo
para o seu. Devolve código de saída 1 se alguma verificação vermelha.

Depende só da biblioteca padrão e do motor `comum/` (para o modo sem
argumentos). Roda em Python 3.10.
"""

from __future__ import annotations

import importlib.util
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# O motor mora em comum/, irmão da pasta do laboratório na árvore fonte e
# vizinho dentro do pacote extraído — este passeio sobe até achar o buscado.
_AQUI = Path(__file__).resolve().parent


def pasta_do_comum() -> Path:
    for pasta in (_AQUI, *_AQUI.parents):
        if (pasta / "comum" / "busca.py").is_file():
            return pasta / "comum"
    raise FileNotFoundError(
        f"comum/busca.py não encontrado a partir de {_AQUI}. Extraia o pacote "
        "inteiro: a pasta comum/ viaja junto do laboratório."
    )


TETO_DE_NOS = 50_000          # o teto da busca em largura da verificação 5
LIMITE_DA_AMOSTRA = 2_000     # estados guardados para as amostras
PROFUNDIDADE_DA_SONDA = 3     # passos da sonda de equivalência da verificação 6


@dataclass
class Afericao:
    """O resultado de uma verificação: número, nome e o que aconteceu."""

    numero: int
    nome: str
    ok: bool
    aviso: bool = False
    mensagem: str = ""


def _e_hashable(valor: Any) -> bool:
    try:
        hash(valor)
    except TypeError:
        return False
    return True


def _achatado(estado: Any) -> tuple | None:
    """Os elementos do estado, se ele for tupla/lista de folhas hashable.

    Devolve None para estados compostos (tuplas de tuplas, dicts, objetos) —
    o detector de duplicados só vale para estados "planos".
    """
    if not isinstance(estado, (tuple, list)):
        return None
    if any(isinstance(e, (tuple, list, dict, set)) for e in estado):
        return None
    if not all(_e_hashable(e) for e in estado):
        return None
    return tuple(estado)


def _profundidade_ate_objetivo(
    problema: Any, estado: Any, teto: int = 400,
) -> int | None:
    """Menor número de ações do estado até qualquer objetivo (None se não
    achar dentro do teto) — o parâmetro que a sonda da verificação 6 usa
    para distinguir situações que só parecem iguais."""
    vistos: set[Any] = {estado}
    if problema.objetivo(estado):
        return 0
    fila: deque[tuple[Any, int]] = deque([(estado, 0)])
    while fila:
        atual, fundura = fila.popleft()
        for acao in problema.acoes(atual):
            proximo = problema.transicao(atual, acao)
            if problema.objetivo(proximo):
                return fundura + 1
            if proximo not in vistos:
                vistos.add(proximo)
                fila.append((proximo, fundura + 1))
                if len(vistos) > teto:
                    return None
    return None


def _amostra_alcancavel(
    problema: Any,
) -> tuple[list[Any], int, bool, bool]:
    """Busca em largura do estado inicial.

    Devolve (estados_amostrados, total_de_estados_unicos, bateu_o_teto,
    achou_objetivo). Os estados amostrados são os primeiros
    `LIMITE_DA_AMOSTRA` na ordem da busca — a amostra que alimenta as
    verificações 1, 2, 3, 4 e 6. O total e o achou valem para o espaço
    INTEIRO, não para a amostra. A busca NÃO para no primeiro objetivo:
    é justamente a região depois dele que denuncia o estado que guarda
    caminho (dois caminhos até a mesma situação, estados distintos).
    """
    inicial = problema.estado_inicial
    vistos: set[Any] = {inicial}
    fila: deque[Any] = deque([inicial])
    ordem: list[Any] = [inicial]
    bateu = achou = problema.objetivo(inicial)
    while fila:
        atual = fila.popleft()
        for acao in problema.acoes(atual):
            proximo = problema.transicao(atual, acao)
            if proximo in vistos:
                continue
            vistos.add(proximo)
            ordem.append(proximo)
            if problema.objetivo(proximo):
                achou = True
            if len(vistos) > TETO_DE_NOS:
                bateu = True
                fila.clear()
                break
            fila.append(proximo)
    return ordem[:LIMITE_DA_AMOSTRA], len(vistos), bateu, achou


def _sonda_de_equivalencia(problema: Any, um: Any, outro: Any) -> bool:
    """Os dois estados comportam-se igual na amostra?

    Compara, passo a passo, até `PROFUNDIDADE_DA_SONDA` ações: a lista de
    ações disponíveis, o custo de cada passo e se o objetivo chegou — mais a
    profundidade até o objetivo. Estados distintos que concordam em tudo
    isso são "situações equivalentes" para a busca, e o estado que guarda
    caminho produz exatamente esse padrão.
    """
    atual_um, atual_outro = um, outro
    for _ in range(PROFUNDIDADE_DA_SONDA):
        acoes_um = problema.acoes(atual_um)
        acoes_outro = problema.acoes(atual_outro)
        if acoes_um != acoes_outro:
            return False
        if problema.objetivo(atual_um) != problema.objetivo(atual_outro):
            return False
        if not acoes_um:
            break
        acao = acoes_um[0]
        seguinte_um = problema.transicao(atual_um, acao)
        custo_um = problema.custo(atual_um, acao, seguinte_um)
        seguinte_outro = problema.transicao(atual_outro, acao)
        custo_outro = problema.custo(atual_outro, acao, seguinte_outro)
        if abs(custo_um - custo_outro) > 1e-9:
            return False
        atual_um, atual_outro = seguinte_um, seguinte_outro
    funda_um = _profundidade_ate_objetivo(problema, atual_um)
    funda_outro = _profundidade_ate_objetivo(problema, atual_outro)
    return funda_um == funda_outro


def verificar(problema: Any) -> list[Afericao]:
    """Roda as seis verificações sobre um problema e devolve os relatos."""
    relatos: list[Afericao] = []

    def registrar(numero: int, nome: str, ok: bool, mensagem: str = "",
                  aviso: bool = False) -> None:
        relatos.append(Afericao(numero, nome, ok, aviso, mensagem))

    # 1 — hashable: o estado inicial e uma amostra dos alcançados.
    try:
        amostra, total, bateu, achou = _amostra_alcancavel(problema)
        erro_hash = next(
            (s for s in amostra if not _e_hashable(s)), None)
        if erro_hash is None:
            registrar(1, "estado é hashable", True,
                      f"{total} estados alcançados a partir do inicial")
        else:
            registrar(
                1, "estado é hashable", False,
                f"o estado {erro_hash!r} não tem hash. O que fazer: estados "
                "entram no conjunto de explorados, que é um set — troque "
                "list/dict/set no estado por tuple/frozenset.")
    except TypeError as erro:
        if "unhashable" in str(erro):
            registrar(
                1, "estado é hashable", False,
                f"{erro}. O que fazer: estados entram no conjunto de "
                "explorados, que é um set — troque list/dict/set no estado "
                "por tuple/frozenset.")
        else:
            registrar(
                1, "estado é hashable", False,
                f"a amostragem falhou com TypeError: {erro}. O que fazer: "
                "confira se transicao() devolve sempre o mesmo tipo de "
                "estado.")
        return relatos

    # 2 — transição é função: mesma entrada, mesma saída.
    falhou_2 = ""
    for estado in amostra:
        for acao in problema.acoes(estado)[:5]:
            primeiro = problema.transicao(estado, acao)
            segundo = problema.transicao(estado, acao)
            if primeiro != segundo:
                falhou_2 = (
                    f"aplicar {acao!r} em {estado!r} devolveu {primeiro!r} "
                    "e depois " f"{segundo!r}. O que fazer: a transicao() "
                    "precisa ser função determinística (estado, ação) → "
                    "estado — sorteio, data do dia e valor global mutável "
                    "não podem participar."
                )
                break
        if falhou_2:
            break
    registrar(2, "transição é função", not falhou_2, falhou_2)

    # 3 — acoes estável: mesma lista, na mesma ordem.
    falhou_3 = ""
    for estado in amostra:
        primeira = problema.acoes(estado)
        segunda = problema.acoes(estado)
        if primeira != segunda:
            falhou_3 = (
                f"duas chamadas de acoes({estado!r}) devolveram listas "
                f"diferentes: {primeira!r} e {segunda!r}. O que fazer: "
                "derive a lista de uma estrutura com ordem estável "
                "(tupla, dict ordenado) — a ordem estável é o que torna "
                "duas rodadas comparáveis."
            )
            break
    registrar(3, "ações estáveis na ordem", not falhou_3, falhou_3)

    # 4 — custo positivo ou zero em toda aresta amostrada.
    falhou_4 = ""
    for estado in amostra:
        for acao in problema.acoes(estado)[:5]:
            seguinte = problema.transicao(estado, acao)
            valor = problema.custo(estado, acao, seguinte)
            if valor < 0:
                falhou_4 = (
                    f"a ação {acao!r} em {estado!r} custa {valor}. O que "
                    "fazer: custo negativo quebra as garantias de "
                    "otimalidade (o custo uniforme e o A* assumem custos "
                    "não negativos) — reveja o custo() ou modele o ganho "
                    "dentro do estado."
                )
                break
        if falhou_4:
            break
    registrar(4, "custo é positivo ou zero", not falhou_4, falhou_4)

    # 5 — objetivo alcançável, com teto de nós.
    if bateu and not achou:
        registrar(
            5, "objetivo é alcançável", False,
            f"a busca em largura passou do teto de {TETO_DE_NOS} nós sem "
            "chegar a um objetivo. Pode ser instância grande demais — "
            "reduza a instância para o laboratório. Se acontecer mesmo em "
            "instância pequena, o teste de objetivo pode ser inatingível: "
            "confira se algum estado satisfaz objetivo().",
            aviso=True)
    elif achou:
        registrar(5, "objetivo é alcançável", True,
                  "chegou a um estado objetivo na busca em largura")
    else:
        registrar(
            5, "objetivo é alcançável", False,
            f"{total} estados alcançados e nenhum objetivo. O que fazer: "
            "o teste de objetivo é inatingível — formulação vazia. Comece "
            "por ele: é o teste de objetivo que define o que precisa "
            "estar no estado, e o resto dos componentes sai dele.")

    # 6 — o estado que guarda o caminho (AVISO, não falha).
    avisos_6: list[str] = []
    canonicos: dict[tuple, Any] = {}
    for estado in amostra:
        chato = _achatado(estado)
        if chato is None:
            continue
        padrao = tuple(sorted(chato))
        outro = canonicos.setdefault(padrao, estado)
        if outro != estado and tuple(chato) != tuple(padrao):
            avisos_6.append(
                f"{estado!r} e {outro!r} guardam os MESMOS elementos em "
                "ordens (ou repetições) diferentes. O que fazer: o estado "
                "deve ser a situação, canônica — ordene ou use frozenset, "
                "e tire do estado o que já se sabe de outro jeito.")
            break
    # Amostra de pares: estados distintos, mesma lista de ações, mesmo
    # comportamento na sonda — situações equivalentes com estados distintos.
    if not avisos_6:
        por_grupo: dict[int, dict[tuple, list[Any]]] = {}
        for fundura, estado in enumerate(amostra):
            chave = tuple(problema.acoes(estado))
            por_grupo.setdefault(fundura, {}).setdefault(chave, []).append(estado)
        testados = 0
        for grupos in por_grupo.values():
            for estados in grupos.values():
                for i in range(len(estados)):
                    for j in range(i + 1, len(estados)):
                        if testados >= 200:
                            break
                        testados += 1
                        um, outro = estados[i], estados[j]
                        if _sonda_de_equivalencia(problema, um, outro):
                            avisos_6.append(
                                f"os estados {um!r} e {outro!r} são "
                                "distintos e se comportam igual na amostra "
                                "(mesmas ações, mesmos custos, mesmo alcance "
                                "do objetivo). O que fazer: provavelmente o "
                                "estado guarda a história do caminho — "
                                "guarde só a situação; o caminho já fica "
                                "guardado nos nós da busca.")
                            break
                    if avisos_6:
                        break
                if avisos_6 or testados >= 200:
                    break
            if avisos_6 or testados >= 200:
                break
    if avisos_6:
        registrar(6, "estado não guarda o caminho", False, avisos_6[0],
                  aviso=True)
    else:
        registrar(
            6, "estado não guarda o caminho", True,
            "nenhuma situação equivalente com estados distintos na amostra")

    return relatos


# --------------------------------------------------------------------------
# Linha de comando
# --------------------------------------------------------------------------

def carregar_problema(especificacao: str) -> Any:
    """Carrega o problema de "arquivo.py:ATRIBUTO" (ou "arquivo.py" só).

    Sem o atributo, procura UM candidato: instância ou classe que tenha os
    cinco membros do protocolo. Mais de um candidato é erro — aponte o
    atributo.
    """
    # O separador do atributo é o ÚLTIMO dois-pontos, e o que vem depois é
    # um identificador — assim o "G:" do Windows na frente do caminho não
    # engana o corte (e um caminho sem atributo continua inteiro).
    caminho, marcador, atributo = especificacao.rpartition(":")
    if (not marcador or not atributo.isidentifier()
            or any(s in atributo for s in "/\\.")):
        caminho, atributo = especificacao, ""
    caminho_arquivo = Path(caminho)
    if not caminho_arquivo.is_file():
        raise FileNotFoundError(f"não encontrei o arquivo {caminho_arquivo}")
    especificacao_modulo = importlib.util.spec_from_file_location(
        caminho_arquivo.stem, caminho_arquivo)
    modulo = importlib.util.module_from_spec(especificacao_modulo)
    # dataclasses com anotações adiadas consultam sys.modules durante o
    # exec_module — sem o registro, o módulo do aluno quebra aqui dentro.
    sys.modules.setdefault(caminho_arquivo.stem, modulo)
    especificacao_modulo.loader.exec_module(modulo)  # type: ignore[union-attr]
    if atributo:
        return getattr(modulo, atributo)
    membros = ("estado_inicial", "acoes", "transicao", "objetivo", "custo")
    instancias: list[tuple[str, Any]] = []
    classes: list[tuple[str, Any]] = []
    for nome, valor in vars(modulo).items():
        if nome.startswith("_") or not all(hasattr(valor, m) for m in membros):
            continue
        if isinstance(valor, type):
            classes.append((nome, valor))
        else:
            instancias.append((nome, valor))
    if len(instancias) == 1:
        return instancias[0][1]
    if not instancias and len(classes) == 1:
        return classes[0][1]
    nomes = [n for n, _ in instancias] + [n for n, _ in classes]
    raise ValueError(
        f"não sei qual problema carregar de {caminho_arquivo.name} "
        f"(candidatos: {', '.join(nomes) or 'nenhum'}) — aponte o atributo: "
        "arquivo.py:NOME_DO_PROBLEMA")


def _catalogo() -> list[tuple[str, Any]]:
    pasta = str(pasta_do_comum())
    if pasta not in sys.path:
        sys.path.insert(0, pasta)
    from problemas import conformidade, consultas, diagnostico  # noqa: E402
    pares: list[tuple[str, Any]] = []
    for modulo in (diagnostico, consultas, conformidade):
        nome = modulo.__name__.rsplit(".", 1)[-1]
        pares.append((f"{nome}.PEQUENA", modulo.PEQUENA))
        pares.append((f"{nome}.MAIOR", modulo.MAIOR))
    return pares


def _marcador(afericao: Afericao) -> str:
    if afericao.ok:
        return "✅"
    return "⚠️ " if afericao.aviso else "❌"


def _relatar(nome_problema: str, afericoes: list[Afericao]) -> bool:
    print(f"\n— {nome_problema}")
    for a in afericoes:
        linha = f"  {a.numero}. {a.nome} {_marcador(a)}"
        print(linha)
        if not a.ok:
            print(f"     {a.mensagem}")
    vermelhas = [a for a in afericoes if not a.ok and not a.aviso]
    amarelas = [a for a in afericoes if a.aviso and not a.ok]
    resumo = (
        f"  resumo: {len(afericoes) - len(vermelhas) - len(amarelas)} ✅ · "
        f"{len(amarelas)} ⚠️ · {len(vermelhas)} ❌"
    )
    print(resumo)
    return not vermelhas


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    print("verificar-formulacao — teste de sanidade da formulação de busca")
    if argv:
        alvos = []
        for especificacao in argv:
            problema = carregar_problema(especificacao)
            alvos.append((especificacao, problema))
    else:
        alvos = _catalogo()
        print("(sem argumentos: rodando sobre o catálogo — aponte o seu "
              "com arquivo.py:ATRIBUTO)")
    tudo_verde = True
    for nome, problema in alvos:
        tudo_verde = _relatar(nome, verificar(problema)) and tudo_verde
    if tudo_verde:
        print("\nSeis verificações verdes — a formulação pode ir para o "
              "agent-spec.md e para o lab-04.")
        return 0
    print("\nHá vermelho acima — cada mensagem diz o que fazer. "
          "Conserte e rode de novo.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
