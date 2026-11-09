"""Тесты запуска программы: вывод параметров и коды завершения."""

import contextlib
import io
import os
import pathlib
import subprocess
import sys
import unittest

import main

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROGRAM = ROOT / "src" / "main.py"
EXIT_OK = 0
EXIT_CONFIG_ERROR = 1
EXIT_USAGE = 2


def start_program(*args):
    """Запускает src/main.py как отдельную программу из корня проекта."""
    return subprocess.run(
        [sys.executable, str(PROGRAM), *args], capture_output=True,
        text=True, encoding="utf-8", cwd=ROOT,
        env=dict(os.environ, PYTHONUTF8="1"), timeout=60, check=False)


class MainTest(unittest.TestCase):
    """Программа целиком."""

    def test_default_config(self):
        """Без --config читается config.yaml и печатаются все параметры."""
        result = start_program()
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(lines[0], "Settings from 'config.yaml':")
        self.assertEqual(lines[1:], [
            "  package: org.apache.commons:commons-text",
            "  repository: https://repo1.maven.org/maven2/",
            "  test_mode: false", "  version: 1.12.0",
            "  output: graph.png", '  filter: ""'])

    def test_test_mode_config(self):
        """Конфиг тестового режима из примеров."""
        result = start_program("-c", "examples/test_mode.yaml")
        self.assertEqual(result.returncode, EXIT_OK, result.stderr)
        self.assertIn("  test_mode: true", result.stdout)
        self.assertIn("  repository: examples/test_repo.txt", result.stdout)

    def test_config_error(self):
        """Ошибка в конфиге: сообщения в stderr, код 1, параметров нет."""
        result = start_program("--config",
                               "examples/errors/many_errors.yaml")
        self.assertEqual(result.returncode, EXIT_CONFIG_ERROR)
        self.assertEqual(result.stdout, "")
        lines = result.stderr.splitlines()
        self.assertIn("Config error in", lines[0])
        self.assertIn("  unknown key 'color'", lines)

    def test_missing_config(self):
        """Нет файла конфига: код 1."""
        result = start_program("--config", "nope.yaml")
        self.assertEqual(result.returncode, EXIT_CONFIG_ERROR)
        self.assertIn("cannot read the file", result.stderr)

    def test_unknown_option(self):
        """Неизвестный параметр командной строки: код 2."""
        result = start_program("--unknown")
        self.assertEqual(result.returncode, EXIT_USAGE)
        self.assertIn("usage:", result.stderr)

    def test_main_function(self):
        """Функция main возвращает код завершения и печатает параметры."""
        out = io.StringIO()
        config = str(ROOT / "examples" / "codec.yaml")
        with contextlib.redirect_stdout(out):
            code = main.main(["--config", config])
        self.assertEqual(code, EXIT_OK)
        self.assertIn("  version: 1.10", out.getvalue())


if __name__ == "__main__":
    unittest.main()
