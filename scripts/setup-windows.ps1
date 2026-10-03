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
# Não exige privilégio de administrador.
#
# Se o PowerShell bloquear este arquivo com erro "running scripts is
# disabled", rode no lugar:
#   powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
# ==================================================================

$ErrorActionPreference = 'Stop'
$Raiz = Split-Path -Parent $PSScriptRoot
Set-Location $Raiz

function Escrever-Titulo {
    param([string]$Texto)
    Write-Host ""
    Write-Host "=== $Texto ===" -ForegroundColor Cyan
}

function Encontrar-Python {
    # Devolve o caminho COMPLETO do python.exe 3.12+ (ex.:
    # C:\Users\ana\AppData\Local\Programs\Python\Python313\python.exe), ou
    # string vazia se não houver.
    #
    # Tudo roda via 'cmd /c ... 2>nul', por dois motivos:
    # - o launcher 'py.exe' escreve avisos no stderr quando a versão pedida
    #   não existe, e o PowerShell 5.1 com 'Stop' faria disso erro fatal;
    # - o PowerShell procura 'py.*' no PATH e aceita arquivo SEM extensão:
    #   se existir um arquivo chamado só 'py' (já visto em C:\Windows\System32),
    #   '& py' abre a janela "Como deseja abrir este arquivo?". O cmd só
    #   executa extensões do PATHEXT e acha o py.exe de verdade.
    # Depois daqui, o script só chama o python pelo caminho completo.
    $pedido = "import sys; print(sys.executable) if sys.version_info >= (3, 12) else sys.exit(1)"

    $candidatos = @('py -3.14', 'py -3.13', 'py -3.12', 'python', 'python3')
    foreach ($candidato in $candidatos) {
        $saida = & cmd /c "$candidato -c `"$pedido`" 2>nul"
        if ($LASTEXITCODE -eq 0 -and $saida) {
            $executavel = ([string]($saida | Select-Object -Last 1)).Trim()
            if ($executavel -and (Test-Path $executavel)) {
                return $executavel
            }
        }
    }
    return ''
}

function Rodar-Pip {
    param([Parameter(Mandatory)][string[]]$Argumentos)
    # O cmd /c junta stdout+stderr como TEXTO. Sem isso, o stderr do pip sob
    # redirecionamento vira erro do PowerShell e, com ErrorActionPreference
    # 'Stop', interromperia este script no meio da instalação.
    $linha = "`"$pythonVenv`" -m pip " + ($Argumentos -join " ") + " 2>&1"
    $texto = cmd /c $linha
    return @{ Codigo = $LASTEXITCODE; Texto = ($texto | Out-String).Trim() }
}

function Traduzir-ErroPip {
    param([Parameter(Mandatory)][string]$Texto)
    if ($Texto -match 'Long Path|long-paths|filename or extension is too long') {
        return ("CAMINHO DA PASTA LONGO DEMAIS PARA O WINDOWS: alguns pacotes têm arquivos " +
            "com mais de 160 caracteres dentro da .venv.`n" +
            "O que fazer: feche este terminal, mova esta pasta para C:\CEDAGI (ex.: " +
            "C:\CEDAGI\D1), APAGUE a pasta .venv e rode este script de novo na pasta nova.")
    }
    if ($Texto -match 'Proxy|proxy|SSL|Timed out|temporary failure|getaddrinfo') {
        $ultimas = ($Texto -split "`r?`n") | Select-Object -Last 6
        return ("SEM INTERNET OU PROXY BLOQUEANDO: confira o Wi-Fi/rede. Em máquina de " +
            "empresa, o firewall costuma bloquear o PyPI — peça liberação à TI.`n" +
            "O que o pip relatou (últimas linhas):`n" + ($ultimas -join "`n"))
    }
    if ($Texto -match 'No space left|disk') {
        return "SEM ESPAÇO EM DISCO: libere pelo menos 2 GB e rode este script de novo."
    }
    $ultimas = ($Texto -split "`r?`n") | Select-Object -Last 6
    return ("A instalação falhou. Últimas linhas do pip para anexar ao pedido de ajuda:`n" +
        ($ultimas -join "`n"))
}

function Exigir-ArquivoDoPacote {
    # Guarda do B04 §3.2: arquivos que deveria ter vindo no D1-00. Se algum
    # falta, o problema é do PACOTE (descompactação incompleta), não da
    # máquina do aluno — a mensagem diz exatamente isso, porque não há nada
    # que o aluno possa "resolver" localmente.
    param([Parameter(Mandatory)][string[]]$Caminhos)
    $faltando = @($Caminhos | Where-Object { -not (Test-Path (Join-Path $Raiz $_)) })
    if ($faltando.Count -gt 0) {
        Write-Host "ERRO: faltam arquivos neste pacote ($($faltando -join ', '))." -ForegroundColor Red
        Write-Host ""
        Write-Host "Baixe o D1-00-antes-de-comecar.zip de novo pelo Moodle e descompacte"
        Write-Host "TUDO — algumas ferramentas de descompactação deixam arquivos para trás."
        Write-Host "Se o problema persistir, escreva para a coordenação."
        exit 1
    }
}

function Instalar-PacotePorAtalho {
    # Plano B quando o pip install -e . falha. Causas conhecidas: caminho de
    # pasta com espaços/acentos quebra o build editável do setuptools
    # ("egg_base"); e sem internet o build isolation não consegue baixar o
    # setuptools. Solução: um junction (atalho de diretório, sem administrador)
    # em caminho sem acentos apontando para o src, registrado via .pth — o
    # resultado prático é o mesmo `import ams`.
    $atalho = Join-Path $env:PUBLIC "ams-d1-src"
    try {
        if (Test-Path $atalho) { (Get-Item $atalho).Delete() }
        New-Item -ItemType Junction -Path $atalho -Target (Join-Path $Raiz 'src') -ErrorAction Stop | Out-Null
    } catch {
        Write-Host "ERRO: não consegui instalar o pacote do projeto." -ForegroundColor Red
        Write-Host "O pip install -e . falhou e o atalho de contorno também."
        Write-Host "Caminho da pasta: $Raiz"
        Write-Host "O que fazer: mova o projeto para C:\CEDAGI\D1 (caminho curto,"
        Write-Host "sem espaços nem acentos), apague a pasta .venv e rode este script de novo."
        exit 1
    }
    $env:AMS_ATALHO = $atalho
    & $pythonVenv -c "from pathlib import Path; import sysconfig, os; p = Path(sysconfig.get_paths()['purelib']) / '_ams_src.pth'; p.write_text(os.environ['AMS_ATALHO'], encoding='ascii'); print('atalho:', p)"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERRO: não consegui registrar o atalho do pacote na venv." -ForegroundColor Red
        Write-Host "Feche editores e rode este script de novo (ele retoma de onde parou)."
        Write-Host "Se repetir, escreva para a coordenação com esta tela anexada."
        exit 1
    }
    Write-Host "Aviso: o pip não conseguiu instalar o pacote editável (motivo no log acima)."
    Write-Host "Registrei um atalho equivalente: import ams funciona normalmente."
}

