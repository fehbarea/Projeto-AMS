"""Testes do Laboratório 06 — a prova de que o baseline e a medição estão de pé.

Como usar (da pasta do laboratório):
    python -m pytest teste.py -q

Quatro famílias:

  1. AS REGRAS — cada condição de `decidir` dispara no caso que a define,
     e a ORDEM das condições importa (a primeira que casa decide);
  2. O ESTADO INTERNO — falhas contam dentro da janela e envelhecem fora
     dela; sem desfecho, o estado não muda;
  3. O GABARITO DA RESERVA — as 30 decisões do `esqueleto.py` sobre
     `casos-de-reserva.csv`, caso a caso, e a métrica final: 25/30. Os
     cinco erros são de propósito: é a matéria-prima da análise escrita;
  4. A TROCA — o mesmo medidor rodando sobre OUTRO arquivo de casos, sem
     tocar em código: a troca do conjunto é uma linha (slide 29).

Se o seu domínio é outro, as famílias 1 e 2 é que continuam valendo —
adapte-as aos SEUS limiares. A 3 é o gabarito do conjunto de reserva.
"""

from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

from medir import medir

_AQUI = Path(__file__).resolve().parent

_spec = importlib.util.spec_from_file_location("esqueleto", _AQUI / "esqueleto.py")
esqueleto = importlib.util.module_from_spec(_spec)
sys.modules["esqueleto"] = esqueleto
_spec.loader.exec_module(esqueleto)  # type: ignore[union-attr]

# O gabarito das 30 decisões sobre o conjunto de reserva, na ordem do
# arquivo (cronológica). Erros de propósito: C07 e C08 (falha intermitente
# que as leituras não veem), C10 (excesso de cautela da família), C11 e
# C22 (os dois atípicos, onde parar era exagero).
ESPERADO = {
    "C01": "seguir_operando", "C02": "parar_para_manutencao",
    "C03": "parar_para_manutencao", "C04": "seguir_operando",
    "C05": "seguir_operando", "C06": "seguir_operando",
    "C07": "seguir_operando", "C08": "seguir_operando",
    "C09": "inspecionar_antes_de_operar", "C10": "inspecionar_antes_de_operar",
    "C11": "parar_para_manutencao", "C12": "seguir_operando",
    "C13": "parar_para_manutencao", "C14": "seguir_operando",
    "C15": "parar_para_manutencao", "C16": "seguir_operando",
    "C17": "seguir_operando", "C18": "inspecionar_antes_de_operar",
    "C19": "inspecionar_antes_de_operar", "C20": "seguir_operando",
    "C21": "parar_para_manutencao", "C22": "parar_para_manutencao",
    "C23": "seguir_operando", "C24": "seguir_operando",
    "C25": "seguir_operando", "C26": "seguir_operando",
    "C27": "parar_para_manutencao", "C28": "parar_para_manutencao",
    "C29": "seguir_operando", "C30": "seguir_operando",
}
ERROS_ESPERADOS = ["C07", "C08", "C10", "C11", "C22"]


def _registro(**mudancas) -> dict:
    base = {"data": "2026-03-02", "tipo_maquina": "TORNO",
            "idade_meses": 60, "temperatura_c": 62.0,
            "vibracao_mm_s": 3.0, "horas_desde_manutencao": 100.0,
            "falhou_depois": 0}
    base.update(mudancas)
    return base


# --- 1. as regras -----------------------------------------------------------

def test_condicao_reativa_para_com_vibracao_alta():
    estado = esqueleto.EstadoDaFrota()
    decisao = esqueleto.decidir(_registro(vibracao_mm_s=7.5), estado)
    assert decisao == "parar_para_manutencao"


def test_condicao_reativa_para_com_temperatura_alta():
    estado = esqueleto.EstadoDaFrota()
    decisao = esqueleto.decidir(_registro(temperatura_c=79.0), estado)
    assert decisao == "parar_para_manutencao"


def test_estado_interno_inspeciona_apos_duas_falhas_da_familia():
    estado = esqueleto.EstadoDaFrota()
    registro = _registro(data="2026-03-02", falhou_depois=1)
    estado.registrar_desfecho(registro)          # primeira falha
    assert esqueleto.decidir(_registro(), estado) == "seguir_operando"
    estado.registrar_desfecho(_registro(data="2026-03-03", falhou_depois=1))
    decisao = esqueleto.decidir(_registro(data="2026-03-04"), estado)
    assert decisao == "inspecionar_antes_de_operar"


