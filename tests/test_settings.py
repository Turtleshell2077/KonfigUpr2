"""Тесты этапа 1: чтение и проверка параметров из YAML-файла."""

import os
import pathlib
import tempfile
import unittest

import yaml

from settings import ConfigError, load_settings

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEST_REPO = str(ROOT / "examples" / "test_repos" / "simple.txt")
REAL = {"package": "org.slf4j:slf4j-api",
        "repository": "https://repo1.maven.org/maven2/",
        "test_mode": False, "version": "2.0.16",
        "output": "graph.png", "filter": ""}
TEST = {**REAL, "package": "A", "repository": TEST_REPO, "test_mode": True,
        "version": "1.0"}
TEXT = ("package: org.slf4j:slf4j-api\n"
        "repository: https://repo1.maven.org/maven2/\n"
        "output: graph.png\n")


class ConfigTestCase(unittest.TestCase):
    """Общая часть тестов: конфиги пишутся во временную папку."""

    def setUp(self):
        """Создаёт временную папку для конфигов."""
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.folder = pathlib.Path(folder.name)

    def load_text(self, text):
        """Записывает текст в конфиг и читает его."""
        path = self.folder / "config.yaml"
        path.write_text(text, encoding="utf-8")
        return load_settings(str(path))

    def load(self, data):
        """Записывает словарь в конфиг (YAML) и читает его."""
        return self.load_text(yaml.safe_dump(data))

    def errors(self, data):
        """Читает конфиг, который должен быть с ошибкой; список сообщений."""
        with self.assertRaises(ConfigError) as caught:
            self.load(data)
        return caught.exception.messages

    def text_errors(self, text):
        """То же, что errors, но конфиг задан готовым текстом."""
        with self.assertRaises(ConfigError) as caught:
            self.load_text(text)
        return caught.exception.messages

    def assert_error(self, data, key, text):
        """Проверяет, что есть ровно одна ошибка, и она у параметра key."""
        messages = self.errors(data)
        self.assertEqual(len(messages), 1, messages)
        self.assertTrue(messages[0].startswith(f"{key}: "), messages)
        self.assertIn(text, messages[0])


class GoodConfigTest(ConfigTestCase):
    """Правильные конфиги."""

    def test_real_repository(self):
        """Все шесть параметров берутся из файла."""
        self.assertEqual(self.load(REAL), REAL)
        data = {**REAL, "output": str(self.folder / "deps.png"),
                "filter": "api"}
        self.assertEqual(self.load(data), data)

    def test_test_mode(self):
        """Тестовый режим: пакет из больших букв, путь к файлу."""
        self.assertEqual(self.load(TEST), TEST)
        settings = self.load({**TEST, "package": "ABC"})
        self.assertEqual(settings["package"], "ABC")

    def test_values_are_text(self):
        """Версия без кавычек остаётся строкой: 1.10 не становится 1.1."""
        for value in ("1.10", "2.0", "33"):
            with self.subTest(value=value):
                text = (f"{TEXT}test_mode: false\nversion: {value}\n"
                        "filter: x\n")
                self.assertEqual(self.load_text(text)["version"], value)

    def test_test_mode_words(self):
        """true и false можно писать в любом регистре."""
        self.assertIs(self.load({**TEST, "test_mode": "True"})["test_mode"],
                      True)
        self.assertIs(self.load({**REAL, "test_mode": "FALSE"})["test_mode"],
                      False)

    def test_empty_filter(self):
        """Пустой фильтр (filter: или filter: "") — фильтра нет."""
        for line in ("filter:", 'filter: ""'):
            with self.subTest(line=line):
                text = f"{TEXT}test_mode: false\nversion: 1.0\n{line}\n"
                self.assertEqual(self.load_text(text)["filter"], "")


class FileErrorTest(ConfigTestCase):
    """Ошибки самого файла: нет файла, не YAML, не те ключи."""

    def test_missing_file(self):
        """Нет файла конфига."""
        with self.assertRaises(ConfigError) as caught:
            load_settings(str(self.folder / "nope.yaml"))
        self.assertIn("cannot read the file", caught.exception.messages[0])

    def test_invalid_yaml(self):
        """Файл не является YAML."""
        messages = self.text_errors("package: [a\nrepository: b\n")
        self.assertIn("invalid YAML", messages[0])

    def test_not_pairs(self):
        """В файле список, а не пары «ключ: значение»."""
        messages = self.text_errors("- package\n- repository\n")
        self.assertIn("'key: value' pairs", messages[0])

    def test_empty_file(self):
        """Пустой файл: нет ни одного параметра."""
        self.assertEqual(self.text_errors(""), [
            f"{key}: the key is required" for key in REAL])

    def test_missing_key(self):
        """Каждый из шести параметров обязателен."""
        for key in REAL:
            with self.subTest(key=key):
                data = {name: REAL[name] for name in REAL if name != key}
                self.assertIn(f"{key}: the key is required",
                              self.errors(data))

    def test_unknown_key(self):
        """Опечатка в имени ключа."""
        data = {**REAL, "pakage": "x"}
        self.assertEqual(self.errors(data), ["unknown key 'pakage'"])

    def test_many_errors(self):
        """Если ошибок несколько, сообщаются все сразу."""
        data = {**REAL, "package": "guava", "repository": "ftp://x",
                "version": "1 0", "output": "nope/a.png", "filter": ["a"]}
        keys = [message.split(":")[0] for message in self.errors(data)]
        self.assertEqual(keys, ["package", "repository", "version",
                                "output", "filter"])


