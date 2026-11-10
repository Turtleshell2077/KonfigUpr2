"""Визуализатор графа зависимостей Maven-пакетов (вариант 14).

По параметрам из YAML-файла строится граф зависимостей пакета с учётом
транзитивности (обход в глубину с рекурсией, этап 3). Источник данных —
настоящий репозиторий Maven или тестовый репозиторий из файла.

Этап 4: режим обратных зависимостей (reverse_mode) — тот же обход по
развёрнутым рёбрам тестового репозитория находит пакеты, которые
зависят от заданного.
"""

import argparse
import sys

from graph import GraphBuilder, graph_lines
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
    а в режиме обратных зависимостей рёбра графа разворачиваются.
    Иначе пакет Maven вместе с версией: groupId:artifactId:версия.
    """
    if settings["test_mode"]:
        repository = TestRepository.load(settings["repository"])
        if settings["reverse_mode"]:
            repository = repository.reversed()
        return repository, settings["package"]
    root = f"{settings['package']}:{settings['version']}"
    return MavenRepository(settings["repository"]), root


def print_graph(settings):
    """Строит граф зависимостей и печатает его."""
    repository, root = open_repository(settings)
    graph = GraphBuilder(repository, settings["filter"]).build(root)
    for line in graph_lines(graph, settings["reverse_mode"]):
        print(line)
    sys.stdout.flush()
    for node, error in graph.errors.items():
        print(f"Warning: cannot get dependencies of {node}: {error}",
              file=sys.stderr)


def main(argv=None):
    """Точка входа: читает конфиг, строит и печатает граф."""
    args = parse_args(argv)
    try:
        settings = load_settings(args.config)
    except ConfigError as error:
        print_config_errors(error)
        return EXIT_ERROR
    try:
        print_graph(settings)
    except RepositoryError as error:
        print(f"Repository error: {error}", file=sys.stderr)
        return EXIT_ERROR
    except RecursionError:
        print("Error: the dependency graph is too deep for recursive DFS",
              file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
