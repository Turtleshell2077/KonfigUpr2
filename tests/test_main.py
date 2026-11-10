"""Тесты запуска программы: вывод графа и коды завершения."""

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
            return run_main("--config", CONFIG)

    def test_graph(self):
        """Тестовая зависимость junit не попадает в граф."""
        code, out, err = self.run_with({TEXT_POM: TEXT_XML,
                                        LANG_POM: "<project/>"})
        self.assertEqual(code, EXIT_OK, err)
        self.assertEqual(out.splitlines(), [
            "Dependency graph of org.apache.commons:commons-text:1.12.0:",
            "  1. org.apache.commons:commons-text:1.12.0",
            "       -> org.apache.commons:commons-lang3:3.14.0",
            "  2. org.apache.commons:commons-lang3:3.14.0",
            "Packages: 2, dependencies: 1", "Cycles: none"])

    def test_dependency_not_found(self):
        """Нет POM зависимости: предупреждение, граф напечатан."""
        code, out, err = self.run_with({TEXT_POM: TEXT_XML})
        self.assertEqual(code, EXIT_OK)
        self.assertIn("Packages: 2, dependencies: 1", out)
        self.assertIn("Warning: cannot get dependencies of "
                      "org.apache.commons:commons-lang3:3.14.0", err)

    def test_package_not_found(self):
        """Нет самого пакета: сообщение в stderr и код 1."""
        code, out, err = self.run_with({})
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertEqual(err.strip(),
                         f"Repository error: not found: {TEXT_POM}")


class TestModeTest(unittest.TestCase):
    """Тестовый репозиторий (программа запускается целиком)."""

    def test_graph(self):
        """Граф из файла: порядок обхода и рёбра."""
        result = start_program("-c", "examples/test_mode/cycle.yaml")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertEqual(result.stdout.splitlines(), [
            "Dependency graph of A:", "  1. A", "       -> B", "  2. B",
            "       -> C", "  3. C", "       -> A", "       -> D", "  4. D",
            "Packages: 4, dependencies: 4", "Cycle: A -> B -> C -> A"])

    def test_filter(self):
        """Фильтр из конфига."""
        result = start_program("-c", "examples/test_mode/filter.yaml")
        self.assertIn("Skipped by filter 'D':\n  D\n", result.stdout)

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