Escrever-Titulo "Configuração do ambiente do AMS"
Write-Host "Pasta do projeto: $Raiz"

# O Windows tem limite histórico de 260 caracteres por caminho. A .venv
# acrescenta até 162 caracteres à pasta do projeto (medido com este
# requirements.txt), e o pip falha no meio da instalação quando a soma passa
# do limite — visto numa pasta de 148 caracteres. 60 deixa folga. Barrar
# ANTES de criar a .venv poupa os minutos de download e a .venv pela metade.
# Acentos também barram: o pip install -e . e as mensagens do cmd quebram.
$limiteDoCaminho = 60
$temAcento = $Raiz -match '[^\x00-\x7F]'
if ($Raiz.Length -gt $limiteDoCaminho -or $temAcento) {
    if ($temAcento) {
        Write-Host "PARE: o caminho desta pasta tem acento ou caractere especial." -ForegroundColor Red
        Write-Host "Com ele, a instalação do pacote do projeto e as mensagens de erro quebram."
    } else {
        Write-Host "PARE: o caminho desta pasta tem $($Raiz.Length) caracteres (o máximo é $limiteDoCaminho)." -ForegroundColor Red
        Write-Host "Com ele, a instalação dos pacotes falha no meio (limite de caminho do Windows)."
    }
    Write-Host ""
    Write-Host "O que fazer:"
    Write-Host "  1. Feche este terminal."
    Write-Host "  2. Crie a pasta C:\CEDAGI e mova esta pasta para dentro dela:"
    Write-Host "     C:\CEDAGI\D1 para o pacote antes de começar (ou extraia o .zip de novo"
    Write-Host "     direto em C:\CEDAGI\D1); C:\CEDAGI\meu-projeto para o repositório clonado."
    Write-Host "  3. Se veio junto uma pasta .venv, apague-a."
    Write-Host "  4. Abra o PowerShell na pasta nova e rode este script de novo."
    exit 1
}

