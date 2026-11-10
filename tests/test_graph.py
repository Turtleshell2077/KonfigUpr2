"""Тесты этапа 3: построение графа обходом в глубину (DFS) с рекурсией."""

import unittest

from graph import GraphBuilder, package_name, summary_lines
from local_repo import TestRepository
from maven import RepositoryError

COMPLEX = {"A": "B C", "B": "D", "C": "D E", "D": "B F", "E": "F",
           "F": "G", "G": "E", "H": "A"}


def repo(packages):
    """Тестовый репозиторий в памяти: {"A": "B C", "B": ""}."""
    return TestRepository("memory", {name: deps.split()
                                     for name, deps in packages.items()})


def build(packages, root="A", text_filter=""):
    """Строит граф по описанию пакетов."""
    return GraphBuilder(repo(packages), text_filter).build(root)


def chain(length):
    """Цепочка пакетов N0 -> N1 -> ... длиной length."""
    names = [f"N{index}" for index in range(length)]
    packages = dict(zip(names, names[1:]))
    packages[names[-1]] = ""
    return packages


class CountingRepository:
    """Репозиторий, который считает запросы зависимостей."""

    def __init__(self, packages):
        """Запоминает пакеты: {пакет: [зависимости]}."""
        self.packages = packages
        self.calls = []

    def dependencies(self, node):
        """Зависимости пакета; запрос запоминается."""
        self.calls.append(node)
        return self.packages[node]


class DfsTest(unittest.TestCase):
    """Обход в глубину: порядок, общие пакеты, транзитивность."""

    def test_package_name(self):
        """Имя пакета — без версии."""
        self.assertEqual(package_name("org.slf4j:slf4j-api:2.0.16"),
                         "org.slf4j:slf4j-api")
        self.assertEqual(package_name("ABC"), "ABC")

    def test_dfs_order(self):
        """Сначала до конца одна ветка, потом следующая (в глубину)."""
        graph = build({"A": "B C", "B": "D", "C": "D E", "D": "", "E": ""})
        self.assertEqual(graph.edges, {"A": ["B", "C"], "B": ["D"],
                                       "D": [], "C": ["D", "E"], "E": []})
        self.assertEqual(list(graph.edges), ["A", "B", "D", "C", "E"])
        self.assertEqual(graph.cycles, [])

    def test_transitive(self):
        """В граф попадают зависимости зависимостей на любой глубине."""
        graph = build(chain(30), root="N0")
        self.assertEqual(len(graph.edges), 30)
        self.assertEqual(graph.edge_count(), 29)

    def test_each_package_once(self):
        """Общая зависимость запрашивается из репозитория один раз."""
        repository = CountingRepository({"A": ["B", "C"], "B": ["D"],
                                         "C": ["D"], "D": []})
        GraphBuilder(repository, "").build("A")
        self.assertEqual(repository.calls, ["A", "B", "D", "C"])

    def test_duplicates_removed(self):
        """Повтор одной зависимости даёт одно ребро."""
        repository = CountingRepository({"A": ["B", "B"], "B": []})
        graph = GraphBuilder(repository, "").build("A")
        self.assertEqual(graph.edges["A"], ["B"])

    def test_not_reachable(self):
        """Пакеты, до которых не дойти от начального, не попадают в граф."""
        graph = build(COMPLEX)
        self.assertNotIn("H", graph.edges)
        self.assertEqual(len(graph.edges), 7)

    def test_deep_graph(self):
        """Очень глубокий граф: рекурсия упирается в предел Python."""
        self.assertEqual(len(build(chain(300), root="N0").edges), 300)
        with self.assertRaises(RecursionError):
            build(chain(5000), root="N0")


