# 📖 Documentação Técnica — Algoritmo Genético para TSP

Este documento explica cada parte do código `main.py` em detalhe, com foco em entendimento real de cada decisão de implementação.

---

## Visão Geral da Arquitetura

O código está organizado em uma única classe (`AlgoritmoGenetico`) mais uma função `main()`. A classe encapsula todo o estado e a lógica do algoritmo; a `main()` cuida de carregar dados, executar e exibir resultados.

---

## Classe `AlgoritmoGenetico`

### `__init__`

```python
def __init__(self, x, y, tam_pop=20, geracoes=10000):
    self.x = x
    self.y = y
    self.n_cidades = len(x)
    self.tam_pop = tam_pop
    self.geracoes = geracoes
    self.matriz_custo = self._gerar_matriz_custo()
    self.populacao, self.aptidoes = self._iniciar_populacao()
    self.historico = [self.aptidoes.min()]
```

O construtor recebe as coordenadas das cidades e os parâmetros do algoritmo. Na inicialização já:
- Gera a matriz de distâncias entre todas as cidades (`_gerar_matriz_custo`)
- Cria a população inicial aleatória (`_iniciar_populacao`)
- Inicia o histórico com o melhor custo da geração 0 — importante para o gráfico de convergência mostrar desde o começo, não só a partir da geração 1

---

### `_gerar_matriz_custo`

```python
coords = np.column_stack((self.x, self.y))
diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
return np.sqrt(np.sum(diff ** 2, axis=-1))
```

Gera uma matriz `n×n` onde `matriz_custo[i][j]` é a distância euclidiana entre a cidade `i` e a cidade `j`.

**Por que broadcast?** A alternativa seria dois `for` aninhados em Python puro, o que é lento. O broadcast do NumPy calcula todas as `n²` distâncias de uma vez em operações vetorizadas — para 20 cidades a diferença é pequena, mas a abordagem escala bem para N maior.

O `np.newaxis` insere dimensões extras que permitem ao NumPy alinhar os arrays para subtração elemento a elemento entre todos os pares de cidades simultaneamente.

---

### `_iniciar_populacao`

```python
pop = np.array([np.random.permutation(self.n_cidades) + 1
                for _ in range(self.tam_pop)])
```

Cada indivíduo é uma **permutação** dos inteiros de 1 a 20 — ou seja, uma ordem de visita às cidades. `np.random.permutation(20)` gera de 0 a 19, então somamos 1 para ficar de 1 a 20 conforme o enunciado.

A população é um array 2D NumPy de forma `(20, 20)`: 20 indivíduos, cada um com 20 genes.

---

### `_calcular_aptidao`

```python
idx = config - 1          # converte cidades 1-20 para índices 0-19
ciclo = np.append(idx, idx[0])  # fecha o ciclo: última cidade → primeira
return self.matriz_custo[ciclo[:-1], ciclo[1:]].sum()
```

Calcula a distância total da rota. O `np.append(idx, idx[0])` é o que torna o percurso um **ciclo fechado** — o caixeiro precisa voltar à cidade inicial, então a distância final inclui essa última perna.

`self.matriz_custo[ciclo[:-1], ciclo[1:]]` usa indexação vetorizada para pegar de uma vez as distâncias entre cada par de cidades consecutivas na rota.

**Fitness = distância total. Menor é melhor.**

---

### `_selecao_roleta`

```python
pesos = 1.0 / aptidoes
probs = pesos / pesos.sum()
return np.random.choice(len(aptidoes), size=qtde, replace=False, p=probs)
```

Implementa a **Roleta Viciada** (Roulette Wheel Selection). Como a aptidão aqui é uma distância (menor = melhor), a probabilidade de seleção é inversamente proporcional: `1/distância`. Quem tem rota mais curta recebe fatia maior da roleta.

`replace=False` é importante: garante que os dois pais sorteados sejam indivíduos **distintos**. Sem isso, um pai poderia cruzar consigo mesmo, gerando filhos idênticos a ele — desperdício de geração.

A roleta opera **apenas sobre a metade elite** da população (os 10 melhores), conforme especificado no enunciado: *"o operador de seleção escolhe apenas a fração da população que é mantida"*.

---

### `_crossover_ciclo`

Este é o operador mais complexo. O **Cycle Crossover (CX)** foi projetado especificamente para permutações — ele garante que os filhos não tenham cidades repetidas sem precisar de correção posterior.

```python
idx = np.random.randint(n)
if f1[idx] == f2[idx]:
    return f1, f2          # sem troca necessária, filhos = pais

f1[idx], f2[idx] = f2[idx], f1[idx]   # Passo 1: troca na posição sorteada
```

Após a troca inicial, um dos filhos tem uma cidade duplicada. O laço resolve isso:

```python
while True:
    duplicatas = np.where(f1 == f1[idx])[0]
    if len(duplicatas) < 2:
        break
    dup_idx = duplicatas[0] if duplicatas[0] != idx else duplicatas[1]
    f1[dup_idx], f2[dup_idx] = f2[dup_idx], f1[dup_idx]
    idx = dup_idx
```

