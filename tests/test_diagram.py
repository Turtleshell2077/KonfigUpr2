"""Тесты этапа 5: текст графа на языке D2 и сохранение картинки PNG."""

import pathlib
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from diagram import (D2_COMMAND, DiagramError, d2_text, quote, render_png,
                     save_png)
from graph import GraphBuilder
from local_repo import TestRepository

PNG = b"\x89PNG\r\n\x1a\n"
SPRING = "org.springframework:spring-context:6.1.12"
CORE = "org.springframework:spring-core:6.1.12"


def build(packages, root="A", text_filter=""):
    """Граф по описанию пакетов: {"A": "B C", "B": ""}."""
    repository = TestRepository("memory", {
        name: deps.split() for name, deps in packages.items()})
    return GraphBuilder(repository, text_filter).build(root)


def finished(code=0, stdout=b"", stderr=b""):
    """Результат subprocess.run с заданным кодом и выводом."""
    return subprocess.CompletedProcess(D2_COMMAND, code, stdout, stderr)


class TextTest(unittest.TestCase):
    """Текст графа на языке D2."""

    def test_quote(self):
        """Имя в кавычках, кавычки и обратная косая черта экранируются."""
        self.assertEqual(quote(SPRING), f'"{SPRING}"')
        self.assertEqual(quote('a"b\\c'), '"a\\"b\\\\c"')

    def test_graph(self):
        """Сначала пакеты в порядке обхода, потом рёбра."""
        graph = build({"A": "B C", "B": "D", "C": "D", "D": ""})
        self.assertEqual(d2_text(graph).splitlines(), [
            '"A"', '"B"', '"D"', '"C"', '"A" -> "B"', '"A" -> "C"',
            '"B" -> "D"', '"C" -> "D"'])

    def test_one_package(self):
        """Пакет без зависимостей тоже есть на картинке."""
        self.assertEqual(d2_text(build({"A": ""})), '"A"\n')

    def test_cycle(self):
        """Ребро цикла записывается как обычное ребро."""
        graph = build({"A": "B", "B": "A"})
        self.assertIn('"B" -> "A"', d2_text(graph).splitlines())

    def test_self_loop(self):
        """Пакет, который зависит от себя: ребро в себя."""
        self.assertIn('"A" -> "A"', d2_text(build({"A": "A"})))

    def test_filter(self):
        """Отфильтрованного пакета в тексте нет."""
        graph = build({"A": "B C", "B": "", "C": ""}, text_filter="C")
        self.assertNotIn('"C"', d2_text(graph))

    def test_maven_names(self):
        """Имена Maven с точками и двоеточиями — в кавычках."""
        repository = mock.Mock()
        repository.dependencies.side_effect = lambda node: (
            [CORE] if node == SPRING else [])
        graph = GraphBuilder(repository, "").build(SPRING)
        self.assertEqual(d2_text(graph).splitlines()[-1],
                         f'"{SPRING}" -> "{CORE}"')


class RenderTest(unittest.TestCase):
    """Запуск программы d2 (подменён, d2 не нужен)."""

    def test_render(self):
        """Текст уходит в stdin, картинка PNG приходит из stdout."""
        with mock.patch("subprocess.run",
                        return_value=finished(stdout=PNG)) as run:
            self.assertEqual(render_png('"A"\n'), PNG)
        run.assert_called_once_with(D2_COMMAND, input=b'"A"\n',
                                    capture_output=True, check=False)
        self.assertIn("png", D2_COMMAND)

    def test_d2_not_installed(self):
        """Программы d2 нет: понятное сообщение."""
        with mock.patch("subprocess.run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(DiagramError, "d2 program is not"):
                render_png('"A"\n')

    def test_d2_failed(self):
        """d2 завершилась с ошибкой: её сообщение в одну строку."""
        result = finished(1, stderr=b"err: bad\n   syntax\n")
        with mock.patch("subprocess.run", return_value=result):
            with self.assertRaises(DiagramError) as caught:
                render_png("->\n")
        self.assertEqual(str(caught.exception), "d2 failed: err: bad syntax")

    def test_save(self):
        """Картинка записывается в файл."""
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / "graph.png"
            with mock.patch("subprocess.run",
                            return_value=finished(stdout=PNG)):
                save_png('"A"\n', str(path))
            self.assertEqual(path.read_bytes(), PNG)

    def test_cannot_write(self):
        """Файл нельзя записать: ошибка с именем файла."""
        with tempfile.TemporaryDirectory() as folder:
            path = str(pathlib.Path(folder) / "no_folder" / "graph.png")
            with mock.patch("subprocess.run",
                            return_value=finished(stdout=PNG)):
                with self.assertRaisesRegex(DiagramError, "cannot write"):
                    save_png('"A"\n', path)


@unittest.skipUnless(shutil.which("d2"), "d2 is not installed")
class RealD2Test(unittest.TestCase):
    """Настоящая программа d2 понимает текст (картинка SVG, без сети)."""

    def test_valid_d2(self):
        """d2 разбирает текст графа с циклом и именами Maven."""
        graph = build({"A": "B", "B": "A"})
        text = d2_text(graph) + f'"{SPRING}" -> "{CORE}"\n'
        result = subprocess.run(["d2", "-", "-"], input=text.encode(),
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(b"<svg", result.stdout)


if __name__ == "__main__":
    unittest.main()
