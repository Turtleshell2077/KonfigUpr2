"""Граф зависимостей: обход в глубину (DFS) с рекурсией.

Граф строится с учётом транзитивности: от заданного пакета к его
зависимостям, от них к их зависимостям и так далее. Пакеты, имя
которых содержит подстроку фильтра, не учитываются. Каждый пакет
посещается один раз, поэтому циклы не приводят к бесконечному обходу,
а найденные циклы запоминаются.

Репозиторий — любой объект с методом dependencies(пакет), который
возвращает список пакетов или бросает RepositoryError. Если дать
обходу репозиторий с развёрнутыми рёбрами, тот же алгоритм находит
обратные зависимости: пакеты, которые зависят от заданного.
"""

from maven import RepositoryError

NAME_PARTS = 2
FORWARD = ("Dependency graph of", "->")
REVERSE = ("Reverse dependencies of", "<-")


def package_name(node):
    """Имя пакета без версии: «g:a:1.0» -> «g:a», «A» -> «A»."""
    return ":".join(node.split(":")[:NAME_PARTS])


class Graph:
    """Результат обхода: рёбра, циклы, отфильтрованные пакеты, ошибки."""

    def __init__(self, root, text_filter):
        """Пустой граф с начальным пакетом root."""
        self.root = root
        self.text_filter = text_filter
        self.edges = {}
        self.cycles = []
        self.skipped = []
        self.errors = {}

    def edge_count(self):
        """Число рёбер (зависимостей) в графе."""
        return sum(len(children) for children in self.edges.values())


class GraphBuilder:
    """Строит граф зависимостей рекурсивным обходом в глубину (DFS)."""

    def __init__(self, repository, text_filter):
        """Запоминает репозиторий и подстроку для фильтрации пакетов."""
        self.repository = repository
        self.text_filter = text_filter
        self.graph = None
        self.path = []

    def build(self, root):
        """Обходит граф от пакета root и возвращает объект Graph."""
        self.graph = Graph(root, self.text_filter)
        self.path = []
        self.visit(root)
        return self.graph

    def is_skipped(self, node):
        """Пакет не учитывается, если его имя содержит подстроку фильтра."""
        name = package_name(node)
        return bool(self.text_filter) and self.text_filter in name

    def children(self, node):
        """Зависимости пакета из репозитория без отфильтрованных.

        Если не удалось получить зависимости начального пакета, это
        ошибка. Для остальных пакетов ошибка запоминается, а пакет
        остаётся в графе без зависимостей.
        """
        try:
            found = self.repository.dependencies(node)
        except RepositoryError as error:
            if node == self.graph.root:
                raise
            self.graph.errors[node] = str(error)
            return []
        result = []
        for child in found:
            if not self.is_skipped(child):
                result.append(child)
            elif child not in self.graph.skipped:
                self.graph.skipped.append(child)
        return list(dict.fromkeys(result))

    def visit(self, node):
        """Посещает пакет и рекурсивно все его зависимости (DFS).

        В self.path лежит текущий путь от начального пакета. Если
        зависимость уже есть на этом пути, найден цикл: дальше по ней
        не идём. Если пакет уже посещён раньше, тоже не идём второй раз.
        """
        self.graph.edges[node] = []
        self.path.append(node)
        for child in self.children(node):
            self.graph.edges[node].append(child)
            if child in self.path:
                start = self.path.index(child)
                self.graph.cycles.append(self.path[start:] + [child])
            elif child not in self.graph.edges:
                self.visit(child)
        self.path.pop()


def dependents(graph):
    """Пакеты, которые зависят от начального (для обратного графа).

    Это все посещённые пакеты, кроме начального. Сам начальный пакет
    добавляется, только если он зависит от себя (через цикл).
    """
    found = [node for node in graph.edges if node != graph.root]
    if any(graph.root in children for children in graph.edges.values()):
        found.append(graph.root)
    return found


def summary_line(graph, reverse):
    """Итог: число пакетов и рёбер или список зависящих пакетов."""
    if not reverse:
        return (f"Packages: {len(graph.edges)}, "
                f"dependencies: {graph.edge_count()}")
    found = ", ".join(dependents(graph)) or "(none)"
    return f"Packages that depend on {graph.root}: {found}"


def graph_lines(graph, reverse=False):
    """Строки для вывода графа.

    Пакеты пронумерованы в порядке обхода в глубину, под каждым —
    его рёбра, по одной на строке: «-> B» — пакет зависит от B,
    «<- B» (обратный режим) — B зависит от пакета.
    """
    title, arrow = REVERSE if reverse else FORWARD
    lines = [f"{title} {graph.root}:"]
    for number, (node, children) in enumerate(graph.edges.items(),
                                              start=1):
        lines.append(f"  {number}. {node}")
        lines.extend(f"       {arrow} {child}" for child in children)
    lines.append(summary_line(graph, reverse))
    if graph.skipped:
        lines.append(f"Skipped by filter '{graph.text_filter}':")
        lines.extend(f"  {node}" for node in graph.skipped)
    for cycle in graph.cycles:
        lines.append("Cycle: " + f" {arrow} ".join(cycle))
    if not graph.cycles:
        lines.append("Cycles: none")
    return lines
