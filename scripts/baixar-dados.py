"""Download dos dados de manutenção (dataset AI4I 2020) com cascata de fallback.

Tenta quatro fontes, parando na primeira que funcionar:

1. URL oficial do UCI Machine Learning Repository (arquivo .zip).
2. Espelho público no GitHub (arquivo .csv idêntico ao oficial).
3. Amostra versionada no repositório (200 linhas em data/amostra/).
4. Gerador sintético determinístico (10.000 linhas, mesma estrutura).

O laboratório precisa funcionar mesmo com a internet fora ou com as
URLs mortas — por isso o último recurso nunca falha.

Uso:
    python scripts/baixar-dados.py             # baixa se ainda não existir
    python scripts/baixar-dados.py --forcar    # ignora o que já existe e refaz

Saída: data/raw/ai4i2020.csv + data/raw/PROVENIENCIA.txt
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import sys
import urllib.error
import urllib.request
import zipfile
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_RAW = RAIZ / "data" / "raw"
PASTA_AMOSTRA = RAIZ / "data" / "amostra"
ARQUIVO_CSV = "ai4i2020.csv"

# Fonte 1 — oficial: repositório UCI (ID 601). Testada e funcionando em 25/08/2026.
URL_UCI = "https://archive.ics.uci.edu/static/public/601/ai4i+2020+predictive+maintenance+dataset.zip"
# Fonte 2 — espelho: cópia pública byte a byte idêntica à oficial (mesmo SHA-256,
# conferido em 25/08/2026). Existe para o caso de o UCI sair do ar.
URL_ESPELHO = (
    "https://raw.githubusercontent.com/SamyamoyRakshit/"
    "AI4I-2020-Predictive-Maintenance-Dataset__Linear-Regression/main/ai4i2020.csv"
)

COLUNAS = [
    "UDI",
    "Product ID",
    "Type",
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "Machine failure",
    "TWF",
    "HDF",
    "PWF",
    "OSF",
    "RNF",
]
LINHAS_COMPLETAS = 10_000
LINHAS_AMOSTRA = 200
LICENCA = "CC BY 4.0 (dataset original) — https://creativecommons.org/licenses/by/4.0/"
CITACAO = (
    "Matzka, S. (2020). AI4I 2020 Predictive Maintenance Dataset. "
    "UCI Machine Learning Repository (ID 601). https://archive.ics.uci.edu/dataset/601"
)


def registrar(mensagem: str) -> None:
    """Imprime uma linha de progresso com prefixo fixo."""
    print(f"[baixar-dados] {mensagem}")


def baixar(url: str, tempo_maximo: int = 120) -> bytes | None:
    """Baixa uma URL e devolve o conteúdo, ou None se a tentativa falhou.

    Nunca lança exceção: falhar é esperado (é o que alimenta a cascata).
    """
    try:
        requisicao = urllib.request.Request(url, headers={"User-Agent": "ams-d1/1.0"})
        with urllib.request.urlopen(requisicao, timeout=tempo_maximo) as resposta:
            return resposta.read()
    except (urllib.error.URLError, TimeoutError, OSError, zipfile.BadZipFile) as erro:
        registrar(f"falhou: {url} ({erro})")
        return None


def extrair_csv_do_zip(conteudo_zip: bytes) -> bytes | None:
    """Localiza o ai4i2020.csv dentro do .zip do UCI e devolve seu conteúdo."""
    try:
        with zipfile.ZipFile(io.BytesIO(conteudo_zip)) as arquivo_zip:
            nome = next(n for n in arquivo_zip.namelist() if n.endswith(".csv"))
            return arquivo_zip.read(nome)
    except (StopIteration, zipfile.BadZipFile, OSError) as erro:
        registrar(f"falhou: zip recebido sem CSV válido ({erro})")
        return None


def validar_csv(caminho: Path, linhas_esperadas: int) -> tuple[bool, str]:
    """Confere colunas (nomes e ordem) e contagem de linhas do CSV.

    Lê com utf-8-sig porque o arquivo oficial do UCI vem com BOM UTF-8 —
    sem isso, a primeira coluna apareceria como '\\ufeffUDI'.
    """
    with open(caminho, encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.reader(arquivo)
        try:
            cabecalho = next(leitor)
        except StopIteration:
            return False, "arquivo vazio"
        if cabecalho != COLUNAS:
            return False, f"colunas não conferem: {cabecalho[:3]}..."
        total = sum(1 for _ in leitor)
    if total != linhas_esperadas:
        return False, f"{total} linhas de dados (esperado: {linhas_esperadas})"
    return True, f"{total} linhas, {len(cabecalho)} colunas"


def gravar(conteudo: bytes, origem: dict[str, str]) -> Path:
    """Grava o CSV final e o arquivo de proveniência ao lado dele."""
    PASTA_RAW.mkdir(parents=True, exist_ok=True)
    destino = PASTA_RAW / ARQUIVO_CSV
    destino.write_bytes(conteudo)

    # MD5 seria suficiente para conferir integridade; SHA-256 porque é o
    # padrão que um aluno encontra em qualquer contexto de dados hoje.
    hash_sha256 = hashlib.sha256(conteudo).hexdigest()
    agora = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    linhas = [
        "PROVENIÊNCIA DOS DADOS — AMS (Disciplina 1)",
        "=" * 52,
        f"Gerado em:      {agora}",
        f"Arquivo:        {ARQUIVO_CSV}",
        f"Fonte usada:    {origem['nome']}",
        f"URL:            {origem.get('url', '—')}",
        f"SHA-256:        {hash_sha256}",
        f"Licença:        {LICENCA}",
        f"Citação:        {CITACAO}",
    ]
    if origem.get("aviso"):
        linhas += ["", f"AVISO: {origem['aviso']}"]
    (PASTA_RAW / "PROVENIENCIA.txt").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return destino


def fonte_uci() -> tuple[bytes, dict[str, str]] | None:
    """Fonte 1: .zip oficial do UCI Machine Learning Repository."""
    registrar("tentando fonte 1/4: UCI Machine Learning Repository (oficial)...")
    zip_bruto = baixar(URL_UCI)
    if zip_bruto is None:
        return None
    conteudo = extrair_csv_do_zip(zip_bruto)
    if conteudo is None:
        return None
    return conteudo, {"nome": "UCI ML Repository (oficial)", "url": URL_UCI}


def fonte_espelho() -> tuple[bytes, dict[str, str]] | None:
    """Fonte 2: espelho público com o mesmo CSV do oficial."""
    registrar("tentando fonte 2/4: espelho público no GitHub...")
    conteudo = baixar(URL_ESPELHO)
    if conteudo is None:
        return None
    return conteudo, {"nome": "Espelho público (GitHub)", "url": URL_ESPELHO}


def fonte_amostra() -> tuple[bytes, dict[str, str], int] | None:
    """Fonte 3: amostra de 200 linhas versionada junto com o código.

    Serve para o repositório funcionar sem nenhum download — suficiente
    para desenvolver, não para a análise completa.
    """
    registrar("tentando fonte 3/4: amostra versionada em data/amostra/...")
    caminho = PASTA_AMOSTRA / ARQUIVO_CSV
    if not caminho.exists():
        registrar(f"falhou: {caminho} não existe")
        return None
    try:
        conteudo = caminho.read_bytes()
    except OSError as erro:
        registrar(f"falhou: não consegui ler a amostra ({erro})")
        return None
    return conteudo, {"nome": "Amostra versionada no repositório (200 linhas)", "url": "—"}, (
        LINHAS_AMOSTRA
    )


def fonte_sintetica() -> tuple[bytes, dict[str, str], int]:
    """Fonte 4: gera 10.000 linhas com numpy, sempre idênticas (semente 42).

    As regras de falha são aproximações das descritas no artigo do dataset:
    HDF por temperatura/rotação, PWF por potência fora da faixa, TWF por
    desgaste, OSF por desgaste + torque, RNF aleatória. Incluímos também
    ~0,3% de 'falha sem modo' para imitar a imperfeição de dados reais
    (que a exploração do notebook investiga).
    """
    registrar("tentando fonte 4/4: gerador sintético determinístico...")
    try:
        import numpy as np
    except ImportError:
        encerrar_com_erro(
            "sem internet e sem numpy instalado — instale os pacotes primeiro "
            "(python -m pip install -r requirements.txt) e rode de novo"
        )

    rng = np.random.default_rng(42)
    total = LINHAS_COMPLETAS

    tipo = rng.choice(np.array(["L", "M", "H"]), size=total, p=[0.60, 0.30, 0.10])
    udi = np.arange(1, total + 1)

    temperatura_ar = np.clip(rng.normal(299.0, 1.6, total), 295.0, 304.5)
    # O clip inferior (7,5 K) fica ABAIXO do limiar de HDF (8,6 K): sem isso,
    # nenhuma máquina teria diferença pequena o bastante para o modo HDF.
    delta = np.clip(rng.normal(10.0, 0.8, total), 7.5, 11.5)
    temperatura_processo = temperatura_ar + delta

    rotacao = np.clip(rng.normal(1538.0, 180.0, total), 1168, 2886)
    # Potência ~6,4 kW em média: os 1,15 kW de desvio criam a cauda que gera PWF
    # em ~0,9% das máquinas (no dataset original, 0,95%).
    potencia_kw = rng.normal(6.4, 1.15, total)
    omega = rotacao * (2 * np.pi / 60)  # rpm → rad/s
    torque = np.clip(potencia_kw * 1000 / omega, 3.0, 80.0)

    desgaste = rng.uniform(5, 240, total)

    hdf = ((temperatura_processo - temperatura_ar) < 8.6) & (rotacao < 1380)
    pwf = (potencia_kw < 3.5) | (potencia_kw > 9.5)
    twf = (desgaste >= 200) & (rng.random(total) < 0.05)
    # OSF calibrado por tipo de produto: reproduz ~0,5% do total sem
    # dominar as demais falhas (no dataset original, ~1% com sobreposição).
    osf = (
        ((tipo == "L") & (desgaste >= 218) & (torque >= 50))
        | ((tipo == "M") & (desgaste >= 230) & (torque >= 52))
        | ((tipo == "H") & (desgaste >= 240) & (torque >= 54))
    )
    rnf = rng.random(total) < 0.0019
    falha = twf | hdf | pwf | osf | rnf

    # Falhas "sem modo": imita os 27 registros do dataset real em que a coluna
    # Machine failure vale 1 sem nenhum modo marcado — a lição de qualidade
    # de dados da pergunta 6 do notebook precisa existir também aqui.
    falha_sem_modo = (~falha) & (rng.random(total) < 0.0028)
    falha = falha | falha_sem_modo

    numero_produto = rng.integers(10000, 99999, total)
    produto = np.array([f"{t}{n}" for t, n in zip(tipo, numero_produto, strict=True)])

    saida = io.StringIO()
    escritor = csv.writer(saida)
    escritor.writerow(COLUNAS)
    for i in range(total):
        escritor.writerow(
            [
                udi[i],
                produto[i],
                tipo[i],
                f"{temperatura_ar[i]:.1f}",
                f"{temperatura_processo[i]:.1f}",
                int(rotacao[i]),
                f"{torque[i]:.1f}",
                int(desgaste[i]),
                int(falha[i]),
                int(twf[i]),
                int(hdf[i]),
                int(pwf[i]),
                int(osf[i]),
                int(rnf[i]),
            ]
        )

    conteudo = saida.getvalue().encode("utf-8")
    taxa = falha.mean() * 100
    origem = {
        "nome": "GERADOR SINTÉTICO (dados artificiais — NÃO é o dataset real)",
        "url": "—",
        "aviso": (
            "Estas linhas foram geradas por numpy com semente 42 porque nenhuma fonte "
            "real respondeu. A estrutura e as distribuições imitam o AI4I 2020, mas "
            "números publicados com estes dados não valem — refaça o download com "
            "--forcar quando houver internet."
        ),
    }
    registrar(f"geradas {total} linhas sintéticas com taxa de falha {taxa:.2f}%")
    return conteudo, origem, total


def encerrar_com_erro(mensagem: str) -> None:
    """Imprime a falha final e encerra com código de erro."""
    registrar(f"ERRO: {mensagem}")
    sys.exit(1)


def csv_atual_valido() -> bool:
    """Confere se já existe um CSV válido em data/raw (idempotência)."""
    caminho = PASTA_RAW / ARQUIVO_CSV
    if not caminho.exists():
        return False
    valido, _ = validar_csv(caminho, LINHAS_COMPLETAS)
    if not valido:
        # Amostra de 200 linhas baixada antes também conta como "existe e é válido".
        valido, _ = validar_csv(caminho, LINHAS_AMOSTRA)
    return valido


def principal() -> int:
    """Executa a cascata e grava o resultado final."""
    parser = argparse.ArgumentParser(
        description="Baixa o dataset AI4I 2020 de manutenção (com fallback)."
    )
    parser.add_argument(
        "--forcar",
        action="store_true",
        help="refaz o download mesmo se data/raw já tiver um arquivo válido",
    )
    argumentos = parser.parse_args()

    if argumentos.forcar:
        registrar("modo --forcar: ignorando arquivos existentes")
    elif csv_atual_valido():
        registrar(f"{PASTA_RAW / ARQUIVO_CSV} já existe e é válido — nada a fazer")
        registrar("(use --forcar para baixar de novo)")
        return 0

    resultado: tuple[bytes, dict[str, str]] | None = None
    linhas_esperadas = LINHAS_COMPLETAS

    tentativas: list[str] = []

    for fonte in (fonte_uci, fonte_espelho):
        tentativa = fonte()
        if tentativa is None:
            tentativas.append(fonte.__doc__.split(":")[0] if fonte.__doc__ else fonte.__name__)
            continue
        resultado = tentativa
        break

    if resultado is None:
        amostra = fonte_amostra()
        if amostra is not None:
            resultado = (amostra[0], amostra[1])
            linhas_esperadas = amostra[2]
        else:
            sintetico = fonte_sintetica()
            resultado = (sintetico[0], sintetico[1])
            linhas_esperadas = sintetico[2]

    conteudo, origem = resultado

    caminho = gravar(conteudo, origem)
    valido, detalhe = validar_csv(caminho, linhas_esperadas)
    if not valido:
        encerrar_com_erro(f"o arquivo gravado não passou na validação: {detalhe}")

    registrar(f"OK: {caminho} ({detalhe})")
    registrar(f"fonte usada: {origem['nome']}")
    if tentativas:
        registrar(f"{len(tentativas)} fonte(s) anterior(es) falharam (motivos linha a linha acima)")
    registrar("proveniência gravada em data/raw/PROVENIENCIA.txt")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
