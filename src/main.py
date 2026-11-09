"""Визуализатор графа зависимостей Maven-пакетов (вариант 14).

Этап 2: по параметрам из YAML-файла скачивается описание пакета
заданной версии из репозитория Maven, и на экран выводятся все его
прямые зависимости.
"""

import argparse
import sys

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


def print_dependencies(settings):
    """Скачивает описание пакета и печатает его прямые зависимости."""
    group, artifact = settings["package"].split(":")
    version = settings["version"]
    repository = MavenRepository(settings["repository"])
    dependencies = repository.direct_dependencies(group, artifact, version)
    print(f"Direct dependencies of {group}:{artifact}:{version}:")
    for dependency in dependencies:
        print(f"  {dependency}")
    if not dependencies:
        print("  (no dependencies)")


def main(argv=None):
    """Точка входа: читает конфиг и печатает прямые зависимости пакета."""
    args = parse_args(argv)
    try:
        settings = load_settings(args.config)
    except ConfigError as error:
        print_config_errors(error)
        return EXIT_ERROR
    if settings["test_mode"]:
        print("Error: the test repository mode is not supported yet",
              file=sys.stderr)
        return EXIT_ERROR
    try:
        print_dependencies(settings)
    except RepositoryError as error:
        print(f"Repository error: {error}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
