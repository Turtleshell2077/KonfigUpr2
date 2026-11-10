"""Визуализатор графа зависимостей Maven-пакетов (вариант 14).

По параметрам из YAML-файла строится граф зависимостей пакета с учётом
транзитивности (обход в глубину с рекурсией). Источник данных —
настоящий репозиторий Maven или тестовый репозиторий из файла.

Этап 5: граф выводится на экран в виде текста на языке диаграмм D2,
а его картинка сохраняется в файл PNG (имя файла — параметр output).
"""

import argparse
import sys

from diagram import DiagramError, d2_text, save_png
from graph import GraphBuilder, summary_lines
from local_repo import TestRepository
from maven import MavenRepository, RepositoryError
from settings import ConfigError, load_settings

DEFAULT_CONFIG = "config.yaml"
EXIT_OK = 0
EXIT_ERROR = 1


def parse_args(argv=None):
    """Разбирает командную строку: в ней только путь к конфигу."""
    parser = argparse.ArgumentParser(
        description="Dependency graph visualizer for Maven packages")
    parser.add_argument(
        "-c", "--config", default=DEFAULT_CONFIG,
        help=f"path to the YAML config file (default: {DEFAULT_CONFIG})")
    return parser.parse_args(argv)


def print_config_errors(error):
    """Печатает все ошибки конфига в поток ошибок."""
    print(f"Config error in '{error.path}':", file=sys.stderr)
    for message in error.messages:
        print(f"  {message}", file=sys.stderr)


def open_repository(settings):
    """Репозиторий и начальный пакет графа.

    В тестовом режиме пакет — это буквы из файла (версия не нужна),
    иначе пакет Maven вместе с версией: groupId:artifactId:версия.
    """
    if settings["test_mode"]:
        repository = TestRepository.load(settings["repository"])
        return repository, settings["package"]
    root = f"{settings['package']}:{settings['version']}"
    return MavenRepository(settings["repository"]), root


def show_graph(settings):
    """Строит граф, печатает его текст на D2 и сохраняет картинку PNG."""
    repository, root = open_repository(settings)
    graph = GraphBuilder(repository, settings["filter"]).build(root)
    text = d2_text(graph)
    print(f"D2 code of the dependency graph of {root}:")
    print(text, end="")
    for line in summary_lines(graph):
        print(line)
    sys.stdout.flush()
    for node, error in graph.errors.items():
        print(f"Warning: cannot get dependencies of {node}: {error}",
              file=sys.stderr)
    save_png(text, settings["output"])
    print(f"PNG image saved to {settings['output']}")


def main(argv=None):
    """Точка входа: читает конфиг, строит граф и рисует его."""
    args = parse_args(argv)
    try:
        settings = load_settings(args.config)
    except ConfigError as error:
        print_config_errors(error)
        return EXIT_ERROR
    try:
        show_graph(settings)
    except RepositoryError as error:
        print(f"Repository error: {error}", file=sys.stderr)
        return EXIT_ERROR
    except DiagramError as error:
        print(f"Image error: {error}", file=sys.stderr)
        return EXIT_ERROR
    except RecursionError:
        print("Error: the dependency graph is too deep for recursive DFS",
              file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
