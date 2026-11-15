# Anotações — Laboratório 02, a descida à mão

> O critério do slide 11: as quatro perguntas respondidas por escrito, com o
> número que sustenta cada resposta. Preencha a tabela rodando o esqueleto
> com as três taxas do slide 12 e copiando a última linha de cada execução.

## A última linha de cada taxa

| Taxa | Última linha da saída (perda, w, b) |
|---|---|
| 0,001 | passo  200 perda 79387.3 w 140.919 b -13.7549 |
| 0,1 | passo  200 perda 0.752176 w 300.008 b 4.91185 |
| 1,5 | passo  200 perda 5.57443e+238 w -5.00076e+119 b 7.7298e+118 |

## As quatro perguntas do slide 11

**1. A perda está caindo a cada passo, ou oscilando?**

R: 0,001 -> caindo
0,1 -> caindo e estabiliza em 0.75
1,5 -> subindo

**2. Ela estabiliza, ou continua descendo até o fim?**

R: No 0,1 estabiliza.

**3. Os pesos encontrados batem com os que geraram os dados?**

R: Sim, no 0,1 o valor é próximos

**4. Se algo divergiu, qual foi o primeiro passo estranho?**
 
R: No 1,5 ele sai do ponto inicial para um valor muito maior, "se perdes"