class ParameterErrorTest(ConfigTestCase):
    """Ошибки в значениях каждого параметра."""

    def test_package(self):
        """Имя пакета для настоящего репозитория: groupId:artifactId."""
        for value in ("slf4j-api", "a:b:c", "org slf4j:api", ":api", 123):
            with self.subTest(value=value):
                self.assert_error({**REAL, "package": value}, "package",
                                  "groupId:artifactId")
        self.assert_error({**REAL, "package": ""}, "package",
                          "the value is empty")

    def test_test_package(self):
        """В тестовом режиме пакеты называются большими буквами."""
        for value in ("a", "A1", "org.slf4j:slf4j-api", "Б"):
            with self.subTest(value=value):
                self.assert_error({**TEST, "package": value}, "package",
                                  "capital Latin letters")

    def test_repository_url(self):
        """Для настоящего репозитория нужен адрес http:// или https://."""
        for value in ("repo1.maven.org/maven2", "ftp://repo1.maven.org",
                      "https://", TEST_REPO):
            with self.subTest(value=value):
                self.assert_error({**REAL, "repository": value},
                                  "repository", "is not an http(s) URL")
        self.assert_error({**REAL, "repository": ["a"]}, "repository",
                          "not a list")

    def test_test_repository(self):
        """В тестовом режиме нужен путь к существующему файлу."""
        missing = str(self.folder / "nope.txt")
        self.assert_error({**TEST, "repository": missing}, "repository",
                          "not found")
        self.assert_error({**TEST, "repository": str(self.folder)},
                          "repository", "is not a file")
        self.assert_error({**TEST, "repository": REAL["repository"]},
                          "repository", "not found")

    def test_test_mode(self):
        """Режим тестового репозитория: только true или false."""
        for value in ("maybe", 1, "yes", "", ["true"]):
            with self.subTest(value=value):
                self.assert_error({**REAL, "test_mode": value},
                                  "test_mode", "must be true or false")

    def test_bad_test_mode_skips_other_checks(self):
        """Без верного режима не ясно, как проверять пакет и репозиторий."""
        data = {**REAL, "package": "x", "repository": "y",
                "test_mode": "maybe"}
        self.assertEqual(self.errors(data),
                         ["test_mode: 'maybe': must be true or false"])

    def test_version(self):
        """Версия: буквы, цифры и знаки . - _ +"""
        for value in ("1 0", "-1", "1.0/2", "2.0 beta"):
            with self.subTest(value=value):
                self.assert_error({**REAL, "version": value}, "version",
                                  "is not a valid version")
        self.assert_error({**REAL, "version": ""}, "version",
                          "the value is empty")
        self.assert_error({**TEST, "version": " "}, "version",
                          "the value is empty")

    def test_output(self):
        """Имя файла картинки: не пустое, не папка, папка для него есть."""
        cases = (("", "the value is empty"), ({"a": "b"}, "not a list"),
                 ("no_such_folder/graph.png", "does not exist"),
                 (str(self.folder), "is a folder"))
        for value, text in cases:
            with self.subTest(value=value):
                self.assert_error({**REAL, "output": value}, "output", text)

    def test_filter(self):
        """Подстрока фильтра — одна строка, а не список."""
        for value in (["a", "b"], {"a": "b"}):
            with self.subTest(value=value):
                self.assert_error({**REAL, "filter": value}, "filter",
                                  "not a list")


class ExamplesTest(unittest.TestCase):
    """Примеры конфигов из репозитория (пути в них — от корня проекта)."""

    def setUp(self):
        """Переходит в корень проекта, после теста возвращается обратно."""
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(ROOT)

    def test_good_examples(self):
        """config.yaml, examples/*.yaml и test_mode/*.yaml без ошибок."""
        paths = ["config.yaml", *sorted(ROOT.glob("examples/*.yaml")),
                 *sorted(ROOT.glob("examples/test_mode/*.yaml"))]
        for path in paths:
            with self.subTest(path=path):
                self.assertIn("package", load_settings(str(path)))

    def test_repository_error_examples(self):
        """В examples/repo_errors/ конфиги верные: ошибка будет в сети."""
        paths = sorted(ROOT.glob("examples/repo_errors/*.yaml"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.name):
                self.assertIn("package", load_settings(str(path)))

    def test_error_examples(self):
        """Каждый конфиг из examples/errors/ даёт ошибку."""
        paths = sorted(ROOT.glob("examples/errors/*.yaml"))
        self.assertTrue(paths)
        for path in paths:
            with self.subTest(path=path.name):
                with self.assertRaises(ConfigError):
                    load_settings(str(path))


if __name__ == "__main__":
    unittest.main()
