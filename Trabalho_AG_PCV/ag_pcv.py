import matplotlib.pyplot as plt
import numpy as np


class AlgoritmoGenetico:
    """Algoritmo Genetico para o Problema do Caixeiro Viajante (TSP com Ciclo Fechado).

    Cromossomos representados por permutações de cidades (numeradas de 1 a n).
    Utiliza seleção por roleta viciada, crossover cíclico (CX), mutação por troca
    de dois genes e estratégia de elitismo que preserva os 50% melhores indivíduos
    da população a cada geração.
    """

    def __init__(self, x, y, tam_pop=20, geracoes=10000):
        self.x = x
        self.y = y
        self.n_cidades = len(x)
        self.tam_pop = tam_pop
        self.geracoes = geracoes
        self.matriz_custo = self._gerar_matriz_custo()
        self.populacao, self.aptidoes = self._iniciar_populacao()
        self.historico = [self.aptidoes.min()]

    def _gerar_matriz_custo(self):
        """Gera matriz de distancias euclidiana usando broadcast do NumPy."""
        coords = np.column_stack((self.x, self.y))
        diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
        return np.sqrt(np.sum(diff ** 2, axis=-1))

    def _iniciar_populacao(self):
        """Cria populacao inicial com permutacoes aleatorias de 1 a n_cidades."""
        pop = np.array(
            [np.random.permutation(self.n_cidades) + 1
             for _ in range(self.tam_pop)]
        )
        apt = np.array(
            [self._calcular_aptidao(pop[i]) for i in range(self.tam_pop)]
        )
        return pop, apt

    def _calcular_aptidao(self, config):
        """Distancia total do percurso (fitness). Ciclo fechado: retorna a cidade inicial."""
        idx = config - 1
        ciclo = np.append(idx, idx[0])
        return self.matriz_custo[ciclo[:-1], ciclo[1:]].sum()

    def _selecao_roleta(self, aptidoes, qtde):
        """Roleta: probabilidade inversamente proporcional a aptidao."""
        pesos = 1.0 / aptidoes
        probs = pesos / pesos.sum()
        return np.random.choice(len(aptidoes), size=qtde, replace=False, p=probs)

    def _crossover_ciclo(self, p1, p2):
        """Crossover Ciclico (CX) conforme os 4 passos do trabalho."""
        n = len(p1)
        f1, f2 = p1.copy(), p2.copy()

        idx = np.random.randint(n)
        if f1[idx] == f2[idx]:
            return f1, f2

        f1[idx], f2[idx] = f2[idx], f1[idx]

        while True:
            duplicatas = np.where(f1 == f1[idx])[0]
            if len(duplicatas) < 2:
                break
            dup_idx = duplicatas[0] if duplicatas[0] != idx else duplicatas[1]
            f1[dup_idx], f2[dup_idx] = f2[dup_idx], f1[dup_idx]
            idx = dup_idx

        return f1, f2

    def _mutacao(self, config):
        """Troca duas posicoes aleatorias no cromossomo (swap mutation)."""
        i, j = np.random.choice(self.n_cidades, 2, replace=False)
        config[i], config[j] = config[j], config[i]
        return config

    def evoluir(self):
        """Executa uma geracao completa do algoritmo genetico."""
        ordem = np.argsort(self.aptidoes)
        self.populacao = self.populacao[ordem]
        self.aptidoes = self.aptidoes[ordem]

        metade = self.tam_pop // 2

        nova_pop = np.empty_like(self.populacao)
        novas_apt = np.empty_like(self.aptidoes)

        nova_pop[:metade] = self.populacao[:metade]
        novas_apt[:metade] = self.aptidoes[:metade]

        elite_apt = self.aptidoes[:metade]

        idx_filho = metade
        while idx_filho < self.tam_pop:
            pais_idx = self._selecao_roleta(elite_apt, 2)
            p1 = self.populacao[pais_idx[0]]
            p2 = self.populacao[pais_idx[1]]

            f1, f2 = self._crossover_ciclo(p1, p2)

            for filho in (f1, f2):
                if idx_filho < self.tam_pop:
                    filho = self._mutacao(filho)
                    nova_pop[idx_filho] = filho
                    novas_apt[idx_filho] = self._calcular_aptidao(filho)
                    idx_filho += 1

        self.populacao = nova_pop
        self.aptidoes = novas_apt
        self.historico.append(self.aptidoes.min())

    def melhor_individuo(self):
        """Retorna (configuracao, aptidao) do melhor individuo da populacao atual."""
        idx = np.argmin(self.aptidoes)
        return self.populacao[idx], self.aptidoes[idx]


