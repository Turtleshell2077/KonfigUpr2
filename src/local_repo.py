"""Тестовый репозиторий: описание графа пакетов в текстовом файле.

Формат файла: в каждой строке пакет, двоеточие и его зависимости через
пробел, например «A: B C». Пакеты называются большими латинскими
буквами. Пакет без зависимостей записывается как «D:». Пустые строки
и строки, которые начинаются с #, пропускаются.
"""

import re

from maven import RepositoryError

NAME = re.compile(r"[A-Z]+")
COMMENT = "#"


class TestRepository:
    """Тестовый репозиторий: {пакет: [его зависимости]}."""

    def __init__(self, path, packages):
        """Запоминает путь к файлу и описание пакетов."""
        self.path = path
        self.packages = packages

    @classmethod
    def load(cls, path):
        """Читает файл тестового репозитория."""
        try:
            with open(path, encoding="utf-8-sig") as file:
                lines = file.read().splitlines()
        except OSError as error:
            raise RepositoryError(f"cannot read '{path}': {error.strerror}")
        except UnicodeDecodeError:
            raise RepositoryError(f"'{path}' is not UTF-8 text")
        return cls(path, parse_lines(lines, path))

    def dependencies(self, node):
        """Зависимости пакета; если пакета нет в файле — ошибка."""
        if node not in self.packages:
            raise RepositoryError(f"package '{node}' not found in "
                                  f"'{self.path}'")
        return list(self.packages[node])

    def names(self):
        """Все пакеты файла: описанные и упомянутые как зависимости."""
        found = dict.fromkeys(self.packages)
        for dependencies in self.packages.values():
            found.update(dict.fromkeys(dependencies))
        return list(found)

    def reversed(self):
        """Обратный репозиторий: рёбра графа развёрнуты.

        Если A зависит от B, то в обратном репозитории у B «зависимость»
        A. Обход такого графа от пакета находит все пакеты, которые
        зависят от него (напрямую или через другие пакеты).
        """
        reverse = {name: [] for name in self.names()}
        for name, dependencies in self.packages.items():
            for dependency in dependencies:
                reverse[dependency].append(name)
        return TestRepository(self.path, reverse)


def parse_line(text, where):
    """Разбирает строку «A: B C» в пару ("A", ["B", "C"])."""
    name, colon, rest = text.partition(":")
    if not colon:
        raise RepositoryError(f"{where}: expected 'PACKAGE: DEPENDENCIES'")
    names = [name.strip(), *rest.split()]
    for item in names:
        if not NAME.fullmatch(item):
            raise RepositoryError(f"{where}: '{item}' is not a name of "
                                  "capital Latin letters")
    return names[0], list(dict.fromkeys(names[1:]))


def parse_lines(lines, path):
    """Разбирает все строки файла: {пакет: [его зависимости]}."""
    packages = {}
    for number, line in enumerate(lines, start=1):
        text = line.strip()
        if not text or text.startswith(COMMENT):
            continue
        where = f"'{path}', line {number}"
        name, dependencies = parse_line(text, where)
        if name in packages:
            raise RepositoryError(f"{where}: package '{name}' is "
                                  "described twice")
        packages[name] = dependencies
    return packages
