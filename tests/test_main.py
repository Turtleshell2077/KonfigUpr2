"""Тесты запуска программы: вывод графа, картинка и коды завершения."""

import contextlib
import io
import os
import pathlib
import string
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import main
from maven import RepositoryError

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "src" / "main.py"
CONFIG = str(ROOT / "config.yaml")
MAVEN = "https://repo1.maven.org/maven2/org/apache/commons/"
TEXT_POM = f"{MAVEN}commons-text/1.12.0/commons-text-1.12.0.pom"
LANG_POM = f"{MAVEN}commons-lang3/3.14.0/commons-lang3-3.14.0.pom"
TEXT_NODE = "org.apache.commons:commons-text:1.12.0"
LANG_NODE = "org.apache.commons:commons-lang3:3.14.0"
TEXT_XML = ("<project><dependencies><dependency>"
            "<groupId>org.apache.commons</groupId>"
            "<artifactId>commons-lang3</artifactId>"
            "<version>3.14.0</version></dependency><dependency>"
            "<groupId>junit</groupId><artifactId>junit</artifactId>"
            "<version>4.13</version><scope>test</scope>"
            "</dependency></dependencies></project>")
EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
PNG = b"\x89PNG\r\n\x1a\n"


def start_program(*args):
    """Запускает src/main.py как отдельную программу из корня проекта."""
    return subprocess.run(
        [sys.executable, str(PROGRAM), *args], capture_output=True,
        text=True, encoding="utf-8", cwd=ROOT,
        env=dict(os.environ, PYTHONUTF8="1"), timeout=60, check=False)