**Exemplo concreto (do enunciado):**

```
Pais:       [4, 1, 5, 3, 2, 6]   e   [3, 4, 6, 2, 1, 5]
                          ↑ posição sorteada: índice 3

Passo 1 — troca na posição 3:
  f1 = [4, 1, 5, 2, 2, 6]   ← duplicata do 2 nas posições 3 e 4
  f2 = [3, 4, 6, 3, 1, 5]

Passo 2 — resolve duplicata do 2 (posição 4):
  f1 = [4, 1, 5, 2, 1, 6]   ← agora duplicata do 1 nas posições 1 e 4
  f2 = [3, 4, 6, 3, 2, 5]

Passo 3 — resolve duplicata do 1 (posição 1):
  f1 = [4, 4, 5, 2, 1, 6]   ← agora duplicata do 4 nas posições 0 e 1
  f2 = [3, 1, 6, 3, 2, 5]

Passo 4 — resolve duplicata do 4 (posição 0):
  f1 = [3, 4, 5, 2, 1, 6]   ← sem duplicatas, encerrado
  f2 = [4, 1, 6, 3, 2, 5]
```

O ciclo sempre termina porque os pais são permutações do mesmo conjunto de valores — eventualmente o ciclo fecha.

---

### `_mutacao`

```python
i, j = np.random.choice(self.n_cidades, 2, replace=False)
config[i], config[j] = config[j], config[i]
```

**Swap Mutation**: sorteia duas posições distintas (`replace=False`) e troca as cidades nessas posições. Simples e eficaz para permutações — mantém a validade do cromossomo (nenhuma cidade é perdida ou duplicada).

A mutação é aplicada a **cada filho gerado**, introduzindo variação genética que evita que a população fique presa em ótimos locais.

---

### `evoluir`

```python
# 1. Ordena por aptidão
ordem = np.argsort(self.aptidoes)
self.populacao = self.populacao[ordem]
self.aptidoes = self.aptidoes[ordem]

# 2. Elitismo: copia os 10 melhores direto
nova_pop[:metade] = self.populacao[:metade]
novas_apt[:metade] = self.aptidoes[:metade]

# 3. Gera 10 filhos via roleta + CX + mutação
elite_apt = self.aptidoes[:metade]
while idx_filho < self.tam_pop:
    pais_idx = self._selecao_roleta(elite_apt, 2)
    f1, f2 = self._crossover_ciclo(...)
    for filho in (f1, f2):
        filho = self._mutacao(filho)
        ...

# 4. Registra o melhor da geração completa
self.historico.append(self.aptidoes.min())
```

O fluxo de uma geração:
1. Ordena toda a população por distância crescente
2. Os 10 melhores vão direto para a próxima geração (elitismo)
3. Desses 10, seleciona pares via roleta para gerar os outros 10 filhos
4. Cada filho passa por crossover e mutação antes de entrar na população
5. `aptidoes.min()` registra o **melhor de toda a nova geração** (incluindo filhos) — não só do elite

---

### `melhor_individuo`

```python
idx = np.argmin(self.aptidoes)
return self.populacao[idx], self.aptidoes[idx]
```

Retorna o indivíduo com menor distância total. Após a execução completa, a população já está ordenada pelo `evoluir`, então `aptidoes[0]` já é o melhor — mas `argmin` funciona independente da ordenação, sendo mais seguro.

---

## Função `main()`

### Carregamento dos dados

```python
data = np.loadtxt("cidades.mat")
x, y = data[0], data[1]
```

`np.loadtxt` ignora linhas que começam com `#` por padrão, então o formato do arquivo Octave/MATLAB (`# name: x`, `# type: global matrix`, etc.) é tratado corretamente sem nenhuma configuração extra.

### Loop principal

```python
for _ in range(GENERATIONS):
    ag.evoluir()
```

Simples: chama `evoluir()` 10.000 vezes. Não há critério de parada antecipada — o algoritmo roda todas as gerações independente de ter convergido.

### Gráficos

**Convergência:** plota `ag.historico`, que tem 10.001 pontos (geração 0 até geração 10.000). O `set_xlim(0, GENERATIONS)` garante que o eixo X sempre vai até 10.000, mesmo que a melhoria pare antes.

**Rota:** `rota = melhor_config - 1` converte os números das cidades (1–20) para índices do array (0–19). O `np.append(x[rota], x[rota[0]])` fecha o ciclo visualmente. As anotações com `ax2.annotate` numernam cada cidade no gráfico para correlacionar com a solução impressa no console.

---

## Representação de Dados Interna

| Estrutura | Tipo | Forma | Descrição |
|---|---|---|---|
| `populacao` | `ndarray` int | `(20, 20)` | 20 indivíduos × 20 cidades |
| `aptidoes` | `ndarray` float | `(20,)` | distância total de cada indivíduo |
| `matriz_custo` | `ndarray` float | `(20, 20)` | distância entre cada par de cidades |
| `historico` | lista de float | `(10001,)` | melhor custo de cada geração |



