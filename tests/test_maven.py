"""Тесты этапа 2: разбор POM-файлов и прямые зависимости (без сети)."""

import pathlib
import tempfile
import unittest
import urllib.error
from http import HTTPStatus
from unittest import mock

import maven
from maven import Dependency, MavenRepository, RepositoryError

REPO = "https://repo.test/maven2"


def pom(body, parent=None):
    """Текст POM-файла: тело внутри <project> и, если нужно, <parent>."""
    parent_xml = ""
    if parent:
        group, artifact, version = parent.split(":")
        parent_xml = (f"<parent><groupId>{group}</groupId>"
                      f"<artifactId>{artifact}</artifactId>"
                      f"<version>{version}</version></parent>")
    return ('<project xmlns="http://maven.apache.org/POM/4.0.0">'
            f"{parent_xml}{body}</project>")


def dep(package, **extra):
    """XML одной зависимости; package — group:artifact[:version]."""
    group, artifact, *version = package.split(":")
    tags = {"groupId": group, "artifactId": artifact,
            "version": version[0] if version else None, **extra}
    inner = "".join(f"<{tag}>{value}</{tag}>"
                    for tag, value in tags.items() if value is not None)
    return f"<dependency>{inner}</dependency>"


def deps(*items):
    """Раздел <dependencies> из нескольких зависимостей."""
    return f"<dependencies>{''.join(items)}</dependencies>"


def managed(*items):
    """Раздел <dependencyManagement> из нескольких зависимостей."""
    return f"<dependencyManagement>{deps(*items)}</dependencyManagement>"


def props(**values):
    """Раздел <properties>; точки в именах записываются как __."""
    inner = "".join(f"<{name.replace('__', '.')}>{value}"
                    f"</{name.replace('__', '.')}>"
                    for name, value in values.items())
    return f"<properties>{inner}</properties>"


class FakeRepositoryTestCase(unittest.TestCase):
    """Общая часть: вместо скачивания файлы берутся из словаря."""

    def setUp(self):
        """Подменяет maven.download поддельным репозиторием."""
        self.files = {}
        self.calls = []
        patcher = mock.patch("maven.download", side_effect=self.fake_download)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repository = MavenRepository(REPO + "/")

    def fake_download(self, url):
        """Отдаёт файл из словаря или сообщает, что его нет."""
        self.calls.append(url)
        if url not in self.files:
            raise RepositoryError(f"not found: {url}")
        return self.files[url].encode("utf-8")

    def add(self, package, text):
        """Кладёт POM пакета group:artifact:version в репозиторий."""
        url = self.repository.pom_url(*package.split(":"))
        self.files[url] = text

    def direct(self, package):
        """Прямые зависимости пакета в виде строк."""
        found = self.repository.direct_dependencies(*package.split(":"))
        return [str(item) for item in found]

    def assert_fails(self, package, text):
        """Проверяет, что получение зависимостей даёт ошибку с text."""
        with self.assertRaises(RepositoryError) as caught:
            self.direct(package)
        self.assertIn(text, str(caught.exception))