def test_a_ordem_das_condicoes_importa():
    estado = esqueleto.EstadoDaFrota()
    for dia in ("2026-03-02", "2026-03-03"):
        estado.registrar_desfecho(
            _registro(data=dia, falhou_depois=1))
    tudo_alto = _registro(data="2026-03-04", vibracao_mm_s=9.0,
                          temperatura_c=85.0)
    assert esqueleto.decidir(tudo_alto, estado) == "parar_para_manutencao", (
        "com leitura crítica, PARA — a condição reativa vem primeiro")


def test_familia_diferente_nao_hera_as_falhas():
    estado = esqueleto.EstadoDaFrota()
    estado.registrar_desfecho(
        _registro(tipo_maquina="PRENSA", data="2026-03-02", falhou_depois=1))
    estado.registrar_desfecho(
        _registro(tipo_maquina="PRENSA", data="2026-03-03", falhou_depois=1))
    decisao = esqueleto.decidir(
        _registro(tipo_maquina="ROBOT", data="2026-03-04"), estado)
    assert decisao == "seguir_operando"


# --- 2. o estado interno e a janela -----------------------------------------

def test_falha_envelhece_fora_da_janela():
    estado = esqueleto.EstadoDaFrota()
    estado.registrar_desfecho(
        _registro(data="2026-03-02", falhou_depois=1))
    # oito dias depois, a falha já saiu da janela de 7 dias
    decisao = esqueleto.decidir(
        _registro(data="2026-03-10", falhou_depois=1), estado)
    assert decisao == "seguir_operando"


def test_sem_desfecho_o_estado_nao_muda():
    estado = esqueleto.EstadoDaFrota()
    estado.registrar_desfecho(_registro(data="2026-03-02", falhou_depois=0))
    assert estado.falhas_recentes("TORNO") == 0


# --- 3. o gabarito da reserva ------------------------------------------------

def test_as_trinta_decisoes_batem_com_o_gabarito():
    casos = esqueleto.carregar_casos(esqueleto.CAMINHO_DOS_CASOS)
    estado = esqueleto.EstadoDaFrota()
    divergentes = []
    for registro in casos:
        decisao = esqueleto.decidir(registro, estado)
        if decisao != ESPERADO[registro["id_caso"]]:
            divergentes.append((registro["id_caso"], decisao))
        estado.registrar_desfecho(registro)
    assert not divergentes, (
        f"decisões divergentes do gabarito: {divergentes}. Ou as regras do "
        "esqueleto mudaram (aí o gabarito deste teste precisa ser regerado "
        "e o número da análise, atualizado), ou há defeito nas regras.")


def test_a_metrica_final_da_reserva_e_25_de_30():
    resultado = medir(esqueleto.CAMINHO_DOS_CASOS)
    assert resultado["total"] == 30
    assert (resultado["acertos"], round(resultado["valor"], 4)) == (25, 0.8333)
    assert [e["id_caso"] for e in resultado["erros"]] == ERROS_ESPERADOS, (
        "os cinco erros são a matéria-prima da análise escrita — mudaram, "
        "muda a análise")


# --- 4. a troca do conjunto é uma linha ---------------------------------------

def test_o_medidor_roda_sobre_outro_arquivo_sem_tocar_em_codigo(tmp_path):
    casos_novos = tmp_path / "meus_casos.csv"
    with casos_novos.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["id_caso", "data", "tipo_maquina", "idade_meses",
                           "temperatura_c", "vibracao_mm_s",
                           "horas_desde_manutencao", "acao_correta",
                           "falhou_depois"])
        escritor.writerow(["M01", "2026-04-01", "TORNO", 60, 82.0, 3.0,
                           100.0, "parar_para_manutencao", 1])
        escritor.writerow(["M02", "2026-04-02", "ROBOT", 40, 60.0, 2.0,
                           120.0, "seguir_operando", 0])
    resultado = medir(casos_novos)
    assert resultado["total"] == 2
    assert resultado["acertos"] == 2
