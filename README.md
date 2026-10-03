# AMS — Projeto Integrador de Agentes Inteligentes

Repositório do Projeto Integrador do **Curso de Especialização em
Desenvolvimento de Agentes Inteligentes (UTFPR)**. Ele nasce neste pacote com
a fundação já construída — ambiente reprodutível, dados válidos, análise
exploratória com conclusões e a primeira integração com um modelo de
linguagem — e cresce uma peça por disciplina ao longo dos 15 meses do curso:
especificação do agente, infraestrutura, aprendizado de máquina, recuperação
de informação, até o agente completo que é auditado na disciplina final.

O domínio deste repositório está descrito no [`dominio.md`](dominio.md) —
o problema, a decisão a automatizar, o usuário e a fonte de dados. Ele chega
preenchido com o domínio padrão do pacote; quem escolheu outro dataset
reescreve as respostas com as suas palavras (o guia do pacote orienta). A
análise exploratória que dá a base numérica dessa decisão está em
[`notebooks/01-eda.ipynb`](notebooks/01-eda.ipynb): oito perguntas com
gráfico e conclusão, mais a seção *"O que meu agente precisaria saber para
decidir isso?"*, que é a ponte com a disciplina seguinte.

## O que o projeto faz hoje

A fundação é um avaliador de risco de ordens de serviço industriais: lê uma
ordem com a leitura atual dos sensores, estima o nível de risco de falha,
indica as normas regulamentares aplicáveis e recomenda (ou não) o bloqueio da
máquina antes da intervenção. A decisão final é do técnico — o sistema apoia.

| Camada | Onde | O que faz |
|---|---|---|
| Configuração | `src/ams/config.py` | lê e valida o `.env` (chave, modelo, log) |
| Modelos do domínio | `src/ams/modelos.py` | `LeituraSensor`, `OrdemServico`, `AvaliacaoRisco` (Pydantic) |
| Dados | `src/ams/dados.py` | carrega, valida e prepara o dataset (com fallback para a amostra) |
| Análise | `src/ams/analise.py` | agregações da exploração (taxa de falha, modos, linha de base) |
| Vetores | `src/ams/vetores.py` | norma, similaridade de cosseno e vizinhos mais próximos (NumPy) |
| Log | `src/ams/log.py` | logging estruturado em JSON |
| Chamada do modelo | `src/ams/llm.py` | requisição REST com resposta estruturada, novas tentativas e modo sem rede |
| Cliente | `src/ams/cliente_llm.py` | lê ordens → chama o modelo → valida → registra, em lote concorrente |
| Exploração | `notebooks/01-eda.ipynb` | as oito perguntas respondidas com gráfico e conclusão |
| API local | `src/ams/api.py` | FastAPI com `/docs` (janela de exploração; documentada no `README-API.md`) |

## Como instalar

Python 3.12 ou mais novo e uma chave gratuita do Gemini
(<https://aistudio.google.com>, sem cartão de crédito) colada no `.env`
(copie do `.env.example`; o `.env` fica fora do Git). O script abaixo cria o
ambiente virtual, instala as dependências com versões fixadas e roda a
verificação de ambiente — em Windows:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1
```

Em macOS/Linux: `bash scripts/setup-unix.sh`.

## Como executar — os três comandos

Na raiz do repositório, depois da instalação (funcionam no PowerShell sem
ativar o ambiente; em macOS/Linux use `.venv/bin/python` no lugar):

```powershell
.venv\Scripts\python.exe scripts\baixar-dados.py      # baixa o dataset completo (precisa de rede; sem rede usa a amostra)
.venv\Scripts\python.exe -m ams.cliente_llm           # avalia 20 ordens de serviço e imprime a tabela
.venv\Scripts\python.exe -m pytest                    # roda os testes (69; nenhum toca a rede)
```

O `baixar-dados.py` é idempotente: rodado de novo, não refaz o download
(`--forcar` refaz). Sem a chave no `.env`, o cliente roda no modo sem rede
com `$env:AMS_MODO_OFFLINE = "1"` (PowerShell) ou `AMS_MODO_OFFLINE=1`
(macOS/Linux), lendo as respostas gravadas em `data/fixtures/` — mesma
validação, mesmo log. O detalhe de cada avaliação fica em
`data/logs/ams.jsonl`.

## Estrutura

```
├── dominio.md             # o problema, a decisão, os dados e o usuário
├── pyproject.toml         # pacote instalável "ams" + config de ruff/pytest
├── requirements.txt       # versões fixadas — fonte da verdade das dependências
├── scripts/               # setup, diagnóstico, download e verificação de entrega
├── src/ams/               # o pacote
├── notebooks/             # exploração dos dados
├── data/
│   ├── raw/               # baixado (fora do Git, regenerado pelo script)
│   ├── amostra/           # 200 linhas versionadas — o projeto roda sem download
│   └── fixtures/          # respostas gravadas do modelo (modo sem rede)
├── receitas/              # download dos datasets dos demais domínios do curso
└── tests/                 # pytest — tudo sem rede
```

## Dataset

O dataset do caminho padrão é o *AI4I 2020 Predictive Maintenance Dataset*
(UCI Machine Learning Repository, ID 601), 10.000 registros, licença
CC BY 4.0, baixado pelo `scripts/baixar-dados.py` com proveniência gravada em
`data/raw/PROVENIENCIA.txt` e resumo em `data/FONTE.md`. Os candidatos para
troca de domínio estão no `MAPA-DE-DATASETS.pdf`, com receita pronta para
cada um em `receitas/` — e o `COMO-TROCAR-O-DATASET.pdf` lista, arquivo a
arquivo, o que a troca exige.

## Modo sem rede

Com `AMS_MODO_OFFLINE=1`, o cliente do modelo lê respostas gravadas em
`data/fixtures/` em vez de chamar a API — a cota gratuita da conta não
interrompe o trabalho. Os testes nunca tocam a rede.