def main():
    """Carrega dados, executa o AG e exibe resultados formatados."""
    try:
        data = np.loadtxt("cidades.mat")
        x, y = data[0], data[1]
    except FileNotFoundError:
        np.random.seed(42)
        x = np.random.rand(20)
        y = np.random.rand(20)

    POP_SIZE = 20
    GENERATIONS = 10000
    N_CIDADES = len(x)

    ag = AlgoritmoGenetico(x, y, tam_pop=POP_SIZE, geracoes=GENERATIONS)

    pop_inicial = ag.populacao.copy()
    apt_inicial = ag.aptidoes.copy()

    for _ in range(GENERATIONS):
        ag.evoluir()

    ordem = np.argsort(ag.aptidoes)
    ag.populacao = ag.populacao[ordem]
    ag.aptidoes = ag.aptidoes[ordem]
    melhor_config, melhor_custo = ag.melhor_individuo()

    separador = "-" * 55
    print(separador)
    print(f"  Tamanho da Populacao : {POP_SIZE}")
    print(f"  Numero de Cidades    : {N_CIDADES}")
    print(f"  Geracoes             : {GENERATIONS}")
    print(separador)

    print("\nPopulacao Inicial:")
    for i in range(POP_SIZE):
        print(f"  {i+1:2d}. {pop_inicial[i].tolist()}  |  Custo: {apt_inicial[i]:.4f}")

    print(f"\nMelhor custo inicial : {apt_inicial.min():.4f}")

    print("\nPopulacao Final (ordenada por aptidao):")
    for i in range(POP_SIZE):
        print(f"  {i+1:2d}. {ag.populacao[i].tolist()}  |  Custo: {ag.aptidoes[i]:.4f}")

    print(f"\n{separador}")
    print(f"  Melhor Custo   : {melhor_custo:.4f}")
    print(f"  Melhor Solucao : {melhor_config.tolist()}")
    print(separador)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

    ax1.plot(ag.historico, linewidth=0.8, color='steelblue')
    ax1.set_title("Convergencia do Algoritmo Genetico")
    ax1.set_xlabel("Geracao")
    ax1.set_ylabel("Melhor Custo")
    ax1.set_xlim(0, GENERATIONS)
    ax1.grid(True, alpha=0.4)

    rota = melhor_config - 1
    x_plot = np.append(x[rota], x[rota[0]])
    y_plot = np.append(y[rota], y[rota[0]])

    ax2.plot(x_plot, y_plot, '-', color='steelblue', linewidth=1.5, zorder=1)
    ax2.scatter(x[rota], y[rota], color='tomato', s=60, zorder=3)

    for i, cidade in enumerate(rota):
        ax2.annotate(
            str(cidade + 1),
            (x[cidade], y[cidade]),
            textcoords="offset points",
            xytext=(6, 6),
            fontsize=8
        )

    ax2.plot(x_plot[0], y_plot[0], 's', color='gold',
             markersize=10, zorder=4, label=f'Inicio (Cidade {rota[0]+1})')
    ax2.set_title(f"Melhor Caminho Encontrado\nCusto: {melhor_custo:.4f}")
    ax2.set_xlabel("Coordenada X")
    ax2.set_ylabel("Coordenada Y")
    ax2.legend()
    ax2.grid(True, alpha=0.4)

    plt.tight_layout()
    plt.savefig("resultado.png", dpi=150, bbox_inches='tight')
    plt.show()


if __name__ == "__main__":
    main()
