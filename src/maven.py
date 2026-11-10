"""Получение прямых зависимостей пакета из репозитория Maven.

Описание пакета лежит в POM-файле (XML) по адресу
<репозиторий>/<groupId через />/<artifactId>/<версия>/<artifactId>-<версия>.pom
Файлы скачиваются стандартным модулем urllib и разбираются xml.etree:
менеджеры пакетов и сторонние библиотеки не используются.

Версии зависимостей часто не написаны прямо, поэтому учитываются
свойства ${...}, родительские POM (<parent>), раздел
<dependencyManagement> и импортированные BOM (scope import).
"""

import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from http import HTTPStatus
from xml.etree import ElementTree

TIMEOUT = 30
MAX_PASSES = 10
PROPERTY = re.compile(r"\$\{([^}]+)\}")
DEPENDENCY_TAGS = ("groupId", "artifactId", "version", "scope", "type",
                   "optional")
COORDINATE_TAGS = ("groupId", "artifactId", "version")
DEFAULT_SCOPE = "compile"
TRANSITIVE_SCOPES = ("compile", "runtime")
UNKNOWN_VERSION = "?"
POM_ROOT = "project"
BOM_TYPE = "pom"
BOM_SCOPE = "import"
TRUE_TEXT = "true"


class RepositoryError(Exception):
    """Не удалось скачать или разобрать POM-файл."""


@dataclass
class Dependency:
    """Прямая зависимость пакета."""

    group: str
    artifact: str
    version: str
    scope: str = DEFAULT_SCOPE
    optional: bool = False

    @property
    def name(self):
        """Имя пакета в виде groupId:artifactId."""
        return f"{self.group}:{self.artifact}"

    @property
    def node(self):
        """Вершина графа: groupId:artifactId:версия."""
        return f"{self.name}:{self.version or UNKNOWN_VERSION}"

    @property
    def is_transitive(self):
        """Maven подтягивает зависимость: compile или runtime, не optional.

        Зависимости test и provided нужны только при сборке самого
        пакета, а optional нужно подключать явно, поэтому в граф
        зависимостей они не попадают.
        """
        return self.scope in TRANSITIVE_SCOPES and not self.optional

    def __str__(self):
        """Строка для вывода: groupId:artifactId:версия (scope)."""
        scope = f"{self.scope}, optional" if self.optional else self.scope
        return f"{self.node} ({scope})"


def download(url):
    """Скачивает файл по адресу и возвращает его содержимое (байты)."""
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            return response.read()
    except urllib.error.HTTPError as error:
        if error.code == HTTPStatus.NOT_FOUND:
            raise RepositoryError(f"not found: {url}")
        raise RepositoryError(f"HTTP error {error.code}: {url}")
    except urllib.error.URLError as error:
        raise RepositoryError(f"cannot download {url}: {error.reason}")
    except OSError as error:
        raise RepositoryError(f"cannot download {url}: {error}")


def parse_pom(data, url):
    """Разбирает XML и убирает из тегов пространство имён Maven."""
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as error:
        raise RepositoryError(f"invalid XML in {url}: {error}")
    for element in root.iter():
        element.tag = element.tag.rsplit("}", 1)[-1]
    if root.tag != POM_ROOT:
        raise RepositoryError(f"not a POM file (no <project>): {url}")
    return root


def child_text(element, tag):
    """Текст дочернего элемента tag без пробелов по краям или None."""
    child = None if element is None else element.find(tag)
    if child is None or child.text is None:
        return None
    return child.text.strip()


def coordinates(element):
    """Тройка (groupId, artifactId, version) из элемента."""
    return tuple(child_text(element, tag) for tag in COORDINATE_TAGS)


def interpolate(value, properties):
    """Подставляет значения свойств ${имя}; свойства могут быть вложены."""
    if value is None:
        return None
    for _ in range(MAX_PASSES):
        new_value = PROPERTY.sub(
            lambda match: properties.get(match.group(1), match.group(0)),
            value)
        if new_value == value:
            break
        value = new_value
    return value


def read_properties(root):
    """Свойства из раздела <properties>: {имя: значение}."""
    section = root.find("properties")
    if section is None:
        return {}
    return {item.tag: (item.text or "").strip() for item in section}


def project_properties(root):
    """Встроенные свойства project.groupId, project.version и другие."""
    parent_group, _, parent_version = coordinates(root.find("parent"))
    found = {
        "project.groupId": child_text(root, "groupId") or parent_group,
        "project.artifactId": child_text(root, "artifactId"),
        "project.version": child_text(root, "version") or parent_version,
        "project.parent.groupId": parent_group,
        "project.parent.version": parent_version}
    return {key: value for key, value in found.items() if value is not None}


def read_dependencies(element):
    """Зависимости из <dependencies> внутри элемента: список словарей."""
    if element is None:
        return []
    return [{tag: child_text(item, tag) for tag in DEPENDENCY_TAGS}
            for item in element.findall("dependencies/dependency")]


def resolve(dependency, properties):
    """Подставляет свойства во все поля зависимости."""
    return {tag: interpolate(value, properties)
            for tag, value in dependency.items()}