class CycleTest(unittest.TestCase):
    """Циклические зависимости."""

    def test_cycle(self):
        """Цикл из трёх пакетов: обход заканчивается, цикл найден."""
        graph = build({"A": "B", "B": "C", "C": "A D", "D": ""})
        self.assertEqual(graph.cycles, [["A", "B", "C", "A"]])
        self.assertEqual(graph.edges["C"], ["A", "D"])

    def test_self_loop(self):
        """Пакет зависит сам от себя."""
        graph = build({"A": "A B", "B": ""})
        self.assertEqual(graph.cycles, [["A", "A"]])
        self.assertEqual(graph.edges, {"A": ["A", "B"], "B": []})

    def test_two_cycles(self):
        """Два цикла в одном графе и общие пакеты."""
        graph = build(COMPLEX)
        self.assertEqual(graph.cycles, [["B", "D", "B"],
                                        ["F", "G", "E", "F"]])
        self.assertEqual(graph.edge_count(), 10)

    def test_start_inside_cycle(self):
        """Обход можно начать с пакета внутри цикла."""
        graph = build(COMPLEX, root="D")
        self.assertEqual(list(graph.edges), ["D", "B", "F", "G", "E"])
        self.assertEqual(graph.cycles[0], ["D", "B", "D"])


class FilterTest(unittest.TestCase):
    """Пакеты с подстрокой фильтра в имени не учитываются."""

    def test_filter(self):
        """Пакет D не анализируется, его зависимости тоже не попадают."""
        graph = build({"A": "B C", "B": "D", "C": "D E", "D": "F",
                       "E": "", "F": ""}, text_filter="D")
        self.assertEqual(graph.edges, {"A": ["B", "C"], "B": [],
                                       "C": ["E"], "E": []})
        self.assertEqual(graph.skipped, ["D"])

    def test_filter_breaks_cycle(self):
        """Если отфильтрован пакет из цикла, цикла больше нет."""
        graph = build({"A": "B", "B": "C", "C": "A"}, text_filter="C")
        self.assertEqual(graph.cycles, [])
        self.assertEqual(list(graph.edges), ["A", "B"])

    def test_substring(self):
        """Фильтр — это подстрока имени, а не имя целиком."""
        graph = build({"A": "BA CD", "BA": "", "CD": ""}, text_filter="B")
        self.assertEqual(graph.edges["A"], ["CD"])

    def test_empty_filter(self):
        """Пустой фильтр ничего не убирает."""
        self.assertEqual(build({"A": "B", "B": ""}).skipped, [])

    def test_name_without_version(self):
        """У пакетов Maven фильтр проверяет имя, а не версию."""
        repository = CountingRepository({
            "a:app:1.0": ["x.y:lib:1.0", "x.y:test-kit:2.0"],
            "x.y:lib:1.0": [], "x.y:test-kit:2.0": []})
        graph = GraphBuilder(repository, "1.0").build("a:app:1.0")
        self.assertIn("x.y:lib:1.0", graph.edges)
        graph = GraphBuilder(repository, "test").build("a:app:1.0")
        self.assertEqual(graph.skipped, ["x.y:test-kit:2.0"])


class ErrorTest(unittest.TestCase):
    """Пакеты, которых нет в репозитории."""

    def test_missing_dependency(self):
        """Нет зависимости: предупреждение, граф всё равно строится."""
        graph = build({"A": "B X", "B": ""})
        self.assertEqual(graph.edges, {"A": ["B", "X"], "B": [], "X": []})
        self.assertIn("package 'X' not found", graph.errors["X"])

    def test_missing_root(self):
        """Нет начального пакета: это ошибка."""
        with self.assertRaises(RepositoryError):
            build({"A": ""}, root="Z")


class SummaryTest(unittest.TestCase):
    """Итог обхода, который печатается после текста D2."""

    def test_summary(self):
        """Число пакетов и рёбер, найденный цикл."""
        graph = build({"A": "B C", "B": "C", "C": "B"})
        self.assertEqual(summary_lines(graph), [
            "Packages: 3, dependencies: 4", "Cycle: B -> C -> B"])

    def test_summary_with_filter(self):
        """Отфильтрованные пакеты и «Cycles: none»."""
        graph = build({"A": "B C", "B": "", "C": ""}, text_filter="C")
        self.assertEqual(summary_lines(graph), [
            "Packages: 2, dependencies: 1", "Skipped by filter 'C':",
            "  C", "Cycles: none"])


if __name__ == "__main__":
    unittest.main()
