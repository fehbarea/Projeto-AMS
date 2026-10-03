#!/usr/bin/env bash
# ==================================================================
# Configuração do ambiente do AMS — Disciplina 1
# Curso de Especialização em Desenvolvimento de Agentes Inteligentes (UTFPR)
#
# O que este script faz (pode rodar quantas vezes quiser):
#   1. Confere se o Python 3.12+ está instalado
#   2. Cria o ambiente virtual .venv
#   3. Instala os pacotes do requirements.txt e o pacote do projeto
#   4. Prepara o arquivo .env (a partir do .env.example)
#   5. Roda a verificação final de ambiente
#
# Uso:  bash scripts/setup-unix.sh
# (Linux e macOS; funciona também no Git Bash do Windows para teste)
# ==================================================================
set -euo pipefail

RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$RAIZ"

titulo() {
    echo ""
    echo "=== $1 ==="
}

# Guarda do B04 §3.2: arquivo que deveria ter vindo no D1-00. Se falta, o
# problema é do PACOTE (descompactação incompleta), não da máquina — não há
# nada que o aluno possa "resolver" localmente.
exigir_arquivo() {
    local faltando=()
    for caminho in "$@"; do
        [ -f "$caminho" ] || faltando+=("$caminho")
    done
    if [ "${#faltando[@]}" -gt 0 ]; then
        echo "ERRO: faltam arquivos neste pacote (${faltando[*]})."
        echo ""
        echo "Baixe o D1-00-antes-de-comecar.zip de novo pelo Moodle e descompacte"
        echo "TUDO — algumas ferramentas de descompactação deixam arquivos para trás."
        echo "Se o problema persistir, escreva para a coordenação."
        exit 1
    fi
}

# Tradução dos erros de rede/disco do pip (paridade com o setup-windows.ps1):
# o texto cru do pip é indecifrável para quem nunca viu um SSL Error.
traduzir_erro_pip() {
    local texto="$1"
    if echo "$texto" | grep -qi "proxy\|ssl\|timed out\|temporary failure\|getaddrinfo\|connection\|network"; then
        echo "SEM INTERNET OU PROXY BLOQUEANDO: confira o Wi-Fi/rede. Em máquina de"
        echo "empresa, o firewall costuma bloquear o PyPI — peça liberação à TI."
        echo "O que o pip relatou (últimas linhas):"
        echo "$texto" | tail -n 6
        return
    fi
    if echo "$texto" | grep -qi "no space left\|disk"; then
        echo "SEM ESPAÇO EM DISCO: libere pelo menos 2 GB e rode este script de novo."
        return
    fi
    echo "A instalação falhou. Últimas linhas do pip para anexar ao pedido de ajuda:"
    echo "$texto" | tail -n 6
}

# --- 1. Python 3.12+ ------------------------------------------------
titulo "1 de 5: procurando Python 3.12 ou superior"
PYTHON=""
for candidato in python3.14 python3.13 python3.12 python3 python; do
    if command -v "$candidato" >/dev/null 2>&1; then
        # >/dev/null 2>&1: o alias falso da Microsoft Store (que ocupa o nome
        # 'python' no Windows) imprime um banner no stdout em vez de rodar.
        if "$candidato" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
            PYTHON="$candidato"
            break
        fi
    fi
done

# Git Bash no Windows: o 'python' do PATH costuma ser só o alias da Store,
# mas o launcher 'py' (instalado junto com o Python do python.org) funciona
# no Git Bash — tentar por ele antes de desistir.
if [ -z "$PYTHON" ] && command -v py >/dev/null 2>&1; then
    for marca in "-3.14" "-3.13" "-3.12" ""; do
        if py $marca -c 'import sys; sys.exit(0 if sys.version_info >= (3, 12) else 1)' >/dev/null 2>&1; then
            PYTHON="py $marca"
            break
        fi
    done
fi

if [ -z "$PYTHON" ]; then
    echo "ERRO: não encontrei Python 3.12 ou superior nesta máquina."
    echo ""
    echo "O que fazer:"
    echo "  1. Instale o Python 3.12+ (macOS: https://www.python.org/downloads/ ou 'brew install python')"
    echo "     (Linux: use o gerenciador de pacotes da sua distribuição)"
    echo "  2. Rode este script de novo"
    exit 1
fi
# o comando pode ter argumento (ex.: 'py -3.'): expandir como lista de palavras
read -ra COMANDO_PYTHON <<< "$PYTHON"
echo "Python encontrado: $("${COMANDO_PYTHON[@]}" --version) (comando: $PYTHON)"

# --- 2. Ambiente virtual ---------------------------------------------
titulo "2 de 5: ambiente virtual (.venv)"
if [ -f ".venv/bin/python" ] || [ -f ".venv/Scripts/python.exe" ]; then
    echo "O ambiente virtual já existe — reutilizando (nada recriado)."
else
    echo "Criando ambiente virtual em .venv (leva ~30 segundos)..."
    codigo_venv=0
    saida_venv="$("${COMANDO_PYTHON[@]}" -m venv .venv 2>&1)" || codigo_venv=$?
    if [ "$codigo_venv" -ne 0 ]; then
        echo "ERRO: não consegui criar o ambiente virtual."
        if echo "$saida_venv" | grep -qi "permission denied\|read-only\|operation not permitted"; then
            echo ""
            echo "A PASTA NÃO PERMITE ESCRITA. Causa comum: o projeto foi executado de"
            echo "dentro do .zip (aberto no navegador) ou extraído em local protegido."
            echo "O que fazer: extraia o projeto para uma pasta comum da sua pasta"
            echo "de usuário e rode este script de novo."
        else
            echo ""
            echo "Saída do comando para anexar ao pedido de ajuda:"
            echo "$saida_venv" | tail -n 6
            echo "Feche o terminal, abra de novo e tente outra vez; se persistir,"
            echo "anexe este erro e escreva para a coordenação antes da aula."
        fi
        exit 1
    fi
    echo "Ambiente virtual criado."