class DirectDependenciesTest(FakeRepositoryTestCase):
    """Прямые зависимости из одного POM-файла."""

    def test_pom_url(self):
        """Адрес POM: группа через /, артефакт, версия, имя файла."""
        repository = MavenRepository("https://repo1.maven.org/maven2/")
        self.assertEqual(
            repository.pom_url("org.slf4j", "slf4j-api", "2.0.16"),
            "https://repo1.maven.org/maven2/org/slf4j/slf4j-api/2.0.16/"
            "slf4j-api-2.0.16.pom")

    def test_dependencies(self):
        """Версия, scope и optional берутся из POM."""
        self.add("a.b:app:1.0", pom(deps(
            dep("x.y:lib:2.0"), dep("x.y:tool:3.1", scope="test"),
            dep("x.y:extra:1", optional="true"))))
        self.assertEqual(self.direct("a.b:app:1.0"), [
            "x.y:lib:2.0 (compile)", "x.y:tool:3.1 (test)",
            "x.y:extra:1 (compile, optional)"])

    def test_only_project_dependencies(self):
        """Зависимости плагинов (<build>) не считаются зависимостями."""
        plugin = ("<build><plugins><plugin><artifactId>p</artifactId>"
                  f"{deps(dep('x.y:plugin-lib:1'))}</plugin></plugins>"
                  "</build>")
        self.add("a.b:app:1.0", pom(deps(dep("x.y:lib:2.0")) + plugin))
        self.assertEqual(self.direct("a.b:app:1.0"),
                         ["x.y:lib:2.0 (compile)"])

    def test_no_dependencies(self):
        """У пакета может не быть зависимостей."""
        self.add("a.b:app:1.0", pom("<artifactId>app</artifactId>"))
        self.assertEqual(self.direct("a.b:app:1.0"), [])

    def test_properties(self):
        """Свойства ${...} подставляются, в том числе вложенные."""
        body = (props(lib__version="${base}", base="2.5")
                + "<groupId>a.b</groupId><version>1.0</version>"
                + deps(dep("${project.groupId}:core:${project.version}"),
                       dep("x.y:lib:${lib.version}"),
                       dep("x.y:other:${nope}")))
        self.add("a.b:app:1.0", pom(body))
        self.assertEqual(self.direct("a.b:app:1.0"), [
            "a.b:core:1.0 (compile)", "x.y:lib:2.5 (compile)",
            "x.y:other:${nope} (compile)"])

    def test_version_not_found(self):
        """Если версию узнать неоткуда, вместо неё печатается ?."""
        self.add("a.b:app:1.0", pom(deps(dep("x.y:lib"))))
        self.assertEqual(self.direct("a.b:app:1.0"),
                         ["x.y:lib:? (compile)"])

    def test_cache(self):
        """Каждый POM-файл скачивается только один раз."""
        self.add("a.b:app:1.0", pom(deps(dep("x.y:lib:2.0"))))
        self.direct("a.b:app:1.0")
        self.direct("a.b:app:1.0")
        self.assertEqual(len(self.calls), 1)


class InheritanceTest(FakeRepositoryTestCase):
    """Родительские POM и импорт BOM."""

    def test_parent(self):
        """Версии из dependencyManagement родителя, его зависимости."""
        self.add("a.b:parent:7", pom(
            props(lib__version="1.0")
            + managed(dep("x.y:lib:${lib.version}"),
                      dep("x.y:tool:4.0", scope="test"))
            + deps(dep("junit:junit:4.13", scope="test"))))
        self.add("a.b:app:1.0", pom(
            props(lib__version="2.0") + "<artifactId>app</artifactId>"
            + deps(dep("x.y:lib"), dep("x.y:tool"),
                   dep("a.b:core:${project.version}")),
            parent="a.b:parent:7"))
        self.assertEqual(self.direct("a.b:app:1.0"), [
            "x.y:lib:2.0 (compile)", "x.y:tool:4.0 (test)",
            "a.b:core:7 (compile)", "junit:junit:4.13 (test)"])

    def test_bom_import(self):
        """Версии из BOM; правило, записанное прямо, важнее BOM."""
        self.add("x.y:bom:5", pom(managed(dep("x.y:lib:5.1"),
                                          dep("x.y:other:5.2"))))
        self.add("a.b:app:1.0", pom(
            managed(dep("x.y:bom:5", type="pom", scope="import"),
                    dep("x.y:other:9.0"))
            + deps(dep("x.y:lib"), dep("x.y:other"))))
        self.assertEqual(self.direct("a.b:app:1.0"), [
            "x.y:lib:5.1 (compile)", "x.y:other:9.0 (compile)"])

    def test_bom_imports_itself(self):
        """BOM, который импортирует сам себя, не зацикливает программу."""
        self.add("x.y:bom:5", pom(managed(
            dep("x.y:bom:5", type="pom", scope="import"),
            dep("x.y:lib:5.1"))))
        self.add("a.b:app:1.0", pom(
            managed(dep("x.y:bom:5", type="pom", scope="import"))
            + deps(dep("x.y:lib"))))
        self.assertEqual(self.direct("a.b:app:1.0"),
                         ["x.y:lib:5.1 (compile)"])

    def test_shared_parent_downloaded_once(self):
        """Общий родитель двух пакетов скачивается один раз."""
        self.add("a.b:parent:7", pom(""))
        self.add("a.b:one:1", pom("", parent="a.b:parent:7"))
        self.add("a.b:two:1", pom("", parent="a.b:parent:7"))
        self.direct("a.b:one:1")
        self.direct("a.b:two:1")
        self.assertEqual(len(self.calls), len(set(self.calls)))