def dependency_name(dependency):
    """Имя groupId:artifactId для зависимости-словаря."""
    return f"{dependency['groupId']}:{dependency['artifactId']}"


def is_bom_import(dependency):
    """Импорт BOM: <type>pom</type> и <scope>import</scope>."""
    return (dependency["type"] == BOM_TYPE
            and dependency["scope"] == BOM_SCOPE)


def make_dependency(raw, managed):
    """Готовая зависимость: недостающие версия и scope из managed."""
    rule = managed.get(dependency_name(raw), {})
    return Dependency(
        group=raw["groupId"], artifact=raw["artifactId"],
        version=raw["version"] or rule.get("version"),
        scope=raw["scope"] or rule.get("scope") or DEFAULT_SCOPE,
        optional=(raw["optional"] or "").lower() == TRUE_TEXT)


class MavenRepository:
    """Репозиторий Maven по адресу URL; скачанные POM хранятся в памяти."""

    def __init__(self, url):
        """Запоминает адрес репозитория (без / в конце)."""
        self.url = url.rstrip("/")
        self.cache = {}

    def pom_url(self, group, artifact, version):
        """Адрес POM-файла пакета нужной версии."""
        path = group.replace(".", "/")
        return (f"{self.url}/{path}/{artifact}/{version}/"
                f"{artifact}-{version}.pom")

    def load_pom(self, group, artifact, version):
        """Скачивает и разбирает POM-файл (каждый файл только один раз)."""
        url = self.pom_url(group, artifact, version)
        if url not in self.cache:
            self.cache[url] = parse_pom(download(url), url)
        return self.cache[url]

    def pom_chain(self, group, artifact, version):
        """POM пакета и всех его родителей: [пакет, родитель, дед, ...]."""
        chain = [self.load_pom(group, artifact, version)]
        seen = {(group, artifact, version)}
        parent = chain[-1].find("parent")
        while parent is not None:
            parent_id = coordinates(parent)
            if None in parent_id:
                raise RepositoryError(f"incomplete <parent> in the POM of "
                                      f"{':'.join(chain_id(chain[-1]))}")
            if parent_id in seen:
                raise RepositoryError("parent POMs form a cycle at "
                                      + ":".join(parent_id))
            seen.add(parent_id)
            chain.append(self.load_pom(*parent_id))
            parent = chain[-1].find("parent")
        return chain

    def model(self, package_id, seen):
        """Свойства, управляемые версии и зависимости с учётом родителей.

        Значения пакета важнее значений родителя. Зависимости пакета
        идут первыми, за ними унаследованные. Свойства подставляются
        в самом конце, когда собраны значения всех POM.
        """
        chain = self.pom_chain(*package_id)
        properties, managed, dependencies = {}, {}, {}
        for root in reversed(chain):
            properties.update(read_properties(root))
            for item in read_dependencies(root.find("dependencyManagement")):
                managed[dependency_name(item)] = item
        for root in chain:
            for item in read_dependencies(root):
                dependencies.setdefault(dependency_name(item), item)
        properties.update(project_properties(chain[0]))
        managed = [resolve(item, properties) for item in managed.values()]
        return {"managed": self.managed_versions(managed, seen),
                "dependencies": [resolve(item, properties)
                                 for item in dependencies.values()]}

    def managed_versions(self, managed, seen):
        """Правила из dependencyManagement вместе с импортированными BOM.

        Правила, записанные прямо, важнее импортированных; из нескольких
        BOM побеждает тот, что указан раньше.
        """
        rules = {dependency_name(item): item for item in managed
                 if not is_bom_import(item)}
        for item in filter(is_bom_import, managed):
            bom_id = coordinates_of(item)
            if bom_id in seen:
                continue
            bom = self.model(bom_id, seen | {bom_id})
            for name, rule in bom["managed"].items():
                rules.setdefault(name, rule)
        return rules

    def direct_dependencies(self, group, artifact, version):
        """Список прямых зависимостей пакета заданной версии."""
        package_id = (group, artifact, version)
        model = self.model(package_id, {package_id})
        return [make_dependency(raw, model["managed"])
                for raw in model["dependencies"]]

    def dependencies(self, node):
        """Зависимости пакета «groupId:artifactId:версия» для графа.

        Возвращаются только зависимости, которые Maven подтягивает
        транзитивно (compile и runtime, не optional), в виде вершин
        «groupId:artifactId:версия».
        """
        group, artifact, version = node.split(":")
        if version == UNKNOWN_VERSION or PROPERTY.search(version):
            raise RepositoryError(f"the version of {group}:{artifact} "
                                  "is unknown")
        found = self.direct_dependencies(group, artifact, version)
        return [item.node for item in found if item.is_transitive]


def chain_id(root):
    """Строка groupId:artifactId:version для POM (для сообщений)."""
    group, artifact, version = coordinates(root)
    parent_group, _, parent_version = coordinates(root.find("parent"))
    return (group or parent_group or "?", artifact or "?",
            version or parent_version or "?")


def coordinates_of(dependency):
    """Тройка (groupId, artifactId, version) зависимости-словаря."""
    return tuple(dependency[tag] for tag in COORDINATE_TAGS)
