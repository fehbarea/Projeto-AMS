# README-API — a API local do AMS (E4-B4, janela de exploração)

O `ams.api` transforma o cliente do modelo em serviço: valida a entrada com Pydantic,
devolve o parecer validado e gera documentação viva em `/docs`. É a
preparação direta para a publicação na D4 — lá o contêiner sobe este mesmo app.

## Rodar

```powershell
# na raiz do projeto, com a venv ativa
uvicorn ams.api:app --reload
```

A API sobe em `http://127.0.0.1:8000` — abra `/docs` no navegador para ver as
rotas e testá-las na hora.

## Rotas

| Método | Caminho | O que faz |
|---|---|---|
| GET | `/saude` | `{"status": "ok", "modo": "online"}` — o modo vem do `.env` (`AMS_MODO_OFFLINE=1` vira `"offline"`) |
| POST | `/avaliar` | Recebe uma `OrdemServico` (JSON validado) e devolve o `AvaliacaoRisco` — o parecer com nível de risco, normas e bloqueio |

Exemplo de chamada com a API de pé:

```powershell
$body = @'
{"identificador": "OS-2026-0001", "maquina": "M14860",
 "leitura": {"udi": 1, "product_id": "M14860", "tipo": "M",
   "temperatura_ar": 298.1, "temperatura_processo": 308.6,
   "rotacao": 1551, "torque": 42.8, "desgaste": 0, "falha": false,
   "twf": false, "hdf": false, "pwf": false, "osf": false, "rnf": false},
 "descricao": "Troca do insert de corte do eixo 3 e regulagem da folga."}
'@
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/avaliar `
  -ContentType "application/json" -Body $body
```

## Comportamento de erro

- Entrada fora do contrato (campo faltando, valor impossível): **422** —
  gerado pelo Pydantic da entrada, antes de gastar chamada de modelo.
- Falha da camada de modelo (cota 429, esquema, rede): **503** com mensagem
  dizendo o que fazer — o problema é do fornecedor, não de quem chamou.

## Testes

```powershell
python -m pytest tests/test_api.py -v
```

Os testes usam `TestClient` e o modo sem rede — nada de rede nem chave. Os
casos cobertos: `/saude` com modo, parecer validado em `/avaliar`, rejeição
422, 503 quando a camada de modelo falha e `/docs` acessível.