if ((Get-ExecutionPolicy) -eq 'Restricted') {
    Write-Host ""
    Write-Host "Nota: a política de scripts deste usuário é 'Restricted'."
    Write-Host "Você conseguiu rodar porque usou -ExecutionPolicy Bypass. Para liberar"
    Write-Host "de forma permanente (só uma vez, sem administrador), rode:"
    Write-Host "  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned"
}

# --- 1. Python 3.12+ ------------------------------------------------
Escrever-Titulo "1 de 5: procurando Python 3.12 ou superior"
$pythonExe = Encontrar-Python
if (-not $pythonExe) {
    Write-Host "ERRO: não encontrei Python 3.12 ou superior nesta máquina." -ForegroundColor Red
    Write-Host ""
    Write-Host "O que fazer:"
    Write-Host "  1. Baixe o Python 3.12+ em: https://www.python.org/downloads/"
    Write-Host "  2. Na tela de instalação, MARQUE a opção 'Add python.exe to PATH'"
    Write-Host "     (fica embaixo, fácil de não ver — é a causa mais comum de problema)"
    Write-Host "  3. Se ao digitar 'python' abrir a LOJA DA MICROSOFT: o Windows traz um"
    Write-Host "     python falso (alias). Desative em Configurações > Aplicativos > Execução"
    Write-Host "     de aplicativos avançada > Aliases: desligue python e python3"
    Write-Host "  4. Feche e reabra o PowerShell, então rode este script de novo"
    exit 1
}
$versaoInstalada = & $pythonExe -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')"
Write-Host "Python encontrado: $versaoInstalada ($pythonExe)"

# --- 2. Ambiente virtual ---------------------------------------------
Escrever-Titulo "2 de 5: ambiente virtual (.venv)"
$pythonVenv = Join-Path $Raiz '.venv\Scripts\python.exe'
# A .venv guarda caminhos absolutos: copiada ou movida de outra pasta (o
# conselho quando o caminho era longo), ela parece existir mas não funciona.
# A marca registra onde esta .venv nasceu; sem marca ou em outra pasta,
# recria. A marca só é gravada no fim da instalação dos pacotes, então uma
# .venv que parou no meio também é recriada na próxima rodada.
$marcaVenv = Join-Path $Raiz '.venv\ams-pasta-de-origem.txt'
$venvValida = (Test-Path $pythonVenv) -and (Test-Path $marcaVenv) -and
    ((Get-Content $marcaVenv -Raw).Trim() -eq $Raiz)