fi
# Linux/macOS usam .venv/bin; no Git Bash do Windows a venv criada pelo
# python.exe usa .venv/Scripts — os dois casos levam ao mesmo python da venv.
if [ -x ".venv/bin/python" ]; then
    PYTHON_VENV=".venv/bin/python"
else
    PYTHON_VENV=".venv/Scripts/python.exe"
fi

# --- 3. Pacotes -------------------------------------------------------
titulo "3 de 5: instalando pacotes do requirements.txt"
# requirements.txt: o passo inteiro depende dele; pyproject.toml + src/ams/
# __init__.py: o 'pip install -e .' que dá o 'import ams' depende dos dois.
exigir_arquivo "requirements.txt" "pyproject.toml" "src/ams/__init__.py"
echo "Baixando numpy, pandas e cia. — na primeira vez são uns 2 minutos..."

codigo=0
saida="$("$PYTHON_VENV" -m pip install --upgrade pip --quiet 2>&1)" || codigo=$?
if [ "$codigo" -ne 0 ]; then
    echo "ERRO: não consegui atualizar o pip."
    traduzir_erro_pip "$saida"
    exit 1
fi

codigo=0
saida="$("$PYTHON_VENV" -m pip install -r requirements.txt 2>&1)" || codigo=$?
if [ "$codigo" -ne 0 ]; then
    echo "ERRO: a instalação dos pacotes falhou."
    traduzir_erro_pip "$saida"
    exit 1
fi
echo "Pacotes instalados (ou já estavam instalados)."

# O próprio projeto é um pacote (pyproject.toml): instalá-lo em modo editável
# deixa 'import ams' funcionar em qualquer lugar da venv. --no-deps porque as
# dependências já vieram do requirements.txt (e sem rede o pip não resolveria).
codigo=0
saida="$("$PYTHON_VENV" -m pip install -e . --no-deps --quiet 2>&1)" || codigo=$?
if [ "$codigo" -eq 0 ]; then
    echo "Pacote do projeto instalado em modo editável (import ams)."
else
    # Plano B (equivalente ao atalho do setup-windows.ps1): registrar a pasta
    # src no caminho de pacotes da venv via .pth — mesmo efeito prático.
    site_packages="$("$PYTHON_VENV" -c 'import sysconfig; print(sysconfig.get_paths()["purelib"])')"
    if printf '%s\n' "$RAIZ/src" > "$site_packages/_ams_src.pth" 2>/dev/null; then
        echo "Aviso: o pip não conseguiu instalar o pacote editável (motivo no log acima)."
        echo "Registrei um atalho equivalente: import ams funciona normalmente."
    else
        echo "Aviso: não consegui instalar o pacote do projeto (import ams pode falhar)."
        echo "Últimas linhas do pip para anexar ao pedido de ajuda:"
        echo "$saida" | tail -n 4
    fi
fi

# --- 4. Arquivo .env ---------------------------------------------------
titulo "4 de 5: arquivo de configuração (.env)"
# O .env.example só é exigido quando o .env ainda não existe: quem já
# RENOMEOU o modelo para .env (em vez de copiar) não tem mais o .example —
# e acusar "pacote incompleto" seria falso: o pacote veio inteiro.
if [ -f ".env" ]; then
    echo "O arquivo .env já existe — mantendo o que está lá."
else
    exigir_arquivo ".env.example"
    cp .env.example .env
    echo "Criei o arquivo .env a partir do modelo (.env.example)."
    echo ""
    echo "IMPORTANTE: falta preencher sua chave do Gemini no .env:"
    echo "  1. Acesse https://aistudio.google.com/apikey (conta Google, sem cartão)"
    echo "  2. Clique em 'Create API key' e copie a chave"
    echo "  3. Abra o arquivo .env na pasta do projeto e cole a chave depois de GEMINI_API_KEY="
fi

# --- 5. Verificação final ----------------------------------------------
titulo "5 de 5: verificação do ambiente"
# O GUIA manda o aluno rodar o baixar-dados.py logo depois deste passo —
# conferir aqui evita a surpresa cinco minutos depois do setup "verde".
exigir_arquivo "scripts/baixar-dados.py"
echo "Rodando scripts/verifica-ambiente.py ..."
echo ""
CODIGO_SAIDA=0
"$PYTHON_VENV" scripts/verifica-ambiente.py || CODIGO_SAIDA=$?
echo ""

if [ "$CODIGO_SAIDA" -eq 0 ]; then
    echo "Configuração concluída: ambiente pronto para a aula."
else
    echo "A verificação apontou problemas (veja as linhas com X acima)."
    echo "Siga as instruções 'o que fazer' de cada item e rode este script de novo."
    echo "Se não resolver, escreva para a coordenação ANTES do primeiro encontro."
fi

echo ""
echo "Para ativar o ambiente manualmente no terminal:"
if [ -x ".venv/bin/python" ]; then
    echo "  source .venv/bin/activate"
else
    echo "  .venv/Scripts/python.exe  (Git Bash no Windows)"
fi
echo ""