def run_main(*args):
    """Вызывает main.main и возвращает (код, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main.main(list(args))
    return code, out.getvalue(), err.getvalue()


def run_drawn(*args):
    """Как run_main, но вместо рисования картинки — заглушка save_png."""
    with mock.patch("main.save_png") as save:
        code, out, err = run_main(*args)
    return code, out, err, save


def letters(number):
    """Имя из больших букв по номеру: 0 -> A, 25 -> Z, 26 -> BA, ..."""
    name = ""
    while True:
        number, rest = divmod(number, len(string.ascii_uppercase))
        name = string.ascii_uppercase[rest] + name
        if not number:
            return name


def fake_download(files):
    """Поддельное скачивание: файлы берутся из словаря «адрес: текст»."""
    def download(url):
        """Отдаёт файл из словаря или сообщает, что его нет."""
        if url not in files:
            raise RepositoryError(f"not found: {url}")
        return files[url].encode("utf-8")
    return download


class MavenGraphTest(unittest.TestCase):
    """Граф для настоящего репозитория (сеть подменена словарём)."""

    def run_with(self, files):
        """Запускает программу с config.yaml и поддельной сетью."""
        with mock.patch("maven.download", fake_download(files)):
            return run_drawn("--config", CONFIG)

    def test_graph(self):
        """Текст D2 (junit для тестов не попадает в граф) и картинка."""
        code, out, err, save = self.run_with({TEXT_POM: TEXT_XML,
                                              LANG_POM: "<project/>"})
        self.assertEqual(code, EXIT_OK, err)
        edge = f'"{TEXT_NODE}" -> "{LANG_NODE}"'
        self.assertEqual(out.splitlines(), [
            f"D2 code of the dependency graph of {TEXT_NODE}:",
            f'"{TEXT_NODE}"', f'"{LANG_NODE}"', edge,
            "Packages: 2, dependencies: 1", "Cycles: none",
            "PNG image saved to graph.png"])
        save.assert_called_once_with(
            f'"{TEXT_NODE}"\n"{LANG_NODE}"\n{edge}\n', "graph.png")

    def test_dependency_not_found(self):
        """Нет POM зависимости: предупреждение, граф напечатан."""
        code, out, err, _ = self.run_with({TEXT_POM: TEXT_XML})
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Packages: 2, dependencies: 1", out)
        self.assertIn("Warning: cannot get dependencies of "
                      "org.apache.commons:commons-lang3:3.14.0", err)

    def test_package_not_found(self):
        """Нет самого пакета: сообщение в stderr и код 1."""
        code, out, err, save = self.run_with({})
        self.assertEqual(code, EXIT_ERROR)
        save.assert_not_called()
        self.assertEqual(out, "")
        self.assertEqual(err.strip(),
                         f"Repository error: not found: {TEXT_POM}")


class TestModeTest(unittest.TestCase):
    """Тестовый репозиторий."""

    def test_graph(self):
        """Граф с циклом: пакеты в порядке обхода, потом рёбра."""
        code, out, err, save = run_drawn(
            "-c", "examples/test_mode/cycle.yaml")
        self.assertEqual(code, EXIT_OK, err)
        self.assertEqual(out.splitlines(), [
            "D2 code of the dependency graph of A:", '"A"', '"B"', '"C"',
            '"D"', '"A" -> "B"', '"B" -> "C"', '"C" -> "A"', '"C" -> "D"',
            "Packages: 4, dependencies: 4", "Cycle: A -> B -> C -> A",
            "PNG image saved to test_graph.png"])
        self.assertEqual(save.call_args.args[1], "test_graph.png")

    def test_filter(self):
        """Фильтр из конфига: пакета D нет в тексте D2."""
        _, out, _, save = run_drawn("-c", "examples/test_mode/filter.yaml")
        self.assertIn("Skipped by filter 'D':\n  D\n", out)
        self.assertNotIn('"D"', save.call_args.args[0])

    def test_errors(self):
        """Нет начального пакета или ошибка в файле: код 1."""
        for name, text in (("no_root", "package 'Z' not found"),
                           ("bad_name", "line 2: 'c' is not a name"),
                           ("bad_line", "line 3: expected")):
            with self.subTest(name=name):
                result = start_program(
                    "-c", f"examples/test_mode/{name}.yaml")
                self.assertEqual(result.returncode, EXIT_ERROR)
                self.assertIn("Repository error:", result.stderr)
                self.assertIn(text, result.stderr)

    def test_too_deep(self):
        """Слишком глубокий граф: понятное сообщение вместо падения."""
        with tempfile.TemporaryDirectory() as folder:
            names = [letters(number) for number in range(3000)]
            repo = pathlib.Path(folder) / "deep.txt"
            repo.write_text("".join(f"{name}: {next_name}\n" for name,
                                    next_name in zip(names, names[1:])),
                            encoding="utf-8")
            config = pathlib.Path(folder) / "config.yaml"
            config.write_text(
                f"package: {names[0]}\nrepository: {repo}\n"
                "test_mode: true\nversion: 1.0\noutput: graph.png\n"
                "filter: ''\n", encoding="utf-8")
            code, _, err = run_main("--config", str(config))
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn("too deep for recursive DFS", err)


class ImageTest(unittest.TestCase):
    """Сохранение картинки (программа d2 подменена)."""

    def write_config(self, folder, output):
        """Конфиг для simple.txt с картинкой output, возвращает путь."""
        config = pathlib.Path(folder) / "config.yaml"
        repo = ROOT / "examples" / "test_repos" / "simple.txt"
        config.write_text(
            f"package: A\nrepository: '{repo}'\ntest_mode: true\n"
            f"version: 1.0\noutput: '{output}'\nfilter: ''\n",
            encoding="utf-8")
        return str(config)

    def test_png_saved(self):
        """Картинка от d2 записана в файл из параметра output."""
        with tempfile.TemporaryDirectory() as folder:
            image = pathlib.Path(folder) / "graph.png"
            done = subprocess.CompletedProcess([], EXIT_OK, PNG, b"")
            with mock.patch("subprocess.run", return_value=done):
                code, out, err = run_main(
                    "-c", self.write_config(folder, image))
            self.assertEqual(code, EXIT_OK, err)
            self.assertEqual(image.read_bytes(), PNG)
        self.assertIn(f"PNG image saved to {image}", out)

    def test_no_d2(self):
        """Нет программы d2: текст D2 напечатан, ошибка и код 1."""
        with tempfile.TemporaryDirectory() as folder:
            config = self.write_config(folder, "graph.png")
            with mock.patch("subprocess.run",
                            side_effect=FileNotFoundError):
                code, out, err = run_main("-c", config)
        self.assertEqual(code, EXIT_ERROR)
        self.assertIn('"A" -> "B"', out)
        self.assertIn("Image error: the d2 program is not found", err)


class ProgramTest(unittest.TestCase):
    """Ошибки конфига и командной строки."""

    def test_config_error(self):
        """Ошибка в конфиге: сообщения в stderr, код 1."""
        result = start_program("--config",
                               "examples/errors/many_errors.yaml")
        self.assertEqual(result.returncode, EXIT_ERROR)
        self.assertEqual(result.stdout, "")
        lines = result.stderr.splitlines()
        self.assertIn("Config error in", lines[0])
        self.assertIn("  unknown key 'color'", lines)

    def test_missing_config(self):
        """Нет файла конфига: код 1."""
        result = start_program("--config", "nope.yaml")
        self.assertEqual(result.returncode, EXIT_ERROR)
        self.assertIn("cannot read the file", result.stderr)

    def test_unknown_option(self):
        """Неизвестный параметр командной строки: код 2."""
        result = start_program("--unknown")
        self.assertEqual(result.returncode, EXIT_USAGE)
        self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
