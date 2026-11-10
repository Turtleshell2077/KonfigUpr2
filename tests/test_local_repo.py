"""Тесты этапа 3: чтение файла тестового репозитория."""

import pathlib
import tempfile
import unittest

from local_repo import TestRepository
from maven import RepositoryError

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPOS = ROOT / "examples" / "test_repos"


class LoadTest(unittest.TestCase):
    """Разбор файла: правильные строки и ошибки."""

    def setUp(self):
        """Создаёт временную папку для файлов."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.path = pathlib.Path(folder.name) / "repo.txt"

    def load(self, text):
        """Записывает текст в файл и читает его как репозиторий."""
        self.path.write_text(text, encoding="utf-8")
        return TestRepository.load(str(self.path))

    def error(self, text):
        """Текст ошибки при чтении файла."""
        with self.assertRaises(RepositoryError) as caught:
            self.load(text)
        return str(caught.exception)

    def test_packages(self):
        """Пакеты, зависимости, пустые строки и комментарии."""
        repository = self.load("# comment\n\nA: B C\n  B:D  \nC:\nD:\n")
        self.assertEqual(repository.packages, {
            "A": ["B", "C"], "B": ["D"], "C": [], "D": []})

    def test_long_names(self):
        """Имя может состоять из нескольких больших букв."""
        repository = self.load("ABC: XYZ\nXYZ:\n")
        self.assertEqual(repository.dependencies("ABC"), ["XYZ"])

    def test_repeated_dependency(self):
        """Повтор зависимости в строке записывается один раз."""
        self.assertEqual(self.load("A: B B C B\n").packages["A"],
                         ["B", "C"])

    def test_dependencies_copy(self):
        """dependencies возвращает копию: изменение не портит репозиторий."""
        repository = self.load("A: B\nB:\n")
        repository.dependencies("A").append("Z")
        self.assertEqual(repository.dependencies("A"), ["B"])

    def test_missing_package(self):
        """Пакета нет в файле."""
        repository = self.load("A: B\n")
        with self.assertRaises(RepositoryError) as caught:
            repository.dependencies("B")
        self.assertIn("package 'B' not found", str(caught.exception))

    def test_no_colon(self):
        """В строке нет двоеточия; в сообщении номер строки."""
        message = self.error("A: B\nB C\n")
        self.assertIn("line 2: expected 'PACKAGE: DEPENDENCIES'", message)

    def test_bad_names(self):
        """Имена только из больших латинских букв."""
        for text, name in (("a: B", "a"), ("A: b", "b"), ("A: B1", "B1"),
                           (": B", ""), ("A: Б", "Б"), ("A-B: C", "A-B")):
            with self.subTest(text=text):
                self.assertIn(f"line 1: '{name}' is not a name",
                              self.error(text))

    def test_described_twice(self):
        """Один пакет описан два раза."""
        self.assertIn("line 3: package 'A' is described twice",
                      self.error("A: B\nB:\nA: C\n"))

    def test_file_errors(self):
        """Нет файла или файл не в UTF-8."""
        with self.assertRaises(RepositoryError) as caught:
            TestRepository.load(str(self.path))
        self.assertIn("cannot read", str(caught.exception))
        self.path.write_bytes(b"A: \xff\n")
        with self.assertRaises(RepositoryError) as caught:
            TestRepository.load(str(self.path))
        self.assertIn("not UTF-8", str(caught.exception))


class ExamplesTest(unittest.TestCase):
    """Файлы из examples/test_repos/."""

    def test_good_files(self):
        """Правильные файлы читаются."""
        for name in ("simple", "cycle", "self_loop", "complex", "missing"):
            with self.subTest(name=name):
                repository = TestRepository.load(str(REPOS / f"{name}.txt"))
                self.assertIn("A", repository.packages)

    def test_bad_files(self):
        """Файлы с ошибками дают RepositoryError."""
        for path in sorted(REPOS.glob("bad_*.txt")):
            with self.subTest(path=path.name):
                with self.assertRaises(RepositoryError):
                    TestRepository.load(str(path))


if __name__ == "__main__":
    unittest.main()
