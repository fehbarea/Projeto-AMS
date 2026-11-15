# FONTE — de onde vêm os vetores desta pasta

Os quatro arquivos aqui (`manutencao-*` e `generico-*`) são cópias byte a
byte dos vetores pré-calculados da disciplina, gerados em 01/09/2026 com o
modelo `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` (384
dimensões, `float32`, sem normalizar — o laboratório compara com e sem
normalização, então os vetores precisam chegar crus; slide 55). Nenhuma
rede é chamada no laboratório: a redução a duas dimensões roda sobre estes
vetores prontos.

| Arquivo | md5 | Papel |
|---|---|---|
| `manutencao-vetores.npy` | `d77072ed31f8c69aaa0e4b00fd27e4be` | conjunto padrão (manutenção industrial) |
| `generico-vetores.npy` | `329b70dde3cc858e2babcac3a9f855bf` | a reserva — a comparação entre domínios da janela |

Modelo, versões da geração, licenças e o roteiro para gerar vetores de
frases próprias estão no `FONTE.md` de origem, ao lado das matrizes
originais em `fonte/dados/vetores/` da disciplina. As frases são de
autoria da coordenação para fim didático; o modelo é Apache 2.0.

Os dois arquivos de cada conjunto viajam SEMPRE juntos e alinhados por
índice: a frase de índice `i` tem o vetor de índice `i`.