class ErrorTest(FakeRepositoryTestCase):
    """Ошибки: нет файла, сломанный XML, неверные родители."""

    def test_package_not_found(self):
        """Пакета (или версии) нет в репозитории."""
        self.assert_fails("a.b:none:1.0", "not found")

    def test_parent_not_found(self):
        """Родительского POM нет в репозитории."""
        self.add("a.b:app:1.0", pom("", parent="a.b:parent:7"))
        self.assert_fails("a.b:app:1.0", "parent/7/parent-7.pom")

    def test_invalid_xml(self):
        """Скачанный файл — не XML."""
        self.add("a.b:app:1.0", "<project><dependencies>")
        self.assert_fails("a.b:app:1.0", "invalid XML")

    def test_not_a_pom(self):
        """Скачанный файл — XML, но не POM (например, HTML-страница)."""
        self.add("a.b:app:1.0", "<html><body>Not found</body></html>")
        self.assert_fails("a.b:app:1.0", "not a POM file")

    def test_parent_cycle(self):
        """Родители, которые ссылаются друг на друга."""
        self.add("a.b:app:1.0", pom("", parent="a.b:p1:1"))
        self.add("a.b:p1:1", pom("", parent="a.b:p2:1"))
        self.add("a.b:p2:1", pom("", parent="a.b:p1:1"))
        self.assert_fails("a.b:app:1.0", "cycle at a.b:p1:1")

    def test_incomplete_parent(self):
        """В <parent> нет версии."""
        self.add("a.b:app:1.0", pom(
            "<parent><groupId>a.b</groupId><artifactId>p</artifactId>"
            "</parent><artifactId>app</artifactId>"))
        self.assert_fails("a.b:app:1.0", "incomplete <parent>")


class DownloadTest(unittest.TestCase):
    """Скачивание файла и сообщения об ошибках сети."""

    def test_local_file(self):
        """urllib умеет читать и file://-адреса."""
        with tempfile.TemporaryDirectory() as folder:
            path = pathlib.Path(folder) / "a.pom"
            path.write_bytes(b"<project/>")
            self.assertEqual(maven.download(path.as_uri()), b"<project/>")
            with self.assertRaises(RepositoryError) as caught:
                maven.download((pathlib.Path(folder) / "b.pom").as_uri())
            self.assertIn("cannot download", str(caught.exception))

    def check_error(self, error, text):
        """Подменяет urlopen ошибкой и проверяет сообщение."""
        with mock.patch("urllib.request.urlopen", side_effect=error):
            with self.assertRaises(RepositoryError) as caught:
                maven.download("https://repo.test/a.pom")
        self.assertIn(text, str(caught.exception))

    def test_http_errors(self):
        """404 — файла нет; другие коды — ошибка HTTP."""
        url = "https://repo.test/a.pom"
        self.check_error(urllib.error.HTTPError(
            url, HTTPStatus.NOT_FOUND, "Not Found", None, None),
            "not found: https://repo.test/a.pom")
        self.check_error(urllib.error.HTTPError(
            url, HTTPStatus.INTERNAL_SERVER_ERROR, "Error", None, None),
            "HTTP error 500")

    def test_network_error(self):
        """Нет сети или неверный адрес сервера."""
        self.check_error(urllib.error.URLError("no network"),
                         "cannot download https://repo.test/a.pom: "
                         "no network")


class DependencyTest(unittest.TestCase):
    """Строковый вид зависимости."""

    def test_str(self):
        """groupId:artifactId:версия (scope[, optional])."""
        item = Dependency("x.y", "lib", "1.0")
        self.assertEqual(item.name, "x.y:lib")
        self.assertEqual(str(item), "x.y:lib:1.0 (compile)")
        item = Dependency("x.y", "lib", None, "runtime", True)
        self.assertEqual(str(item), "x.y:lib:? (runtime, optional)")


if __name__ == "__main__":
    unittest.main()