if ($venvValida) {
    Write-Host "O ambiente virtual já existe — reutilizando (nada recriado)."
} else {
    if (Test-Path (Join-Path $Raiz '.venv')) {
        Write-Host "Há uma .venv incompleta ou vinda de outra pasta — apagando para recriar..."
        try {
            Remove-Item -Recurse -Force (Join-Path $Raiz '.venv') -ErrorAction Stop
        } catch {
            Write-Host "ERRO: não consegui apagar a pasta .venv (algum programa está usando)." -ForegroundColor Red
            Write-Host "Feche o VS Code, o Jupyter e outros terminais, apague a pasta .venv"
            Write-Host "pelo Explorer e rode este script de novo."
            exit 1
        }
    }
    Write-Host "Criando ambiente virtual em .venv (leva ~30 segundos)..."
    $criacao = cmd /c "`"$pythonExe`" -m venv .venv 2>&1"
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $pythonVenv)) {
        Write-Host "ERRO: não consegui criar o ambiente virtual." -ForegroundColor Red
        if (($criacao | Out-String) -match "Access is denied|WinError 5") {
            Write-Host "A PASTA NÃO PERMITE ESCRITA. Causa comum: o projeto foi executado de"
            Write-Host "dentro do .zip (aberto no navegador) ou extraído em local protegido."
            Write-Host "O que fazer: extraia o projeto em C:\CEDAGI\D1 e rode este script de novo."
        } else {
            Write-Host "Saída do comando para anexar ao pedido de ajuda:"
            Write-Host (($criacao | Out-String).Trim())
            Write-Host "Feche o PowerShell, abra de novo e tente outra vez; se persistir,"
            Write-Host "anexe este erro e escreva para a coordenação antes da aula."
        }
        exit 1
    }
    Write-Host "Ambiente virtual criado."
}

# --- 3. Pacotes -------------------------------------------------------
Escrever-Titulo "3 de 5: instalando pacotes do requirements.txt"
# requirements.txt: o passo inteiro depende dele; pyproject.toml + src/ams/
# __init__.py: o 'pip install -e .' que dá o 'import ams' depende dos dois.
Exigir-ArquivoDoPacote @('requirements.txt', 'pyproject.toml', 'src\ams\__init__.py')
Write-Host "Baixando numpy, pandas e cia. — na primeira vez são uns 2 minutos..."

$atualizar = Rodar-Pip @("install", "--upgrade", "pip", "--quiet")
if ($atualizar.Codigo -ne 0) {
    Write-Host "ERRO: não consegui atualizar o pip." -ForegroundColor Red
    Write-Host (Traduzir-ErroPip $atualizar.Texto)
    exit 1
}

$instalar = Rodar-Pip @("install", "-r", "requirements.txt")
if ($instalar.Codigo -ne 0) {
    Write-Host "ERRO: a instalação dos pacotes falhou." -ForegroundColor Red
    Write-Host (Traduzir-ErroPip $instalar.Texto)
    Write-Host ""
    Write-Host "Rode este script de novo após resolver; ele retoma de onde parou."
    exit 1
}
Write-Host "Pacotes instalados (ou já estavam instalados)."
Set-Content -Path $marcaVenv -Value $Raiz -Encoding ASCII

# O próprio projeto é um pacote (pyproject.toml): instalá-lo em modo editável
# deixa `import ams` funcionar em qualquer lugar da venv. --no-deps porque as
# dependências já vieram do requirements.txt (e sem rede o pip não resolveria).
if (Test-Path (Join-Path $Raiz 'pyproject.toml')) {
    $editavel = Rodar-Pip @("install", "-e", ".", "--no-deps", "--quiet")
    if ($editavel.Codigo -eq 0) {
        Write-Host "Pacote do projeto instalado em modo editável (import ams)."
    } else {
        Write-Host "Aviso: pip install -e . relatou (últimas linhas):"
        Write-Host (($editavel.Texto -split "`r?`n") | Select-Object -Last 4)
        Instalar-PacotePorAtalho
    }
}

# --- 4. Arquivo .env ---------------------------------------------------
Escrever-Titulo "4 de 5: arquivo de configuração (.env)"
# O .env.example só é exigido quando o .env ainda não existe: quem já
# RENOMEOU o modelo para .env (em vez de copiar) não tem mais o .example —
# e acusar "pacote incompleto" seria falso: o pacote veio inteiro.
if (Test-Path (Join-Path $Raiz '.env')) {
    Write-Host "O arquivo .env já existe — mantendo o que está lá."
} else {
    Exigir-ArquivoDoPacote @('.env.example')
    Copy-Item (Join-Path $Raiz '.env.example') (Join-Path $Raiz '.env')
    Write-Host "Criei o arquivo .env a partir do modelo (.env.example)."
    Write-Host ""
    Write-Host "IMPORTANTE: falta preencher sua chave do Gemini no .env:" -ForegroundColor Yellow
    Write-Host "  1. Acesse https://aistudio.google.com/apikey (conta Google, sem cartão)"
    Write-Host "  2. Clique em 'Create API key' e copie a chave"
    Write-Host "  3. Abra o arquivo .env na pasta do projeto e cole a chave depois de GEMINI_API_KEY="
}

# --- 5. Verificação final ----------------------------------------------
Escrever-Titulo "5 de 5: verificação do ambiente"
# O GUIA manda o aluno rodar o baixar-dados.py logo depois deste passo —
# conferir aqui evita a surpresa cinco minutos depois do setup "verde".
Exigir-ArquivoDoPacote @('scripts\baixar-dados.py')
Write-Host "Rodando scripts\verifica-ambiente.py ..."
Write-Host ""
& $pythonVenv scripts\verifica-ambiente.py
$codigoSaida = $LASTEXITCODE
Write-Host ""

if ($codigoSaida -eq 0) {
    Write-Host "Configuração concluída: ambiente pronto para a aula." -ForegroundColor Green
} else {
    Write-Host "A verificação apontou problemas (veja as linhas com X acima)." -ForegroundColor Yellow
    Write-Host "Siga as instruções 'o que fazer' de cada item e rode este script de novo."
    Write-Host "Se não resolver, escreva para a coordenação ANTES do primeiro encontro."
}

Write-Host ""
Write-Host "Para ativar o ambiente manualmente no PowerShell:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host ""
