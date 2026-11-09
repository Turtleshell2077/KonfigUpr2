"""Тесты запуска программы: вывод зависимостей и коды завершения."""

import contextlib
import io
import os
import pathlib
import subprocess
import sys
import unittest
from unittest import mock

import main
from maven import RepositoryError

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "src" / "main.py"
CONFIG = str(ROOT / "config.yaml")
TEXT_POM = ("https://repo1.maven.org/maven2/org/apache/commons/"
            "commons-text/1.12.0/commons-text-1.12.0.pom")
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


def fake_download(files):
    """Поддельное скачивание: файлы берутся из словаря «адрес: текст»."""
    def download(url):
        """Отдаёт файл из словаря или сообщает, что его нет."""
        if url not in files:
            raise RepositoryError(f"not found: {url}")
        return files[url].encode("utf-8")
    return download


class DependenciesOutputTest(unittest.TestCase):
    """Вывод прямых зависимостей (сеть подменена словарём)."""

    def test_prints_dependencies(self):
        """Печатается заголовок и по одной зависимости в строке."""
        text = ("<project><dependencies><dependency>"
                "<groupId>org.apache.commons</groupId>"
                "<artifactId>commons-lang3</artifactId>"
                "<version>3.14.0</version></dependency><dependency>"
                "<groupId>junit</groupId><artifactId>junit</artifactId>"
                "<version>4.13</version><scope>test</scope>"
                "</dependency></dependencies></project>")
        with mock.patch("maven.download",
                        fake_download({TEXT_POM: text})):
            code, out, _ = run_main("--config", CONFIG)
        self.assertEqual(code, EXIT_OK)
        self.assertEqual(out.splitlines(), [
            "Direct dependencies of org.apache.commons:commons-text:1.12.0:",
            "  org.apache.commons:commons-lang3:3.14.0 (compile)",
            "  junit:junit:4.13 (test)"])

    def test_no_dependencies(self):
        """Пакет без зависимостей."""
        with mock.patch("maven.download",
                        fake_download({TEXT_POM: "<project/>"})):
            code, out, _ = run_main("--config", CONFIG)
        self.assertEqual(code, EXIT_OK)
        self.assertIn("  (no dependencies)", out)

    def test_repository_error(self):
        """Пакета нет в репозитории: сообщение в stderr и код 1."""
        with mock.patch("maven.download", fake_download({})):
            code, out, err = run_main("--config", CONFIG)
        self.assertEqual(code, EXIT_ERROR)
        self.assertEqual(out, "")
        self.assertEqual(err.strip(),
                         f"Repository error: not found: {TEXT_POM}")


class ProgramTest(unittest.TestCase):
    """Программа целиком (без обращения к сети)."""

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

    def test_test_mode(self):
        """Тестовый репозиторий на этом этапе ещё не поддерживается."""
        result = start_program("-c", "examples/test_mode.yaml")
        self.assertEqual(result.returncode, EXIT_ERROR)
        self.assertIn("test repository mode is not supported yet",
                      result.stderr)

    def test_unknown_option(self):
        """Неизвестный параметр командной строки: код 2."""
        result = start_program("--unknown")
        self.assertEqual(result.returncode, EXIT_USAGE)
        self.assertIn("usage:", result.stderr)


if __name__ == "__main__":
    unittest.main()
