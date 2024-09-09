def transform_to_directed(G):
    """Transforma um grafo não direcionado em um grafo direcionado"""
    directed_G = nx.DiGraph()
    for u, v, data in G.edges(data=True):
        # Adiciona aresta u -> v
        directed_G.add_edge(u, v, **data)
        # Adiciona aresta v -> u
        directed_G.add_edge(v, u, **data)
    return directed_G

# Função de Rótulos nos Vértices com restrições MTZ (sem SEC)
def solve_with_mtz(G, d):
    solver = pywraplp.Solver.CreateSolver('SCIP')
    if not solver:
        return None

    # Transformar o grafo não direcionado em direcionado
    G = transform_to_directed(G)

    # Variáveis de decisão: 1 se o arco (u, v) estiver na árvore, 0 caso contrário
    y = {}
    for u, v in G.edges():
        y[(u, v)] = solver.BoolVar(f'y_{u}_{v}')

    # Função objetivo: minimizar o custo total das arestas selecionadas
    solver.Minimize(solver.Sum(G[u][v]['weight'] * y[(u, v)] for u, v in G.edges()))

    # Definir um vértice raiz arbitrário (pode ser modificado para qualquer vértice de C)
    root = 0  # A raiz recebe rótulo 0, pode ser central ou definido de outra forma
    labels = {}
    
    # Variáveis de rótulos para os vértices
    for v in G.nodes():
        if v == root:
            labels[v] = solver.IntVar(0, 0, f'label_{v}')  # A raiz recebe rótulo 0
        else:
            labels[v] = solver.IntVar(1, len(G.nodes()), f'label_{v}')  # Demais vértices com rótulos ≥ 1

    # Restrições de rotulação de vértices para evitar ciclos (MTZ)
    for u, v in G.edges():
        solver.Add(labels[u] - labels[v] + len(G.nodes()) * y[(u, v)] <= len(G.nodes()) - 1)

    # Restrições de grau mínimo para os vértices centrais
    for v in d:
        solver.Add(solver.Sum(y[(u, v)] for u in G.predecessors(v)) >= d[v])
        solver.Add(solver.Sum(y[(v, j)] for j in G.successors(v)) >= d[v])

    # Restrições de folhas: vértices que não são centrais devem ser folhas (grau 1)
    for v in G.nodes():
        if v not in d:
            solver.Add(solver.Sum(y[(u, v)] for u in G.predecessors(v)) + solver.Sum(y[(v, j)] for j in G.successors(v)) == 1)

    # Definir limite de tempo de execução
    solver.SetTimeLimit(1800000)  # 30 minutos em milissegundos

    # Resolver o problema
    start_time = time.time()
    status = solver.Solve()
    final_time = time.time() - start_time

    # Exibir o status da solução
    if status == pywraplp.Solver.OPTIMAL:
        print("Solução ótima encontrada.")
    elif status == pywraplp.Solver.FEASIBLE:
        print("Solução viável encontrada, mas pode não ser ótima.")
    else:
        print("Solução não encontrada.")

    return final_time